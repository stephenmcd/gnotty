
from gnotty.conf import settings
from gnotty.lib.irclib import SimpleIRCClient


class BaseIRCClient(SimpleIRCClient):
    """
    Base class for IRC clients. Handles initial connection and
    channel join. Currently only supports a single channel.
    """

    def __init__(self, host, port, channel, nickname):
        SimpleIRCClient.__init__(self)
        self.host = host
        self.port = int(port) if str(port).isdigit() else 6667
        self.channel = channel
        self.nickname = nickname
        self.connect(self.host, self.port, self.nickname)

    def get_nickname(self, event):
        """
        Format a nickname.
        """
        return event.source().split("!")[0]

    def on_welcome(self, connection, event):
        """
        Join the channel once connected to the IRC server.
        """
        connection.join(self.channel)

    def on_nicknameinuse(self, connection, event):
        """
        Increment a digit on the nickname if it's in use, and
        re-connect.
        """
        digits = ""
        while self.nickname[-1].isdigit():
            digits = self.nickname[-1] + digits
            self.nickname = self.nickname[:-1]
        digits = 1 if not digits else int(digits) + 1
        self.nickname += str(digits)
        self.connect(self.host, self.port, self.nickname)


class LoggingIRCClient(BaseIRCClient):
    """
    Subclassable IRC client that simply logs each channel message.
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
        self.log(**self.log_args(event, "joins"))

    def on_pubmsg(self, connection, event):
        for message in event.arguments():
            self.log(**self.log_args(event, message))


class WebSocketIRCClient(BaseIRCClient):
    """
    IRC client that's bridged with a gevent-socketio namespace.
    """

    def __init__(self, host, port, channel, nickname, namespace):
        self.nicknames = set()
        self.namespace = namespace
        BaseIRCClient.__init__(self, host, port, channel, nickname)

    def emit_message(self, message):
        """
        Send a message to the channel. We also emit the message
        back to the sender's WebSocket.
        """
        if self.nickname in self.nicknames:
            message = message[:settings.MAX_MESSAGE_LENGTH]
            self.connection.privmsg(self.channel, message)
            self.namespace.emit("message", self.nickname, message)

    def emit_nicknames(self):
        """
        Send the nickname list to the Websocket. Called whenever the
        nicknames list changes.
        """
        self.namespace.emit("nicknames", list(self.nicknames))

    def on_erroneusnickname(self, connection, event):
        """
        Invalid nickname chars/length - report back to the client.
        """
        self.namespace.emit("invalid")

    def on_namreply(self, connection, event):
        """
        Initial list of nicknames received - remove op/voice prefixes,
        and send the list to the WebSocket.
        """
        nicknames = [s.lstrip("@+") for s in event.arguments()[-1].split()]
        self.nicknames |= set(nicknames)
        self.emit_nicknames()

    def on_join(self, connection, event):
        """
        Someone joined the channel - send the nicknames list to the
        WebSocket.
        """
        #from time import sleep; sleep(10)  # Simulate a slow connection
        nickname = self.get_nickname(event)
        self.nicknames.add(nickname)
        self.namespace.emit("join")
        self.namespace.emit("message", nickname, "joins")
        self.emit_nicknames()

    def on_quit(self, connection, event):
        """
        Someone left the channel - send the nicknames list to the
        WebSocket.
        """
        nickname = self.get_nickname(event)
        self.nicknames.remove(nickname)
        self.namespace.emit("message", nickname, "leaves")
        self.emit_nicknames()

    def on_pubmsg(self, connection, event):
        """
        Messages received in the channel - send them to the WebSocket.
        """
        for message in event.arguments():
            self.namespace.emit("message", self.get_nickname(event), message)
