import json
import yaml
import requests

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

input("Press ENTER to try blink 1:")
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload1,
)

input("Press ENTER to try blink 2:")
r = requests.put(
    f"{HUE_URL}/api/{HUE_KEY}/groups/1/action", headers=headers, json=payload2,
)
