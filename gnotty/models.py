
from django.db import models
from django.utils.translation import ugettext_lazy as _

from gnotty.client import color


class IRCMessage(models.Model):
    """
    An IRC message logged by the DjangoBot from the
    ``run_gnotty`` management command.
    """

    nickname = models.CharField(_("Nickname"), max_length=100)
    message = models.TextField(_("Message"))
    server = models.CharField(_("Server"), max_length=100)
    channel = models.CharField(_("Channel"), max_length=100)
    message_time = models.DateTimeField(_("Time"), auto_now_add=True)
    join_or_leave = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ("message_time",)

    def __unicode__(self):
        return "[%s] %s%s %s: %s" % (self.message_time, self.server,
                                     self.channel, self.nickname,
                                     self.short_message())

    @models.permalink
    def get_absolute_url(self):
        kwargs = {
            "year": self.message_time.year,
            "month": self.message_time.month,
            "day": self.message_time.day,
        }
        return ("gnotty_day", (), kwargs)

    def short_message(self):
        return self.message[:50]
    short_message.short_description = _("Message")

    def color(self):
        return color(self.nickname)
