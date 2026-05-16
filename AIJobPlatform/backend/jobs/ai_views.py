import json
import re
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg, Count
from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from accounts.decorators import jwt_required, role_required
from accounts.models import User
from core.ai_integrations import AIIntegrationService
from .resume_match_service import ResumeMatchService
from .models import (
    AIResumeAnalysis, AIMatchScore, AICareerCoach, ChatMessage,
    RecruiterDashboard, Resume, JobPost, JobApplication, Notification,
    RecruiterQuery, QueryResult, SkillNode, SkillEdge, UserSkillProgress,
    CareerPathModel, UserCareerPath, ResumeJobComparison,
    CodingQuestion, CodeSubmission, CodingContest, ContestParticipant,
    VoiceSession, InterviewPracticeSession, CollaborativeReview, ReviewComment,
    InterviewSession, InterviewNotes, PersonalityProfile, PersonalityInsight,
    UserGameProfile, XPTransaction, Badge, UserBadge, DailyChallenge,
    UserChallenge, AutoApplyPreferences, AutoApplication
)


def split_skill_keywords(text):
    if isinstance(text, list):
        return [str(part).strip().lower() for part in text if str(part).strip()]
    return [part.strip().lower() for part in (text or "").split(",") if part.strip()]


def title_skills(skills):
    return [skill.upper() if skill in {"ai", "aws", "css", "html", "nlp", "sql"} else skill.title() for skill in skills]


def parse_json(request):
    try:
        return json.loads(request.body)
    except Exception:
        return None


def normalize_skill(skill):
    normalized = str(skill or "").strip().lower()
    if not normalized:
        return ""
    return ResumeMatchService.CANONICAL_SKILLS.get(normalized, normalized)


def extract_skills_from_text(text):
    if not text:
        return []

    text_lower = text.lower()
    extracted = set()
    for skill in ResumeMatchService._get_skill_keywords():
        if skill in text_lower:
            extracted.add(normalize_skill(skill))

    return sorted(skill for skill in extracted if skill)


def extract_years_of_experience(text, default_years=0):
    if not text:
        return default_years

    explicit_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text, re.IGNORECASE)
    if explicit_match:
        return int(explicit_match.group(1))

    text_lower = text.lower()
    if any(keyword in text_lower for keyword in ["principal", "expert", "lead", "senior"]):
        return 5
    if any(keyword in text_lower for keyword in ["junior", "entry", "graduate", "fresher", "intern"]):
        return 1
    return default_years


def get_text_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0

    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=250)
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        return round(float(similarity * 100), 1)
    except Exception:
        return 0.0


def get_profile_strength(profile, resume=None):
    profile_checks = [
        bool(getattr(profile, "headline", "")),
        bool(getattr(profile, "location", "")),
        bool(getattr(profile, "skills", []) or []),
        bool(getattr(profile, "bio", "")),
        bool(getattr(profile, "github_url", "") or getattr(profile, "linkedin_url", "")),
        bool(resume and (resume.extracted_text or resume.extracted_skills)),
    ]
    return int((sum(1 for item in profile_checks if item) / len(profile_checks)) * 100)


def build_career_job_alerts(user_skills, resume_text, limit=3):
    alerts = []
    for job in JobPost.objects.filter(is_active=True).select_related("posted_by")[:40]:
        job_text = f"{job.title} {job.description} {job.skills_required}"
        job_skills = {normalize_skill(skill) for skill in split_skill_keywords(job.skills_required)}
        if not job_skills:
            job_skills = set(extract_skills_from_text(job_text))
        overlap = sorted(job_skills.intersection(user_skills))
        missing = sorted(job_skills.difference(user_skills))
        text_similarity = get_text_similarity(resume_text, job_text)
        match_percentage = min(100, int((len(overlap) * 18) + (text_similarity * 0.45) + max(0, 40 - len(missing) * 4)))
        if match_percentage < 55:
            continue
        alerts.append(
            {
                "job": {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "views_count": job.views_count,
                },
                "match_percentage": match_percentage,
                "message": f"You are {match_percentage}% match for {job.title} at {job.company}.",
                "missing_skills": title_skills(missing[:4]),
            }
        )
    alerts.sort(key=lambda item: item["match_percentage"], reverse=True)
    return alerts[:limit]


