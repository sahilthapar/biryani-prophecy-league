import httplib2
import json
from assets import Team, Fixture

BOOTSTRAP_URL = "http://fantasy.premierleague.com/api/bootstrap-static/"
EVENT_URL = "http://fantasy.premierleague.com/api/fixtures/?event="
H = httplib2.Http(".cache", disable_ssl_certificate_validation=True)


def get_teams():
    _, content = H.request(BOOTSTRAP_URL, "GET")
    bootstrap = json.loads(content)
    teams = {}
    for x in bootstrap['teams']:
        teams[x['id']] = Team(x)
    return teams


def get_events(gameweek, teams):
    _, content = H.request(EVENT_URL + gameweek, "GET")
    events = json.loads(content)
    return [Fixture(e, teams) for e in events]

# def
