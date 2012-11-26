
from django.core.management import call_command
from gevent import spawn

from gnotty.management.commands import gnottify


class Command(gnottify.Command):

    def handle(self, *args, **options):
        spawn(lambda: call_command("runserver", *args))
        super(Command, self).handle(*args, **options)
