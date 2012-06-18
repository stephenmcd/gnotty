
import os

try:
    os.environ["DJANGO_SETTINGS_MODULE"]
except KeyError:
    settings = None
else:
    from django.conf import settings


IRC_HOST = getattr(settings, "GNOTTY_IRC_HOST", "irc.freenode.net")
IRC_PORT = getattr(settings, "GNOTTY_IRC_PORT", 6667)
IRC_CHANNEL = getattr(settings, "GNOTTY_IRC_CHANNEL", "#mezzanine")
LOGGER_NICKNAME = getattr(settings, "GNOTTY_LOGGER_NICKNAME", "gnotty")
HTTP_HOST = getattr(settings, "GNOTTY_HTTP_HOST", "127.0.0.1")
HTTP_PORT = getattr(settings, "GNOTTY_HTTP_PORT", 8080)
STATIC_URL = "/static/"
