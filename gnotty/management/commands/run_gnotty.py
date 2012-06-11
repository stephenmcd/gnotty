
from gevent import spawn
from gevent.monkey import patch_all
patch_all()

from django.core.management.base import BaseCommand

from gnotty.client import LoggingIRCClient
from gnotty.server import run
from gnotty.models import IRCMessage


class ModelLoggingIRCClient(LoggingIRCClient):

    def log(self, **kwargs):
        LoggingIRCClient.log(self, **kwargs)
        IRCMessage.objects.create(**kwargs)


class Command(BaseCommand):

    def handle(self, *args, **options):
        gnotty = ModelLoggingIRCClient("localhost", 6667, "#test", "gnotty")
        spawn(gnotty.start)
        run()
