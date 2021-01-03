from twitchAPI.pubsub import PubSub
from twitchAPI.twitch import Twitch
from twitchAPI.types import AuthScope
from twitchAPI.oauth import UserAuthenticator
from uuid import UUID

import asyncio
import traceback
import colorsys
import json
import sys
import re
import os

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

MINIMUM_BRIGHTNESS = config["MINIMUM_BRIGHTNESS"]

MAXIMUM_BRIGHTNESS = config["MAXIMUM_BRIGHTNESS"]

DEBUG = config["DEBUG"]
WHISPER_MODE = config["WHISPER_MODE"]

secrets = {
    "HUE_KEY": None,
    "TOKEN": None,
    "REFRESH_TOKEN": None,
}


secrets_fn = "secrets.json"


def update_secrets(new_data):
    with open(secrets_fn, "w+") as fl:
        fl.write(json.dumps(new_data))


def load_secrets():
    with open(secrets_fn) as fl:
        return json.loads(fl.read())


if not secrets_fn in os.listdir():
    update_secrets(secrets)
else:
    secrets = load_secrets()

HUE_KEY = secrets["HUE_KEY"]
TOKEN = secrets["TOKEN"]
REFRESH_TOKEN = secrets["REFRESH_TOKEN"]


headers = {"content-type": "application/json"}

twitch = Twitch(CLIENT_ID, CLIENT_SECRET)
twitch.session = None


def callback(uuid: UUID, data: dict) -> None:
    try:
        if DEBUG:
            print("Data received: ", data)

        ### This block for testing on whispers ###
        if WHISPER_MODE:
            if data["type"] != "whisper_received":
                return

            resp_data = data["data"]
            resp_data = json.loads(resp_data)  # Comment this if it breaks somehow

            initiating_user = resp_data["tags"]["login"]
            original_color = resp_data["body"]

        ### End Block ###

        ### This block for prod channel points ###
        else:
            if data["type"] != "reward-redeemed":
                return

            resp_data = data["data"]
            resp_data = json.loads(resp_data)  # Comment this if it breaks somehow

            if resp_data["reward"]["title"] != REWARD_NAME:
                return

            initiating_user = resp_data["user"]["login"]
            original_color = resp_data["user_input"]

        ### End Block ###

        if DEBUG:
            print("User input: ", original_color)

        original_color = re.sub(r"\s", "", str(original_color).strip())

        color = original_color.lower().strip("#")

        hue = 0
        sat = 0
        bri = 0

        try:
            color = COLOR_LOOKUP.get(color, color)
            color = re.sub(r"[^0-9a-f]", "0", "{:0>6}".format(color)[:6])
            hue, sat, bri = colorsys.rgb_to_hsv(
                int(color[:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            )

            # Hue: [0, 1) to [0, 360)
            hue = int(hue * 360)
            # Sat: [0, 1] to [0, 255]
            sat = int(sat * 255)
            # Bri: [0, 255] to [0, 255] (We're also ensuring this value stays within its bound
            min_bri = MINIMUM_BRIGHTNESS / 100 * 255
            max_bri = MAXIMUM_BRIGHTNESS / 100 * 255
            bri = min(max(bri, min_bri), max_bri)

        except:
            print(f"{initiating_user}: Failed to parse color {original_color}")
            return

        if DEBUG:
            print("Final color:", color)

        payload = {"hue": hue, "sat": sat, "bri": bri}

        if FORCE_ON:
            payload["on"] = True

        hue_id = HUE_ID

        if DEBUG:
            print("Sending to hue:", payload)

        asyncio.get_event_loop().create_task(
            callback_task(initiating_user, hue_id, payload, color)
        )
    except Exception as e:
        print(
            "".join(traceback.TracebackException.from_exception(e).format()),
            file=sys.stderr,
        )
        pass


async def callback_task(initiating_user, bulb_id, payload, color):
    try:
        if DEBUG:
            print("Running callback task...")

        if not twitch.session:
            twitch.session = aiohttp.ClientSession()

        async with twitch.session.put(
            f"{HUE_URL}/api/{HUE_KEY}/lights/{bulb_id}/state",
            headers=headers,
            data=json.dumps(payload),
        ) as r:
            resp = await r.text()

        if DEBUG:
            print("Response:", resp)

        print(f"{initiating_user}: Changed bulb {bulb_id} color to #{color}")

    except Exception as e:
        print(
            "".join(traceback.TracebackException.from_exception(e).format()),
            file=sys.stderr,
        )
        pass


while not HUE_KEY:
    # Press button
    input("Press the link button on the bridge and then press ENTER...\n")
    r = requests.post(
        f"{HUE_URL}/api",
        headers=headers,
        data=json.dumps({"devicetype": "light-changing#thingy-idk"}),
    )
    resp = r.json()[0]
    if "error" in resp:
        print(f"An error has occured: \"{resp['error']['description']}\"\nRetrying...")
    else:
        HUE_KEY = resp["success"]["username"]
        secrets["HUE_KEY"] = HUE_KEY
        update_secrets(secrets)
        print("Hue successfully linked.")


# setting up Authentication and getting your user id
twitch.authenticate_app([])

target_scope = [
    AuthScope.CHANNEL_READ_REDEMPTIONS if not WHISPER_MODE else AuthScope.WHISPERS_READ
]

if (not TOKEN) or (not REFRESH_TOKEN):
    # this will open your default browser and prompt you with the twitch verification website
    auth = UserAuthenticator(twitch, target_scope, force_verify=False)
    TOKEN, REFRESH_TOKEN = auth.authenticate()
    secrets["TOKEN"] = TOKEN
    secrets["REFRESH_TOKEN"] = REFRESH_TOKEN
    update_secrets(secrets)

twitch.set_user_authentication(TOKEN, target_scope, REFRESH_TOKEN)

user_id = twitch.get_users(logins=[USERNAME])["data"][0]["id"]

# starting up PubSub
pubsub = PubSub(twitch)
pubsub.start()
# you can either start listening before or after you started pubsub.
if WHISPER_MODE:
    uuid = pubsub.listen_whispers(user_id, callback)
else:
    uuid = pubsub.listen_channel_points(user_id, callback)

input("Now listening for events.\nPress ENTER at any time to stop.\n")
# you do not need to unlisten to topics before stopping but you can listen and unlisten at any moment you want
pubsub.unlisten(uuid)

pubsub.stop()
