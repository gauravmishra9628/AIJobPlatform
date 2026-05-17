"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import json
import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django_asgi_app = get_asgi_application()


async def http_application(scope, receive, send):
    if scope.get("type") != "http":
        await django_asgi_app(scope, receive, send)
        return

    method = scope.get("method")
    path = scope.get("path")

    if method == "HEAD" and path in {"/", "/health/"}:
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-length", b"0"),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": b"",
        })
        return

    if method == "GET" and path == "/health/":
        body = json.dumps({
            "status": "healthy",
            "checks": {
                "application": "ok",
            },
        }).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
        return

    if method == "GET" and path == "/":
        body = json.dumps({
            "message": "AI Job Platform API is running.",
            "available_routes": [
                "/health/",
                "/api/auth/",
                "/api/jobs/",
                "/api/companies/",
                "/swagger/",
            ],
        }).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
        return

    await django_asgi_app(scope, receive, send)

# WebSocket URL routing
from jobs import routing as jobs_routing

application = ProtocolTypeRouter({
    "http": http_application,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                jobs_routing.websocket_urlpatterns
            )
        )
    ),
})
