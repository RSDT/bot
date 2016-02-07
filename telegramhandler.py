from datetime import datetime
import tokens
from utils import logger, one_of_in
import telegram
import threading
import time
import _thread as thread
import requests
import micky_api as ma
import math
from jotihunt_api import Hint, Opdracht, Nieuws, Status
import random
import utils
import command_handler
import logging
import subprocess
from collections import namedtuple
import functools
import botan
StatusRecords = namedtuple('StatusRecords', ['aantal_keer_rood', 'aantal_keer_oranje', 'aantal_keer_groen',
                             'deelgebied', 'huidige_status','laatste_keer_verandering', 'eerst_status'])
status_records = {}
__author__ = 'mattijn'
FORMAT = '%(asctime)-15s %(message)s'
log = logging.getLogger()
log.setLevel(logging.NOTSET)
log.error('Test')
logging.basicConfig(filename='example.log', filemode='a', level=logging.DEBUG, format=FORMAT)
skip_reminder = set()
known_updates = []
in_chats = set()
map_url = ma.MickyApi().get_meta()["MAP"]

auth_token = tokens.auth_token
admins = tokens.admins
admins_only = True
RP_addme_groepschat = None
known_users = []

update_list = []
status_plaatjes = {'a': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADOAADxPsqAXmyBBClXTd4Ag'}, 'rood': {'type': 'sticker', 'file_id': 'BQADBAADNAADxPsqAWy_jDGSfM8VAg'}, 'oranje': {'type': 'sticker', 'file_id': 'BQADBAADNgADxPsqAW5L5FGEVeZsAg'}}, 'c': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADTAADxPsqAYLV3juZLpBdAg'}, 'rood': {'type': 'sticker', 'file_id': 'BQADBAADSgADxPsqAT-u5My8rm3gAg'}, 'oranje': {'type': 'sticker', 'file_id': 'BQADBAADRgADxPsqAQV4dBO6m83XAg'}}, 'b': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADQAADxPsqAe0nAoB-ZMyOAg'}, 'rood': {'type': 'sticker', 'file_id': 'BQADBAADQgADxPsqAYIFsuIiE6hzAg'}, 'oranje': {'type': 'sticker', 'file_id': 'BQADBAADRAADxPsqAWxDH1LIGSXKAg'}}, 'e': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADWgADxPsqAUL07wYDRvidAg'}, 'rood': {'type': 'sticker', 'file_id': 'BQADBAADVAADxPsqAQsjZhRr4lEnAg'}, 'oranje': {'type': 'sticker', 'file_id': 'BQADBAADWAADxPsqATm-pA-vdphAAg'}}, 'd': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADTgADxPsqAZx6xRcZie8dAg'}, 'rood': {'type': 'sticker', 'file_id': 'BQADBAADUgADxPsqAb2HyQa_q_n8Ag'}, 'oranje': {'type': 'sticker', 'file_id': 'BQADBAADUAADxPsqAQmw5iS__C7yAg'}}, 'f': {'groen': {'type': 'sticker', 'file_id': 'BQADBAADXgADxPsqATT7K_u22oL7Ag'}, 'rood': {'type': 'sticker', 'file_id': 'BQADBAADXAADxPsqAYLGQPHFp1xLAg'}, 'oranje': {'type': 'sticker', 'file_id': 'BQADBAADVgADxPsqAffXkv_Pldg-Ag'}}}

def update_status_records():
    try:
        try:
            r = requests.get('http://jotihunt.net/api/1.0/vossen')
        except:
            mockresponse=namedtuple('mockresponse',['status_code'])
            r = mockresponse(status_code=404)
            r.status_code = 404
            return False
        if 'error' in r.json().keys():
            return False
        data = {}
        if 'data' in r.json().keys():
            data2 = r.json()['data']
            for dgb in data2:
                data[get_deelgebied(dgb['team'].lower())] = dgb['status']
        twaalf_uur_geweest = False
        global status_records
        for k,v in status_records.items():
            dt_laatste = datetime.fromtimestamp(v.laatste_keer_verandering)
            dt_nu = datetime.fromtimestamp(time.time())
            if dt_nu.day != dt_laatste.day:
                twaalf_uur_geweest = True
        if twaalf_uur_geweest:
            status_records = {}
        for k, v in data.items():
            status_record = None
            if k not in status_records.keys():
                status_record = StatusRecords(aantal_keer_rood=int(v == 'rood'),
                                          aantal_keer_oranje=int(v == 'oranje'),
                                          aantal_keer_groen=int(v == 'groen'),
                                          deelgebied=k,
                                          huidige_status=v,
                                          laatste_keer_verandering=time.time(),
                                          eerst_status=v)
            elif status_records[k].huidige_status != v:
                oude_status_record = status_records[k]
                if v == 'groen':
                    status_record = StatusRecords(aantal_keer_rood=oude_status_record.aantal_keer_rood,
                                              aantal_keer_oranje=oude_status_record.aantal_keer_oranje,
                                              aantal_keer_groen=oude_status_record.aantal_keer_groen + 1,
                                              deelgebied=k,
                                              huidige_status=v,
                                              laatste_keer_verandering=time.time(),
                                              eerst_status=oude_status_record.eerst_status)
                if v == 'oranje':
                    status_record = StatusRecords(aantal_keer_rood=oude_status_record.aantal_keer_rood,
                                              aantal_keer_oranje=oude_status_record.aantal_keer_oranje + 1,
                                              aantal_keer_groen=oude_status_record.aantal_keer_groen,
                                              deelgebied=k,
                                              huidige_status=v,
                                              laatste_keer_verandering=time.time(),
                                              eerst_status=oude_status_record.eerst_status)
                if v == 'rood':
                    status_record = StatusRecords(aantal_keer_rood=oude_status_record.aantal_keer_rood + 1,
                                              aantal_keer_oranje=oude_status_record.aantal_keer_oranje,
                                              aantal_keer_groen=oude_status_record.aantal_keer_groen,
                                              deelgebied=k,
                                              huidige_status=v,
                                              laatste_keer_verandering=time.time(),
                                              eerst_status=oude_status_record.eerst_status)
            if status_record is not None:
                status_records[k] = status_record
        return True
    except:
        return False


