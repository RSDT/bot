"""zie docs van micky"""
__author__ = 'mattijn'
import requests
import utils
from tokens import sleutel_micky
from datetime import date
class MattijnError(Exception):
    """
    42000
    42001
    42002
    42003
    42004
    42005
    """
    pass


class HunterLocatie(utils.Json):
    def __init__(self, json):
        super(HunterLocatie, self).__init__(json)


class Vos(utils.Json):
    def __init__(self, json):
        super(Vos, self).__init__(json)


class ScoutingGroep(dict):
    def __init__(self, json):
        super(ScoutingGroep, self).__init__(json=json)


class MickyApi:
    def __init__(self):
        self.base_url = 'http://jotihunt-api.area348.nl/{call}/' + sleutel_micky
        self.teams = ['a', 'b', 'c', 'd', 'e', 'f', 'x']

    def send_hunter_coord(self, *, gebruiker=None, latitude=None, longitude=None, hunter=None):
        raise NotImplementedError()  # TODO implement this

    def get_hunter_namen(self):
        url = (self.base_url +'/gebruiker').format(call='hunter')
        try:
            r = requests.get(url)
            return r.json()
        except:
            return []

    def get_tail(self, gebruiker):
        if gebruiker == '':
            raise MattijnError(42001, 'empty user')
        if type(gebruiker) != str:
            raise MattijnError(42002, 'username is no str')
        url = (self.base_url + '/gebruiker/tail/' + gebruiker).format(call='hunter')
        # if int(r.status_code) != 200 or int(r.status_code) != 201:
        #     raise MattijnError(42003, r.status_code, "waarschijnlijk geen bestaande data ingevoerd")
        try:
            r = requests.get(url)
            return r.json()
        except:
            return {gebruiker: []}

    def get_alle_hunters(self):
        url = self.base_url + '/all').format(call='hunter')
        try:
            r = requests.get(url)
            return r.json()
        except:
            return {}


    def send_vos(self,*, gebruiker,latitude,longitude,team,opmerking):
        raise NotImplementedError()  # TODO implement this

    def get_last_vos(self, team):
        if team not in self.teams:
            raise MattijnError(42004, 'Team is geen team', team)
        url = (self.base_url + '/' + team + '/last').format(call='vos')
        try:
            r = requests.get(url)
            return r.json()
        except:
            return {"id": "-1",
                     "datetime": "2015-01-1 00:00:01",
                     "latitude": "0",
                     "longitude": "0",
                     "team": team,
                     "team_naam": team.upper(),
                     "opmerking": "ERROR: " + str(r.status_code),
                     "gebruiker": ""}

    def get_coord_vos(self, team, id):
        if team not in self.teams:
            raise MattijnError(42004, 'Team is geen team', team)
        if type(id) != int:
            raise MattijnError(42005, 'id is not an int')
        url = (self.base_url + '/' + team + '/' + str(id)).format(call='vos')
        try:
            r = requests.get(url)
            print(r.status_code + '/' + type(r.status_code))
            return r.json()
        except:
            return {"id": id,
                     "datetime": "2015-01-1 00:00:01",
                     "latitude": "0",
                     "longitude": "0",
                     "team": team,
                     "team_naam": team.upper(),
                     "opmerking": "ERROR: " + str(r.status_code),
                     "gebruiker": ""}

    def get_all_vos(self, team):
        if team not in self.teams:
            raise MattijnError(42004, 'Team is geen team', team)
        url = (self.base_url + '/' + team).format(call='vos')
        try:
            r = requests.get(url)
            return r.json()
        except:
            return []

    def get_all_scouting_groepen(self):
        url = (self.base_url + '/all').format(call='sc')
        try:
            r = requests.get(url)
            return r.json()
        except:
            return []

    def get_scouting_groep(self, id):
        if type(id) != int:
            raise MattijnError(42005, 'id is not an int')
        url = (self.base_url + '/all/' + str(id)).format(call='sc')
        try:
            r = requests.get(url)
            return r.json()
        except:
            return {"adres": "Broek",
                    "id": id,
                    "latitude": "0.0",
                    "longitude": "0.0",
                    "naam": "ERROR" + str(r.status_code)}

    def get_meta(self):
        url = self.base_url.format(call='meta')
        try:
            r = requests.get(url)
            return r.json()
        except:
            year = date.today().year
            return {"MAP": "http:\/\/jotihunt{year}.area348.nl\/map.php".format(year=year),
                    "URL": "http:\/\/jotihunt{year}.area348.nl\/".format(year=year),
                    "JAAR": "{year}".format(year=year),
                    "THEMA": "ERROR" + str(r.status_code)}
