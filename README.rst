======
Gnotty
======

Created by `Stephen McDonald <http://twitter.com/stephen_mcd>`_

``gnotty`` ties the knot between the web and IRC. It is designed to
assist open source projects that host an IRC channel for collaboration
on their project.

``gnotty`` is comprised of two parts. The first part is web client
built with `gevent`_ and `WebSockets`_. It provides a web interface
for connecting to an IRC channel and chatting with other users in the
channel.

The second part is a message archive. When configured, Gnotty will
launch an IRC bot that connects to the IRC channel, which logs all
messages in the channel to a database. A web interface is then provided
that allows messages to be searched by keyword, or browsed by date with
monthly calendars.

``gnotty`` is implemented as a `Django`_ reusable app, but the web
client can be run as a stand-alone service without using Django at all.
The integration with Django provides the message archiving and search
functionality, as well as a Django management command for running the
web client.

``gnotty`` uses Twitter's ``Bootstrap`` to implement its web
interfaces.

Installation
============

The easiest way to install ``gnotty`` is directly from PyPi using
`pip`_ by running the command below::

    $ pip install -U gnotty

Otherwise you can download ``gnotty`` and install it directly from
source::

    $ python setup.py install

Configuration
=============

``gnotty`` is configured via a handful of settings. When integrated
with Django, these settings can be defined in your Django project's
``settings.py`` module. When ``gnotty`` is run as a stand-alone
client, these same settings can be defined in a separate Python
configuration module, specified via the command line.

  * ``GNOTYY_IRC_HOST``: IRC host address to connect to.
  * ``GNOTTY_IRC_PORT``: IRC port to connect to.
  * ``GNOTTY_HTTP_HOST``: HTTP host address to serve from.
  * ``GNOTTY_HTTP_PORT``: HTTP port to serve from.
  * ``GNOTTY_IRC_CHANNEL``: IRC channel to join.
  * ``GNOTTY_LOGGER_NICKNAME``: IRC nickname the logging client will use.

To be clear: the IRC host and port are for specifing the IRC server to
connect to. The HTTP host and port are what will be used to host the
gevent/WebSocket server.

Django Integration
==================

With the above settings defined in your Django project's ``settings.py``
module, a few more steps are required. As with most Django apps, add
``gnotty`` to your ``INSTALLED_APPS`` setting, and ``gnotty.urls`` to
your project's ``urls.py`` module::

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

As you can see we've mounted all of the urls ``gnotty`` provides under
the prefix ``/irc/`` - feel free to use whatever suits you here. With
this prefix, the URL on our Django development server
`http://127.0.0.1:8000/irc/ <http://127.0.0.1:8000/irc/>`_ will load
the chat interface to the IRC channel, along with a search form for
searching the message archive, and links to browsing the archive by
date.

The final step when integrated with Django is to run the ``gnotty``
server itself. The ``gnotty`` server is backed by gevent, and will host
the WebSocket bridge to the IRC channel. It will also start up the
IRC bot that will connect to the channel, and log all of the messages
in the channel to the database archive.

Running the ``gnotty`` server when integrated with Django is simply a
matter of running the following Django management command::

    $ python manage.py run_gnotty

Stand-alone Web Client
======================

As mentioned, ``gnotty`` can also be run as a stand-alone web client
without using Django at all. In this mode, only the web interface to
the IRC channel is provided, and no message logging and search is
available.

Once installed, the command ``gnotty`` should be available on your
system, and all of the options described earlier can be provided as
arguments to it::

    $ gnotty --help
    Usage: server.py [options]

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -a HOST, --irc-host=HOST
                            IRC host address to connect to. [default: irc.freenode.net]
      -p PORT, --irc-port=PORT
                            IRC port to connect to. [default: 6667]
      -A HOST, --http-host=HOST
                            HTTP host address to serve from. [default: 127.0.0.1]
      -P PORT, --http-port=PORT
                            HTTP port to serve from. [default: 8080]
      -c CHANNEL, --irc-channel=CHANNEL
                            IRC channel to join. [default: #mezzanine]
      -n NICKNAME, --logger-nickname=NICKNAME
                            IRC nickname the logging client will use. [default: gnotty]
      -f PATH, --conf-file=PATH
                            Path to a Python config file to load options from.

Note the final argument in the list, ``--conf-file``. This can be used
to provide the path to a Python config module, that contains each of
the settings described earlier. Any options provided via command-line
arguments will take precedence over any options defined in the Python
configuration module.
