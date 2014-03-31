"""
Django settings for histograph project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

try:
    from local_settings import *
except ImportError:
    pass


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+2qq7qat+a9xyps@_iw!x)8a+=nu=0bpqvgo6y9ujhtw*g$t3c'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_facebook',
    'core',
    'graph',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
<<<<<<< HEAD
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'django_facebook.context_processors.facebook',
=======
     "django.contrib.auth.context_processors.auth",
     "django.core.context_processors.debug",
     "django.core.context_processors.i18n",
     "django.core.context_processors.media",
     "django.core.context_processors.static",
     "django.core.context_processors.tz",
     "django.core.context_processors.request",
     "django.contrib.messages.context_processors.messages",
     "django_facebook.context_processors.facebook",
>>>>>>> ad635866559d09521dd898d3a87915732012f5c5
)

AUTHENTICATION_BACKENDS = (
    'django_facebook.auth_backends.FacebookBackend',
    'django.contrib.auth.backends.ModelBackend',
)

<<<<<<< HEAD


=======
>>>>>>> ad635866559d09521dd898d3a87915732012f5c5
TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

ROOT_URLCONF = 'histograph.urls'

WSGI_APPLICATION = 'histograph.wsgi.application'

<<<<<<< HEAD

=======
STATIC_ROOT = os.path.join(BASE_DIR, "static_prod")

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)
>>>>>>> ad635866559d09521dd898d3a87915732012f5c5

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

<<<<<<< HEAD
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
    '/var/www/histograph-dev1/static/'
)

=======
AUTH_USER_MODEL = 'django_facebook.FacebookCustomUser'
>>>>>>> ad635866559d09521dd898d3a87915732012f5c5

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Dat Facebook Doe
FACEBOOK_APP_ID = 621832427895740
FACEBOOK_APP_SECRET = 'd74accde2c85ef2af87da411ef1c64c5'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

<<<<<<< HEAD
=======
FACEBOOK_APP_ID = '243320595870291'
FACEBOOK_APP_SECRET = '50a0c2365fd8561c866bf133a15f798a'

try:
    from local_settings import *
except ImportError:
    pass
>>>>>>> ad635866559d09521dd898d3a87915732012f5c5
