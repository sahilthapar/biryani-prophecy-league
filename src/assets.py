import os.path
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class Team(object):
    """
    A class that represents a Premier League Team
    """
    def __init__(self, team_json):
        self.id = team_json['id']
        self.name = team_json['name']
        self.short_name = team_json['short_name']

    def __str__(self):
        return '{} ({})'.format(self.name, self.short_name)


class Fixture(object):
    """
    A class representing a single fixture in the English Premier League
    """
    def __init__(self, fixture_json, teams):
        self.id = fixture_json['id']
        self.event = fixture_json['event']
        self.team_a_id = fixture_json['team_a']
        self.team_a = teams[self.team_a_id]
        self.team_a_score = fixture_json['team_a_score']
        self.team_h_id = fixture_json['team_h']
        self.team_h = teams[self.team_h_id]
        self.team_h_score = fixture_json['team_h_score']
        self.scoreline = self.get_scoreline()
        self.result = self.get_result()

    def __str__(self):
        return '{} {} {}'.format(self.team_h, self.scoreline, self.team_a)

    def get_short_name(self):
        """
        Return a string representation of the fixture with team short names.
        Example Everton vs Tottenham Spurs is representated as "EVE - TOT"
        :return:
        """
        return '{}-{}'.format(self.team_h.short_name, self.team_a.short_name)

    def get_scoreline(self):
        """
        Method to get a match scoreline
        :return:
        """
        if self.team_h_score is None or self.team_a_score is None:
            return ''
        return '{}-{}'.format(self.team_h_score, self.team_a_score)

    def get_result(self):
        """
        Method to get result for a match ['home', 'away', 'draw']
        :return:
        """
        if self.scoreline == '':
            return None
        elif self.team_h_score > self.team_a_score:
            return 'home'
        elif self.team_a_score > self.team_h_score:
            return 'away'
        elif self.team_h_score == self.team_a_score:
            return 'draw'


class Player(object):
    def __init__(self, name, points=0, correct_results=0, correct_scorelines=0, correct_h_score=0, correct_a_score=0):
        self.name = name
        self.points = int(points)
        self.correct_results = int(correct_results)
        self.correct_scorelines = int(correct_scorelines)
        self.correct_h_score = int(correct_h_score)
        self.correct_a_score = int(correct_a_score)

    def __str__(self):
        return '{} has {} points'.format(self.name, self.points)

    def add_points(self, score):
        self.points += score['points']
        if score['result']:
            self.correct_results += 1
        if score['home'] and score['away']:
            self.correct_scorelines += 1
        if score['away']:
            self.correct_a_score += 1
        if score['home']:
            self.correct_h_score += 1


class Prediction(object):
    def __init__(self, scoreline):
        if '(c)' in scoreline.lower():
            self.scoreline = scoreline.lower().replace('(c)', '')
            self.multiplier = 2
        elif scoreline:
            self.scoreline = scoreline
            self.multiplier = 1
        else:
            self.scoreline = None
            self.multiplier = 1
        self.team_h_score = int(self.scoreline.split('-')[0]) if self.scoreline else None
        self.team_a_score = int(self.scoreline.split('-')[1]) if self.scoreline else None
        self.result = self.get_result()

    def get_result(self):
        if self.scoreline is None:
            return None
        elif self.team_h_score > self.team_a_score:
            return 'home'
        elif self.team_a_score > self.team_h_score:
            return 'away'
        elif self.team_h_score == self.team_a_score:
            return 'draw'

    def evaluate_prediction(self, fixture):
        """
        Evaluates a prediction and returns the number of points scored;
            if result is correct then returns 2
            if scoreline is correct then returns 4
            else returns 0
        :param fixture
        :return:
        """
        score = {
            'points': 0,
            'result': False,
            'away': False,
            'home': False
        }
        if (not self.result) or (not self.scoreline) or (
                not fixture.result) or (not fixture.scoreline) or (self.result != fixture.result):
            score['points'] = 0
        if self.result == fixture.result:
            score['points'] += (2 * self.multiplier)
            score['result'] = True
            if self.team_h_score == fixture.team_h_score:
                score['points'] += (1 * self.multiplier)
                score['home'] = True
            if self.team_a_score == fixture.team_a_score:
                score['points'] += (1 * self.multiplier)
                score['away'] = True
        return score


class GoogleSheets(object):
    def _get_sheet_(self):
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        if os.path.exists('../token.pickle'):
            with open('../token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('../token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        service = build('sheets', 'v4', credentials=creds)
        return service.spreadsheets()

    def __init__(self, spreadsheet_id='10GbBiTCcI0ZrJx7_M-L0HWYTpiMOr9twdHUVB1PHt84'):
        self.sheet = self._get_sheet_()
        self.spreadsheet_id = spreadsheet_id

    def get_data(self, spreadsheet_name, spreadsheet_range):
        rng = spreadsheet_name + spreadsheet_range
        result = self.sheet.values().get(spreadsheetId=self.spreadsheet_id, range=rng).execute()
        return result.get('values', [])

    def put_data(self, spreadsheet_name, spreadsheet_range, values):
        rng = spreadsheet_name + spreadsheet_range
        value_body = {
            "range": rng,
            "values": values
        }
        self.sheet.values().update(spreadsheetId=self.spreadsheet_id,
                                   range=rng,
                                   valueInputOption='RAW',
                                   body=value_body).execute()
