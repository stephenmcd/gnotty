======
Gnotty
======

Created by `Stephen McDonald <http://twitter.com/stephen_mcd>`_

Gnotty ties the knot between the web and IRC. It is designed to assist
open source projects that host an IRC channel for collaboration on
their project.
Gnotty is `BSD licensed <http://www.linfo.org/bsdlicense.html>`_.

Gnotty is comprised of several parts. Primarily Gnotty provides a
modern web client for communicating with an IRC channel via a web
browser. The web server uses `gevent <http://www.gevent.org>`_ and
`WebSockets <http://en.wikipedia.org/wiki/WebSockets>`_, which provide
the communication layer between the IRC channel and the web browser.
Twitter's `Bootstrap <http://twitter.github.com/bootstrap/>`_ is used
to style the web interface, providing a fully responsive layout
suitable for use with mobile devices. Customisable templates are also
provided for skinning the chat interface.

Check out the `Gnotty live demo <http://gnotty.jupo.org>`_ to see the
web interface in action.

Secondly, Gnotty provides the ability to run a highly customisable
IRC bot. Different classes of bots can be configured on startup, and
bots can perform different services such as message logging and
interacting with users in the IRC channel. Bots also contain webhooks,
which allows bots to receive input over HTTP from external services.

Gnotty also provides an optional Django application for archiving IRC
messages for browsing and searching via a web interface. By default
the IRC bot uses Python's logging module to provide configurable
logging handlers for IRC messages. When the Django application is
used, a logging handler is added that logs all IRC messages to the
Django project's database. The Django application then provides all
the necessary views and templates for messages to be searched by
keyword, or browsed by date with monthly calendars.

Note that the Django application is entirely optional. Gnotty can
be run without using Django at all, as a stand-alone gevent web
server that provides the web interface to an IRC channel, with
configurable IRC bots.

Installation
============

The easiest way to install Gnotty is directly from PyPi using
`pip <http://www.pip-installer.org>`_ by running the command below::

    $ pip install -U gnotty

Otherwise you can download Gnotty and install it directly from
source::

    $ python setup.py install

Configuration
=============

Gnotty is configured via a handful of settings. When integrated
with Django, these settings can be defined in your Django project's
``settings.py`` module. When Gnotty is run as a stand-alone
client, these same settings can be defined via the command line, or
in a separate Python configuration module. See the "Stand-Alone Web
Client" section below for details.

  * ``GNOTTY_IRC_HOST`` - IRC host address to connect to.
    *string, default: irc.freenode.net*
  * ``GNOTTY_IRC_PORT`` - IRC port to connect to.
    *integer, default: 6667*
  * ``GNOTTY_HTTP_HOST`` - HTTP host address to serve from.
    *string, default: 127.0.0.1*
  * ``GNOTTY_HTTP_PORT`` - HTTP port to serve from.
    *integer, default: 8080*
  * ``GNOTTY_IRC_CHANNEL`` - IRC channel to join.
    *string, default: #gnotty*
  * ``GNOTTY_BOT_CLASS`` - Dotted Python path to the IRC client bot
    class to run.
    *string, default: gnotty.bots.BaseBot*
  * ``GNOTTY_BOT_NICKNAME`` - IRC nickname the logging client will
    use.
    *string, default: gnotty*
  * ``GNOTTY_BOT_PASSWORD`` - Optional IRC password for the bot.
    *string, default: None*
  * ``GNOTTY_DAEMON`` - run in daemon mode.
    *boolean, default: False*
  * ``GNOTTY_PID_FILE`` - path to write PID file to when in daemon
    mode.
    *string, default: [tmp]/gnotty-[http-host]-[http-port].pid*
  * ``GNOTTY_LOG_LEVEL`` - Log level to use. ``DEBUG`` will spew out
    all IRC data.
    *string, default: INFO*

To be clear: the IRC host and port are for specifing the IRC server to
connect to. The HTTP host and port are what will be used to host the
gevent/WebSocket server.

Django Integration
==================

With the above settings defined in your Django project's
``settings.py`` module, a few more steps are required. As with most
Django apps, add ``gnotty`` to your ``INSTALLED_APPS`` setting, and
``gnotty.urls`` to your project's ``urls.py`` module::

    # settings.py
    INSTALLED_APPS = (
        # other apps here
        'gnotty',
    )

    # urls.py
    from django.conf.urls.defaults import patterns, include, url
    urlpatterns = patterns('',
        # other patterns here
        ('^irc/', include('gnotty.urls')),
    )

As you can see we've mounted all of the urls Gnotty provides under
the prefix ``/irc/`` - feel free to use whatever suits you here. With
this prefix, the URL on our Django development server
`http://127.0.0.1:8000/irc/ <http://127.0.0.1:8000/irc/>`_ will load
the chat interface to the IRC channel, along with a search form for
searching the message archive, and links to browsing the archive by
date.

