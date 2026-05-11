import json
import re

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.decorators import jwt_required, role_required
from accounts.models import User

from .models import JobApplication, JobPost, NetworkMessage, Resume


TOKEN_PATTERN = re.compile(r"[a-zA-Z]{3,}")
SKILL_KEYWORDS = {
    "ai",
    "analytics",
    "aws",
    "communication",
    "css",
    "django",
    "docker",
    "excel",
    "fastapi",
    "figma",
    "git",
    "html",
    "java",
    "javascript",
    "leadership",
    "linux",
    "machine learning",
    "mongodb",
    "nextjs",
    "nlp",
    "node",
    "postgres",
    "product",
    "python",
    "react",
    "rest",
    "sql",
    "tailwind",
    "typescript",
}


def parse_json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        raise ValueError("Request body must be valid JSON.")


def job_payload(job):
    return {
        "id": job.pk,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "skills_required": job.skills_required,
        "employment_type": job.employment_type,
        "salary_range": job.salary_range,
        "is_active": job.is_active,
        "posted_by": {
            "id": job.posted_by_id,
            "email": job.posted_by.email,
            "role": job.posted_by.role,
        },
        "created_at": job.created_at.isoformat(),
    }


def user_summary(user):
    return {
        "id": user.pk,
        "email": user.email,
        "name": f"{user.first_name} {user.last_name}".strip() or user.email,
        "role": user.role,
        "headline": getattr(getattr(user, "profile", None), "headline", ""),
        "skills": getattr(getattr(user, "profile", None), "skills", []),
    }


def resume_payload(resume, request=None):
    if not resume:
        return None
    file_url = resume.file.url
    if request:
        file_url = request.build_absolute_uri(file_url)
    return {
        "id": resume.pk,
        "original_name": resume.original_name,
        "uploaded_at": resume.uploaded_at.isoformat(),
        "file_url": file_url,
        "extracted_skills": resume.extracted_skills,
        "analysis": analyze_resume_text(resume.extracted_text, resume.extracted_skills),
    }


def application_payload(application):
    return {
        "id": application.pk,
        "job": job_payload(application.job),
        "applicant": user_summary(application.applicant),
        "resume": resume_payload(application.resume),
        "cover_note": application.cover_note,
        "match_score": application.match_score,
        "status": application.status,
        "created_at": application.created_at.isoformat(),
        "updated_at": application.updated_at.isoformat(),
    }


def message_payload(message):
    return {
        "id": message.pk,
        "sender": user_summary(message.sender),
        "recipient": user_summary(message.recipient),
        "body": message.body,
        "is_read": message.is_read,
        "created_at": message.created_at.isoformat(),
    }


def tokenize(text):
    if not text:
        return set()
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


def extract_skills(text):
    lowered = f" {text.lower()} "
    tokens = tokenize(text)
    skills = set()
    for skill in SKILL_KEYWORDS:
        if " " in skill:
            if skill in lowered:
                skills.add(skill.title())
        elif skill in tokens:
            skills.add(skill.upper() if skill in {"ai", "aws", "css", "html", "nlp", "sql"} else skill.title())
    return sorted(skills)


def analyze_resume_text(text, skills):
    word_count = len(text.split()) if text else 0
    strengths = []
    gaps = []

    if len(skills) >= 5:
        strengths.append("Strong skill signal across multiple tools or domains.")
    elif skills:
        strengths.append("Clear initial skill signal detected from the resume.")
    else:
        gaps.append("Add a skills section with tools, languages, and project keywords.")

    if word_count >= 250:
        strengths.append("Resume has enough content for matching.")
    else:
        gaps.append("Add project outcomes, metrics, responsibilities, and technologies used.")

    if not any(skill.lower() in {"communication", "leadership", "product"} for skill in skills):
        gaps.append("Add collaboration, leadership, or product-impact examples.")

    return {
        "word_count": word_count,
        "detected_skills": skills,
        "strengths": strengths,
        "gaps": gaps,
    }


def score_job_for_resume(job, resume_tokens):
    job_text = f"{job.title} {job.description} {job.skills_required} {job.location}"
    job_tokens = tokenize(job_text)
    if not resume_tokens or not job_tokens:
        return 0
    overlap = resume_tokens.intersection(job_tokens)
    return len(overlap)


