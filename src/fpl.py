import httplib2
import json
from assets import Team, Fixture, Player, Prediction, GoogleSheets

BOOTSTRAP_URL = "http://fantasy.premierleague.com/api/bootstrap-static/"
EVENT_URL = "http://fantasy.premierleague.com/api/fixtures/?event="
H = httplib2.Http(".cache", disable_ssl_certificate_validation=True)


def find_gameweek(events):
    cur = next(item for item in events if item["is_current"] is True)
    nxt = next(item for item in events if item["is_next"] is True)
    if cur['finished'] and cur['data_checked']:
        return nxt
    else:
        return cur


def get_discord_token():
    with open('../secrets.json') as f:
        data = json.load(f)
    return data['bot_token']


def bootstrap(bot):
    bot.sheets = get_sheets()
    bot.primary_sheet = bot.sheets[-1][-1]

    _, content = H.request(BOOTSTRAP_URL, "GET")
    response = json.loads(content)
    teams = {}
    for x in response['teams']:
        teams[x['id']] = Team(x)
    bot.teams = teams

    bot.gameweek = find_gameweek(response['events'])
    bot.gameweek_id = bot.gameweek['id']
    bot.fixtures = get_events(bot.gameweek_id, bot.teams)

    bot.start, bot.end = get_interval(fixtures=bot.fixtures,
                                      gameweek=bot.gameweek_id,
                                      start_gw=bot.start_gw,
                                      base_padding=bot.base_padding)


def get_sheets():
    primary_sheet = GoogleSheets()
    with open('../secrets.json') as f:
        data = json.load(f)
    return [(v['name'], GoogleSheets(v['sheet_id'])) for v in data['player_sheet_ids']] + [('main', primary_sheet)]


def get_events(gameweek, teams):
    _, content = H.request(EVENT_URL + str(gameweek), "GET")
    events = json.loads(content)
    return [Fixture(e, teams) for e in events]


def get_interval(fixtures: list, gameweek: int, start_gw: int, base_padding=0):
    base_padding = 0
    start = (11 * (gameweek - start_gw)) + 2 + base_padding
    end = start + len(fixtures) - 1
    return start, end


def calculate_live_scores(bot):
    standings = bot.primary_sheet.get_data('POINTS TABLE', '!A2:F6')
    bot.players = dict()
    for p in standings:
        bot.players[p[0]] = Player(*p)
    raw_predictions = bot.primary_sheet.get_data('Fixtures', '!A{}:G{}'.format(bot.start, bot.end))
    for idx, p in enumerate(raw_predictions):
        if len(p) < 7 or '' in p:
            continue
        bot.players['ani'].add_points(Prediction(p[2]).evaluate_prediction(bot.fixtures[idx]))
        bot.players['arjun'].add_points(Prediction(p[3]).evaluate_prediction(bot.fixtures[idx]))
        bot.players['deepak'].add_points(Prediction(p[4]).evaluate_prediction(bot.fixtures[idx]))
        bot.players['sahil'].add_points(Prediction(p[5]).evaluate_prediction(bot.fixtures[idx]))
        bot.players['tanuj'].add_points(Prediction(p[6]).evaluate_prediction(bot.fixtures[idx]))

    standings = sorted(bot.players.values(),
                       key=lambda s: [s.points, s.correct_results, s.correct_scorelines, s.correct_a_score,
                                      s.correct_h_score, s.name],
                       reverse=True)
    return standings
