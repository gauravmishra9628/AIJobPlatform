from celery import shared_task
from django.utils import timezone

from .comparison_service import AIComparisonService
from .models import UsageLedger, RecruiterQuery, QueryResult, JobApplication, ResumeJobComparison
from .recruiter_services import RecruiterAssistant


@shared_task
def compact_usage_activity(user_id):
    cutoff = timezone.now() - timezone.timedelta(days=90)
    deleted, _ = UsageLedger.objects.filter(user_id=user_id, created_at__lt=cutoff).delete()
    return {"deleted": deleted, "user_id": user_id}


@shared_task
def warm_dashboard_cache():
    return {"status": "ready", "warmed_at": timezone.now().isoformat()}


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
