from django.contrib.auth import get_user_model

from .tokens import decode_jwt


def get_bearer_token(request):
    auth_header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        return None
    return auth_header[len(prefix) :].strip()


def authenticate_jwt(request):
    token = get_bearer_token(request)
    if not token:
        return None
    payload = decode_jwt(token, expected_type="access")
    user = get_user_model().objects.get(pk=payload["sub"], is_active=True)
    return user

