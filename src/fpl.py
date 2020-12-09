import httplib2
import json
from assets import Team, Fixture, GoogleSheets

BOOTSTRAP_URL = "http://fantasy.premierleague.com/api/bootstrap-static/"
EVENT_URL = "http://fantasy.premierleague.com/api/fixtures/?event="
H = httplib2.Http(".cache", disable_ssl_certificate_validation=True)


def get_discord_token():
    with open('../secrets.json') as f:
        data = json.load(f)
    return data['bot_token']

def get_teams():
    _, content = H.request(BOOTSTRAP_URL, "GET")
    bootstrap = json.loads(content)
    teams = {}
    for x in bootstrap['teams']:
        teams[x['id']] = Team(x)
    return teams


def get_sheets():
    primary_sheet = GoogleSheets()
    with open('../secrets.json') as f:
        data = json.load(f)
    return [(v['name'], GoogleSheets(v['sheet_id'])) for v in data['player_sheet_ids']] + [('main', primary_sheet)]


def get_events(gameweek, teams):
    _, content = H.request(EVENT_URL + gameweek, "GET")
    events = json.loads(content)
    return [Fixture(e, teams) for e in events]


def get_interval(fixtures: list, gameweek: int, start_gw: int, base_padding=0):
    base_padding = 0
    start = (11 * (gameweek - start_gw)) + 2 + base_padding
    end = start + len(fixtures) - 1
    return start, end

