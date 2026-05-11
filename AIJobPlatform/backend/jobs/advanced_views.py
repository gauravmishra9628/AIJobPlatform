import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, F, Avg
from django.utils import timezone

from accounts.decorators import jwt_required, role_required
from accounts.models import User
from .models import (
    JobBookmark, ResumeAtsScore, ApplicationStageLog,
    SkillGapAnalysis, Notification, InterviewPreparation,
    RecruiterAnalytics, JobApplication, JobPost, Resume
)


def parse_json(request):
    try:
        return json.loads(request.body)
    except Exception:
        return None


# ============ ATS SCORING ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def analyze_resume_ats(request):
    """Analyze resume for ATS compatibility and generate score"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    resume_id = data.get("resume_id")
    job_id = data.get("job_id")
    
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
        job = JobPost.objects.get(id=job_id) if job_id else None
    except Resume.DoesNotExist:
        return JsonResponse({"error": "Resume not found"}, status=404)
    except JobPost.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)
    
    # Simple ATS scoring logic
    resume_text = resume.extracted_text.lower()
    resume_skills = set(resume.extracted_skills)
    
    scores = {}
    missing = {"keywords": [], "skills": []}
    suggestions = []
    
    if job:
        job_skills = set(s.lower().strip() for s in job.skills_required.split(","))
        matched_skills = resume_skills & job_skills
        skills_match_score = int((len(matched_skills) / max(len(job_skills), 1)) * 100)
        missing["skills"] = list(job_skills - resume_skills)
        
        scores["skills_match_score"] = skills_match_score
        
        # Keyword matching
        job_keywords = set(job.description.lower().split())
        resume_keywords = set(resume_text.split())
        keyword_overlap = len(job_keywords & resume_keywords)
        keyword_score = min(int((keyword_overlap / max(len(job_keywords), 1)) * 100), 100)
        scores["keyword_match_score"] = keyword_score
        
        # Format checks
        format_score = 85
        if len(resume_text) < 100:
            format_score -= 20
            suggestions.append("Resume appears too short. Expand with more details.")
        if "@" not in resume_text:
            format_score -= 15
            suggestions.append("Include contact email in resume.")
        scores["format_score"] = format_score
        
        # Experience score (basic heuristic)
        exp_keywords = ["experience", "years", "project", "work"]
        exp_score = sum(50 for kw in exp_keywords if kw in resume_text)
        exp_score = min(exp_score, 100)
        scores["experience_score"] = exp_score
        
        # Overall score
        overall = (keyword_score * 0.3 + skills_match_score * 0.4 + format_score * 0.2 + exp_score * 0.1)
        scores["overall_score"] = int(overall)
        
        # Improvement suggestions
        if scores["overall_score"] < 70:
            suggestions.append("Add more relevant keywords from the job description.")
        if missing["skills"]:
            suggestions.append(f"Consider mentioning: {', '.join(list(missing['skills'])[:3])}")
        if skills_match_score < 50:
            suggestions.append("Your skills don't match well. Consider upskilling in required areas.")
    else:
        scores = {
            "overall_score": 0,
            "keyword_match_score": 0,
            "skills_match_score": 0,
            "experience_score": 0,
            "format_score": 0,
        }
        suggestions = ["Specify a job to get detailed ATS analysis."]
    
    # Save or update ATS score
    ats_score, created = ResumeAtsScore.objects.update_or_create(
        resume=resume,
        defaults={
            "job": job,
            **scores,
            "missing_keywords": missing["keywords"],
            "missing_skills": missing["skills"],
            "improvement_suggestions": suggestions,
        }
    )
    
    return JsonResponse({
        "id": ats_score.id,
        **scores,
        "missing_skills": missing["skills"],
        "improvement_suggestions": suggestions,
        "created": created,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_ats_score(request, score_id):
    """Get ATS score details"""
    try:
        score = ResumeAtsScore.objects.get(id=score_id, resume__user=request.user)
    except ResumeAtsScore.DoesNotExist:
        return JsonResponse({"error": "ATS score not found"}, status=404)
    
    return JsonResponse({
        "id": score.id,
        "overall_score": score.overall_score,
        "keyword_match_score": score.keyword_match_score,
        "skills_match_score": score.skills_match_score,
        "experience_score": score.experience_score,
        "format_score": score.format_score,
        "missing_keywords": score.missing_keywords,
        "missing_skills": score.missing_skills,
        "improvement_suggestions": score.improvement_suggestions,
        "analyzed_at": score.analyzed_at.isoformat(),
    })


# ============ JOB BOOKMARK ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def bookmark_job(request):
    """Bookmark or unbookmark a job"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    job_id = data.get("job_id")
    action = data.get("action", "add")  # add or remove
    notes = data.get("notes", "")
    
    try:
        job = JobPost.objects.get(id=job_id)
    except JobPost.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)
    
    if action == "add":
        bookmark, created = JobBookmark.objects.get_or_create(
            user=request.user,
            job=job,
            defaults={"notes": notes}
        )
        if not created:
            bookmark.notes = notes
            bookmark.save()
        return JsonResponse({
            "id": bookmark.id,
            "job_id": job.id,
            "bookmarked": True,
            "bookmarked_at": bookmark.bookmarked_at.isoformat(),
        })
    elif action == "remove":
        JobBookmark.objects.filter(user=request.user, job=job).delete()
        return JsonResponse({"bookmarked": False})
    
    return JsonResponse({"error": "Invalid action"}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def list_bookmarks(request):
    """List all bookmarked jobs for user"""
    bookmarks = JobBookmark.objects.filter(user=request.user).select_related("job")
    
    return JsonResponse({
        "count": bookmarks.count(),
        "bookmarks": [
            {
                "id": b.id,
                "job": {
                    "id": b.job.id,
                    "title": b.job.title,
                    "company": b.job.company,
                    "location": b.job.location,
                    "employment_type": b.job.employment_type,
                    "salary_range": b.job.salary_range,
                },
                "notes": b.notes,
                "bookmarked_at": b.bookmarked_at.isoformat(),
            }
            for b in bookmarks
        ]
    })


# ============ APPLICATION TRACKING ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
@role_required(["recruiter", "admin"])
def update_application_stage(request):
    """Update application stage with tracking"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    app_id = data.get("application_id")
    new_stage = data.get("stage")
    notes = data.get("notes", "")
    
    try:
        app = JobApplication.objects.get(id=app_id, job__posted_by=request.user)
    except JobApplication.DoesNotExist:
        return JsonResponse({"error": "Application not found"}, status=404)
    
    old_stage = app.status
    app.status = new_stage
    app.save()
    
    # Log the stage change
    ApplicationStageLog.objects.create(
        application=app,
        from_stage=old_stage,
        to_stage=new_stage,
        changed_by=request.user,
        notes=notes,
    )
    
    # Create notification for applicant
    Notification.objects.create(
        user=app.applicant,
        type=Notification.NotificationType.APPLICATION,
        title=f"Application Status Updated",
        message=f"Your application for {app.job.title} at {app.job.company} has been moved to {new_stage}.",
        related_application=app,
    )
    
    return JsonResponse({
        "id": app.id,
        "status": new_stage,
        "stage_log_created": True,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_application_history(request, app_id):
    """Get application stage history"""
    try:
        app = JobApplication.objects.get(
            Q(id=app_id, applicant=request.user) | Q(id=app_id, job__posted_by=request.user)
        )
    except JobApplication.DoesNotExist:
        return JsonResponse({"error": "Application not found"}, status=404)
    
    logs = ApplicationStageLog.objects.filter(application=app)
    
    return JsonResponse({
        "application_id": app.id,
        "current_status": app.status,
        "history": [
            {
                "from_stage": log.from_stage,
                "to_stage": log.to_stage,
                "changed_by": log.changed_by.email if log.changed_by else "System",
                "notes": log.notes,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    })


# ============ SKILL GAP ANALYSIS ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def analyze_skill_gap(request):
    """Analyze skill gap for user"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    target_role = data.get("target_role", "")
    
    # Get user's current skills
    profile = request.user.profile
    current_skills = profile.skills or []
    
    # Define role-based required skills (simplified)
    role_skills = {
        "junior developer": ["Python", "JavaScript", "HTML", "CSS", "Git"],
        "senior developer": ["Python", "JavaScript", "Docker", "AWS", "SQL"],
        "data scientist": ["Python", "Machine Learning", "SQL", "Statistics", "TensorFlow"],
        "product manager": ["Product Strategy", "Analytics", "Communication", "Leadership"],
    }
    
    target_skills = role_skills.get(target_role.lower(), [])
    missing_skills = [s for s in target_skills if s not in current_skills]
    
    learning_paths = {
        "Python": "https://www.udemy.com/course/python/",
        "JavaScript": "https://www.udemy.com/course/javascript/",
        "Docker": "https://www.udemy.com/course/docker-mastery/",
        "AWS": "https://aws.amazon.com/training/",
        "Machine Learning": "https://www.coursera.org/learn/machine-learning",
        "Product Strategy": "https://www.reforge.com/learn/product-strategy",
    }
    
    gap_analysis, created = SkillGapAnalysis.objects.update_or_create(
        user=request.user,
        defaults={
            "current_skills": current_skills,
            "target_role": target_role,
            "missing_skills": missing_skills,
            "learning_paths": [{"skill": s, "resource": learning_paths.get(s, "")} for s in missing_skills],
        }
    )
    
    return JsonResponse({
        "id": gap_analysis.id,
        "target_role": target_role,
        "current_skills": current_skills,
        "missing_skills": missing_skills,
        "learning_paths": gap_analysis.learning_paths,
        "proficiency_levels": gap_analysis.proficiency_levels,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_skill_gap(request):
    """Get user's skill gap analysis"""
    try:
        gap = SkillGapAnalysis.objects.get(user=request.user)
    except SkillGapAnalysis.DoesNotExist:
        return JsonResponse({"error": "No skill gap analysis found"}, status=404)
    
    return JsonResponse({
        "id": gap.id,
        "target_role": gap.target_role,
        "current_skills": gap.current_skills,
        "missing_skills": gap.missing_skills,
        "learning_paths": gap.learning_paths,
        "proficiency_levels": gap.proficiency_levels,
        "analyzed_at": gap.analyzed_at.isoformat(),
    })


# ============ NOTIFICATIONS ENDPOINTS ============

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def list_notifications(request):
    """Get user notifications"""
    unread_only = request.GET.get("unread", "false").lower() == "true"
    
    notifications = Notification.objects.filter(user=request.user)
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    return JsonResponse({
        "count": notifications.count(),
        "unread_count": Notification.objects.filter(user=request.user, is_read=False).count(),
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications[:50]  # Latest 50
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def mark_notification_read(request):
    """Mark notification as read"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    notification_id = data.get("notification_id")
    
    try:
        notif = Notification.objects.get(id=notification_id, user=request.user)
        notif.is_read = True
        notif.save()
        return JsonResponse({"id": notif.id, "is_read": True})
    except Notification.DoesNotExist:
        return JsonResponse({"error": "Notification not found"}, status=404)


# ============ INTERVIEW PREPARATION ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def generate_interview_prep(request):
    """Generate interview preparation materials"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    app_id = data.get("application_id")
    
    try:
        app = JobApplication.objects.get(id=app_id, applicant=request.user)
    except JobApplication.DoesNotExist:
        return JsonResponse({"error": "Application not found"}, status=404)
    
    role = app.job.title
    
    # Generate sample interview questions
    questions = [
        f"Tell us about your experience with the technologies required for {role}.",
        f"How would you approach {app.job.description[:50]}...?",
        f"What interests you most about this {role} role?",
        "What are your strengths and how do they apply to this role?",
        "Describe a challenging project you've worked on.",
    ]
    
    # Coding problems for tech roles
    coding_problems = []
    if any(lang in role.lower() for lang in ["developer", "engineer", "programmer"]):
        coding_problems = [
            "Reverse a string or linked list",
            "Find duplicate elements in array",
            "Implement a stack/queue",
            "Sort an array efficiently",
        ]
    
    # Tips
    tips = [
        "Research the company thoroughly",
        "Prepare examples using STAR method",
        "Practice answering technical questions",
        "Prepare questions to ask the interviewer",
        "Get good sleep before the interview",
    ]
    
    # Resources
    resources = [
        {"title": "LeetCode", "url": "https://leetcode.com/"},
        {"title": "InterviewBit", "url": "https://www.interviewbit.com/"},
        {"title": "GeeksforGeeks", "url": "https://www.geeksforgeeks.org/"},
        {"title": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer"},
    ]
    
    prep, created = InterviewPreparation.objects.update_or_create(
        user=request.user,
        job_application=app,
        defaults={
            "role": role,
            "generated_questions": questions,
            "coding_problems": coding_problems,
            "tips_and_tricks": tips,
            "preparation_resources": resources,
        }
    )
    
    return JsonResponse({
        "id": prep.id,
        "role": role,
        "generated_questions": questions,
        "coding_problems": coding_problems,
        "tips_and_tricks": tips,
        "preparation_resources": resources,
        "created": created,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_interview_prep(request, prep_id):
    """Get interview preparation details"""
    try:
        prep = InterviewPreparation.objects.get(id=prep_id, user=request.user)
    except InterviewPreparation.DoesNotExist:
        return JsonResponse({"error": "Interview prep not found"}, status=404)
    
    return JsonResponse({
        "id": prep.id,
        "role": prep.role,
        "generated_questions": prep.generated_questions,
        "coding_problems": prep.coding_problems,
        "tips_and_tricks": prep.tips_and_tricks,
        "preparation_resources": prep.preparation_resources,
        "created_at": prep.created_at.isoformat(),
    })


# ============ RECRUITER ANALYTICS ENDPOINTS ============

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
@role_required(["recruiter", "admin"])
def get_recruiter_analytics(request):
    """Get recruiter analytics dashboard"""
    # Count statistics
    jobs_posted = JobPost.objects.filter(posted_by=request.user).count()
    applications = JobApplication.objects.filter(job__posted_by=request.user).count()
    hired = JobApplication.objects.filter(
        job__posted_by=request.user,
        status=JobApplication.Status.SHORTLISTED
    ).count()
    
    # Calculate average time to hire
    completed_apps = JobApplication.objects.filter(
        job__posted_by=request.user,
        status__in=[JobApplication.Status.SHORTLISTED, JobApplication.Status.REJECTED]
    )
    if completed_apps.exists():
        time_diffs = [(a.updated_at - a.created_at).days for a in completed_apps]
        avg_time = int(sum(time_diffs) / len(time_diffs))
    else:
        avg_time = 0
    
    # Engagement rate
    engagement_rate = (hired / max(applications, 1)) * 100
    
    # Top performing jobs
    top_jobs = JobPost.objects.filter(posted_by=request.user).annotate(
        app_count=Count("applications")
    ).order_by("-app_count")[:5]
    
    analytics, created = RecruiterAnalytics.objects.update_or_create(
        recruiter=request.user,
        defaults={
            "total_jobs_posted": jobs_posted,
            "total_applications": applications,
            "total_hired": hired,
            "average_time_to_hire": avg_time,
            "engagement_rate": engagement_rate,
            "top_performing_jobs": [
                {"id": j.id, "title": j.title, "applications": j.app_count}
                for j in top_jobs
            ],
        }
    )
    
    return JsonResponse({
        "total_jobs_posted": analytics.total_jobs_posted,
        "total_applications": analytics.total_applications,
        "total_hired": analytics.total_hired,
        "average_time_to_hire": analytics.average_time_to_hire,
        "engagement_rate": analytics.engagement_rate,
        "top_performing_jobs": analytics.top_performing_jobs,
        "updated_at": analytics.updated_at.isoformat(),
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
@role_required(["recruiter", "admin"])
def get_hiring_trends(request):
    """Get hiring trends and statistics"""
    days_back = int(request.GET.get("days", 30))
    start_date = timezone.now() - timedelta(days=days_back)
    
    # Applications trend
    apps_by_date = {}
    for i in range(days_back):
        date = (start_date + timedelta(days=i)).date()
        count = JobApplication.objects.filter(
            job__posted_by=request.user,
            created_at__date=date
        ).count()
        apps_by_date[str(date)] = count
    
    # Status distribution
    status_dist = JobApplication.objects.filter(
        job__posted_by=request.user
    ).values("status").annotate(count=Count("id"))
    
    return JsonResponse({
        "applications_trend": apps_by_date,
        "status_distribution": {item["status"]: item["count"] for item in status_dist},
    })
