
from logging import getLogger

from irc.client import SimpleIRCClient

from gnotty.conf import settings


class BaseIRCClient(SimpleIRCClient, object):
    """
    Base class for IRC clients. Handles initial connection and
    channel join. Currently only supports a single channel.
    """

    def __init__(self, host, port, channel, nickname, password):
        SimpleIRCClient.__init__(self)
        self.host = host
        self.port = int(port) if str(port).isdigit() else 6667
        self.channel = channel
        self.nickname = nickname
        password = password or None
        self.connect(self.host, self.port, self.nickname, password=password)

    def _dispatcher(self, connection, event):
        event_args = "".join(event.arguments()).decode("utf-8")
        log = (event.eventtype(), self.nickname, event_args)
        getLogger("irc.dispatch").debug("%s: [%s] %s" % log)
        SimpleIRCClient._dispatcher(self, connection, event)

    def get_nickname(self, event):
        """
        Format a nickname.
        """
        return event.source().split("!")[0]

    def on_welcome(self, connection, event):
        """
        Join the channel once connected to the IRC server.
        """
        connection.join(self.channel, key=settings.IRC_CHANNEL_KEY or "")

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

    def message_channel(self, message):
        """
        Nicer shortcut for sending a message to a channel.
        """
        self.connection.privmsg(self.channel, message)


class WebSocketIRCClient(BaseIRCClient):
    """
    IRC client that's bridged with a gevent-socketio namespace.
    """

    def __init__(self, host, port, channel, nickname, password, namespace):
        self.nicknames = set()
        self.namespace = namespace
        client_args = (host, port, channel, nickname, password)
        super(WebSocketIRCClient, self).__init__(*client_args)

    def emit_message(self, message):
        """
        Send a message to the channel. We also emit the message
        back to the sender's WebSocket.
        """
        if self.nickname in self.nicknames:
            message = message[:settings.MAX_MESSAGE_LENGTH]
            self.message_channel(message)
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
