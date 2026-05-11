from django.conf import settings
from django.http import HttpResponse


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

