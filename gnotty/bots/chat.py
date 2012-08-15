
from random import choice, randint

from gevent import sleep

from gnotty.bots import events


class ChatMixin(object):
    """
    Mixin for a chat bot that greets and responds to people.
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

    @events.on("join")
    def greet(self, connection, event):
        nickname = self.get_nickname(event)
        greeting = choice(self.greetings)
        if nickname != self.nickname:
            self.message_channel_delayed("%s: %s" % (nickname, greeting))

    @events.on("pubmsg")
    def respond(self, connection, event):
        if not self.chatbots:
            return
        for message in event.arguments():
            prefix = "%s: " % self.nickname
            if message.startswith(prefix):
                nickname = self.get_nickname(event)
                chatbot = choice(self.chatbots)
                reply = chatbot.respond(message.replace(prefix, "", 1))
                self.message_channel_delayed("%s: %s" % (nickname, reply))
