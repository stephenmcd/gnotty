
from __future__ import with_statement
from gevent import monkey
monkey.patch_all()

import os
import sys
from mimetypes import guess_type

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace

from gnotty.client import WebSocketIRCClient
from gnotty import settings


class IRCNamespace(BaseNamespace):
    """
    gevent-socketio namespace that's bridged with an IRC client.
    """

    def on_start(self, host, port, channel, nickname):
        """
        A WebSocket session has started - create a greenlet to host
        the IRC client, and start it.
        """
        self.client = WebSocketIRCClient(host, port, channel, nickname, self)
        self.spawn(self.client.start)

    def on_message(self, message):
        """
        Message received from a WebSocket - send it to the IRC channel.
        """
        if hasattr(self, "client"):
            self.client.emit_message(message)

    def disconnect(self, silent=False):
        """
        WebSocket was disconnected - leave the IRC channel.
        """
        self.client.connection.quit("bye")
        super(IRCNamespace, self).disconnect(silent)


class IRCApplication(object):

    def __call__(self, environ, start_response):
        """
        WSGI application handler.
        """
        path = os.path.normpath(environ["PATH_INFO"]).lstrip("/")
        if not path:
            path = os.path.join("templates", "gnotty", "chat.html")
        if path.startswith("socket.io/"):
            socketio_manage(environ, {"": IRCNamespace})
            return
        path = os.path.join(os.path.dirname(__file__), path)
        try:
            with open(path, "r") as f:
                data = f.read()
        except IOError:
            data = None
        if not data:
            start_response("404 Not Found", [])
            return ["<h1>Not Found</h1>"]
        setting_names = ("IRC_HOST", "IRC_PORT", "IRC_CHANNEL",
                         "HTTP_HOST", "HTTP_PORT", "STATIC_URL")
        for name in setting_names:
            value = str(getattr(settings, name))
            data = data.replace("{{ %s }}" % name, value)
        ext = path.split(".")[-1]
        content_type = "text/%s" % guess_type(path)[0].split("/")[-1]
        start_response("200 OK", [("Content-Type", content_type)])
        return [data]


def serve(host, port):
    print "gnotty server running on %s:%s" % (host, port)
    server = SocketIOServer((host, port), IRCApplication(),
                            namespace="socket.io", policy_server=False)
    server.serve_forever()

def run():
    # try:
    #     arg = sys.argv[1]
    # except IndexError:
    #     arg = "0.0.0.0:8080"
    arg = "0.0.0.0:8080"
    try:
        host, port = arg.split(":")
    except ValueError:
        host, port = "0.0.0.0", arg
    try:
        port = int(port)
    except ValueError:
        raise Exception("Invalid port: %s" % port)
    serve(host, port)
