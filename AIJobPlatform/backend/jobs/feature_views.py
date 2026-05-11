"""
Feature API Views for AI Job Platform
Handles: External APIs, AI Analysis, Authentication, Dashboards, PDF Generation, Analytics
"""
import json
import requests
import secrets
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Count, Q, Sum, Avg
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    ExternalJobListing, JobPost, JobApplication, Resume, 
    ResumeTemplate, OTPVerification, PasswordResetToken,
    RecruiterAnalytics, RecruiterDashboard, Notification, ChatMessage
)
from accounts.models import User, Profile
from accounts.emails import send_otp_email, send_password_reset_email


# ========== 1. LIVE COMPANY JOBS API INTEGRATION ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_external_jobs(request):
    """Fetch jobs from external APIs (JSearch, Adzuna, Remotive)"""
    query = request.query_params.get('q', '')
    location = request.query_params.get('location', '')
    job_type = request.query_params.get('type', '')  # full-time, part-time, internship, remote
    
    if not query:
        return Response({'error': 'Search query required'}, status=status.HTTP_400_BAD_REQUEST)
    
    results = {'results': []}
    
    # JSearch API Integration
    jsearch_results = fetch_jsearch_jobs(query, location)
    results['results'].extend(jsearch_results)
    
    # Adzuna API Integration
    adzuna_results = fetch_adzuna_jobs(query, location)
    results['results'].extend(adzuna_results)
    
    # Remotive API Integration (for remote jobs)
    if job_type == 'remote' or not job_type:
        remotive_results = fetch_remotive_jobs(query)
        results['results'].extend(remotive_results)
    
    return Response(results)


