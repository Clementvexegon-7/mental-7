# ================================================================
#  mental/asgi.py
# ================================================================
"""
ASGI config for the MindWell project.
Exposes the ASGI callable as a module-level variable named ``application``.
Required for async-capable servers (Daphne, Uvicorn) and future WebSocket support.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental.settings')

application = get_asgi_application()