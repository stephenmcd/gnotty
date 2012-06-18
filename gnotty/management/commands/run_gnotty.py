
from gevent import spawn
from gevent.monkey import patch_all
patch_all()

from django.core.management.base import BaseCommand

from gnotty.client import LoggingIRCClient
from gnotty.models import IRCMessage
from gnotty.server import serve_forever
from gnotty.settings import (IRC_HOST, IRC_PORT, IRC_CHANNEL, LOGGER_NICKNAME,
                             HTTP_HOST, HTTP_PORT)



class ModelLoggingIRCClient(LoggingIRCClient):

    def log(self, **kwargs):
        LoggingIRCClient.log(self, **kwargs)
        IRCMessage.objects.create(**kwargs)


class Command(BaseCommand):

    def handle(self, *args, **options):
        gnotty = ModelLoggingIRCClient(IRC_HOST, IRC_PORT, IRC_CHANNEL,
                                       LOGGER_NICKNAME)
        spawn(gnotty.start)
        serve_forever(HTTP_HOST, HTTP_PORT, socketio_only=True)
