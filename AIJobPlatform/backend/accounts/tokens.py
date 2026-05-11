import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.core import signing


def _b64encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def create_jwt(user, token_type="access", lifetime=None):
    lifetime = lifetime or settings.JWT_ACCESS_TOKEN_LIFETIME
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.pk),
        "email": user.email,
        "role": user.role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        [
            _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_jwt(token, expected_type="access"):
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid token format.") from exc

    signing_input = f"{header_b64}.{payload_b64}"
    expected_signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    supplied_signature = _b64decode(signature_b64)
    if not hmac.compare_digest(expected_signature, supplied_signature):
        raise ValueError("Invalid token signature.")

    payload = json.loads(_b64decode(payload_b64))
    if payload.get("type") != expected_type:
        raise ValueError("Invalid token type.")
    if int(datetime.now(timezone.utc).timestamp()) >= int(payload["exp"]):
        raise ValueError("Token has expired.")
    return payload


def make_signed_token(user, purpose, max_age=None):
    max_age = max_age or int(timedelta(hours=24).total_seconds())
    payload = {"user_id": user.pk, "purpose": purpose}
    return signing.dumps(payload, salt=purpose, compress=True), max_age


def read_signed_token(token, purpose, max_age):
    payload = signing.loads(token, salt=purpose, max_age=max_age)
    if payload.get("purpose") != purpose:
        raise signing.BadSignature("Invalid token purpose.")
    return payload