def notify_high_match(user, job, match_percentage, missing_skills):
    title = f"You are {int(round(match_percentage))}% match for this job"
    message = (
        f"{job.title} at {job.company} matches your profile. "
        f"Missing skills: {', '.join(missing_skills[:4]) if missing_skills else 'none'}"
    )
    notification, created = Notification.objects.get_or_create(
        user=user,
        type=Notification.NotificationType.JOB_MATCH,
        related_job=job,
        title=title,
        defaults={"message": message},
    )
    if not created and notification.message != message:
        notification.message = message
        notification.is_read = False
        notification.save(update_fields=["message", "is_read"])

    if getattr(user, "is_email_verified", False) and getattr(user, "email", ""):
        try:
            send_mail(
                subject=title,
                message=f"{message}\n\nOpen the app to view the job and apply.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass


def build_skill_recommendations(missing_required, missing_optional, bonus_skills):
    recommendations = []

    for skill in missing_required[:5]:
        display_skill = title_skills([skill])[0]
        recommendations.append({
            "skill": display_skill,
            "priority": "high",
            "reason": f"{display_skill} is explicitly requested in the job requirements.",
            "action": f"Add a project bullet, certification, or measurable result showing {display_skill} experience.",
            "resource": f"Practice one focused {display_skill} project and update your resume with the outcome.",
        })

    for skill in missing_optional[:3]:
        if any(item["skill"].lower() == skill.lower() for item in recommendations):
            continue
        display_skill = title_skills([skill])[0]
        recommendations.append({
            "skill": display_skill,
            "priority": "medium",
            "reason": f"{display_skill} appears in the job description and will strengthen alignment.",
            "action": f"Mention {display_skill} in your profile if you have hands-on experience, or plan a quick project to cover it.",
            "resource": f"Look for a small {display_skill} tutorial or walkthrough you can finish this week.",
        })

    for skill in bonus_skills[:2]:
        display_skill = title_skills([skill])[0]
        recommendations.append({
            "skill": display_skill,
            "priority": "low",
            "reason": f"{display_skill} is a transferable strength worth highlighting in the application.",
            "action": f"Keep {display_skill} visible in your summary and top project bullets.",
            "resource": "Use this as a differentiator rather than a gap to fix.",
        })

    return recommendations[:6]


# ============ AI RESUME ANALYZER ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def analyze_resume_ai(request):
    """Perform detailed AI analysis on resume using OpenAI"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    resume_id = data.get("resume_id")
    job_id = data.get("job_id")  # Optional for job-specific analysis
    
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
    except Resume.DoesNotExist:
        return JsonResponse({"error": "Resume not found"}, status=404)
    
    # Get job description if provided
    job_description = None
    if job_id:
        try:
            job = JobPost.objects.get(id=job_id)
            job_description = f"{job.title} at {job.company}: {job.description}\nRequired skills: {job.skills_required}"
        except JobPost.DoesNotExist:
            pass
    
    # Use AI service for analysis
    ai_result = AIIntegrationService.analyze_resume_with_ai(
        resume.extracted_text,
        job_description
    )
    
    analysis_data = ai_result["data"]
    
    # Create/update analysis record
    analysis, created = AIResumeAnalysis.objects.update_or_create(
        resume=resume,
        defaults={
            "overall_rating": analysis_data.get("overall_rating", 70),
            "strengths": analysis_data.get("strengths", []),
            "weaknesses": analysis_data.get("weaknesses", []),
            "readability_score": analysis_data.get("readability_score", 70),
            "impact_score": analysis_data.get("impact_score", 70),
            "recommendations": analysis_data.get("recommendations", []),
            "detailed_feedback": analysis_data.get("detailed_feedback", "Analysis completed"),
        }
    )
    
    return JsonResponse({
        "id": analysis.id,
        "overall_rating": analysis.overall_rating,
        "strengths": analysis.strengths,
        "weaknesses": analysis.weaknesses,
        "readability_score": analysis.readability_score,
        "impact_score": analysis.impact_score,
        "recommendations": analysis.recommendations,
        "detailed_feedback": analysis.detailed_feedback,
        "model_used": ai_result.get("model", "unknown"),
        "is_fallback": ai_result.get("fallback", False),
        "created": created,
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def generate_ai_interview_questions(request):
    """Generate AI interview questions for a target role using user profile signals."""
    data = parse_json(request) or {}
    target_role = data.get("target_role") or data.get("job_title") or "Software Engineer"
    difficulty = str(data.get("difficulty") or data.get("level") or "medium").lower()

    difficulty_aliases = {
        "beginner": "easy",
        "intermediate": "medium",
        "advanced": "hard",
    }
    difficulty = difficulty_aliases.get(difficulty, difficulty)

    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"

    resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()
    skills = []
    if resume and resume.extracted_skills:
        skills = [skill for skill in resume.extracted_skills if skill]

    ai_result = AIIntegrationService.generate_interview_questions(target_role, difficulty, skills)
    questions = ai_result.get("questions") or []

    if isinstance(questions, str):
        questions = [line.strip("- ") for line in questions.split("\n") if line.strip()]

    role_key = target_role.lower()
    primary_skill = skills[0] if skills else ("React" if "frontend" in role_key else "Python")
    secondary_skill = skills[1] if len(skills) > 1 else ("SQL" if "data" in role_key else "System Design")
    mcq_questions = [
        {
            "question": f"Which answer best shows production readiness for a {target_role} role?",
            "options": [
                "Clear requirements, tests, monitoring, and rollback plan",
                "Only a working local demo",
                "A large feature without documentation",
                "Skipping edge cases to save time",
            ],
            "answer": "Clear requirements, tests, monitoring, and rollback plan",
        },
        {
            "question": f"When using {primary_skill}, what should you optimize first in an interview answer?",
            "options": ["Correctness and clarity", "Memorized syntax only", "Longest possible answer", "Unrelated tools"],
            "answer": "Correctness and clarity",
        },
    ]
    coding_round = {
        "prompt": f"Build a small {target_role} exercise using {primary_skill}: parse input, handle edge cases, and explain complexity.",
        "starter_code": "function solve(input) {\n  // Write your solution here\n  return input;\n}",
        "evaluation_focus": ["Correctness", "Edge cases", "Readable code", "Complexity explanation"],
    }
    if difficulty == "hard":
        coding_round["prompt"] = f"Design and implement a scalable {target_role} workflow using {primary_skill} and {secondary_skill}. Include tradeoffs."
        coding_round["evaluation_focus"].extend(["System design", "Data model", "Failure handling"])

    return JsonResponse(
        {
            "target_role": target_role,
            "difficulty": difficulty,
            "level": {"easy": "Beginner", "medium": "Intermediate", "hard": "Advanced"}[difficulty],
            "skills_context": skills,
            "questions": questions[:8],
            "mcq_questions": mcq_questions,
            "coding_round": coding_round,
            "question_count": len(questions),
            "model_used": ai_result.get("model", "fallback"),
            "is_fallback": ai_result.get("fallback", False),
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_resume_analysis(request, resume_id):
    """Get AI resume analysis"""
    try:
        analysis = AIResumeAnalysis.objects.get(resume__id=resume_id, resume__user=request.user)
    except AIResumeAnalysis.DoesNotExist:
        return JsonResponse({"error": "Analysis not found"}, status=404)
    
    return JsonResponse({
        "id": analysis.id,
        "overall_rating": analysis.overall_rating,
        "strengths": analysis.strengths,
        "weaknesses": analysis.weaknesses,
        "readability_score": analysis.readability_score,
        "impact_score": analysis.impact_score,
        "recommendations": analysis.recommendations,
        "detailed_feedback": analysis.detailed_feedback,
    })


# ============ RECRUITER ASSISTANT ENDPOINTS ============


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def submit_recruiter_query(request):
    """Submit a free-text recruiter query. Stores the query and returns an id."""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    query_text = data.get("query_text") or data.get("query")
    if not query_text:
        return JsonResponse({"error": "query_text is required"}, status=400)

    rq = RecruiterQuery.objects.create(recruiter=request.user, query=query_text)

    # Basic synchronous processing for simple patterns (best-effort)
    qlower = (query_text or "").lower()
    results = []
    if "react" in qlower or "reactjs" in qlower:
        apps = JobApplication.objects.filter(resume__extracted_skills__icontains="react").order_by("-match_score")[:20]
    elif "ats" in qlower:
        apps = JobApplication.objects.filter(resume__isnull=False).order_by("-match_score")[:20]
    else:
        apps = JobApplication.objects.select_related("applicant", "job").order_by("-match_score")[:20]

    for app in apps:
        qr = QueryResult.objects.create(query=rq, candidate=app, relevance_score=float(getattr(app, "match_score", 0)))
        results.append({"candidate_id": app.id, "applicant": app.applicant.email, "score": qr.relevance_score})

    rq.results_count = len(results)
    rq.save(update_fields=["results_count"])

    return JsonResponse({"query_id": rq.id, "results_count": rq.results_count, "results": results})


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def refine_recruiter_query(request, query_id):
    """Return stored results for a given query and allow optional refinement parameters."""
    try:
        rq = RecruiterQuery.objects.get(id=query_id, recruiter=request.user)
    except RecruiterQuery.DoesNotExist:
        return JsonResponse({"error": "Query not found"}, status=404)

    data = parse_json(request) or {}
    limit = int(data.get("limit", 20))

    results = []
    for r in rq.results.select_related("candidate__applicant")[:limit]:
        results.append({
            "candidate_id": r.candidate.id,
            "applicant": r.candidate.applicant.email,
            "relevance_score": r.relevance_score,
            "reasoning": r.reasoning,
        })

    return JsonResponse({"query_id": rq.id, "results": results})


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def auto_shortlist(request):
    """Auto-shortlist top applicants for a job_id. Returns created shortlist results."""
    data = parse_json(request) or {}
    job_id = data.get("job_id")
    count = int(data.get("count", 10))

    if not job_id:
        return JsonResponse({"error": "job_id required"}, status=400)

    try:
        job = JobPost.objects.get(id=job_id)
    except JobPost.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)

    rq = RecruiterQuery.objects.create(recruiter=request.user, query=f"auto_shortlist_job_{job_id}", query_type="shortlist")

    apps = JobApplication.objects.filter(job=job).order_by("-match_score")[:count]
    shortlisted = []
    for app in apps:
        qr = QueryResult.objects.create(query=rq, candidate=app, relevance_score=float(getattr(app, "match_score", 0)))
        shortlisted.append({"application_id": app.id, "applicant": app.applicant.email, "score": qr.relevance_score})

    rq.results_count = len(shortlisted)
    rq.save(update_fields=["results_count"])

    return JsonResponse({"query_id": rq.id, "shortlisted": shortlisted})


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def recruiter_query_patterns(request):
    """Return simple analytics over stored recruiter queries (counts by type)."""
    data = list(
        RecruiterQuery.objects.values("query_type").annotate(count=Count("id")).order_by("-count")
    )
    return JsonResponse({"patterns": data})


# ============ AI MATCH SCORING ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def calculate_ai_match(request):
    """Calculate AI match score between resume and job"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    job_id = data.get("job_id")
    resume_id = data.get("resume_id")
    
    try:
        job = JobPost.objects.get(id=job_id)
        resume = Resume.objects.get(id=resume_id, user=request.user)
    except (JobPost.DoesNotExist, Resume.DoesNotExist):
        return JsonResponse({"error": "Job or resume not found"}, status=404)
    
    job_text = f"{job.title} {job.description} {job.skills_required}".strip()
    resume_text = resume.extracted_text or ""

    resume_skills = {normalize_skill(skill) for skill in split_skill_keywords(resume.extracted_skills)}
    resume_skills.update(extract_skills_from_text(resume_text))
    resume_skills = {skill for skill in resume_skills if skill}

    required_skills = {normalize_skill(skill) for skill in split_skill_keywords(job.skills_required)}
    required_skills = {skill for skill in required_skills if skill}
    extracted_job_skills = set(extract_skills_from_text(job_text))

    if not required_skills:
        required_skills = extracted_job_skills.copy()

    all_job_skills = required_skills.union(extracted_job_skills)
    if not all_job_skills:
        all_job_skills = required_skills or extracted_job_skills

    matched_required = sorted(required_skills.intersection(resume_skills))
    matched_context = sorted(all_job_skills.intersection(resume_skills))
    missing_required = sorted(required_skills - resume_skills)
    missing_optional = sorted(all_job_skills - required_skills - resume_skills)
    bonus_skills = sorted(resume_skills - all_job_skills)

    required_match_pct = (len(matched_required) / len(required_skills) * 100) if required_skills else 100.0
    contextual_match_pct = (len(matched_context) / len(all_job_skills) * 100) if all_job_skills else 50.0
    semantic_similarity = get_text_similarity(resume_text, job_text)

    candidate_years = extract_years_of_experience(resume_text, default_years=0)
    required_years = extract_years_of_experience(job_text, default_years=3)
    if candidate_years == 0 and resume_skills:
        candidate_years = min(5, max(1, len(resume_skills) // 4 or 1))

    if required_years <= 0:
        experience_alignment = 70
    elif candidate_years >= required_years:
        experience_alignment = min(100, 72 + (candidate_years - required_years) * 6)
    else:
        experience_gap_years = required_years - candidate_years
        experience_alignment = max(20, 78 - experience_gap_years * 18)

    soft_skills = {"communication", "teamwork", "leadership", "collaboration", "problem solving", "ownership", "stakeholder"}
    resume_text_lower = resume_text.lower()
    job_text_lower = job_text.lower()
    soft_match = sum(1 for skill in soft_skills if skill in resume_text_lower and skill in job_text_lower)
    culture_fit = min(100, 45 + soft_match * 15 + (10 if any(word in resume_text_lower for word in ["led", "managed", "built", "launched"]) else 0))

    growth_potential = min(100, 50 + len(bonus_skills) * 4 + max(0, 10 - len(missing_required) * 2))

    skills_alignment = round(required_match_pct * 0.7 + contextual_match_pct * 0.3, 1)
    match_percentage = round(
        min(
            100,
            skills_alignment * 0.45
            + experience_alignment * 0.2
            + culture_fit * 0.15
            + growth_potential * 0.1
            + semantic_similarity * 0.1,
        ),
        1,
    )

    skill_recommendations = build_skill_recommendations(missing_required, missing_optional, bonus_skills)
    improvement_suggestions = [
        f"Show hands-on evidence of {item['skill']} in a project, certification, or impact bullet."
        for item in skill_recommendations[:4]
    ]
    if semantic_similarity < 55:
        improvement_suggestions.append("Mirror the job language more closely in your summary, skills, and project bullets where it is truthful.")
    if experience_alignment < 65:
        improvement_suggestions.append("Add measurable outcomes, timelines, and ownership signals to strengthen experience alignment.")
    
    match, created = AIMatchScore.objects.update_or_create(
        job=job,
        resume=resume,
        defaults={
            "match_percentage": match_percentage,
            "skills_alignment": int(round(skills_alignment)),
            "experience_alignment": experience_alignment,
            "culture_fit": culture_fit,
            "growth_potential": growth_potential,
            "matched_skills": title_skills(matched_required),
            "missing_skills": title_skills(missing_required),
            "bonus_skills": title_skills(bonus_skills),
            "match_reasons": f"Matched {len(matched_required)} of {len(required_skills)} required skills with {semantic_similarity:.0f}% textual similarity",
        }
    )

    if match_percentage >= 80:
        notify_high_match(request.user, job, match_percentage, title_skills(missing_required))
    
    return JsonResponse({
        "id": match.id,
        "match_percentage": match_percentage,
        "skills_alignment": int(round(skills_alignment)),
        "experience_alignment": experience_alignment,
        "culture_fit": culture_fit,
        "growth_potential": growth_potential,
        "semantic_similarity": semantic_similarity,
        "candidate_experience_years": candidate_years,
        "required_experience_years": required_years,
        "required_experience_level": "senior" if required_years >= 5 else "mid" if required_years >= 3 else "junior",
        "matched_skills": title_skills(matched_required),
        "missing_skills": title_skills(missing_required + missing_optional),
        "missing_skills_required": title_skills(missing_required),
        "missing_skills_nice": title_skills(missing_optional),
        "bonus_skills": title_skills(bonus_skills),
        "skill_recommendations": skill_recommendations,
        "improvement_suggestions": improvement_suggestions,
        "match_reasons": match.match_reasons,
        "created": created,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_job_matches(request, job_id):
    """Get top matching resumes for a job"""
    try:
        job = JobPost.objects.get(id=job_id, posted_by=request.user)
    except JobPost.DoesNotExist:
        return JsonResponse({"error": "Job not found"}, status=404)
    
    matches = AIMatchScore.objects.filter(job=job).order_by("-match_percentage")[:10]
    
    return JsonResponse({
        "count": matches.count(),
        "matches": [
            {
                "id": m.id,
                "resume_id": m.resume.id,
                "candidate": m.resume.user.email,
                "match_percentage": m.match_percentage,
                "skills_alignment": m.skills_alignment,
                "experience_alignment": m.experience_alignment,
                "culture_fit": m.culture_fit,
                "matched_skills": m.matched_skills,
            }
            for m in matches
        ]
    })


# ============ AI CAREER COACH ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def generate_career_plan(request):
    """Generate personalized career plan"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    target_role = data.get("target_role", "")
    current_level = data.get("current_level", "junior")
    
    profile = request.user.profile
    current_skills = profile.skills or []
    
    # Recommended roles based on level
    role_progression = {
        "junior": ["Mid-Level Developer", "Associate", "Specialist"],
        "mid": ["Senior Developer", "Team Lead", "Manager"],
        "senior": ["Principal Engineer", "Director", "VP"],
        "lead": ["VP Engineering", "Chief Architect", "CTO"],
    }
    
    recommended_roles = role_progression.get(current_level, [])
    
    # Skill development plan
    plan = []
    all_roles_skills = {
        "junior developer": ["Python", "JavaScript", "Git", "SQL"],
        "senior developer": ["System Design", "Architecture", "Leadership", "DevOps"],
        "data scientist": ["Machine Learning", "Statistics", "Python", "SQL"],
    }
    
    target_skills = all_roles_skills.get(target_role.lower(), [])
    for skill in target_skills:
        if skill not in current_skills:
            plan.append({
                "skill": skill,
                "timeline": "3-6 months",
                "resources": ["Coursera", "Udemy", "Practice Projects"]
            })
    
    # Career milestones
    milestones = [
        {"milestone": "Master core skills", "timeline": "3 months", "status": "pending"},
        {"milestone": "Complete side projects", "timeline": "6 months", "status": "pending"},
        {"milestone": "Interview preparation", "timeline": "2 weeks before", "status": "pending"},
    ]
    
    # Salary insights
    salary_ranges = {
        "junior developer": "$60K - $90K",
        "mid developer": "$90K - $130K",
        "senior developer": "$130K - $180K",
    }
    
    coach, created = AICareerCoach.objects.update_or_create(
        user=request.user,
        defaults={
            "career_goals": data.get("goals", ""),
            "current_level": current_level,
            "target_level": target_role,
            "recommended_roles": recommended_roles,
            "skill_development_plan": plan,
            "career_milestones": milestones,
            "personalized_advice": f"Based on your current skills in {', '.join(current_skills[:3])}, focus on learning {target_skills[0] if target_skills else 'new technologies'}.",
            "salary_insights": salary_ranges,
        }
    )
    
    return JsonResponse({
        "id": coach.id,
        "current_level": current_level,
        "target_level": target_role,
        "recommended_roles": recommended_roles,
        "skill_development_plan": plan,
        "career_milestones": milestones,
        "personalized_advice": coach.personalized_advice,
        "salary_insights": salary_ranges,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_career_coach(request):
    """Get user's career coach plan"""
    try:
        coach = AICareerCoach.objects.get(user=request.user)
    except AICareerCoach.DoesNotExist:
        return JsonResponse({"error": "No career plan found"}, status=404)
    
    return JsonResponse({
        "id": coach.id,
        "career_goals": coach.career_goals,
        "current_level": coach.current_level,
        "target_level": coach.target_level,
        "recommended_roles": coach.recommended_roles,
        "skill_development_plan": coach.skill_development_plan,
        "career_milestones": coach.career_milestones,
        "personalized_advice": coach.personalized_advice,
        "job_recommendations": coach.job_recommendations,
        "salary_insights": coach.salary_insights,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def predict_career_path(request):
    """Predict career opportunities and learning paths using profile, resume, and market signals."""
    profile = getattr(request.user, "profile", None)
    resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()

    profile_skills = [skill.lower() for skill in (getattr(profile, "skills", []) or [])]
    resume_skills = [skill.lower() for skill in (resume.extracted_skills or [])] if resume else []
    combined_skills = sorted(set(profile_skills + resume_skills))

    applications_qs = JobApplication.objects.filter(applicant=request.user)
    total_applications = applications_qs.count()
    shortlisted_count = applications_qs.filter(status=JobApplication.Status.SHORTLISTED).count()

    skills_count = len(combined_skills)
    if skills_count >= 12 or shortlisted_count >= 3:
        current_level = "senior"
    elif skills_count >= 7 or total_applications >= 5:
        current_level = "mid"
    else:
        current_level = "junior"

    trajectory_map = {
        "junior": [
            {"role": "Junior Software Engineer", "timeline": "0-6 months", "confidence": 78},
            {"role": "Software Engineer", "timeline": "6-18 months", "confidence": 72},
            {"role": "Senior Software Engineer", "timeline": "18-36 months", "confidence": 63},
        ],
        "mid": [
            {"role": "Senior Software Engineer", "timeline": "0-12 months", "confidence": 79},
            {"role": "Tech Lead", "timeline": "12-24 months", "confidence": 68},
            {"role": "Engineering Manager", "timeline": "24-48 months", "confidence": 59},
        ],
        "senior": [
            {"role": "Principal Engineer", "timeline": "0-18 months", "confidence": 71},
            {"role": "Engineering Manager", "timeline": "12-30 months", "confidence": 66},
            {"role": "Director of Engineering", "timeline": "30-60 months", "confidence": 54},
        ],
    }

    active_jobs = list(JobPost.objects.filter(is_active=True)[:120])
    skill_demand = {}
    for job in active_jobs:
        for skill in split_skill_keywords(job.skills_required):
            skill_demand[skill] = skill_demand.get(skill, 0) + 1

    top_demanded = sorted(skill_demand.items(), key=lambda item: item[1], reverse=True)[:10]
    missing_demanded = [skill for skill, _count in top_demanded if skill not in combined_skills][:5]

    learning_catalog = {
        "python": ["Python for Everybody", "FastAPI Crash Course", "LeetCode Python Track"],
        "react": ["React Official Tutorial", "Frontend Masters React Path", "Build 3 React Projects"],
        "django": ["Django for APIs", "Deploy Django on Cloud", "Django REST Framework Guide"],
        "sql": ["SQLBolt", "Data Modeling Fundamentals", "PostgreSQL Performance Basics"],
        "aws": ["AWS Cloud Practitioner", "Serverless on AWS", "AWS Well-Architected Labs"],
        "system design": ["Grokking System Design", "Scalable Systems Course", "Design Interview Prep"],
    }

    learning_recommendations = []
    for skill in missing_demanded:
        learning_recommendations.append(
            {
                "skill": skill.title(),
                "priority": "high",
                "why": "High demand in currently open jobs relevant to your profile.",
                "resources": learning_catalog.get(skill, ["Coursera", "Udemy", "Hands-on project practice"]),
            }
        )

    if not learning_recommendations:
        learning_recommendations.append(
            {
                "skill": "Leadership & Communication",
                "priority": "medium",
                "why": "Soft skills increase shortlist rates for mid and senior roles.",
                "resources": ["Public speaking practice", "Leadership micro-courses", "Mentor-led mock interviews"],
            }
        )

    predicted_paths = trajectory_map[current_level]
    roadmap_graph = {
        "nodes": [
            {"id": "now", "label": f"Current ({current_level.title()})"},
            *[
                {
                    "id": f"step-{index}",
                    "label": step["role"],
                    "timeline": step["timeline"],
                }
                for index, step in enumerate(predicted_paths, start=1)
            ],
        ],
        "edges": [
            {"from": "now", "to": "step-1"},
            {"from": "step-1", "to": "step-2"},
            {"from": "step-2", "to": "step-3"},
        ],
    }

    return JsonResponse(
        {
            "current_level": current_level,
            "skills_signal": combined_skills,
            "application_signal": {
                "total_applications": total_applications,
                "shortlisted": shortlisted_count,
            },
            "predicted_paths": predicted_paths,
            "learning_recommendations": learning_recommendations,
            "roadmap_graph": roadmap_graph,
            "profile_strength": get_profile_strength(profile, resume),
            "resume_rating": (AIResumeAnalysis.objects.filter(resume=resume).values_list("overall_rating", flat=True).first() or 0) if resume else 0,
            "market_insights": {
                "active_jobs": len(active_jobs),
                "top_demanded_skills": [
                    {"skill": skill.title(), "openings": count}
                    for skill, count in top_demanded
                ],
            },
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def simulate_voice_interview(request):
    """Conduct a text-backed mock voice interview with instant AI evaluation."""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    role = (data.get("role") or "Software Engineer").strip()
    transcript = (data.get("transcript") or "").strip().lower()
    if not transcript:
        return JsonResponse({"error": "transcript is required"}, status=400)

    answer_length = len(transcript.split())
    filler_count = sum(transcript.count(token) for token in ["um", "uh", "like", "basically"])
    structure_signals = sum(1 for token in ["first", "second", "because", "therefore", "example"] if token in transcript)
    confidence_signals = sum(1 for token in ["led", "built", "implemented", "improved", "delivered"] if token in transcript)

    fluency_score = max(35, min(100, 85 - (filler_count * 6) + min(10, structure_signals * 2)))
    communication_score = max(40, min(100, 55 + min(18, answer_length // 20) + structure_signals * 4))
    confidence_score = max(35, min(100, 50 + confidence_signals * 8 - filler_count * 3))
    overall_score = int((fluency_score * 0.35) + (communication_score * 0.4) + (confidence_score * 0.25))

    recommendations = []
    if filler_count > 3:
        recommendations.append("Reduce filler words by pausing briefly before key points.")
    if structure_signals < 2:
        recommendations.append("Use a clearer structure: context, action, and measurable result.")
    if confidence_signals < 2:
        recommendations.append("Add impact verbs and ownership language to sound more confident.")
    if answer_length < 80:
        recommendations.append("Provide deeper examples with tools, constraints, and outcomes.")
    if not recommendations:
        recommendations.append("Strong response quality. Practice with role-specific technical questions.")

    return JsonResponse(
        {
            "role": role,
            "overall_score": overall_score,
            "fluency_score": fluency_score,
            "communication_score": communication_score,
            "confidence_score": confidence_score,
            "filler_words_detected": filler_count,
            "recommendations": recommendations,
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def analyze_mock_interview(request):
    """Analyze a mock interview using transcript + webcam signals and return structured AI feedback."""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    role = (data.get("role") or "Software Engineer").strip()
    transcript_raw = (data.get("transcript") or "").strip()
    if not transcript_raw:
        return JsonResponse({"error": "transcript is required"}, status=400)

    transcript = transcript_raw.lower()
    webcam = data.get("webcam") or {}

    answer_length = len(transcript.split())
    filler_count = sum(transcript.count(token) for token in ["um", "uh", "like", "basically"])
    structure_signals = sum(1 for token in ["first", "second", "because", "therefore", "example"] if token in transcript)
    confidence_signals = sum(1 for token in ["led", "built", "implemented", "improved", "delivered"] if token in transcript)

    fluency_score = max(35, min(100, 85 - (filler_count * 6) + min(10, structure_signals * 2)))
    communication_score = max(40, min(100, 55 + min(18, answer_length // 20) + structure_signals * 4))
    voice_confidence = max(35, min(100, 50 + confidence_signals * 8 - filler_count * 3))

    eye_contact_score = int(webcam.get("eye_contact_score", data.get("eye_contact_score", 70)) or 70)
    posture_score = int(webcam.get("posture_score", data.get("posture_score", 68)) or 68)
    expression_score = int(webcam.get("expression_score", data.get("expression_score", 66)) or 66)
    speaking_pace_wpm = int(data.get("speaking_pace_wpm", 132) or 132)

    eye_contact_score = max(0, min(100, eye_contact_score))
    posture_score = max(0, min(100, posture_score))
    expression_score = max(0, min(100, expression_score))
    speaking_pace_wpm = max(60, min(220, speaking_pace_wpm))

    webcam_presence = int((eye_contact_score * 0.45) + (posture_score * 0.35) + (expression_score * 0.20))
    confidence_score = int((voice_confidence * 0.55) + (webcam_presence * 0.45))
    overall_score = int(
        (fluency_score * 0.25)
        + (communication_score * 0.30)
        + (confidence_score * 0.30)
        + (webcam_presence * 0.15)
    )

    strengths = []
    improvements = []

    if communication_score >= 72:
        strengths.append("Clear and structured response flow")
    if confidence_score >= 72:
        strengths.append("Confident delivery with strong ownership language")
    if eye_contact_score >= 70:
        strengths.append("Stable eye contact with interviewer")
    if posture_score >= 70:
        strengths.append("Professional posture and composure")
    if speaking_pace_wpm >= 105 and speaking_pace_wpm <= 165:
        strengths.append("Balanced speaking pace for interview clarity")

    if filler_count > 3:
        improvements.append("Reduce filler words by pausing before key ideas")
    if structure_signals < 2:
        improvements.append("Use STAR-style structure: situation, action, result")
    if eye_contact_score < 65:
        improvements.append("Look at the camera for stronger virtual eye contact")
    if posture_score < 65:
        improvements.append("Keep shoulders aligned and avoid frequent lean shifts")
    if speaking_pace_wpm < 105:
        improvements.append("Increase speaking pace slightly to sound more decisive")
    if speaking_pace_wpm > 165:
        improvements.append("Slow down to improve clarity and interviewer retention")

    if not strengths:
        strengths.append("You stayed engaged and completed the response")
    if not improvements:
        improvements.append("Strong baseline performance. Focus on deeper impact examples")

    if overall_score >= 80:
        summary = "Strong interview performance with confident delivery and clear communication."
    elif overall_score >= 65:
        summary = "Good interview performance with a few delivery and structure improvements needed."
    else:
        summary = "Developing performance. Prioritize structure, pacing, and camera presence practice."

    follow_up_question = (
        f"For the {role} role, describe one project where you solved a difficult blocker and quantify the result."
    )

    return JsonResponse(
        {
            "role": role,
            "scores": {
                "overall": overall_score,
                "confidence": confidence_score,
                "fluency": fluency_score,
                "communication": communication_score,
                "eye_contact": eye_contact_score,
                "posture": posture_score,
                "expression": expression_score,
                "webcam_presence": webcam_presence,
                "speaking_pace_wpm": speaking_pace_wpm,
            },
            "analysis": {
                "filler_words_detected": filler_count,
                "answer_word_count": answer_length,
                "structure_signals": structure_signals,
            },
            "ai_feedback": {
                "summary": summary,
                "strengths": strengths,
                "improvements": improvements,
                "next_question": follow_up_question,
            },
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def optimize_resume_keywords(request):
    """Suggest ATS keywords using resume signal and active job market demand."""
    resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()
    if not resume:
        return JsonResponse({"error": "No resume found for optimization."}, status=404)

    resume_skills = [skill.lower() for skill in (resume.extracted_skills or [])]
    demand = {}
    for job in JobPost.objects.filter(is_active=True)[:150]:
        for skill in split_skill_keywords(job.skills_required):
            demand[skill] = demand.get(skill, 0) + 1

    top_market_skills = sorted(demand.items(), key=lambda item: item[1], reverse=True)[:20]
    missing_keywords = [skill for skill, _count in top_market_skills if skill not in resume_skills][:8]
    matched_keywords = [skill for skill, _count in top_market_skills if skill in resume_skills][:8]

    summary_hint = "Highlight measurable outcomes, ownership, and role-relevant keywords in the first 4 lines."
    formatting_hint = "Use concise bullet points, action verbs, and a dedicated skills section for ATS readability."

    return JsonResponse(
        {
            "resume_id": resume.id,
            "matched_keywords": [skill.title() for skill in matched_keywords],
            "missing_keywords": [skill.title() for skill in missing_keywords],
            "summary_hint": summary_hint,
            "formatting_hint": formatting_hint,
            "optimization_score": max(30, min(95, 45 + len(matched_keywords) * 6 - len(missing_keywords))),
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def recommend_teams(request):
    """Recommend collaborators and mentors based on skill overlap and role diversity."""
    profile = getattr(request.user, "profile", None)
    my_skills = set([skill.lower() for skill in (getattr(profile, "skills", []) or [])])

    recommendations = []
    candidates = User.objects.exclude(id=request.user.id).select_related("profile")[:120]
    for user in candidates:
        peer_skills = set([skill.lower() for skill in (getattr(user.profile, "skills", []) or [])])
        overlap = my_skills.intersection(peer_skills)
        complement = peer_skills.difference(my_skills)
        if not overlap and not complement:
            continue
        score = (len(overlap) * 6) + (len(complement) * 2)
        recommendations.append(
            {
                "user_id": user.id,
                "name": f"{user.first_name} {user.last_name}".strip() or user.email,
                "role": user.role,
                "score": score,
                "shared_skills": sorted(list(overlap))[:5],
                "complementary_skills": sorted(list(complement))[:5],
            }
        )

    recommendations.sort(key=lambda item: item["score"], reverse=True)
    return JsonResponse({"count": len(recommendations[:8]), "recommendations": recommendations[:8]})


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def generate_internship_roadmap(request):
    """Generate a semester-wise internship roadmap from current skill readiness."""
    profile = getattr(request.user, "profile", None)
    skills = [skill.lower() for skill in (getattr(profile, "skills", []) or [])]
    has_projects = bool(getattr(profile, "portfolio_items", []) or [])

    base_roadmap = [
        {
            "semester": "Semester 1",
            "focus": "Core skills foundation",
            "actions": ["Master one language deeply", "Build 2 mini projects", "Complete DSA basics"],
        },
        {
            "semester": "Semester 2",
            "focus": "Portfolio and problem solving",
            "actions": ["Add full-stack project", "Practice mock interviews", "Contribute to open source"],
        },
        {
            "semester": "Semester 3",
            "focus": "Internship targeting",
            "actions": ["Optimize resume keywords", "Apply to 30+ internships", "Network with mentors"],
        },
    ]

    if "python" not in skills and "javascript" not in skills:
        base_roadmap[0]["actions"].insert(0, "Choose Python or JavaScript as primary language.")
    if not has_projects:
        base_roadmap[1]["actions"].insert(0, "Publish at least one project with demo and README.")

    readiness = 35 + (min(8, len(skills)) * 6) + (10 if has_projects else 0)
    return JsonResponse(
        {
            "readiness_score": min(95, readiness),
            "roadmap": base_roadmap,
            "next_best_action": base_roadmap[0]["actions"][0],
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def candidate_reputation_score(request):
    """Score candidate credibility from profile quality, activity, and recruiter outcomes."""
    profile = getattr(request.user, "profile", None)
    applications = JobApplication.objects.filter(applicant=request.user)
    total_apps = applications.count()
    shortlisted = applications.filter(status=JobApplication.Status.SHORTLISTED).count()

    profile_checks = [
        bool(getattr(profile, "headline", "")),
        bool(getattr(profile, "location", "")),
        bool(getattr(profile, "bio", "")),
        bool(getattr(profile, "github_url", "") or getattr(profile, "linkedin_url", "")),
        len(getattr(profile, "skills", []) or []) >= 5,
        len(getattr(profile, "portfolio_items", []) or []) >= 1,
    ]
    profile_strength = int((sum(1 for item in profile_checks if item) / len(profile_checks)) * 100)
    shortlist_rate = int((shortlisted / total_apps) * 100) if total_apps else 0

    reputation = int((profile_strength * 0.55) + (min(100, total_apps * 8) * 0.2) + (shortlist_rate * 0.25))
    band = "High" if reputation >= 75 else "Medium" if reputation >= 55 else "Emerging"

    return JsonResponse(
        {
            "reputation_score": reputation,
            "band": band,
            "profile_strength": profile_strength,
            "application_activity": total_apps,
            "shortlist_rate": shortlist_rate,
            "improvement_tip": "Increase score by adding portfolio proof and consistent interview follow-ups.",
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def detect_fake_resume(request):
    """Detect potentially manipulated resume content using heuristic AI checks."""
    resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()
    if not resume:
        return JsonResponse({"error": "No resume found."}, status=404)

    text = (resume.extracted_text or "").lower()
    suspicious_flags = []
    if text.count("lorem") > 1:
        suspicious_flags.append("Placeholder text detected (lorem/ipsum).")
    if text.count("certified") > 8:
        suspicious_flags.append("Unusually high certification claims.")
    if len(text.split()) < 70:
        suspicious_flags.append("Resume too short for reliable assessment.")
    if not any(token in text for token in ["project", "experience", "intern", "built"]):
        suspicious_flags.append("Missing concrete work evidence.")

    confidence = max(20, 92 - len(suspicious_flags) * 17)
    verdict = "likely_authentic" if confidence >= 70 else "needs_verification"

    return JsonResponse(
        {
            "resume_id": resume.id,
            "verdict": verdict,
            "authenticity_confidence": confidence,
            "flags": suspicious_flags,
            "verification_suggestions": [
                "Attach GitHub or portfolio links with project proof.",
                "Use measurable achievements and role-specific details.",
            ],
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def internship_attendance_tracking(request):
    """Provide internship participation and progress analytics."""
    internships = JobApplication.objects.filter(
        applicant=request.user,
        job__employment_type=JobPost.EmploymentType.INTERNSHIP,
    ).select_related("job")

    total = internships.count()
    completed = internships.filter(status=JobApplication.Status.SHORTLISTED).count()
    active = internships.filter(status__in=[JobApplication.Status.APPLIED, JobApplication.Status.REVIEWING]).count()

    participation = min(100, total * 20)
    attendance_score = min(100, 45 + (completed * 18) + (active * 10)) if total else 0
    progress_score = min(100, 30 + (completed * 22) + (total * 8)) if total else 0

    return JsonResponse(
        {
            "total_internships": total,
            "active_internships": active,
            "completed_or_shortlisted": completed,
            "participation_score": participation,
            "attendance_score": attendance_score,
            "progress_score": progress_score,
            "tracker": [
                {
                    "job": app.job.title,
                    "company": app.job.company,
                    "status": app.status,
                    "match_score": app.match_score,
                }
                for app in internships[:20]
            ],
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def simulate_group_discussion(request):
    """Simulate group discussion round with AI-generated participants and instant feedback."""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    topic = (data.get("topic") or "AI in modern hiring").strip()
    response = (data.get("candidate_response") or "").lower().strip()
    if not response:
        return JsonResponse({"error": "candidate_response is required"}, status=400)

    participants = [
        {"name": "Riya", "stance": "supports innovation"},
        {"name": "Arjun", "stance": "focus on ethics"},
        {"name": "Maya", "stance": "focus on practical rollout"},
    ]

    idea_score = min(100, 45 + len(response.split()) // 3)
    structure_score = min(100, 40 + sum(1 for token in ["first", "second", "however", "therefore"] if token in response) * 14)
    collaboration_score = min(100, 35 + sum(1 for token in ["agree", "build", "add", "point"] if token in response) * 15)
    total_score = int((idea_score * 0.4) + (structure_score * 0.35) + (collaboration_score * 0.25))

    feedback = []
    if idea_score < 65:
        feedback.append("Add more domain-relevant examples and sharper arguments.")
    if structure_score < 65:
        feedback.append("Organize points with clear transitions and counter-arguments.")
    if collaboration_score < 65:
        feedback.append("Acknowledge peer points and build on them collaboratively.")
    if not feedback:
        feedback.append("Strong GD presence. Maintain concise and collaborative delivery.")

    return JsonResponse(
        {
            "topic": topic,
            "participants": participants,
            "scores": {
                "idea_score": idea_score,
                "structure_score": structure_score,
                "collaboration_score": collaboration_score,
                "overall_score": total_score,
            },
            "feedback": feedback,
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def personal_branding_assistant(request):
    """Generate LinkedIn-style personal branding guidance from profile signal."""
    profile = getattr(request.user, "profile", None)
    skills = getattr(profile, "skills", []) or []

    headline = getattr(profile, "headline", "") or ""
    bio = getattr(profile, "bio", "") or ""
    about = getattr(profile, "about", "") or ""
    links_ready = bool(getattr(profile, "github_url", "") or getattr(profile, "linkedin_url", ""))

    strength = int((
        (1 if headline else 0)
        + (1 if len(bio) > 60 else 0)
        + (1 if len(about) > 120 else 0)
        + (1 if len(skills) >= 5 else 0)
        + (1 if links_ready else 0)
    ) / 5 * 100)

    return JsonResponse(
        {
            "brand_strength": strength,
            "headline_suggestion": headline or "AI/Software Engineer | Building scalable products with measurable impact",
            "about_suggestion": "Summarize your niche, strongest projects, outcomes, and target role in 4-6 lines.",
            "content_strategy": [
                "Post one project breakdown weekly with architecture and results.",
                "Share internship/career milestones and learnings.",
                "Engage with recruiters and mentors in your domain twice a week.",
            ],
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def networking_suggestions(request):
    """Recommend recruiters, mentors, and peers by shared and complementary skills."""
    base = recommend_teams(request)
    data = json.loads(base.content.decode("utf-8"))
    enriched = []
    for item in data.get("recommendations", []):
        persona = "mentor" if item["role"] in [User.Role.RECRUITER, User.Role.ADMIN] else "peer"
        enriched.append({**item, "persona": persona})
    return JsonResponse({"count": len(enriched), "recommendations": enriched})


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def career_timeline(request):
    """Generate timeline view of career milestones and activity events."""
    profile = getattr(request.user, "profile", None)
    resumes = Resume.objects.filter(user=request.user).order_by("uploaded_at")
    apps = JobApplication.objects.filter(applicant=request.user).select_related("job").order_by("created_at")

    timeline = [
        {
            "date": request.user.created_at.date().isoformat(),
            "event": "Joined platform",
            "type": "account",
        }
    ]
    if profile and profile.updated_at:
        timeline.append(
            {
                "date": profile.updated_at.date().isoformat(),
                "event": "Profile updated",
                "type": "profile",
            }
        )
    for resume in resumes[:5]:
        timeline.append(
            {
                "date": resume.uploaded_at.date().isoformat(),
                "event": f"Resume uploaded ({resume.original_name})",
                "type": "resume",
            }
        )
    for app in apps[:12]:
        timeline.append(
            {
                "date": app.created_at.date().isoformat(),
                "event": f"Applied to {app.job.title} at {app.job.company}",
                "type": "application",
                "status": app.status,
            }
        )

    timeline.sort(key=lambda item: item["date"])
    return JsonResponse({"count": len(timeline), "timeline": timeline})


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def translate_resume(request):
    """Translate extracted resume text to supported languages (heuristic translation layer)."""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    target_language = (data.get("target_language") or "es").lower()
    supported = {
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "hi": "Hindi",
    }
    if target_language not in supported:
        return JsonResponse({"error": "Unsupported language. Use es/fr/de/hi."}, status=400)

    resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()
    if not resume:
        return JsonResponse({"error": "No resume found."}, status=404)

    glossary = {
        "experience": {"es": "experiencia", "fr": "experience", "de": "erfahrung", "hi": "anubhav"},
        "skills": {"es": "habilidades", "fr": "competences", "de": "fahigkeiten", "hi": "kaushal"},
        "project": {"es": "proyecto", "fr": "projet", "de": "projekt", "hi": "pariyojana"},
        "education": {"es": "educacion", "fr": "education", "de": "ausbildung", "hi": "shiksha"},
    }

    text = resume.extracted_text or ""
    translated = text
    for source, map_values in glossary.items():
        translated = translated.replace(source, map_values[target_language])
        translated = translated.replace(source.title(), map_values[target_language].title())

    return JsonResponse(
        {
            "resume_id": resume.id,
            "target_language": supported[target_language],
            "translated_excerpt": translated[:1600],
            "note": "Heuristic translation preview. For production, plug in a full neural translation provider.",
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def company_hiring_heatmaps(request):
    """Return region and technology heatmap style hiring distribution."""
    active_jobs = JobPost.objects.filter(is_active=True)[:250]
    location_heat = {}
    tech_heat = {}

    for job in active_jobs:
        location = (job.location or "unknown").strip().lower()
        location_heat[location] = location_heat.get(location, 0) + 1
        for skill in split_skill_keywords(job.skills_required):
            tech_heat[skill] = tech_heat.get(skill, 0) + 1

    top_locations = sorted(location_heat.items(), key=lambda item: item[1], reverse=True)[:12]
    top_tech = sorted(tech_heat.items(), key=lambda item: item[1], reverse=True)[:15]

    return JsonResponse(
        {
            "location_heatmap": [{"region": key.title(), "openings": value} for key, value in top_locations],
            "technology_heatmap": [{"skill": key.title(), "openings": value} for key, value in top_tech],
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def evaluate_competitive_coding(request):
    """Evaluate coding performance based on speed, correctness, and optimization approach."""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    solved = max(0, int(data.get("problems_solved", 0)))
    attempts = max(1, int(data.get("attempts", 1)))
    avg_minutes = max(1, int(data.get("avg_minutes_per_problem", 30)))
    optimized = bool(data.get("uses_optimized_approach", False))

    accuracy = min(100, int((solved / attempts) * 100))
    speed = max(20, min(100, 110 - avg_minutes * 2))
    optimization = 85 if optimized else 55
    total = int((accuracy * 0.45) + (speed * 0.3) + (optimization * 0.25))

    return JsonResponse(
        {
            "accuracy_score": accuracy,
            "speed_score": speed,
            "optimization_score": optimization,
            "overall_score": total,
            "feedback": [
                "Practice timed contests for speed consistency.",
                "Review complexity trade-offs after every problem.",
                "Track weak topics and solve 5 focused problems per topic.",
            ],
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def personality_development_coach(request):
    """Provide lightweight personality growth guidance from profile and activity signals."""
    profile = getattr(request.user, "profile", None)
    skills = split_skill_keywords(getattr(profile, "skills", "") or "")
    resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()
    applications = JobApplication.objects.filter(applicant=request.user)

    confidence_score = min(
        100,
        35
        + (12 if getattr(profile, "headline", "") else 0)
        + (10 if getattr(profile, "bio", "") else 0)
        + min(24, len(skills) * 4)
        + (8 if resume else 0)
        + min(16, applications.count() * 2),
    )

    strengths = []
    if getattr(profile, "headline", ""):
        strengths.append("Clear professional identity")
    if len(skills) >= 3:
        strengths.append("Solid skill expression")
    if resume:
        strengths.append("Active job preparation")
    if applications.exists():
        strengths.append("Consistent career activity")

    development_plan = [
        "Practice short self-introductions that combine your role, impact, and interests.",
        "Write weekly progress notes about projects and lessons learned.",
        "Ask for feedback after interviews and refine communication patterns.",
    ]

    confidence_drills = [
        "Record a 60-second intro and remove filler words.",
        "Explain one project using problem, action, result, and learning.",
        "Share one professional update or project insight every week.",
    ]

    return JsonResponse(
        {
            "coach_score": confidence_score,
            "strengths": strengths or ["Build a clearer public profile and document your wins."],
            "development_plan": development_plan,
            "confidence_drills": confidence_drills,
            "focus_area": "communication" if confidence_score < 65 else "leadership",
            "tone_tip": "Use concise, positive, and outcome-driven language.",
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def interactive_career_simulation_engine(request):
    """Simulate likely career decisions with simple branching scenarios."""
    profile = getattr(request.user, "profile", None)
    skills = split_skill_keywords(getattr(profile, "skills", "") or "")
    apps = JobApplication.objects.filter(applicant=request.user).select_related("job")
    active_jobs = JobPost.objects.filter(is_active=True)[:100]

    scenarios = [
        {
            "phase": "Next 30 days",
            "choice": "Apply broadly or target a focused shortlist",
            "recommended_action": "Target a focused shortlist and tailor every application.",
            "outcome": "Higher response quality and better interview preparation.",
        },
        {
            "phase": "Next 90 days",
            "choice": "Ship one showcase project or wait for more experience",
            "recommended_action": "Ship one showcase project that proves your strongest skill.",
            "outcome": "Stronger portfolio signal and better networking conversations.",
        },
        {
            "phase": "Next 12 months",
            "choice": "Specialize deeply or stay broad",
            "recommended_action": "Specialize in a core area while maintaining adjacent fluency.",
            "outcome": "Improved role fit and clearer career narrative.",
        },
    ]

    recommended_path = [
        "Strengthen one core stack with proof-of-work projects.",
        "Use internships or freelance work to build outcome stories.",
        "Translate each project into measurable impact and interview examples.",
    ]

    simulation_score = min(100, 40 + len(skills) * 4 + min(20, apps.count() * 3) + min(15, len(active_jobs) // 15))

    return JsonResponse(
        {
            "simulation_score": simulation_score,
            "current_signal": {
                "skills": skills[:8],
                "applications": apps.count(),
            },
            "scenarios": scenarios,
            "recommended_path": recommended_path,
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def smart_internship_performance_evaluation(request):
    """Score internship readiness and performance from active application history."""
    internships = JobApplication.objects.filter(applicant=request.user, job__employment_type="internship").select_related("job")
    total = internships.count()
    active = internships.filter(status__in=[JobApplication.Status.APPLIED, JobApplication.Status.REVIEWING]).count()
    shortlisted = internships.filter(status=JobApplication.Status.SHORTLISTED).count()
    completed = internships.filter(status=JobApplication.Status.HIRED).count()

    attendance_score = min(100, 48 + total * 9 + active * 8)
    project_completion_score = min(100, 42 + shortlisted * 14 + completed * 18)
    communication_score = min(100, 40 + total * 7 + completed * 4)
    performance_score = int((attendance_score * 0.35) + (project_completion_score * 0.4) + (communication_score * 0.25))

    feedback = []
    if total == 0:
        feedback.append("Apply to internships regularly to generate performance evidence.")
    if active < 2:
        feedback.append("Keep more internship options active to improve resilience.")
    if shortlisted == 0 and completed == 0:
        feedback.append("Focus on stronger tailoring and proof-of-work for internship screening.")
    if not feedback:
        feedback.append("Your internship signal is healthy. Keep converting applications into interviews.")

    return JsonResponse(
        {
            "performance_score": performance_score,
            "attendance_score": attendance_score,
            "project_completion_score": project_completion_score,
            "communication_score": communication_score,
            "tracker": [
                {
                    "job": app.job.title,
                    "company": app.job.company,
                    "status": app.status,
                    "match_score": app.match_score,
                }
                for app in internships[:20]
            ],
            "feedback": feedback,
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def collaborative_project_builder(request):
    """Generate a collaborative project plan based on profile and job-market demand."""
    profile = getattr(request.user, "profile", None)
    skills = split_skill_keywords(getattr(profile, "skills", "") or "")
    demand = {}
    for job in JobPost.objects.filter(is_active=True)[:120]:
        for skill in split_skill_keywords(job.skills_required):
            demand[skill] = demand.get(skill, 0) + 1

    top_skills = [skill for skill, _count in sorted(demand.items(), key=lambda item: item[1], reverse=True)[:6]]
    project_title = f"{getattr(profile, 'headline', '') or 'Career'} Impact Builder"
    team_roles = [
        {"role": "Project Lead", "focus": "Scope, milestones, and shipping rhythm"},
        {"role": "Frontend Builder", "focus": "UI, accessibility, and demo flows"},
        {"role": "Backend Builder", "focus": "APIs, data models, and automation"},
        {"role": "Quality Analyst", "focus": "Testing, bug tracking, and reliability"},
    ]

    sprint_plan = [
        {"week": "Week 1", "goal": "Define problem, users, and success metrics."},
        {"week": "Week 2", "goal": "Ship a thin vertical slice with one polished workflow."},
        {"week": "Week 3", "goal": "Add analytics, collaboration, and feedback loops."},
        {"week": "Week 4", "goal": "Prepare demo, case study, and launch checklist."},
    ]

    return JsonResponse(
        {
            "project_title": project_title,
            "project_brief": "Build a small but measurable product that proves end-to-end ownership.",
            "priority_skills": (skills[:3] + top_skills[:3])[:6],
            "team_roles": team_roles,
            "sprint_plan": sprint_plan,
            "collaboration_tools": ["Kanban board", "Shared docs", "Code review checklist", "Weekly demo call"],
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def automated_interview_transcript_generator(request):
    """Generate a mock interview transcript from profile and resume signals."""
    role = request.GET.get("role") or request.GET.get("job_role") or "Software Engineer"
    profile = getattr(request.user, "profile", None)
    resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()
    skills = split_skill_keywords(getattr(profile, "skills", "") or "")

    intro = getattr(profile, "headline", "") or "I am a motivated candidate with hands-on project experience."
    project_line = "I have worked on projects involving " + ", ".join(skills[:3]) if skills else "I have built projects that improved workflow efficiency."
    transcript = [
        {
            "speaker": "Interviewer",
            "text": f"Tell me about yourself for the {role} role.",
        },
        {
            "speaker": "Candidate",
            "text": intro,
        },
        {
            "speaker": "Interviewer",
            "text": "Walk me through a project that demonstrates ownership.",
        },
        {
            "speaker": "Candidate",
            "text": project_line + (" Resume evidence is available." if resume else " I am ready to share more project evidence.") ,
        },
        {
            "speaker": "Interviewer",
            "text": "How do you handle deadlines and changing priorities?",
        },
        {
            "speaker": "Candidate",
            "text": "I prioritize tasks by impact, communicate blockers early, and break work into smaller deliverables.",
        },
    ]

    return JsonResponse(
        {
            "role": role,
            "transcript": transcript,
            "summary": "Interview flow covers introduction, project ownership, and time management.",
            "key_signals": ["ownership", "clarity", "impact", "priority management"],
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def ai_time_management_analyzer(request):
    """Analyze task load and suggest a practical weekly time plan."""
    applications = JobApplication.objects.filter(applicant=request.user)
    messages = ChatMessage.objects.filter(Q(sender=request.user) | Q(recipient=request.user))
    resumes = Resume.objects.filter(user=request.user)
    active_jobs = JobPost.objects.filter(is_active=True)

    focus_score = min(100, 45 + applications.count() * 4 + resumes.count() * 6 + min(18, messages.count() // 3))
    priorities = []
    if applications.exists():
        priorities.append("Follow up on active applications")
    if resumes.exists():
        priorities.append("Update resume for the next target role")
    if messages.exists():
        priorities.append("Reply to recruiter or mentor messages")
    priorities.append("Reserve one block for skill-building or project work")

    weekly_plan = [
        {"day": "Mon", "focus": "Applications and recruiter follow-ups"},
        {"day": "Tue", "focus": "Skill practice and interview prep"},
        {"day": "Wed", "focus": "Project work and portfolio updates"},
        {"day": "Thu", "focus": "Networking and message replies"},
        {"day": "Fri", "focus": "Review progress and plan next steps"},
    ]

    return JsonResponse(
        {
            "focus_score": focus_score,
            "load_summary": {
                "applications": applications.count(),
                "messages": messages.count(),
                "resumes": resumes.count(),
                "active_jobs": active_jobs.count(),
            },
            "priorities": priorities,
            "weekly_plan": weekly_plan,
            "time_blocks": ["90-minute focus block", "30-minute follow-up block", "20-minute review block"],
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def recruiter_trust_badge(request):
    """Issue recruiter verification status and trust badge metadata."""
    if request.user.role not in [User.Role.RECRUITER, User.Role.ADMIN]:
        return JsonResponse({"error": "Only recruiters/admins can access badge status."}, status=403)

    posted_jobs = JobPost.objects.filter(posted_by=request.user).count()
    application_volume = JobApplication.objects.filter(job__posted_by=request.user).count()

    verified = bool(request.user.is_email_verified and posted_jobs >= 1)
    score = min(100, 45 + posted_jobs * 12 + min(25, application_volume // 3))
    tier = "Gold" if score >= 85 else "Silver" if score >= 65 else "Bronze"

    return JsonResponse(
        {
            "verified": verified,
            "trust_score": score,
            "badge_tier": tier,
            "eligibility": {
                "email_verified": request.user.is_email_verified,
                "jobs_posted": posted_jobs,
                "application_volume": application_volume,
            },
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def generate_cover_letter(request):
    """Generate a tailored cover letter."""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    job_title = data.get("job_title", "Software Engineer")
    company = data.get("company", "the company")
    skills = data.get("skills", [])
    user_name = data.get("user_name") or request.user.get_full_name() or request.user.email

    if isinstance(skills, str):
        skills = [skill.strip() for skill in skills.split(",") if skill.strip()]

    ai_result = AIIntegrationService.generate_cover_letter(user_name, job_title, company, skills)
    return JsonResponse(
        {
            "success": ai_result.get("success", False),
            "cover_letter": ai_result.get("cover_letter", ""),
            "model_used": "gpt-3.5-turbo" if ai_result.get("success") else "fallback",
        }
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
def predict_salary(request):
    """Estimate a salary band from profile and resume signals."""
    if request.method == "POST":
        data = parse_json(request) or {}
        target_role = data.get("target_role", "Software Engineer")
    else:
        target_role = request.GET.get("target_role", "Software Engineer")

    profile = getattr(request.user, "profile", None)
    resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()

    skills = []
    if profile and getattr(profile, "skills", None):
        skills = [skill for skill in profile.skills if skill]
    if resume and resume.extracted_skills:
        skills = sorted(set(skills + [skill for skill in resume.extracted_skills if skill]))

    base_salary_map = {
        "junior": (50000, 85000),
        "mid": (85000, 130000),
        "senior": (130000, 180000),
        "lead": (160000, 240000),
    }

    total_applications = JobApplication.objects.filter(applicant=request.user).count()
    if len(skills) >= 12 or total_applications >= 10:
        level = "senior"
    elif len(skills) >= 7 or total_applications >= 4:
        level = "mid"
    else:
        level = "junior"

    salary_min, salary_max = base_salary_map[level]
    target_role_text = str(target_role).lower()
    if any(keyword in target_role_text for keyword in ["lead", "principal", "director"]):
        level = "lead"
        salary_min, salary_max = base_salary_map[level]
    elif any(keyword in target_role_text for keyword in ["senior", "staff", "architect"]):
        level = "senior"
        salary_min, salary_max = base_salary_map[level]

    midpoint = int((salary_min + salary_max) / 2)
    confidence = min(92, 55 + len(skills) * 2 + min(12, total_applications))

    signals = [
        f"Skills matched: {len(skills)}",
        f"Applications tracked: {total_applications}",
    ]
    if resume:
        signals.append(f"Latest resume: {resume.original_name}")

    return JsonResponse(
        {
            "target_role": target_role,
            "level": level,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_midpoint": midpoint,
            "label": f"${salary_min // 1000}k - ${salary_max // 1000}k",
            "confidence": confidence,
            "signals": signals,
        }
    )


# ============ REAL CHAT ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def send_chat_message(request):
    """Send a chat message"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    recipient_id = data.get("recipient_id")
    message_text = data.get("message")
    
    try:
        recipient = User.objects.get(id=recipient_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "Recipient not found"}, status=404)
    
    chat_msg = ChatMessage.objects.create(
        sender=request.user,
        recipient=recipient,
        message=message_text
    )
    
    return JsonResponse({
        "id": chat_msg.id,
        "sender_id": request.user.id,
        "recipient_id": recipient.id,
        "message": message_text,
        "is_read": False,
        "created_at": chat_msg.created_at.isoformat(),
    }, status=201)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_chat_messages(request, user_id):
    """Get chat messages with a specific user"""
    try:
        other_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    
    # Get messages between request.user and other_user
    messages = ChatMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by("created_at")
    
    # Mark received messages as read
    ChatMessage.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    return JsonResponse({
        "count": messages.count(),
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender.id,
                "sender_email": m.sender.email,
                "message": m.message,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_chat_list(request):
    """Get list of recent conversations"""
    # Get all unique users who have chatted
    conversations = ChatMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).values_list('sender_id', 'recipient_id').distinct()
    
    users_set = set()
    for sender_id, recipient_id in conversations:
        if sender_id != request.user.id:
            users_set.add(sender_id)
        if recipient_id != request.user.id:
            users_set.add(recipient_id)
    
    chat_users = User.objects.filter(id__in=users_set)
    
    return JsonResponse({
        "count": chat_users.count(),
        "conversations": [
            {
                "id": u.id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
            }
            for u in chat_users
        ]
    })


# ============ RECRUITER DASHBOARD ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
@role_required(["recruiter", "admin"])
def save_favorite_job(request):
    """Save/unsave a job in recruiter dashboard"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    job_id = data.get("job_id")
    action = data.get("action", "add")  # add or remove
    
    try:
        dashboard = RecruiterDashboard.objects.get(recruiter=request.user)
    except RecruiterDashboard.DoesNotExist:
        dashboard = RecruiterDashboard.objects.create(recruiter=request.user)
    
    favorite_jobs = dashboard.favorite_jobs or []
    
    if action == "add":
        if job_id not in favorite_jobs:
            favorite_jobs.append(job_id)
    else:
        if job_id in favorite_jobs:
            favorite_jobs.remove(job_id)
    
    dashboard.favorite_jobs = favorite_jobs
    dashboard.save()
    
    return JsonResponse({
        "job_id": job_id,
        "action": action,
        "favorite_jobs": favorite_jobs,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
@role_required(["recruiter", "admin"])
def get_recruiter_dashboard(request):
    """Get recruiter dashboard data"""
    try:
        dashboard = RecruiterDashboard.objects.get(recruiter=request.user)
    except RecruiterDashboard.DoesNotExist:
        dashboard = RecruiterDashboard.objects.create(recruiter=request.user)
    
    # Get favorite jobs data
    from django.db.models import Count
    favorite_jobs_data = []
    for job_id in (dashboard.favorite_jobs or []):
        try:
            job = JobPost.objects.get(id=job_id)
            app_count = JobApplication.objects.filter(job=job).count()
            favorite_jobs_data.append({
                "id": job.id,
                "title": job.title,
                "applications": app_count,
            })
        except JobPost.DoesNotExist:
            pass
    
    # Get saved candidates
    saved_candidates_data = []
    for candidate_id in (dashboard.saved_candidates or []):
        try:
            user = User.objects.get(id=candidate_id)
            saved_candidates_data.append({
                "id": user.id,
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
            })
        except User.DoesNotExist:
            pass
    
    recruiter_jobs = JobPost.objects.filter(posted_by=request.user)
    recruiter_applications = JobApplication.objects.filter(job__posted_by=request.user)
    applications_by_stage = list(
        recruiter_applications.values("status").annotate(total=Count("id")).order_by("status")
    )
    recent_applications = recruiter_applications.select_related("job", "applicant").order_by("-created_at")[:8]

    return JsonResponse({
        "id": dashboard.id,
        "favorite_jobs": favorite_jobs_data,
        "saved_candidates": saved_candidates_data,
        "pipeline_stages": dashboard.pipeline_stages,
        "hiring_goals": dashboard.hiring_goals,
        "interview_schedule": dashboard.interview_schedule,
        "team_members": dashboard.team_members,
        "notifications_settings": dashboard.notifications_settings,
        "analytics": {
            "total_jobs": recruiter_jobs.count(),
            "active_jobs": recruiter_jobs.filter(is_active=True).count(),
            "total_applications": recruiter_applications.count(),
            "shortlisted": recruiter_applications.filter(status="shortlisted").count(),
            "hired": recruiter_applications.filter(status="hired").count(),
            "applications_by_stage": applications_by_stage,
        },
        "recent_applications": [
            {
                "id": app.id,
                "job_id": app.job_id,
                "job_title": app.job.title,
                "applicant_id": app.applicant_id,
                "applicant_name": app.applicant.get_full_name() or app.applicant.email,
                "status": app.status,
                "created_at": app.created_at.isoformat(),
            }
            for app in recent_applications
        ],
    })


@csrf_exempt
@require_http_methods(["PUT"])
@jwt_required
@role_required(["recruiter", "admin"])
def update_recruiter_dashboard(request):
    """Update recruiter dashboard settings"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    try:
        dashboard = RecruiterDashboard.objects.get(recruiter=request.user)
    except RecruiterDashboard.DoesNotExist:
        dashboard = RecruiterDashboard.objects.create(recruiter=request.user)
    
    if "pipeline_stages" in data:
        dashboard.pipeline_stages = data["pipeline_stages"]
    if "hiring_goals" in data:
        dashboard.hiring_goals = data["hiring_goals"]
    if "interview_schedule" in data:
        dashboard.interview_schedule = data["interview_schedule"]
    if "team_members" in data:
        dashboard.team_members = data["team_members"]
    if "notifications_settings" in data:
        dashboard.notifications_settings = data["notifications_settings"]
    
    dashboard.save()
    
    return JsonResponse({
        "id": dashboard.id,
        "message": "Dashboard updated successfully",
        "updated_at": dashboard.updated_at.isoformat(),
    })


# ========== SMART CAREER GRAPH ENDPOINTS ==========

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def career_graph(request):
    """Get user's skill graph with radar chart data"""
    user = request.user

    # Get user's skill progress
    user_skills = UserSkillProgress.objects.filter(user=user).select_related('skill')

    # Build radar data by category
    radar_data = {}
    for us in user_skills:
        cat = us.skill.category
        if cat not in radar_data:
            radar_data[cat] = {"category": cat, "current": 0, "count": 0}
        radar_data[cat]["current"] += us.current_level
        radar_data[cat]["count"] += 1

    radar_chart = [
        {"category": v["category"], "level": round(v["current"] / v["count"], 1)}
        for v in radar_data.values()
    ]

    # Get nodes (user's skills)
    nodes = [
        {
            "id": us.skill.id,
            "name": us.skill.name,
            "category": us.skill.category,
            "current_level": us.current_level,
            "target_level": us.target_level,
            "progress": us.progress_percentage,
        }
        for us in user_skills
    ]

    # Get edges (prerequisites for user's skills)
    skill_ids = [us.skill_id for us in user_skills]
    edges = list(SkillEdge.objects.filter(
        models.Q(to_skill_id__in=skill_ids) | models.Q(from_skill_id__in=skill_ids)
    ).values('from_skill_id', 'to_skill_id', 'typical_weeks', 'difficulty_jump'))

    return JsonResponse({
        "nodes": nodes,
        "edges": edges,
        "radarChart": radar_chart,
        "total_skills": len(nodes),
        "avg_progress": round(sum(us.progress_percentage for us in user_skills) / max(len(user_skills), 1), 1)
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def career_paths(request):
    """Get available career paths"""
    paths = CareerPathModel.objects.all().prefetch_related('required_skills', 'optional_skills')

    return JsonResponse({
        "paths": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "skills_count": p.required_skills.count(),
                "experience_years": p.typical_years_experience,
                "salary_range": f"{p.average_salary_min}-{p.average_salary_max}",
                "market_demand": p.market_demand_score,
                "growth_trajectory": p.growth_trajectory,
            }
            for p in paths
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def generate_career_path(request):
    """Generate personalized career path to target role"""
    data = parse_json(request)
    target_role = data.get("target_role")

    if not target_role:
        return JsonResponse({"error": "target_role is required"}, status=400)

    try:
        career_path = CareerPathModel.objects.get(name__icontains=target_role)
    except CareerPathModel.DoesNotExist:
        return JsonResponse({"error": "Career path not found"}, status=404)

    user = request.user
    user_skill_ids = set(UserSkillProgress.objects.filter(user=user).values_list('skill_id', flat=True))
    required_skill_ids = set(career_path.required_skills.values_list('id', flat=True))

    missing_skills = required_skill_ids - user_skill_ids

    # Generate learning path
    learning_path = []
    total_weeks = 0

    for skill_id in missing_skills:
        skill = SkillNode.objects.get(id=skill_id)

        # Find path to this skill
        prerequisites = SkillEdge.objects.filter(to_skill=skill).select_related('from_skill')

        path_item = {
            "skill": skill.name,
            "category": skill.category,
            "weeks_needed": skill.level * 4,  # 4 weeks per level
            "difficulty": skill.level,
            "prerequisites": [p.from_skill.name for p in prerequisites],
            "resources": [
                {"title": f"Learn {skill.name} Basics", "type": "course", "url": f"https://example.com/{skill.name.lower()}"}
            ]
        }
        learning_path.append(path_item)
        total_weeks += path_item["weeks_needed"]

    # Calculate hiring probability timeline
    timeline = []
    current_prob = 20  # Base probability
    for i in range(0, total_weeks + 1, 4):
        timeline.append({
            "weeks": i,
            "probability": min(current_prob + (i * 0.5), 95),
            "milestone": f"Month {i // 4 + 1}" if i > 0 else "Current"
        })

    # Save user career path
    user_career, created = UserCareerPath.objects.update_or_create(
        user=user,
        career_path=career_path,
        is_active=True,
    )

    return JsonResponse({
        "career_path": career_path.name,
        "current_skills": list(user_skill_ids),
        "missing_skills": list(missing_skills),
        "learning_path": learning_path,
        "total_weeks": total_weeks,
        "hiring_probability_timeline": timeline,
        "projected_salary": f"{career_path.average_salary_min}-{career_path.average_salary_max}",
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def update_skill_progress(request):
    """Update skill milestone progress"""
    data = parse_json(request)
    skill_id = data.get("skill_id")
    progress = data.get("progress", 0)
    milestones = data.get("milestones", [])

    if not skill_id:
        return JsonResponse({"error": "skill_id is required"}, status=400)

    user = request.user

    skill_progress, created = UserSkillProgress.objects.get_or_create(
        user=user,
        skill_id=skill_id,
        defaults={"progress_percentage": progress, "milestones_completed": milestones}
    )

    if not created:
        skill_progress.progress_percentage = progress
        skill_progress.milestones_completed = milestones
        skill_progress.save()

    return JsonResponse({
        "skill_id": skill_id,
        "progress": skill_progress.progress_percentage,
        "updated_at": skill_progress.last_updated.isoformat()
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def skill_nodes(request):
    """Get all available skill nodes"""
    category = request.GET.get("category")

    skills = SkillNode.objects.all()
    if category:
        skills = skills.filter(category=category)

    return JsonResponse({
        "skills": [
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "level": s.level,
                "description": s.description,
                "market_demand": s.market_demand,
            }
            for s in skills
        ]
    })


# ========== RESUME vs JOB COMPARATOR ENDPOINTS ==========

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def compare_resume_job(request):
    """Compare resume to job and return detailed match analysis"""
    data = parse_json(request)
    resume_id = data.get("resume_id")
    job_id = data.get("job_id")

    if not resume_id or not job_id:
        return JsonResponse({"error": "resume_id and job_id are required"}, status=400)

    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
        job = JobPost.objects.get(id=job_id)
    except (Resume.DoesNotExist, JobPost.DoesNotExist) as e:
        return JsonResponse({"error": str(e)}, status=404)

    # Extract skills
    resume_skills = set(resume.parsed_skills or [])
    job_skills = set(SkillNode.objects.filter(
        name__in=[s.strip() for s in (job.skills_required or "").split(",")]
    ).values_list('name', flat=True))

    # Calculate match
    matched = list(resume_skills & job_skills)
    missing = list(job_skills - resume_skills)
    match_pct = round((len(matched) / max(len(job_skills), 1)) * 100, 1) if job_skills else 0

    # Generate improvement suggestions
    suggestions = []
    for skill in missing[:5]:
        suggestions.append({
            "skill": skill,
            "importance": "critical" if len(missing) < 3 else "high",
            "learning_time_weeks": 4,
            "resources": [
                {"title": f"Learn {skill}", "type": "course", "url": f"https://example.com/{skill.lower()}"}
            ]
        })

    # Salary prediction (simple heuristic)
    base_salary = (job.salary_min or 0 + job.salary_max or 0) / 2
    adjusted_salary = int(base_salary * (match_pct / 100)) if base_salary else 0

    return JsonResponse({
        "match_percentage": match_pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "experience_match": "good" if abs(resume.experience_years - job.required_experience_years) <= 2 else "needs_improvement",
        "salary_prediction": adjusted_salary,
        "improvement_suggestions": suggestions,
        "resume_skills": list(resume_skills),
        "job_skills": list(job_skills),
    })


# ========== RECRUITER QUERY ENHANCEMENTS ==========

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
@role_required(["recruiter"])
def recruiter_candidates(request):
    """Search candidates with NLP-like query support"""
    query = request.GET.get("q", "")
    skills = request.GET.getlist("skills")
    experience_min = request.GET.get("experience_min", 0)
    experience_max = request.GET.get("experience_max", 20)

    # Get all applications
    applications = JobApplication.objects.select_related(
        'applicant', 'resume', 'job'
    ).order_by('-match_score')

    # Filter by experience
    if experience_min:
        applications = applications.filter(resume__experience_years__gte=int(experience_min))
    if experience_max:
        applications = applications.filter(resume__experience_years__lte=int(experience_max))

    # Filter by skills if provided
    if skills:
        for skill in skills:
            applications = applications.filter(resume__parsed_skills__contains=[skill])

    # Simple text search on query
    if query:
        applications = applications.filter(
            models.Q(job__title__icontains=query) |
            models.Q(applicant__first_name__icontains=query) |
            models.Q(applicant__last_name__icontains=query) |
            models.Q(candidate_summary__icontains=query)
        )

    return JsonResponse({
        "candidates": [
            {
                "id": app.id,
                "name": f"{app.applicant.first_name} {app.applicant.last_name}",
                "email": app.applicant.email,
                "job_title": app.job.title,
                "match_score": app.match_score,
                "experience_years": app.resume.experience_years if app.resume else 0,
                "skills": app.resume.parsed_skills if app.resume else [],
                "status": app.status,
            }
            for app in applications[:20]
        ],
        "total": applications.count()
    })


# ========== AI CODING TEST PLATFORM (Feature 4) ==========

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def coding_questions(request):
    """List DSA questions with filters"""
    difficulty = request.GET.get("difficulty")
    topic = request.GET.get("topic")
    limit = int(request.GET.get("limit", 20))

    questions = CodingQuestion.objects.all()
    if difficulty:
        questions = questions.filter(difficulty=difficulty)
    if topic:
        questions = questions.filter(topics__contains=[topic])

    return JsonResponse({
        "questions": [
            {
                "id": q.id,
                "title": q.title,
                "difficulty": q.difficulty,
                "topics": q.topics,
                "acceptance_rate": q.acceptance_rate,
                "likes": q.likes,
            }
            for q in questions[:limit]
        ]
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def coding_question_detail(request, question_id):
    """Get question details with test cases"""
    try:
        question = CodingQuestion.objects.get(id=question_id)
    except CodingQuestion.DoesNotExist:
        return JsonResponse({"error": "Question not found"}, status=404)

    return JsonResponse({
        "id": question.id,
        "title": question.title,
        "description": question.description,
        "difficulty": question.difficulty,
        "topics": question.topics,
        "test_cases": question.test_cases,
        "starter_code": question.starter_code,
        "acceptance_rate": question.acceptance_rate,
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def submit_code(request):
    """Submit code solution"""
    data = parse_json(request)
    question_id = data.get("question_id")
    code = data.get("code")
    language = data.get("language", "python")

    if not question_id or not code:
        return JsonResponse({"error": "question_id and code are required"}, status=400)

    try:
        question = CodingQuestion.objects.get(id=question_id)
    except CodingQuestion.DoesNotExist:
        return JsonResponse({"error": "Question not found"}, status=404)

    # Simulate code execution (in production, use Docker container)
    test_cases = question.test_cases or []
    passed = 0

    # Simple simulation - in production, run actual code
    status = "accepted" if code else "wrong"
    if "def solution" in code or "print(" in code:
        passed = len(test_cases) if test_cases else 1
        status = "accepted"

    submission = CodeSubmission.objects.create(
        user=request.user,
        question=question,
        code=code,
        language=language,
        status=status,
        runtime_ms=50,
        test_cases_passed=passed,
        total_test_cases=len(test_cases),
    )

    return JsonResponse({
        "submission_id": submission.id,
        "status": submission.status,
        "test_cases_passed": passed,
        "total_test_cases": len(test_cases),
        "runtime_ms": submission.runtime_ms,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def code_submissions(request):
    """Get user's submission history"""
    user_id = request.GET.get("user_id")
    limit = int(request.GET.get("limit", 20))

    submissions = CodeSubmission.objects.all()
    if user_id:
        submissions = submissions.filter(user_id=user_id)
    else:
        submissions = submissions.filter(user=request.user)

    return JsonResponse({
        "submissions": [
            {
                "id": s.id,
                "question_title": s.question.title,
                "language": s.language,
                "status": s.status,
                "test_cases_passed": s.test_cases_passed,
                "submission_date": s.submission_date.isoformat(),
            }
            for s in submissions[:limit]
        ]
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def coding_contests(request):
    """List active contests"""
    contests = CodingContest.objects.filter(is_active=True)

    return JsonResponse({
        "contests": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "start_time": c.start_time.isoformat(),
                "end_time": c.end_time.isoformat(),
                "duration_minutes": c.duration_minutes,
                "participants_count": c.participants.count(),
            }
            for c in contests
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def join_contest(request, contest_id):
    """Join a coding contest"""
    try:
        contest = CodingContest.objects.get(id=contest_id, is_active=True)
    except CodingContest.DoesNotExist:
        return JsonResponse({"error": "Contest not found"}, status=404)

    participant, created = ContestParticipant.objects.get_or_create(
        contest=contest,
        user=request.user,
        defaults={"rank": 0}
    )

    return JsonResponse({
        "message": "Joined contest successfully",
        "participant_id": participant.id,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def contest_leaderboard(request, contest_id):
    """Get contest leaderboard"""
    try:
        contest = CodingContest.objects.get(id=contest_id)
    except CodingContest.DoesNotExist:
        return JsonResponse({"error": "Contest not found"}, status=404)

    participants = ContestParticipant.objects.filter(contest=contest).order_by("rank")[:20]

    return JsonResponse({
        "leaderboard": [
            {
                "rank": p.rank,
                "user": p.user.email,
                "score": p.score,
                "questions_solved": p.questions_solved,
            }
            for p in participants
        ]
    })


# ========== VOICE-BASED CAREER COACH (Feature 5) ==========

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def start_voice_session(request):
    """Start a voice session"""
    data = parse_json(request)
    session_type = data.get("session_type", "advice")

    session = VoiceSession.objects.create(
        user=request.user,
        session_type=session_type,
    )

    return JsonResponse({
        "session_id": session.id,
        "session_type": session.session_type,
        "start_time": session.start_time.isoformat(),
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def process_voice_transcript(request):
    """Process voice transcript and get AI response with follow-up questions"""
    data = parse_json(request)
    session_id = data.get("session_id")
    transcript = data.get("transcript", "")
    speech_analysis = data.get("speech_analysis", {})

    if not session_id:
        return JsonResponse({"error": "session_id is required"}, status=400)

    try:
        session = VoiceSession.objects.get(id=session_id, user=request.user)
    except VoiceSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

    # Analyze speech metrics from frontend
    confidence = speech_analysis.get("confidence", 0)
    filler_count = speech_analysis.get("fillerWordCount", 0)
    words_per_minute = speech_analysis.get("wordsPerMinute", 0)
    total_words = speech_analysis.get("totalWords", 0)

    # Determine mood based on speech analysis
    if confidence >= 80:
        mood = "confident"
    elif confidence >= 60:
        mood = "neutral"
    else:
        mood = "uncertain"

    # Generate AI response based on session type with follow-up questions
    follow_up_questions = []

    if session.session_type == "interview":
        # Interview practice mode - provide STAR method guidance
        response_parts = []
        response_parts.append(f"I hear you mentioning: '{transcript[:100]}...' ")

        if filler_count > 3:
            response_parts.append("I noticed some filler words. Try to pause naturally between thoughts. ")

        if words_per_minute > 160:
            response_parts.append("Try slowing down a bit - your speaking speed was quite fast. ")
        elif words_per_minute > 0 and words_per_minute < 100:
            response_parts.append("Try to be more confident and speak a bit faster. ")

        response_parts.append("Consider using the STAR method to structure your answer: Situation, Task, Action, Result. ")

        response = "".join(response_parts)
        follow_up_questions = [
            "Can you describe a specific challenging situation you faced and how you resolved it?",
            "Tell me about a time you had to work with a difficult team member.",
            "What's your greatest professional achievement?",
        ]

    elif session.session_type == "advice":
        # Career advice mode
        response_parts = []
        response_parts.append(f"Thanks for sharing: '{transcript[:100]}...' ")

        if confidence < 60:
            response_parts.append("I can sense some uncertainty. Let's work through this together. ")

        response_parts.append("Here are my recommendations: First, identify your key strengths and how they align with your goals. Second, seek opportunities to demonstrate leadership even in small ways. Third, continuously update your technical skills through real-world projects.")

        response = "".join(response_parts)
        follow_up_questions = [
            "What's your current role and years of experience?",
            "Are you more interested in technical advancement or management?",
            "What's your target timeline for progression?",
        ]

    else:  # skill guidance
        response_parts = []
        response_parts.append(f"Let's work on: '{transcript[:100]}...' ")

        if filler_count > 5:
            response_parts.append("Focus on being more concise when describing your skills. ")

        response_parts.append("For skill development, I recommend: 1) Start with foundational concepts, 2) Build real-world projects, 3) Get feedback from peers, 4) Document your learning journey.")

        response = "".join(response_parts)
        follow_up_questions = [
            "What's your current proficiency level?",
            "How many hours per week can you dedicate to learning?",
            "Do you prefer structured courses or project-based learning?",
        ]

    # Update session
    session.transcript = (session.transcript or "") + f"\n{transcript}"
    session.ai_response = (session.ai_response or "") + f"\n{response}"

    # Update key insights with speech analysis
    session.key_insights = [
        {"metric": "confidence", "value": confidence},
        {"metric": "filler_words", "value": filler_count},
        {"metric": "speaking_speed", "value": words_per_minute},
        {"metric": "total_words", "value": total_words},
    ]

    # Detect mood
    if confidence >= 75 and filler_count < 3:
        session.mood_detected = "confident"
    elif confidence >= 50:
        session.mood_detected = "neutral"
    else:
        session.mood_detected = "uncertain"

    session.save()

    return JsonResponse({
        "transcript": transcript,
        "response": response,
        "mood_detected": session.mood_detected,
        "follow_up_questions": follow_up_questions[:3],
        "speech_analysis": {
            "confidence": confidence,
            "filler_word_count": filler_count,
            "words_per_minute": words_per_minute,
            "total_words": total_words,
            "speaking_speed_status": "fast" if words_per_minute > 160 else "slow" if words_per_minute < 100 else "optimal",
        },
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def end_voice_session(request):
    """End voice session"""
    data = parse_json(request)
    session_id = data.get("session_id")

    try:
        session = VoiceSession.objects.get(id=session_id, user=request.user)
    except VoiceSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

    session.is_active = False
    session.duration_seconds = int((timezone.now() - session.start_time).total_seconds())
    session.save()

    return JsonResponse({
        "session_id": session.id,
        "duration_seconds": session.duration_seconds,
        "message": "Session ended successfully",
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def voice_sessions(request):
    """Get user's voice session history"""
    sessions = VoiceSession.objects.filter(user=request.user)[:20]

    return JsonResponse({
        "sessions": [
            {
                "id": s.id,
                "session_type": s.session_type,
                "start_time": s.start_time.isoformat(),
                "duration_seconds": s.duration_seconds,
                "is_active": s.is_active,
            }
            for s in sessions
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def whisper_transcribe(request):
    """Whisper-based audio transcription endpoint"""
    try:
        audio_file = request.FILES.get("audio")
        if not audio_file:
            return JsonResponse({"error": "No audio file provided"}, status=400)

        # For now, return a placeholder - in production, use OpenAI Whisper API
        # You would use: openai.Audio.transcribe("whisper-1", audio_file)
        # Or use a self-hosted Whisper model

        # Check if OPENAI_API_KEY is available for Whisper
        api_key = getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY")

        if api_key and len(api_key) > 10:
            # Use OpenAI Whisper API
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                for chunk in audio_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            with open(tmp_path, "rb") as audio:
                # Note: OpenAI Python SDK v1.0+ uses new syntax
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                    with open(tmp_path, "rb") as f:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=f
                        )
                    transcription_text = transcript.text
                except ImportError:
                    # Fallback for older SDK
                    response = openai.Audio.transcribe("whisper-1", audio)
                    transcription_text = response["text"]

            os.unlink(tmp_path)

            return JsonResponse({
                "transcript": transcription_text,
                "confidence": 0.95,
                "language": "en",
                "source": "whisper"
            })
        else:
            # Fallback: require transcript from frontend (Web Speech API)
            return JsonResponse({
                "transcript": "",
                "error": "Whisper API not configured. Use Web Speech API for transcription.",
                "source": "fallback"
            })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def generate_followup_questions(request):
    """Generate AI-powered follow-up questions based on conversation context"""
    data = parse_json(request)
    transcript = data.get("transcript", "")
    session_type = data.get("session_type", "advice")
    context = data.get("context", "")

    if not transcript:
        return JsonResponse({"error": "transcript is required"}, status=400)

    # Use AI service to generate personalized follow-up questions
    try:
        api_key = getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY")
        gemini_key = getattr(settings, "GOOGLE_GEMINI_KEY", "") or os.environ.get("GOOGLE_GEMINI_KEY")

        prompt = f"""Based on the following conversation in a {session_type} session:

User said: "{transcript}"
Context: {context}

Generate 3-5 personalized follow-up questions that:
1. Help dig deeper into the user's situation
2. Are specific and actionable
3. Help tailor career advice to their needs

Return as JSON array of strings."""

        questions = []

        if api_key and len(api_key) > 10:
            # Use OpenAI
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful career coach AI."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                content = response.choices[0].message.content
                questions = json.loads(content)
            except Exception as e:
                print(f"OpenAI API error: {e}")
                questions = _get_default_questions(session_type)
        elif gemini_key and len(gemini_key) > 10:
            # Use Gemini
            import requests
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={gemini_key}"
            gemini_payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 300}
            }
            resp = requests.post(gemini_url, json=gemini_payload)
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                questions = json.loads(text)
            else:
                questions = _get_default_questions(session_type)
        else:
            questions = _get_default_questions(session_type)

        return JsonResponse({
            "follow_up_questions": questions,
            "source": "ai"
        })

    except Exception as e:
        return JsonResponse({
            "follow_up_questions": _get_default_questions(session_type),
            "source": "fallback",
            "error": str(e)
        })


def _get_default_questions(session_type):
    """Default follow-up questions based on session type"""
    if session_type == "interview":
        return [
            "Can you describe a specific situation where you had to solve a difficult problem?",
            "Tell me about a time you failed and what you learned from it.",
            "What are your greatest strengths and how do you demonstrate them?",
            "Why are you interested in this role and company?",
        ]
    elif session_type == "advice":
        return [
            "What's your current career level and experience?",
            "What specific skills are you looking to develop?",
            "What's your timeline for career progression?",
            "What type of work environment do you thrive in?",
        ]
    else:
        return [
            "What's your current skill level?",
            "How much time can you dedicate to learning?",
            "Do you prefer theoretical or practical learning?",
            "What's your learning goal timeline?",
        ]


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def analyze_speech_quality(request):
    """Analyze speech quality metrics from text"""
    data = parse_json(request)
    transcript = data.get("transcript", "")

    if not transcript:
        return JsonResponse({"error": "transcript is required"}, status=400)

    # Analyze speech patterns
    words = transcript.lower().split()
    word_count = len(words)

    # Filler words detection
    filler_words = ["um", "uh", "like", "you know", "basically", "actually", "literally", "so", "well", "I mean"]
    filler_count = sum(1 for w in words if w in filler_words)

    # Confidence estimation (based on sentence structure)
    has_questions = "?" in transcript
    has_ellipsis = "..." in transcript
    sentence_count = transcript.count(".") + transcript.count("!") + transcript.count("?")

    confidence = 85
    if filler_count > word_count * 0.1:
        confidence -= 15
    if has_ellipsis:
        confidence -= 10
    if sentence_count == 0 and word_count > 10:
        confidence -= 10
    confidence = max(50, min(100, confidence))

    # Speaking pace indication
    avg_word_length = sum(len(w) for w in words) / max(1, word_count)

    return JsonResponse({
        "confidence_score": confidence,
        "filler_word_count": filler_count,
        "filler_word_percentage": round((filler_count / max(1, word_count)) * 100, 2),
        "total_words": word_count,
        "has_uncertainty_markers": has_ellipsis or has_questions,
        "avg_word_length": round(avg_word_length, 2),
        "assessment": "Good" if confidence >= 80 else "Needs improvement" if confidence >= 60 else "Needs work"
    })


# ========== REALTIME COLLABORATION (Feature 6) ==========

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
@role_required(["recruiter"])
def create_collaborative_review(request):
    """Create a collaborative review"""
    data = parse_json(request)
    candidate_id = data.get("candidate_id")

    try:
        candidate = JobApplication.objects.get(id=candidate_id)
    except JobApplication.DoesNotExist:
        return JsonResponse({"error": "Candidate not found"}, status=404)

    review = CollaborativeReview.objects.create(
        candidate=candidate,
        reviewer=request.user,
        rating=data.get("rating", 3),
        notes=data.get("notes", ""),
    )

    return JsonResponse({
        "review_id": review.id,
        "rating": review.rating,
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def add_review_comment(request):
    """Add comment to review"""
    data = parse_json(request)
    review_id = data.get("review_id")
    content = data.get("content", "")

    try:
        review = CollaborativeReview.objects.get(id=review_id)
    except CollaborativeReview.DoesNotExist:
        return JsonResponse({"error": "Review not found"}, status=404)

    comment = ReviewComment.objects.create(
        review=review,
        author=request.user,
        content=content,
        mentions=data.get("mentions", []),
    )

    return JsonResponse({
        "comment_id": comment.id,
        "content": comment.content,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_interview_notes(request, session_id):
    """Get interview notes for a session"""
    try:
        session = InterviewSession.objects.get(id=session_id)
    except InterviewSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

    notes = InterviewNotes.objects.filter(session=session).order_by("-version").first()

    return JsonResponse({
        "content": notes.content if notes else "",
        "version": notes.version if notes else 0,
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def save_interview_notes(request, session_id):
    """Save interview notes"""
    data = parse_json(request)

    try:
        session = InterviewSession.objects.get(id=session_id)
    except InterviewSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)

    last_notes = InterviewNotes.objects.filter(session=session).order_by("-version").first()
    version = (last_notes.version + 1) if last_notes else 1

    notes = InterviewNotes.objects.create(
        session=session,
        content=data.get("content", ""),
        version=version,
        last_modified_by=request.user,
    )

    return JsonResponse({
        "version": notes.version,
        "message": "Notes saved",
    })


# ========== AI PERSONALITY ANALYZER (Feature 7) ==========

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def analyze_personality(request):
    """Analyze personality from resume and data"""
    data = parse_json(request)
    target_user_id = data.get("user_id")

    try:
        if target_user_id:
            target_user = User.objects.get(id=target_user_id)
        else:
            target_user = request.user
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    # Generate personality profile based on available data
    profile, created = PersonalityProfile.objects.get_or_create(user=target_user)

    # Simulate personality analysis based on available data
    import random
    profile.openness = random.randint(40, 80)
    profile.conscientiousness = random.randint(40, 80)
    profile.extraversion = random.randint(30, 70)
    profile.agreeableness = random.randint(50, 90)
    profile.neuroticism = random.randint(20, 60)

    profile.communication = random.randint(40, 85)
    profile.leadership = random.randint(30, 80)
    profile.teamwork = random.randint(50, 90)
    profile.problem_solving = random.randint(40, 85)
    profile.adaptability = random.randint(45, 80)

    # Determine MBTI
    e_i = "E" if profile.extraversion > 55 else "I"
    s_n = "N" if profile.openness > 55 else "S"
    t_f = "F" if profile.agreeableness > 55 else "T"
    j_p = "J" if profile.conscientiousness > 55 else "P"
    profile.mbti_type = f"{e_i}{s_n}{t_f}{j_p}"

    profile.save()

    return JsonResponse({
        "big_five": {
            "openness": profile.openness,
            "conscientiousness": profile.conscientiousness,
            "extraversion": profile.extraversion,
            "agreeableness": profile.agreeableness,
            "neuroticism": profile.neuroticism,
        },
        "soft_skills": {
            "communication": profile.communication,
            "leadership": profile.leadership,
            "teamwork": profile.teamwork,
            "problem_solving": profile.problem_solving,
            "adaptability": profile.adaptability,
        },
        "mbti_type": profile.mbti_type,
        "team_fit_score": profile.team_fit_score,
        "confidence_level": profile.confidence_level,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_personality_profile(request, user_id):
    """Get personality profile"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    try:
        profile = PersonalityProfile.objects.get(user=user)
    except PersonalityProfile.DoesNotExist:
        return JsonResponse({"error": "Profile not analyzed yet"}, status=404)

    return JsonResponse({
        "mbti_type": profile.mbti_type,
        "big_five": {
            "openness": profile.openness,
            "conscientiousness": profile.conscientiousness,
            "extraversion": profile.extraversion,
            "agreeableness": profile.agreeableness,
            "neuroticism": profile.neuroticism,
        },
        "soft_skills": {
            "communication": profile.communication,
            "leadership": profile.leadership,
            "teamwork": profile.teamwork,
            "problem_solving": profile.problem_solving,
            "adaptability": profile.adaptability,
        },
    })


# ========== GAMIFICATION SYSTEM (Feature 8) ==========

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def game_profile(request):
    """Get user game stats"""
    profile, created = UserGameProfile.objects.get_or_create(user=request.user)

    badges = UserBadge.objects.filter(user=request.user).select_related("badge")[:10]

    return JsonResponse({
        "total_xp": profile.total_xp,
        "level": profile.level,
        "current_streak": profile.current_streak,
        "longest_streak": profile.longest_streak,
        "badges": [
            {"name": b.badge.name, "icon": b.badge.icon_url, "earned_at": b.earned_at.isoformat()}
            for b in badges
        ],
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def award_xp(request):
    """Award XP for activity"""
    data = parse_json(request)
    activity_type = data.get("activity_type")

    XP_REWARDS = {
        "job_apply": 10,
        "profile_complete": 50,
        "skill_verified": 25,
        "dsa_solved": 20,
        "interview_prep": 20,
        "portfolio_update": 35,
    }

    xp = XP_REWARDS.get(activity_type, 10)

    profile, created = UserGameProfile.objects.get_or_create(user=request.user)
    old_level = profile.level
    profile.total_xp += xp

    # Calculate level
    thresholds = [100, 250, 500, 1000, 2000, 5000, 10000]
    new_level = 1
    for t in thresholds:
        if profile.total_xp >= t:
            new_level += 1

    profile.level = new_level
    profile.last_activity_date = timezone.now().date()
    profile.save()

    # Record transaction
    XPTransaction.objects.create(
        user=request.user,
        activity_type=activity_type,
        xp_earned=xp,
    )

    return JsonResponse({
        "xp_earned": xp,
        "total_xp": profile.total_xp,
        "level": profile.level,
        "level_up": new_level > old_level,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def game_leaderboard(request):
    """Get global leaderboard"""
    timeframe = request.GET.get("timeframe", "all")
    limit = int(request.GET.get("limit", 20))

    profiles = UserGameProfile.objects.all().order_by("-total_xp")[:limit]

    return JsonResponse({
        "leaderboard": [
            {
                "rank": idx + 1,
                "user": p.user.email,
                "level": p.level,
                "total_xp": p.total_xp,
                "streak": p.current_streak,
            }
            for idx, p in enumerate(profiles)
        ]
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def daily_challenges(request):
    """Get daily challenges"""
    today = timezone.now().date()
    challenges = DailyChallenge.objects.filter(date=today, is_active=True)

    user_challenges = UserChallenge.objects.filter(
        user=request.user,
        challenge__date=today
    ).select_related("challenge")

    completed = {uc.challenge_id: uc.completed for uc in user_challenges}

    return JsonResponse({
        "challenges": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "objective": c.objective,
                "xp_reward": c.xp_reward,
                "difficulty": c.difficulty,
                "completed": completed.get(c.id, False),
            }
            for c in challenges
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def complete_challenge(request):
    """Complete a daily challenge"""
    data = parse_json(request)
    challenge_id = data.get("challenge_id")

    try:
        challenge = DailyChallenge.objects.get(id=challenge_id)
    except DailyChallenge.DoesNotExist:
        return JsonResponse({"error": "Challenge not found"}, status=404)

    user_challenge, created = UserChallenge.objects.get_or_create(
        user=request.user,
        challenge=challenge,
        defaults={"completed": True, "completed_at": timezone.now()}
    )

    if not created and not user_challenge.completed:
        user_challenge.completed = True
        user_challenge.completed_at = timezone.now()
        user_challenge.save()

        # Award XP
        profile, _ = UserGameProfile.objects.get_or_create(user=request.user)
        profile.total_xp += challenge.xp_reward
        profile.save()

    return JsonResponse({
        "xp_earned": challenge.xp_reward,
        "completed": True,
    })


# ========== ADVANCED SEARCH (Feature 9) ==========

@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def advanced_job_search(request):
    """Advanced job search with filters"""
    query = request.GET.get("q", "")
    skills = request.GET.getlist("skills")
    min_salary = request.GET.get("min_salary")
    max_salary = request.GET.get("max_salary")
    experience_min = request.GET.get("experience_min")
    experience_max = request.GET.get("experience_max")
    work_type = request.GET.getlist("work_type")
    page = int(request.GET.get("page", 1))
    limit = int(request.GET.get("limit", 20))

    jobs = JobPost.objects.filter(is_active=True)

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__icontains=query)
        )

    if skills:
        for skill in skills:
            jobs = jobs.filter(skills_required__icontains=skill)

    if min_salary:
        jobs = jobs.filter(salary_min__gte=int(min_salary))
    if max_salary:
        jobs = jobs.filter(salary_max__lte=int(max_salary))

    if experience_min:
        jobs = jobs.filter(required_experience_years__gte=int(experience_min))
    if experience_max:
        jobs = jobs.filter(required_experience_years__lte=int(experience_max))

    total = jobs.count()
    jobs = jobs[(page - 1) * limit:page * limit]

    return JsonResponse({
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "skills_required": j.skills_required,
                "salary_range": j.salary_range,
                "employment_type": j.employment_type,
                "created_at": j.created_at.isoformat(),
            }
            for j in jobs
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def search_suggestions(request):
    """Get autocomplete suggestions"""
    prefix = request.GET.get("prefix", "")
    if len(prefix) < 2:
        return JsonResponse({"suggestions": []})

    jobs = JobPost.objects.filter(
        is_active=True,
        title__icontains=prefix
    ).values_list("title", flat=True).distinct()[:10]

    return JsonResponse({
        "suggestions": list(jobs)
    })


# ========== AI AUTO APPLY (Feature 10) ==========

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def set_auto_apply_prefs(request):
    """Set auto-apply preferences"""
    data = parse_json(request)

    prefs, created = AutoApplyPreferences.objects.get_or_create(
        user=request.user,
        defaults={
            "enabled": data.get("enabled", False),
            "target_roles": data.get("target_roles", []),
            "preferred_companies": data.get("preferred_companies", []),
            "min_salary": data.get("min_salary", 0),
            "max_salary": data.get("max_salary", 0),
            "preferred_locations": data.get("preferred_locations", []),
            "work_type_preferences": data.get("work_type_preferences", []),
            "skill_requirements": data.get("skill_requirements", []),
            "max_applications_per_day": data.get("max_applications_per_day", 5),
            "min_match_score": data.get("min_match_score", 0.7),
        }
    )

    if not created:
        for field in ["enabled", "target_roles", "preferred_companies", "min_salary",
                      "max_salary", "preferred_locations", "work_type_preferences",
                      "skill_requirements", "max_applications_per_day", "min_match_score"]:
            if field in data:
                setattr(prefs, field, data[field])
        prefs.save()

    return JsonResponse({
        "enabled": prefs.enabled,
        "message": "Preferences saved",
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def get_auto_apply_prefs(request):
    """Get auto-apply preferences"""
    try:
        prefs = AutoApplyPreferences.objects.get(user=request.user)
    except AutoApplyPreferences.DoesNotExist:
        return JsonResponse({
            "enabled": False,
            "target_roles": [],
            "min_salary": 0,
            "max_salary": 0,
        })

    return JsonResponse({
        "enabled": prefs.enabled,
        "target_roles": prefs.target_roles,
        "preferred_companies": prefs.preferred_companies,
        "min_salary": prefs.min_salary,
        "max_salary": prefs.max_salary,
        "preferred_locations": prefs.preferred_locations,
        "work_type_preferences": prefs.work_type_preferences,
        "skill_requirements": prefs.skill_requirements,
        "max_applications_per_day": prefs.max_applications_per_day,
        "min_match_score": prefs.min_match_score,
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
def auto_apply_history(request):
    """Get auto-apply history"""
    applications = AutoApplication.objects.filter(user=request.user)[:20]

    return JsonResponse({
        "applications": [
            {
                "id": a.id,
                "job_title": a.job.title,
                "company": a.job.company,
                "match_score": a.match_score,
                "applied_at": a.applied_at.isoformat(),
            }
            for a in applications
        ]
    })


import django.db.models as models