def score_job_for_user(job, user, resume=None):
    profile = getattr(user, "profile", None)
    profile_skills = " ".join(getattr(profile, "skills", []) or [])
    profile_text = f"{getattr(profile, 'headline', '')} {getattr(profile, 'bio', '')} {profile_skills}"
    resume_text = resume.extracted_text if resume else ""
    tokens = tokenize(f"{profile_text} {resume_text}")
    return score_job_for_resume(job, tokens)


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
def jobs_collection(request):
    if request.method == "GET":
        jobs = JobPost.objects.filter(is_active=True).select_related("posted_by")
        return JsonResponse({"jobs": [job_payload(job) for job in jobs]})

    if request.user.role not in (User.Role.RECRUITER, User.Role.ADMIN):
        return JsonResponse({"detail": "Only recruiters and admins can post jobs."}, status=403)

    try:
        data = parse_json(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    title = data.get("title", "").strip()
    company = data.get("company", "").strip() or request.user.company_name.strip() or "Company"
    location = data.get("location", "").strip()
    description = data.get("description", "").strip()

    if not title or not location or not description:
        return JsonResponse(
            {"detail": "title, location, and description are required."},
            status=400,
        )

    employment_type = data.get("employment_type", JobPost.EmploymentType.FULL_TIME)
    if employment_type not in JobPost.EmploymentType.values:
        employment_type = JobPost.EmploymentType.FULL_TIME

    job = JobPost.objects.create(
        posted_by=request.user,
        title=title,
        company=company,
        location=location,
        description=description,
        skills_required=data.get("skills_required", "").strip(),
        employment_type=employment_type,
        salary_range=data.get("salary_range", "").strip(),
    )
    return JsonResponse({"detail": "Job posted successfully.", "job": job_payload(job)}, status=201)


@csrf_exempt
@require_http_methods(["POST"])
@role_required(User.Role.STUDENT)
def apply_to_job(request, job_id):
    try:
        job = JobPost.objects.select_related("posted_by").get(pk=job_id, is_active=True)
    except JobPost.DoesNotExist:
        return JsonResponse({"detail": "Job not found."}, status=404)

    try:
        data = parse_json(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    resume = Resume.objects.filter(user=request.user).first()
    application, created = JobApplication.objects.get_or_create(
        job=job,
        applicant=request.user,
        defaults={
            "resume": resume,
            "cover_note": data.get("cover_note", "").strip(),
            "match_score": score_job_for_user(job, request.user, resume),
        },
    )
    if not created:
        return JsonResponse({"detail": "You already applied to this job.", "application": application_payload(application)}, status=409)

    return JsonResponse({"detail": "Application submitted.", "application": application_payload(application)}, status=201)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def applications_collection(request):
    if request.user.role == User.Role.STUDENT:
        applications = JobApplication.objects.filter(applicant=request.user).select_related("job", "job__posted_by", "applicant", "resume")
    elif request.user.role in (User.Role.RECRUITER, User.Role.ADMIN):
        applications = JobApplication.objects.filter(job__posted_by=request.user).select_related("job", "job__posted_by", "applicant", "resume")
    else:
        applications = JobApplication.objects.none()

    return JsonResponse({"applications": [application_payload(item) for item in applications]})


@csrf_exempt
@require_http_methods(["PATCH"])
@jwt_required
def application_detail(request, application_id):
    if request.user.role not in (User.Role.RECRUITER, User.Role.ADMIN):
        return JsonResponse({"detail": "Only recruiters and admins can manage application status."}, status=403)

    try:
        application = JobApplication.objects.select_related("job", "job__posted_by", "applicant", "resume").get(
            pk=application_id,
            job__posted_by=request.user,
        )
    except JobApplication.DoesNotExist:
        return JsonResponse({"detail": "Application not found."}, status=404)

    try:
        data = parse_json(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    status = data.get("status")
    if status not in JobApplication.Status.values:
        return JsonResponse({"detail": "Invalid application status."}, status=400)

    application.status = status
    application.save(update_fields=["status", "updated_at"])
    return JsonResponse({"detail": "Application updated.", "application": application_payload(application)})


@require_http_methods(["GET"])
@jwt_required
def my_jobs(request):
    if request.user.role not in (User.Role.RECRUITER, User.Role.ADMIN):
        return JsonResponse({"detail": "Only recruiters and admins can view posted jobs."}, status=403)

    jobs = JobPost.objects.filter(posted_by=request.user).select_related("posted_by")
    return JsonResponse({"jobs": [job_payload(job) for job in jobs]})


@csrf_exempt
@require_http_methods(["POST"])
@role_required(User.Role.STUDENT)
def upload_resume(request):
    uploaded = request.FILES.get("resume")
    if not uploaded:
        return JsonResponse({"detail": "resume file is required."}, status=400)

    preview_bytes = uploaded.read(250000)
    try:
        extracted_text = preview_bytes.decode("utf-8", errors="ignore")
    except Exception:
        extracted_text = ""
    uploaded.seek(0)
    extracted_skills = extract_skills(extracted_text)

    resume = Resume.objects.create(
        user=request.user,
        file=uploaded,
        original_name=uploaded.name,
        extracted_text=extracted_text,
        extracted_skills=extracted_skills,
    )

    return JsonResponse(
        {
            "detail": "Resume uploaded successfully.",
            "resume": resume_payload(resume, request),
        },
        status=201,
    )


@require_http_methods(["GET"])
@jwt_required
def latest_resume(request):
    resume = Resume.objects.filter(user=request.user).first()
    if not resume:
        return JsonResponse({"resume": None})

    return JsonResponse({"resume": resume_payload(resume, request)})


@require_http_methods(["GET"])
@role_required(User.Role.STUDENT)
def recommendations(request):
    jobs = JobPost.objects.filter(is_active=True).select_related("posted_by")
    resume = Resume.objects.filter(user=request.user).first()

    resume_tokens = tokenize(resume.extracted_text if resume else "")
    ranked = []
    for job in jobs:
        score = score_job_for_resume(job, resume_tokens)
        ranked.append((score, job))

    ranked.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)

    items = []
    for score, job in ranked[:8]:
        payload = job_payload(job)
        payload["match_score"] = score
        items.append(payload)

    return JsonResponse(
        {
            "recommendations": items,
            "strategy": "keyword-overlap",
            "resume_present": bool(resume),
        }
    )


@require_http_methods(["GET"])
@role_required(User.Role.STUDENT)
def career_guidance(request):
    profile = getattr(request.user, "profile", None)
    resume = Resume.objects.filter(user=request.user).first()
    skills = set(getattr(profile, "skills", []) or [])
    skills.update(resume.extracted_skills if resume else [])
    skill_list = sorted(skills)

    recommendations_payload = []
    for job in JobPost.objects.filter(is_active=True).select_related("posted_by")[:5]:
        score = score_job_for_user(job, request.user, resume)
        missing = sorted(set(extract_skills(job.skills_required)) - set(skill_list))
        recommendations_payload.append(
            {
                "job": job_payload(job),
                "match_score": score,
                "missing_skills": missing[:5],
            }
        )

    roadmap = [
        "Complete headline, location, portfolio links, and top skills.",
        "Upload a keyword-rich resume with projects, metrics, and tools.",
        "Apply to roles where your match score is strongest.",
        "Close gaps by building one focused project for missing in-demand skills.",
    ]
    if "React" in skill_list and "Django" in skill_list:
        roadmap.append("Package a full-stack AI hiring workflow project for your portfolio.")
    if not skill_list:
        roadmap.insert(0, "Add at least five skills to unlock better recommendations.")

    return JsonResponse(
        {
            "skills": skill_list,
            "roadmap": roadmap,
            "role_targets": recommendations_payload,
            "growth_insights": [
                "Your best matches come from overlap between resume keywords, profile skills, and job requirements.",
                "Recruiters see stronger signal when applications include a focused note and current resume.",
            ],
        }
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
def messages_collection(request):
    if request.method == "GET":
        messages = NetworkMessage.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).select_related("sender", "recipient")
        return JsonResponse({"messages": [message_payload(message) for message in messages]})

    try:
        data = parse_json(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    recipient_id = data.get("recipient_id")
    body = data.get("body", "").strip()
    if not recipient_id or not body:
        return JsonResponse({"detail": "recipient_id and body are required."}, status=400)

    try:
        recipient = get_user_model().objects.get(pk=recipient_id, is_active=True)
    except get_user_model().DoesNotExist:
        return JsonResponse({"detail": "Recipient not found."}, status=404)

    if recipient.pk == request.user.pk:
        return JsonResponse({"detail": "You cannot message yourself."}, status=400)

    message = NetworkMessage.objects.create(sender=request.user, recipient=recipient, body=body)
    return JsonResponse({"detail": "Message sent.", "message": message_payload(message)}, status=201)
