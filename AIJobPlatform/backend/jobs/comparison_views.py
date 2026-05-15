from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.parsers import JSONParser

from accounts.decorators import jwt_required
from .comparison_service import AIComparisonService
from .models import JobPost, Resume, ResumeJobComparison, SkillGapAnalysis
from .serializers import (
    AIMatchInputSerializer,
    CompareInputSerializer,
    ResumeJobComparisonSerializer,
    ResumeSerializer,
    SalaryPredictInputSerializer,
    SkillGapInputSerializer,
)


MAX_RESUME_UPLOAD_BYTES = 5 * 1024 * 1024


def parse_body(request):
    try:
        return JSONParser().parse(request)
    except Exception:
        return {}


def serializer_errors(serializer):
    return {"errors": serializer.errors}


def extract_text_from_upload(upload: UploadedFile) -> str:
    suffix = Path(upload.name).suffix.lower()
    upload.seek(0)
    if suffix == ".pdf":
        try:
            import PyPDF2

            reader = PyPDF2.PdfReader(upload)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValueError(f"Unable to parse PDF: {exc}")
    if suffix == ".docx":
        try:
            from docx import Document

            document = Document(upload)
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception as exc:
            raise ValueError(f"Unable to parse DOCX: {exc}")
    if suffix == ".txt":
        return upload.read().decode("utf-8", errors="ignore")
    raise ValueError("Unsupported resume file type.")


def validate_resume_file(upload: UploadedFile):
    suffix = Path(upload.name).suffix.lower()
    allowed = getattr(settings, "ALLOWED_RESUME_EXTENSIONS", {".pdf", ".docx", ".txt"})
    if suffix not in allowed:
        raise ValueError(f"Unsupported file type. Allowed: {', '.join(sorted(allowed))}")
    if upload.size > MAX_RESUME_UPLOAD_BYTES:
        raise ValueError("Resume is too large. Maximum upload size is 5 MB.")
    if upload.content_type and upload.content_type not in {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/msword",
    }:
        raise ValueError("Invalid resume content type.")


