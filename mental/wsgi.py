# ================================================================
#  mental/wsgi.py
# ================================================================
"""
WSGI config for the MindWell project.
Exposes the WSGI callable as a module-level variable named ``application``.
Used by Gunicorn in production (Render, Railway, Heroku).

  Procfile:  web: gunicorn mental.wsgi
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental.settings')

application = get_wsgi_application()