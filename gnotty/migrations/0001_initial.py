# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'IRCMessage'
        db.create_table('gnotty_ircmessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nickname', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('server', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('channel', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('message_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('gnotty', ['IRCMessage'])


    def backwards(self, orm):
        # Deleting model 'IRCMessage'
        db.delete_table('gnotty_ircmessage')


    models = {
        'gnotty.ircmessage': {
            'Meta': {'ordering': "('message_time',)", 'object_name': 'IRCMessage'},
            'channel': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'message_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'nickname': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'server': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['gnotty']