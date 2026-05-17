"""
Cover Letter Generator API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from jobs.cover_letter_generator import generate_cover_letter


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_cover_letter_view(request):
    """Generate a cover letter"""
    company_name = request.data.get('company_name')
    position = request.data.get('position')
    job_id = request.data.get('job_id')
    job_description = request.data.get('job_description')
    tone = request.data.get('tone', 'professional')

    if not company_name and not job_id:
        return Response(
            {'error': 'Please provide company_name or job_id'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not position and not job_id:
        return Response(
            {'error': 'Please provide position or job_id'},
            status=status.HTTP_400_BAD_REQUEST
        )

    result = generate_cover_letter(
        user_id=request.user.id,
        company_name=company_name,
        position=position,
        job_description=job_description,
        job_id=job_id,
        tone=tone
    )

    if result.get('success'):
        return Response(result)
    else:
        return Response(
            {'error': result.get('error', 'Failed to generate cover letter')},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_multiple_cover_letters(request):
    """Generate cover letters for multiple jobs"""
    jobs = request.data.get('jobs', [])

    if not jobs:
        return Response(
            {'error': 'Please provide jobs array'},
            status=status.HTTP_400_BAD_REQUEST
        )

    from jobs.cover_letter_generator import cover_letter_generator

    letters = cover_letter_generator.generate_multiple(
        user_id=request.user.id,
        jobs=jobs
    )

    return Response({
        'success': True,
        'letters': letters,
    })