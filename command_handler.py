from __future__ import print_function
from inspect import getmembers, ismethod
import threading
import logging
import telegram
import time
import functools
import botan
import random
from utils import logger

ch_Thread = threading.Thread


log = logging.getLogger(__name__)
__all__ = ['CommandHandler', 'CommandHandlerWithHelp', 'CommandHandlerWithFatherCommand',
           'CommandHandlerWithHelpAndFather']


class FakeThread:
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        self.group = group
        self.target = target
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.return_value = None
        self.started = False
        self.deamon = True
        self._ident = random.randint(1, 100)
        self._thread = self

    def f(self, x):
        return 2 * x

    def start(self):
        # self.start.__doc__ = self._thread.start.__doc__
        if not self.started:
            self.started = True
            self.return_value = self.target(*self.args, **self.kwargs)
            logger('fake_thread_started', self.target.__name__)
        else:
            raise RuntimeError()

    def run(self, *args, **kwargs):
        # self.run.__doc__ = self._thread.run.__doc__
        self.return_value = self.target(*args, **kwargs)
        return self.return_value

    def join(self, timeout=None):
        # self.join.__doc__ = self._thread.join.__doc__
        if self.started:
            pass
            # raise RuntimeError()
        return None

    def getName(self):
        # self.getName.__doc__ = self._thread.getName.__doc__
        return self.name

    def setName(self, name):
        # self.setName.__doc__ = self._thread.setName.__doc__
        self.name = name

    def ident(self):
        # self.ident.__doc__ = self._thread.ident.__doc__
        return self._ident

    def is_alive(self):
        # self.is_alive.__doc__ = self._thread.is_alive.__doc__
        return False

    def isAlive(self):
        # self.isAlive.__doc__ = self._thread.isAlive.__doc__
        return self.is_alive()

    def setDeamon(self, deamonic):
        # self.setDeamon.__doc__ = self._thread.setDaemon.__doc__
        self.deamon = deamonic

    def isDeamon(self):
        # self.isDeamon.__doc__ = self._thread.isDaemon.__doc__
        return self.deamon


def timer(dtime):
    start_time = time.time()
    while time.time() - start_time < dtime:
        yield time.time()


class CommandHandler(object):
    """ This handles incomming commands and gives an easy way to create commands.

    How to use this:
      create a new class which inherits this class or CommandHandlerWithHelp.
      define new methods that start with 'command_' and then the command_name.
      run run()
    """
    def __init__(self, bot):
        self._found_updates = False
        self._last_updates = []
        self._getupdates_can_write = []
        self._not_authorized_message = "Sorry, the command was not authorised or valid: {command}."
        self.bot = bot  # a telegram bot
        self.isValidCommand = None  # a function that returns a boolean and takes one agrument an update.
        # If False is returned the the command is not executed.

    def _get_command_func(self, command):
        if command[0] == '/':
            command = command[1:]
        if hasattr(self, 'command_' + command): # TODO what if a function doesn't exist
            func = self.__getattribute__('command_' + command)  # a function
            if callable(func):
                return func
            else:
                return None
        else:
            return None



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

    def run(self, make_thread=True, last_update_id=None, thread_timeout=2, sleep=0.2):
        """Continuously check for commands and run the according method

        Args:
          make_thread:
            if True make a thread for each command it found.
            if False make run the code linearly
          last_update:
            the offset arg from getUpdates and is kept up to date within this function
          thread_timeout:
            The timeout on a thread. If a thread is alive after this period then try to join the thread in
            the next loop.
        """

        old_threads = {}
        while True:
            time.sleep(sleep)
            threads, last_update_id = self.run_once(make_thread=make_thread, last_update_id=last_update_id)
            for k, t in threads.items():
                t.start()
            for k, t in old_threads:
                threads[k] = t
            old_threads = {}
            for k, t in threads.items():
                t.join(timeout=thread_timeout)
                if t.isAlive():
                    old_threads[k] = t

    def run_once(self, make_thread=True, last_update_id=None, update_timeout=30):
        """ Check the the messages for commands and make a Thread or FakeThread with the command depending on make_thread.

        Args:
          make_thread:
            True: the function returns a list with threads. Which didn't start yet.
            False: the function returns a list with FakeThreads. Which did'nt start yet.
          last_update_id:
            the offset arg from getUpdates and is kept up to date within this function
          update_timeout:
            timeout for updates. can be None for no timeout.

        Returns:
          A tuple of two elements. The first element is a list with Threads or FakeThreads which didn't start yet.
          The second element is the updated las_update_id
         """
        if make_thread:
            ch_Thread = threading.Thread
        else:
            ch_Thread = FakeThread
        bot_name = self.bot.username
        threads = {}
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
            if len(message.text) == 0:
                message.text = '   '
            if message.text[0] == '/':
                command, username = message.text.split(' ')[0], bot_name
                if '@' in command:
                    command, username = command.split('@')
                if username == bot_name:
                    command_func = self._get_command_func(command)
                    if command_func is not None:
                        self.bot.sendChatAction(chat_id=update.message.chat.id, action=telegram.ChatAction.TYPING)
                        if self.isValidCommand is None or self.isValidCommand(update):
                            t = ch_Thread(target=command_func, args=(update,))
                            threads[(message.text, update.message.chat.id)] = t
                        else:
                            t = ch_Thread(target=self._command_not_valid, args=(update,))
                            threads[(message.text + ' unauthorized', update.message.chat.id)] = t
                    else:
                        t = ch_Thread(target=self._command_not_found, args=(update,))
                        threads[(message.text + ' not found', update.message.chat.id)] = t
        return threads, last_update_id

    def _command_not_valid(self, update):
        """Inform the telegram user that the command was not found.

        Override this method if you want to do it another way then by sending the the text:
        Sorry, I didn't understand the command: /command[@bot].
        """
        chat_id = update.message.chat.id
        reply_to = update.message.message_id
        message = self._not_authorized_message.format(
            command=update.message.text.split(' ')[0])
        self.bot.sendMessage(chat_id=chat_id, text=message, reply_to_message_id=reply_to)

    def _command_not_found(self, update):
        """Inform the telegram user that the command was not found.

        Override this method if you want to do it another way then by sending the the text:
        Sorry, I didn't understand the command: /command[@bot].
        """
        chat_id = update.message.chat.id
        reply_to = update.message.message_id
        message = "Sorry, I didn't understand the command: {command}.".format(command=update.message.text.split(' ')[0])
        self.bot.sendMessage(chat_id=chat_id, text=message, reply_to_message_id=reply_to)