def run_comparison(resume, job):
    service = AIComparisonService()
    result = service.compare(resume, job)
    resume.parsed_skills = result["resume_data"]["skills"]
    resume.extracted_skills = result["resume_data"]["skills"]
    resume.experience_years = result["resume_data"]["experience_years"]
    resume.education = result["resume_data"]["education"]
    resume.certifications = result["resume_data"]["certifications"]
    resume.ats_score = result["ats_score"]
    resume.ai_suggestions = result["improvement_suggestions"]
    resume.save(
        update_fields=[
            "parsed_skills",
            "extracted_skills",
            "experience_years",
            "education",
            "certifications",
            "ats_score",
            "ai_suggestions",
        ]
    )
    comparison, _ = ResumeJobComparison.objects.update_or_create(
        resume=resume,
        job=job,
        defaults={
            "match_percentage": result["match_percentage"],
            "semantic_similarity": result["semantic_similarity"],
            "tfidf_similarity": result["tfidf_similarity"],
            "skill_match": result["skill_match"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
            "missing_certifications": result["missing_certifications"],
            "experience_score": result["experience_score"],
            "ats_score": result["ats_score"],
            "salary_prediction": result["salary_prediction"],
            "improvement_suggestions": result["improvement_suggestions"],
            "career_recommendations": result["career_recommendations"],
            "keyword_analysis": result["keyword_analysis"],
            "heatmap": result["heatmap"],
            "status": "completed",
            "error_message": "",
        },
    )
    return comparison


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def upload_resume_api(request):
    upload = request.FILES.get("file") or request.FILES.get("resume")
    if not upload:
        return JsonResponse({"error": "file is required."}, status=400)
    try:
        validate_resume_file(upload)
        text = extract_text_from_upload(upload)
        service = AIComparisonService()
        parsed = service.parse_resume(text)
        upload.seek(0)
        resume = Resume.objects.create(
            user=request.user,
            file=upload,
            original_name=upload.name,
            extracted_text=text,
            extracted_skills=parsed["skills"],
            parsed_skills=parsed["skills"],
            experience_years=parsed["experience_years"],
            education=parsed["education"],
            certifications=parsed["certifications"],
            ats_score=parsed["ats_score"],
            ai_suggestions=[],
        )
        return JsonResponse(ResumeSerializer(resume).data, status=201)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        return JsonResponse({"error": "Resume upload failed."}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def compare_api(request):
    serializer = CompareInputSerializer(data=parse_body(request))
    if not serializer.is_valid():
        return JsonResponse(serializer_errors(serializer), status=400)

    resume = get_object_or_404(Resume, id=serializer.validated_data["resume_id"], user=request.user)
    job = get_object_or_404(JobPost, id=serializer.validated_data["job_id"])

    if serializer.validated_data.get("async_process"):
        comparison, _ = ResumeJobComparison.objects.update_or_create(
            resume=resume,
            job=job,
            defaults={"status": "queued", "error_message": ""},
        )
        try:
            from .tasks import process_resume_job_comparison

            task = process_resume_job_comparison.delay(comparison.id)
            return JsonResponse({"comparison_id": comparison.id, "task_id": task.id, "status": "queued"}, status=202)
        except Exception:
            comparison = run_comparison(resume, job)
            return JsonResponse(ResumeJobComparisonSerializer(comparison).data)

    comparison = run_comparison(resume, job)
    return JsonResponse(ResumeJobComparisonSerializer(comparison).data)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def ai_match_api(request):
    serializer = AIMatchInputSerializer(data=parse_body(request))
    if not serializer.is_valid():
        return JsonResponse(serializer_errors(serializer), status=400)
    resume = get_object_or_404(Resume, id=serializer.validated_data["resume_id"], user=request.user)
    job = get_object_or_404(JobPost, id=serializer.validated_data["job_id"])
    comparison = run_comparison(resume, job)
    return JsonResponse(ResumeJobComparisonSerializer(comparison).data)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def skill_gap_api(request):
    serializer = SkillGapInputSerializer(data=parse_body(request))
    if not serializer.is_valid():
        return JsonResponse(serializer_errors(serializer), status=400)

    service = AIComparisonService()
    resume = None
    if serializer.validated_data.get("resume_id"):
        resume = get_object_or_404(Resume, id=serializer.validated_data["resume_id"], user=request.user)
        current_skills = resume.parsed_skills or resume.extracted_skills
    else:
        current_skills = getattr(getattr(request.user, "profile", None), "skills", []) or []

    if serializer.validated_data.get("job_id"):
        job = get_object_or_404(JobPost, id=serializer.validated_data["job_id"])
        target_skills = service.parse_job(job)["skills"]
        target_role = job.title
    else:
        target_role = serializer.validated_data.get("target_role") or "target role"
        target_skills = service.extract_skills(target_role)

    gap = service.match_skills(current_skills, target_skills)
    learning_paths = [
        {
            "skill": skill,
            "resource": f"Build one portfolio project using {skill.title()}",
            "estimated_weeks": 4,
            "impact": f"Can increase match by {min(23, 8 + index * 3)}%",
        }
        for index, skill in enumerate(gap["missing_skills"][:8])
    ]
    analysis, _ = SkillGapAnalysis.objects.update_or_create(
        user=request.user,
        defaults={
            "current_skills": current_skills,
            "target_role": target_role,
            "missing_skills": gap["missing_skills"],
            "learning_paths": learning_paths,
            "proficiency_levels": {skill: "recommended" for skill in gap["missing_skills"]},
        },
    )
    payload = {
        "id": analysis.id,
        "resume_id": resume.id if resume else None,
        "target_role": target_role,
        "current_skills": current_skills,
        "missing_skills": gap["missing_skills"],
        "matched_skills": gap["matched_skills"],
        "learning_paths": learning_paths,
    }
    return JsonResponse(payload)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def salary_predict_api(request):
    serializer = SalaryPredictInputSerializer(data=parse_body(request))
    if not serializer.is_valid():
        return JsonResponse(serializer_errors(serializer), status=400)

    service = AIComparisonService()
    resume_data = {
        "skills": serializer.validated_data.get("skills", []),
        "experience_years": serializer.validated_data.get("experience_years", 0),
    }
    if serializer.validated_data.get("resume_id"):
        resume = get_object_or_404(Resume, id=serializer.validated_data["resume_id"], user=request.user)
        resume_data = service.parse_resume(resume.extracted_text)

    if serializer.validated_data.get("job_id"):
        job = get_object_or_404(JobPost, id=serializer.validated_data["job_id"])
        skill_match = service.match_skills(resume_data["skills"], service.parse_job(job)["skills"])["match_percentage"]
        salary = service.estimate_salary(job, resume_data, skill_match)
        role = job.title
    else:
        class SalaryOnlyJob:
            salary_min = None
            salary_max = None
            salary_range = ""

        salary = service.estimate_salary(SalaryOnlyJob(), resume_data, 70)
        role = serializer.validated_data.get("role") or "Software Engineer"

    return JsonResponse({
        "role": role,
        "salary_prediction": salary,
        "currency": "INR",
        "confidence": "medium",
        "factors": {
            "experience_years": resume_data.get("experience_years", 0),
            "skills_count": len(resume_data.get("skills", [])),
        },
    })
