"""
Analytics Export - Export data to Excel/CSV
"""
import io
import csv
import xlsxwriter
from django.http import HttpResponse
from django.db.models import Count, Sum, Avg
from jobs.models import JobPost, JobApplication, Resume, User
from accounts.models import User as AuthUser
from datetime import datetime, timedelta


class AnalyticsExporter:
    """Export analytics data to Excel/CSV"""

    @staticmethod
    def export_users(format='xlsx'):
        """Export user analytics"""
        users = AuthUser.objects.filter(is_active=True).select_related('profile')

        output = io.BytesIO()

        if format == 'xlsx':
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Users')

            # Headers
            headers = ['Email', 'Name', 'Role', 'University/Company', 'Skills', 'Joined Date']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)

            # Data
            for row, user in enumerate(users, start=1):
                worksheet.write(row, 0, user.email)
                worksheet.write(row, 1, f"{user.first_name} {user.last_name}")
                worksheet.write(row, 2, user.role)
                worksheet.write(row, 3, user.university_name or user.company_name or '')
                worksheet.write(row, 4, ', '.join(user.profile.skills or []))
                worksheet.write(row, 5, user.date_joined.strftime('%Y-%m-%d'))

            workbook.close()
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'users_export_{datetime.now().strftime("%Y%m%d")}.xlsx'
        else:
            # CSV
            writer = csv.writer(output)
            writer.writerow(['Email', 'Name', 'Role', 'University/Company', 'Skills', 'Joined Date'])

            for user in users:
                writer.writerow([
                    user.email,
                    f"{user.first_name} {user.last_name}",
                    user.role,
                    user.university_name or user.company_name or '',
                    ', '.join(user.profile.skills or []),
                    user.date_joined.strftime('%Y-%m-%d')
                ])

            content_type = 'text/csv'
            filename = f'users_export_{datetime.now().strftime("%Y%m%d")}.csv'

        output.seek(0)
        response = HttpResponse(output, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @staticmethod
    def export_jobs(format='xlsx'):
        """Export job analytics"""
        jobs = JobPost.objects.select_related('posted_by').order_by('-created_at')

        output = io.BytesIO()

        if format == 'xlsx':
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Jobs')

            headers = ['Title', 'Company', 'Location', 'Type', 'Salary', 'Posted By', 'Views', 'Applications', 'Created']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)

            for row, job in enumerate(jobs, start=1):
                app_count = job.applications.count()
                worksheet.write(row, 0, job.title)
                worksheet.write(row, 1, job.company)
                worksheet.write(row, 2, job.location)
                worksheet.write(row, 3, job.employment_type)
                worksheet.write(row, 4, job.salary_range or 'Not specified')
                worksheet.write(row, 5, job.posted_by.email)
                worksheet.write(row, 6, job.views_count)
                worksheet.write(row, 7, app_count)
                worksheet.write(row, 8, job.created_at.strftime('%Y-%m-%d'))

            workbook.close()
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'jobs_export_{datetime.now().strftime("%Y%m%d")}.xlsx'
        else:
            writer = csv.writer(output)
            writer.writerow(headers)

            for job in jobs:
                writer.writerow([
                    job.title, job.company, job.location, job.employment_type,
                    job.salary_range or 'Not specified', job.posted_by.email,
                    job.views_count, job.applications.count(), job.created_at.strftime('%Y-%m-%d')
                ])

            content_type = 'text/csv'
            filename = f'jobs_export_{datetime.now().strftime("%Y%m%d")}.csv'

        output.seek(0)
        response = HttpResponse(output, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @staticmethod
    def export_applications(format='xlsx'):
        """Export application analytics"""
        applications = JobApplication.objects.select_related(
            'applicant', 'job'
        ).order_by('-created_at')

        output = io.BytesIO()

        if format == 'xlsx':
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet('Applications')

            headers = ['Candidate', 'Job Title', 'Company', 'Status', 'Match Score', 'Applied Date']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)

            for row, app in enumerate(applications, start=1):
                worksheet.write(row, 0, app.applicant.email)
                worksheet.write(row, 1, app.job.title)
                worksheet.write(row, 2, app.job.company)
                worksheet.write(row, 3, app.status)
                worksheet.write(row, 4, app.match_score)
                worksheet.write(row, 5, app.created_at.strftime('%Y-%m-%d'))

            workbook.close()
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'applications_export_{datetime.now().strftime("%Y%m%d")}.xlsx'
        else:
            writer = csv.writer(output)
            writer.writerow(headers)

            for app in applications:
                writer.writerow([
                    app.applicant.email, app.job.title, app.job.company,
                    app.status, app.match_score, app.created_at.strftime('%Y-%m-%d')
                ])

            content_type = 'text/csv'
            filename = f'applications_export_{datetime.now().strftime("%Y%m%d")}.csv'

        output.seek(0)
        response = HttpResponse(output, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @staticmethod
    def export_full_analytics(format='xlsx'):
        """Export comprehensive analytics report"""
        output = io.BytesIO()

        if format == 'xlsx':
            workbook = xlsxwriter.Workbook(output)

            # Summary Sheet
            summary = workbook.add_worksheet('Summary')

            # Stats
            total_users = AuthUser.objects.filter(is_active=True).count()
            total_jobs = JobPost.objects.filter(is_active=True).count()
            total_applications = JobApplication.objects.count()
            total_resumes = Resume.objects.count()

            summary.write(0, 0, 'AI Job Platform Analytics Report')
            summary.write(2, 0, 'Metric')
            summary.write(2, 1, 'Value')
            summary.write(3, 0, 'Total Users')
            summary.write(3, 1, total_users)
            summary.write(4, 0, 'Total Jobs')
            summary.write(4, 1, total_jobs)
            summary.write(5, 0, 'Total Applications')
            summary.write(5, 1, total_applications)
            summary.write(6, 0, 'Total Resumes')
            summary.write(6, 1, total_resumes)

            # Role breakdown
            roles = AuthUser.objects.values('role').annotate(count=Count('id'))
            summary.write(8, 0, 'Users by Role')
            summary.write(9, 0, 'Role')
            summary.write(9, 1, 'Count')
            for i, role in enumerate(roles, start=10):
                summary.write(i, 0, role['role'])
                summary.write(i, 1, role['count'])

            # Applications by status
            statuses = JobApplication.objects.values('status').annotate(count=Count('id'))
            summary.write(15, 0, 'Applications by Status')
            summary.write(16, 0, 'Status')
            summary.write(16, 1, 'Count')
            for i, status in enumerate(statuses, start=17):
                summary.write(i, 0, status['status'])
                summary.write(i, 1, status['count'])

            workbook.close()
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f'analytics_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        else:
            # Simple CSV
            writer = csv.writer(output)
            writer.writerow(['AI Job Platform Analytics'])

            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Users', AuthUser.objects.filter(is_active=True).count()])
            writer.writerow(['Total Jobs', JobPost.objects.filter(is_active=True).count()])
            writer.writerow(['Total Applications', JobApplication.objects.count()])

            content_type = 'text/csv'
            filename = f'analytics_report_{datetime.now().strftime("%Y%m%d")}.csv'

        output.seek(0)
        response = HttpResponse(output, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# =================== VIEWS ===================

"""
Add to views.py:

from .analytics_export import AnalyticsExporter

def export_analytics(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin only'}, status=403)

    export_type = request.GET.get('type', 'all')
    export_format = request.GET.get('format', 'xlsx')

    if export_type == 'users':
        return AnalyticsExporter.export_users(export_format)
    elif export_type == 'jobs':
        return AnalyticsExporter.export_jobs(export_format)
    elif export_type == 'applications':
        return AnalyticsExporter.export_applications(export_format)
    else:
        return AnalyticsExporter.export_full_analytics(export_format)
"""

# =================== URLS ===================

"""
Add to urls.py:
path('analytics/export/', views.export_analytics, name='analytics-export'),
"""