class CommandHandlerWithHelp(CommandHandler):
    """ This CommandHandler has a builtin /help. It grabs the text from the docstrings of command_ functions."""
    def __init__(self, bot):
        super(CommandHandlerWithHelp, self).__init__(bot)
        self._help_title = 'Welcome to {name}.'.format(name=self.bot.username)  # the title of help
        self._help_before_list = ''  # text with information about the bot
        self._help_after_list = ''  # a footer
        self._help_list_title = 'These are the commands:'  # the title of the list
        self._help_extra_message = 'These commands are only usefull to the developer.'
        self.is_reply = True
        self.command_start = self.command_help
        self.skip_in_help = []

    def command_helpextra(self, update):
        """ The commands in here are only usefull to the developer of the bot"""
        command_functions = [attr[1] for attr in getmembers(self, predicate=ismethod) if attr[0][:8] == 'command_' and
                             attr[0] in self.skip_in_help]
        chat_id = update.message.chat.id
        help_message = self._help_extra_message + '\n'
        for command_function in command_functions:
            if command_function.__doc__ is not None:
                help_message += '  /' + command_function.__name__[8:] + ' - ' + command_function.__doc__ + '\n'
            else:
                help_message += '  /' + command_function.__name__[8:] + ' - ' + '\n'
        self.bot.sendMessage(chat_id=chat_id, text=help_message)

    def _generate_help(self):
        """ Generate a string which can be send as a help file.

            This function generates a help file from all the docstrings from the commands.
            so docstrings of methods that start with command_ should explain what a command does and how a to use the
            command to the telegram user.
        """

        help_message = self._help_title + '\n\n'
        help_message += self._help_before_list + '\n\n'
        help_message += self._help_list_title + '\n'
        help_message += self._generate_help_list()
        help_message += '\n'
        help_message += self._help_after_list
        return help_message

    def _generate_help_list(self):
        logger('methods', [attr[0] for attr in getmembers(self, predicate=ismethod)])
        command_functions = [attr[1] for attr in getmembers(self, predicate=ismethod) if attr[0][:8] == 'command_' and
                             attr[0] not in self.skip_in_help]
        help_message = ''
        for command_function in command_functions:
            if command_function.__doc__ is not None:
                help_message += '  /' + command_function.__name__[8:] + ' - ' + command_function.__doc__ + '\n'
            else:
                help_message += '  /' + command_function.__name__[8:] + ' - ' + '\n'
        return help_message

    def _command_not_found(self, update):
        """Inform the telegram user that the command was not found."""
        chat_id = update.message.chat.id
        reply_to = update.message.message_id
        message = 'Sorry, I did not understand the command: {command}. Please see /help for all available commands'
        if self.is_reply:
            self.bot.sendMessage(chat_id=chat_id, text=message.format(command=update.message.text.split(' ')[0]),
                                 reply_to_message_id=reply_to)
        else:
            self.bot.sendMessage(chat_id=chat_id, text=message.format(command=update.message.text.split(' ')[0]))

    def command_help(self, update):
        """ The help file. """
        chat_id = update.message.chat.id
        reply_to = update.message.message_id
        message = self._generate_help()
        self.bot.sendMessage(chat_id=chat_id, text=message, reply_to_message_id=reply_to)


class CommandHandlerWithFatherCommand(CommandHandler):
    """ A class that creates some commands that are usefull when setting up the bot
    """

    def __init__(self, bot):
        super(CommandHandlerWithFatherCommand, self).__init__(bot)
        self.skip_in_help = ['command_father']

    def command_father(self, update):
        """Gives you the commands you need to setup this bot. in telegram.me/BotFather"""
        chat_id = update.message.chat.id
        self.bot.sendMessage(chat_id=chat_id, text='Send the following messages to telegram.me/BotFather')
        self.bot.sendMessage(chat_id=chat_id, text='/setcommands')
        self.bot.sendMessage(chat_id=chat_id, text='@' + self.bot.username)
        commands = ''
        command_functions = [attr[1] for attr in getmembers(self, predicate=ismethod) if attr[0][:8] == 'command_' and
                             attr[0] not in self.skip_in_help]

        for command_function in command_functions:
            if command_function.__doc__ is not None:
                commands += command_function.__name__[8:] + ' - ' + command_function.__doc__ + '\n'
            else:
                commands += command_function.__name__[8:] + ' - ' + '\n'
        self.bot.sendMessage(chat_id=chat_id, text=commands)


class CommandHandlerWithHelpAndFather(CommandHandlerWithFatherCommand, CommandHandlerWithHelp):
    """A class that combines CommandHandlerWithHelp and CommandHandlerWithFatherCommand.
    """
    pass