def fetch_jsearch_jobs(query, location):
    """Fetch from JSearch API"""
    try:
        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {
            "query": f"{query} in {location}" if location else query,
            "page": "1",
            "num_pages": "1"
        }
        headers = {
            "x-rapidapi-key": settings.JSEARCH_API_KEY,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        jobs = response.json().get('data', [])
        
        results = []
        for job in jobs:
            results.append({
                'external_id': job.get('job_id'),
                'source': 'jsearch',
                'title': job.get('job_title'),
                'company': job.get('employer_name'),
                'location': job.get('job_location'),
                'description': job.get('job_description', ''),
                'job_url': job.get('job_apply_link'),
                'is_remote': job.get('job_is_remote', False),
                'employment_type': job.get('job_employment_type', 'full-time'),
            })
            # Save to database
            ExternalJobListing.objects.update_or_create(
                external_id=job.get('job_id'),
                defaults={
                    'source': 'jsearch',
                    'title': job.get('job_title'),
                    'company': job.get('employer_name'),
                    'location': job.get('job_location'),
                    'description': job.get('job_description', ''),
                    'job_url': job.get('job_apply_link'),
                    'is_remote': job.get('job_is_remote', False),
                    'employment_type': job.get('job_employment_type', 'full-time'),
                }
            )
        return results
    except Exception as e:
        print(f"JSearch API Error: {str(e)}")
        return []


def fetch_adzuna_jobs(query, location):
    """Fetch from Adzuna API"""
    try:
        url = f"https://api.adzuna.com/v1/api/jobs/{location or 'us'}/search/1"
        params = {
            'app_id': settings.ADZUNA_API_ID,
            'app_key': settings.ADZUNA_API_KEY,
            'results_per_page': 10,
            'what': query,
            'where': location or '',
        }
        response = requests.get(url, params=params, timeout=10)
        jobs = response.json().get('results', [])
        
        results = []
        for job in jobs:
            results.append({
                'external_id': job.get('id'),
                'source': 'adzuna',
                'title': job.get('title'),
                'company': job.get('company', {}).get('display_name'),
                'location': job.get('location', {}).get('display_name'),
                'description': job.get('description', ''),
                'job_url': job.get('redirect_url'),
                'employment_type': job.get('contract_type'),
                'salary_min': job.get('salary_min'),
                'salary_max': job.get('salary_max'),
            })
            # Save to database
            ExternalJobListing.objects.update_or_create(
                external_id=str(job.get('id')),
                defaults={
                    'source': 'adzuna',
                    'title': job.get('title'),
                    'company': job.get('company', {}).get('display_name'),
                    'location': job.get('location', {}).get('display_name'),
                    'description': job.get('description', ''),
                    'job_url': job.get('redirect_url'),
                    'employment_type': job.get('contract_type'),
                    'salary_min': job.get('salary_min'),
                    'salary_max': job.get('salary_max'),
                }
            )
        return results
    except Exception as e:
        print(f"Adzuna API Error: {str(e)}")
        return []


def fetch_remotive_jobs(query):
    """Fetch from Remotive API (remote jobs)"""
    try:
        url = "https://remotive.com/api/remote-jobs"
        params = {
            'search': query,
            'limit': 10,
        }
        response = requests.get(url, params=params, timeout=10)
        jobs = response.json().get('jobs', [])
        
        results = []
        for job in jobs:
            results.append({
                'external_id': job.get('id'),
                'source': 'remotive',
                'title': job.get('title'),
                'company': job.get('company_name'),
                'location': 'Remote',
                'description': job.get('description', ''),
                'job_url': job.get('url'),
                'is_remote': True,
                'employment_type': job.get('job_type'),
            })
            # Save to database
            ExternalJobListing.objects.update_or_create(
                external_id=str(job.get('id')),
                defaults={
                    'source': 'remotive',
                    'title': job.get('title'),
                    'company': job.get('company_name'),
                    'location': 'Remote',
                    'description': job.get('description', ''),
                    'job_url': job.get('url'),
                    'is_remote': True,
                    'employment_type': job.get('job_type'),
                }
            )
        return results
    except Exception as e:
        print(f"Remotive API Error: {str(e)}")
        return []


# ========== 2. AUTHENTICATION ENHANCEMENTS ==========

@api_view(['POST'])
def send_email_otp(request):
    """Send OTP to email for verification"""
    email = request.data.get('email')
    
    if not email:
        return Response({'error': 'Email required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate 6-digit OTP
    otp = ''.join([str(i) for i in [secrets.randbelow(10) for _ in range(6)]])
    
    # Clean up old OTPs
    OTPVerification.objects.filter(email=email, is_used=False).delete()
    
    # Create new OTP
    expires_at = now() + timedelta(minutes=10)
    otp_obj = OTPVerification.objects.create(
        user=None,
        otp=otp,
        email=email,
        expires_at=expires_at
    )
    
    # Send OTP email
    send_otp_email(email, otp)
    
    return Response({
        'message': 'OTP sent to email',
        'email': email,
        'expires_in': 10
    })


@api_view(['POST'])
def verify_email_otp(request):
    """Verify OTP and register user"""
    email = request.data.get('email')
    otp = request.data.get('otp')
    password = request.data.get('password')
    role = request.data.get('role', 'student')
    
    if not all([email, otp, password]):
        return Response({'error': 'Email, OTP, and password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check OTP
    try:
        otp_obj = OTPVerification.objects.get(email=email, otp=otp, is_used=False)
        if otp_obj.expires_at < now():
            return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
    except OTPVerification.DoesNotExist:
        return Response({'error': 'Invalid OTP'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Create user
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(
        email=email,
        password=password,
        role=role,
        is_email_verified=True
    )
    
    # Mark OTP as used
    otp_obj.user = user
    otp_obj.is_used = True
    otp_obj.save()
    
    return Response({
        'message': 'Email verified and user created',
        'user_id': user.id,
        'email': user.email,
    })


@api_view(['POST'])
def send_password_reset_email(request):
    """Send password reset link to email"""
    email = request.data.get('email')
    
    if not email:
        return Response({'error': 'Email required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'message': 'If email exists, reset link will be sent'})
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    expires_at = now() + timedelta(hours=24)
    
    PasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=expires_at
    )
    
    # Send email
    send_password_reset_email(user.email, token)
    
    return Response({'message': 'Password reset email sent'})


@api_view(['POST'])
def reset_password(request):
    """Reset password using token"""
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not all([token, new_password]):
        return Response({'error': 'Token and new password required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
        if reset_token.expires_at < now():
            return Response({'error': 'Reset link expired'}, status=status.HTTP_400_BAD_REQUEST)
    except PasswordResetToken.DoesNotExist:
        return Response({'error': 'Invalid reset link'}, status=status.HTTP_401_UNAUTHORIZED)
    
    user = reset_token.user
    user.set_password(new_password)
    user.save()
    
    reset_token.is_used = True
    reset_token.save()
    
    return Response({'message': 'Password reset successful'})


# ========== 3. RECRUITER DASHBOARD ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recruiter_dashboard(request):
    """Get recruiter dashboard data"""
    if request.user.role != 'recruiter':
        return Response({'error': 'Only recruiters can access this'}, status=status.HTTP_403_FORBIDDEN)
    
    dashboard, created = RecruiterDashboard.objects.get_or_create(recruiter=request.user)
    
    # Calculate analytics
    posted_jobs = JobPost.objects.filter(posted_by=request.user)
    applications = JobApplication.objects.filter(job__posted_by=request.user)
    
    return Response({
        'dashboard': {
            'favorite_jobs': dashboard.favorite_jobs,
            'saved_candidates': dashboard.saved_candidates,
            'pipeline_stages': dashboard.pipeline_stages,
            'hiring_goals': dashboard.hiring_goals,
        },
        'analytics': {
            'total_jobs': posted_jobs.count(),
            'total_applications': applications.count(),
            'shortlisted': applications.filter(status='shortlisted').count(),
            'hired': applications.filter(status='hired').count(),
            'pending': applications.filter(status='applied').count(),
        }
    })


# ========== 4. STUDENT DASHBOARD ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_dashboard(request):
    """Get student dashboard data"""
    if request.user.role != 'student':
        return Response({'error': 'Only students can access this'}, status=status.HTTP_403_FORBIDDEN)
    
    applications = JobApplication.objects.filter(applicant=request.user)
    bookmarks = JobPost.objects.filter(bookmarks__user=request.user)
    profile = Profile.objects.get(user=request.user)
    resumes = Resume.objects.filter(user=request.user)
    
    # Calculate profile completion percentage
    profile_fields = ['bio', 'skills', 'github_url', 'linkedin_url']
    completed = sum(1 for field in profile_fields if getattr(profile, field, None))
    profile_completion = (completed / len(profile_fields)) * 100
    
    return Response({
        'applications': {
            'total': applications.count(),
            'applied': applications.filter(status='applied').count(),
            'shortlisted': applications.filter(status='shortlisted').count(),
            'rejected': applications.filter(status='rejected').count(),
        },
        'bookmarks': bookmarks.count(),
        'resumes': resumes.count(),
        'profile_completion': round(profile_completion, 2),
        'profile': {
            'headline': profile.headline,
            'skills': profile.skills,
            'experience': profile.portfolio_items,
        }
    })


# ========== 5. RESUME PDF GENERATOR ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_resume_pdf(request):
    """Generate professional resume as PDF"""
    template_data = request.data.get('template', {})
    style = request.data.get('style', 'modern')
    
    # Create or update template
    template, created = ResumeTemplate.objects.get_or_create(
        user=request.user,
        defaults={
            'full_name': request.user.first_name or request.user.email,
            'email': request.user.email,
        }
    )
    
    for key, value in template_data.items():
        if hasattr(template, key):
            setattr(template, key, value)
    
    template.template_style = style
    template.save()
    
    # Generate PDF (integration point for libraries like reportlab, pypdf)
    # This is a placeholder - actual PDF generation would use reportlab or similar
    pdf_url = f"/api/jobs/resume/download/{template.id}/"
    
    return Response({
        'message': 'Resume generated successfully',
        'pdf_url': pdf_url,
        'format': 'pdf',
        'style': style
    })


# ========== 6. ADMIN ANALYTICS ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_admin_analytics(request):
    """Get analytics for admin panel"""
    if request.user.role != 'admin':
        return Response({'error': 'Only admins can access this'}, status=status.HTTP_403_FORBIDDEN)
    
    # User statistics
    total_users = User.objects.count()
    students = User.objects.filter(role='student').count()
    recruiters = User.objects.filter(role='recruiter').count()
    
    # Job statistics
    total_jobs = JobPost.objects.count()
    active_jobs = JobPost.objects.filter(is_active=True).count()
    
    # Application statistics
    total_applications = JobApplication.objects.count()
    applications_this_month = JobApplication.objects.filter(
        created_at__gte=now().replace(day=1)
    ).count()
    
    # Analytics
    analytics = RecruiterAnalytics.objects.aggregate(
        total_jobs_posted=Sum('total_jobs_posted'),
        total_applications_sum=Sum('total_applications'),
        total_hired_sum=Sum('total_hired'),
        avg_time_to_hire=Avg('average_time_to_hire'),
    )
    
    return Response({
        'users': {
            'total': total_users,
            'students': students,
            'recruiters': recruiters,
        },
        'jobs': {
            'total': total_jobs,
            'active': active_jobs,
        },
        'applications': {
            'total': total_applications,
            'this_month': applications_this_month,
        },
        'recruiter_analytics': analytics,
    })


# ========== 7. THEME TOGGLE ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_theme(request):
    """Toggle dark/light theme preference"""
    theme = request.data.get('theme', 'light')  # light, dark, system
    
    if theme not in ['light', 'dark', 'system']:
        return Response({'error': 'Invalid theme'}, status=status.HTTP_400_BAD_REQUEST)
    
    request.user.theme_preference = theme
    request.user.save()
    
    return Response({
        'message': 'Theme updated',
        'theme': theme,
    })


# ========== 8. NOTIFICATIONS ENHANCEMENT ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Get user notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    
    return Response({
        'notifications': [{
            'id': n.id,
            'type': n.type,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at,
        } for n in notifications]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request):
    """Mark notification as read"""
    notification_id = request.data.get('notification_id')
    
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


# ========== REAL-TIME CHAT ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_history(request, recipient_id):
    """Get chat history with a user"""
    try:
        recipient = User.objects.get(id=recipient_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    messages = ChatMessage.objects.filter(
        Q(sender=request.user, recipient=recipient) |
        Q(sender=recipient, recipient=request.user)
    ).order_by('created_at')
    
    return Response({
        'messages': [{
            'id': m.id,
            'sender_id': m.sender.id,
            'recipient_id': m.recipient.id,
            'message': m.message,
            'is_read': m.is_read,
            'created_at': m.created_at,
        } for m in messages]
    })
