import json
import os

import requests


class ZabbixManager:
    zabbix_url = ""
    zabbix_api_key = ""
    cf_client_id = ""
    cf_client_secret = ""

    def __init__(self):
        self.zabbix_url = os.getenv("zabbix_url", default="")
        self.zabbix_api_key = os.getenv("zabbix_api_key", default="")
        self.cf_client_id = os.getenv("cf_client_id", default="")
        self.cf_client_secret = os.getenv("cf_client_secret", default="")

    def checkZabbixProblems(self):
        # Get Zabbix Problems for the enabled trigger ids
        body = {
            "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": ["eventid", "name", "severity", "acknowledged", "suppressed", "clock", "source"],
                # 'clock' is the start date
                "sortfield": ["eventid"],
                "sortorder": "DESC",
                "severities": [2, 3, 4, 5],  # Warning level and up
                "groupids": ["22"]  # Filtering on the production group
            },
            "id": 1
        }

        problems_json = self.sendToZabbixServer(body=body)
        if problems_json == "":
            return {
                "active_problems": [],
                "current_severity": 0
            }

        problems = []

        highest_severity = 0

        for problem in problems_json['result']:
            # Check that the name isn't related to buffer pool, this has been disabled, and doesn't show
            # as an active problem on the Zabbix GUI but this keeps getting returned
            if problem['name'] != "Buffer pool utilization is too low (less than 50% for 5m)":
                problems.append({
                    "eventid": problem['eventid'],
                    "name": problem['name'],
                    "severity": problem['severity'],
                })

                if int(problem['severity']) > highest_severity:
                    highest_severity = int(problem['severity'])

        print(problems)

        current_status_json = {
            "active_problems": problems,
            "current_severity": highest_severity
        }

        with open('./status.json', 'w') as json_file:
            json.dump(current_status_json, json_file, indent=4)

        return current_status_json

    def sendToZabbixServer(self, body):
        try:

            if self.zabbix_url == "":
                print("Zabbix URL is not set")
                return ""
            if self.cf_client_id == "":
                print("CF Client ID not set")
                return ""
            if self.cf_client_secret == "":
                print("CF Client Secret not set")
                return ""
            if self.zabbix_api_key == "":
                print("Zabbix API Key not set")
                return ""

            url = self.zabbix_url
            print(f"Sending zabbix request to {url}")
            headers = {
                'Authorization': f"Bearer {self.zabbix_api_key}",  # Replace with your actual token
                'Content-Type': 'application/json-rpc',
                "CF-Access-Client-Id": self.cf_client_id,
                "CF-Access-Client-Secret": self.cf_client_secret
            }

            print("Sending response to zabbix")
            response = requests.post(url, headers=headers, json=body)
            print(f"Status Code: {response.status_code}")
            return response.json()
        except:
            print("Failed to send zabbix request")
            return ""
