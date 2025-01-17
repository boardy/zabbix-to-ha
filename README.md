# Introduction
This project makes use of the Zabbix API to detect problems within Zabbix 
monitoring and flash lights configured within Home Assistant based on the severity
of whether the problems are resolved. 

There is active hours which default to be between 09:00 and 23:00
so if a problem is raised outside of these errors, the lights don't flash
so you don't get woken up :)

This is a python script so can run directly, but can also be run via a docker 
container for simple deployment. 

Note there are a couple of headers `CF-Access-Client-Id` and `CF-Access-Client-Secret`
which are used to authenticate to the Zabbix server hosted by Cloudflare Zero Trust.
Configuring cloudflare zero trust is out of scope for this project, but if 
you are not using it, these headers would be ignored, or you can remove them. 

However, if not using them, you may want to amend the script to not check
whether the `cf-*` config values are not set otherwise the script won't run. 

This project is also not deployed docker hub as its too custom and specific to 
my setup, however, you can deploy to your own local docker repository 
and tweak to set up for your needs. 

# Configuration
| Config Name  | Description                         | Default Value | Required |
|--------------|-------------------------------------|---------------|-------|
| cf_client_id | The cloudflare zero trust client id | ""            | true  | 
| cf_client_secret | The cloudflare zero trust secret | ""            | true |
| cycle_time | How long to wait between each API request to Zabbix | 60            | false |
| ha_auth_token | The authentication token generated within Home Assistant |  true       |
| ha_base_url | The URL to home assistant URL `<IP_ADDR>:8123/api` | ""            | true |
| zabbi_api_key | The API key to send API requests to Zabbix | ""            | true |
| zabbix_url | The URL to the Zabbix API `<IP ADDR>/zabbix/api_jsonrpc.php` | "" true "     
| alert_active_hours_only | Only flash the lights during awake hours (i.e. don't flash at early morning etc | true          | false
| alert_start_active_hours | The start time the lights should be able to flash | "09:00" | false |
| alert_end_active_hours | The end time of when the lights should stop being flashed | "23:00" | false |

# Notes
There's a couple of things to note:
* The home assistant URL, can technically be a DNS name, however, I noticed API
requests were significantly slower when using the hostname (3 seconds) even though
DNS lookups were sub second, so used the IP address. 
* In the code you will notice under the Zabbi manager, there's a specific problem
being ignored to not get added to the list of active problems. This problem is 
`Buffer pool utilization is too low (less than 50% for 5m)`. Although this doesn't
show as an active problem on the GUI and the trigger is disabled, it always 
gets returned. 
* You will probably want to change the code in ZabbixManager.py on line 30
as that is filtering a specific zabbix group id which probably won't apply
to your own zabbix set up. 

# Deployment
## Running python script direct
Ensure that environment variables are set on your system and run the command
`pip3 install --no-cache-dir -r requirements.txt` to install requirements. 

Then run the service `python3 main.py` to run the script. This can be put into
a systemd service on Linux for example to keep running so its always monitored. 

## Deploying to local docker repository
Ensure docker is running on the machine you are building from, and/or where
you want to run the container form. 

Run the below command to build the container
```shell
docker build --platform linux/amd64 -t zabbix-to-ha:latest .
```
 
Note you can omit --platform if you are already on x86/64 CPU architecture,
however if you are building locally and pushing somewhere else, that has different
architecture, such as building from M Chip Apple Silicon but deploying to a 
standard linux server. 

Run the below command to tag and push the container to a custom repository
```shell
docker tag zabbix-to-ha:latest repository/zabbix-to-ha
docker push repository/zabbix-to-ha
```

Change `repository` for the `IP:PORT` if hosting on a custom docker registry. 

```shell
docker run  --restart always --network bridge --name zabbix-to-ha repository/zabbix-to-ha:latest
```

Remember to hae the environment variables set, this can be done using the `-e`
argument in the docker run command. For example
`docker run ... -e ha_base_url='http://localhost:8123/api'`

To simplify things, using a docker management tool such as portainer
can help deploy the docker container issue

Change `repository` for the `IP:PORT` if hosting on a custom docker registry. 
