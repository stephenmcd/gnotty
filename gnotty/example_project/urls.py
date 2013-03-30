
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect


admin.autodiscover()

urlpatterns = patterns('',
    url('^admin/', include(admin.site.urls)),
    url('^irc/', include('gnotty.urls')),
    url('^' + settings.LOGIN_URL.lstrip('/'), 'gnotty.views.login'),
    url('^' + settings.LOGOUT_URL.lstrip('/'), 'gnotty.views.logout'),
    url('^$', lambda r: redirect('gnotty_chat')),
)
