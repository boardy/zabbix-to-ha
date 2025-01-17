import os
from requests import get, post
from calendar import calendar
from datetime import datetime
import calendar
import time


class HAManager:
    base_url = ''
    auth_token = ''
    alert_active_hours_only = True
    start_active_hours = "09:00"
    end_active_hours = "23:00"
    headers = {}

    # Create the default headers

    def __init__(self):
        self.name = "HAManager"

        self.base_url = os.getenv('ha_base_url', default='')
        self.auth_token = os.getenv('ha_auth_token', default='')
        self.alert_active_hours_only = os.getenv('alert_active_hours_only', default=True)
        self.start_active_hours = os.getenv('alert_start_active_hours', default='09:00')
        self.end_active_hours = os.getenv('alert_end_active_hours', default='23:00')

        if self.base_url == '':
            print("ha_base_url is not defined as environment variable")
            exit(1)

        if self.auth_token == '':
            print("ha_auth_token is not defined as environment variable")
            exit(1)

        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "content-type": "application/json",
        }

    def is_during_active_hours(self):

        # Check if the flag for alerting only during active hours is set. If its set to 0, just return True
        # as user wants alerted 24/7

        if not self.alert_active_hours_only:
            return True

        # Get the current epoch time
        current_epoch = time.time()
        current_date = str(datetime.date(datetime.now()))

        start_active_hours_epoch = calendar.timegm(time.strptime(current_date + ' ' + self.start_active_hours,
                                                                 '%Y-%m-%d %H:%M'))
        end_active_hours_epoch = calendar.timegm(time.strptime(current_date + ' ' + self.end_active_hours,
                                                               '%Y-%m-%d %H:%M'))

        if start_active_hours_epoch <= current_epoch <= end_active_hours_epoch:
            return True
        else:
            return False

    def flash_lights(self, entity, color):

        if not self.is_during_active_hours():
            return False

        print(f"Flashing lights for entity: {entity}")
        current_state = self._getCurrentState(entity=entity)
        print(current_state)
        post_data = {
            "entity_id": entity,
            "brightness": 255,
        }

        if color == "RED":
            post_data["rgb_color"] = [255, 0, 0]
        elif color == "YELLOW":
            post_data["rgb_color"] = [255, 253, 1]
        elif color == "GREEN":
            post_data["rgb_color"] = [0, 255, 0]

        turn_off_data = {
            "entity_id": entity
        }

        for i in range(4):
            try:
                url = f"{self.base_url}/services/light/turn_on"
                response = post(url, json=post_data, headers=self.headers, timeout=1)
                if response.status_code != 200:
                    print(f"Failed to turn on lights: {response.status_code}")

                time.sleep(1)

                url = f"{self.base_url}/services/light/turn_off"
                response = post(url, json=turn_off_data, headers=self.headers)
                if response.status_code != 200:
                    print(f"Failed to turn off lights: {response.status_code}")

                time.sleep(1)
            except:
                print("An error occurred communicating with home assistant, will continue to try")

        self.restore_state(previous_state=current_state)

        return True

    def _getCurrentState(self, entity):
        # Get the current state of the entity, it is assumed this is an entity helper with a collection of lights
        url = f"{self.base_url}/states/{entity}"
        response = get(url, headers=self.headers)
        if response.status_code != 200:
            print("Failed to get entity collection status. Status code: " + str(response.status_code))
            exit(1)

        collection_state = response.json()

        # Now that we have the collection entity, go through each entity and create a state object so we
        # can restore to the original state
        restore_state = []
        for specific_entity in collection_state["attributes"]["entity_id"]:
            try:
                # Get the current state of the specific light entity
                url = f"{self.base_url}/states/{specific_entity}"
                response = get(url, headers=self.headers)
                if response.status_code != 200:
                    print("Failed to get specific light entity status. Status code: " + str(response.status_code))
                    exit(1)

                specific_entity_state = response.json()

                # Add the specific light entity state to the restore_state list

                light_state = {
                    "entity": specific_entity,
                    "attributes": {
                        "state": specific_entity_state["state"],
                        "brightness": specific_entity_state["attributes"]["brightness"],
                    }
                }
                if 'rgb_color' in specific_entity_state["attributes"]:
                    light_state["attributes"]["rgb_color"] = specific_entity_state["attributes"]["rgb_color"]

                restore_state.append(light_state)

            except Exception as e:
                print("Failed to get the current state of collection")
                print(e)
        return restore_state

    def restore_state(self, previous_state):
        print("Restoring State")
        for state in previous_state:
            try:
                if state["attributes"]["state"] == "on":
                    post_data = {
                        "entity_id": state["entity"],
                        "brightness": state["attributes"]["brightness"],
                    }
                    if "rgb_color" in state["attributes"]:
                        post_data["rgb_color"] = state["attributes"]["rgb_color"]

                    url = f"{self.base_url}/services/light/turn_on"
                    response = post(url, json=post_data, headers=self.headers)
                    if response.status_code != 200:
                        print(f"Failed to turn on lights: {response.status_code}")
                else:
                    post_data = {
                        "entity_id": state["entity"]
                    }
                    url = f"{self.base_url}/services/light/turn_off"
                    response = post(url, json=post_data, headers=self.headers)
                    if response.status_code != 200:
                        print(f"Failed to turn on lights: {response.status_code}")
            except:
                print(f"Failed to restore light: '{state['entity']}'")