class Chat(object):
    def __init__(self, bot, chat_id):
        self.chat_id = chat_id
        self.bot = bot


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
        self.micky_api = ma.MickyApi()

    def to_tuple(self):
        return self.chat_id, self.deelgebied

    def update(self):
        if self.deelgebied != 'All':
            team = self.deelgebied[0].lower()
            temp = self.micky_api.get_last_vos(team)
            if temp != self.last_update_micky:
                self.jh_bot.bot.sendMessage(self.chat_id, "Er is een nieuwe hint voor " + self.deelgebied
                                                + " ingevoerd.\n" + 'Dit is een hint van ' + str(temp['datetime'][11:]))  # TODO moet dit naar x minuten geleden?
                self.jh_bot.bot.sendLocation(self.chat_id, latitude=float(temp['latitude']),
                                                 longitude=float(temp['longitude']))
                self.jh_bot.bot.sendMessage(self.chat_id,
                                            'zie deze hint op de kaart: ' + map_url + '?' + 'gebied=' +
                                                self.deelgebied[0].upper())
                self.last_update_micky = temp
            self.status.update()
            for deelgebied in [d for d in self.status.get_updated() if d == self.deelgebied[0].lower()]:
                self.jh_bot.bot.sendMessage(self.chat_id, 'Er is een status-update voor ' +
                                            get_deelgebied(deelgebied[0].upper())+'.\n' +
                                            'de nieuwe status voor ' + get_deelgebied(deelgebied[0].upper()) + ' = ' +
                                            self.status[deelgebied])
                if status_plaatjes[deelgebied[0].lower()][self.status[deelgebied].lower()]['type'] == 'photo':
                    self.jh_bot.bot.sendPhoto(self.chat_id, status_plaatjes[deelgebied[0].lower()][self.status[deelgebied].lower()]['file_id'])
                if status_plaatjes[deelgebied[0].lower()][self.status[deelgebied].lower()]['type'] == 'sticker':
                    self.jh_bot.bot.sendSticker(self.chat_id, status_plaatjes[deelgebied[0].lower()][self.status[deelgebied].lower()]['file_id'])


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

    def update_hints(self):

        try:
            r = requests.get('http://jotihunt.net/api/1.0/hint')
            r.json()
        except:
            mockresponse=namedtuple('mockresponse',['status_code'])
            r = mockresponse(status_code=404)
            r.status_code = 404
        if r.status_code == 404 or'error' in r.json().keys() and self.errors['hints'] != r.json()['error']:
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
            if opdracht.id in skip_reminder:
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
            mockresponse=namedtuple('mockresponse', ['status_code'])
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
            mockresponse=namedtuple('mockresponse', ['status_code'])
            r = mockresponse(status_code=404)
            r.status_code = 404
        if r.status_code == 404 or 'error' in r.json().keys() and self.errors['nieuws'] != r.json()['error']:
            nieuws= []
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
        self.opdracht_reminders()


def convert_tijden(waarde, eenheid='seconden'):
    if eenheid in ['seconden', 's', 'seconds', 'second', 'seconde']:
        return waarde
    if eenheid in ['minuten', 'm', 'minutes', 'minuut', 'minute']:
        return convert_tijden(waarde * 60, 'seconden')
    if eenheid in ['uur', 'u', 'hour', 'uren', 'hours', 'h']:
        return convert_tijden(waarde * 60, 'minuten')
    if eenheid in ['dagen', 'd', 'days', 'dag', 'day']:
        return convert_tijden(waarde * 24, 'uur')



def command_botan_wrapper(func):
        @functools.wraps
        def command_inner(self,*args, **kwargs):
            r = func(*args, **kwargs)
            botan.track(token=self.botankey, uid=self.bot.id, message=r)
        command_inner.__name__ = func.__name__
        command_inner.__doc__ = func.__doc__
        return command_inner

