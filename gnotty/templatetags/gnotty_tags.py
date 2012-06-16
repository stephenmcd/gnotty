
from django import template
from django.db.models import Min, Max

from gnotty.models import IRCMessage
from gnotty.settings import IRC_CHANNEL


register = template.Library()


@register.inclusion_tag("gnotty/includes/header.html")
def gnotty_header():
    min_max = IRCMessage.objects.aggregate(Min("message_time"),
                                           Max("message_time"))
    if min_max:
        years = range(min_max["message_time__max"].year,
                      min_max["message_time__min"].year - 1, -1)
    else:
        years = []
    return {"IRC_CHANNEL": IRC_CHANNEL, "years": years}
