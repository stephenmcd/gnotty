
/*

Manages a connection to an IRC room - takes an options objects
that should include the following members:

    - httpHost:     HTTP host for the gnotty WebSocket server.
    - httpPort:     HTTP port for the gnotty WebSocket server.
    - ircHost:      IRC host to connect to.
    - ircPort:      IRC port to connect to.
    - ircChannel:   IRC channel to join.
    - ircNickname:  IRC nickname.

The follwing methods are implemented:

    - message(message):         Sends a message string to the channel
    - onConnect():              Called when the client has joined the channel
    - onNickNames(nicknames):   Called each time someone joins or leaves the
                                channel, nicknames is an unsorted array of
                                strings.
    - onMessage(message):       Called when a message is received from the
                                channel, message is an object with nickname
                                and message string members.

*/
var IRCClient = function(options) {

    var self = this;
    for (var k in options) {
        self[k] = options[k];
    }

    var socket = io.connect(options.httpHost + ':' + options.httpPort)

    self.message = function(message) {
        socket.emit('message', message);
    };

    socket.on('connect', function() {
        socket.emit('start', options.ircHost, options.ircPort,
                             options.ircChannel, options.ircNickname);
        if (self.onConnect) {
            self.onConnect();
        }
    });

    socket.on('nicknames', function(nicknames) {
        if (self.onNicknames) {
            self.onNicknames(nicknames);
        }
    });

    socket.on('message', function(nickname, message) {
        if (self.onMessage) {
            self.onMessage({nickname: nickname, message: message});
        }
    });

};

// UI setup.
var gnotty = function(options) {

    var focused = true;
    var unread = 0;
    var title = $('title').text();

    // Assign a dark colour to each nickname.
    var colors = {};
    var color = function(nickname) {
        if (!colors[nickname]) {
            var c = function() {
                return Math.ceil(Math.random() * 150);
            };
            colors[nickname] = 'rgb(' + c() + ',' + c() + ',' + c() + ')';
        }
        return colors[nickname];
    };

    // Main setup function called when nickname is entered.
    // Creates IRC client and sets up event handlers.
    var start = function(nickname) {

        options.ircNickname = nickname;
        client = new IRCClient(options);

        // Once connected, show the 'leaves' button, user list,
        // and change the submit text to 'Send' for sending messages.
        client.onConnect = function() {
            $('#input').animate({width: '65%'}, function() {
                $('#input').attr('placeholder', 'message');
                $('.hidden').slideDown(function() {
                    $('#submit').val('Send');
                }).removeClass('hidden');
            });
        };

        // Render the nickanmes list each time we receive it,
        // which is each time someone joins or leaves.
        client.onNicknames = function(nicknames) {
            nicknames = $.map(nicknames.sort(), function(nickname) {
                return {nickname: nickname, color: color(nickname)};
            });
            var data = {nicknames: nicknames};
            $('#nicknames').html($('#nicknames-template').tmpl(data));
        };

        client.onMessage = function(data) {

            // Add a timestamp to each message as we receive it, and
            // add it to the messages display.
            var d = new Date();
            var parts = [d.getHours(), d.getMinutes(), d.getSeconds()];
            data.time = $.map(parts, function(s) {
                return (String(s).length == 1 ? '0' : '') + s;
            }).join(':')
            data.color = color(data.nickname);

            // Auto-scroll the window if we're at the bottom of the
            // messages list. We need to calculate it before we add
            // actual message to the list.
            var win = $(window);
            var doc = $(window.document);
            var bottom = win.scrollTop() + win.height() >= doc.height();
            $('#messages-template').tmpl(data).appendTo('#messages');
            if (bottom) {
                window.scrollBy(0, 10000);
            }

            // Add the number of unread messages to the title if the
            // page isn't focused.
            if (!focused) {
                unread += 1;
                var s = (unread == 1 ? '' : 's');
                $('title').text('(' + unread + ' message' + s + ') ' + title);
            }

        };

    };

    // Main submit handler - if there are still hidden elements,
    // we haven't connected yet, so the value submitted is the
    // initial nickname. Otherwise we've started, and the value
    // submitted is a message.
    $('.chat').submit(function() {
        var value = $('#input').val();
        if (value) {
            if ($('.hidden').length > 0) {
                start(value);
            } else {
                client.message(value);
            }
        }
        $('#input').val('').focus();
        return false;
    });

    // Leaves just reloads - this will trigger a disconnect for
    // the client.
    $('#leave').click(function() {
        location = location.href.split('?')[0];
    });

    // Join if there's a nickname in the querystring.
    var parts = location.href.split('?nickname=');
    if (parts.length == 2) {
        start(parts[1].split('&')[0]);
    }

    $(window).focus(function() {
        focused = true;
        $('title').text(title);
    });

    $(window).blur(function() {
        unread = 0;
        focused = false;
    });

    $('#input').val('').focus();

};
