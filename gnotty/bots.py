
from datetime import datetime
from inspect import getdoc, getargspec
from json import loads
from logging import Formatter, StreamHandler, INFO, getLogger
from random import choice, randint

from gevent import sleep

from gnotty.client import BaseIRCClient
from gnotty.conf import settings


class BaseBot(BaseIRCClient):
    """
    Base bot class. Defines the log and webook methods.
    """

    def __init__(self, *args, **kwargs):
        super(BaseBot, self).__init__(*args, **kwargs)
        fmt = Formatter("[%(server)s%(channel)s] %(nickname)s: %(message)s")
        handler = StreamHandler()
        handler.setFormatter(fmt)
        logger = getLogger("irc.message")
        logger.setLevel(settings.LOG_LEVEL)
        logger.addHandler(handler)

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
        for message in event.arguments():
            self.log(event, message)

    def on_webhook(self, environ, url, params):
        raise NotImplementedError


class ChatBot(BaseBot):
    """
    A demo bot that greets and responds to people.
    """

    def __init__(self, *args, **kwargs):
        super(ChatBot, self).__init__(*args, **kwargs)
        self.chatbots = []
        self.greetings = ("Hi", "Hello", "Howdy", "Welcome")
        try:
            from nltk.chat import bots
        except ImportError:
            from warnings import warn
            warn("ChatBot requires nltk installed")
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
        super(ChatBot, self).on_join(connection, event)
        nickname = self.get_nickname(event)
        greeting = choice(self.greetings)
        if nickname != self.nickname:
            self.message_channel_delayed("%s: %s" % (nickname, greeting))

    def on_pubmsg(self, connection, event):
        super(ChatBot, self).on_pubmsg(connection, event)
        if not self.chatbots:
            return
        for message in event.arguments():
            prefix = "%s: " % self.nickname
            if message.startswith(prefix):
                nickname = self.get_nickname(event)
                chatbot = choice(self.chatbots)
                reply = chatbot.respond(message.replace(prefix, "", 1))
                self.message_channel_delayed("%s: %s" % (nickname, reply))


class CommitBot(BaseBot):
    """
    Base bot for GitHub/BitBucket post-push webhooks. Accepts the
    webhook payload and writes out new commits and URLs to the
    channel.
    """

    def on_webhook(self, environ, url, params):
        payload = loads(params["payload"])
        commit = lambda c: "%s - %s" % (c["message"], self.author(c))
        messages = [commit(c) for c in payload["commits"]]
        if len(messages) == 1:
            messages[0] = "%s %s" % (messages[0], self.commit_url(commit))
        else:
            messages.insert(0, "%s new commits:" % len(payload["commits"]))
            messages.append("Compare view: %s" % self.diff_url(payload))
        for message in messages:
            self.message_channel(message)

    def author(self, commit):
        raise NotImplementedError

    def commit_url(self, commit, payload):
        raise NotImplementedError

    def diff_url(self, payload):
        raise NotImplementedError


class GitHubBot(CommitBot):
    """
    GitHub post-push webhook bot.
    """

    def author(self, commit):
        return commit["committer"]["name"]

    def commit_url(self, commit, payload):
        return commit["url"]

    def diff_url(self, payload):
        return payload["compare"].replace("^", "")


class BitBucketBot(CommitBot):
    """
    BitBucket post-push webhook bot.
    """

    def repo_url(self, payload):
        return payload["canon_url"] + payload["repository"]["absolute_url"]

    def author(self, commit):
        return commit["raw_author"].split("<")[0]

    def commit_url(self, commit, payload):
        return "%schangeset/%s/" % (self.repo_url(payload), commit["node"])

    def diff_url(self, payload):
        f, l = payload["commits"][0]["node"], payload["commits"][-1]["node"]
        return "%scompare/%s..%s" % (self.repo_url(payload), l, f)


