"""
ASGI config for melting_potlist project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import apps.websocket_sync.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melting_potlist.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.websocket_sync.routing.websocket_urlpatterns
        )
    ),
})
