from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("token/refresh/", views.refresh_token, name="token-refresh"),
    path("verify-email/<str:token>/", views.verify_email, name="verify-email"),
    path("verify-email/resend/", views.resend_verification, name="resend-verification"),
    path("password/forgot/", views.forgot_password, name="forgot-password"),
    path("password/reset/<str:token>/", views.password_reset_confirm, name="password-reset-confirm"),
    path("me/", views.profile, name="profile"),
    path("profile/", views.profile_detail, name="profile-detail"),
    path("profile/<int:user_id>/", views.public_profile, name="public-profile"),
    path("users/<int:user_id>/badges/", views.skill_badges, name="user-badges"),
    path("badges/upload/", views.upload_skill_certificate, name="upload-skill-certificate"),
    path("badges/connect-github/", views.connect_github_badges, name="connect-github-badges"),
    path("dashboard/student/", views.student_dashboard, name="student-dashboard"),
    path("dashboard/recruiter/", views.recruiter_dashboard, name="recruiter-dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin-dashboard"),
    
    # OAuth
    path("oauth/google/", views.google_oauth_login, name="google-oauth"),
    
    # OTP Verification
    path("otp/send/", views.send_otp, name="send-otp"),
    path("otp/verify/", views.verify_otp, name="verify-otp"),
    
    # Enhanced Password Reset
    path("password/request-reset/", views.request_password_reset, name="request-password-reset"),
    path("password/verify-reset-token/", views.verify_reset_token_view, name="verify-reset-token"),
    path("password/confirm-reset/", views.confirm_password_reset, name="confirm-password-reset"),
    
    # Theme
    path("theme/", views.theme_preference, name="theme-preference"),
]

