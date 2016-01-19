from collections import namedtuple

__author__ = 'Mattijn'
import requests
import time
import utils
__all__ = ['Status', 'Opdracht', 'Hint', 'Nieuws', 'JotihuntApi']

Alpha = ['ALPHA', 'A', 'Alpha']
Bravo = ['Bravo', 'B', 'Bravo']
Charlie = ['CHARLIE', 'C', 'Charlie']
Delta = ['DELTA', 'D', 'Delta']
Echo = ['ECHO', 'E', 'Echo']
Foxtrot = ['FOXTROT', 'F', 'Foxtrot']


def flatten(lists):
    if type(lists) != list:
        return []
    else:
        return_value = []
        for l in lists:
            li = flatten(l)
            if not li:
                return_value.append(l)
            else:
                for e in li:
                    return_value.append(e)
        return return_value


class Status:
    def __init__(self):
        self._dictionary = {}
        self['a'] = None
        self['b'] = None
        self['c'] = None
        self['d'] = None
        self['e'] = None
        self['f'] = None
        self._last_update = {'a': self.Alpha,
                             'b': self.Bravo,
                             'c': self.Charlie,
                             'd': self.Delta,
                             'e': self.Echo,
                             'f': self.Foxtrot}

    def __setitem__(self, key, value):
        self._dictionary[key] = value

    def __delitem__(self, key):
        del self._dictionary[key]

    def __getitem__(self, key):
        return self._dictionary[key]

    def __getattr__(self, item):
        if item in flatten([Alpha, Bravo, Charlie, Delta, Echo, Foxtrot]):
            return self[item[0].lower()]
        else:
            raise AttributeError(str(item))

    def set_deelgebied(self, deelgebied, status):
        self[deelgebied[0].lower()] = status.lower()

    def update(self):
        """ Zet de statussen naar de waarde van de jh site. """
        try:
            try:
                r = requests.get('http://jotihunt.net/api/1.0/vossen')
                json = r.json()
                data = json['data']
                for deelgebied in data:
                    self[deelgebied['team'][0].lower()] = deelgebied['status']
            except:
                pass
        except:
            data = {'alfa': 'error: status error',
                    'bravo': 'error: status error' ,
                    'charlie': 'error: status error' ,
                    'delta': 'error:  status error' ,
                    'echo': 'error: status error' ,
                    'foxtrot': 'error: status error' ,
                    'x': 'error: status error'}

        # TODO klopt dat data niet als lijst wordt gegeven?

    def get_updated(self):
        """ Return de deelgebieden die veranderd zijn sinds de vorige run. """
        return_value = [k for k,  v in self._last_update.items() if self[k] != v]
        if return_value:
            self._last_update = {'a': self.Alpha,
                                 'b': self.Bravo,
                                 'c': self.Charlie,
                                 'd': self.Delta,
                                 'e': self.Echo,
                                 'f': self.Foxtrot}
        return return_value


