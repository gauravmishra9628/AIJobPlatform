"""
OAuth and Enhanced Authentication Module
Handles Google OAuth, OTP, and advanced authentication flows
"""

import os
import secrets
from datetime import timedelta
from typing import Optional, Dict, Tuple
import requests
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response

User = get_user_model()


class GoogleOAuthService:
    """Service for Google OAuth integration"""
    
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    @staticmethod
    def verify_google_token(id_token: str) -> Optional[Dict]:
        """
        Verify Google ID token and get user info
        Returns user data if valid, None if invalid
        """
        try:
            # Option 1: Verify via Google's tokeninfo endpoint
            response = requests.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Google OAuth verification error: {str(e)}")
            return None
    
    @staticmethod
    def get_user_from_google(id_token: str, access_token: str = None) -> Tuple[Optional[User], bool]:
        """
        Get or create user from Google OAuth token
        Returns (user, created) tuple
        """
        user_info = GoogleOAuthService.verify_google_token(id_token)
        
        if not user_info:
            return None, False
        
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name", "")
        picture_url = user_info.get("picture")
        
        if not google_id or not email:
            return None, False
        
        # Get or create user
        user, created = User.objects.get_or_create(
            google_id=google_id,
            defaults={
                "email": email,
                "first_name": name.split()[0] if name else "",
                "last_name": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
                "oauth_provider": "google",
                "is_email_verified": True,  # Google emails are verified
            }
        )
        
        # Update existing user's Google ID if they signed up with email
        if not created and not user.google_id:
            user.google_id = google_id
            user.oauth_provider = "google"
            user.is_email_verified = True
            user.save()
        
        # Download and save profile picture if new user
        if created and picture_url:
            try:
                GoogleOAuthService._save_profile_picture(user, picture_url)
            except Exception as e:
                print(f"Failed to save profile picture: {str(e)}")
        
        return user, created
    
    @staticmethod
    def _save_profile_picture(user, picture_url):
        """Download and save profile picture from Google"""
        try:
            from django.core.files.base import ContentFile
            
            response = requests.get(picture_url, timeout=5)
            if response.status_code == 200:
                file_name = f"google_profile_{user.id}.jpg"
                user.profile.profile_picture.save(
                    file_name,
                    ContentFile(response.content),
                    save=True
                )
        except Exception as e:
            print(f"Error saving profile picture: {str(e)}")


class OTPService:
    """Service for OTP-based email verification"""
    
    OTP_EXPIRY_MINUTES = 15
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a random 6-digit OTP"""
        return str(secrets.randbelow(1000000)).zfill(6)
    
    @staticmethod
    def send_otp_email(user: User, email: str = None) -> bool:
        """
        Generate OTP and send to user's email
        Returns True if successful
        """
        from django.core.mail import send_mail
        from .models import OTPVerification
        
        target_email = email or user.email
        otp = OTPService.generate_otp()
        
        try:
            # Create OTP record
            expires_at = timezone.now() + timedelta(minutes=OTPService.OTP_EXPIRY_MINUTES)
            OTPVerification.objects.create(
                user=user,
                otp=otp,
                email=target_email,
                expires_at=expires_at
            )
            
            # Send email
            subject = "Your Email Verification Code"
            message = f"""Hello {user.first_name or user.email},

Your OTP for email verification is: {otp}

This code expires in {OTPService.OTP_EXPIRY_MINUTES} minutes.

Do not share this code with anyone.

Best regards,
AI Job Platform Team"""
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [target_email],
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending OTP email: {str(e)}")
            return False
    
    @staticmethod
    def verify_otp(user: User, otp: str, email: str = None) -> Tuple[bool, str]:
        """
        Verify OTP for user
        Returns (is_valid, message)
        """
        from .models import OTPVerification
        
        target_email = email or user.email
        
        try:
            # Get latest OTP for this email
            otp_record = OTPVerification.objects.filter(
                user=user,
                email=target_email,
                otp=otp,
                is_used=False
            ).order_by("-created_at").first()
            
            if not otp_record:
                return False, "Invalid OTP"
            
            # Check if expired
            if timezone.now() > otp_record.expires_at:
                return False, "OTP has expired"
            
            # Mark as used and verify email
            otp_record.is_used = True
            otp_record.save()
            
            user.is_email_verified = True
            user.save()
            
            return True, "Email verified successfully"
            
        except Exception as e:
            print(f"Error verifying OTP: {str(e)}")
            return False, str(e)


class PasswordResetService:
    """Service for password reset functionality"""
    
    RESET_TOKEN_EXPIRY_HOURS = 24
    
    @staticmethod
    def generate_reset_token(user: User) -> str:
        """
        Generate and save password reset token
        Returns the token
        """
        from .models import PasswordResetToken
        
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=PasswordResetService.RESET_TOKEN_EXPIRY_HOURS)
        
        # Invalidate previous tokens
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        
        reset_token = PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )
        
        return token
    
    @staticmethod
    def send_reset_email(user: User, token: str, frontend_url: str = None) -> bool:
        """Send password reset email"""
        try:
            from django.core.mail import send_mail
            
            reset_url = f"{frontend_url or settings.FRONTEND_URL}/reset-password?token={token}"
            
            subject = "Password Reset Request"
            message = f"""Hello {user.first_name or user.email},

You requested a password reset. Click the link below to reset your password:

{reset_url}

This link expires in {PasswordResetService.RESET_TOKEN_EXPIRY_HOURS} hours.

If you didn't request this, ignore this email.

Best regards,
AI Job Platform Team"""
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending reset email: {str(e)}")
            return False
    
    @staticmethod
    def verify_reset_token(token: str) -> Tuple[Optional[User], str]:
        """
        Verify reset token and return user
        Returns (user, message)
        """
        from .models import PasswordResetToken
        
        try:
            reset_record = PasswordResetToken.objects.get(
                token=token,
                is_used=False
            )
            
            # Check if expired
            if timezone.now() > reset_record.expires_at:
                return None, "Reset link has expired"
            
            return reset_record.user, "Valid token"
            
        except PasswordResetToken.DoesNotExist:
            return None, "Invalid reset token"
    
    @staticmethod
    def reset_password(token: str, new_password: str) -> Tuple[bool, str]:
        """Reset password using token"""
        from .models import PasswordResetToken
        
        user, message = PasswordResetService.verify_reset_token(token)
        
        if not user:
            return False, message
        
        try:
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_record = PasswordResetToken.objects.get(token=token)
            reset_record.is_used = True
            reset_record.save()
            
            return True, "Password reset successfully"
            
        except Exception as e:
            return False, str(e)


class LinkedInOAuthService:
    """Service for LinkedIn OAuth integration (future use)"""
    
    LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/me"
    
    @staticmethod
    def get_user_from_linkedin(access_token: str) -> Tuple[Optional[User], bool]:
        """Get or create user from LinkedIn OAuth token"""
        # Implementation similar to Google OAuth
        # To be implemented when LinkedIn credentials are available
        pass
