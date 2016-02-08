import random
import re
from collections import namedtuple
from datetime import time, datetime, date

import math
import requests
import telegram

import jotihuntScraper
from jotihunt_api import Nieuws, Opdracht, Hint, Status
from utils import convert_tijden, get_deelgebied
import micky_api as ma

map_url = ma.MickyApi().get_meta()["MAP"]
skip_reminder = set()
status_plaatjes = {'a': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADOAADxPsqAXmyBBClXTd4Ag'},
                         'rood': {'type': 'sticker', 'file_id': 'BQADBAADNAADxPsqAWy_jDGSfM8VAg'},
                         'oranje': {'type': 'sticker', 'file_id': 'BQADBAADNgADxPsqAW5L5FGEVeZsAg'}},
                   'c': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADTAADxPsqAYLV3juZLpBdAg'},
                         'rood': {'type': 'sticker', 'file_id': 'BQADBAADSgADxPsqAT-u5My8rm3gAg'},
                         'oranje': {'type': 'sticker', 'file_id': 'BQADBAADRgADxPsqAQV4dBO6m83XAg'}},
                   'b': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADQAADxPsqAe0nAoB-ZMyOAg'},
                         'rood': {'type': 'sticker', 'file_id': 'BQADBAADQgADxPsqAYIFsuIiE6hzAg'},
                         'oranje': {'type': 'sticker', 'file_id': 'BQADBAADRAADxPsqAWxDH1LIGSXKAg'}},
                   'e': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADWgADxPsqAUL07wYDRvidAg'},
                         'rood': {'type': 'sticker', 'file_id': 'BQADBAADVAADxPsqAQsjZhRr4lEnAg'},
                         'oranje': {'type': 'sticker', 'file_id': 'BQADBAADWAADxPsqATm-pA-vdphAAg'}},
                   'd': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADTgADxPsqAZx6xRcZie8dAg'},
                         'rood': {'type': 'sticker', 'file_id': 'BQADBAADUgADxPsqAb2HyQa_q_n8Ag'},
                         'oranje': {'type': 'sticker', 'file_id': 'BQADBAADUAADxPsqAQmw5iS__C7yAg'}},
                   'f': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADXgADxPsqATT7K_u22oL7Ag'},
                         'rood': {'type': 'sticker', 'file_id': 'BQADBAADXAADxPsqAYLGQPHFp1xLAg'},
                         'oranje': {'type': 'sticker', 'file_id': 'BQADBAADVgADxPsqAffXkv_Pldg-Ag'}}}


