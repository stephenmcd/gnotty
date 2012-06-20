
from gevent import spawn
from gevent.monkey import patch_all
patch_all()

from django.core.management.base import BaseCommand

from gnotty.client import LoggingIRCClient
from gnotty.conf import settings
from gnotty.models import IRCMessage
from gnotty.server import serve_forever


class ModelLoggingIRCClient(LoggingIRCClient):

    def log(self, **kwargs):
        LoggingIRCClient.log(self, **kwargs)
        IRCMessage.objects.create(**kwargs)


class Command(BaseCommand):

    def handle(self, *args, **options):
        gnotty = ModelLoggingIRCClient(settings.IRC_HOST,
                                       settings.IRC_PORT,
                                       settings.IRC_CHANNEL,
                                       settings.LOGGER_NICKNAME)
        spawn(gnotty.start)
        serve_forever(socketio_only=True)
