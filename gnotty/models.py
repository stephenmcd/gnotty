
from django.db import models
from django.utils.timezone import now


class IRCMessage(models.Model):

    nickname = models.CharField(max_length=100)
    message = models.TextField()
    server = models.CharField(max_length=100)
    channel = models.CharField(max_length=100)
    message_time = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.message_time = now()
        super(IRCMessage, self).save(*args, **kwargs)

