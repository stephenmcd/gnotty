
from calendar import Calendar, SUNDAY
from datetime import datetime, date, timedelta

from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.messages import info, error
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render, redirect

from gnotty.models import IRCMessage
from gnotty.conf import settings


def hide_joins_and_leaves(request):
    return request.COOKIES.get("gnotty-hide-joins-leaves", "") == "1"


def chat(request, template="gnotty/chat.html"):
    context = dict(settings)
    return render(request, template, context)


def messages(request, year=None, month=None, day=None,
             template="gnotty/messages.html"):
    """
    Show messages for the given query or day.
    """

    query = request.REQUEST.get("q")
    prev_url, next_url = None, None
    messages = IRCMessage.objects.all()
    if hide_joins_and_leaves(request):
        messages = messages.filter(join_or_leave=False)
    if query:
        search = Q(message__icontains=query) | Q(nickname__icontains=query)
        messages = messages.filter(search).order_by("-message_time")
    elif year and month and day:
        messages = messages.filter(message_time__year=year,
                                   message_time__month=month,
                                   message_time__day=day)
        day_delta = timedelta(days=1)
        this_date = date(int(year), int(month), int(day))
        prev_date = this_date - day_delta
        next_date = this_date + day_delta
        prev_url = reverse("gnotty_day", args=prev_date.timetuple()[:3])
        next_url = reverse("gnotty_day", args=next_date.timetuple()[:3])
    else:
        return redirect("gnotty_year", year=datetime.now().year)

    context = dict(settings)
    context["messages"] = messages
    context["prev_url"] = prev_url
    context["next_url"] = next_url
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
    if hide_joins_and_leaves(request):
        lookup["join_or_leave"] = False

    messages = IRCMessage.objects.filter(**lookup)
    try:
        dates = messages.datetimes("message_time", "day")
    except AttributeError:
        dates = messages.dates("message_time", "day")
    days = [d.date() for d in dates]
    months = []

    if days:
        min_date, max_date = days[0], days[-1]
        days = set(days)
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

    context = dict(settings)
    context["months"] = months
    return render(request, template, context)


if settings.LOGIN_REQUIRED:
    chat     = login_required(chat)
    messages = login_required(messages)
    calendar = login_required(calendar)


def login(request):
    if request.method == "POST":
        user = auth.authenticate(username=request.POST["username"],
                                 password=request.POST["password"])
        if user:
            auth.login(request, user)
            return redirect(request.GET.get("next", "/"))
        error(request, "Invalid username/password")
    return render(request, "gnotty/login.html", {"request": request})


def logout(request):
    auth.logout(request)
    info(request, "You have successfully logged out")
    return redirect("/")
