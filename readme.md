# Twitch Channel Points Philips Hue integration

Watch it in action [here](https://m.twitch.tv/cdawgva/clip/SillyObeseBadgerPraiseIt-NoG6VrDXmgIgtT0M)!

## Requirements

 - a Philips Hue Bridge
 - a Philips Hue
 - at least affiliate on Twitch for access to channel points

## Guide
1. Install [Python3.7.x](https://www.python.org/downloads/) if you haven't (Doesn't work on 3.9, unsure about 3.8). Ensure the "Add to PATH" setting is checked. See [here](https://datatofish.com/add-python-to-windows-path/) for how to add Python to PATH if it was already installed without that setting checked.
2. Run `pip install -r requirements.txt` in command prompt (Admin mode) to install dependencies (you only need to do this once)
3. Copy `config.sample.yaml` and rename it `config.yaml`
4. Fill in `config.yaml` with the required details (You can probably use notepad for this, but the text won't be colored)
5. Run `run_a.bat` and follow the prompts. (If there's a weird message about Microsoft Store, run `run_b.bat` instead)

## Important Notes
 - This will only work *while* the script is running. You will have to leave it turned on (and remember to turn it on each time) for it to work.
 - In the same vein, any redemptions done before or after this script is run will be lost. Running it won't immediately run any that were missed.
 - Currently, you can only change just one Hue light. The Bridge doesn't let you change all your lights at the same time, so if I ever add this feature, they may not all update at once.

## Troubleshooting

**It breaks on Step 2!**

Ensure you're on Admin Mode. Some systems may also require you to use `pip3` instead of `pip`
