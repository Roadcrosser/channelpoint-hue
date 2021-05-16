from twitchAPI.pubsub import PubSub
from twitchAPI.twitch import Twitch
from twitchAPI.types import AuthScope, InvalidRefreshTokenException
from twitchAPI.oauth import UserAuthenticator, refresh_access_token
from uuid import UUID

import asyncio
import traceback
import colorsys
import pprint
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

NEVER_CACHE_TWITCH = config.get("NEVER_CACHE_TWITCH", False)

DEBUG = config["DEBUG"]
WHISPER_MODE = config["WHISPER_MODE"]

hue_data = {"HUE_KEY": None}

twitch_secrets = {
    "TOKEN": None,
    "REFRESH_TOKEN": None,
}


hue_data_fn = "hue_data.json"
secrets_fn = "twitch_secrets.json"


def update_twitch_secrets(new_data):
    with open(secrets_fn, "w+") as fl:
        fl.write(json.dumps(new_data))


def load_twitch_secrets():
    with open(secrets_fn) as fl:
        return json.loads(fl.read())


def update_hue_data(new_data):
    with open(hue_data_fn, "w+") as fl:
        fl.write(json.dumps(new_data))


def load_hue_data():
    with open(hue_data_fn) as fl:
        return json.loads(fl.read())


file_list = os.listdir()

if not secrets_fn in file_list:
    update_twitch_secrets(twitch_secrets)
else:
    twitch_secrets = load_twitch_secrets()

if not hue_data_fn in file_list:
    update_hue_data(hue_data)
else:
    hue_data = load_hue_data()


HUE_KEY = hue_data["HUE_KEY"]

TOKEN = twitch_secrets["TOKEN"]
REFRESH_TOKEN = twitch_secrets["REFRESH_TOKEN"]


headers = {"content-type": "application/json"}

twitch = Twitch(CLIENT_ID, CLIENT_SECRET)
twitch.session = None


def format_payload(payload):
    if FORCE_ON:
        payload["on"] = True

    return payload


async def blink_effect():
    payload = format_payload({"alert": "select"})
    await send_request(HUE_ID, payload)


white_payload = format_payload({"hue": 0, "sat": 0, "bri": 254})


async def rainbow_effect():

    rainbow = format_payload({"hue": 0, "sat": 254, "bri": 254})
    rainbow_max = 65535
    rainbow_split = 7
    rainbow_total_time = 2

    for i in range(rainbow_split + 1):
        pl = rainbow
        pl["hue"] = int(rainbow_max / rainbow_split * i)
        await send_request(HUE_ID, pl)

        await asyncio.sleep(rainbow_total_time / rainbow_split)

    await send_request(HUE_ID, white_payload)


async def police_effect():
    red = format_payload({"hue": 0, "sat": 254, "bri": 254})
    blue = format_payload({"hue": 43690, "sat": 254, "bri": 254})

    await send_request(HUE_ID, red)
    await asyncio.sleep(0.5)
    await send_request(HUE_ID, blue)
    await asyncio.sleep(0.5)
    await send_request(HUE_ID, red)
    await asyncio.sleep(0.5)
    await send_request(HUE_ID, blue)
    await asyncio.sleep(0.5)
    await send_request(HUE_ID, white_payload)


