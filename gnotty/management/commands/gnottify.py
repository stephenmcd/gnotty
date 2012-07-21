
from gevent.monkey import patch_all
patch_all()

from django.core.management.base import BaseCommand

from gnotty.conf import settings


class Command(BaseCommand):

    option_list = BaseCommand.option_list + tuple(settings.option_list)

    def handle(self, *args, **options):
        settings.parse_args()
        from gnotty.server import serve_forever
        serve_forever(django=True)