class ScanUpdates:
    def __init__(self, jh_bot, chat_id, deelgebied):
        self.chat_id = chat_id
        self.jh_bot = jh_bot
        self.status = Status()
        self.status.update()
        # self.status.get_updated()
        self.deelgebied = get_deelgebied(deelgebied)
        self.last_update_jh = None
        self.last_update_micky = None
        self.gecontroleerde_codes = []
        self.last_hunt = None
        self.micky_api = ma.MickyApi()

    def to_tuple(self):
        return self.chat_id, self.deelgebied

    def update_ingevoerd(self):
        # TODO deze functie testen
        hunts, labels, pref_label = jotihuntScraper.get_hunts()
        for h in hunts:
            if get_deelgebied(h[2][0]) == get_deelgebied(self.deelgebied):
                p1 =re.compile('\d+e ')
                dag = p1.findall(h[0])[0][:-2]
                p2 = re.compile('e \d+\:')
                uur= p2.findall(h[0])[0][2:-1]
                p3 = re.compile('\:\d+')
                minuut= p3.findall(h[0])[0][1:]
                d= datetime(year=date.today().year,month=10,day=dag,hour=uur,minute=minuut)
                if self.last_hunt is None:
                    self.last_hunt = d
                else:
                    dd1 = datetime.now().timestamp() - d.timestamp()
                    dd2 = datetime.now().timestamp() - self.last_hunt.timestamp()
                    if dd1 < dd2:
                        self.last_hunt = d
                if h[3] in ['goedgekeurd','afgekeurd'] and h[2] not in self.gecontroleerde_codes:
                    self.jh_bot.bot.sendMessage(self.chat_id, 'Voor de hunt '+ str(h[2]) + ' hebben we ' + str(h[-1]) +
                                                'punten gekregen.')
                    self.gecontroleerde_codes.append(h[-1])

    def update_hunt_reminder(self):
        # TODO implement this
        return

    def update(self):
        self.update_ingevoerd()
        self.update_hunt_reminder()
        if self.deelgebied != 'All':
            team = self.deelgebied[0].lower()
            temp = self.micky_api.get_last_vos(team)
            if temp != self.last_update_micky:
                self.jh_bot.bot.sendMessage(self.chat_id, "Er is een nieuwe hint voor " + self.deelgebied
                                            + " ingevoerd.\n" + 'Dit is een hint van ' + str(
                    temp['datetime'][11:]))  # TODO moet dit naar x minuten geleden?
                self.jh_bot.bot.sendLocation(self.chat_id, latitude=float(temp['latitude']),
                                             longitude=float(temp['longitude']))
                self.jh_bot.bot.sendMessage(self.chat_id,
                                            'zie deze hint op de kaart: ' + map_url + '?' + 'gebied=' +
                                            self.deelgebied[0].upper())
                self.last_update_micky = temp
            self.status.update()
            for deelgebied in [d for d in self.status.get_updated() if d == self.deelgebied[0].lower()]:
                self.jh_bot.bot.sendMessage(self.chat_id, 'Er is een status-update voor ' +
                                            get_deelgebied(deelgebied[0].upper()) + '.\n' +
                                            'de nieuwe status voor ' + get_deelgebied(deelgebied[0].upper()) + ' = ' +
                                            self.status[deelgebied])
                if status_plaatjes[deelgebied[0].lower()][self.status[deelgebied].lower()]['type'] == 'photo':
                    self.jh_bot.bot.sendPhoto(self.chat_id,
                                              status_plaatjes[deelgebied[0].lower()][self.status[deelgebied].lower()][
                                                  'file_id'])
                if status_plaatjes[deelgebied[0].lower()][self.status[deelgebied].lower()]['type'] == 'sticker':
                    self.jh_bot.bot.sendSticker(self.chat_id,
                                                status_plaatjes[deelgebied[0].lower()][self.status[deelgebied].lower()][
                                                    'file_id'])

