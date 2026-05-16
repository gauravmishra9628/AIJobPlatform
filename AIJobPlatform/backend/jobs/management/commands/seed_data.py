"""
Management command to create sample data for testing
Usage: python manage.py seed_data --users=10 --jobs=50
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from jobs.models import JobPost, JobApplication, Resume
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=10, help='Number of users to create')
        parser.add_argument('--jobs', type=int, default=20, help='Number of jobs to create')
        parser.add_argument('--applications', type=int, default=50, help='Number of applications to create')

    def handle(self, *args, **options):
        num_users = options['users']
        num_jobs = options['jobs']
        num_applications = options['applications']

        self.stdout.write('Creating sample data...')

        # Create students
        students = []
        for i in range(num_users):
            user, created = User.objects.get_or_create(
                email=f'student{i}@example.com',
                defaults={
                    'first_name': f'Student{i}',
                    'last_name': 'User',
                    'role': 'student',
                    'university_name': random.choice(['MIT', 'Stanford', 'Harvard', 'Berkeley']),
                    'is_email_verified': True
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            students.append(user)

        # Create recruiters
        recruiters = []
        for i in range(5):
            user, created = User.objects.get_or_create(
                email=f'recruiter{i}@example.com',
                defaults={
                    'first_name': f'Recruiter{i}',
                    'last_name': 'User',
                    'role': 'recruiter',
                    'company_name': random.choice(['Google', 'Microsoft', 'Amazon', 'Meta', 'StartupInc']),
                    'is_email_verified': True
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            recruiters.append(user)

        self.stdout.write(self.style.SUCCESS(f'Created {len(students)} students and {len(recruiters)} recruiters'))

        # Create jobs
        job_titles = [
            'Python Developer', 'Frontend Developer', 'Backend Engineer',
            'Full Stack Developer', 'Data Scientist', 'ML Engineer',
            'DevOps Engineer', 'Product Manager', 'UI/UX Designer'
        ]
        companies = ['TechCorp', 'DataInc', 'WebSolutions', 'CloudBase', 'AppWorks']
        locations = ['Remote', 'San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX']
        skills_list = [
            'Python,Django,React', 'JavaScript,Node.js,SQL',
            'Python,TensorFlow,Kubernetes', 'AWS,Docker,Linux',
            'React,TypeScript,GraphQL', 'Java,SpringBoot,PostgreSQL'
        ]

        jobs = []
        for i in range(num_jobs):
            recruiter = random.choice(recruiters)
            job, created = JobPost.objects.get_or_create(
                title=f"{random.choice(job_titles)} {i}",
                company=random.choice(companies),
                defaults={
                    'posted_by': recruiter,
                    'location': random.choice(locations),
                    'description': 'We are looking for a talented developer to join our team. '
                                   'Responsibilities include designing and building applications.',
                    'skills_required': random.choice(skills_list),
                    'employment_type': random.choice(['full-time', 'part-time', 'internship']),
                    'salary_range': f'${random.randint(50, 150)}k - ${random.randint(80, 200)}k',
                    'is_active': True
                }
            )
            if created:
                job.save()
            jobs.append(job)

        self.stdout.write(self.style.SUCCESS(f'Created {len(jobs)} jobs'))

        # Create applications
        statuses = ['applied', 'reviewing', 'shortlisted', 'rejected']
        for _ in range(num_applications):
            student = random.choice(students)
            job = random.choice(jobs)
            if not JobApplication.objects.filter(applicant=student, job=job).exists():
                JobApplication.objects.create(
                    applicant=student,
                    job=job,
                    status=random.choice(statuses),
                    cover_note=f"I'm excited to apply for this position. "
                               f"My background in {random.choice(['Python', 'JavaScript', 'Data Science'])} "
                               f"makes me a great fit.",
                    match_score=random.randint(30, 95)
                )

        self.stdout.write(self.style.SUCCESS(f'Created {num_applications} applications'))
        self.stdout.write(self.style.SUCCESS('Sample data creation complete!'))

        # Print test credentials
        self.stdout.write('')
        self.stdout.write('Test Credentials:')
        self.stdout.write('  Student: student0@example.com / testpass123')
        self.stdout.write('  Recruiter: recruiter0@example.com / testpass123')
        self.stdout.write('  Admin: Check database')