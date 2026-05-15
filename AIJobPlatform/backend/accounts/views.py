import json
import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .decorators import jwt_required, role_required
from .emails import build_absolute_api_url, send_password_reset_email, send_verification_email
from .models import Profile, User, OTPVerification, PasswordResetToken
from .tokens import create_jwt, decode_jwt, make_signed_token, read_signed_token
from .oauth import GoogleOAuthService, OTPService, PasswordResetService


def _badge_tier_for_score(score):
    if score >= 85:
        return "gold"
    if score >= 65:
        return "silver"
    return "bronze"


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


def public_profile_payload(user):
    profile = ensure_profile(user)
    resume = None
    try:
        resume = user.resumes.order_by("-uploaded_at").first()
    except Exception:
        resume = None

    skills = list(profile.skills or [])
    badges = []
    try:
        from jobs.models import SkillVerificationBadge

        badges = [
            {
                "id": badge.id,
                "skill_name": badge.skill_name,
                "badge_tier": badge.badge_tier,
                "source": badge.source,
                "score": badge.score,
                "evidence_url": badge.evidence_url,
                "verified_at": badge.verified_at.isoformat(),
            }
            for badge in SkillVerificationBadge.objects.filter(user=user)
        ]
    except Exception:
        badges = []

    portfolio_items = profile.portfolio_items or []
    profile_strength = int(
        (
            bool(profile.headline)
            + bool(profile.bio)
            + bool(profile.location)
            + bool(skills)
            + bool(portfolio_items)
            + bool(profile.github_url or profile.linkedin_url)
            + bool(resume)
        )
        / 7
        * 100
    )

    return {
        "user": user_payload(user),
        "profile": profile_payload(profile),
        "public_url": f"/profile/{user.pk}",
        "share_link": f"/profile/{user.pk}",
        "profile_strength": profile_strength,
        "resume_link": resume.file.url if resume and getattr(resume, "file", None) else "",
        "portfolio": portfolio_items,
        "badges": badges,
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
def public_profile(request, user_id):
    try:
        user = get_user_model().objects.select_related("profile").get(pk=user_id, is_active=True)
    except get_user_model().DoesNotExist:
        return JsonResponse({"detail": "Profile not found."}, status=404)

    return JsonResponse(public_profile_payload(user))


@csrf_exempt
@require_http_methods(["GET", "POST"])
def skill_badges(request, user_id):
    try:
        user = get_user_model().objects.get(pk=user_id, is_active=True)
    except get_user_model().DoesNotExist:
        return JsonResponse({"detail": "User not found."}, status=404)

    from jobs.models import SkillVerificationBadge

    if request.method == "GET":
        badges = SkillVerificationBadge.objects.filter(user=user).order_by("-verified_at")
        return JsonResponse({
            "user": user_payload(user),
            "count": badges.count(),
            "badges": [
                {
                    "id": badge.id,
                    "skill_name": badge.skill_name,
                    "badge_tier": badge.badge_tier,
                    "source": badge.source,
                    "score": badge.score,
                    "evidence_url": badge.evidence_url,
                    "note": badge.note,
                    "verified_at": badge.verified_at.isoformat(),
                }
                for badge in badges
            ],
        })

    try:
        data = parse_json(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    skill_name = (data.get("skill_name") or "").strip()
    score = int(data.get("score") or 0)
    source = (data.get("source") or "test").strip().lower()
    evidence_url = (data.get("evidence_url") or "").strip()
    note = (data.get("note") or "").strip()

    if not skill_name:
        return JsonResponse({"detail": "skill_name is required."}, status=400)

    badge, _created = SkillVerificationBadge.objects.update_or_create(
        user=user,
        skill_name=skill_name,
        badge_tier=_badge_tier_for_score(score),
        defaults={
            "source": source if source in dict(SkillVerificationBadge.BadgeSource.choices) else SkillVerificationBadge.BadgeSource.TEST,
            "score": max(0, min(score, 100)),
            "evidence_url": evidence_url,
            "note": note,
        },
    )
    return JsonResponse({"badge": {
        "id": badge.id,
        "skill_name": badge.skill_name,
        "badge_tier": badge.badge_tier,
        "source": badge.source,
        "score": badge.score,
        "evidence_url": badge.evidence_url,
        "note": badge.note,
        "verified_at": badge.verified_at.isoformat(),
    }}, status=201)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def upload_skill_certificate(request):
    from jobs.models import SkillVerificationBadge

    skill_name = (request.POST.get("skill_name") or "").strip()
    if not skill_name:
        try:
            data = parse_json(request)
        except ValueError:
            data = {}
        skill_name = (data.get("skill_name") or "").strip()

    if not skill_name:
        return JsonResponse({"detail": "skill_name is required."}, status=400)

    certificate = request.FILES.get("certificate")
    if certificate:
        saved_path = default_storage.save(
            os.path.join("skill-badges", str(request.user.pk), certificate.name),
            ContentFile(certificate.read()),
        )
        evidence_url = default_storage.url(saved_path)
    else:
        evidence_url = ""

    profile = ensure_profile(request.user)
    skill_set = {str(skill).strip().lower() for skill in (profile.skills or [])}
    if skill_name.lower() not in skill_set:
        skill_set.add(skill_name.lower())
        profile.skills = sorted(skill_set)
        profile.save(update_fields=["skills", "updated_at"])

    score = 90 if certificate else 75
    badge, _created = SkillVerificationBadge.objects.update_or_create(
        user=request.user,
        skill_name=skill_name,
        badge_tier=_badge_tier_for_score(score),
        defaults={
            "source": SkillVerificationBadge.BadgeSource.CERTIFICATE,
            "score": score,
            "evidence_url": evidence_url,
            "note": "Uploaded certificate verification.",
        },
    )

    return JsonResponse({
        "badge": {
            "id": badge.id,
            "skill_name": badge.skill_name,
            "badge_tier": badge.badge_tier,
            "source": badge.source,
            "score": badge.score,
            "evidence_url": badge.evidence_url,
            "note": badge.note,
            "verified_at": badge.verified_at.isoformat(),
        }
    }, status=201)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def connect_github_badges(request):
    profile = ensure_profile(request.user)
    from jobs.models import SkillVerificationBadge

    skill_name = "GitHub"
    if profile.github_url:
        badge, _created = SkillVerificationBadge.objects.update_or_create(
            user=request.user,
            skill_name=skill_name,
            badge_tier="gold",
            defaults={
                "source": SkillVerificationBadge.BadgeSource.GITHUB,
                "score": 95,
                "evidence_url": profile.github_url,
                "note": "GitHub portfolio connected.",
            },
        )
        return JsonResponse({
            "auth_url": profile.github_url,
            "badge": {
                "id": badge.id,
                "skill_name": badge.skill_name,
                "badge_tier": badge.badge_tier,
                "source": badge.source,
                "score": badge.score,
                "evidence_url": badge.evidence_url,
                "note": badge.note,
                "verified_at": badge.verified_at.isoformat(),
            },
        })

    return JsonResponse({
        "auth_url": "https://github.com/login/oauth/authorize",
        "detail": "Connect GitHub in your profile to mint a verified badge.",
    })


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


# ============ OAUTH ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
def google_oauth_login(request):
    """
    Handle Google OAuth login/signup
    Expects: { "id_token": "<google_id_token>", "access_token": "<optional>" }
    """
    try:
        data = parse_json(request)
        id_token = data.get("id_token")
        role = data.get("role", User.Role.STUDENT)
        
        if not id_token:
            return JsonResponse({"detail": "id_token is required"}, status=400)
        
        # Get or create user
        user, created = GoogleOAuthService.get_user_from_google(id_token)
        
        if not user:
            return JsonResponse({"detail": "Failed to authenticate with Google"}, status=401)
        
        # Set role for new users
        if created and role in (User.Role.STUDENT, User.Role.RECRUITER):
            user.role = role
            user.save()
        
        # Ensure profile exists
        ensure_profile(user)
        
        # Create tokens
        login(request, user)
        
        payload = {
            "detail": f"{'Account created' if created else 'Logged in'} successfully via Google",
            "user": user_payload(user),
            "profile": profile_payload(user.profile),
            "tokens": token_pair(user),
            "is_new_user": created,
        }
        
        response = JsonResponse(payload, status=201 if created else 200)
        response.set_cookie(
            "sessionid",
            request.session.session_key,
            httponly=True,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )
        return response
        
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


# ============ OTP ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def send_otp(request):
    """
    Send OTP to user's email for verification
    Expects: { "email": "<optional, defaults to user email>" }
    """
    try:
        data = parse_json(request)
        email = data.get("email", request.user.email)
        
        # Validate email
        if not email:
            return JsonResponse({"detail": "Email is required"}, status=400)
        
        # Send OTP
        success = OTPService.send_otp_email(request.user, email)
        
        if not success:
            return JsonResponse({"detail": "Failed to send OTP"}, status=500)
        
        return JsonResponse({
            "detail": f"OTP sent to {email}",
            "email": email,
            "expires_in_minutes": OTPService.OTP_EXPIRY_MINUTES
        })
        
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def verify_otp(request):
    """
    Verify OTP for email confirmation
    Expects: { "otp": "<6-digit-code>", "email": "<optional>" }
    """
    try:
        data = parse_json(request)
        otp = data.get("otp", "").strip()
        email = data.get("email", request.user.email)
        
        if not otp or len(otp) != 6 or not otp.isdigit():
            return JsonResponse({"detail": "Invalid OTP format"}, status=400)
        
        is_valid, message = OTPService.verify_otp(request.user, otp, email)
        
        if not is_valid:
            return JsonResponse({"detail": message}, status=400)
        
        # Reload user to get updated is_email_verified
        request.user.refresh_from_db()
        
        return JsonResponse({
            "detail": message,
            "user": user_payload(request.user),
            "is_email_verified": request.user.is_email_verified,
        })
        
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


# ============ PASSWORD RESET ENDPOINTS (Enhanced) ============

@csrf_exempt
@require_http_methods(["POST"])
def request_password_reset(request):
    """
    Request password reset via email
    Expects: { "email": "<email>" }
    """
    try:
        data = parse_json(request)
        email = data.get("email", "").strip().lower()
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Generate reset token
            token = PasswordResetService.generate_reset_token(user)
            
            # Send email
            frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:5173"
            PasswordResetService.send_reset_email(user, token, frontend_url)
            
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return JsonResponse({
            "detail": "If an account with that email exists, a password reset link has been sent."
        })
        
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_reset_token_view(request):
    """
    Verify if a reset token is valid
    Expects: { "token": "<reset_token>" }
    """
    try:
        data = parse_json(request)
        token = data.get("token", "").strip()
        
        user, message = PasswordResetService.verify_reset_token(token)
        
        if not user:
            return JsonResponse({"detail": message}, status=400)
        
        return JsonResponse({
            "detail": message,
            "email": user.email,
            "valid": True
        })
        
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def confirm_password_reset(request):
    """
    Complete password reset with new password
    Expects: { "token": "<reset_token>", "password": "<new_password>" }
    """
    try:
        data = parse_json(request)
        token = data.get("token", "").strip()
        password = data.get("password", "")
        
        if not token or not password:
            return JsonResponse({"detail": "Token and password are required"}, status=400)
        
        success, message = PasswordResetService.reset_password(token, password)
        
        if not success:
            return JsonResponse({"detail": message}, status=400)
        
        return JsonResponse({"detail": message})
        
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


# ============ THEME PREFERENCE ENDPOINTS ============

@csrf_exempt
@require_http_methods(["GET", "PUT"])
@jwt_required
def theme_preference(request):
    """Get or update user's theme preference"""
    if request.method == "GET":
        return JsonResponse({
            "theme_preference": request.user.theme_preference,
            "available_themes": [choice[0] for choice in User.Theme.choices]
        })
    
    try:
        data = parse_json(request)
        theme = data.get("theme_preference", "").strip()
        
        if theme not in dict(User.Theme.choices):
            return JsonResponse({"detail": "Invalid theme choice"}, status=400)
        
        request.user.theme_preference = theme
        request.user.save(update_fields=["theme_preference", "updated_at"])
        
        return JsonResponse({
            "detail": "Theme preference updated",
            "theme_preference": request.user.theme_preference
        })
        
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)
