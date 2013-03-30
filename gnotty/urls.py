
from django.conf.urls import patterns, url


archive_pattern = "^archive/"
year_pattern    = archive_pattern + "(?P<year>\d{4})/"
month_pattern   = year_pattern    + "(?P<month>\d{1,2})/"
day_pattern     = month_pattern   + "(?P<day>\d{1,2})/"

urlpatterns = patterns("gnotty.views",
    url("^$", "chat", name="gnotty_chat"),
    url(archive_pattern + "$", "messages", name="gnotty_search"),
    url(year_pattern    + "$", "calendar", name="gnotty_year"),
    url(month_pattern   + "$", "calendar", name="gnotty_month"),
    url(day_pattern     + "$", "messages", name="gnotty_day"),
)
