from functools import wraps

from django.http import JsonResponse

from .authentication import authenticate_jwt


def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            user = authenticate_jwt(request)
        except Exception:
            return JsonResponse({"detail": "Invalid or expired access token."}, status=401)
        if user is None:
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
        request.user = user
        return view_func(request, *args, **kwargs)

    return wrapper


def role_required(*roles):
    def decorator(view_func):
        @jwt_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                return JsonResponse({"detail": "You do not have permission to access this dashboard."}, status=403)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

