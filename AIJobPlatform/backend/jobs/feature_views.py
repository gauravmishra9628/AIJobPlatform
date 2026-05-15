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
    ResumeTemplate, 
    RecruiterAnalytics, RecruiterDashboard, Notification, ChatMessage, SkillVerificationBadge
)
from accounts.decorators import jwt_required
from accounts.models import User, Profile, OTPVerification, PasswordResetToken
from accounts.emails import send_otp_email, send_password_reset_email


# ========== 1. LIVE COMPANY JOBS API INTEGRATION ==========

@api_view(['GET'])
@jwt_required
def fetch_external_jobs(request):
    """Fetch jobs from Google Jobs, LinkedIn-style, remote, and internship sources."""
    query = request.query_params.get('q', '')
    location = request.query_params.get('location', '')
    job_type = request.query_params.get('type', '')  # full-time, part-time, internship, remote
    source = request.query_params.get('source', 'all')  # all, google, linkedin, remote, internships
    
    if not query:
        return Response({'error': 'Search query required'}, status=status.HTTP_400_BAD_REQUEST)
    
    requested_sources = resolve_external_job_sources(source, job_type)
    jobs = []
    errors = []

    source_fetchers = {
        'google': lambda: fetch_google_jobs(query, location, job_type),
        'linkedin': lambda: fetch_linkedin_style_jobs(query, location, job_type),
        'remote': lambda: fetch_remotive_jobs(query),
        'internships': lambda: fetch_internship_jobs(query, location),
    }

    for source_name in requested_sources:
        try:
            jobs.extend(source_fetchers[source_name]())
        except Exception as exc:
            errors.append({'source': source_name, 'message': str(exc)})

    jobs = filter_external_jobs(jobs, job_type)
    return Response({
        'results': jobs,
        'count': len(jobs),
        'sources': requested_sources,
        'errors': errors,
    })


def resolve_external_job_sources(source, job_type):
    """Map UI/API filters to concrete provider fetchers."""
    source = (source or 'all').lower()
    job_type = (job_type or '').lower()

    if source in ['google', 'google_jobs']:
        return ['google']
    if source in ['linkedin', 'linkedin-style', 'linkedin_style']:
        return ['linkedin']
    if source == 'remote' or job_type == 'remote':
        return ['remote', 'google', 'linkedin']
    if source in ['internship', 'internships'] or job_type == 'internship':
        return ['internships', 'google', 'linkedin']

    return ['google', 'linkedin', 'remote', 'internships']


def filter_external_jobs(jobs, job_type):
    if not job_type:
        return jobs

    job_type = job_type.lower()
    filtered = []
    for job in jobs:
        employment_type = (job.get('employment_type') or '').lower()
        title = (job.get('title') or '').lower()
        description = (job.get('description') or '').lower()
        is_internship = job.get('is_internship') or 'intern' in title or 'internship' in description

        if job_type == 'remote' and job.get('is_remote'):
            filtered.append(job)
        elif job_type == 'internship' and is_internship:
            filtered.append(job)
        elif job_type not in ['remote', 'internship'] and job_type in employment_type:
            filtered.append(job)

    return filtered


def persist_external_job(job):
    external_id = str(job.get('external_id') or '').strip()
    if not external_id or not job.get('title') or not job.get('job_url'):
        return

    source = job.get('source') or 'jsearch'
    namespaced_id = external_id if external_id.startswith(f'{source}:') else f'{source}:{external_id}'
    job['external_id'] = namespaced_id

    ExternalJobListing.objects.update_or_create(
        external_id=namespaced_id,
        defaults={
            'source': source,
            'title': (job.get('title') or 'Untitled role')[:180],
            'company': (job.get('company') or 'Unknown company')[:180],
            'location': (job.get('location') or 'Not specified')[:180],
            'description': job.get('description') or '',
            'skills_required': job.get('skills_required') or [],
            'job_url': job.get('job_url'),
            'is_remote': bool(job.get('is_remote')),
            'is_internship': bool(job.get('is_internship')),
            'employment_type': job.get('employment_type') or '',
            'salary_min': normalize_salary(job.get('salary_min')),
            'salary_max': normalize_salary(job.get('salary_max')),
        }
    )


