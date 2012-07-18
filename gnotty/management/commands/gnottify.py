
from gevent.monkey import patch_all
patch_all()

from django.core.management.base import BaseCommand

from gnotty.server import serve_forever


class Command(BaseCommand):
    def handle(self, *args, **options):
        serve_forever(socketio_only=True)
