"""
Company Review System
Allow users to rate and review companies they've worked for or interviewed with
"""

from typing import List, Dict
from django.db.models import Avg, Count

from jobs.models import CompanyReview


def get_company_reviews(company_name: str, limit: int = 20) -> List[Dict]:
    """Get reviews for a company"""

    reviews = CompanyReview.objects.filter(
        company_name__icontains=company_name
    ).order_by('-created_at')[:limit]

    return [
        {
            'id': r.id,
            'role': r.role,
            'employment_type': r.employment_type,
            'is_current_employee': r.is_current_employee,
            'overall_rating': r.overall_rating,
            'work_life_balance': r.work_life_balance,
            'culture': r.culture,
            'compensation': r.compensation,
            'growth': r.growth,
            'management': r.management,
            'pros': r.pros,
            'cons': r.cons,
            'advice_to_management': r.advice_to_management,
            'is_verified': r.is_verified,
            'is_anonymous': r.is_anonymous,
            'helpful_count': r.helpful_count,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'user': None if r.is_anonymous else {
                'id': r.user.id,
                'username': r.user.username,
            },
        }
        for r in reviews
    ]


def get_company_rating_summary(company_name: str) -> Dict:
    """Get aggregated ratings for a company"""

    reviews = CompanyReview.objects.filter(
        company_name__icontains=company_name
    )

    if not reviews.exists():
        return {
            'company_name': company_name,
            'total_reviews': 0,
            'average_rating': 0,
            'rating_breakdown': {},
        }

    rating_data = reviews.values(
        'overall_rating'
    ).annotate(count=Count('id'))

    breakdown = {i: 0 for i in range(1, 6)}

    for item in rating_data:
        breakdown[item['overall_rating']] = item['count']

    return {
        'company_name': company_name,
        'total_reviews': reviews.count(),
        'average_rating': round(
            reviews.aggregate(avg=Avg('overall_rating'))['avg'],
            1
        ),
        'rating_breakdown': breakdown,
        'recommended_percentage': round(
            reviews.filter(overall_rating__gte=4).count()
            / reviews.count() * 100,
            1
        ),
    }


def create_company_review(data: Dict, user_id: int) -> Dict:
    """Create a new company review"""

    try:
        review = CompanyReview.objects.create(
            company_name=data['company_name'],
            user_id=user_id,
            role=data.get('role', ''),
            employment_type=data.get('employment_type', ''),
            is_current_employee=data.get('is_current_employee', True),
            overall_rating=data['overall_rating'],
            work_life_balance=data.get('work_life_balance'),
            culture=data.get('culture'),
            compensation=data.get('compensation'),
            growth=data.get('growth'),
            management=data.get('management'),
            pros=data.get('pros', ''),
            cons=data.get('cons', ''),
            advice_to_management=data.get('advice_to_management', ''),
            is_anonymous=data.get('is_anonymous', False),
        )

        return {
            'success': True,
            'review_id': review.id,
            'message': 'Review submitted successfully!',
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


def mark_review_helpful(review_id: int, user_id: int) -> Dict:
    """Mark a review as helpful"""

    review = CompanyReview.objects.filter(id=review_id).first()

    if not review:
        return {
            'success': False,
            'error': 'Review not found'
        }

    review.helpful_count += 1
    review.save()

    return {
        'success': True,
        'helpful_count': review.helpful_count
    }


def get_top_companies(limit: int = 20) -> List[Dict]:
    """Get top rated companies"""

    companies = CompanyReview.objects.values(
        'company_name'
    ).annotate(
        avg_rating=Avg('overall_rating'),
        review_count=Count('id')
    ).filter(
        review_count__gte=3
    ).order_by('-avg_rating')[:limit]

    return [
        {
            'company_name': c['company_name'],
            'average_rating': round(c['avg_rating'], 1),
            'review_count': c['review_count'],
        }
        for c in companies
    ]