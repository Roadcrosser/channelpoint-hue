import json
import yaml
import requests
import time

headers = {"content-type": "application/json"}

with open("config.yaml") as fl:
    config = yaml.load(fl, Loader=yaml.FullLoader)

HUE_URL = config["HUE_URL"]

with open("hue_data.json") as fl:
    secrets = json.loads(fl.read())

HUE_KEY = secrets["HUE_KEY"]

headers = {"content-type": "application/json"}

payload1 = {"on": True, "alert": "select"}
payload2 = {"on": True, "alert": "lselect"}
payload3 = {"on": True, "hue": 0, "sat": 254, "bri": 254}
payload4 = {"on": True, "hue": 65535, "transitiontime": 300}
payload5 = {"on": True, "hue": 32767, "transitiontime": 300}

payload_police1 = {"on": True, "hue": 0, "sat": 254, "bri": 254}
payload_police2 = {"on": True, "hue": 43690, "sat": 254, "bri": 254}


input("Press ENTER to try blink 1:")
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload1,
)

input("Press ENTER to try blink 2:")
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload2,
)

input("Press ENTER to try rainbow 1:")
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload3,
)
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload4,
)

input("Press ENTER to try rainbow 2:")
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload3,
)
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload5,
)
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload4,
)

input("Press ENTER to try police:")
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload_police1,
)
time.sleep(0.5)
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload_police2,
)
time.sleep(0.5)
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload_police1,
)
time.sleep(0.5)
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload_police2,
)
