
from __future__ import with_statement
from optparse import OptionParser
import sys

from gnotty import __version_string__


parser = OptionParser(usage="%prog [options]", version=__version_string__)
parser.add_option("-a", "--irc-host", dest="IRC_HOST", metavar="HOST",
                  default="irc.freenode.net",
                  help="IRC host address to connect to. [default: %default]")
parser.add_option("-p", "--irc-port", dest="IRC_PORT", metavar="PORT",
                  default=6667, type=int,
                  help="IRC port to connect to. [default: %default]")
parser.add_option("-A", "--http-host", dest="HTTP_HOST", metavar="HOST",
                  default="127.0.0.1",
                  help="HTTP host address to serve from. [default: %default]")
parser.add_option("-P", "--http-port", dest="HTTP_PORT", metavar="PORT",
                  default=8080, type=int,
                  help="HTTP port to serve from. [default: %default]")
parser.add_option("-c", "--irc-channel", dest="IRC_CHANNEL", metavar="CHANNEL",
                  default="#mezzanine",
                  help="IRC channel to join. [default: %default]")
parser.add_option("-n", "--logger-nickname", dest="LOGGER_NICKNAME",
                  metavar="NICKNAME", default="gnotty",
                  help="IRC nickname the logging client will use. "
                       "[default: %default]")
parser.add_option("-f", "--conf-file", dest="CONF_FILE", metavar="PATH",
                  help="Path to a Python config file to load options from.")


class Settings(dict):
    """
    Settings object, backed by either Django settings, or CLI args. The
    ``--conf-file`` CLI arg can also be used to specify the path to a
    Python module to load the settings from. Available settings and
    their defaults are defined above by the ``OptionParser`` instance
    used for parsing CLI args.
    """

    def __init__(self):
        """
        Try and initialize with Django settings.
        """
        try:
            from django.conf import settings
            for k, v in parser.defaults.items():
                self[k] = getattr(settings, "GNOTTY_%s" % k, v)
        except ImportError:
            pass

    def __getattr__(self, k):
        return self[k]

    def parse_args(self):
        """
        Called from ``gnotty.server.run`` and parses any CLI args
        provided. Also handles loading settings from the Python
        module specified with the ``--conf-file`` arg. CLI args
        take precedence over any settings defined in the Python
        module defined by ``--conf-file``.
        """
        options, _ = parser.parse_args()
        file_settings = {}
        if options.CONF_FILE:
            execfile(options.CONF_FILE, {}, file_settings)
        for option in parser.option_list:
            if option.dest:
                file_value = file_settings.get("GNOTTY_%s" % option.dest, None)
                # optparse doesn't seem to provide a way to determine if
                # an option's value was provided as a CLI arg, or if the
                # default is being used, so we manually check sys.argv,
                # since provided CLI args should take precedence over
                # any settings defined in a conf module.
                flags = option._short_opts + option._long_opts
                if file_value and not set(flags) & set(sys.argv):
                    self[option.dest] = file_value
                else:
                    self[option.dest] = getattr(options, option.dest)
        self["STATIC_URL"] = "/static/"


settings = Settings()
