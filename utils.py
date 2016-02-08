__author__ = 'mattijn'
import inspect

import random
def line_number():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno


class CommandsFaker:
    def getstatusoutput(self, *args, **kwargs):
        return (424242, 'commands python packet niet gevonden')

class Json:
    def __init__(self, json):
        self.json = json

    def __getitem__(self, item):
        if item in self.json.keys():
            return self.json[item]

    def __getattr__(self, item):
        if item in self.json.keys():
            return self.json[item]
        else:
            raise AttributeError()


def get_chat_id(update):
    return update.message.chat.id


def get_first_name(update):
    first_name = str(random.choice(range(500)))  # TODO kan dit niet de code breken na 500 keer aanroepen moet er iets 2 x gemaakt zijn.
    if 'first_name' in update.message.to_dict()['from'].keys():
        first_name = update.message.to_dict()['from']['first_name']
    return first_name


def get_username(update):
    username = "None"
    if 'username' in update.message.to_dict()['from'].keys():
        username = update.message.to_dict()['from']['username']
    return username


def get_command(update):
    command = update.message.text.split(' ')
    temp = command[0].split('@')
    command[0] = temp[0]
    return command


def logger(log, *values, **kwargs):
    try:
        f = open('logger.log', mode='a')
    except:
        print("kan logger.log niet openen.")
    import datetime
    message = log
    for v in values:
        message += ', ' + str(v)
    for k, v in kwargs.items():
        message += ', ' + str(k) + '=' + str(v)
    lineno = inspect.currentframe().f_back.f_lineno
    filename = inspect.currentframe().f_back.f_code.co_filename.split('/')[-1]
    print(filename, lineno, datetime.datetime.now(), message)

    return_mess = '{filename} {lineno} {datetime} {message}\n'.format(filename=filename, lineno=lineno,
                                                                    datetime=datetime.datetime.now(), message=message)
    try:
        f.write(return_mess)
    except:
        print('vorige log niet toegevoegd aan log.logger')
    finally:
        f.close()
    return return_mess


def one_of_in(list_a, list_b):
    for a in list_a:
        if a in list_b:
            return True
    return False

def convert_tijden(waarde, eenheid='seconden'):
    if eenheid in ['seconden', 's', 'seconds', 'second', 'seconde']:
        return waarde
    if eenheid in ['minuten', 'm', 'minutes', 'minuut', 'minute']:
        return convert_tijden(waarde * 60, 'seconden')
    if eenheid in ['uur', 'u', 'hour', 'uren', 'hours', 'h']:
        return convert_tijden(waarde * 60, 'minuten')
    if eenheid in ['dagen', 'd', 'days', 'dag', 'day']:
        return convert_tijden(waarde * 24, 'uur')

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

