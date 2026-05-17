"""
Analytics API Views
User dashboard and analytics endpoints
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from jobs.analytics import user_analytics


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_dashboard(request):
    """Get complete user dashboard analytics"""
    data = user_analytics.get_dashboard_analytics(request.user.id)
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_application_trends(request):
    """Get application trends"""
    user = request.user
    app_analytics = user_analytics._application_analytics(user)
    return Response(app_analytics)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skill_progress(request):
    """Get skill progress analytics"""
    user = request.user
    skill_analytics = user_analytics._skill_growth_analytics(user)
    return Response(skill_analytics)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_interview_performance(request):
    """Get interview performance analytics"""
    user = request.user
    interview_analytics = user_analytics._interview_performance(user)
    return Response(interview_analytics)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume_strength(request):
    """Get resume strength analytics"""
    user = request.user
    resume_analytics = user_analytics._resume_strength_analytics(user)
    return Response(resume_analytics)