"""
GitHub and LinkedIn Import
Import profile data, skills, experience from social platforms
"""
import os
import requests
from typing import Dict, List, Optional
from django.db.models import Q
from jobs.models import Resume
from django.contrib.auth import get_user_model
from jobs.models import Resume
User = get_user_model()
from accounts.models import User as AuthUser


class GitHubImporter:
    """Import profile data from GitHub"""

    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.environ.get('GITHUB_TOKEN', '')
        self.api_base = 'https://api.github.com'

    def get_headers(self) -> Dict:
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.access_token:
            headers['Authorization'] = f'token {self.access_token}'
        return headers

    def import_profile(self, username: str) -> Dict:
        """Import full GitHub profile"""
        try:
            # Get user info
            user_data = self._get_user(username)
            if not user_data:
                return {'error': 'User not found'}

            # Get repositories
            repos = self._get_repositories(username)

            # Get skills from repo languages
            languages = self._get_language_stats(repos)

            # Get contributions/activity
            contributions = self._get_contributions(user_data)

            return {
                'success': True,
                'profile': {
                    'name': user_data.get('name', username),
                    'username': username,
                    'bio': user_data.get('bio', ''),
                    'location': user_data.get('location', ''),
                    'blog': user_data.get('blog', ''),
                    'company': user_data.get('company', ''),
                    'followers': user_data.get('followers', 0),
                    'public_repos': user_data.get('public_repos', 0),
                },
                'skills': list(languages.keys()),
                'languages': languages,
                'repositories': self._format_repos(repos),
                'contributions': contributions,
                'imported_from': 'github',
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_user(self, username: str) -> Optional[Dict]:
        url = f'{self.api_base}/users/{username}'
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            return response.json()
        return None

    def _get_repositories(self, username: str) -> List[Dict]:
        url = f'{self.api_base}/users/{username}/repos?sort=updated&per_page=100'
        response = requests.get(url, headers=self.get_headers())
        if response.status_code == 200:
            return response.json()
        return []

    def _get_language_stats(self, repos: List[Dict]) -> Dict[str, int]:
        """Get language usage statistics"""
        languages = {}
        for repo in repos[:50]:  # Limit to 50 repos
            lang = repo.get('language')
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        return languages

    def _get_contributions(self, user_data: Dict) -> Dict:
        """Get contribution stats"""
        return {
            'followers': user_data.get('followers', 0),
            'following': user_data.get('following', 0),
            'public_repos': user_data.get('public_repos', 0),
            'total_commits': 0,  # Requires additional API calls
        }

    def _format_repos(self, repos: List[Dict]) -> List[Dict]:
        """Format repository data"""
        return [
            {
                'name': repo.get('name', ''),
                'description': repo.get('description', ''),
                'language': repo.get('language', ''),
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'url': repo.get('html_url', ''),
                'updated': repo.get('updated_at', ''),
            }
            for repo in repos[:10]  # Top 10 repos
        ]


class LinkedInImporter:
    """Import profile data from LinkedIn"""

    # Note: LinkedIn API is strict - requires OAuth or scraping
    # This provides a manual input form as fallback

    @staticmethod
    def parse_imported_data(data: Dict) -> Dict:
        """Parse manually imported LinkedIn data"""

        # Extract experience
        experiences = []
        for exp in data.get('experience', []):
            experiences.append({
                'title': exp.get('title', ''),
                'company': exp.get('company', ''),
                'duration': exp.get('duration', ''),
                'description': exp.get('description', ''),
            })

        # Extract education
        education = []
        for edu in data.get('education', []):
            education.append({
                'school': edu.get('school', ''),
                'degree': edu.get('degree', ''),
                'field': edu.get('field', ''),
                'year': edu.get('year', ''),
            })

        # Extract skills
        skills = [s.get('name', '') for s in data.get('skills', [])]

        return {
            'success': True,
            'profile': {
                'name': data.get('name', ''),
                'headline': data.get('headline', ''),
                'location': data.get('location', ''),
                'summary': data.get('summary', ''),
            },
            'experience': experiences,
            'education': education,
            'skills': skills,
            'imported_from': 'linkedin',
        }

    @staticmethod
    def generate_questions_for_import() -> List[Dict]:
        """Questions to guide manual import"""
        return [
            {
                'section': 'Basic Info',
                'questions': [
                    {'id': 'name', 'label': 'Full Name', 'type': 'text', 'required': True},
                    {'id': 'headline', 'label': 'Professional Headline', 'type': 'text', 'required': True},
                    {'id': 'location', 'label': 'Location', 'type': 'text', 'required': False},
                ]
            },
            {
                'section': 'Work Experience',
                'questions': [
                    {'id': 'company', 'label': 'Company Name', 'type': 'text', 'required': True},
                    {'id': 'title', 'label': 'Job Title', 'type': 'text', 'required': True},
                    {'id': 'duration', 'label': 'Duration', 'type': 'text', 'placeholder': 'e.g., Jan 2020 - Present'},
                ]
            },
            {
                'section': 'Skills',
                'questions': [
                    {'id': 'skills', 'label': 'Skills (comma-separated)', 'type': 'tags', 'placeholder': 'Python, Django, React...'},
                ]
            },
        ]


def import_github_profile(username: str, user_id: int) -> Dict:
    """Import GitHub profile and save to user"""
    importer = GitHubImporter()
    result = importer.import_profile(username)

    if result.get('success'):
        # Save to user's profile
        try:
            user = AuthUser.objects.get(id=user_id)
            profile = user.profile

            # Update profile with GitHub data
            if result['profile'].get('bio'):
                profile.bio = result['profile']['bio']
            if result['profile'].get('location') and not profile.location:
                profile.location = result['profile']['location']

            # Add GitHub skills
            existing_skills = profile.skills or []
            new_skills = list(set(existing_skills + result['skills']))
            profile.skills = new_skills

            profile.save()

            # Create a resume entry if none exists
            resume, created = Resume.objects.get_or_create(
                user=user,
                defaults={
                    'file_name': f'{username}_github',
                    'extracted_skills': result['skills'],
                    'parsed_summary': result['profile'].get('bio', ''),
                }
            )

            result['saved'] = True

        except Exception as e:
            result['saved'] = False
            result['save_error'] = str(e)

    return result


def import_linkedin_data(data: Dict, user_id: int) -> Dict:
    """Import manually entered LinkedIn data"""
    result = LinkedInImporter.parse_imported_data(data)

    if result.get('success'):
        try:
            user = AuthUser.objects.get(id=user_id)
            profile = user.profile

            # Update profile
            if result['profile'].get('headline') and not profile.headline:
                profile.headline = result['profile']['headline']
            if result['profile'].get('location') and not profile.location:
                profile.location = result['profile']['location']

            # Add skills
            existing_skills = profile.skills or []
            new_skills = list(set(existing_skills + result['skills']))
            profile.skills = new_skills

            profile.save()

            # Create resume
            resume, created = Resume.objects.get_or_create(
                user=user,
                defaults={
                    'file_name': 'linkedin_import',
                    'extracted_skills': result['skills'],
                    'parsed_summary': result['profile'].get('summary', ''),
                }
            )

            result['saved'] = True

        except Exception as e:
            result['saved'] = False
            result['save_error'] = str(e)

    return result