The final step when integrated with Django is to run the Gnotty
server itself. The Gnotty server is backed by gevent, and will host
the WebSocket bridge to the IRC channel. It will also start up the
IRC bot that will connect to the channel, and log all of the messages
in the channel to the database archive.

Running the Gnotty server when integrated with Django is simply a
matter of running the ``gnottify`` Django management command::

    $ python manage.py gnottify

Stand-Alone Web Client
======================

As mentioned, Gnotty can also be run as a stand-alone web client
without using Django at all. In this mode, only the web interface to
the IRC channel is provided, along with whichever IRC bot class is
configured. Message logging can be configured using standard handlers
for the ``logging`` module in Python's standard library.

Once installed, the command ``gnottify`` should be available on your
system, and all of the options described earlier can be provided as
arguments to it::

    $ gnottify --help
    Usage: gnottify [options]

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -A HOST, --irc-host=HOST
                            IRC host address to connect to
                            [default: irc.freenode.net]
      -P PORT, --irc-port=PORT
                            IRC port to connect to
                            [default: 6667]
      -a HOST, --http-host=HOST
                            HTTP host address to serve from
                            [default: 127.0.0.1]
      -p PORT, --http-port=PORT
                            HTTP port to serve from
                            [default: 8080]
      -C CHANNEL, --irc-channel=CHANNEL
                            IRC channel to join
                            [default: #gnotty]
      -c DOTTED_PYTHON_PATH, --bot-class=DOTTED_PYTHON_PATH
                            Dotted Python path to the IRC client bot class to run
                            [default: gnotty.bots.LoggingBot]
      -n NICKNAME, --bot-nickname=NICKNAME
                            IRC nickname the bot will use
                            [default: gnotty]
       -x PASSWORD, --bot-password=PASSWORD
                            Optional IRC password for the bot
                            [default: None]
      -D, --daemon          run in daemon mode
      -k, --kill            Shuts down a previously started daemon
      -F FILE_PATH, --pid-file=FILE_PATH
                            path to write PID file to when in daemon mode
      -l INFO|DEBUG, --log-level=INFO|DEBUG
                            Log level to use. DEBUG will spew out all IRC
                            data.
                            [default: INFO]
      -f FILE_PATH, --conf-file=FILE_PATH
                            path to a Python config file to load options from

Note the final argument in the list, ``--conf-file``. This can be used
to provide the path to a Python config module, that contains each of
the settings described earlier. Any options provided via command-line
arguments will take precedence over any options defined in the Python
configuration module.

Daemon Mode
===========

Gnotty can be configured to run as a background process when the
``GNOTTY_DAEMON`` setting is set to ``True`` (the ``--daemon`` arg
when running stand-alone). When in daemon mode, Gnotty will write its
process ID to the absolute file path specfified by the
``GNOTTY_PID_FILE`` setting (the ``--pid-file`` arg when running
stand-alone). If the PID file path is not configured, Gnotty will use
a file name based on the HTTP host and port, in your operating
system's location for temporary files.

When run in daemon mode, Gnotty will check for an existing PID file
and if found, will attempt to shut down a previously started server
with the same PID file.

IRC Bots
========

When running, Gnotty hosts an IRC bot that will connect to the
configured IRC channel. The ``gnotty.bots.BaseBot`` bot is run by
default, which implements message logging and an empty interface for
webhooks, which allows the IRC bot to receive data over HTTP.

You can implement your own IRC bot simply by subclassing
``gnotty.bots.BaseBot`` and defining the Python dotted path to it on
startup, via the ``GNOTTY_BOT_CLASS`` setting (the ``--bot-class`` arg
when running stand-alone).

The ``gnotty.bots.BaseBot`` class is derived from the third-party
``irclib`` package's ``irc.client.SimpleIRCClient`` class (and
translated into a Python new-style class for sanity). Consult the
``irclib`` docs and code for details about each of the methods that
are implemented for handling events with an IRC channel.

These are the built-in IRC bot classes provided by the
``gnotty.bots`` module:

  * ``gnotty.bots.BaseBot`` - The default bot class that implements
    logging and webhooks. Your custom bots should subclass this.
  * ``gnotty.bots.ChatBot`` - A bot that demonstrates interacting with
    the IRC channel by greeting and responding to other users.
    Requires the ``nltk`` package to be installed.
  * ``gnotty.bots.CommitBot`` - A base bot class for receiving commit
    information for version control systems via bot webhooks, and
    relaying the commits to the IRC channel. Used as the base for the
    ``GitHubBot`` and ``BitBucketBot`` classes.
  * ``gnotty.bots.GitHubBot`` - ``CommitBot`` subclass for
    `GitHub <http://github.com>`_
  * ``gnotty.bots.BitBucketBot`` - ``CommitBot`` subclass for
    `Bitbucket <http://bitbucket.org>`_

