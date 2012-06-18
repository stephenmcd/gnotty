
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
from gnotty import settings, __version__


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

    def __init__(self, socketio_only=False):
        self.socketio_only = socketio_only
        self.server_string = "gnotty/%s" % __version__

    def index(self):
        """
        Loads the chat interface template, manually dealing with the
        Django template bits.
        """
        root_dir = os.path.dirname(__file__)
        template_dir = os.path.join(root_dir, "templates", "gnotty")
        with open(os.path.join(template_dir, "base.html"), "r") as f:
            base = f.read()
        with open(os.path.join(template_dir, "chat.html"), "r") as f:
            base = base.replace("{% block content %}", f.read())
        replace = {
            "{% block content %}": "",
            "{% endblock %}": "",
            "{% gnotty_nav %}": "",
            "{% load gnotty_tags %}": "",
            "{% extends \"gnotty/base.html\" %}": "",
            "{% templatetag openvariable %}": "{{",
            "{% templatetag closevariable %}": "}}",
        }
        for k, v in replace.items():
            base = base.replace(k, v)
        setting_names = ("IRC_HOST", "IRC_PORT", "IRC_CHANNEL",
                         "HTTP_HOST", "HTTP_PORT", "STATIC_URL")
        for name in setting_names:
            value = str(getattr(settings, name))
            base = base.replace("{{ %s }}" % name, value)
        return base

    def static(self, path):
        """
        Loads a static file.
        """
        path = os.path.join(os.path.dirname(__file__), path)
        content_type = "text/%s" % guess_type(path)[0].split("/")[-1]
        try:
            with open(path, "r") as f:
                return f.read()
        except IOError:
            pass

    def __call__(self, environ, start_response):
        """
        WSGI application handler.
        """
        path = os.path.normpath(environ["PATH_INFO"]).lstrip("/")
        if path.startswith("socket.io/"):
            socketio_manage(environ, {"": IRCNamespace})
            return

        status = "200 OK"
        content_type = "text/html"
        data = None

        if not self.socketio_only:
            if not path:
                data = self.index()
            else:
                data = self.static(path)
                if data:
                    content_type = guess_type(path)[0]
                    print content_type
        if not data:
            status = "404 Not Found"
            data = "<h1>Not Found</h1>"

        start_response(status, [
            ("Content-Type", content_type),
            ("Server", self.server_string)
        ])
        return [data]


def serve_forever(host, port, socketio_only=False):
    app = IRCApplication(socketio_only)
    server = SocketIOServer((host, port), app, namespace="socket.io",
                            policy_server=False)
    print "%s listening on %s:%s" % (app.server_string, host, port)
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
    serve_forever(host, port)
