# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
        if not db.dry_run:
            orm['gnotty.IRCMessage'].objects.filter(message="joins").update(join_or_leave=True)
            orm['gnotty.IRCMessage'].objects.filter(message="leaves").update(join_or_leave=True)


    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        'gnotty.ircmessage': {
            'Meta': {'ordering': "('message_time',)", 'object_name': 'IRCMessage'},
            'channel': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'join_or_leave': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'message_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'nickname': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'server': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['gnotty']
    symmetrical = True
