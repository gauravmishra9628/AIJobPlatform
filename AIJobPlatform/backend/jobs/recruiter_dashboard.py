"""
Recruiter Dashboard Views & Services
Complete recruiter functionality for SaaS
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Avg, Max, Min
from django.core.paginator import Paginator
from accounts.decorators import jwt_required, role_required
from accounts.models import User
from jobs.models import (
    JobPost, JobApplication, Resume, CompanyProfile,
    RecruiterAnalytics, Notification
)
from .recommendation_engine import recommendation_engine
import json


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
@role_required(['recruiter', 'admin'])
def recruiter_dashboard(request):
    """Get recruiter dashboard data"""
    user = request.user

    # Get recruiter's posted jobs
    posted_jobs = JobPost.objects.filter(posted_by=user).select_related('posted_by')
    active_jobs = posted_jobs.filter(is_active=True)
    inactive_jobs = posted_jobs.filter(is_active=False)

    # Get applications for recruiter's jobs
    recruiter_job_ids = posted_jobs.values_list('id', flat=True)
    applications = JobApplication.objects.filter(job_id__in=recruiter_job_ids)

    # Application stats by status
    status_counts = applications.values('status').annotate(count=Count('id'))

    # Recent applications
    recent_applications = applications.select_related(
        'applicant', 'job'
    ).order_by('-created_at')[:10]

    # Analytics
    analytics, _ = RecruiterAnalytics.objects.get_or_create(
        recruiter=user,
        defaults={
            'total_jobs_posted': posted_jobs.count(),
            'total_applications': applications.count(),
            'total_hired': applications.filter(status='shortlisted').count(),
        }
    )

    # Calculate engagement rate
    if applications.count() > 0:
        engagement = (applications.filter(status='shortlisted').count() / applications.count()) * 100
    else:
        engagement = 0

    data = {
        'jobs': {
            'total': posted_jobs.count(),
            'active': active_jobs.count(),
            'inactive': inactive_jobs.count(),
        },
        'applications': {
            'total': applications.count(),
            'by_status': {item['status']: item['count'] for item in status_counts},
        },
        'analytics': {
            'total_hires': analytics.total_hired,
            'engagement_rate': round(engagement, 1),
            'average_time_to_hire': analytics.average_time_to_hire,
        },
        'recent_applications': [
            {
                'id': app.id,
                'candidate': {
                    'id': app.applicant.id,
                    'name': f"{app.applicant.first_name} {app.applicant.last_name}".strip() or app.applicant.email,
                    'email': app.applicant.email,
                },
                'job': {
                    'id': app.job.id,
                    'title': app.job.title,
                    'company': app.job.company,
                },
                'status': app.status,
                'match_score': app.match_score,
                'applied_at': app.created_at.isoformat(),
            }
            for app in recent_applications
        ]
    }

    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET", "POST"])
@jwt_required
@role_required(['recruiter', 'admin'])
def manage_jobs(request):
    """List and create jobs for recruiter"""
    user = request.user

    if request.method == 'GET':
        # Get all jobs posted by recruiter with pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        status_filter = request.GET.get('status', 'all')
        search = request.GET.get('search', '')

        jobs = JobPost.objects.filter(posted_by=user).select_related('posted_by')

        # Apply filters
        if status_filter == 'active':
            jobs = jobs.filter(is_active=True)
        elif status_filter == 'inactive':
            jobs = jobs.filter(is_active=False)

        if search:
            jobs = jobs.filter(
                Q(title__icontains=search) |
                Q(company__icontains=search)
            )

        # Sort by date
        jobs = jobs.order_by('-created_at')

        # Paginate
        paginator = Paginator(jobs, per_page)
        page_obj = paginator.get_page(page)

        return JsonResponse({
            'jobs': [
                {
                    'id': job.id,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'employment_type': job.employment_type,
                    'is_active': job.is_active,
                    'views_count': job.views_count,
                    'applications_count': job.applications.count(),
                    'created_at': job.created_at.isoformat(),
                }
                for job in page_obj
            ],
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_next': page_obj.has_next(),
                'has_prev': page_obj.has_previous(),
            }
        })

    elif request.method == 'POST':
        # Create new job
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Validate required fields
        required = ['title', 'company', 'location', 'description']
        for field in required:
            if not data.get(field):
                return JsonResponse({'error': f'{field} is required'}, status=400)

        job = JobPost.objects.create(
            posted_by=user,
            title=data['title'],
            company=data['company'],
            location=data['location'],
            description=data['description'],
            skills_required=data.get('skills_required', ''),
            employment_type=data.get('employment_type', 'full-time'),
            salary_range=data.get('salary_range', ''),
            salary_min=data.get('salary_min'),
            salary_max=data.get('salary_max'),
            required_experience_years=data.get('required_experience_years', 0),
            required_education=data.get('required_education', ''),
            requirements=data.get('requirements', {}),
            is_active=data.get('is_active', True),
        )

        return JsonResponse({
            'message': 'Job created successfully',
            'job': {
                'id': job.id,
                'title': job.title,
                'company': job.company,
            }
        }, status=201)


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
@jwt_required
@role_required(['recruiter', 'admin'])
def manage_job(request, job_id):
    """Get, update or delete a specific job"""
    user = request.user

    try:
        job = JobPost.objects.get(id=job_id, posted_by=user)
    except JobPost.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

    if request.method == 'GET':
        # Get job with applications
        applications = job.applications.select_related('applicant').order_by('-created_at')

        return JsonResponse({
            'job': {
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'skills_required': job.skills_required,
                'employment_type': job.employment_type,
                'salary_range': job.salary_range,
                'is_active': job.is_active,
                'views_count': job.views_count,
                'created_at': job.created_at.isoformat(),
            },
            'applications': [
                {
                    'id': app.id,
                    'candidate': {
                        'id': app.applicant.id,
                        'name': f"{app.applicant.first_name} {app.applicant.last_name}".strip() or app.applicant.email,
                        'email': app.applicant.email,
                    },
                    'status': app.status,
                    'match_score': app.match_score,
                    'applied_at': app.created_at.isoformat(),
                }
                for app in applications[:20]
            ],
            'total_applications': applications.count(),
        })

    elif request.method == 'PATCH':
        # Update job
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        for field in ['title', 'company', 'location', 'description', 'skills_required',
                     'employment_type', 'salary_range', 'is_active', 'salary_min', 'salary_max']:
            if field in data:
                setattr(job, field, data[field])

        job.save()

        return JsonResponse({'message': 'Job updated successfully'})

    elif request.method == 'DELETE':
        job.delete()
        return JsonResponse({'message': 'Job deleted successfully'})


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
@role_required(['recruiter', 'admin'])
def search_candidates(request):
    """Search and filter candidates"""
    user = request.user

    # Get filter parameters
    skills = request.GET.get('skills', '')
    experience_min = request.GET.get('experience_min', 0)
    experience_max = request.GET.get('experience_max', 20)
    location = request.GET.get('location', '')
    status = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))

    # Get jobs posted by recruiter
    recruiter_job_ids = JobPost.objects.filter(posted_by=user).values_list('id', flat=True)

    # Get applications for recruiter's jobs
    applications = JobApplication.objects.filter(
        job_id__in=recruiter_job_ids
    ).select_related('applicant', 'job', 'resume')

    # Apply filters
    if search:
        applications = applications.filter(
            Q(applicant__email__icontains=search) |
            Q(applicant__first_name__icontains=search) |
            Q(applicant__last_name__icontains=search)
        )

    if status != 'all':
        applications = applications.filter(status=status)

    # Group by candidate (in case they applied to multiple jobs)
    candidates = {}
    for app in applications:
        user_id = app.applicant.id
        if user_id not in candidates:
            # Get resume info
            resume = None
            try:
                resume = app.applicant.resumes.first()
            except:
                pass

            candidates[user_id] = {
                'user_id': user_id,
                'name': f"{app.applicant.first_name} {app.applicant.last_name}".strip() or app.applicant.email,
                'email': app.applicant.email,
                'location': getattr(app.applicant.profile, 'location', ''),
                'headline': getattr(app.applicant.profile, 'headline', ''),
                'skills': getattr(app.applicant.profile, 'skills', []),
                'applications': [],
                'best_match_score': 0,
                'resume_id': resume.id if resume else None,
                'resume_skills': resume.extracted_skills if resume and resume.extracted_skills else [],
            }

        # Update application info
        candidates[user_id]['applications'].append({
            'job_id': app.job.id,
            'job_title': app.job.title,
            'status': app.status,
            'applied_at': app.created_at.isoformat(),
        })

        # Update best match score
        if app.match_score > candidates[user_id]['best_match_score']:
            candidates[user_id]['best_match_score'] = app.match_score

    # Convert to list and sort by match score
    candidates_list = list(candidates.values())
    candidates_list.sort(key=lambda x: x['best_match_score'], reverse=True)

    # Paginate
    paginator = Paginator(candidates_list, per_page)
    page_obj = paginator.get_page(page)

    return JsonResponse({
        'candidates': list(page_obj),
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
@role_required(['recruiter', 'admin'])
def ai_shortlist_candidates(request):
    """AI-powered candidate shortlisting"""
    user = request.user

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    job_id = data.get('job_id')
    min_match_score = data.get('min_match_score', 70)

    if not job_id:
        return JsonResponse({'error': 'job_id is required'}, status=400)

    # Verify job belongs to recruiter
    try:
        job = JobPost.objects.get(id=job_id, posted_by=user)
    except JobPost.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404)

    # Get all applications for this job
    applications = job.applications.select_related('applicant').order_by('-match_score')

    # Filter by minimum score
    qualified_candidates = []
    for app in applications:
        if app.match_score >= min_match_score:
            qualified_candidates.append({
                'application_id': app.id,
                'candidate': {
                    'id': app.applicant.id,
                    'name': f"{app.applicant.first_name} {app.applicant.last_name}".strip() or app.applicant.email,
                    'email': app.applicant.email,
                    'skills': getattr(app.applicant.profile, 'skills', []),
                },
                'match_score': app.match_score,
                'status': app.status,
                'ai_recommendation': 'highly_recommended' if app.match_score >= 85 else 'recommended',
            })

    # Create notification
    Notification.objects.create(
        user=user,
        type=Notification.NotificationType.APPLICATION,
        title="AI Shortlisting Complete",
        message=f"Found {len(qualified_candidates)} qualified candidates for {job.title}",
    )

    return JsonResponse({
        'job': {'id': job.id, 'title': job.title},
        'total_applicants': applications.count(),
        'qualified_candidates': len(qualified_candidates),
        'candidates': qualified_candidates,
        'filter_criteria': {
            'min_match_score': min_match_score,
        }
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
@role_required(['recruiter', 'admin'])
def candidate_detail(request, candidate_id):
    """Get detailed candidate profile"""
    user = request.user

    # Verify recruiter has posted jobs
    recruiter_job_ids = JobPost.objects.filter(posted_by=user).values_list('id', flat=True)

    # Check if candidate has applied to recruiter's jobs
    applications = JobApplication.objects.filter(
        applicant_id=candidate_id,
        job_id__in=recruiter_job_ids
    ).select_related('job', 'resume')

    if not applications.exists():
        return JsonResponse({'error': 'Candidate not found'}, status=404)

    # Get candidate details
    candidate = applications.first().applicant

    # Get all resumes
    resumes = Resume.objects.filter(user=candidate)

    # Get profile
    try:
        profile = candidate.profile
    except:
        profile = None

    return JsonResponse({
        'candidate': {
            'id': candidate.id,
            'name': f"{candidate.first_name} {candidate.last_name}".strip(),
            'email': candidate.email,
            'role': candidate.role,
            'profile': {
                'headline': getattr(profile, 'headline', ''),
                'bio': getattr(profile, 'bio', ''),
                'location': getattr(profile, 'location', ''),
                'skills': getattr(profile, 'skills', []),
                'github_url': getattr(profile, 'github_url', ''),
                'linkedin_url': getattr(profile, 'linkedin_url', ''),
            } if profile else None,
        },
        'applications': [
            {
                'id': app.id,
                'job': {'id': app.job.id, 'title': app.job.title, 'company': app.job.company},
                'status': app.status,
                'match_score': app.match_score,
                'applied_at': app.created_at.isoformat(),
                'cover_note': app.cover_note,
            }
            for app in applications
        ],
        'resumes': [
            {
                'id': resume.id,
                'name': resume.original_name,
                'uploaded_at': resume.uploaded_at.isoformat(),
                'skills': resume.extracted_skills or [],
            }
            for resume in resumes
        ],
    })


@csrf_exempt
@require_http_methods(["POST"])
@jwt_required
@role_required(['recruiter', 'admin'])
def update_application_status(request):
    """Update application status"""
    user = request.user

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    application_id = data.get('application_id')
    new_status = data.get('status')

    if not application_id or not new_status:
        return JsonResponse({'error': 'application_id and status are required'}, status=400)

    # Verify the application is for recruiter's job
    try:
        application = JobApplication.objects.select_related('job').get(
            id=application_id,
            job__posted_by=user
        )
    except JobApplication.DoesNotExist:
        return JsonResponse({'error': 'Application not found'}, status=404)

    # Update status
    old_status = application.status
    application.status = new_status
    application.save()

    # Create notification for candidate
    Notification.objects.create(
        user=application.applicant,
        type=Notification.NotificationType.APPLICATION,
        title=f"Application Status Update: {application.job.title}",
        message=f"Your application status changed from {old_status} to {new_status}",
        related_application=application,
    )

    return JsonResponse({
        'message': 'Status updated successfully',
        'application': {
            'id': application.id,
            'status': application.status,
        }
    })


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required
@role_required(['recruiter', 'admin'])
def recruiter_analytics(request):
    """Get recruiter analytics and insights"""
    user = request.user

    # Get all jobs posted by recruiter
    posted_jobs = JobPost.objects.filter(posted_by=user)
    job_ids = posted_jobs.values_list('id', flat=True)

    # Get all applications
    applications = JobApplication.objects.filter(job_id__in=job_ids)

    # Time-based stats
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    applications_this_week = applications.filter(created_at__date__gte=week_ago).count()
    applications_this_month = applications.filter(created_at__date__gte=month_ago).count()

    # Status breakdown
    status_counts = applications.values('status').annotate(count=Count('id'))

    # Top performing jobs
    top_jobs = posted_jobs.annotate(
        app_count=Count('applications')
    ).order_by('-app_count')[:5]

    # Average match score
    avg_match = applications.aggregate(Avg('match_score'))['match_score__avg'] or 0

    return JsonResponse({
        'overview': {
            'total_jobs': posted_jobs.count(),
            'total_applications': applications.count(),
            'applications_this_week': applications_this_week,
            'applications_this_month': applications_this_month,
            'average_match_score': round(avg_match, 1),
        },
        'by_status': {item['status']: item['count'] for item in status_counts},
        'top_jobs': [
            {
                'id': job.id,
                'title': job.title,
                'applications': job.applications.count(),
                'views': job.views_count,
            }
            for job in top_jobs
        ],
    })