special_effects = {
    "blink": blink_effect,
    "alert": blink_effect,
    "strobe": blink_effect,
    "rainbow": rainbow_effect,
    "police": police_effect,
}


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

            resp_data = data["data"]["redemption"]
            # resp_data = json.loads(resp_data)  # Uncomment this if it breaks somehow

            if resp_data["reward"]["title"] != REWARD_NAME:
                return

            initiating_user = resp_data["user"]["login"]
            original_color = resp_data.get("user_input", "ffffff")

        ### End Block ###

        if DEBUG:
            print("User input: ", original_color)

        original_color = re.sub(r"\s", "", str(original_color).strip())

        color = original_color.lower().strip("#")
        effect = False
        payload = None

        if color in special_effects:
            effect = special_effects.get(color)
            if DEBUG:
                print("Effect:", effect)
        else:

            hue = 0
            sat = 0
            bri = 0

            try:
                color = COLOR_LOOKUP.get(color, color)
                color = re.sub(r"[^0-9a-f]", "0", "{:0>6}".format(color)[:6])
                hue, sat, bri = colorsys.rgb_to_hsv(
                    int(color[:2], 16), int(color[2:4], 16), int(color[4:6], 16)
                )

                # Hue: [0, 1) to [0, 65535)
                hue = int(hue * 65535)
                # Sat: [0, 1] to [0, 254]
                sat = int(sat * 254)
                # Bri: [0, 255] to [0, 254] (We're also ensuring this value stays within its bound
                min_bri = MINIMUM_BRIGHTNESS / 100 * 254
                max_bri = MAXIMUM_BRIGHTNESS / 100 * 254
                bri = int(min(max(bri, min_bri), max_bri))

            except:
                print(f"{initiating_user}: Failed to parse color {original_color}")
                return

            if DEBUG:
                print("Final color:", color)

            payload = {"hue": hue, "sat": sat, "bri": bri}

            payload = format_payload(payload)

            if DEBUG:
                print("Sending to hue:", payload)

        hue_id = HUE_ID
        asyncio.get_event_loop().create_task(
            callback_task(initiating_user, hue_id, payload, color, effect)
        )
    except Exception as e:
        print(
            "".join(traceback.TracebackException.from_exception(e).format()),
            file=sys.stderr,
        )
        pass


async def callback_task(initiating_user, group_id, payload, color, effect):
    try:
        if DEBUG:
            print("Running callback task...")

        if effect:
            print(f"{initiating_user}: Running {color} effect on group {group_id}")
            await effect()
        else:
            await send_request(group_id, payload)
            print(f"{initiating_user}: Changed group {group_id} color to #{color}")

    except Exception as e:
        print(
            "".join(traceback.TracebackException.from_exception(e).format()),
            file=sys.stderr,
        )
        pass


async def send_request(group_id, payload):

    payload = json.dumps(payload)

    if DEBUG:
        print("Sending request:", payload)

    if not twitch.session:
        twitch.session = aiohttp.ClientSession()

    async with twitch.session.put(
        f"{HUE_URL}/api/{HUE_KEY}/groups/{group_id}/action",
        headers=headers,
        data=payload,
    ) as r:
        resp = await r.text()

    if DEBUG:
        print("Response:", resp)


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
        hue_data["HUE_KEY"] = HUE_KEY
        update_hue_data(hue_data)
        print("Hue successfully linked.")

print("Querying hue...")
r = requests.get(
    f"{HUE_URL}/api/{HUE_KEY}/groups",
    headers=headers,
    data=json.dumps({"devicetype": "light-changing#thingy-idk"}),
)
resp = r.json()
if "error" in resp:
    print(f"An error has occured: \"{resp['error']['description']}\"\nAborting.")
    exit()
else:
    print("Hue successfully connected.")
    if DEBUG:
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(resp)


# setting up Authentication and getting your user id
twitch.authenticate_app([])

target_scope = [
    AuthScope.CHANNEL_READ_REDEMPTIONS if not WHISPER_MODE else AuthScope.WHISPERS_READ
]

auth = UserAuthenticator(twitch, target_scope, force_verify=False)

if (not TOKEN) or (not REFRESH_TOKEN) or (NEVER_CACHE_TWITCH):
    # this will open your default browser and prompt you with the twitch verification website
    TOKEN, REFRESH_TOKEN = auth.authenticate()
else:
    try:
        TOKEN, REFRESH_TOKEN = refresh_access_token(
            REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET
        )
    except InvalidRefreshTokenException:
        TOKEN, REFRESH_TOKEN = auth.authenticate()


twitch_secrets["TOKEN"] = TOKEN
twitch_secrets["REFRESH_TOKEN"] = REFRESH_TOKEN
update_twitch_secrets(twitch_secrets)

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
