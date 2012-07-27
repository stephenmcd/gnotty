
from json import loads
from logging import Formatter, StreamHandler, INFO, getLogger
from random import choice, randint

from gevent import sleep

from gnotty.client import BaseIRCClient


class BaseBot(BaseIRCClient):
    """
    Base bot class. Defines the log and webook methods.
    """

    def __init__(self, *args, **kwargs):
        super(BaseBot, self).__init__(*args, **kwargs)
        fmt = Formatter("[%(server)s%(channel)s] %(nickname)s: %(message)s")
        handler = StreamHandler()
        handler.setLevel(INFO)
        handler.setFormatter(fmt)
        logger = getLogger("irc")
        logger.setLevel(INFO)
        logger.addHandler(handler)

    def log(self, event, message):
        extra = {
            "server": self.connection.server,
            "channel": self.channel,
            "nickname": self.get_nickname(event) if event else self.nickname,
        }
        getLogger("irc").info(message, extra=extra)

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
