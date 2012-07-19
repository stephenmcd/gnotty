
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
        LoggingBot.log(self, **kwargs)
        IRCMessage.objects.create(**kwargs)
