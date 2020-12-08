import json


def get_discord_token():
    with open('../secrets.json') as f:
        data = json.load(f)
    return data['bot_token']