def normalize_salary(value):
    try:
        return int(float(value)) if value not in [None, ''] else None
    except (TypeError, ValueError):
        return None


def is_internship_job(title='', description='', employment_type=''):
    haystack = f'{title} {description} {employment_type}'.lower()
    return any(term in haystack for term in ['intern', 'internship', 'student trainee', 'co-op'])


def fetch_google_jobs(query, location, job_type=''):
    """Fetch Google Jobs through SerpApi when SERPAPI_API_KEY/GOOGLE_JOBS_API_KEY is configured."""
    api_key = getattr(settings, 'SERPAPI_API_KEY', '') or getattr(settings, 'GOOGLE_JOBS_API_KEY', '')
    if not api_key:
        return fetch_jsearch_jobs(query, location, job_type, source_label='google_jobs')

    google_query = query
    if job_type == 'internship':
        google_query = f'{query} internship'
    elif job_type == 'remote':
        google_query = f'{query} remote'

    response = requests.get(
        'https://serpapi.com/search.json',
        params={
            'engine': 'google_jobs',
            'q': google_query,
            'location': location or 'United States',
            'api_key': api_key,
        },
        timeout=10,
    )
    response.raise_for_status()
    jobs = response.json().get('jobs_results', [])

    results = []
    for job in jobs:
        apply_options = job.get('apply_options') or []
        job_url = (apply_options[0] or {}).get('link') if apply_options else job.get('share_link')
        title = job.get('title')
        description = job.get('description', '')
        schedule_type = job.get('detected_extensions', {}).get('schedule_type', '')
        employment_type = ', '.join(schedule_type) if isinstance(schedule_type, list) else schedule_type
        result = {
            'external_id': job.get('job_id') or job.get('job_id_hashed') or job_url,
            'source': 'google_jobs',
            'title': title,
            'company': job.get('company_name'),
            'location': job.get('location') or location or 'Not specified',
            'description': description,
            'job_url': job_url,
            'is_remote': 'remote' in f"{job.get('location', '')} {description}".lower(),
            'is_internship': is_internship_job(title, description, employment_type),
            'employment_type': employment_type,
        }
        persist_external_job(result)
        results.append(result)

    return results


def fetch_linkedin_style_jobs(query, location, job_type=''):
    """
    Fetch LinkedIn-style jobs.
    Uses the RapidAPI LinkedIn Jobs Search API when LINKEDIN_JOBS_API_KEY is configured,
    otherwise falls back to JSearch with LinkedIn-focused query terms.
    """
    api_key = getattr(settings, 'LINKEDIN_JOBS_API_KEY', '')
    if not api_key:
        linkedin_query = f'{query} LinkedIn'
        if job_type == 'internship':
            linkedin_query = f'{query} internship LinkedIn'
        elif job_type == 'remote':
            linkedin_query = f'{query} remote LinkedIn'
        return fetch_jsearch_jobs(linkedin_query, location, job_type, source_label='linkedin')

    response = requests.get(
        'https://linkedin-jobs-search.p.rapidapi.com/',
        headers={
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'linkedin-jobs-search.p.rapidapi.com',
            'Content-Type': 'application/json',
        },
        json={
            'search_terms': query,
            'location': location or 'United States',
            'page': '1',
        },
        timeout=10,
    )
    response.raise_for_status()
    jobs = response.json()
    if isinstance(jobs, dict):
        jobs = jobs.get('jobs') or jobs.get('data') or []

    results = []
    for job in jobs[:10]:
        title = job.get('job_title') or job.get('title')
        description = job.get('job_description') or job.get('description', '')
        employment_type = job.get('job_type') or job.get('employment_type', '')
        result = {
            'external_id': job.get('job_id') or job.get('id') or job.get('job_url'),
            'source': 'linkedin',
            'title': title,
            'company': job.get('company_name') or job.get('company'),
            'location': job.get('job_location') or job.get('location') or location,
            'description': description,
            'job_url': job.get('job_url') or job.get('linkedin_job_url') or job.get('url'),
            'is_remote': 'remote' in f"{job.get('job_location', '')} {description}".lower(),
            'is_internship': is_internship_job(title, description, employment_type),
            'employment_type': employment_type,
        }
        persist_external_job(result)
        results.append(result)

    return results


