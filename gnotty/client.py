
from irclib import SimpleIRCClient


class BaseIRCClient(SimpleIRCClient):
    """
    Base class for IRC clients. Handles initial connection and
    channel join. Currently only supports a single channel.
    """

    def __init__(self, host, port, channel, nickname):
        SimpleIRCClient.__init__(self)
        self.channel = channel
        self.connect(host, port, nickname)

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
        self.nickname = nickname
        self.nicknames = []
        self.namespace = namespace
        BaseIRCClient.__init__(self, host, port, channel, nickname)

    def emit_message(self, message):
        """
        Send a message to the channel. We also emit the message
        back to the sender's WebSocket.
        """
        self.connection.privmsg(self.channel, message)
        self.namespace.emit("message", self.nickname, message)

    def emit_nicknames(self):
        """
        Send the nickname list to the Websocket. Called whenever the
        nicknames list changes.
        """
        self.namespace.emit("nicknames", self.nicknames)

    def on_namreply(self, connection, event):
        """
        Initial list of nicknames received - remove op/voice prefixes,
        and send the list to the WebSocket.
        """
        self.nicknames = [s.lstrip("@+") for s in event.arguments()[-1].split()]
        self.emit_nicknames()

    def on_join(self, connection, event):
        """
        Someone joined the channel - send the nicknames list to the
        WebSocket.
        """
        self.nicknames.append(self.get_nickname(event))
        self.namespace.emit("message", self.nickname, "joins")
        self.emit_nicknames()

    def on_quit(self, connection, event):
        """
        Someone left the channel - send the nicknames list to the
        WebSocket.
        """
        self.nicknames.remove(self.get_nickname(event))
        self.namespace.emit("message", self.nickname, "leaves")
        self.emit_nicknames()

    def on_pubmsg(self, connection, event):
        """
        Messages received in the channel - send them to the WebSocket.
        """
        for message in event.arguments():
            self.namespace.emit("message", self.get_nickname(event), message)


