
import os


###################
# Django settings #
###################

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, STATIC_URL.strip('/'))
ROOT_URLCONF = '%s.urls' % PROJECT_ROOT.split(os.sep)[-1]
TEMPLATE_DIRS = (os.path.join(PROJECT_ROOT, 'templates'),)
DEBUG = True
SITE_ID = 1
SECRET_KEY = "change me"
ALLOWED_HOSTS = ["*"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'dev.db',
    }
}

INSTALLED_APPS = (
    'gnotty',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.static',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)

try:
    import south
except ImportError:
    pass
else:
    INSTALLED_APPS += ("south",)


###################
# Gnotty settings #
###################

GNOTTY_HTTP_PORT = 8080
GNOTTY_IRC_HOST = '127.0.0.1'
GNOTTY_IRC_PORT = 6667
GNOTTY_IRC_CHANNEL = '#gnotty'
GNOTTY_IRC_CHANNEL_KEY = None
GNOTTY_BOT_CLASS = 'gnotty.bots.BaseBot'
GNOTTY_BOT_NICKNAME = 'gnotty'
GNOTTY_BOT_PASSWORD = None
GNOTTY_LOGIN_REQUIRED = False


##################
# Local settings #
##################

try:
    from local_settings import *
except ImportError:
    pass

TEMPLATE_DEBUG = DEBUG
GNOTTY_LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'
GNOTTY_HTTP_HOST = '127.0.0.1' if DEBUG else '0.0.0.0'