def fetch_jsearch_jobs(query, location, job_type='', source_label='jsearch'):
    """Fetch from JSearch API"""
    try:
        if not getattr(settings, 'JSEARCH_API_KEY', ''):
            return []

        url = "https://jsearch.p.rapidapi.com/search"
        search_query = f"{query} in {location}" if location else query
        if job_type == 'internship' and 'intern' not in search_query.lower():
            search_query = f'{search_query} internship'
        if job_type == 'remote' and 'remote' not in search_query.lower():
            search_query = f'{search_query} remote'

        querystring = {
            "query": search_query,
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
            title = job.get('job_title')
            description = job.get('job_description', '')
            employment_type = job.get('job_employment_type', 'full-time')
            result = {
                'external_id': job.get('job_id'),
                'source': source_label,
                'title': title,
                'company': job.get('employer_name'),
                'location': job.get('job_location'),
                'description': description,
                'job_url': job.get('job_apply_link'),
                'is_remote': job.get('job_is_remote', False),
                'is_internship': is_internship_job(title, description, employment_type),
                'employment_type': employment_type,
            }
            persist_external_job(result)
            results.append(result)
        return results
    except Exception as e:
        print(f"JSearch API Error: {str(e)}")
        return []


def fetch_adzuna_jobs(query, location, job_type=''):
    """Fetch from Adzuna API"""
    try:
        if not getattr(settings, 'ADZUNA_API_ID', '') or not getattr(settings, 'ADZUNA_API_KEY', ''):
            return []

        url = f"https://api.adzuna.com/v1/api/jobs/{location or 'us'}/search/1"
        search_query = query
        if job_type == 'internship' and 'intern' not in search_query.lower():
            search_query = f'{search_query} internship'
        if job_type == 'remote' and 'remote' not in search_query.lower():
            search_query = f'{search_query} remote'
        params = {
            'app_id': settings.ADZUNA_API_ID,
            'app_key': settings.ADZUNA_API_KEY,
            'results_per_page': 10,
            'what': search_query,
            'where': location or '',
        }
        response = requests.get(url, params=params, timeout=10)
        jobs = response.json().get('results', [])
        
        results = []
        for job in jobs:
            title = job.get('title')
            description = job.get('description', '')
            employment_type = job.get('contract_type')
            result = {
                'external_id': job.get('id'),
                'source': 'adzuna',
                'title': title,
                'company': job.get('company', {}).get('display_name'),
                'location': job.get('location', {}).get('display_name'),
                'description': description,
                'job_url': job.get('redirect_url'),
                'employment_type': employment_type,
                'salary_min': job.get('salary_min'),
                'salary_max': job.get('salary_max'),
                'is_remote': 'remote' in f"{job.get('location', {}).get('display_name', '')} {description}".lower(),
                'is_internship': is_internship_job(title, description, employment_type),
            }
            persist_external_job(result)
            results.append(result)
        return results
    except Exception as e:
        print(f"Adzuna API Error: {str(e)}")
        return []


def fetch_internship_jobs(query, location):
    """Fetch internship listings from general job providers."""
    results = []
    results.extend(fetch_jsearch_jobs(query, location, 'internship'))
    results.extend(fetch_adzuna_jobs(query, location, 'internship'))
    return results


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
            title = job.get('title')
            description = job.get('description', '')
            employment_type = job.get('job_type')
            result = {
                'external_id': job.get('id'),
                'source': 'remotive',
                'title': title,
                'company': job.get('company_name'),
                'location': 'Remote',
                'description': description,
                'job_url': job.get('url'),
                'is_remote': True,
                'is_internship': is_internship_job(title, description, employment_type),
                'employment_type': employment_type,
            }
            persist_external_job(result)
            results.append(result)
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
@jwt_required
def get_recruiter_dashboard(request):
    """Get recruiter dashboard data"""
    if request.user.role != 'recruiter':
        return Response({'error': 'Only recruiters can access this'}, status=status.HTTP_403_FORBIDDEN)
    
    dashboard, created = RecruiterDashboard.objects.get_or_create(recruiter=request.user)
    
    # Calculate analytics
    posted_jobs = JobPost.objects.filter(posted_by=request.user)
    applications = JobApplication.objects.filter(job__posted_by=request.user).select_related("applicant", "job")
    total_views = sum(job.views_count for job in posted_jobs)
    most_viewed_jobs = [
        {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'views_count': job.views_count,
            'applications_count': job.applications.count(),
        }
        for job in posted_jobs.order_by('-views_count', '-created_at')[:5]
    ]
    candidate_ranking = [
        {
            'application_id': application.id,
            'candidate_id': application.applicant.id,
            'candidate_name': application.applicant.get_full_name() or application.applicant.email,
            'job_id': application.job_id,
            'job_title': application.job.title,
            'match_score': application.match_score,
            'status': application.status,
        }
        for application in applications.order_by('-match_score', '-created_at')[:8]
    ]
    
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
            'total_views': total_views,
        }
        ,
        'most_viewed_jobs': most_viewed_jobs,
        'candidate_ranking': candidate_ranking,
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


