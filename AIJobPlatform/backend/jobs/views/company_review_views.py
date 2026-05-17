"""
Company Review API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from jobs.company_reviews import (
    get_company_reviews,
    get_company_rating_summary,
    create_company_review,
    mark_review_helpful,
    get_top_companies,
)


@api_view(['GET'])
@permission_classes([AllowAny])
def company_reviews_list(request):
    """Get reviews for a company"""
    company_name = request.query_params.get('company', '')

    if not company_name:
        return Response(
            {'error': 'Company name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    reviews = get_company_reviews(company_name)
    summary = get_company_rating_summary(company_name)

    return Response({
        'reviews': reviews,
        'summary': summary,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def company_rating_summary(request):
    """Get company rating summary"""
    company_name = request.query_params.get('company', '')

    if not company_name:
        return Response(
            {'error': 'Company name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    summary = get_company_rating_summary(company_name)
    return Response(summary)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request):
    """Create a new company review"""
    data = request.data

    required_fields = ['company_name', 'overall_rating']
    for field in required_fields:
        if field not in data:
            return Response(
                {'error': f'{field} is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

    if not 1 <= data['overall_rating'] <= 5:
        return Response(
            {'error': 'Rating must be between 1 and 5'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = create_company_review(data, request.user.id)

    if result.get('success'):
        return Response(result)
    else:
        return Response(
            {'error': result.get('error', 'Failed to create review')},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_helpful(request, review_id):
    """Mark a review as helpful"""
    result = mark_review_helpful(review_id, request.user.id)
    return Response(result)


@api_view(['GET'])
@permission_classes([AllowAny])
def top_companies(request):
    """Get top rated companies"""
    limit = int(request.query_params.get('limit', 20))
    companies = get_top_companies(limit)
    return Response({'companies': companies})