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
    path("dashboard/student/", views.student_dashboard, name="student-dashboard"),
    path("dashboard/recruiter/", views.recruiter_dashboard, name="recruiter-dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin-dashboard"),
]

