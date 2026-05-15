import json
import re
from pathlib import Path
from django.http import FileResponse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import F, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.decorators import jwt_required, role_required
from accounts.models import User

from .models import AutoApplyRun, JobApplication, JobPost, NetworkMessage, Resume
from .models import AIResumeAnalysis
from core.pdf_generator import PDFResumeGenerator
from core.ai_integrations import AIIntegrationService


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
        "views_count": job.views_count,
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
        "candidate_summary": application.candidate_summary,
        "portfolio_url": application.portfolio_url,
        "expected_salary": application.expected_salary,
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


def paginate_queryset(request, queryset, default_page_size=20, max_page_size=50):
    try:
        page = max(int(request.GET.get("page", "1")), 1)
        page_size = min(max(int(request.GET.get("page_size", str(default_page_size))), 1), max_page_size)
    except ValueError:
        page = 1
        page_size = default_page_size

    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    return queryset[start:end], {
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_next": end < total,
    }


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
def jobs_collection(request):
    if request.method == "GET":
        jobs = JobPost.objects.filter(is_active=True).select_related("posted_by")
        query = request.GET.get("q", "").strip()
        location = request.GET.get("location", "").strip()
        employment_type = request.GET.get("type", "").strip()

        if query:
            jobs = jobs.filter(
                Q(title__icontains=query)
                | Q(company__icontains=query)
                | Q(description__icontains=query)
                | Q(skills_required__icontains=query)
            )
        if location:
            jobs = jobs.filter(location__icontains=location)
        if employment_type in JobPost.EmploymentType.values:
            jobs = jobs.filter(employment_type=employment_type)

        page_jobs, pagination = paginate_queryset(request, jobs)
        return JsonResponse({"jobs": [job_payload(job) for job in page_jobs], "pagination": pagination})

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
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
@jwt_required
def job_detail(request, job_id):
    try:
        job = JobPost.objects.select_related("posted_by").get(pk=job_id)
    except JobPost.DoesNotExist:
        return JsonResponse({"detail": "Job not found."}, status=404)

    if request.user.role not in (User.Role.RECRUITER, User.Role.ADMIN):
        return JsonResponse({"detail": "Only recruiters and admins can manage jobs."}, status=403)

    if request.user.role != User.Role.ADMIN and job.posted_by_id != request.user.id:
        return JsonResponse({"detail": "You can only manage your own jobs."}, status=403)

    if request.method == "GET":
        JobPost.objects.filter(pk=job.pk).update(views_count=F("views_count") + 1)
        job.refresh_from_db(fields=["views_count"])
        return JsonResponse({"job": job_payload(job)})

    if request.method == "DELETE":
        job.is_active = False
        job.save(update_fields=["is_active", "updated_at"])
        return JsonResponse({"detail": "Job deleted.", "job": job_payload(job)})

    try:
        data = parse_json(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    title = data.get("title", job.title).strip()
    company = data.get("company", job.company).strip() or job.company
    location = data.get("location", job.location).strip()
    description = data.get("description", job.description).strip()

    if not title or not location or not description:
        return JsonResponse({"detail": "title, location, and description are required."}, status=400)

    employment_type = data.get("employment_type", job.employment_type)
    if employment_type not in JobPost.EmploymentType.values:
        employment_type = job.employment_type

    job.title = title
    job.company = company
    job.location = location
    job.description = description
    job.skills_required = data.get("skills_required", job.skills_required).strip()
    job.employment_type = employment_type
    job.salary_range = data.get("salary_range", job.salary_range).strip()
    job.is_active = data.get("is_active", job.is_active)
    job.save(
        update_fields=[
            "title",
            "company",
            "location",
            "description",
            "skills_required",
            "employment_type",
            "salary_range",
            "is_active",
            "updated_at",
        ]
    )
    return JsonResponse({"detail": "Job updated successfully.", "job": job_payload(job)})


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
            "candidate_summary": data.get("candidate_summary", "").strip(),
            "portfolio_url": data.get("portfolio_url", "").strip(),
            "expected_salary": data.get("expected_salary", "").strip(),
            "match_score": score_job_for_user(job, request.user, resume),
        },
    )
    if not created:
        return JsonResponse({"detail": "You already applied to this job.", "application": application_payload(application)}, status=409)

    return JsonResponse({"detail": "Application submitted.", "application": application_payload(application)}, status=201)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
