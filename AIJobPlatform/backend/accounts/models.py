from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        RECRUITER = "recruiter", "Recruiter"
        ADMIN = "admin", "Admin"

    class Theme(models.TextChoices):
        LIGHT = "light", "Light"
        DARK = "dark", "Dark"
        SYSTEM = "system", "System"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    is_email_verified = models.BooleanField(default=False)
    company_name = models.CharField(max_length=150, blank=True)
    university_name = models.CharField(max_length=150, blank=True)
    
    # OAuth fields
    google_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    linkedin_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    oauth_provider = models.CharField(max_length=50, blank=True)  # google, linkedin, email
    
    # Theme preference
    theme_preference = models.CharField(
        max_length=20,
        choices=Theme.choices,
        default=Theme.LIGHT
    )
    notifications_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    about = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_items = models.JSONField(default=list, blank=True)
    profile_picture = models.FileField(upload_to="profiles/", blank=True, null=True)
    headline = models.CharField(max_length=180, blank=True)
    location = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Profile({self.user.email})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()


# OTP Verification for Authentication
class OTPVerification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="otp_verifications",
    )
    otp = models.CharField(max_length=6)
    email = models.EmailField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.email}"


# Password Reset Token
class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=255, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Reset Token for {self.user.email}"

