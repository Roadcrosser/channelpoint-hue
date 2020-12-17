from twitchAPI.pubsub import PubSub
from twitchAPI.twitch import Twitch
from twitchAPI.types import AuthScope
from twitchAPI.oauth import UserAuthenticator
from uuid import UUID

import asyncio
import colorsys
import json
import re

import requests
import yaml
import aiohttp

from colors import COLOR_LOOKUP

with open("config.yaml") as fl:
    config = yaml.load(fl, Loader=yaml.FullLoader)

HUE_URL = config["HUE_URL"]

HUE_ID = config["HUE_ID"]

CLIENT_ID = config["CLIENT_ID"]
CLIENT_SECRET = config["CLIENT_SECRET"]

USERNAME = config["USERNAME"]
REWARD_NAME = config["REWARD_NAME"]

FORCE_ON = config["FORCE_ON"]

HUE_KEY = config["HUE_KEY"]

MINIMUM_BRIGHTNESS = config["MINIMUM_BRIGHTNESS"]

MAXIMUM_BRIGHTNESS = config["MAXIMUM_BRIGHTNESS"]


headers = {"content-type": "application/json"}

twitch = Twitch(CLIENT_ID, CLIENT_SECRET)
twitch.session = None


def callback(uuid: UUID, data: dict) -> None:
    asyncio.get_event_loop().create_task(callback_task(data))

async def callback_task(data):
    if data["type"] != "reward-redeemed":
        return

    resp_data = data["data"]["redemption"]
    resp_data = json.loads(resp_data) # Comment this if it breaks somehow

    if resp_data["reward"]["title"] != REWARD_NAME:
        return

    if not twitch.session:
        twitch.session = aiohttp.ClientSession()
    
    original_color = re.sub(r"\s", "", str(resp_data["user_input"]).strip())

    color = original_color.lower().strip("#")

    hue = 0
    sat = 0
    bri = 0

    try:
        color = COLOR_LOOKUP.get(color, color)
        color = re.sub(r"[^0-9a-f]", "0", "{:0>6}".format(color)[:6])
        hue, sat, bri = colorsys.rgb_to_hsv(int(color[:2], 16), int(color[2:4], 16), int(color[4:6], 16))

        # Hue: [0, 1) to [0, 360)
        hue = int(hue * 360)
        # Sat: [0, 1] to [0, 255]
        sat = int(sat * 255)
        # Bri: [0, 255] to [0, 255] (We're also ensuring this value stays within its bound
        min_bri = MINIMUM_BRIGHTNESS/100 * 255
        max_bri = MAXIMUM_BRIGHTNESS/100 * 255
        bri = min(max(bri, min_bri), max_bri)

    except:
        print(f"{resp_data['user']['login']}: Failed to parse color {original_color}")
        return

    payload = {
            "hue": hue,
            "sat": sat,
            "bri": bri
        }
    
    if FORCE_ON:
        payload["on"] = True

    await twitch.session.put(
        f"{HUE_URL}/api/{HUE_KEY}/lights/{HUE_ID}/state",
        headers=headers,
        data=json.dumps(payload)
        )

    print(f"{resp_data['user']['login']}: Changed color to #{color}")


while not HUE_KEY:
    # Press button
    input('Press the link button on the bridge and then press ENTER...\n')
    r = requests.post(
        f"{HUE_URL}/api",
        headers=headers,
        data=json.dumps({
            "devicetype": "light-changing#thingy-idk"
        })
        )
    resp = r.json()[0]
    if "error" in resp:
        print(f"An error has occured: \"{resp['error']['description']}\"\nRetrying...")
    else:
        HUE_KEY = resp["success"]["username"]

print(f"Your token is: {HUE_KEY}\nEdit the script and add this key to `HUE_KEY` to skip this step in the future.")

# setting up Authentication and getting your user id
twitch.authenticate_app([])

target_scope = [AuthScope.CHANNEL_READ_REDEMPTIONS]
auth = UserAuthenticator(twitch, target_scope, force_verify=False)

# this will open your default browser and prompt you with the twitch verification website
token, refresh_token = auth.authenticate()
twitch.set_user_authentication(token, target_scope, refresh_token)

user_id = twitch.get_users(logins=[USERNAME])['data'][0]['id']

# starting up PubSub
pubsub = PubSub(twitch)
pubsub.start()
# you can either start listening before or after you started pubsub.
uuid = pubsub.listen_whispers(user_id, callback)
# uuid = pubsub.listen_channel_points(user_id, callback)
input('press ENTER to close...\n')
# you do not need to unlisten to topics before stopping but you can listen and unlisten at any moment you want
pubsub.unlisten(uuid)

pubsub.stop()