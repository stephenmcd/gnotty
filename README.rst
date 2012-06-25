======
Gnotty
======

Created by `Stephen McDonald <http://twitter.com/stephen_mcd>`_

Gnotty ties the knot between the web and IRC. It is a web client and
message archive for IRC, designed to assist open source projects that
host an IRC channel for collaboration on their project. Gnotty is
`BSD licensed <http://www.linfo.org/bsdlicense.html>`_.

Gnotty is comprised of two parts. The first part is a web client
built with `gevent <http://www.gevent.org>`_ and
`WebSockets <http://en.wikipedia.org/wiki/WebSockets>`_. It provides a
web interface for connecting to an IRC channel and chatting with other
users in the channel.

The second part is a message archive. When configured, Gnotty will
launch an IRC bot that connects to the IRC channel, which logs all
messages in the channel to a database. A web interface is then provided
that allows messages to be searched by keyword, or browsed by date with
monthly calendars.

Gnotty is implemented as a `Django <http://djangoproject.com>`_
reusable app, but the web client can be run as a stand-alone service
without using Django at all. The integration with Django provides the
message archiving and search functionality, as well as a Django
management command for running the web client.

Gnotty uses Twitter's
`Bootstrap <http://twitter.github.com/bootstrap/>`_ to style its web
interface.

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
client, these same settings can be defined in a separate Python
configuration module, specified via the command line.

  * ``GNOTYY_IRC_HOST`` - IRC host address to connect to.
    *default: irc.freenode.net*
  * ``GNOTTY_IRC_PORT`` - IRC port to connect to.
    *default: 6667*
  * ``GNOTTY_HTTP_HOST`` - HTTP host address to serve from.
    *default: 127.0.0.1*
  * ``GNOTTY_HTTP_PORT`` - HTTP port to serve from.
    *default: 8080*
  * ``GNOTTY_IRC_CHANNEL`` - IRC channel to join.
    *default: #gnotty*
  * ``GNOTTY_LOGGER_NICKNAME`` - IRC nickname the logging client will use.
    *default: gnotty*

To be clear: the IRC host and port are for specifing the IRC server to
connect to. The HTTP host and port are what will be used to host the
gevent/WebSocket server.

Django Integration
==================

With the above settings defined in your Django project's ``settings.py``
module, a few more steps are required. As with most Django apps, add
Gnotty to your ``INSTALLED_APPS`` setting, and ``gnotty.urls`` to
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
the IRC channel is provided, and no message logging and search is
available.

Once installed, the command ``gnottify`` should be available on your
system, and all of the options described earlier can be provided as
arguments to it::

    $ gnottify --help
    Usage: server.py [options]

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -a HOST, --irc-host=HOST
                            IRC host address to connect to
      -p PORT, --irc-port=PORT
                            IRC port to connect to
      -A HOST, --http-host=HOST
                            HTTP host address to serve from
      -P PORT, --http-port=PORT
                            HTTP port to serve from
      -c CHANNEL, --irc-channel=CHANNEL
                            IRC channel to join
      -n NICKNAME, --logger-nickname=NICKNAME
                            IRC nickname the logging client will use
      -f PATH, --conf-file=PATH
                            path to a Python config file to load options from

Note the final argument in the list, ``--conf-file``. This can be used
to provide the path to a Python config module, that contains each of
the settings described earlier. Any options provided via command-line
arguments will take precedence over any options defined in the Python
configuration module.

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
    });

    // When the client is first connected to the IRC channel,
    // send a message to the channel to say hello.
    client.onConnect = function() {
        console.log('connected');
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

As you may have guessed, the server-side settings configured for Gnotty
are passed directly into the ``gnotty`` JavaScript function, which then
creates its own ``IRCClient`` instance.
