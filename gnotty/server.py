
from __future__ import with_statement
from gevent import monkey
monkey.patch_all()

import os
import sys

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace

from gnotty.client import WebSocketIRCClient


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
        if environ["PATH_INFO"].startswith("/socket.io/"):
            socketio_manage(environ, {"": IRCNamespace})
        elif environ["PATH_INFO"] == "/":
            d = os.path.dirname(__file__)
            with open(os.path.join(d, "templates", "index.html"), "r") as f:
                start_response("200 OK", [("Content-Type", "text/html")])
                return [f.read()]
        start_response("404 Not Found", [])
        return ["<h1>Not Found</h1>"]


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
    print "gnotty server running on %s:%s" % (host, port)
    server = SocketIOServer((host, port), IRCApplication(),
                            namespace="socket.io", policy_server=False)
    server.serve_forever()
