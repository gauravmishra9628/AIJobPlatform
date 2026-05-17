"""
Notification System
Handles email and in-app notifications
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from jobs.models import Notification
from accounts.models import User
from celery import shared_task
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications"""

    @staticmethod
    def create_notification(
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        link: str = None,
        job_id: int = None,
        application_id: int = None
    ) -> Notification:
        """Create in-app notification"""
        from jobs.models import JobPost, JobApplication

        notification = Notification.objects.create(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
        )

        if job_id:
            notification.related_job_id = job_id
        if application_id:
            notification.related_application_id = application_id

        notification.save()

        return notification

    @staticmethod
    def send_email_notification(
        user_email: str,
        subject: str,
        template: str = None,
        context: dict = None,
        html_message: str = None,
        plain_message: str = None
    ) -> bool:
        """Send email notification"""
        try:
            if not settings.DEFAULT_FROM_EMAIL:
                logger.warning("No DEFAULT_FROM_EMAIL configured")
                return False

            # Prepare message
            if html_message is None and template and context:
                html_message = render_to_string(f'emails/{template}.html', context)
                plain_message = strip_tags(html_message)
            elif plain_message is None and html_message:
                plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message or message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Email sent to {user_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {user_email}: {str(e)}")
            return False

    @staticmethod
    def notify_job_alert(user, job):
        """Notify user about new job matching their profile"""
        # In-app notification
        NotificationService.create_notification(
            user_id=user.id,
            notification_type=Notification.NotificationType.JOB_MATCH,
            title=f"New Job: {job.title}",
            message=f"A new job matching your profile: {job.title} at {job.company}",
            link=f"/jobs/{job.id}",
            job_id=job.id
        )

        # Email notification (if enabled)
        if user.notifications_enabled:
            send_job_alert_email.delay(user.id, job.id)

    @staticmethod
    def notify_application_update(application, new_status):
        """Notify about application status change"""
        user = application.applicant

        status_messages = {
            'reviewing': 'Your application is being reviewed',
            'shortlisted': 'Congratulations! You have been shortlisted',
            'rejected': 'Your application was not selected this time',
            'interview': 'You have been invited for an interview',
        }

        message = status_messages.get(new_status, f'Application status: {new_status}')

        # In-app
        NotificationService.create_notification(
            user_id=user.id,
            notification_type=Notification.NotificationType.APPLICATION,
            title=f"Application Update: {application.job.title}",
            message=message,
            link=f"/applications/{application.id}",
            application_id=application.id
        )

        # Email
        send_application_update_email.delay(application.id)


# =================== CELERY TASKS ===================

@shared_task
def send_job_alert_email(user_id, job_id):
    """Send job alert email asynchronously"""
    from jobs.models import JobPost

    try:
        user = User.objects.get(id=user_id)
        job = JobPost.objects.get(id=job_id)

        subject = f"🔔 New Job Alert: {job.title}"

        context = {
            'user': user,
            'job': job,
            'match_score': 85,  # Could calculate actual match
        }

        html_message = render_to_string('emails/job_alert.html', context)

        return NotificationService.send_email_notification(
            user_email=user.email,
            subject=subject,
            html_message=html_message
        )
    except Exception as e:
        logger.error(f"Job alert email failed: {e}")
        return False


@shared_task
def send_application_update_email(application_id):
    """Send application update email asynchronously"""
    from jobs.models import JobApplication

    try:
        application = JobApplication.objects.select_related(
            'applicant', 'job'
        ).get(id=application_id)

        user = application.applicant
        job = application.job

        subject = f"📋 Application Update: {job.title}"

        context = {
            'user': user,
            'application': application,
            'job': job,
        }

        html_message = render_to_string('emails/application_update.html', context)

        return NotificationService.send_email_notification(
            user_email=user.email,
            subject=subject,
            html_message=html_message
        )
    except Exception as e:
        logger.error(f"Application update email failed: {e}")
        return False


@shared_task
def send_daily_digest(user_id):
    """Send daily digest email"""
    from jobs.models import JobPost, JobApplication

    try:
        user = User.objects.get(id=user_id)

        # Get new jobs since last login
        new_jobs = JobPost.objects.filter(
            is_active=True,
            created_at__gte=user.last_login
        )[:10]

        # Get application updates
        applications = JobApplication.objects.filter(
            applicant=user,
            updated_at__gte=user.last_login
        )

        if not new_jobs and not applications:
            return "No updates to send"

        subject = f"📊 Your Daily Digest - {len(new_jobs)} new jobs"

        context = {
            'user': user,
            'new_jobs': new_jobs,
            'applications': applications,
        }

        html_message = render_to_string('emails/daily_digest.html', context)

        return NotificationService.send_email_notification(
            user_email=user.email,
            subject=subject,
            html_message=html_message
        )
    except Exception as e:
        logger.error(f"Daily digest email failed: {e}")
        return False


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new users"""
    try:
        user = User.objects.get(id=user_id)

        subject = "🎉 Welcome to AI Job Platform!"

        context = {
            'user': user,
        }

        html_message = render_to_string('emails/welcome.html', context)

        return NotificationService.send_email_notification(
            user_email=user.email,
            subject=subject,
            html_message=html_message
        )
    except Exception as e:
        logger.error(f"Welcome email failed: {e}")
        return False


@shared_task
def batch_notify_users(notification_type, user_ids, title, message, **kwargs):
    """Batch notification to multiple users"""
    results = []

    for user_id in user_ids:
        try:
            notification = NotificationService.create_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                **kwargs
            )
            results.append({'user_id': user_id, 'success': True})
        except Exception as e:
            results.append({'user_id': user_id, 'success': False, 'error': str(e)})

    return {
        'total': len(user_ids),
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success'])
    }


# =================== EMAIL TEMPLATES ===================
# Create these templates in jobs/templates/emails/

# jobs/templates/emails/welcome.html
WELCOME_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #4F46E5; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .btn { display: inline-block; background: #4F46E5; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome to AI Job Platform!</h1>
        </div>
        <div class="content">
            <p>Hi {{ user.first_name }},</p>
            <p>Welcome to AI Job Platform! We're excited to help you find your dream career.</p>
            <p>Here's what you can do:</p>
            <ul>
                <li>📄 <strong>Upload your resume</strong> - Get AI-powered analysis</li>
                <li>🎯 <strong>Get job recommendations</strong> - Based on your skills</li>
                <li>🤖 <strong>AI Career Coach</strong> - Personalized career guidance</li>
                <li>📝 <strong>Practice interviews</strong> - With AI-generated questions</li>
            </ul>
            <p><a href="https://aijobplatform.com/dashboard" class="btn">Get Started</a></p>
            <p>Best of luck!</p>
            <p>— The AI Job Platform Team</p>
        </div>
    </div>
</body>
</html>
"""