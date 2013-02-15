
from json import loads

from gnotty.bots import events


class CommitMixin(object):
    """
    Base mixin for DCVS post-push webhooks. Defines the
    ``handle_payload`` method that accepts a  ``CommitPayload``
    instance, and converts it into messages to send back to the
    IRC channel.
    """

    def handle_payload(self, payload):
        commit = lambda c: "%s - %s" % (c["message"], payload.author(c))
        messages = [commit(c) for c in payload.commits()]
        if len(messages) == 1:
            commit_url = payload.commit_url(payload.commits()[0])
            messages[0] = "%s %s" % (messages[0], commit_url)
        else:
            messages.insert(0, "%s new commits:" % len(payload.commits()))
            messages.append("Compare view: %s" % payload.diff_url())
        for message in messages:
            self.message_channel(message)


class CommitPayload(object):
    """
    Base class for commit payloads. Commit payloads define each
    of the methods for extracting the relevant bits of information
    from the commit payload, that ``CommitMixin`` expects in order
    to be able to convert the commits into messages.
    """

    def __init__(self, payload):
        self.payload = payload

    def commits(self):
        return self.payload["commits"]

    def author(self, commit):
        raise NotImplementedError

    def commit_url(self, commit):
        raise NotImplementedError

    def diff_url(self):
        raise NotImplementedError


class GitHubPayload(CommitPayload):
    """
    GitHub payload handler.
    """

    def author(self, commit):
        return commit["committer"]["name"]

    def commit_url(self, commit):
        return commit["url"]

    def diff_url(self):
        return self.payload["compare"].replace("^", "")


class GitHubMixin(CommitMixin):
    """
    Mixin for GitHub post-push webhook bot.
    """

    @events.on("webhook", urlpattern="^/webhook/github/$")
    def github_payload(self, environ, url, params):
        payload = loads(params["payload"])
        self.handle_payload(GitHubPayload(payload))


class BitBucketPayload(CommitPayload):
    """
    Mixin for Bitbucket post-push webhook bot.
    """

    def repo_url(self):
        host = self.payload["canon_url"]
        return "%s%s" % (host, self.payload["repository"]["absolute_url"])

    def author(self, commit):
        return commit["raw_author"].split("<")[0]

    def commit_url(self, commit):
        return "%schangeset/%s/" % (self.repo_url(), commit["node"])

    def diff_url(self):
        first, last = self.commits()[0]["node"], self.commits()[-1]["node"]
        return "%scompare/%s..%s" % (self.repo_url(), first, last)


class BitBucketMixin(CommitMixin):
    """
    Bitbucket payload handler.
    """

    @events.on("webhook", urlpattern="^/webhook/bitbucket/$")
    def bitbucket_payload(self, environ, url, params):
        payload = loads(params["payload"])
        self.handle_payload(BitBucketPayload(payload))
