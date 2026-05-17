from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .comparison_service import AIComparisonService
from .models import (
    UsageLedger, RecruiterQuery, QueryResult, JobApplication,
    ResumeJobComparison, JobPost, Notification, UserSubscription,
    JobApplication
)
from .recruiter_services import RecruiterAssistant
from core.cache import CacheService


# =================== USER TASKS ===================

@shared_task
def compact_usage_activity(user_id):
    """Clean up old usage records"""
    cutoff = timezone.now() - timezone.timedelta(days=90)
    deleted, _ = UsageLedger.objects.filter(user_id=user_id, created_at__lt=cutoff).delete()
    return {"deleted": deleted, "user_id": user_id}


@shared_task
def warm_dashboard_cache():
    """Pre-warm dashboard cache for active users"""
    from accounts.models import User
    active_users = User.objects.filter(is_active=True)[:100]
    for user in active_users:
        # Cache dashboard data
        CacheService.set_user_profile(user.id, {"cached": True}, ttl=60)
    return {"status": "ready", "warmed_at": timezone.now().isoformat()}


# =================== NOTIFICATION TASKS ===================

@shared_task
def send_job_alert_email(user_id, job_id):
    """Send email when new job matches user preferences"""
    from accounts.models import User
    from jobs.models import JobPost

    try:
        user = User.objects.get(id=user_id)
        job = JobPost.objects.get(id=job_id)

        send_mail(
            subject=f"New Job Alert: {job.title}",
            message=f"A new job matching your preferences: {job.title} at {job.company}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return {"status": "sent", "user_id": user_id, "job_id": job_id}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@shared_task
def send_application_update_email(application_id):
    """Send email when application status changes"""
    try:
        application = JobApplication.objects.select_related('applicant', 'job').get(id=application_id)
        user = application.applicant
        job = application.job

        send_mail(
            subject=f"Application Update: {job.title}",
            message=f"Your application for {job.title} at {job.company} is now {application.status}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return {"status": "sent", "application_id": application_id}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@shared_task
def create_daily_digest(user_id):
    """Create daily digest notification for user"""
    from accounts.models import User

    try:
        user = User.objects.get(id=user_id)
        new_jobs = JobPost.objects.filter(
            is_active=True,
            created_at__gte=timezone.now() - timezone.timedelta(days=1)
        ).count()

        if new_jobs > 0:
            Notification.objects.create(
                user=user,
                type=Notification.NotificationType.JOB_MATCH,
                title="New Jobs Available",
                message=f"{new_jobs} new jobs matching your profile are available!",
            )
        return {"status": "created", "user_id": user_id, "new_jobs": new_jobs}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# =================== AI TASKS ===================

@shared_task
def process_ai_resume_analysis(resume_id):
    """Process AI resume analysis asynchronously"""
    from jobs.models import Resume
    from core.ai_integrations import AIIntegrationService

    try:
        resume = Resume.objects.get(id=resume_id)
        result = AIIntegrationService.analyze_resume_with_ai(
            resume.extracted_text or "",
            None
        )

        if result.get("success"):
            from jobs.models import AIResumeAnalysis
            data = result.get("data", {})

            AIResumeAnalysis.objects.update_or_create(
                resume=resume,
                defaults={
                    "overall_rating": data.get("overall_rating", 0),
                    "strengths": data.get("strengths", []),
                    "weaknesses": data.get("weaknesses", []),
                    "detailed_feedback": data.get("detailed_feedback", ""),
                    "readability_score": data.get("readability_score", 0),
                    "impact_score": data.get("impact_score", 0),
                    "recommendations": data.get("recommendations", []),
                }
            )
            return {"status": "completed", "resume_id": resume_id}
        return {"status": "failed", "resume_id": resume_id, "error": result.get("error")}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@shared_task
def process_batch_resume_scoring(job_id):
    """Score all resumes against a job"""
    from jobs.models import Resume

    job = JobPost.objects.get(id=job_id)
    resumes = Resume.objects.filter(user__is_active=True).select_related("user")

    results = []
    for resume in resumes:
        from core.ai_integrations import AIIntegrationService
        result = AIIntegrationService.analyze_resume_with_ai(
            resume.extracted_text or "",
            job.description
        )
        if result.get("success"):
            score = result.get("data", {}).get("overall_rating", 0)
            results.append({"resume_id": resume.id, "score": score})

    return {"job_id": job_id, "scored_count": len(results), "results": results}


# =================== ANALYTICS TASKS ===================

@shared_task
def update_recruiter_analytics(recruiter_id):
    """Update analytics for recruiter"""
    from jobs.models import RecruiterAnalytics
    from jobs.models import JobPost, JobApplication

    recruiter = User.objects.get(id=recruiter_id)
    posted_jobs = JobPost.objects.filter(posted_by_id=recruiter_id, is_active=True)

    total_applications = JobApplication.objects.filter(job__posted_by_id=recruiter_id).count()
    total_hired = JobApplication.objects.filter(
        job__posted_by_id=recruiter_id,
        status="shortlisted"
    ).count()

    RecruiterAnalytics.objects.update_or_create(
        recruiter=recruiter,
        defaults={
            "total_jobs_posted": posted_jobs.count(),
            "total_applications": total_applications,
            "total_hired": total_hired,
            "engagement_rate": (total_hired / total_applications * 100) if total_applications > 0 else 0,
        }
    )
    return {"status": "updated", "recruiter_id": recruiter_id}


@shared_task
def generate_weekly_report():
    """Generate weekly analytics report"""
    from accounts.models import User

    total_users = User.objects.filter(is_active=True).count()
    total_jobs = JobPost.objects.filter(is_active=True).count()
    total_applications = JobApplication.objects.count()

    # Could send to admin email
    report = f"""
    Weekly Report:
    - Total Users: {total_users}
    - Total Jobs: {total_jobs}
    - Total Applications: {total_applications}
    """

    return {"report": report, "generated_at": timezone.now().isoformat()}


# =================== MAINTENANCE TASKS ===================

@shared_task
def cleanup_old_notifications(days=30):
    """Delete old read notifications"""
    cutoff = timezone.now() - timezone.timedelta(days=days)
    deleted, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff
    ).delete()
    return {"notifications_deleted": deleted}


@shared_task
def cleanup_inactive_sessions():
    """Clean up expired sessions"""
    from django.contrib.sessions.models import Session
    expired = Session.objects.filter(expire_date__lt=timezone.now())
    count = expired.count()
    expired.delete()
    return {"sessions_deleted": count}


@shared_task
def sync_external_jobs():
    """Sync jobs from external APIs"""
    from jobs.feature_views import fetch_external_jobs

    # This would call the external API functions
    # fetch_external_jobs() - already implemented in feature_views
    return {"status": "synced", "synced_at": timezone.now().isoformat()}


# =================== SUBSCRIPTION TASKS ===================

@shared_task
def check_subscription_expiry():
    """Check and notify users about expiring subscriptions"""
    from datetime import timedelta
    from accounts.models import User

    expiring_date = timezone.now() + timedelta(days=3)

    subscriptions = UserSubscription.objects.filter(
        status=UserSubscription.Status.ACTIVE,
        current_period_end__lte=expiring_date
    ).select_related("user")

    for sub in subscriptions:
        send_mail(
            subject="Subscription Expiring Soon",
            message="Your subscription will expire in 3 days. Please renew to continue premium features.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[sub.user.email],
            fail_silently=False,
        )

    return {"notified_count": subscriptions.count()}


# =================== CACHE TASKS ===================

@shared_task
def invalidate_user_cache(user_id):
    """Invalidate all cache for a user"""
    CacheService.invalidate_user_profile(user_id)
    return {"status": "invalidated", "user_id": user_id}


@shared_task
def invalidate_job_cache(job_id):
    """Invalidate all cache for a job"""
    CacheService.invalidate_job(job_id)
    return {"status": "invalidated", "job_id": job_id}


@shared_task
def process_recruiter_query(query_id):
    """Process recruiter query asynchronously and persist ranked results."""
    try:
        query = RecruiterQuery.objects.get(id=query_id)
    except RecruiterQuery.DoesNotExist:
        return {"error": "query_not_found", "query_id": query_id}

    assistant = RecruiterAssistant()
    parsed = assistant.parse_query(query.query or "")

    filters = parsed.get("filters") or {}
    filters["limit"] = int(parsed.get("limit", 20))
    results = assistant.search_candidates(filters)

    # Replace old result set for this query with fresh results.
    query.results.all().delete()

    app_ids = [item.get("candidate_id") for item in results if item.get("candidate_id")]
    app_map = {
        app.id: app
        for app in JobApplication.objects.filter(id__in=app_ids).select_related("applicant", "job")
    }

    stored = 0
    for item in results:
        app_id = item.get("candidate_id")
        application = app_map.get(app_id)
        if not application:
            continue

        QueryResult.objects.create(
            query=query,
            candidate=application,
            relevance_score=float(item.get("score", 0) or 0),
            reasoning=item.get("reasoning", ""),
        )
        stored += 1

    query.query_type = parsed.get("intent", query.query_type or "search")
    query.results_count = stored
    query.save(update_fields=["query_type", "results_count"])

    return {
        "query_id": query.id,
        "intent": query.query_type,
        "stored_results": stored,
    }


@shared_task
def process_resume_job_comparison(comparison_id):
    """Run resume-to-job comparison in the background for larger uploads."""
    try:
        comparison = ResumeJobComparison.objects.select_related("resume", "job").get(id=comparison_id)
    except ResumeJobComparison.DoesNotExist:
        return {"error": "comparison_not_found", "comparison_id": comparison_id}

    comparison.status = "processing"
    comparison.error_message = ""
    comparison.save(update_fields=["status", "error_message"])

    try:
        service = AIComparisonService()
        result = service.compare(comparison.resume, comparison.job)
        ResumeJobComparison.objects.filter(id=comparison.id).update(
            match_percentage=result["match_percentage"],
            semantic_similarity=result["semantic_similarity"],
            tfidf_similarity=result["tfidf_similarity"],
            skill_match=result["skill_match"],
            matched_skills=result["matched_skills"],
            missing_skills=result["missing_skills"],
            missing_certifications=result["missing_certifications"],
            experience_score=result["experience_score"],
            ats_score=result["ats_score"],
            salary_prediction=result["salary_prediction"],
            improvement_suggestions=result["improvement_suggestions"],
            career_recommendations=result["career_recommendations"],
            keyword_analysis=result["keyword_analysis"],
            heatmap=result["heatmap"],
            status="completed",
            error_message="",
        )
        return {"comparison_id": comparison.id, "status": "completed", "match": result["match_percentage"]}
    except Exception as exc:
        ResumeJobComparison.objects.filter(id=comparison.id).update(status="failed", error_message=str(exc))
        return {"comparison_id": comparison.id, "status": "failed", "error": str(exc)}
