"""
Referral System
Users can invite friends and earn credits
"""
from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone
from datetime import timedelta


class ReferralCode(models.Model):
    """Unique referral code for each user"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_code'
    )
    code = models.CharField(max_length=20, unique=True)
    max_referrals = models.PositiveIntegerField(default=10)  # Max earning limit
    total_earned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.code}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        super().save(*args, **kwargs)

    def _generate_code(self):
        """Generate unique referral code"""
        return f"REF{uuid.uuid4().hex[:8].upper()}"


class Referral(models.Model):
    """Tracks referrals"""
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SIGNED_UP = "signed_up", "Signed Up"
        VERIFIED = "verified", "Verified"
        EARNED = "earned", "Credits Awarded"

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referrals_made'
    )
    referee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referred_by',
        null=True,
        blank=True
    )
    referee_email = models.EmailField()  # Email of invited person
    referral_code = models.ForeignKey(
        ReferralCode,
        on_delete=models.CASCADE,
        related_name='referrals'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    credits_earned = models.PositiveIntegerField(default=0)
    signed_up_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['referrer', 'referee_email']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.referrer.email} -> {self.referee_email}"


class ReferralSettings(models.Model):
    """Global referral settings"""
    referrer_credit_reward = models.PositiveIntegerField(default=5)  # Credits for referrer
    referee_credit_reward = models.PositiveIntegerField(default=3)  # Credits for new user
    min_signups_to_earn = models.PositiveIntegerField(default=1)  # Signups needed to earn
    referral_expiry_days = models.PositiveIntegerField(default=30)  # Referral expires after

    class Meta:
        verbose_name_plural = "Referral Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create settings"""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings


def generate_referral_code(user):
    """Generate referral code for a user"""
    referral_code, created = ReferralCode.objects.get_or_create(
        user=user,
        defaults={'max_referrals': 10}
    )
    return referral_code.code


def process_referral(referee_email, referrer_code):
    """Process a referral when new user signs up"""
    try:
        referral_code = ReferralCode.objects.get(code=referrer_code)
    except ReferralCode.DoesNotExist:
        return {'success': False, 'error': 'Invalid referral code'}

    if referral_code.user.email == referee_email:
        return {'success': False, 'error': 'Cannot refer yourself'}

    # Create or update referral
    referral, created = Referral.objects.get_or_create(
        referral_code=referral_code,
        referee_email=referee_email,
        defaults={
            'status': Referral.Status.SIGNED_UP,
            'signed_up_at': timezone.now()
        }
    )

    if not created and referral.status == Referral.Status.PENDING:
        referral.status = Referral.Status.SIGNED_UP
        referral.signed_up_at = timezone.now()
        referral.save()

    return {'success': True, 'referral': referral}


def award_referral_credits(referral_id):
    """Award credits after referral is verified"""
    try:
        referral = Referral.objects.get(id=referral_id)
    except Referral.DoesNotExist:
        return {'success': False, 'error': 'Referral not found'}

    if referral.status == Referral.Status.EARNED:
        return {'success': False, 'error': 'Already earned'}

    settings = ReferralSettings.get_settings()

    # Check if referrer has reached max
    if referral.referral_code.total_earned >= referral.referral_code.max_referrals:
        return {'success': False, 'error': 'Referral limit reached'}

    # Award credits
    from accounts.models import User

    # Credits for referrer
    referrer = referral.referral_code.user
    # Add credit logic here - depends on your credits system

    # Credits for referee (new user)
    if referral.referee:
        # Add credit logic for referee
        pass

    # Update referral status
    referral.status = Referral.Status.EARNED
    referral.credits_earned = settings.referrer_credit_reward
    referral.verified_at = timezone.now()
    referral.save()

    # Update referrer total
    referral.referral_code.total_earned += settings.referrer_credit_reward
    referral.referral_code.save()

    return {
        'success': True,
        'credits_awarded': settings.referrer_credit_reward,
        'referrer': referrer.email
    }


# =================== API ENDPOINTS ===================

"""
Add to jobs/urls.py:

path('referral/code/', views.get_referral_code, name='get-referral-code'),
path('referral/track/', views.track_referral, name='track-referral'),
path('referral/stats/', views.referral_stats, name='referral-stats'),
"""

# =================== FRONTEND INTEGRATION ===================

"""
Frontend - Referral Share Component:

const shareReferral = () => {
  const referralCode = user.referral_code;
  const shareUrl = `${window.location.origin}/signup?ref=${referralCode}`;

  // Copy to clipboard
  navigator.clipboard.writeText(shareUrl);

  // Share options
  const shareData = {
    title: 'Join AI Job Platform',
    text: 'Use my referral link to join and get free AI credits!',
    url: shareUrl
  };

  if (navigator.share) {
    navigator.share(shareData);
  }
};

const referralLink = `https://aijobplatform.com/signup?ref=${referralCode}`;
"""