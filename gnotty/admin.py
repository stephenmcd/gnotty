
from django.contrib import admin

from gnotty.models import IRCMessage


class IRCMessageAdmin(admin.ModelAdmin):

    list_display = ("message_time", "server", "channel", "nickname",
                    "short_message")
    list_filter = ("server", "channel", "nickname")
    search_fields = ("channel", "nickname", "message")
    date_hierarchy = "message_time"


admin.site.register(IRCMessage, IRCMessageAdmin)
