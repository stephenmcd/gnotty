
from random import choice

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

    def log_args(self, event, message):
        return {
            "server": self.connection.server,
            "channel": self.channel,
            "nickname": self.get_nickname(event),
            "message": message,
        }

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

    def __init__(self, *args, **kwargs):
        super(ChatterMixin, self).__init__(*args, **kwargs)
        try:
            from nltk.chat.eliza import eliza_chatbot
            from nltk.chat.iesha import iesha_chatbot
            from nltk.chat.rude import rude_chatbot
            from nltk.chat.suntsu import suntsu_chatbot
            from nltk.chat.zen import zen_chatbot
        except ImportError:
            print "ChatterMixin requires nltk installed"
        else:
            self.chatbots = [eliza_chatbot, iesha_chatbot, rude_chatbot,
                             suntsu_chatbot, zen_chatbot]

    def on_join(self, connection, event):
        nickname = self.get_nickname(event)
        greetings = ("Hi", "Hello", "Howdy", "Welcome")
        if nickname != self.nickname:
            self.message_channel("%s: %s" % (nickname, choice(greetings)))
        super(GreeterMixin, self).on_join(connection, event)

    def on_pubmsg(self, connection, event):
        from nltk.chat.rude import rude_chatbot
        for message in event.arguments():
            prefix = "%s: " % self.nickname
            if message.startswith(prefix):
                nickname = self.get_nickname(event)
                chatbot = choice(self.chatbots)
                reply = chatbot.respond(message.replace(prefix, "", 1))
                self.message_channel("%s: %s" % (nickname, reply))