@role_required(User.Role.STUDENT)
def auto_apply_jobs(request):
    try:
        data = parse_json(request)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    threshold = int(data.get("threshold") or 80)
    max_applications = int(data.get("limit") or 10)
    resume = Resume.objects.filter(user=request.user).first()
    if not resume:
        return JsonResponse({"detail": "Upload a resume before auto applying."}, status=400)

    from .ai_views import calculate_ai_match

    applied_jobs = []
    skipped_jobs = []
    candidate_jobs = JobPost.objects.filter(is_active=True).select_related("posted_by")[:80]
    for job in candidate_jobs:
        if len(applied_jobs) >= max_applications:
            break

        score = score_job_for_user(job, request.user, resume)
        if score < threshold:
            skipped_jobs.append({"job_id": job.id, "title": job.title, "match_score": score})
            continue

        application, created = JobApplication.objects.get_or_create(
            job=job,
            applicant=request.user,
            defaults={
                "resume": resume,
                "cover_note": data.get("cover_note", "").strip() or "Applied automatically by AI from the resume match flow.",
                "candidate_summary": data.get("candidate_summary", "").strip(),
                "portfolio_url": data.get("portfolio_url", "").strip(),
                "expected_salary": data.get("expected_salary", "").strip(),
                "match_score": score,
            },
        )
        if created:
            applied_jobs.append({"job_id": job.id, "title": job.title, "match_score": score, "application_id": application.id})
        else:
            skipped_jobs.append({"job_id": job.id, "title": job.title, "match_score": score, "reason": "already_applied"})

    AutoApplyRun.objects.create(
        user=request.user,
        resume=resume,
        threshold=threshold,
        applied_jobs=applied_jobs,
        skipped_jobs=skipped_jobs,
    )

    return JsonResponse({
        "detail": f"Auto applied to {len(applied_jobs)} jobs.",
        "applied_jobs": applied_jobs,
        "skipped_jobs": skipped_jobs[:20],
        "threshold": threshold,
    })


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

    page_applications, pagination = paginate_queryset(request, applications)
    return JsonResponse({"applications": [application_payload(item) for item in page_applications], "pagination": pagination})


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
    page_jobs, pagination = paginate_queryset(request, jobs)
    return JsonResponse({"jobs": [job_payload(job) for job in page_jobs], "pagination": pagination})


