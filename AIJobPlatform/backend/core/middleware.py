import hashlib
import fnmatch
import re
from html import escape
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse


class SimpleCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [
            'http://localhost:5173',
            'http://localhost:3000',
        ])

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
        if not origin:
            return False

        for allowed_origin in self.allowed_origins:
            if allowed_origin == origin:
                return True
            if "*" in allowed_origin and fnmatch.fnmatch(origin, allowed_origin):
                return True
        return False


class ApiRateLimitMiddleware:
    """Rate limiting middleware with user-specific limits"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.default_limit = getattr(settings, "API_RATE_LIMIT_PER_MINUTE", 120)
        self.auth_limit = 10  # Stricter limit for auth endpoints

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        # Determine rate limit based on endpoint
        if "/auth/" in request.path:
            limit = self.auth_limit
        else:
            limit = self.default_limit

        if limit <= 0:
            return self.get_response(request)

        # Get identity
        identity = self._get_identity(request)
        identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()
        cache_key = f"rate-limit:{identity_hash}:{request.path}"
        request_count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, request_count, 60)

        if request_count > limit:
            return JsonResponse({
                "detail": f"Rate limit exceeded. Max {limit} requests per minute.",
                "retry_after": 60
            }, status=429)

        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(max(0, limit - request_count))
        return response

    def _get_identity(self, request):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return f"user:{auth_header[:50]}"
        return request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or "anonymous"


class SecurityHeadersMiddleware:
    """Add security headers to all responses"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only add headers to API responses
        if request.path.startswith("/api/") or request.path.startswith("/swagger"):
            # Prevent clickjacking
            if getattr(settings, 'X_FRAME_OPTIONS', 'DENY') == 'DENY':
                response["X-Frame-Options"] = "DENY"

            # XSS Protection
            response["X-XSS-Protection"] = "1; mode=block"

            # Content Type sniffing
            response["X-Content-Type-Options"] = "nosniff"

            # Referrer Policy
            response["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # CSP for API (more lenient than static site)
            if not settings.DEBUG:
                response["Content-Security-Policy"] = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "connect-src 'self' https://api.openai.com https://api.anthropic.com;"
                )

        return response


class InputSanitizationMiddleware:
    """Sanitize user input to prevent XSS and injection attacks"""

    # Patterns that might indicate malicious input
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'expression\s*\(',
        r'<\s*iframe',
        r'<\s*object',
        r'<\s*embed',
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.dangerous_regex = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        # Paths to skip sanitization
        self.skip_paths = ['/admin/', '/swagger/', '/redoc/']

    def __call__(self, request):
        # Skip for safe paths
        if any(request.path.startswith(p) for p in self.skip_paths):
            return self.get_response(request)

        # Only sanitize POST, PUT, PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            if hasattr(request, 'body') and request.body:
                try:
                    # Check for dangerous patterns in body
                    body_str = request.body.decode('utf-8', errors='ignore')
                    for regex in self.dangerous_regex:
                        if regex.search(body_str):
                            return JsonResponse({
                                "detail": "Invalid input detected. Potential security violation."
                            }, status=400)
                except Exception:
                    pass

        return self.get_response(request)


class RequestSizeLimitMiddleware:
    """Limit request body size"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.max_body_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)

    def __call__(self, request):
        # Skip for safe methods
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return self.get_response(request)

        # Check Content-Length
        content_length = request.headers.get('Content-Length')
        if content_length and int(content_length) > self.max_body_size:
            return JsonResponse({
                "detail": f"Request body too large. Max size: {self.max_body_size} bytes"
            }, status=413)

        return self.get_response(request)


def sanitize_input(value):
    """Sanitize a single input value"""
    if isinstance(value, str):
        # Escape HTML
        sanitized = escape(value)
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        return sanitized
    elif isinstance(value, list):
        return [sanitize_input(item) for item in value]
    elif isinstance(value, dict):
        return {key: sanitize_input(val) for key, val in value.items()}
    return value