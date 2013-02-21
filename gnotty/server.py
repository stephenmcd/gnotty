#!/usr/bin/env python

from __future__ import with_statement
from gevent import monkey, spawn, sleep
monkey.patch_all()

from Cookie import Cookie
from cgi import FieldStorage
from logging import getLogger, StreamHandler
from mimetypes import guess_type
import os
import sys
from tempfile import gettempdir
from traceback import format_exc

from daemon import daemonize
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace

from gnotty.client import WebSocketIRCClient
from gnotty.conf import settings


HTTP_STATUS_TEXT = {
    200: "OK",
    301: "MOVED PERMANENTLY",
    401: "UNAUTHORIZED",
    404: "NOT FOUND",
    500: "INTERNAL SERVER ERROR",
}


class IRCNamespace(BaseNamespace):
    """
    gevent-socketio namespace that's bridged with an IRC client.
    """

    def on_start(self, host, port, channel, nickname, password):
        """
        A WebSocket session has started - create a greenlet to host
        the IRC client, and start it.
        """
        self.client = WebSocketIRCClient(host, port, channel, nickname,
                                         password, self)
        self.spawn(self.client.start)

    def on_message(self, message):
        """
        Message received from a WebSocket - send it to the IRC channel.
        """
        if hasattr(self, "client"):
            self.client.emit_message(message)

    def disconnect(self, *args, **kwargs):
        """
        WebSocket was disconnected - leave the IRC channel.
        """
        quit_message = "%s %s" % (settings.GNOTTY_VERSION_STRING,
                                  settings.GNOTTY_PROJECT_URL)
        self.client.connection.quit(quit_message)
        super(IRCNamespace, self).disconnect(*args, **kwargs)