class CommandBot(BaseBot):

    prefix_call = "!"
    prefix_method = "on_command_"

    def __init__(self, *args, **kwargs):
        # Build the command dict - each method beginning
        # with ``prefix_method``.
        self.commands = dict([
            (self.prefix_call + s[len(self.prefix_method):], getattr(self, s))
            for s in dir(self) if s.startswith(self.prefix_method)
        ])
        self.joined = {}
        self.quit = {}
        super(CommandBot, self).__init__(*args, **kwargs)

    def on_pubmsg(self, connection, event):
        """
        Check for a command on each new message, validates the
        command's argument length, and runs the command returning
        its result to the channel.
        """
        super(CommandBot, self).on_pubmsg(connection, event)
        for message in event.arguments():
            args = filter(None, message.split())
            try:
                command = self.commands[args.pop(0)]
            except KeyError:
                continue
            argspec = getargspec(command)
            num_all_args = len(argspec.args) - 2  # Ignore self/event args
            num_pos_args = num_all_args - len(argspec.defaults or [])
            if num_pos_args <= len(args) <= num_all_args:
                response = command(event, *args)
            elif num_all_args == num_pos_args:
                s = "s are" if num_all_args != 1 else " is"
                response = "%s arg%s required" % (num_all_args, s)
            else:
                bits = (num_pos_args, num_all_args)
                response = "between %s and %s args are required" % bits
            response = "%s: %s" % (self.get_nickname(event), response)
            self.message_channel(response)

    def on_namreply(self, connection, event):
        """
        Store join times for current nicknames when we first join.
        """
        nicknames = [s.lstrip("@+") for s in event.arguments()[-1].split()]
        for nickname in nicknames:
            self.joined[nickname] = datetime.now()

    def on_join(self, connection, event):
        """
        Store join time for a nickname when it joins.
        """
        super(CommandBot, self).on_join(connection, event)
        nickname = self.get_nickname(event)
        self.joined[nickname] = datetime.now()

    def on_quit(self, connection, event):
        """
        Store quit time for a nickname when it quits.
        """
        super(CommandBot, self).on_quit(connection, event)
        nickname = self.get_nickname(event)
        self.quit[nickname] = datetime.now()
        del self.joined[nickname]

    def timesince(self, when):
        """
        Returns human friendly version of the timespan between now
        and the given datetime.
        """
        units = (
            ("year",   60 * 60 * 24 * 365),
            ("week",   60 * 60 * 24 * 7),
            ("day",    60 * 60 * 24),
            ("hour",   60 * 60),
            ("minute", 60),
            ("second", 1),
        )
        delta = datetime.now() - when
        total_seconds = delta.days * 60 * 60 * 24 + delta.seconds
        parts = []
        for name, seconds in units:
            value = total_seconds / seconds
            if value > 0:
                total_seconds %= seconds
                s = "s" if value != 1 else ""
                parts.append("%s %s%s" % (value, name, s))
        return " and ".join(", ".join(parts).rsplit(", ", 1))

    ##############
    #  Commands  #
    ##############

    def on_command_version(self, event):
        """
        Shows version information.
        """
        return settings.GNOTTY_VERSION_STRING

    def on_command_commands(self, event):
        """
        Lists all available commands.
        """
        commands = sorted(self.commands.keys())
        return "Available commands: %s" % " ".join(commands)

    def on_command_help(self, event, command_name=None):
        """
        Shows the help message for the bot. Takes an optional command name
        which when given, will show help for that command.
        """
        if command_name is None:
            return ("Type %scommands for a list of all commands. Type "
                    "%shelp [command] to see help for a specific command." %
                    (self.prefix_call, self.prefix_call))
        try:
            command = self.commands[command_name]
        except KeyError:
            return "%s is not a command" % command_name

        argspec = getargspec(command)
        args = argspec.args[2:]
        defaults = argspec.defaults or []
        for i in range(-1, -len(defaults) - 1, -1):
            args[i] = "%s [default: %s]" % (args[i], defaults[i])
        args = ", ".join(args)
        help = getdoc(command).replace("\n", " ")
        return "help for %s: (args: %s) %s" % (command_name, args, help)

    def on_command_uptime(self, event, nickname=None):
        """
        Shows the amount of time since the given nickname has been
        in the channel. If no nickname is given, I'll use my own.
        """
        if nickname and nickname != self.nickname:
            try:
                uptime = self.timesince(self.joined[nickname])
            except KeyError:
                return "%s is not in the channel" % nickname
            else:
                if nickname == self.get_nickname(event):
                    prefix = "you have"
                else:
                    prefix = "%s has" % nickname
                return "%s been here for %s" % (prefix, uptime)
        uptime = self.timesince(self.joined[self.nickname])
        return "I've been here for %s" % uptime

    def on_command_seen(self, event, nickname):
        """
        Shows the amount of time since the given nickname was last
        seen in the channel.
        """
        try:
            self.joined[nickname]
        except KeyError:
            pass
        else:
            if nickname == self.get_nickname(event):
                prefix = "you are"
            else:
                prefix = "%s is" % nickname
            return "%s here right now" % prefix
        try:
            seen = self.timesince(self.quit[nickname])
        except KeyError:
            return "%s has never been seen" % nickname
        else:
            return "%s was last seen %s ago" % (nickname,  seen)

    def on_command_users(self, event):
        """
        Shows the list of users currently in the channel.
        """
        return "Current users: %s" % ", ".join(sorted(self.joined.keys()))
