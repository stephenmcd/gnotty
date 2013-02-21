
try:
    from feedparser import parse
except ImportError:
    parse = None

from gnotty.bots import events


class RSSMixin(object):
    """
    Mixin for bots that consume RSS feeds and post them to the
    channel. Feeds are defined by the ``feeds`` keyword arg to
    ``__init__``, and should contain a sequence of RSS feed URLs.

    Requires the ``feedparser`` library to be installed.
    """

    def __init__(self, *args, **kwargs):
        if parse is None:
            from warnings import warn
            warn("RSSMixin requires feedparser installed")
        self.feeds = kwargs.pop("feeds", [])
        self.feed_items = set()
        # Consume initial feed items without posting them.
        self.parse_feeds(message_channel=False)
        super(RSSMixin, self).__init__(*args, **kwargs)

    @events.on("timer", seconds=60)
    def parse_feeds(self, message_channel=True):
        """
        Iterates through each of the feed URLs, parses their items, and
        sends any items to the channel that have not been previously
        been parsed.
        """
        if parse:
            for feed_url in self.feeds:
                feed = parse(feed_url)
                for item in feed.entries:
                    if item["id"] not in self.feed_items:
                        self.feed_items.add(item["id"])
                        if message_channel:
                            message = self.format_item_message(feed, item)
                            self.message_channel(message)
                            return

    def format_item_message(self, feed, item):
        item["feed_title"] = feed.feed.title or feed.url
        return "%(title)s: %(id)s (via %(feed_title)s)" % item

