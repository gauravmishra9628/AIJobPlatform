"""
Pytest Configuration and Fixtures
"""
import pytest
from django.conf import settings
from rest_framework.test import APIClient
from accounts.models import User, Profile


@pytest.fixture(scope='session')
def django_db_setup():
    """Setup test database"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def api_client():
    """Return an API client for testing"""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create_user(
        email='testuser@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        role='student',
        university_name='Test University'
    )


@pytest.fixture
def recruiter(db):
    """Create a test recruiter"""
    return User.objects.create_user(
        email='recruiter@example.com',
        password='testpass123',
        first_name='Recruiter',
        last_name='User',
        role='recruiter',
        company_name='Test Company'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def authenticated_recruiter(api_client, recruiter):
    """Return an authenticated recruiter client"""
    api_client.force_authenticate(user=recruiter)
    return api_client


@pytest.fixture
def user_profile(db, user):
    """Return user profile with sample data"""
    profile = user.profile
    profile.headline = 'Software Developer'
    profile.bio = 'Experienced developer'
    profile.skills = ['Python', 'Django', 'React', 'JavaScript']
    profile.location = 'San Francisco, CA'
    profile.github_url = 'https://github.com/testuser'
    profile.linkedin_url = 'https://linkedin.com/in/testuser'
    profile.save()
    return profile


@pytest.fixture
def sample_job_data():
    """Return sample job data for testing"""
    return {
        'title': 'Python Developer',
        'company': 'Tech Corp',
        'location': 'Remote',
        'description': 'We are looking for a Python developer...',
        'skills_required': 'Python, Django, REST API',
        'employment_type': 'full-time',
        'salary_range': '$80,000 - $120,000',
        'required_experience_years': 2
    }


@pytest.fixture
def sample_resume_data():
    """Return sample resume data for testing"""
    return {
        'original_name': 'test_resume.pdf',
        'extracted_text': '''
        John Doe
        Software Developer
        Email: john@example.com

        Experience:
        - Senior Developer at Tech Corp (2020-Present)
        - Developer at Startup Inc (2018-2020)

        Skills:
        Python, Django, React, JavaScript, PostgreSQL, AWS

        Education:
        BS Computer Science, MIT
        ''',
        'extracted_skills': ['Python', 'Django', 'React', 'JavaScript', 'PostgreSQL', 'AWS'],
        'experience_years': 5
    }