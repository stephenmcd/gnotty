
from calendar import Calendar, SUNDAY
from datetime import datetime, date

from django.db.models import Q
from django.shortcuts import render, redirect

from gnotty.models import IRCMessage
from gnotty.conf import settings


def chat(request, template="gnotty/chat.html"):
    return render(request, template, settings)


def messages(request, year=None, month=None, day=None,
             template="gnotty/messages.html"):
    """
    Show messages for the given query or day.
    """

    query = request.REQUEST.get("q")
    if query:
        search = Q(message__icontains=query) | Q(nickname__icontains=query)
        messages = IRCMessage.objects.filter(search).order_by("-message_time")
    elif year and month and day:
        messages = IRCMessage.objects.filter(message_time__year=year,
                                             message_time__month=month,
                                             message_time__day=day)
    else:
        return redirect("gnotty_year", year=datetime.now().year)

    context = {"messages": messages}
    return render(request, template, context)


def calendar(request, year=None, month=None, template="gnotty/calendar.html"):
    """
    Show calendar months for the given year/month.
    """

    try:
        year = int(year)
    except TypeError:
        year = datetime.now().year
    lookup = {"message_time__year": year}
    if month:
        lookup["message_time__month"] = month
    days = [d.date() for d in
            IRCMessage.objects.filter(**lookup).dates("message_time", "day")]
    min_date, max_date = days[0], days[-1]
    days = set(days)
    months = []
    calendar = Calendar(SUNDAY)

    for m in range(1, 13) if not month else [int(month)]:
        lt_max = m <= max_date.month or year < max_date.year
        gt_min = m >= min_date.month or year > min_date.year
        if lt_max and gt_min:
            weeks = calendar.monthdatescalendar(year, m)
            for w, week in enumerate(weeks):
                for d, day in enumerate(week):
                    weeks[w][d] = {
                        "date": day,
                        "in_month": day.month == m,
                        "has_messages": day in days,
                    }
            months.append({"month": date(year, m, 1), "weeks": weeks})

    context = {"months": months}
    return render(request, template, context)