@csrf_exempt
@require_http_methods(["POST"])
@role_required(User.Role.STUDENT)
def upload_resume(request):
    uploaded = request.FILES.get("resume")
    if not uploaded:
        return JsonResponse({"detail": "resume file is required."}, status=400)

    max_size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE
    extension = Path(uploaded.name).suffix.lower()
    allowed_extensions = getattr(settings, "ALLOWED_RESUME_EXTENSIONS", {".pdf", ".doc", ".docx", ".txt"})

    if extension not in allowed_extensions:
        return JsonResponse({"detail": "Only PDF, DOC, DOCX, and TXT resumes are allowed."}, status=400)

    if uploaded.size > max_size:
        size_mb = max_size // (1024 * 1024)
        return JsonResponse({"detail": f"Resume file must be {size_mb}MB or smaller."}, status=400)

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
@jwt_required
def download_resume_pdf(request, resume_id):
    """Download resume as PDF"""
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
    except Resume.DoesNotExist:
        return JsonResponse({"error": "Resume not found"}, status=404)
    
    try:
        # Get resume data from template if available
        resume_template = resume.user.resume_template if hasattr(resume.user, 'resume_template') else None
        
        if resume_template:
            resume_data = {
                "full_name": resume_template.full_name,
                "email": resume_template.email,
                "phone": resume_template.phone,
                "location": resume_template.location,
                "professional_summary": resume_template.professional_summary,
                "experience": resume_template.experience,
                "education": resume_template.education,
                "skills": resume_template.skills,
                "certifications": resume_template.certifications,
                "projects": resume_template.projects,
                "headline": request.user.profile.headline if hasattr(request.user, 'profile') else "",
            }
        else:
            # Create basic resume data from extracted information
            resume_data = {
                "full_name": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
                "email": request.user.email,
                "phone": "",
                "location": request.user.profile.location if hasattr(request.user, 'profile') else "",
                "professional_summary": request.user.profile.bio if hasattr(request.user, 'profile') else "",
                "experience": [],
                "education": [],
                "skills": resume.extracted_skills or [],
                "certifications": [],
                "projects": [],
                "headline": request.user.profile.headline if hasattr(request.user, 'profile') else "",
            }
        
        # Generate PDF
        pdf_buffer = PDFResumeGenerator.generate_resume_pdf(resume_data)
        
        # Return as download
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Resume_{request.user.email}.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def download_resume_pdf_from_template(request):
    """Generate and download PDF from resume template data"""
    try:
        data = parse_json(request)
        
        resume_data = {
            "full_name": data.get("full_name", f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email),
            "email": data.get("email", request.user.email),
            "phone": data.get("phone", ""),
            "location": data.get("location", ""),
            "professional_summary": data.get("professional_summary", ""),
            "experience": data.get("experience", []),
            "education": data.get("education", []),
            "skills": data.get("skills", []),
            "certifications": data.get("certifications", []),
            "projects": data.get("projects", []),
            "headline": data.get("headline", ""),
        }
        
        # Generate PDF
        pdf_buffer = PDFResumeGenerator.generate_resume_pdf(resume_data)
        
        # Return as download
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Resume_{request.user.email}.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


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
    profile_strength = int((
        bool(getattr(profile, "headline", ""))
        + bool(getattr(profile, "location", ""))
        + bool(skill_list)
        + bool(getattr(profile, "bio", ""))
        + bool(getattr(profile, "github_url", "") or getattr(profile, "linkedin_url", ""))
        + bool(resume)
    ) / 6 * 100)

    resume_analysis = AIResumeAnalysis.objects.filter(resume=resume).first() if resume else None
    resume_rating = resume_analysis.overall_rating if resume_analysis else min(95, 40 + len(skill_list) * 5 + (10 if resume else 0))

    recommendations_payload = []
    active_jobs = list(JobPost.objects.filter(is_active=True).select_related("posted_by")[:8])
    for job in active_jobs[:5]:
        score = score_job_for_user(job, request.user, resume)
        missing = sorted(set(extract_skills(job.skills_required)) - set(skill_list))
        recommendations_payload.append(
            {
                "job": job_payload(job),
                "match_score": score,
                "missing_skills": missing[:5],
            }
        )

    job_alerts = []
    for job in active_jobs[:3]:
        score = score_job_for_user(job, request.user, resume)
        if score < 3:
            continue
        job_alerts.append(
            {
                "job": job_payload(job),
                "match_score": score,
                "message": f"You are {score}% match for {job.title} at {job.company}.",
            }
        )

    weekly_tips = [
        "Apply to your highest-match roles first to improve shortlist chances.",
        "Use project outcomes and measurable impact in your resume summary.",
    ]
    if skill_list:
        weekly_tips.insert(0, f"Double down on {skill_list[0]} with a small portfolio project or certification.")
    if not resume:
        weekly_tips.insert(0, "Upload a resume to unlock AI rating, match alerts, and stronger job recommendations.")

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
            "recommended_jobs": recommendations_payload,
            "growth_insights": [
                "Your best matches come from overlap between resume keywords, profile skills, and job requirements.",
                "Recruiters see stronger signal when applications include a focused note and current resume.",
            ],
            "profile_strength": profile_strength,
            "resume_rating": resume_rating,
            "weekly_tips": weekly_tips,
            "job_alerts": job_alerts,
            "next_best_job": job_alerts[0] if job_alerts else None,
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
