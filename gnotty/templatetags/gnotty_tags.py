
from django import template
from django.conf import settings as django_settings
from django.db.models import Min, Max

from gnotty.models import IRCMessage
from gnotty.conf import settings


register = template.Library()


@register.inclusion_tag("gnotty/includes/nav.html", takes_context=True)
def gnotty_nav(context):
    min_max = IRCMessage.objects.aggregate(Min("message_time"),
                                           Max("message_time"))
    if min_max.values()[0]:
        years = range(min_max["message_time__max"].year,
                      min_max["message_time__min"].year - 1, -1)
    else:
        years = []
    context["IRC_CHANNEL"] = settings.IRC_CHANNEL
    context["years"] = years
    context["LOGOUT_URL"] = django_settings.LOGOUT_URL
    return context
