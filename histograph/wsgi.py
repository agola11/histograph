"""
WSGI config for histograph project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os, sys

import local_wsgi

sys.path.append(local_wsgi.PYTHON_PATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", local_wsgi.DJANGO_SETTINGS_MODULE)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
