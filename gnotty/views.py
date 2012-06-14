
from datetime import date

from django.conf import settings
from django.db.models import Q
from django.shortcuts import render

from gnotty.models import IRCMessage
from gnotty.settings import (IRC_HOST, IRC_PORT, IRC_CHANNEL,
                             HTTP_HOST, HTTP_PORT)


def chat(request, template="gnotty/chat.html"):
    context = {
        "IRC_HOST": IRC_HOST,
        "IRC_PORT": IRC_PORT,
        "IRC_CHANNEL": IRC_CHANNEL,
        "HTTP_HOST": HTTP_HOST,
        "HTTP_PORT": HTTP_PORT,
    }
    return render(request, template, context)


def search(request, template="gnotty/search.html"):
    messages = []
    query = request.REQUEST.get("q")
    if query:
        search = Q(message__icontains=query) | Q(nickname__icontains=query)
        messages = IRCMessage.objects.filter(search).order_by("-message_time")
    context = {"messages": messages}
    return render(request, template, context)


def day(request, year, month, day, template="gnotty/day.html"):
    day_date = date(year=int(year), month=int(month), day=int(day))
    messages = IRCMessage.objects.filter(message_time__year=year,
                                         message_time__month=month,
                                         message_time__day=day)
    context = {"messages": messages, "date": day_date}
    return render(request, template, context)
