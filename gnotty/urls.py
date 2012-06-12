
from django.conf.urls.defaults import patterns, url


urlpatterns = patterns("gnotty.views",
    url("^$", "chat", name="gnotty_chat"),
    url("^search/$", "search", name="gnotty_search"),
    url("^(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$",
        "day", name="gnotty_day"),
)