Bot Webhooks
============

IRC bots run by Gnotty contain the ability to receive data over HTTP
via webhooks. The gevent web server will intercept any URLs prefixed
with the path ``/webhook/``, and pass the request onto the
``on_webhook`` method defined on the bot class running. The
``on_webhook`` method receives the following arguments:

  * ``environ`` - The raw environment dict supplied by the gevent web
    server that contains all information about the HTTP request.
  * ``url`` - The actual URL accessed.
  * ``params`` - A dictionary containing all of the POST and GET data.

Note that the ``url`` and ``params`` arguments are provided for
convenience, with their values retrieved from the ``environ``
argument.

Here's an example bot implementing a webhook that reads a
query-string value and sends it to the IRC channel::

  # in my_bot.py

  from gnotty.bots import BaseBot

  class MyWebhookBot(BaseBot):
      def on_webhook(self, environ, url, params):
          # Get the "message" query-string parameter.
          self.message_channel(params["message"])

Then with Gnotty started using the following arguments::

  $ gnottify --http-host=127.0.0.1 --http-port=8000 --bot-class=my_bot.MyWebhookBot

Hitting the URL ``http://127.0.0.1:8000/webhook/?message=Hello`` would
cause the bot to send the message "Hello" to the IRC channel.

Message Logging
===============

By default, each IRC message in the channel is logged by the IRC bot
run by Gnotty. Logging occurs using `Python's logging module
<http://docs.python.org/library/logging.html>`_, to the logger named
``irc.message``.

Each log record contains the following attributes, where ``record`` is
the log record instance:

  * ``record.server`` - The IRC server the message occurred on.
  * ``record.channel`` - The IRC channel the message occurred on.
  * ``record.nickname`` - The nickname of the user who sent the
    message.
  * ``record.msg`` - The message itself.

Here's an example of adding an extra logging handler for IRC messages::

  from logging import getLogger, StreamHandler

  class MyLogHandler(StreamHandler):
      def emit(self, record):
          # Do something cool with the log record.
          print record.msg

  getLogger("irc.message").addHandler(MyLogHandler())

JavaScript Client
=================

The web client that Gnotty provides includes all the necessary
JavaScript files for communicating with the WebSocket server, such as
Douglas Crockford's ``json2.js``, and the ``socket.io.js`` library
itself. Also provided is the file ``gnotty.js`` which implements a
couple of public functions used by the web interface. The first is the
``gnotty`` JavaScript function, which deals directly with the HTML
structure of the chat template::

    // Start up the default UI. This function isn't very
    // interesting, since it's bound to the HTML provided
    // by Gnotty's chat template.
    gnotty({
        httpHost:     '127.0.0.1',
        httpPort:     '8080',
        ircHost:      'irc.freenode.net',
        ircPort:      '6667',
        ircChannel:   '#gnotty'
    });

The second interface is the ``IRCClient`` function. This is of
particular interest if you'd like to create your own chat interface,
as it deals exclusively with communication between the web browser and
the WebSocket server. Here's an example client that simply writes
events out to the console::

    // Prompt the user for a nickname and create a IRC client.
    var client = new IRCClient({
        httpHost:     '127.0.0.1',
        httpPort:     '8080',
        ircHost:      'irc.freenode.net',
        ircPort:      '6667',
        ircChannel:   '#gnotty',
        ircNickname:  prompt('Enter a nickname:')
        ircPassword:  prompt('Enter a password (optional):')
    });

    // When the client first joins the IRC channel,
    // send a message to the channel to say hello.
    client.onJoin = function() {
        console.log('joined the channel');
        client.message('Hello, is it me you\'re looking for?');
    };

    // When someone joins or leaves the channel, we're given the
    // entire user list.
    client.onNicknames = function(nicknames) {
        console.log('The user list changed, here it is: ' + nicknames.join(', '));
    });

    // Whenever a message is received from the channel, it's an
    // object with nickname and message properties.
    client.onMessage = function(data) {
        console.log(data.nickname + ' wrote: ' + data.message);
    });

    // When we leave, reload the page.
    client.onLeave = function() {
        location.reload();
    };

    // The IRC server rejected the nickname.
    client.onInvalid = function() {
        console.log('Invalid nickname, please try again.');
    };

As you may have guessed, the server-side settings configured for
Gnotty are passed directly into the ``gnotty`` JavaScript function,
which then creates its own ``IRCClient`` instance.