class JotihuntBot(command_handler.CommandHandlerWithHelpAndFather):
    def __init__(self, token=tokens.telegramtoken, reset_old_messages=True,
                 botankey=tokens.botankey):
        self.token = token
        self.botankey = botankey
        self.bot = telegram.Bot(token=self.token)
        super(JotihuntBot, self).__init__(self.bot)
        self.known_updates = set()
        self._in_chats_ids = set()
        self._chats_in_file = set()
        self.chats = []
        self.command_42 = 42
        self.groeps_chat = None
        self.users_in_groeps_chat = []
        self.offset = 0
        self.isValidCommand = self.authenticate
        self.number_of_updates = 0
        self._not_authorized_message = 'Je bent geen admin daardoor kun je geen commandos uitvoeren in groepsapps.\n' + 'Je kunt de bot wel hier gebruiken telegram.me/' + self.bot.username
        sih = ['command_help_oud', 'command_servertemp', 'command_kill', 'command_set_group', 'command_del_sticker',
               'command_add_stickers', 'command_del_admin', 'command_add_admin', 'command_test', 'command_foto_info',
               'command_opdracht_klaar', 'command_opdracht_toch_niet_klaar']
        for temp in self.skip_in_help:
            sih.append(temp)
        self.skip_in_help = sih
        self._help_title = 'Welkom bij de Jotihunt bot van de Rhedense Pioniers.'
        self._help_list_title = 'Deze comando\'s kun je uitvoeren.'
        self._help_before_list = """Welkom bij de Jotihunt bot van de Rhedense Pioniers.

            Deze bot  kan updates van de jotihuntsite en rp-site in de gaten houden. Ook kan de bot je informatie geven.

            Omdat het niet de bedoeling is dat je in de groepsapp loopt te spammen kun je geen commando's sturen in groepsapps."""
        self._help_after_list = """
            Is er een bug of fout, iets onduidelijk enof zou je volgend jaar iets nieuws willen zien?
            Laat het ons dan weten. Dit kun je doen door je bericht aan de bot te starten met /bug.

            !! Krijg je geen antwoord van de bot stuur dan meteen een berichtje naar telegram.me/njittam !!"""
        if reset_old_messages:
            self.set_old_updates()
        else:
            for update in self.bot.getUpdates(offset=self.offset):
                self.in_chats_ids.add(update.message.chat.id)
                self.offset = update.update_id + 1
                self.number_of_updates += 1
            self.send_message_to_all('excuses voor de spam maar alle voorgaande berichten werden opnieuw ingeladen')

    def authenticate(self, update):
        chat_id = utils.get_chat_id(update)
        try:
            username = utils.get_username(update)
        except:
            username = None
        first_name = utils.get_first_name(update)
        try:
            command = utils.get_command(update)
            logger(command[0])
        except:
            command = ['/error']
        if command[0] in ['/updates','/u'] and username not in admins:
            return False
        if chat_id < 0:
            if command[0] == '/addme':
                return True
            if username in admins:
                return True
        else:
            if username in admins:
                return True
            if RP_addme_groepschat is None:
                return True
            elif first_name in known_users:
                return True
        return False



    @property
    def in_chats_ids(self):
        f = open('chat_ids.txt', 'a')
        for id in self._in_chats_ids:
            if id not in self._chats_in_file:
                f.write(str(id) + '\n')
                self._chats_in_file.add(id)
        f.close()
        return self._in_chats_ids

    @in_chats_ids.setter
    def in_chats_ids(self, s):
        f = open('chat_ids.txt', 'r')
        for id in f.readlines():
            self._chats_in_file.add(id)
            self._in_chats_ids.add(id)
        f.close()
        for i in s:
            self._in_chats_ids.add(i)
        logger(self.in_chats_ids)

    def set_old_updates(self):
            for update in self.bot.getUpdates(self.offset):
                self.known_updates.add(update.update_id)
                self.in_chats_ids.add(update.message.chat.id)
                self.chats.append(Chat(self, update.message.chat.id))
                self.offset = update.update_id + 1
                self.number_of_updates += 1

    def new_command_generator(self):
        for update in self.bot.getUpdates(offset=self.offset):
            if update.update_id not in self.known_updates:
                if update.message.text != '' and update.message.text[0] == '/':
                    yield update
                    self.known_updates.add(update.update_id)
                    self.in_chats_ids.add(update.message.chat.id)
            self.offset = update.update_id + 1
            self.number_of_updates += 1

    def send_message_to_all(self, text_message):
        for id in self.in_chats_ids:
            self.bot.sendMessage(id, text_message)

    def send_location_to_all(self, lat, lon):
        for id in self.in_chats_ids:
            self.bot.sendLocation(id, lat, lon)

        #if self.groeps_chat is None and command[0] != '/setgroep':
        #    self.bot.sendMessage(chat_id,
        #                         "de groepsapp is nog niet ingesteld. Dit kan gedaan worden door /setgroep te typen in de algemene groep van de RP.", reply_to_message_id=update.message.message_id)
        #if self.groeps_chat is not None and first_name not in self.users_in_groeps_chat:
        #    if command[0] == '/addme' and chat_id == self.groeps_chat:
        #        self.users_in_groeps_chat.append(first_name)
        #        self.bot.sendMessage(chat_id, "je bent toegevoegd in de lijst met bekende gebruikers", reply_to_message_id=update.message.message_id)
        #        return
        #    else:
        #        self.bot.sendMessage(chat_id, "je bent nog niet geverifiërd. dit kun je doen door /addme te typen in de groepsapp van de rp", reply_to_message_id=update.message.message_id)
        #        return
    def command_thema(self, update):
        'wat was het thema ook al weer?'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        api=ma.MickyApi()
        message=api.get_meta()["THEMA"]
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        return self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_admins(self,update):
        'laat alle admins zien.'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        message = "admins:\n"
        for admin in admins:
            message += admin + '\n'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        return self.bot.sendMessage(chat_id, str(message),
                                    reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_opdrachten_die_klaar_zijn(self, update):
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        message = 'opdrachten waar geen reminders voor worden gegeven.\n'
        for opdracht in skip_reminder:
            message += 'http://jotihunt.net/bericht/?MID=' + opdracht
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        return self.bot.sendMessage(chat_id, str(message),
                                    reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_opdracht_toch_niet_klaar(self, update):
        'zet reminders voor een opdracht aan'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        if username not in admins:
                message = 'Je bent geen admin dus je kunt dit commando niet uitvoeren.'
        elif len(command) == 1:
            message = 'Je moet het id van de opdracht meegeven dit is wat achter MID= staat in de url.'
        elif len (command) == 2:
            url ='http://jotihunt.net/bericht/?MID=' + str(command[1])
            try:
                r = requests.get(url)
            except:
                mockresponse=namedtuple('mockresponse',['status_code'])
                r = mockresponse(status_code=404)
                r.status_code = 404
            if r.status_code == 200:
                try:
                    skip_reminder.remove(command[1])
                    message = 'reminders voor ' + str(url) + ' staan nu weer aan.'
                except:
                    message = str(url) + ' reminders voor deze opdracht werden al gegeven.'
            else:
                message = url + ' deze link is niet bereikbaar. \n Is ' + str(command[1]) + ' wel een id van een opdracht?'
        else:
            message = 'te veel argumenten meegegeven.'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        return self.bot.sendMessage(chat_id, str(message),
                                    reply_to_message_id=update.message.message_id, reply_markup=reply_markup)


    def command_opdracht_klaar(self, update):
        'zet reminders voor een oprdracht uit.'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        if username not in admins:
            message = 'Je bent geen admin dus je kunt dit commando niet uitvoeren.'
        elif len(command) == 1:
            message = 'Je moet het id van de opdracht meegeven dit is wat achter MID= staat in de url.'
        elif len(command) == 2:
            url ='http://jotihunt.net/bericht/?MID=' + str(command[1])
            try:
                r = requests.get(url)
            except:
                mockresponse=namedtuple('mockresponse', ['status_code'])
                r = mockresponse(status_code=404)
                r.status_code = 404
            if r.status_code == 200:
                skip_reminder.add(command[1])
                message = 'reminders voor ' + url + ' staat uit.'
            else:
                message = url + ' deze link is niet bereikbaar. Is ' + url + ' wel een id van een opdracht?'
        else:
            message = 'te veel argumenten meegegeven.'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        return self.bot.sendMessage(chat_id, str(message),
                                    reply_to_message_id=update.message.message_id, reply_markup=reply_markup)


    def command_rp_site(self, update):
        'Een link naar de RP JH site met onder andere de kaart'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        api=ma.MickyApi()
        message=api.get_meta()["URL"]
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        return self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_statusinfo(self, update):
        'Geeft informatie over hoevaak een vos offline is geweest. Begint met tellen om 12 uur. de eerste en de huidige status worden ook meegeteld.'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        if len(command) == 1:
            deelgebieden = ['A', 'B', 'C', 'D', 'E', 'F']
            keyboard = [['/statusinfo ' + get_deelgebied(dg)] for dg in deelgebieden]
            reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
            message = "Welke Vos?"
        elif len(command) == 2:
            if get_deelgebied(command[1]) is not None:
                if get_deelgebied(command[1]) in status_records.keys():
                    message = ''
                    status_record = status_records[get_deelgebied(command[1])]
                    message += 'deelgebied =\t' + status_record.deelgebied + '\n'
                    message += 'huidige status =\t' + status_record.huidige_status + '\n'
                    message += 'tijd sinds laatste verandering =\t' +str(round((time.time() - status_record.laatste_keer_verandering) / 60)) + ' minuten\n'
                    message += 'status om 12 uur was (wordt ook meegeteld) =' + status_record.eerst_status + '\n'
                    message += 'aantal keer groen=\t' + str(status_record.aantal_keer_groen) + '\n'
                    message += 'aantal keer oranje =\t' + str(status_record.aantal_keer_oranje) + '\n'
                    message += 'aantal keer rood =\t' + str(status_record.aantal_keer_rood) + '\n'


                else:
                    message = 'geen records van dit deelgebied.'
            else:
                message = 'argument is geen deelgebied.'
        else:
            message='teveel argumenten ingevoerd'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        return self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_waaris(self, update):
        'Geeft de laatste bekende locatie terug van een hunter.'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        api = ma.MickyApi()
        hunter_namen = [hunter['gebruiker'] for hunter in api.get_hunter_namen()]
        if len(command) == 1:
            keyboard = [['/waaris ' + hunter] for hunter in hunter_namen]
            if keyboard != [[]] and keyboard != []:
                reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                message = "Wie?"
            else:
                message = 'Er zin geen hunters die de app aan hebben.'
        elif len(command) == 2:
            if chat_id > 0:
                if command[1] in hunter_namen:
                    tail = api.get_tail(command[1])[command[1]]
                    last_loc = sorted(tail, key=lambda x: int(x['id']), reverse=True)[0]
                    self.bot.sendLocation(chat_id, latitude=last_loc['latitude'], longitude=last_loc['longitude'])
                    message = 'Dit is de locatie van: ' + command[1]
                else:
                    message = command[1] + ' Heeft geen locaties ingestuurd afgelopen uur.'
            else:
                message = 'Dit commando kan niet worden uitgevoerd in groepschats'
        else:
            message = 'Te veel argumenten meegegeven.'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        return self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_status(self, update):
        'Zie de huidige status van alle vossen.'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        if chat_id < 0:
            message = 'Dit commando kan niet worden uitgevoerd in een groepschat.'
        else:
            if len(command) != 1:
                message = self.get_status(command[1:])
            else:
                message = self.get_status()
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        return self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_del_sticker(self, update):
        'Admins only! Verwijder de sticker die meegezonden wordt tijdens een statusupdate. De updates komen nu alleen binnen via text.'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        if username not in admins:
            message = 'Je moet admin zijn om dit te kunnen doen.'
        elif chat_id < 0:
            message = 'Je kunt dit commando niet uitvoeren in groepschats'
        else:
            if len(command) == 1:
                keyboard = [['/delsticker ' + get_deelgebied(d)] for d in ['A', 'B', 'C', 'D', 'E', 'F']]
                reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                message = ' Welk Deelgebied?'
            elif len(command) == 2:
                keyboard = [['/delsticker ' + command[1] + ' ' + s] for s in ['rood', 'oranje', 'groen']]
                reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                message = ' Welke status?'
            elif len(command) == 3:
                if get_deelgebied(command[1]) is None:
                    message = '1e argument moe een deelgebied zijn.'
                elif command[2] not in ['rood', 'oranje', 'groen']:
                    message = '2e argument moet een status zijn.'
                else:
                    status_plaatjes[command[1][0].lower()][command[2].lower()]['type'] = None
                    status_plaatjes[command[1][0].lower()][command[2].lower()]['file_id'] = None
                    message = 'Sticker of afbeelding verwijderd voor: {deelgebied} {status}'.format(
                        deelgebied=get_deelgebied(command[1]), status=command[2])
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)
    def command_foto_info(self, update):
        'is nog niet geimplementeerd'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        message = 'nog niet geimplementeerd'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_help_oud(self, update):
        'de oude helpfile'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        message = """Welkom bij de Jotihunt bot van de Rhedense Pioniers.

            Deze bot  kan updates van de jotihuntsite en rp-site in de gaten houden.
            Ook kan ik je informatie geven.

            Omdat het niet de bedoeling is dat je in de groepsapp loopt te spammen kun je geen commando's sturen in groepsapps.""" + """

            Is er een bug of fout, iets onduidelijk enof zou je volgend jaar iets nieuws willen zien?
            Laat het ons dan weten. Dit kun je doen door je bericht aan de bot te starten met /bug.

            !! Krijg je geen antwoord van de bot stuur dan meteen een berichtje naar telegram.me/njittam !!""" + """

            Je kunt de volgende commando's uitvoeren:
              * /help - laat deze text zien.
              * /update, /updates, ,/u - zeg voor welk deelgebied je updates aan of uit wil zetten. Dit heeft een automatisch menu.
              * /scoutinggroup, /sc - krijg de locatie van een deelgebied. Dit heeft een automatisch menu.
              * /addme - (doet nu nog niks ook al krijg je een reactie van de bot.)
              * /bug - Stuur je bug of feature request. voor app, site, bot of iets anders.

              Voor admins:
              * /addadmin - geef een username mee. (gebruiker moet er dus 1 hebben)
              * /deladmin
              * /setgroup - (doet nu nog niks ook al krijg je een reactie van de bot.)
              * /addsticker - stel sticker in dat wordt meeverzonden bij een status-update
              * /delsticker -

            """
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_bug(self, update):
        'Stuur je bug of feature request. voor app, site, bot of iets anders.'
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        first_name = utils.get_first_name(update)
        message, reply_markup = 'This is the default response.', None
        if len(command) == 1:
            message = 'Je hebt niet verteld wat de bug was. begin je bericht met /bug en vertel daarna in hetzelfde bericht wat er beter kan.'
            if reply_markup is None:
                reply_markup = telegram.ReplyKeyboardHide()
            self.bot.sendMessage(chat_id, str(message),
                                 reply_to_message_id=update.message.message_id, reply_markup=reply_markup)
            return
        try:
            f = open('bugs.txt', 'a')
        except Exception as e:
            self.bot.sendMessage(chat_id, 'Er is een fout opgetreden probeer het later opnieuw.')
            raise e
        try:
            for _ in range(80):
                f.write('=')
            f.write('\n')
            f.write('Username: ')
            f.write(username + '\n')
            f. write('First_name: ')
            f.write(first_name + '\n')
            f.write("Uts: " + str(time.time())+'\n')
            for _ in range(80):
                f.write('=')
            f.write('\n')
            f.write(update.message.text)
            f.write('\n')
            for _ in range(80):
                f.write('*')
            f.write('\n')
        except Exception as e:
            self.bot.sendMessage(chat_id, 'Er is een fout opgetreden probeer het later opnieuw')
            raise e
        finally:
            f.close()
        message = 'bug of aanvraag voor feature is verzonden(als er geen errors waren).  We gaan kijken of het volgend jaar erin gebouwdkan worden.'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_kill(self, update):
        'ehm...'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        first_name = utils.get_first_name(update)
        if len(command) != 1 and command[1] == '@e':
            message = "everybody is dead now"
        elif len(command) != 1:
            message = command[1] + " is dead now"
        else:
            message = "you're dead now"
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_del_admin(self, update):
        'Admins only! verwijder een admin.(dit kan jijzelf niet zijn)'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        first_name = utils.get_first_name(update)
        if username not in admins:
            message = 'je moet admin zijn om een admin te verwijderen.'
        elif len(command) != 2 or type(command[1]) != str:
            message = 'je moet een gebruikersnaam meegeven en meer hoeft ook niet'
        elif command[1] == username:
            'Je kunt je zelf niet on-admin-en. Je bent nog steeds admin.'
        elif command[1] not in admins:
            message = command[1] + ' is geen admin.'
        else:
            admins.remove(command[1])
            message = command[1] + ' is verwijderd uit de de admin lijst.'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_add_admin(self, update):
        'Admins only! voeg een admin toe.'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        first_name = utils.get_first_name(update)
        if username not in admins:
            message = 'je moet admin zijn om een admin toe te voegen.'
        elif len(command) != 2 or type(command[1]) != str:
            message = 'je moet een gebruikersnaam meegeven'
        else:
            admins.add(command[1])
            message = command[1] + ' is toegevoegd aan de admin lijst.'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_add_stickers(self, update):
        'Admins only! verander het plaatje dat meegegeven tijden status-updates'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        first_name = utils.get_first_name(update)
        if username not in admins:
            message = 'Je moet admin zijn om dit te kunnen doen.'
        elif chat_id < 0:
            message = 'Je kunt dit commando niet uitvoeren in groepschats'
        else:
            if len(command) == 1:
                keyboard = [['/addsticker ' + get_deelgebied(d)] for d in ['A', 'B', 'C', 'D', 'E', 'F']]
                reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                message = ' Welk Deelgebied?'
            elif len(command) == 2:
                keyboard = [['/addsticker ' + command[1] + ' ' + s] for s in ['rood', 'oranje', 'groen']]
                reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                message = ' Welke status?'
            elif len(command) == 3:
                if get_deelgebied(command[1]) is None:
                    message = '1e argument moe een deelgebied zijn.'
                elif command[2] not in ['rood', 'oranje','groen']:
                    message = '2e argument moet een status zijn.'
                else:
                    reply_markup = telegram.ReplyKeyboardHide()
                    self.bot.sendMessage(chat_id,
                                         'Zend je afbeelding of sticker binnen 2 minuten (korter als de server druk is) die mee moet worden gezonden bij een status-update.',
                                         reply_markup=reply_markup)
                    b = True
                    start_time = time.time()
                    u_ids = []
                    while b:
                        updates = self.bot.getUpdates()
                        if len(updates) == 100 or time.time() - start_time > 120:
                            b = False
                            self.bot.sendMessage(chat_id, ' \'t duurde te lang dus er wordt niet meer geluiterd.')
                        else:
                            for u in updates:
                                if u.update_id not in u_ids:
                                    u_ids.append(u.update_id)
                                    if u.message.chat.id == chat_id:
                                        if 'sticker' in u.message.to_dict().keys():
                                            logger(u.message.sticker)
                                            status_plaatjes[command[1][0].lower()][command[2].lower()]['type'] = 'sticker'
                                            status_plaatjes[command[1][0].lower()][command[2].lower()]['file_id'] = u.message.sticker.file_id
                                            b = False
                                            message = ' Sticker wordt nu verzonden bij een status-update.'
                                        elif 'photo' in u.message.to_dict().keys():
                                            status_plaatjes[command[1][0].lower()][command[2].lower()]['type'] = 'photo'
                                            status_plaatjes[command[1][0].lower()][command[2].lower()]['file_id'] = u.message.photo[0].file_id
                                            b = False
                                            message = ' Foto wordt nu verzonden bij een status-update.'
                                        else:
                                            message = 'Het vorige bericht was geen sticker.'
                                        logger(status_plaatjes)
            else:
                message = ' error: Te veel argumenten.'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_scouting_groep_per_dg(self, update):
        'Sorteer scoutinggroep per deelgebied'
        deelgebied_key_in_api = 'deelgebied' # TODO remove this als micky het geimplementeerd heeft.
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        first_name = utils.get_first_name(update)
        api = ma.MickyApi()
        scouting_groepen = api.get_all_scouting_groepen()
        if len(command) == 1:
            if chat_id > 0:
                keyboard = [[x] for x in sorted(set('/scouting_groep_per_dg ' + get_deelgebied(x[deelgebied_key_in_api]) for x in scouting_groepen))]
                reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                message = "Welke deelgebied?"
            else:
                message = ' Dit commando werkt niet in groepsgesprekken.'
        elif len(command) == 2:
            if chat_id > 0:
                deelgebied = get_deelgebied(command[1])
                if deelgebied is not None:
                    groepen_in_deelgebied = [sc for sc in scouting_groepen if get_deelgebied(sc[deelgebied_key_in_api]) == get_deelgebied(command[1])]
                    keyboard = [['/scouting_groep ' + x['naam']] for x in groepen_in_deelgebied]
                    reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                    message = "Welke deelgebied?"
                else:
                    message = 'argument {argument} is geen deelgebied.'.format(argument=command[1])
            else:
                message = ' Dit commando werkt niet in groepsgesprekken.'

        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_scouting_groep(self, update):
        'Laat de locatie van een scoutingroep zien. Dit heeft een automatisch menu.'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        first_name = utils.get_first_name(update)
        api = ma.MickyApi()
        if len(command) == 1:
            if chat_id > 0:
                keyboard = [['/scouting_groep ' + x['naam']] for x in api.get_all_scouting_groepen()]
                reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                message = "Welke scoutinggroep?"
            else:
                message = ' je moet een scoutinggroep meegeven'
        else:
            sg = command[1]
            for w in command[2:]:
                sg += ' ' + w

            sgl = [sc for sc in api.get_all_scouting_groepen() if sc['naam'] == sg]
            if sgl:
                self.bot.sendLocation(chat_id, float(sgl[0]['latitude']), float(sgl[0]['longitude']),
                                      reply_to_message_id=update.message.message_id)
                message = ' dit is de locatie van ' + sg
            else:
                message = sg + ' is geen scouting groep.'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_u(self, update):
        'zelfde als /updates'
        return self.command_updates(update)

    def command_updates(self, update):
        'zeg voor welk deelgebied je updates aan of uit wil zetten. Dit heeft een automatisch menu.'
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        first_name = utils.get_first_name(update)
        if chat_id > 0:
            if len(command) == 1:
                keyboard = [['/updates ' + x] for x in ['aan', 'uit', 'show']]
                reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                message = "updates voor een deelgebied aan of uit zetten? of wil je weten voor welke deelgebieden updates aanstaan?"
            elif len(command) == 2:
                if command[1] == 'show':
                    logger([u.to_tuple() for u in known_updates])
                    l = [u for u in update_list if u.to_tuple()[0] == chat_id]
                    logger(l)
                    message = 'updates staan aan voor: \n'
                    for u in l:
                        message += str(u.deelgebied) + '\n'
                    if not l:
                        message += ' geen deelgebieden'
                elif command[1] in ['aan','uit']:
                    keyboard = [['/updates ' + str(command[1]) + ' ' + str(x)] for x in ['Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'HB', 'All']]
                    reply_markup = telegram.ReplyKeyboardMarkup(keyboard)
                    message = "voor welk deelgebied wil je updates " + command[1] + ' zetten?'
                else:
                    message = 'geen aan of uit gevonden in de argumenten'
            else:
                message = str(self.add_update(command, chat_id))
        else:
            if 'aan' in command or 'uit' in command:
                    message = str(self.add_update(command, chat_id))
            elif len(command) == 2:
                if command[1] == 'show':
                    logger([u.to_tuple() for u in known_updates])
                    l = [u for u in update_list if u.to_tuple()[0] == chat_id]
                    logger(l)
                    message = 'updates staan aan voor\n'
                    for u in l:
                        message += str(u.deelgebied) + '\n'
                    if not l:
                        message += ' geen deelgebieden'
            elif len(command) == 1:
                logger([u.to_tuple() for u in known_updates])
                l = [u for u in update_list if u.to_tuple()[0] == chat_id]
                logger(l)
                message = 'updates staan aan voor\n'
                for u in l:
                    message += str(u.deelgebied) + '\n'
                if not l:
                    message += ' geen deelgebieden'
            else:
                message = 'aan of uit niet gevonden in de argumenten'
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_set_group(self, update):
        'Admins only! Deze functie doet momenteel niks. '
        return
        message, reply_markup = 'This is the default response.', None
        chat_id = utils.get_chat_id(update)
        command = utils.get_command(update)
        username = utils.get_username(update)
        first_name = utils.get_first_name(update)
        if chat_id > 0:
            message = "je zit niet in een groepsapp dus je kunt dit niet uitvoeren"
        else:
            self.groeps_chat = chat_id
            message = "de groepsapp is gewijzigd!"
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, str(message),
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def command_test(self, update):
        'check of de server online is.'
        chat_id = utils.get_chat_id(update)
        self.bot.sendMessage(chat_id, 'De server is online!!')

    def command_servertemp(self, update):
        'Als de server een rpi is krijg je de temp terug.'
        message, reply_markup = 'This is the default response.', None
        try:
            r = subprocess.check_output(['/opt/vc/bin/vcgencmd', 'measure_temp'])
        except:
            message = 'De server is geen raspberry pi\n'
        else:
            message = r
        chat_id = utils.get_chat_id(update)
        if reply_markup is None:
            reply_markup = telegram.ReplyKeyboardHide()
        self.bot.sendMessage(chat_id, message,
                             reply_to_message_id=update.message.message_id, reply_markup=reply_markup)

    def add_update(self, command, chat_id):
        u = [su.to_tuple() for su in update_list]
        deelgebieden = ['A', 'B', 'C', 'D', 'E', 'F', 'HB']
        if 'aan' in command and 'uit' in command:
            return "ehm, aan of uit? beide gaat niet lukken."
        elif len(command) > 3:
            return "meerdere deelgebieden tegelijk selecteren is nog niet ondersteund"
        elif 'aan' in command:
            if len(command) == 2 or 'All' in command:
                l = [(chat_id, get_deelgebied(d)) for d in deelgebieden if
                     (chat_id, get_deelgebied(d)) not in [u.to_tuple() for u in update_list]]
                if not l:
                    return "updates voor alle deelgebieden stonden al aan in deze chat"
                else:
                    for t in l:
                        if t[1] == get_deelgebied('HB'):
                            update_list.append(HBUpdates(self, t[0], deelgebied=get_deelgebied(t[1])))
                        else:
                            update_list.append(ScanUpdates(self, t[0], deelgebied=get_deelgebied(t[1])))
                return "updates voor alle deelgebieden staan in deze chat aan"
            if len(command) == 3:
                if get_deelgebied(command[2]) is not None:
                    if (chat_id, get_deelgebied(command[2])) in u:
                        return "updates voor " + get_deelgebied(command[2]) +" stonden al aan in deze chat"
                    if command[2] == get_deelgebied('HB'):
                        update_list.append(HBUpdates(self, chat_id, deelgebied=get_deelgebied(command[2])))
                    else:
                        update_list.append(ScanUpdates(self, chat_id, deelgebied=get_deelgebied(command[2])))
                    return "updates voor " + get_deelgebied(command[2]) + " staan in deze chat aan"
                elif get_deelgebied(command[1]) is not None:
                    if (chat_id, get_deelgebied(command[1])) in u:
                        return "updates voor " + get_deelgebied(command[1]) +" stonden al aan in deze chat"
                    if command[1] == get_deelgebied('HB'):
                        update_list.append(HBUpdates(self, chat_id, deelgebied=get_deelgebied(command[1])))
                    else:
                        update_list.append(ScanUpdates(self, chat_id, deelgebied=get_deelgebied(command[1])))
                    return "updates voor " + get_deelgebied(command[1]) + " staan in deze chat aan"
                else:
                    return "deelgebied niet begrepen."

        if 'uit' in command:
            if len(command) == 2 or 'All' in command:
                l = [u for u in update_list if u.to_tuple() in [(chat_id, get_deelgebied(d)) for d in deelgebieden]]
                if not l:
                    return "er stonden geen updates aan in deze chat."
                else:
                    for u in l:
                        update_list.remove(u)
                    return "Updates voor alle deelgebieden staan uit in deze chat."
            if len(command) == 3:
                if get_deelgebied(command[2]) is not None:
                    l = [u for u in update_list if u.to_tuple() == (chat_id, get_deelgebied(command[2]))]
                    if not l:
                        return "updates stonden niet aan voor " + get_deelgebied(command[2]) + " in deze chat."
                    else:
                        for u in l:
                            update_list.remove(u)
                        return "Updates voor " + get_deelgebied(command[2]) + " staan uit in deze chat."
                elif get_deelgebied(command[1]) is not None:
                    l = [u for u in update_list if u.to_tuple() == (chat_id, get_deelgebied(command[1]))]
                    if not l:
                        return "updates stonden niet aan voor " + get_deelgebied(command[1]) + " in deze chat."
                    else:
                        for u in l:
                            update_list.remove(u)
                        return "Updates voor " + get_deelgebied(command[2]) + " staan uit in deze chat."
                else:
                    return "deelgebied niet begrepen."

    def get_status(self, *deelgebied):
        try:
            r = requests.get('http://jotihunt.net/api/1.0/vossen')
            r.json()
        except:
            mockresponse=namedtuple('mockresponse', ['status_code'])
            r = mockresponse(status_code=404)
            r.status_code = 404
        s = 'deelgebied:\tstatus\n'
        if r.status_code == 404 or 'error' in r.json().keys():
            s += 'error:\t\t' + r.json()['error'] + '\n'
        data = {}
        if r.status_code != 404 and 'data' in r.json().keys():
            data2 = r.json()['data']
            for dgb in data2:
                data[dgb['team'].lower()] = dgb['status']
        logger(data)
        if len(deelgebied) == 0:
            deelgebied = ('Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot')
        if one_of_in(['Alpha', 'alpha', 'A', 'a'], deelgebied) and 'alpha' in data.keys():
            s += ' Alpha:\t' + data['alpha'] + '\n'
        if one_of_in(['Bravo', 'bravo', 'B', 'b'], deelgebied) and 'bravo' in data.keys():
            s += ' Bravo:\t' + data['bravo'] + '\n'
        if one_of_in(['charlie', 'Charlie', 'C', 'c'], deelgebied) and 'charlie' in data.keys():
            s += ' Charlie:\t' + data['charlie'] + '\n'
        if one_of_in(['Delta', 'delta', 'D', 'd'], deelgebied) and 'delta' in data.keys():
            s += ' Delta:\t' + data['delta'] + '\n'
        if one_of_in(['Echo', 'echo', 'E', 'e'], deelgebied) and 'echo' in data.keys():
            s += ' Echo:\t' + data['echo'] + '\n'
        if one_of_in(['Foxtrot', 'foxtrot', 'F', 'f'], deelgebied) and 'foxtrot' in data.keys():
            s += ' Foxtrot:\t' + data['foxtrot'] + '\n'
        return s


def to_tuple(update):
    try:
        return update.message.chat.id, update.message.text
    except:
        return random.choice(range(200)), 'kon geen tuple maken'


def get_deelgebied(deelgebied):
    if one_of_in(['Home', 'Base', 'hb', 'HB', 'hq', 'HQ'], deelgebied):
        return 'HB'
    elif one_of_in(['Alpha', 'alpha', 'A'], deelgebied):
        return 'Alpha'
    elif one_of_in(['Bravo', 'bravo', 'B'], deelgebied):
        return 'Bravo'
    elif one_of_in(['Charlie', 'charlie', 'C'], deelgebied):
        return 'Charlie'
    elif one_of_in(['Delta', 'delta', 'D'], deelgebied):
        return 'Delta'
    elif one_of_in(['Echo', 'echo', 'E'], deelgebied):
        return 'Echo'
    elif one_of_in(['Foxtrot', 'foxtrot', 'F'], deelgebied):
        return 'Foxtrot'
    else:
        return None


def run2(jh_bot, send_exit_message, new_thread):
    while True:
        time.sleep(0.5)
        run(jh_bot, new_thread=new_thread, send_exit_message=send_exit_message)
        # try:
        #     run(jh_bot, new_thread=new_thread, send_exit_message=send_exit_message)
        # except telegram.TelegramError as e:
        #     logger('*** Bot ging uit na tg error', e,'***')
        #     bot.bot.sendMessage(19594180, 'de bot is herstart na een telegram error.\n' + str(e))
        #     run(bot, send_exit_message=send_exit_message, new_thread=new_thread, startfrom_error=True, error=e)
        # except ma.MattijnError as e:
        #     logger('*** bot ging uit na error van api van micky' + str(e))
        #     bot.bot.sendMessage(19594180, 'de bot is herstart na een error in api van micky.\n' + str(e))
        #     run(bot, send_exit_message=send_exit_message, new_thread=new_thread, startfrom_error=True, error=e)
        # except requests.ConnectionError as e:
        #     logger('*** bot ging uit na connectionerror ' + str(e))
        #     bot.bot.sendMessage(19594180, 'de bot is herstart na een connection error.\n' + str(e))
        #     run(bot, send_exit_message=send_exit_message, new_thread=new_thread, startfrom_error=True, error=e)
        # except KeyboardInterrupt as e:
        #     logger("***bot is ging uit ", e, '**')
        #     if send_exit_message:
        #         bot.send_message_to_all('bot gaat uit, hierdoor worden alle data gewist.')
        #     # run(bot, send_exit_message=send_exit_message, new_thread=new_thread, startfrom_error=True, error=e)
        #     raise e
        # except socket.error as e:
        #     logger("*** bot is gecrashed ", e, '***')
        #     run(bot, send_exit_message=send_exit_message, new_thread=new_thread, startfrom_error=True, error=e)
        # except Exception as e:
        #     logger("***bot is gecrashed ", e, '***')
        #     if send_exit_message:
        #         bot.send_message_to_all("bot is gecrashed, hierdoor worden alle data gewist. Speciaal voor Mattijn:" + str(e))
        #     raise e
        # except:
        #     logger('unkown error')


def handle_updates_once(make_threads=True):
    if not make_threads:
        command_handler.ch_Thread = command_handler.FakeThread
    threads = {}
    for u in update_list:
        t = threading.Thread(target=u.update)
        logger('update-thread aangemaakt', u.to_tuple())
        threads[u.to_tuple()] = t
        logger('update-thread toegevoegd', u.to_tuple())
    return threads


def handle_updates(make_threads=True):
    delay = 0
    while True:
        time.sleep(60 - delay)
        delay = 0
        threads = handle_updates_once(make_threads)
        for k, t in threads.items():
                        t.start()
                        logger('update-thread is gestart', k)
        delete_threads = []
        for k, t in threads.items():
                t.join(timeout=1.5)
                if not t.isAlive():
                    logger("update-Thread" + str(k) + " stopped")
                    delete_threads.append(k)
                    logger("update-Thread has been queued for deletion: ", k)
                else:
                    logger("*** WARNING update-Thread has not stopped: ", k, '***')
        for k in delete_threads:
                del threads[k]
                logger("update-Thread has been deleted:", k)
        if threads:
                logger('update-threads remaining', threads)


def run(jh_bot, new_thread=True, first=True, send_exit_message=True, startfrom_error=False, error=None):
        if first:
            if new_thread:
                thread.start_new(jh_bot.run, ())
                logger('bot-Thread started')
                thread.start_new(handle_updates, ())
                logger('update-Thread started')
                while True:
                    update_status_records()
                    time.sleep(60)
            else:
                start_time = time.time()
                update_interval = 60
                last_update = None
                while True:

                    threads = {}
                    # print(start_time, time.time(), time.time() - start_time, update_interval)
                    if time.time() - start_time > update_interval:
                        logger('checking also for updates')
                        logger('n real_threads = ', threading.active_count())
                        start_time = time.time()
                        update_status_records()
                        for k, v in handle_updates_once(make_threads=False).items():
                            threads[k] = v
                        update_interval = time.time() - start_time
                        if update_interval < 60:
                            update_interval = 60
                        logger('new interval =', update_interval)
                        start_time = time.time()
                    r = jh_bot.run_once(make_thread=False, last_update_id=last_update)
                    last_update = r[1]
                    for k, v in r[0].items():
                        logger('commando gevonden')
                        threads[k] = v
                    for k, t in threads.items():
                        logger('starting fakethreat', k)
                        t.start()
                        logger('fakethreat done', k)

        if send_exit_message and not startfrom_error:
            bot.send_message_to_all("de bot is gestart")
        if send_exit_message and startfrom_error:
            bot.bot.sendMessage(19594180, 'de bot is herstart na een error.\n' + str(error))


if __name__ == '__main__':
    logger(
        '\n-----------------------------------------------------------------------------------------------------------')
    bot = JotihuntBot()
    logger(bot.bot.getMe())
    logger('bot created')
    run2(bot, new_thread=False, send_exit_message=True)
