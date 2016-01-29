__author__ = 'mattijn'
from utils import logger
import threading

class Observer:
    def __init__(self, bot):
        self._getupdates_can_write = []
        self._last_updates = []
        self.bot = bot

    def get_updates(self, *args, index, offset, **kwargs):
        try:
            temp = self.bot.getUpdates(*args, offset=offset, **kwargs)
        except Exception as e:
            temp = []
            logger('because an error occoured updates will be empty id:', index, type(e), e.args, e)
        if self._getupdates_can_write[index]:
            self._last_updates = temp
        else:
            logger('error get_updates done. but not able to send output.', index)
        return temp

    def scan_once(self, last_update_id, update_timeout):
        bot_name = self.bot.username
        self._getupdates_can_write.append(True)
        get_updates_index = len(self._getupdates_can_write) - 1
        get_updates_thread = threading.Thread(target=self.get_updates,
                                              kwargs={'index': get_updates_index,
                                                      'offset': last_update_id})
        get_updates_thread.start()
        get_updates_thread.join(timeout=update_timeout)
        if get_updates_thread.isAlive():
            logger('ERROR getupdates timed out, using empty list')
            self._getupdates_can_write[get_updates_index] = False
            self._last_updates = []
        updates = self._last_updates
        for update in updates:
            last_update_id = update.update_id + 1
            message = update.message
            if message.text[0] == '/':
                command, username = message.text.split(' ')[0], bot_name
                if '@' in command:
                    command, username = command.split('@')
                if username == bot_name:
                    events['on_command'].trigger(update.message)



class Event(object):
    def __init__(self):
        self.handlers = set()

    def fire(self, *args, **kwargs):
        for handler in self.handlers:
            handler(*args, **kwargs)

    def add_handler(self, handler):
        if callable(handler):
            self.handlers.add(handler)
        else:
            raise ValueError('handler is not callable')

    def remove_handler(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)
        else:
            raise KeyError('handler not in handlers')

    __iadd__ = add_handler
    __isub__ = remove_handler
    __call__ = fire
    trigger = fire

    def __len__(self):
        return len(self.handlers)

events = {'on_command': Event(),
          'on_new_chat_participant': Event(),
          'on_left_chat_participant': Event(),
          'on_new_chat_title': Event(),
          'on_new_chat_photo': Event(),
          'on_delete_chat_photo': Event(),
          'on_mentioned': Event()}
