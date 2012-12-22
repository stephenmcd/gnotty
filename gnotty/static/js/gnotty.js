
WEB_SOCKET_SWF_LOCATION = '/static/swf/WebSocketMain.swf';

/*

Manages a connection to an IRC room - takes an options objects
that should include the following members:

    - httpHost:     HTTP host for the gnotty WebSocket server.
    - httpPort:     HTTP port for the gnotty WebSocket server.
    - ircHost:      IRC host to connect to.
    - ircPort:      IRC port to connect to.
    - ircChannel:   IRC channel to join.
    - ircNickname:  IRC nickname.
    - ircPassword:  IRC password (optional).

The follwing methods are implemented:

    - message(message):         Sends a message string to the channel
    - leave():                  Disconnect from the channel
    - onJoin():                 Called when the client has joined the channel
    - onInvalid():              Called if the nickname used is invalid, eg:
                                too long, or contains invalid characters.
    - onNickNames(nicknames):   Called each time someone joins or leaves the
                                channel, nicknames is an unsorted array of
                                strings.
    - onMessage(message):       Called when a message is received from the
                                channel, message is an object with nickname
                                and message string members.
    - onLeave():                Called when client.leave() has completed

*/
var IRCClient = function(options) {

    var self = this;
    for (var k in options) {
        self[k] = options[k];
    }

    var host = options.httpHost == '0.0.0.0' ? '' : options.httpHost;
    self.socket = io.connect(host + ':' + options.httpPort, {
        transports: ['websocket', 'htmlfile', 'xhr-multipart',
                     'xhr-polling', 'jsonp-polling']
    });

    self.message = function(message) {
        self.socket.emit('message', message);
    };

    self.leave = function() {
        self.socket.disconnect();
        if (self.onLeave) {
            var interval = setInterval(function() {
                if (!self.socket.socket.connected) {
                    clearInterval(interval);
                    self.onLeave();
                }
            }, 100);
        }
    };

    self.socket.on('connect', function() {
        self.socket.emit('start', options.ircHost, options.ircPort,
                                  options.ircChannel, options.ircNickname,
                                  options.ircPassword);
    });

    self.socket.on('join', function() {
        if (self.onJoin) {
            self.onJoin();
        }
    });

    self.socket.on('invalid', function() {
        self.socket.disconnect();
        if (self.onInvalid) {
            self.onInvalid();
        } else {
            alert('Invalid nickname');
        }
    });

    self.socket.on('nicknames', function(nicknames) {
        if (self.onNicknames) {
            self.onNicknames(nicknames);
        }
    });

    self.socket.on('message', function(nickname, message, color) {
        if (self.onMessage) {
            self.onMessage({
                nickname: nickname,
                message: message,
                color: color
            });
        }
    });

};

// UI setup.
var gnotty = function(options) {

    var focused = true;
    var joining = false;
    var unread = 0;
    var title = $('title').text();

    // Main setup function called when nickname is entered.
    // Creates IRC client and sets up event handlers.
    var start = function(nickname, password) {

        // Start the IRC client.
        joining = true;
        options.ircNickname = nickname;
        options.ircPassword = password;
        client = new IRCClient(options);

        // Set up the loading animation.
        $('.loading').modal({backdrop: 'static'}).css({opacity: 0.7});
        var bar = $('.loading .bar');
        var width = $('.loading .progress').css({opacity: 0.5}).width();
        var connectTimeout = 30000;
        $('.loading .bar').animate({width: width}, connectTimeout / 2);

        // Fade the page out and reload it whenever we're finished,
        // such as an error occurring, or explicitly leaving.
        client.onLeave = function() {
            $('body').fadeOut('fast', function() {
                location = location.href.split('?')[0];
            });
        };

        // Error handler - shows an error message, and leaves.
        var error = function(message) {
            if (message) {
                alert(message);
            }
            client.leave();
        };

        // Took too long to connect.
        var timeout = setTimeout(function() {
            error('Took too long to connect, please try again');
        }, connectTimeout);

        // Name in use, too long, invalid chars.
        client.onInvalid = function() {
            error('Invalid nickname, please try again');
        };

        // Animations for setting up the main chat interface
        // once successfully joined.
        var joined = function() {
            $('.loading').modal('hide');
            $('#password').hide();
            $('#input').removeClass('nick').addClass('msg');
            $('#input').animate({width: '65%'}, function() {
                $('#input').attr('placeholder', 'message');
                $('#leave').fadeIn();
                $('.hidden').slideDown(function() {
                    $('#submit').addClass('submit-joined').val('Send');
                    $('#messages').fadeIn();
                }).removeClass('hidden');
            });
            $('#leave').click(function() {
                client.leave();
            });
        }

        // On join, finish the progress animation.
        client.onJoin = function() {
            joining = false;
            bar.stop().animate({width: width}, 500);
            clearTimeout(timeout);
            var interval = setInterval(function() {
                if (bar.width() == width) {
                    clearInterval(interval);
                    joined();
                }
            }, 100);
        };

        // Render the nickanmes list each time we receive it,
        // which is each time someone joins or leaves.
        client.onNicknames = function(nicknames) {
            var data = {nicknames: nicknames};
            $('#nicknames').html($('#nicknames-template').tmpl(data));
        };

        // Message received handler.
        client.onMessage = function(data) {

            if ((data.message == 'joins' || data.message == 'leaves')
                && !showJoinsAndLeaves()) {
                return;
            }

            // Add a timestamp to each message as we receive it, and
            // add it to the messages display.
            var d = new Date();
            var parts = [d.getHours(), d.getMinutes(), d.getSeconds()];
            data.time = $.map(parts, function(s) {
                return (String(s).length == 1 ? '0' : '') + s;
            }).join(':')

            data.message = urlize($('<div>').text(data.message).html());

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
        if (!joining && value) {
            if ($('.hidden').length > 0) {
                start(value, $('#password').val());
            } else {
                client.message(value);
            }
        }
        $('#input').val('').focus();
        return false;
    });

    // Wat. Enter key stops triggering the above form submit if the
    // submit button is not visible via media queries on small
    // devices, so we need to trigger it manually here.
    $('#input').keypress(function(e) {
        if (e.keyCode == 13) {
            $('.chat').submit();
            return false;
        }
    });

    // Join if there's a nickname in the querystring.
    var parts = location.href.split('?nickname=');
    if (parts.length == 2) {
        start(parts[1].split('&')[0]);
    }

    // When the window loses focus, reset the unread messages count.
    $(window).blur(function() {
        unread = 0;
        focused = false;
    });

    // When the window regains focus, remove the unread messages
    // count from the page title.
    $(window).focus(function() {
        focused = true;
        $('title').text(title);
    });

    // Focus the main input box on first load.
    $('#input').val('').focus();

    // Only add the password field when we're on the actual chat
    // interface, since having it in the archive interfaces
    // would result in the password being put into the
    // querystring when the join form is submitted regularly.
    $('#input').after('<input type="password" class="input-xlarge" ' +
                      'id="password" placeholder="password (optional)" ' +
                      'name="password" autocomplete="off">');

    // Remove the action of the form for the show joins/leaves checkbox.
    // This prevents the page from being reloaded, which is what happens
    // (triggered in show-joins-leaves.js) when the checkbox changes,
    // in any of the archive views, since we need to reload to
    // to show any changes triggered by this, but when we're chatting
    // in the channel, this happens on the fly.
    $('#joins-leaves').attr({action: ''});

};
