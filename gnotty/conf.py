
from __future__ import with_statement
from optparse import OptionParser
import sys

from gnotty import __version__, __version_string__, __url__


parser = OptionParser(usage="%prog [options]", version=__version__)
parser.add_option("-A", "--irc-host", dest="IRC_HOST", metavar="HOST",
                  default="irc.freenode.net",
                  help="IRC host address to connect to [default: %default]")
parser.add_option("-P", "--irc-port", dest="IRC_PORT", metavar="PORT",
                  default=6667, type=int,
                  help="IRC port to connect to [default: %default]")
parser.add_option("-a", "--http-host", dest="HTTP_HOST", metavar="HOST",
                  default="127.0.0.1",
                  help="HTTP host address to serve from [default: %default]")
parser.add_option("-p", "--http-port", dest="HTTP_PORT", metavar="PORT",
                  default=8080, type=int,
                  help="HTTP port to serve from [default: %default]")
parser.add_option("-C", "--irc-channel", dest="IRC_CHANNEL", metavar="CHANNEL",
                  default="#gnotty",
                  help="IRC channel to join [default: %default]")
parser.add_option("-c", "--bot-class", dest="BOT_CLASS",
                  metavar="DOTTED_PYTHON_PATH",
                  default="gnotty.bots.LoggingBot",
                  help="Dotted Python path to the IRC client bot class to run "
                       "[default: %default]")
parser.add_option("-n", "--bot-nickname", dest="BOT_NICKNAME",
                  metavar="NICKNAME", default="gnotty",
                  help="IRC nickname the bot will use [default: %default]")
parser.add_option("-D", "--daemon", dest="DAEMON", action="store_true",
                  default=False,
                  help="run in daemon mode")
parser.add_option("-k", "--kill", dest="KILL", action="store_true",
                  default=False,
                  help="Shuts down a previously started daemon")
parser.add_option("-F", "--pid-file", dest="PID_FILE", metavar="FILE_PATH",
                  help="path to write PID file to when in daemon mode")
parser.add_option("-f", "--conf-file", dest="CONF_FILE", metavar="FILE_PATH",
                  help="path to a Python config file to load options from")


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
        # Some constants about the software.
        self["GNOTTY_VERSION"] = __version__
        self["GNOTTY_VERSION_STRING"] = __version_string__
        self["GNOTTY_PROJECT_URL"] = __url__
        django_defaults = {
            "BOT_CLASS": "gnotty.bots.ModelLoggingBot",
        }
        try:
            from django.conf import settings
            for k, v in dict(parser.defaults, **django_defaults).items():
                self[k] = getattr(settings, "GNOTTY_%s" % k, v)
            self.set_max_message_length()
        except ImportError:
            pass

    def set_max_message_length(self):
        extra_message_chars = "#PRIVMSG %s :\r\n" % self["IRC_CHANNEL"]
        self["MAX_MESSAGE_LENGTH"] = 512 - len(extra_message_chars)

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
        self.set_max_message_length()
        self["STATIC_URL"] = "/static/"


settings = Settings()
