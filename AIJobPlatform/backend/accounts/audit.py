"""
Audit Logging for AI Job Platform
Tracks user actions for security and compliance
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import json


class AuditLog(models.Model):
    """Model for audit logging"""

    class ActionType(models.TextChoices):
        # Authentication
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        LOGIN_FAILED = "login_failed", "Login Failed"
        PASSWORD_CHANGE = "password_change", "Password Change"
        PASSWORD_RESET = "password_reset", "Password Reset"

        # User Management
        USER_CREATE = "user_create", "User Created"
        USER_UPDATE = "user_update", "User Updated"
        USER_DELETE = "user_delete", "User Deleted"
        PROFILE_UPDATE = "profile_update", "Profile Updated"

        # Job Management
        JOB_CREATE = "job_create", "Job Created"
        JOB_UPDATE = "job_update", "Job Updated"
        JOB_DELETE = "job_delete", "Job Deleted"
        JOB_VIEW = "job_view", "Job Viewed"

        # Application
        APPLICATION_CREATE = "application_create", "Application Created"
        APPLICATION_UPDATE = "application_update", "Application Updated"
        APPLICATION_STATUS_CHANGE = "application_status_change", "Application Status Changed"

        # Resume
        RESUME_UPLOAD = "resume_upload", "Resume Uploaded"
        RESUME_DOWNLOAD = "resume_download", "Resume Downloaded"
        RESUME_ANALYSIS = "resume_analysis", "Resume Analyzed"

        # AI Features
        AI_ANALYSIS = "ai_analysis", "AI Analysis"
        AI_RECOMMENDATION = "ai_recommendation", "AI Recommendation"

        # Payment
        PAYMENT_INITIATED = "payment_initiated", "Payment Initiated"
        PAYMENT_COMPLETED = "payment_completed", "Payment Completed"
        PAYMENT_FAILED = "payment_failed", "Payment Failed"

        # Admin
        ADMIN_ACTION = "admin_action", "Admin Action"
        SETTINGS_CHANGE = "settings_change", "Settings Changed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=30, choices=ActionType.choices)
    resource_type = models.CharField(max_length=50)  # job, user, application, etc.
    resource_id = models.PositiveIntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    status_code = models.PositiveSmallIntegerField(null=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"


class AuditLogger:
    """Helper class for creating audit logs"""

    @staticmethod
    def log(
        user=None,
        action=None,
        resource_type=None,
        resource_id=None,
        request=None,
        status_code=None,
        details=None
    ):
        """Create an audit log entry"""
        ip_address = None
        user_agent = ""
        request_method = ""
        request_path = ""

        if request:
            ip_address = (
                request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
                or request.META.get("REMOTE_ADDR")
            )
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
            request_method = request.method
            request_path = request.path

        AuditLog.objects.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            status_code=status_code,
            details=details or {},
        )

    @staticmethod
    def log_login(user, request, success=True):
        """Log login attempt"""
        AuditLogger.log(
            user=user if success else None,
            action=AuditLog.ActionType.LOGIN if success else AuditLog.ActionType.LOGIN_FAILED,
            resource_type="auth",
            request=request,
            status_code=200 if success else 401,
            details={"email": user.email if success else request.POST.get("email", "")}
        )

    @staticmethod
    def log_job_action(user, action, job, request):
        """Log job-related action"""
        AuditLogger.log(
            user=user,
            action=action,
            resource_type="job",
            resource_id=job.id if job else None,
            request=request,
            details={"title": job.title if job else ""}
        )

    @staticmethod
    def log_application_action(user, action, application, request, details=None):
        """Log application action"""
        AuditLogger.log(
            user=user,
            action=action,
            resource_type="application",
            resource_id=application.id if application else None,
            request=request,
            details=details or {}
        )

    @staticmethod
    def log_ai_feature(user, feature_name, request, details=None):
        """Log AI feature usage"""
        AuditLogger.log(
            user=user,
            action=AuditLog.ActionType.AI_ANALYSIS,
            resource_type="ai_feature",
            request=request,
            details=details or {"feature": feature_name}
        )

    @staticmethod
    def log_payment(user, action, payment_id, request, details=None):
        """Log payment action"""
        AuditLogger.log(
            user=user,
            action=action,
            resource_type="payment",
            resource_id=payment_id,
            request=request,
            details=details or {}
        )


# Middleware for automatic audit logging
class AuditLogMiddleware:
    """Middleware to automatically log API requests"""

    # Paths to exclude from logging
    EXCLUDE_PATHS = [
        '/health/',
        '/ready/',
        '/admin/jsi18n/',
        '/static/',
        '/media/',
    ]

    # Actions that don't need detailed logging
    SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip excluded paths
        if any(request.path.startswith(p) for p in self.EXCLUDE_PATHS):
            return self.get_response(request)

        response = self.get_response(request)

        # Log only for API endpoints
        if request.path.startswith('/api/'):
            # Determine action type from request
            action = self._get_action_from_request(request)

            # Only log significant actions
            if action and response.status_code in [200, 201, 400, 401, 403, 404, 500]:
                # Get user if authenticated
                user = getattr(request, 'user', None)
                if user and user.is_authenticated:
                    AuditLog(
                        user=user,
                        action=action,
                        resource_type=self._get_resource_type(request),
                        ip_address=request.META.get("REMOTE_ADDR"),
                        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                        request_method=request.method,
                        request_path=request.path,
                        status_code=response.status_code,
                    ).save()

        return response

    def _get_action_from_request(self, request):
        """Determine action type from request"""
        path = request.path.lower()

        if '/auth/login' in path:
            return AuditLog.ActionType.LOGIN if request.method == 'POST' else None
        if '/auth/signup' in path:
            return AuditLog.ActionType.USER_CREATE if request.method == 'POST' else None
        if '/jobs/' in path and request.method == 'POST':
            return AuditLog.ActionType.JOB_CREATE
        if '/applications/' in path and request.method == 'POST':
            return AuditLog.ActionType.APPLICATION_CREATE

        return None

    def _get_resource_type(self, request):
        """Determine resource type from request path"""
        path = request.path.lower()

        if '/auth/' in path:
            return 'auth'
        if '/jobs/' in path:
            return 'job'
        if '/applications/' in path:
            return 'application'
        if '/resume/' in path:
            return 'resume'
        if '/billing/' in path:
            return 'payment'

        return 'unknown'