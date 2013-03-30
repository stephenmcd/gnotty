
from logging import getLogger
from hashlib import md5

from irc.client import SimpleIRCClient, ServerConnectionError

from gnotty.conf import settings


def color(nickname):
    """
    Provides a consistent color for a nickname. Uses first 6 chars
    of nickname's md5 hash, and then slightly darkens the rgb values
    for use on a light background.
    """
    _hex = md5(nickname).hexdigest()[:6]
    darken = lambda s: str(int(round(int(s, 16) * .7)))
    return "rgb(%s)" % ",".join([darken(_hex[i:i+2]) for i in range(6)[::2]])


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
        self.password = password or None
        self.reconnect()

    def reconnect(self):
        args = (self.host, self.port, self.nickname)
        try:
            self.connect(*args, password=self.password)
            return True
        except ServerConnectionError:
            return False

    def _dispatcher(self, connection, event):
        if not callable(event.arguments):
            # irclib decided to change the event API, so here
            # we make it backward compatible.
            arguments = event.arguments
            event.arguments = lambda: arguments
            event.eventtype = lambda: event.type
            source = event.source
            event.source = lambda: source
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
        Nicer shortcut for sending a message to a channel. Also
        irclib doesn't handle unicode so we bypass its
        privmsg -> send_raw methods and use its socket directly.
        """
        data = "PRIVMSG %s :%s\r\n" % (self.channel, message)
        self.connection.socket.send(data.encode("utf-8"))


class WebSocketIRCClient(BaseIRCClient):
    """
    IRC client that's bridged with a gevent-socketio namespace.
    """

    def __init__(self, host, port, channel, nickname, password, namespace):
        self.nicknames = {}
        self.namespace = namespace
        client_args = (host, port, channel, nickname, password)
        super(WebSocketIRCClient, self).__init__(*client_args)

    def emit_message(self, message):
        """
        Send a message to the channel. We also emit the message
        back to the sender's WebSocket.
        """
        try:
            nickname_color = self.nicknames[self.nickname]
        except KeyError:
            # Only accept messages if we've joined.
            return
        message = message[:settings.MAX_MESSAGE_LENGTH]
        # Handle IRC commands.
        if message.startswith("/"):
            self.connection.send_raw(message.lstrip("/"))
            return
        self.message_channel(message)
        self.namespace.emit("message", self.nickname, message, nickname_color)

    def emit_nicknames(self):
        """
        Send the nickname list to the Websocket. Called whenever the
        nicknames list changes.
        """
        nicknames = [{"nickname": name, "color": color(name)}
                     for name in sorted(self.nicknames.keys())]
        self.namespace.emit("nicknames", nicknames)

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
        for nickname in event.arguments()[-1].split():
            nickname = nickname.lstrip("@+")
            self.nicknames[nickname] = color(nickname)
        self.emit_nicknames()

    def on_join(self, connection, event):
        """
        Someone joined the channel - send the nicknames list to the
        WebSocket.
        """
        #from time import sleep; sleep(10)  # Simulate a slow connection
        nickname = self.get_nickname(event)
        nickname_color = color(nickname)
        self.nicknames[nickname] = nickname_color
        self.namespace.emit("join")
        self.namespace.emit("message", nickname, "joins", nickname_color)
        self.emit_nicknames()

    def on_nick(self, connection, event):
        """
        Someone changed their nickname - send the nicknames list to the
        WebSocket.
        """
        old_nickname = self.get_nickname(event)
        old_color = self.nicknames.pop(old_nickname)
        new_nickname = event.target()
        message = "is now known as %s" % new_nickname
        self.namespace.emit("message", old_nickname, message, old_color)
        new_color = color(new_nickname)
        self.nicknames[new_nickname] = new_color
        self.emit_nicknames()
        if self.nickname == old_nickname:
            self.nickname = new_nickname

    def on_quit(self, connection, event):
        """
        Someone left the channel - send the nicknames list to the
        WebSocket.
        """
        nickname = self.get_nickname(event)
        nickname_color = self.nicknames[nickname]
        del self.nicknames[nickname]
        self.namespace.emit("message", nickname, "leaves", nickname_color)
        self.emit_nicknames()

    def on_pubmsg(self, connection, event):
        """
        Messages received in the channel - send them to the WebSocket.
        """
        for message in event.arguments():
            nickname = self.get_nickname(event)
            nickname_color = self.nicknames[nickname]
            self.namespace.emit("message", nickname, message, nickname_color)
