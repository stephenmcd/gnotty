
from random import choice, randint

from gevent import sleep

from gnotty.client import BaseIRCClient


class BaseBot(BaseIRCClient):
    """
    Base bot class. Defines the log and webook methods for subclasses
    to override.
    """

    def log(self, **kwargs):
        """
        Log handler - override me.
        """
        print "[%(server)s%(channel)s] %(nickname)s: %(message)s" % kwargs

    def log_args(self, event, message, nickname=None):
        return {
            "server": self.connection.server,
            "channel": self.channel,
            "nickname": nickname or self.get_nickname(event),
            "message": message,
        }

    def message_channel(self, message):
        """
        We won't receive our own messages, so log them manually.
        """
        self.log(**self.log_args(None, message, self.nickname))
        super(BaseBot, self).message_channel(message)

    def on_join(self, connection, event):
        self.log(**self.log_args(event, "joins"))

    def on_quit(self, connection, event):
        self.log(**self.log_args(event, "leaves"))

    def on_pubmsg(self, connection, event):
        for message in event.arguments():
            self.log(**self.log_args(event, message))

    def on_webhook(self, environ):
        raise NotImplementedError


class DjangoBot(BaseBot):
    """
    Bot for Django integration that logs messages to a database.
    """

    def log(self, **kwargs):
        from gnotty.models import IRCMessage
        IRCMessage.objects.create(**kwargs)
        super(DjangoBot, self).log(**kwargs)


class ChatMixin(object):
    """
    A demo bot mixin that greets and responds to people.
    """

    def __init__(self, *args, **kwargs):
        super(ChatMixin, self).__init__(*args, **kwargs)
        self.chatbots = []
        self.greetings = ("Hi", "Hello", "Howdy", "Welcome")
        try:
            from nltk.chat import bots
        except ImportError:
            from warnings import warn
            warn("ChatMixin requires nltk installed")
        else:
            get_bot = lambda x: x[0].func_globals["%sbot" % x[0].__name__]
            self.chatbots = map(get_bot, bots)

    def message_channel_delayed(self, message):
        """
        Pause for a random few seconds before messaging, to seem less
        bot like.
        """
        sleep(randint(2, 5))
        self.message_channel(message)

    def on_join(self, connection, event):
        super(ChatMixin, self).on_join(connection, event)
        nickname = self.get_nickname(event)
        greeting = choice(self.greetings)
        if nickname != self.nickname:
            self.message_channel_delayed("%s: %s" % (nickname, greeting))

    def on_pubmsg(self, connection, event):
        super(ChatMixin, self).on_pubmsg(connection, event)
        if not self.chatbots:
            return
        for message in event.arguments():
            prefix = "%s: " % self.nickname
            if message.startswith(prefix):
                nickname = self.get_nickname(event)
                chatbot = choice(self.chatbots)
                reply = chatbot.respond(message.replace(prefix, "", 1))
                self.message_channel_delayed("%s: %s" % (nickname, reply))
