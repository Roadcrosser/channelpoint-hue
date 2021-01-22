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

blink = {"on": True, "alert": "select"}

rainbow = {"on": True, "hue": 0, "sat": 254, "bri": 254}
rainbow_max = 65535
rainbow_split = 7
rainbow_total_time = 3

payload_police1 = {"on": True, "hue": 0, "sat": 254, "bri": 254}
payload_police2 = {"on": True, "hue": 43690, "sat": 254, "bri": 254}


input("Press ENTER to try blink 1:")
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=blink,
)

input("Press ENTER to try rainbow:")
for i in range(rainbow_split + 1):
    pl = rainbow
    pl["hue"] = rainbow_max / rainbow_split * i

    r = requests.put(
        f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=pl,
    )

    if i != rainbow_split:
        time.sleep(rainbow_total_time / rainbow_split)


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
