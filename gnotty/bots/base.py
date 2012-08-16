
from collections import defaultdict
from inspect import getargspec
from logging import Formatter, StreamHandler, getLogger
from re import match

from gnotty.client import BaseIRCClient
from gnotty.conf import settings


class BaseBot(BaseIRCClient):
    """
    Base bot class. Bots can be built by subclassing ``BaseBot`` and
    using mixins that define event handlers. The subclass itself can
    also implement the event handlers. See the README for more info
    on event handlers.
    """

    class __metaclass__(type):
        def __new__(cls, name, bases, attrs):
            """
            Build a dict mapping event names to their handler methods,
            which are any methods defined on any classes in the
            inheritance heirarchy, that have been marked with an
            "event" attribute, which gets assgined by the
            ``gnotty.bots.events.on`` decorator.
            """
            members = sum([b.__dict__.values() for b in bases], attrs.values())
            attrs["events"] = defaultdict(list)
            for member in members:
                if hasattr(member, "event"):
                    attrs["events"][member.event["name"]].append(member)
            return type.__new__(cls, name, bases, attrs)

    def __init__(self, *args, **kwargs):
        """
        Sets up logging.
        """
        super(BaseBot, self).__init__(*args, **kwargs)
        fmt = Formatter("[%(server)s%(channel)s] %(nickname)s: %(message)s")
        handler = StreamHandler()
        handler.setFormatter(fmt)
        logger = getLogger("irc.message")
        logger.setLevel(settings.LOG_LEVEL)
        logger.addHandler(handler)

    def _dispatcher(self, connection, event):
        """
        This is the method in ``SimpleIRCClient`` that all IRC events
        get passed through. Here we map events to our own custom
        event handlers, and call them.
        """
        super(BaseBot, self)._dispatcher(connection, event)
        for handler in self.events[event.eventtype()]:
            handler(self, connection, event)

    def log(self, event, message):
        extra = {
            "server": self.connection.server,
            "channel": self.channel,
            "nickname": self.get_nickname(event) if event else self.nickname,
        }
        getLogger("irc.message").info(message, extra=extra)

    def message_channel(self, message):
        """
        We won't receive our own messages, so log them manually.
        """
        self.log(None, message)
        super(BaseBot, self).message_channel(message)

    def on_join(self, connection, event):
        self.log(event, "joins")

    def on_quit(self, connection, event):
        self.log(event, "leaves")

    def on_pubmsg(self, connection, event):
        """
        Log any public messages, and also handle the command event.
        """
        for message in event.arguments():
            self.log(event, message)
            args = filter(None, message.split())
            name = args.pop(0)
            for command in self.events["command"]:
                if command.event["args"][0] == name:
                    self.on_command(event, command, args)

    def on_command(self, event, command, args):
        """
        Command handler - treats each word in the message
        that triggered the command as an argument to the command,
        and does some validation to ensure that the number of
        arguments match.
        """
        argspec = getargspec(command)
        num_all_args = len(argspec.args) - 2  # Ignore self/event args
        num_pos_args = num_all_args - len(argspec.defaults or [])
        if num_pos_args <= len(args) <= num_all_args:
            response = command(self, event, *args)
        elif num_all_args == num_pos_args:
            s = "s are" if num_all_args != 1 else " is"
            response = "%s arg%s required" % (num_all_args, s)
        else:
            bits = (num_pos_args, num_all_args)
            response = "between %s and %s args are required" % bits
        response = "%s: %s" % (self.get_nickname(event), response)
        self.message_channel(response)

    def on_webhook(self, environ, url, params):
        """
        Webhook handler - each handler for the webhook event
        takes an initial pattern argument for matching the URL
        requested. Here we match the URL to the pattern for each
        webhook handler, and bail out if it returns a response.
        """
        for handler in self.events["webhook"]:
            args = handler.event["args"]
            if not args or match(args[0], url):
                response = handler(self, environ, url, params)
                if response:
                    return response
