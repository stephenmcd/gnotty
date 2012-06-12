
from datetime import datetime
from django.db.models import Q
from django.shortcuts import render

from gnotty.models import IRCMessage


def chat(request, template="gnotty/chat.html"):
    context = {
        "host": "localhost",
        "port": 6667,
        "channel": "#test"
    }
    return render(request, template, context)


def search(request, template="gnotty/search.html"):
    messages = []
    query = request.REQUEST.get("q")
    if query:
        search = Q(message__icontains=query) | Q(nickname__icontains=query)
        messages = IRCMessage.objects.filter(search)
    context = {"messages": messages}
    return render(request, template, context)


def day(request, year, month, day, template="gnotty/day.html"):
    date = datetime(year=int(year), month=int(month), day=int(day))
    messages = IRCMessage.objects.filter(message_time_date=date)
    context = {"messages": messages}
    return render(request, template, context)
