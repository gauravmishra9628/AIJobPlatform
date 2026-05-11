import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .decorators import jwt_required, role_required
from .emails import build_absolute_api_url, send_password_reset_email, send_verification_email
from .models import Profile, User
from .tokens import create_jwt, decode_jwt, make_signed_token, read_signed_token


def parse_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        raise ValueError("Request body must be valid JSON.")


def user_payload(user):
    return {
        "id": user.pk,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "is_email_verified": user.is_email_verified,
        "company_name": user.company_name,
        "university_name": user.university_name,
    }


def profile_payload(profile):
    picture_url = None
    if profile.profile_picture:
        picture_url = profile.profile_picture.url

    return {
        "id": profile.pk,
        "user_id": profile.user_id,
        "headline": profile.headline,
        "bio": profile.bio,
        "about": profile.about,
        "skills": profile.skills,
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "portfolio_items": profile.portfolio_items,
        "location": profile.location,
        "profile_picture": picture_url,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
    }


def ensure_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def token_pair(user):
    return {
        "access": create_jwt(user, "access", settings.JWT_ACCESS_TOKEN_LIFETIME),
        "refresh": create_jwt(user, "refresh", settings.JWT_REFRESH_TOKEN_LIFETIME),
    }


@csrf_exempt
@require_http_methods(["POST"])
def signup(request):
    try:
        data = parse_json(request)
        role = data.get("role", User.Role.STUDENT)
        if role not in (User.Role.STUDENT, User.Role.RECRUITER):
            return JsonResponse({"detail": "Role must be 'student' or 'recruiter'."}, status=400)

        password = data.get("password", "")
        validate_password(password)

        user = get_user_model().objects.create_user(
            email=data.get("email", "").strip().lower(),
            password=password,
            first_name=data.get("first_name", "").strip(),
            last_name=data.get("last_name", "").strip(),
            role=role,
            company_name=data.get("company_name", "").strip() if role == User.Role.RECRUITER else "",
            university_name=data.get("university_name", "").strip() if role == User.Role.STUDENT else "",
            is_active=True,
        )
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    except ValidationError as exc:
        return JsonResponse({"password": exc.messages}, status=400)
    except IntegrityError:
        return JsonResponse({"email": "A user with this email already exists."}, status=400)

    token, _ = make_signed_token(user, "email-verification", settings.EMAIL_VERIFICATION_MAX_AGE)
    send_verification_email(request, user, token)
    payload = {
        "detail": "Account created. Please verify your email before using protected features.",
        "user": user_payload(user),
        "profile": profile_payload(ensure_profile(user)),
    }
    if settings.DEBUG:
        payload["debug"] = {
            "verification_url": build_absolute_api_url(request, "accounts:verify-email", token),
            "verification_path": f"/verify-email/{token}",
        }
    return JsonResponse(payload, status=201)


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    try:
        data = parse_json(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    user = authenticate(request, email=data.get("email", "").strip().lower(), password=data.get("password", ""))
    if user is None:
        return JsonResponse({"detail": "Invalid email or password."}, status=401)
    if not user.is_email_verified:
        return JsonResponse({"detail": "Please verify your email before logging in."}, status=403)

    login(request, user)
    response = JsonResponse({"detail": "Login successful.", "user": user_payload(user), "tokens": token_pair(user)})
    response.set_cookie(
        "sessionid",
        request.session.session_key,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    return response


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def logout_view(request):
    logout(request)
    response = JsonResponse({"detail": "Logout successful."})
    response.delete_cookie("sessionid", samesite=settings.SESSION_COOKIE_SAMESITE)
    return response


@require_http_methods(["GET"])
def verify_email(request, token):
    try:
        payload = read_signed_token(token, "email-verification", settings.EMAIL_VERIFICATION_MAX_AGE)
        user = get_user_model().objects.get(pk=payload["user_id"], is_active=True)
    except (signing.BadSignature, signing.SignatureExpired, get_user_model().DoesNotExist):
        return JsonResponse({"detail": "Verification link is invalid or expired."}, status=400)

    user.is_email_verified = True
    user.save(update_fields=["is_email_verified", "updated_at"])
    return JsonResponse({"detail": "Email verified successfully. You can now log in."})


@csrf_exempt
@require_http_methods(["POST"])
def resend_verification(request):
    try:
        data = parse_json(request)
        user = get_user_model().objects.get(email=data.get("email", "").strip().lower(), is_active=True)
    except (ValueError, get_user_model().DoesNotExist):
        return JsonResponse({"detail": "If the account exists, a verification email has been sent."})

    if not user.is_email_verified:
        token, _ = make_signed_token(user, "email-verification", settings.EMAIL_VERIFICATION_MAX_AGE)
        send_verification_email(request, user, token)
    return JsonResponse({"detail": "If the account exists, a verification email has been sent."})


@csrf_exempt
@require_http_methods(["POST"])
def refresh_token(request):
    try:
        data = parse_json(request)
        payload = decode_jwt(data.get("refresh", ""), expected_type="refresh")
        user = get_user_model().objects.get(pk=payload["sub"], is_active=True, is_email_verified=True)
    except Exception:
        return JsonResponse({"detail": "Invalid or expired refresh token."}, status=401)
    return JsonResponse({"tokens": token_pair(user)})


@csrf_exempt
@require_http_methods(["POST"])
def forgot_password(request):
    try:
        data = parse_json(request)
        user = get_user_model().objects.get(email=data.get("email", "").strip().lower(), is_active=True)
    except (ValueError, get_user_model().DoesNotExist):
        return JsonResponse({"detail": "If the account exists, a password reset email has been sent."})

    token, _ = make_signed_token(user, "password-reset", int(timedelta(hours=1).total_seconds()))
    send_password_reset_email(request, user, token)
    payload = {"detail": "If the account exists, a password reset email has been sent."}
    if settings.DEBUG:
        payload["debug"] = {
            "reset_url": build_absolute_api_url(request, "accounts:password-reset-confirm", token),
            "reset_path": f"/reset-password/{token}",
        }
    return JsonResponse(payload)


@csrf_exempt
@require_http_methods(["POST"])
def password_reset_confirm(request, token):
    try:
        data = parse_json(request)
        payload = read_signed_token(token, "password-reset", int(timedelta(hours=1).total_seconds()))
        user = get_user_model().objects.get(pk=payload["user_id"], is_active=True)
        validate_password(data.get("password", ""), user=user)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)
    except ValidationError as exc:
        return JsonResponse({"password": exc.messages}, status=400)
    except (signing.BadSignature, signing.SignatureExpired, get_user_model().DoesNotExist):
        return JsonResponse({"detail": "Password reset link is invalid or expired."}, status=400)

    user.set_password(data["password"])
    user.save(update_fields=["password", "updated_at"])
    return JsonResponse({"detail": "Password has been reset successfully."})


@require_http_methods(["GET"])
@jwt_required
def profile(request):
    profile = ensure_profile(request.user)
    return JsonResponse({"user": user_payload(request.user), "profile": profile_payload(profile)})


@csrf_exempt
@require_http_methods(["GET", "PUT", "PATCH"])
@jwt_required
def profile_detail(request):
    profile = ensure_profile(request.user)

    if request.method == "GET":
        return JsonResponse({"profile": profile_payload(profile)})

    data = {}
    files = request.FILES
    content_type = request.headers.get("Content-Type", "")
    if "multipart/form-data" in content_type:
        data = request.POST
    else:
        try:
            data = parse_json(request)
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)

    skills_value = data.get("skills", profile.skills)
    if isinstance(skills_value, str):
        skills_value = [item.strip() for item in skills_value.split(",") if item.strip()]

    portfolio_value = data.get("portfolio_items", profile.portfolio_items)
    if isinstance(portfolio_value, str):
        try:
            portfolio_value = json.loads(portfolio_value)
        except json.JSONDecodeError:
            return JsonResponse({"portfolio_items": "Must be valid JSON."}, status=400)

    profile.headline = data.get("headline", profile.headline).strip()
    profile.bio = data.get("bio", profile.bio).strip()
    profile.about = data.get("about", profile.about).strip()
    profile.github_url = data.get("github_url", profile.github_url).strip()
    profile.linkedin_url = data.get("linkedin_url", profile.linkedin_url).strip()
    profile.location = data.get("location", profile.location).strip()
    profile.skills = skills_value
    profile.portfolio_items = portfolio_value

    if files.get("profile_picture"):
        profile.profile_picture = files["profile_picture"]

    profile.save()
    return JsonResponse({"detail": "Profile updated successfully.", "profile": profile_payload(profile)})


@require_http_methods(["GET"])
@role_required(User.Role.STUDENT)
def student_dashboard(request):
    return JsonResponse(
        {
            "dashboard": "student",
            "message": "Welcome to your student dashboard.",
            "widgets": ["recommended_jobs", "applications", "profile_strength", "ai_resume_feedback"],
        }
    )


@require_http_methods(["GET"])
@role_required(User.Role.RECRUITER)
def recruiter_dashboard(request):
    return JsonResponse(
        {
            "dashboard": "recruiter",
            "message": "Welcome to your recruiter dashboard.",
            "widgets": ["posted_jobs", "candidate_matches", "interview_pipeline", "ai_candidate_ranker"],
        }
    )


@require_http_methods(["GET"])
@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    return JsonResponse(
        {
            "dashboard": "admin",
            "message": "Welcome to the admin dashboard.",
            "widgets": ["user_counts", "pending_recruiters", "platform_health", "audit_summary"],
        }
    )
