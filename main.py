from HAManager import HAManager
from ZabbixManager import ZabbixManager
import time
import json
import os

zabbix = ZabbixManager()
ha_manager = HAManager()
first_loop_completed = False
previous_severity = 0
cycle_time = int(os.getenv("cycle_time", default=60))
light_entity = os.getenv("light_entity", default="")

if light_entity == "":
    print("Light entity is not set")
    exit(1)

while True:

    if not first_loop_completed:
        if os.path.exists('./status.json'):
            with open('./status.json', 'r') as file:
                data = json.load(file)  # Parses the JSON content
                previous_severity = data['current_severity']
        else:
            previous_severity = 0

    problems_status = zabbix.checkZabbixProblems()
    current_severity = problems_status["current_severity"]

    if current_severity != previous_severity:
        if current_severity >= 4:
            print("Severity changed flashing lights red")
            ha_manager.flash_lights(entity=light_entity, color="RED")
        elif current_severity >= 2:
            print("Severity changed flashing lights yellow")
            ha_manager.flash_lights(entity=light_entity, color="YELLOW")
        else:
            print("Severity changed flashing lights green")
            ha_manager.flash_lights(entity=light_entity, color="GREEN")

        previous_severity = current_severity
    else:
        print("Severity not changed - not flashing lights")

    first_loop_completed = True
    time.sleep(cycle_time)
