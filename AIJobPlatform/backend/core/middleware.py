import hashlib

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.http import JsonResponse


class SimpleCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin")
        if request.method == "OPTIONS" and self._origin_allowed(origin):
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        if self._origin_allowed(origin):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = "Authorization,Content-Type,X-CSRFToken"
            response["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
            response["Vary"] = "Origin"
        return response

    def _origin_allowed(self, origin):
        return bool(origin and origin in settings.CORS_ALLOWED_ORIGINS)


class ApiRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        limit = getattr(settings, "API_RATE_LIMIT_PER_MINUTE", 120)
        if limit <= 0:
            return self.get_response(request)

        identity = (
            request.headers.get("Authorization")
            or request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            or request.META.get("REMOTE_ADDR", "anonymous")
        )
        identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        cache_key = f"rate-limit:{identity_hash}:{request.path}"
        request_count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, request_count, 60)

        if request_count > limit:
            return JsonResponse({"detail": "Too many requests. Please wait a minute and try again."}, status=429)

        return self.get_response(request)