class IRCApplication(object):

    def __init__(self, django=False):
        """
        Loads and starts the IRC bot for the entire application.
        """
        self.django = django
        self.bot = None
        if settings.BOT_CLASS:
            module_name, class_name = settings.BOT_CLASS.rsplit(".", 1)
            __import__(module_name)
            bot_class = getattr(sys.modules[module_name], class_name)
            self.bot = bot_class(settings.IRC_HOST, settings.IRC_PORT,
                                 settings.IRC_CHANNEL, settings.BOT_NICKNAME,
                                 settings.BOT_PASSWORD)
            spawn(self.bot.start)
            spawn(self.bot_watcher)
        self.logger = getLogger("irc.webhooks")
        self.logger.setLevel(settings.LOG_LEVEL)
        self.logger.addHandler(StreamHandler())

    def bot_watcher(self):
        """
        Thread (greenlet) that will try and reconnect the bot if
        it's not connected.
        """
        default_interval = 5
        interval = default_interval
        while True:
            if not self.bot.connection.connected:
                if self.bot.reconnect():
                    interval = default_interval
                else:
                    interval *= 2
            sleep(interval)

    def respond_webhook(self, environ):
        """
        Passes the request onto a bot with a webhook if the webhook
        path is requested.
        """
        request = FieldStorage(fp=environ["wsgi.input"], environ=environ)
        url = environ["PATH_INFO"]
        params = dict([(k, request[k].value) for k in request])
        try:
            if self.bot is None:
                raise NotImplementedError
            response = self.bot.handle_webhook_event(environ, url, params)
        except NotImplementedError:
            return 404
        except:
            self.logger.debug(format_exc())
            return 500
        return response or 200

    def respond_static(self, environ):
        """
        Serves a static file when Django isn't being used.
        """
        path = os.path.normpath(environ["PATH_INFO"])
        if path == "/":
            content = self.index()
            content_type = "text/html"
        else:
            path = os.path.join(os.path.dirname(__file__), path.lstrip("/"))
            try:
                with open(path, "r") as f:
                    content = f.read()
            except IOError:
                return 404
            content_type = guess_type(path)[0]
        return (200, [("Content-Type", content_type)], content)

    def index(self):
        """
        Loads the chat interface template when Django isn't being
        used, manually dealing with the Django template bits.
        """
        root_dir = os.path.dirname(__file__)
        template_dir = os.path.join(root_dir, "templates", "gnotty")
        with open(os.path.join(template_dir, "base.html"), "r") as f:
            base = f.read()
        with open(os.path.join(template_dir, "chat.html"), "r") as f:
            base = base.replace("{% block content %}", f.read())
        replace = {
            "{% block content %}": "",
            "{% block extrahead %}": "",
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

    def respond_django(self, environ):
        """
        Tries to redirect to a Django app if someone accesses an
        invalid URL when Django is being used.
        """
        environ["port"] = ""
        if environ["SERVER_NAME"] in ("127.0.0.1", "localhost"):
            environ["port"] = ":8000"
        location = ("%(wsgi.url_scheme)s://" +
            "%(SERVER_NAME)s%(port)s%(PATH_INFO)s") % environ
        return (301, [("Location", location)], None)

    def respond_unauthorized(self, environ):
        """
        Just return unauthorized HTTP status if the
        ``unauthorized`` method returns ``True`` inside
        ``__call__``.
        """
        return 401

    def authorized(self, environ):
        """
        If we're running Django and ``GNOTTY_LOGIN_REQUIRED`` is set
        to ``True``, pull the session cookie from the environment and
        validate that the user is authenticated.
        """
        if self.django and settings.LOGIN_REQUIRED:
            try:
                from django.conf import settings as django_settings
                from django.contrib.auth import SESSION_KEY
                from django.contrib.auth.models import User
                from django.contrib.sessions.models import Session
                from django.core.exceptions import ObjectDoesNotExist
                cookie = Cookie(environ["HTTP_COOKIE"])
                cookie_name = django_settings.SESSION_COOKIE_NAME
                session_key = cookie[cookie_name].value
                session = Session.objects.get(session_key=session_key)
                user_id = session.get_decoded().get(SESSION_KEY)
                user = User.objects.get(id=user_id)
            except (ImportError, KeyError, ObjectDoesNotExist):
                return False
        return True

    def __call__(self, environ, start_response):
        """
        WSGI application handler.
        """
        authorized = self.authorized(environ)
        path = environ["PATH_INFO"]
        if path.startswith("/socket.io/") and authorized:
            socketio_manage(environ, {"": IRCNamespace})
            return
        if not authorized:
            dispatch = self.respond_unauthorized
        elif path.startswith("/webhook/"):
            dispatch = self.respond_webhook
        elif self.django:
            dispatch = self.respond_django
        else:
            dispatch = self.respond_static
        response = dispatch(environ)
        if isinstance(response, int):
            response = (response, [], None)
        elif isinstance(response, basestring):
            response = (200, [], response)
        status, headers, content = response
        status_text = HTTP_STATUS_TEXT.get(status, "")
        headers.append(("Server", settings.GNOTTY_VERSION_STRING))
        start_response("%s %s" % (status, status_text), headers)
        if content is None:
            if status == 200:
                content = ""
            else:
                content = "<h1>%s</h1>" % status_text.title()
        return [content]


def serve_forever(django=False):
    """
    Starts the gevent-socketio server.
    """
    logger = getLogger("irc.dispatch")
    logger.setLevel(settings.LOG_LEVEL)
    logger.addHandler(StreamHandler())
    app = IRCApplication(django)
    server = SocketIOServer((settings.HTTP_HOST, settings.HTTP_PORT), app)
    print "%s [Bot: %s] listening on %s:%s" % (
        settings.GNOTTY_VERSION_STRING,
        app.bot.__class__.__name__,
        settings.HTTP_HOST,
        settings.HTTP_PORT,
    )
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
    pid_name = "gnotty-%s-%s.pid" % (settings.HTTP_HOST, settings.HTTP_PORT)
    pid_file = settings.PID_FILE or os.path.join(gettempdir(), pid_name)
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
