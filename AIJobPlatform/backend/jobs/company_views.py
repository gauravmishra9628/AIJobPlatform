import json

from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.decorators import jwt_required
from accounts.models import User

from .models import CompanyProfile, CompanyReview, JobPost


def _badge_for_company(company: CompanyProfile) -> dict:
    average_rating = float(company.average_rating or 0)
    review_count = company.review_count or 0
    active_positions = company.active_positions or 0

    if average_rating >= 4.6 and review_count >= 8:
        badge_tier = "Platinum"
    elif average_rating >= 4.2 and review_count >= 5:
        badge_tier = "Gold"
    elif average_rating >= 3.6:
        badge_tier = "Silver"
    else:
        badge_tier = "Bronze"

    return {
        "badge_tier": badge_tier,
        "badge_label": f"{badge_tier} Hiring Badge",
        "is_featured": average_rating >= 4.2 or active_positions >= 5,
    }


def _serialize_review(review: CompanyReview) -> dict:
    reviewer_name = "Anonymous" if review.is_anonymous else review.reviewer.get_full_name() or review.reviewer.email
    return {
        "id": review.id,
        "rating": review.rating,
        "title": review.title,
        "body": review.body,
        "is_anonymous": review.is_anonymous,
        "is_verified_employee": review.is_verified_employee,
        "reviewer": reviewer_name,
        "created_at": review.created_at.isoformat(),
    }


def _serialize_company(company: CompanyProfile) -> dict:
    badge = _badge_for_company(company)
    recruiter = company.verified_recruiter
    recruiter_verified = bool(recruiter and recruiter.is_email_verified)
    return {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
        "industry": company.industry,
        "employee_count": company.employee_count,
        "founded_year": company.founded_year,
        "location": company.location,
        "description": company.description,
        "logo": company.logo_url,
        "website": company.website,
        "linkedin_url": company.linkedin_url,
        "twitter_url": company.twitter_url,
        "recruiter": company.recruiter_name,
        "verified_recruiter": recruiter_verified,
        "verified_recruiter_email": recruiter.email if recruiter else "",
        "verified_recruiter_name": recruiter.get_full_name() if recruiter else "",
        "active_positions": company.active_positions,
        "hiring_urgency": company.hiring_urgency,
        "average_rating": round(float(company.average_rating or 0), 2),
        "review_count": company.review_count,
        **badge,
    }


def _sync_company_stats(company: CompanyProfile) -> None:
    reviews = company.reviews.all()
    aggregate = reviews.aggregate(avg_rating=Avg("rating"), review_count=Count("id"))
    company.average_rating = aggregate["avg_rating"] or 0
    company.review_count = aggregate["review_count"] or 0

    if company.active_positions >= 8 or float(company.average_rating or 0) >= 4.6:
        company.hiring_urgency = "high"
    elif company.active_positions >= 3 or float(company.average_rating or 0) >= 4.0:
        company.hiring_urgency = "medium"
    else:
        company.hiring_urgency = "low"

    company.save(update_fields=["average_rating", "review_count", "hiring_urgency", "updated_at"])


def ensure_company_profiles() -> None:
    company_names = JobPost.objects.values_list("company", flat=True).distinct()
    for company_name in company_names:
        normalized = company_name.strip()
        if not normalized:
            continue
        slug = slugify(normalized)
        active_positions = JobPost.objects.filter(company__iexact=normalized, is_active=True).count()
        top_recruiter = (
            User.objects.filter(
                role=User.Role.RECRUITER,
                is_email_verified=True,
                posted_jobs__company__iexact=normalized,
                posted_jobs__is_active=True,
            )
            .annotate(
                matched_jobs=Count(
                    "posted_jobs",
                    filter=Q(posted_jobs__company__iexact=normalized, posted_jobs__is_active=True),
                )
            )
            .order_by("-matched_jobs", "id")
            .first()
        )

        company, created = CompanyProfile.objects.get_or_create(
            slug=slug,
            defaults={
                "name": normalized,
                "location": "Remote",
                "description": f"{normalized} hiring profile created from active job listings.",
                "active_positions": active_positions,
                "verified_recruiter": top_recruiter,
                "recruiter_name": (top_recruiter.get_full_name() or top_recruiter.email) if top_recruiter else "",
            },
        )
        if not created:
            updated_fields = []
            if company.active_positions != active_positions:
                company.active_positions = active_positions
                updated_fields.append("active_positions")
            if top_recruiter and company.verified_recruiter_id != top_recruiter.id:
                company.verified_recruiter = top_recruiter
                updated_fields.append("verified_recruiter")
            recruiter_name = (top_recruiter.get_full_name() or top_recruiter.email) if top_recruiter else ""
            if company.recruiter_name != recruiter_name:
                company.recruiter_name = recruiter_name
                updated_fields.append("recruiter_name")
            if updated_fields:
                updated_fields.append("updated_at")
                company.save(update_fields=updated_fields)


@csrf_exempt
@require_http_methods(["GET"])
def list_companies(request):
    ensure_company_profiles()
    companies = CompanyProfile.objects.all().order_by("-review_count", "-average_rating", "name")
    query = request.GET.get("q", "").strip()
    if query:
        companies = companies.filter(name__icontains=query)

    return JsonResponse({"companies": [_serialize_company(company) for company in companies]})


@csrf_exempt
@require_http_methods(["GET"])
def company_detail(request, company_id):
    ensure_company_profiles()
    try:
        company = CompanyProfile.objects.get(pk=company_id)
    except CompanyProfile.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    return JsonResponse(
        {
            "company": _serialize_company(company),
            "reviews": [_serialize_review(review) for review in company.reviews.select_related("reviewer")[:25]],
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
def company_reviews(request, company_id):
    ensure_company_profiles()
    try:
        company = CompanyProfile.objects.get(pk=company_id)
    except CompanyProfile.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    rating = int(payload.get("rating") or 0)
    title = str(payload.get("title") or "").strip()
    body = str(payload.get("body") or "").strip()
    is_anonymous = bool(payload.get("is_anonymous", False))

    if rating < 1 or rating > 5 or not title or not body:
        return JsonResponse({"error": "rating, title, and body are required"}, status=400)

    review = CompanyReview.objects.create(
        company=company,
        reviewer=request.user,
        rating=rating,
        title=title,
        body=body,
        is_anonymous=is_anonymous,
        is_verified_employee=bool(getattr(request.user, "company_name", "")),
    )
    _sync_company_stats(company)

    return JsonResponse({"review": _serialize_review(review), "company": _serialize_company(company)}, status=201)


@csrf_exempt
@require_http_methods(["GET"])
def company_badge(request, company_id):
    ensure_company_profiles()
    try:
        company = CompanyProfile.objects.get(pk=company_id)
    except CompanyProfile.DoesNotExist:
        return JsonResponse({"error": "Company not found"}, status=404)

    return JsonResponse({"badge": _badge_for_company(company), "company": _serialize_company(company)})