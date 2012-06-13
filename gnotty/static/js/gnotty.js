
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