class HBUpdates(ScanUpdates):
    def __init__(self, jh_bot, chat_id, deelgebied):
        super(HBUpdates, self).__init__(jh_bot, chat_id, deelgebied)
        self.chat_id = chat_id
        self.jh_bot = jh_bot
        self.deelgebied = get_deelgebied(deelgebied)
        self.opdrachten = []
        self.hints = []
        self.nieuws = []
        self.errors = {'opdrachten': None, 'hints': None, 'nieuws': None}

    def update_opdracht_klaar(self):
        opdrachten, labels, pref_label = jotihuntScraper.get_opdrachten()
        for opdracht in opdrachten:
            opdrachten2 = [o for o in self.opdrachten if opdracht[1] == o.titel]
            if len(opdrachten2) == 1:
                if opdrachten2[0].gekregen_punten == None:
                    if opdracht[2] != None:
                        opdrachten2[0].aantal_punten = opdracht[2]
                        self.jh_bot.bot.sendMessage(self.chat_id, 'We hebben '+ str(opdrachten2[0].aantal_punten) +
                                                    'van de ' + opdrachten2[0].max_punten +
                                                    'punten gekregen voor de opdracht met de titel: [' +
                                                    opdrachten2[0].titel + ']' + '(http://jotihunt.net/bericht/?MID=' +
                                                    opdrachten2[0].id + ')' + '\n de inlevertijd was: ' +
                                                    str(opdrachten2[0].ingeleverd),
                                                    parse_mode=telegram.ParseMode.MARKDOWN)
                if opdrachten2[0].ingeleverd is None:
                    if opdracht[0] is not None:
                        opdrachten2[0].ingeleverd = opdracht[0]
                        self.jh_bot.bot.sendMessage(self.chat_id, 'De opdracht is ingeleverd met de titel: [' +
                                                    opdrachten2[0].titel + ']' + '(http://jotihunt.net/bericht/?MID=' +
                                                    opdrachten2[0].id + ')' + '\n de inlevertijd was: ' +
                                                    str(opdrachten2[0].ingeleverd),
                                                    parse_mode=telegram.ParseMode.MARKDOWN)

    def update_hints(self):

        try:
            r = requests.get('http://jotihunt.net/api/1.0/hint')
            r.json()
        except:
            mockresponse = namedtuple('mockresponse', ['status_code'])
            r = mockresponse(status_code=404)
            r.status_code = 404
        if r.status_code == 404 or 'error' in r.json().keys() and self.errors['hints'] != r.json()['error']:
            hints = []
            self.errors['hints'] = r.json()['error']
            self.jh_bot.bot.sendMessage(self.chat_id,
                                        'De jotihuntsite gaf een error tijdens het binnenhalen van de hints: ' +
                                        r.json()['error'])
        elif 'error' in r.json().keys():
            hints = []
        else:
            self.errors['hints'] = None
            hints = r.json()['data']
        for h in hints:
            if h['ID'] not in [hi.id for hi in self.hints]:
                hint = Hint(h['ID'])
                self.hints.append(hint)
                self.jh_bot.bot.sendMessage(self.chat_id, 'Er zijn nieuwe hints met de titel: [' + hint.titel + ']' +
                                            '(http://jotihunt.net/bericht/?MID=' + h['ID'] + ')',
                                            parse_mode=telegram.ParseMode.MARKDOWN)

    def opdracht_reminders(self):
        reminders = [[None, (1, 'dag'), (1, 'dag')],
                     [(1, 'dag'), (1, 'uur'), (2, 'uur')],
                     [(1, 'uur'), (30, 'minuten'), (10, 'minuten')],
                     [(30, 'minuten'), (10, 'minuten'), (5, 'minuten')],
                     [(15, 'minuten'), (3, 'minuten'), (3, 'minuten')],
                     [(3, 'minuten'), (0, 'minuten'), (1, 'minuten')],
                     [(0, 'minuten'), (-2, 'minuten'), (1, 'minuten')],
                     [(-2, 'minuten'), None, None]]
        for opdracht in self.opdrachten:
            if opdracht.id in skip_reminder or opdracht.ingeleverd is not None:
                return
            for reminder in reminders:
                if None in reminder:
                    if reminder[0] is None:
                        reminder[0] = (opdracht.remaining_time() + 9001, 'seconds')
                        while not reminder[0][0] > opdracht.remaining_time(reminder[0][1]):
                            reminder[0] = (
                                opdracht.remaining_time() + (random.choice([1, -1]) * random.choice(range(1000))),
                                'seconds')
                    if reminder[1] is None:
                        reminder[1] = (opdracht.remaining_time() - 9001, 'seconds')
                        while not reminder[1][0] > opdracht.remaining_time(reminder[1][1]):
                            reminder[1] = (
                                opdracht.remaining_time() + (random.choice([1, -1]) * random.choice(range(1000))),
                                'seconds')
                if reminder[0][0] > opdracht.remaining_time(reminder[0][1]) and reminder[1][
                    0] < opdracht.remaining_time(reminder[1][1]):
                    d_time = time.time() - opdracht.last_warning
                    if reminder[2] is not None and d_time > convert_tijden(reminder[2][0], reminder[2][1]):
                        opdracht.last_warning = time.time()
                        self.jh_bot.bot.sendMessage(self.chat_id,
                                                    'Reminder voor de opdracht: [' + opdracht.titel +
                                                    '](.http://jotihunt.net/bericht/?MID=' + str(opdracht.id) +
                                                    "\n Hier kunnen we " + str(opdracht.max_punten) +
                                                    "punt" + ('en' * (opdracht.max_punten != 0)) + "mee verdienen." +
                                                    "We kunnen hier nog " +
                                                    str(math.floor(opdracht.remaining_time('uur'))) + ' uur en ' +
                                                    str(math.floor(opdracht.remaining_time('minuten') % 60)) +
                                                    ' minuten over doen.' + '\n',
                                                    parse_mode=telegram.ParseMode.MARKDOWN)

    def update_opdrachten(self):
        try:
            r = requests.get('http://jotihunt.net/api/1.0/opdracht')
            r.json()
        except:
            mockresponse = namedtuple('mockresponse', ['status_code'])
            r = mockresponse(status_code=404)
            r.status_code = 404
        if r.status_code == 404 or 'error' in r.json().keys() and r.json()['error'] != self.errors['opdrachten']:
            opdrachten = []
            self.errors['opdrachten'] = r.json()['error']
            self.jh_bot.bot.sendMessage(self.chat_id,
                                        'De jotihuntsite gaf een error tijdens het binnenhalen van de opdrachten: ' +
                                        r.json()['error'])
        elif 'error' in r.json().keys():
            opdrachten = []
        else:
            self.errors['opdrachten'] = None
            opdrachten = r.json()['data']
        for o in opdrachten:
            if o['ID'] not in [op.id for op in self.opdrachten]:
                opdracht = Opdracht(o['ID'])
                opdracht.last_warning = time.time()
                self.opdrachten.append(opdracht)
                self.jh_bot.bot.sendMessage(self.chat_id, 'Er is een nieuwe opdracht met de titel: [' + opdracht.titel +
                                            ']' + '(http://jotihunt.net/bericht/?MID=' + o['ID'] + ')' +
                                            ".\n Hier kunnen we " + str(opdracht.max_punten) + "punten mee verdienen." +
                                            "We kunnen hier nog " + str(math.floor(opdracht.remaining_time('uur'))) +
                                            ' uur en ' + str(math.floor(opdracht.remaining_time('minuten') % 60)) +
                                            ' minuten over doen.', parse_mode=telegram.ParseMode.MARKDOWN
                                            )

    def update_nieuws(self):
        try:
            r = requests.get('http://jotihunt.net/api/1.0/nieuws')
        except:
            mockresponse = namedtuple('mockresponse', ['status_code'])
            r = mockresponse(status_code=404)
            r.status_code = 404
        if r.status_code == 404 or 'error' in r.json().keys() and self.errors['nieuws'] != r.json()['error']:
            nieuws = []
            self.errors['nieuws'] = r.json()['error']
            self.jh_bot.bot.sendMessage(self.chat_id,
                                        'De jotihuntsite gaf een error tijdens het binnenhalen van nieuws: ' +
                                        r.json()['error'])
        elif 'error' in r.json().keys():
            nieuws = []
        else:
            self.errors['nieuws'] = None
            nieuws = r.json()['data']
        for n in nieuws:
            if n['ID'] not in [ni.id for ni in self.nieuws]:
                nieuwst = Nieuws(n['ID'], self.chat_id)
                self.nieuws.append(nieuwst)
                self.jh_bot.bot.sendMessage(self.chat_id, 'Er is nieuws met de titel: [' + nieuwst.titel +
                                            '](http://jotihunt.net/bericht/?MID=' + n['ID'] + ')',
                                            parse_mode=telegram.ParseMode.MARKDOWN)
                # hashed_niewuws = [hash(ni) for ni in self.nieuws]
                # for n in nieuws:
                #     temp_n = Nieuws(n['ID'], chat_id=self.chat_id)
                #     if hash(temp_n) in hashed_niewuws:
                #
                #         for ni in self.nieuws:

    def update(self):
        self.update_hints()
        self.update_nieuws()
        self.update_opdrachten()
        self.update_opdracht_klaar()
        self.opdracht_reminders()


