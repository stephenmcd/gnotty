#!/usr/bin/env python

from __future__ import with_statement
from gevent import monkey, spawn
monkey.patch_all()

import os
import sys
from tempfile import gettempdir
from mimetypes import guess_type

from daemon import daemonize
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace

from gnotty.client import WebSocketIRCClient
from gnotty.conf import settings


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

    def recv_disconnect(self):
        """
        WebSocket was disconnected - leave the IRC channel.
        """
        quit_message = "%s %s" % (settings.GNOTTY_VERSION_STRING,
                                  settings.GNOTTY_PROJECT_URL)
        self.client.connection.quit(quit_message)
        self.disconnect(silent=True)


class IRCApplication(object):

    def __init__(self, django=False):
        self.django = django
        self.bot = None
        # Load the bot.
        if settings.BOT_CLASS:
            module, attr = settings.BOT_CLASS.rsplit(".", 1)
            __import__(module)
            bot_class = getattr(sys.modules[module], attr)
            self.bot = bot_class(settings.IRC_HOST, settings.IRC_PORT,
                                 settings.IRC_CHANNEL, settings.BOT_NICKNAME)
            spawn(self.bot.start)
        self.webhook = hasattr(self.bot, "on_webhook")

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
            "{% load gnotty_tags %}": "",
            "{% extends \"gnotty/base.html\" %}": "",
            "{% url gnotty_chat %}": "/",
            "{% gnotty_nav %}": "",
            "{% templatetag openvariable %}": "{{",
            "{% templatetag closevariable %}": "}}",
        }
        for k, v in replace.items():
            base = base.replace(k, v)
        for k, v in settings.items():
            base = base.replace("{{ %s }}" % k, unicode(v or ""))
        return base

    def respond_webhook(self, environ):
        """
        Passes the request onto a bot running with webhook if one is
        running and the webhook path is requested.
        """
        try:
            response = self.bot.on_webhook(environ)
        except:
            return ("500 INTERNAL SERVER ERROR", [], "")
        if not response or isinstance(response, basestring):
            response = ("200 OK", [], response or "")
        return response

    def respond_django(self, environ):
        """
        Tries to redirect to a Django app if someone tries to
        access an invalid URL.
        """
        environ["port"] = ""
        if environ["SERVER_NAME"] in ("127.0.0.1", "localhost"):
            environ["port"] = ":8000"
        location = ("%(wsgi.url_scheme)s://" +
            "%(SERVER_NAME)s%(port)s%(PATH_INFO)s") % environ
        return ("301 MOVED PERMANENTLY", [("Location", location)], "")

    def respond_static(self, environ):
        """
        Serves a static file when Django isn't being used.
        """
        root = os.path.dirname(__file__)
        path = os.path.normpath(environ["PATH_INFO"])
        status = "200 OK"
        content_type = "text/html"
        data = None
        if path == "/":
            data = self.index()
        else:
            try:
                with open(os.path.join(root, path.lstrip("/")), "r") as f:
                    data = f.read()
            except IOError:
                pass
            if data:
                content_type = guess_type(path)[0]
        if not data:
            status = "404 NOT FOUND"
            data = "<h1>Not Found</h1>"
        return (status, [("Content-Type", content_type)], data)

    def __call__(self, environ, start_response):
        """
        WSGI application handler.
        """
        path = environ["PATH_INFO"]
        if path.startswith("/socket.io/"):
            socketio_manage(environ, {"": IRCNamespace})
            return
        if path.startswith("/webhook/") and self.webhook:
            dispatch = self.respond_webhook
        elif self.django:
            dispatch = self.respond_django
        else:
            dispatch = self.respond_static
        status, headers, data = dispatch(environ)
        headers.append(("Server", settings.GNOTTY_VERSION_STRING))
        start_response(status, headers)
        return [data]


def serve_forever(django=False):
    """
    Starts the gevent-socketio server.
    """
    host_port = (settings.HTTP_HOST, settings.HTTP_PORT)
    server = SocketIOServer(host_port, IRCApplication(django),
                            resource="socket.io", policy_server=False)
    print "%s listening on %s:%s" % (
          (settings.GNOTTY_VERSION_STRING,) + host_port)
    server.serve_forever()


def kill(pid_file):
    """
    Attempts to shut down a previously started daemon.
    """
    try:
        with open(pid_file) as f:
            os.kill(int(f.read()), 9)
        os.remove(pid_file)
    except (IOError, OSError):
        return False
    return True


def run():
    """
    CLI entry point. Parses args and starts the gevent-socketio server.
    """
    settings.parse_args()
    pid_file = settings.PID_FILE or os.path.join(gettempdir(),
        "gnotty-%s-%s.pid" % (settings.HTTP_HOST, settings.HTTP_PORT))
    if settings.KILL:
        if kill(pid_file):
            print "Daemon killed"
        else:
            print "Could not kill any daemons"
        return
    elif kill(pid_file):
        print "Running daemon killed"
    if settings.DAEMON:
        daemonize(pid_file)
    serve_forever()


if __name__ == "__main__":
    run()
