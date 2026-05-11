import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Avg
from django.utils import timezone

from accounts.decorators import jwt_required, role_required
from accounts.models import User
from .models import (
    AIResumeAnalysis, AIMatchScore, AICareerCoach, ChatMessage,
    RecruiterDashboard, Resume, JobPost, JobApplication
)


def split_skill_keywords(text):
    return [part.strip().lower() for part in (text or "").split(",") if part.strip()]


def parse_json(request):
    try:
        return json.loads(request.body)
    except Exception:
        return None


# ============ AI RESUME ANALYZER ENDPOINTS ============

@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def analyze_resume_ai(request):
    """Perform detailed AI analysis on resume"""
    data = parse_json(request)
    if not data:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    resume_id = data.get("resume_id")
    
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
    except Resume.DoesNotExist:
        return JsonResponse({"error": "Resume not found"}, status=404)
    
    resume_text = resume.extracted_text.lower()
    
    # AI Analysis scoring
    strengths = []
    weaknesses = []
    recommendations = []
    
    # Check for strengths
    if len(resume_text) > 500:
        strengths.append("Comprehensive and detailed resume")
    if any(kw in resume_text for kw in ["experience", "project", "achieved", "led"]):
        strengths.append("Strong action verbs and achievement focus")
    if resume.extracted_skills and len(resume.extracted_skills) >= 5:
        strengths.append(f"Good skill diversity ({len(resume.extracted_skills)} skills)")
    
    # Check for weaknesses
    if len(resume_text) < 200:
        weaknesses.append("Resume is too brief - add more details")
    if not any(kw in resume_text for kw in ["experience", "project", "achievement"]):
        weaknesses.append("Lacks specific examples and achievements")
    if len(resume.extracted_skills) < 3:
        weaknesses.append("Limited skills listed - expand skill section")
    
    # Readability scoring
    readability_score = min(100, len(resume_text) // 5)
    if any(metric in resume_text for metric in ["increased", "reduced", "improved", "%", "$"]):
        readability_score += 15
    
    # Impact scoring
    impact_score = 70
    if resume.extracted_skills:
        impact_score += min(20, len(resume.extracted_skills) * 2)
    
    # Recommendations
    if readability_score < 70:
        recommendations.append("Add quantifiable metrics and specific achievements")
    if impact_score < 70:
        recommendations.append("Highlight more technical skills and projects")
    recommendations.append("Ensure consistent formatting and professional tone")
    
    overall_rating = (readability_score + impact_score) // 2
    
    analysis, created = AIResumeAnalysis.objects.update_or_create(
        resume=resume,
        defaults={
            "overall_rating": overall_rating,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "readability_score": readability_score,
            "impact_score": impact_score,
            "recommendations": recommendations,
            "detailed_feedback": f"Your resume scores well in readability and impact. {' '.join(recommendations)}",
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
        "created": created,
    })


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
        resume = Resume.objects.get(id=resume_id)
    except (JobPost.DoesNotExist, Resume.DoesNotExist):
        return JsonResponse({"error": "Job or resume not found"}, status=404)
    
    # Calculate match scores
    job_text = (job.title + " " + job.description + " " + job.skills_required).lower()
    resume_text = resume.extracted_text.lower()
    resume_skills = set(resume.extracted_skills) if resume.extracted_skills else set()
    job_skills = set(s.strip().lower() for s in job.skills_required.split(",") if s.strip())
    
    # Skills alignment
    matched_skills = resume_skills & job_skills
    skills_alignment = int((len(matched_skills) / max(len(job_skills), 1)) * 100)
    
    # Experience alignment
    exp_keywords = ["experience", "years", "senior", "lead", "manage"]
    exp_count = sum(1 for kw in exp_keywords if kw in resume_text)
    experience_alignment = min(100, exp_count * 20)
    
    # Culture fit (based on soft skills)
    soft_skills = ["communication", "teamwork", "leadership", "collaboration", "problem solving"]
    soft_match = sum(1 for skill in soft_skills if skill in resume_text)
    culture_fit = min(100, soft_match * 20)
    
    # Growth potential
    growth_potential = 70 + (len(resume_skills) * 2)
    growth_potential = min(100, growth_potential)
    
    # Overall match
    match_percentage = int((skills_alignment * 0.4 + experience_alignment * 0.3 + 
                           culture_fit * 0.2 + growth_potential * 0.1))
    
    missing_skills = list(job_skills - resume_skills)
    bonus_skills = [s for s in resume_skills if s not in job_skills]
    
    match, created = AIMatchScore.objects.update_or_create(
        job=job,
        resume=resume,
        defaults={
            "match_percentage": match_percentage,
            "skills_alignment": skills_alignment,
            "experience_alignment": experience_alignment,
            "culture_fit": culture_fit,
            "growth_potential": growth_potential,
            "matched_skills": list(matched_skills),
            "missing_skills": missing_skills,
            "bonus_skills": bonus_skills,
            "match_reasons": f"Strong alignment in {len(matched_skills)} key skills",
        }
    )
    
    return JsonResponse({
        "id": match.id,
        "match_percentage": match_percentage,
        "skills_alignment": skills_alignment,
        "experience_alignment": experience_alignment,
        "culture_fit": culture_fit,
        "growth_potential": growth_potential,
        "matched_skills": list(matched_skills),
        "missing_skills": missing_skills,
        "bonus_skills": bonus_skills,
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
    
    return JsonResponse({
        "id": dashboard.id,
        "favorite_jobs": favorite_jobs_data,
        "saved_candidates": saved_candidates_data,
        "pipeline_stages": dashboard.pipeline_stages,
        "hiring_goals": dashboard.hiring_goals,
        "interview_schedule": dashboard.interview_schedule,
        "team_members": dashboard.team_members,
        "notifications_settings": dashboard.notifications_settings,
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