# ========== 5B. CANDIDATE LEADERBOARD ========== 

@api_view(['GET'])
@jwt_required
@permission_classes([IsAuthenticated])
def get_candidate_leaderboard(request):
    if request.user.role not in ('recruiter', 'admin'):
        return Response({'error': 'Only recruiters can access this'}, status=status.HTTP_403_FORBIDDEN)

    candidates = User.objects.filter(role='student').select_related('profile')
    leaderboard = []
    for candidate in candidates:
        profile = getattr(candidate, 'profile', None)
        resume = Resume.objects.filter(user=candidate).order_by('-uploaded_at').first()
        applications = JobApplication.objects.filter(applicant=candidate)
        badges = SkillVerificationBadge.objects.filter(user=candidate)
        profile_score = 0
        profile_checks = [
            bool(getattr(profile, 'headline', '')),
            bool(getattr(profile, 'bio', '')),
            bool(getattr(profile, 'skills', []) or []),
            bool(getattr(profile, 'github_url', '') or getattr(profile, 'linkedin_url', '')),
            bool(getattr(profile, 'portfolio_items', []) or []),
            bool(resume),
        ]
        profile_score = int((sum(1 for item in profile_checks if item) / len(profile_checks)) * 100)
        skill_score = min(100, (len(getattr(profile, 'skills', []) or []) * 12) + (len(badges) * 10))
        experience_score = min(100, applications.count() * 8 + applications.filter(status='shortlisted').count() * 15)
        leaderboard_score = int((profile_score * 0.35) + (skill_score * 0.35) + (experience_score * 0.3))

        leaderboard.append({
            'candidate_id': candidate.id,
            'candidate_name': candidate.get_full_name() or candidate.email,
            'headline': getattr(profile, 'headline', ''),
            'skills': getattr(profile, 'skills', []) or [],
            'badge_count': badges.count(),
            'resume_uploaded': bool(resume),
            'applications_count': applications.count(),
            'shortlisted_count': applications.filter(status='shortlisted').count(),
            'profile_score': profile_score,
            'skill_score': skill_score,
            'experience_score': experience_score,
            'leaderboard_score': leaderboard_score,
            'share_link': f'/profile/{candidate.id}',
        })

    leaderboard.sort(key=lambda item: item['leaderboard_score'], reverse=True)
    return Response({
        'count': len(leaderboard),
        'top_candidates': leaderboard[:10],
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
