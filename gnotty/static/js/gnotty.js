
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