class Opdracht(utils.Json):
    def __init__(self, id):
        self.id = id
        try:
            self.result = requests.get('http://jotihunt.net/api/1.0/opdracht/' + str(id))
            self.json = self.result.json()
        except:
            mockresponse=namedtuple('mockresponse', ['status_code'])
            self.result = mockresponse(status_code=404)
            self.result.status_code = 404
            self.json = {'error': '404.42'}
        if 'error' in self.json.keys():
            self.error = self.json['error']
        else:
            self.last_update = int(self.json["last_update"])
            self.data = self.json['data'][0]
            self.titel = self.data['titel']
            self.inhoud = self.data['inhoud']
            self.datum = self.data['datum']
            self.eindtijd = int(self.data['eindtijd'])
            self.max_punten = int(self.data['maxpunten'])
            self.last_warning = 0

    def remaining_time(self, eenheid='seconden'):
        """Return de tijd tot de opdracht moet worden ingeleverd in eenheid. """
        if eenheid is None or eenheid in ['seconden', 's', 'seconds', 'second', 'seconde']:
            return self.eindtijd - time.time()
        if eenheid in ['minuten', 'm', 'minutes', 'minuut', 'minute']:
            return self.remaining_time() / 60
        if eenheid in ['uur', 'u', 'hour', 'uren', 'hours', 'h']:
            return self.remaining_time(eenheid='minuten') / 60
        if eenheid in ['dagen', 'd', 'days', 'dag', 'day']:
            return self.remaining_time(eenheid='uur') / 24
        else:
            return None

    def update_data(self):
        try:
            self.result = requests.get('http://jotihunt.net/api/1.0/opdracht/' + str(id))
            self.json = self.result.json()
        except:
            mockresponse=namedtuple('mockresponse', ['status_code'])
            self.result = mockresponse(status_code=404)
            self.result.status_code = 404
            self.json = {"last_update": time.time(),
                        'data':[
                            {'titel': 'error',
                             'inhoud': 'error',
                             'eindtijd': time.time() + 1000,
                             'maxpunten': 0}
                        ]}
        self.last_update = int(self.json["last_update"])
        self.data = self.json['data'][0]
        self.titel = self.data['titel']
        self.inhoud = self.data['inhoud']
        self.eindtijd = int(self.data['eindtijd'])
        self.max_punten = int(self.data['maxpunten'])




class Hint(utils.Json):
    def __init__(self, id):
        self.id = id
        self.data = None
        self.titel = None
        self.inhoud = None
        self.datum = None
        self.error = None
        self.json = None
        self.result = None
        try:
            self.result = requests.get('http://jotihunt.net/api/1.0/hint/' + str(id))
            self.json = self.result.json()
        except:
            mockresponse=namedtuple('mockresponse',['status_code'])
            self.result = mockresponse(status_code=404)
            self.result.status_code = 404
            self.json = {'error': '404.42'}
        if 'error' in self.json.keys():
            self.error =self.json['error']
        else:
            self.last_update = int(self.json["last_update"])
            self.data = self.json['data'][0]
            self.titel = self.data['titel']
            self.inhoud = self.data['inhoud']
            self.datum = self.data['datum']


class Nieuws:
    nieuws = dict()

    def __init__(self, jh_id, chat_id=None):

        self.chat_ids = set()
        if chat_id is not None:
            self.chat_ids.add(chat_id)
        self.id = jh_id
        self.url = 'http://jotihunt.net/api/1.0/nieuws/' + str(self.id)
        try:
            self.result = requests.get(self.url)
            self.json = self.result.json()
        except:
            mockresponse=namedtuple('mockresponse',['status_code'])
            self.result = mockresponse(status_code=404)
            self.result.status_code = 404
        self.error = None
        self.titel = None
        self.inhoud = None
        self.datum = None
        self.has_data = False
        if self.result.status_code == 404:
            self.error = 'an Error occurred'
        elif 'error' in self.json.keys():
            self.error = self.json['error']
        else:
            self.last_update = int(self.json["last_update"])
            self.data = self.json['data'][0]
            self.titel = self.data['titel']
            self.inhoud = self.data['inhoud']
            self.datum = self.data['datum']
            self.has_data = True

    def update(self):
        self.url = 'http://jotihunt.net/api/1.0/nieuws/' + str(self.id)
        try:
            self.result = requests.get(self.url)
            self.json = self.result.json()
        except:
            mockresponse=namedtuple('mockresponse', ['status_code'])
            self.result = mockresponse(status_code=404)
            self.result.status_code = 404
        self.error = None
        if self.result.status_code == 404:
            self.error = 'error'
        elif 'error' in self.json.keys():
            self.error = self.json['error']
        else:
            self.last_update = int(self.json["last_update"])
            self.data = self.json['data'][0]
            self.titel = self.data['titel']
            self.inhoud = self.data['inhoud']
            self.datum = self.data['datum']
            self.has_data = True

    def __hash__(self):
        return hash(self.id)


class JotihuntApi():
    def __init__(self):
        self.base_url = 'http://jotihunt.net/api/1.0/'
