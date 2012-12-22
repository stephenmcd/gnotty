
var gnottyCookieName = 'gnotty-hide-joins-leaves';

// Checks the joins/leaves cookie and returns false if its
// checkbox has been unchecked, and join/leave messages
// should be filtered server-side for the archive, or client-side
// in the chat interface.
var showJoinsAndLeaves = function() {
    var at = ('; ' + document.cookie).indexOf('; ' + gnottyCookieName + '=');
    var cookieValue = '';
    if (at > -1) {
        at += gnottyCookieName.length + 1;
        cookieValue = document.cookie.substr(at).split(';')[0];
    }
    return cookieValue != '1';
};

// Sets the joins/leaves cookie on change of its checkbox. We
// also reload the page by default (for all of the archive views)
// as the value of the cookie is used server-side. In the case of
// the chat interface, the action of the form is removed and we
// don't reload, since the cookie value is checked for on the fly
// during a chat session.
$(function() {
    var joinsLeavesCheckbox = $('#show-joins-leaves');
    joinsLeavesCheckbox.attr({checked: showJoinsAndLeaves()});
    joinsLeavesCheckbox.change(function() {
        var cookieValue = this.checked ? '' : '1';
        document.cookie = gnottyCookieName + '=' + cookieValue + '; path=/';
        if (this.form.action != location.href) {
            location.reload();
        }
        return true;
    });
});
