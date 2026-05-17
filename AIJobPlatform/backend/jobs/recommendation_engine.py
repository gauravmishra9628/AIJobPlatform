"""
AI Job Recommendation Engine
Provides personalized job recommendations based on user profile, skills, and activity
"""
from django.db.models import Q, Count
from django.db.models.functions import Coalesce
from jobs.models import JobPost, JobApplication, Resume, User
from accounts.models import User as AuthUser
from typing import List, Dict, Optional
import numpy as np
from collections import defaultdict


class JobRecommendationEngine:
    """AI-powered job recommendation system using multiple signals"""

    def __init__(self):
        self.openai_key = None

    def get_recommendations(self, user_id: int, limit: int = 10, use_ai: bool = True) -> List[Dict]:
        """
        Get personalized job recommendations for a user

        Args:
            user_id: User ID
            limit: Number of recommendations to return
            use_ai: Whether to use AI for enhanced recommendations

        Returns:
            List of recommended jobs with scores
        """
        try:
            user = AuthUser.objects.get(id=user_id)
        except AuthUser.DoesNotExist:
            return []

        # Get user's skills from profile
        user_skills = self._get_user_skills(user)

        # Get user's resume skills
        resume_skills = self._get_resume_skills(user)

        # Combine all skills
        all_skills = list(set(user_skills + resume_skills))

        # Get applied job IDs to exclude
        applied_job_ids = set(
            JobApplication.objects.filter(applicant=user)
            .values_list('job_id', flat=True)
        )

        # Get recommendations using multiple signals
        recommendations = []

        # 1. Skill-based matching
        skill_matches = self._skill_based_recommendations(all_skills, applied_job_ids)
        recommendations.extend(skill_matches)

        # 2. Title/role based matching
        role_matches = self._role_based_recommendations(user, applied_job_ids)
        recommendations.extend(role_matches)

        # 3. Activity-based (similar users also applied)
        activity_matches = self._activity_based_recommendations(user_id, applied_job_ids)
        recommendations.extend(activity_matches)

        # 4. Location-based
        location_matches = self._location_based_recommendations(user, applied_job_ids)
        recommendations.extend(location_matches)

        # Combine and deduplicate
        combined = self._combine_recommendations(recommendations)

        # Sort by score
        sorted_recommendations = sorted(combined, key=lambda x: x['score'], reverse=True)

        # Apply AI enhancement if enabled
        if use_ai and self.openai_key:
            sorted_recommendations = self._ai_enhance_recommendations(
                user, all_skills, sorted_recommendations
            )

        return sorted_recommendations[:limit]

    def _get_user_skills(self, user) -> List[str]:
        """Get skills from user's profile"""
        try:
            profile = user.profile
            skills = profile.skills or []
            # Extract individual skills from skill strings
            extracted = []
            for skill in skills:
                if isinstance(skill, str):
                    # Handle comma-separated skills
                    extracted.extend([s.strip() for s in skill.split(',')])
                else:
                    extracted.append(str(skill))
            return [s.lower() for s in extracted if s]
        except:
            return []

    def _get_resume_skills(self, user) -> List[str]:
        """Get skills from user's uploaded resumes"""
        try:
            resumes = Resume.objects.filter(user=user)
            skills = []
            for resume in resumes:
                if resume.extracted_skills:
                    skills.extend(resume.extracted_skills)
                if resume.parsed_skills:
                    skills.extend(resume.parsed_skills)
            return [s.lower() for s in skills if s]
        except:
            return []

    def _skill_based_recommendations(self, skills: List[str], exclude_ids: set) -> List[Dict]:
        """Recommend jobs based on skill matching"""
        if not skills:
            return []

        # Build OR query for skills
        skills_query = Q()
        for skill in skills[:10]:  # Limit to avoid query too complex
            skills_query |= Q(skills_required__icontains=skill)

        jobs = JobPost.objects.filter(
            skills_query,
            is_active=True
        ).exclude(id__in=exclude_ids).select_related('posted_by')[:50]

        recommendations = []
        for job in jobs:
            # Calculate skill match score
            job_text = (job.skills_required or '').lower()
            matched_skills = [s for s in skills if s in job_text]
            match_score = len(matched_skills) / max(len(skills), 1) * 100

            recommendations.append({
                'job': job,
                'score': match_score * 0.4,  # Weight: 40% for skills
                'match_type': 'skill',
                'matched_skills': matched_skills,
                'match_details': f"Matched {len(matched_skills)} skills"
            })

        return recommendations

    def _role_based_recommendations(self, user, exclude_ids: set) -> List[Dict]:
        """Recommend jobs based on user's role preferences"""
        # Get user's headline/title
        try:
            headline = (user.profile.headline or '').lower()
        except:
            headline = ''

        if not headline:
            return []

        # Extract role keywords from headline
        role_keywords = []
        roles = ['developer', 'engineer', 'manager', 'analyst', 'designer', 'specialist', 'lead', 'intern']
        for role in roles:
            if role in headline:
                role_keywords.append(role)

        if not role_keywords:
            return []

        # Find matching jobs
        query = Q()
        for keyword in role_keywords:
            query |= Q(title__icontains=keyword)

        jobs = JobPost.objects.filter(
            query,
            is_active=True
        ).exclude(id__in=exclude_ids).select_related('posted_by')[:30]

        recommendations = []
        for job in jobs:
            recommendations.append({
                'job': job,
                'score': 30,  # Moderate score for role match
                'match_type': 'role',
                'matched_skills': [],
                'match_details': 'Matches your role preferences'
            })

        return recommendations

    def _activity_based_recommendations(self, user_id: int, exclude_ids: set) -> List[Dict]:
        """Recommend jobs based on what similar users applied to"""
        # Get jobs that similar users applied to
        # "Similar" = users with similar skills (simplified version)

        # Get jobs with high application count
        popular_jobs = JobPost.objects.filter(
            is_active=True
        ).exclude(
            id__in=exclude_ids
        ).annotate(
            app_count=Count('applications')
        ).filter(
            app_count__gte=3
        ).order_by('-app_count').select_related('posted_by')[:20]

        recommendations = []
        for job in popular_jobs:
            recommendations.append({
                'job': job,
                'score': 20,  # Lower score for activity-based
                'match_type': 'popular',
                'matched_skills': [],
                'match_details': f"{job.applications.count()} people applied"
            })

        return recommendations

    def _location_based_recommendations(self, user, exclude_ids: set) -> List[Dict]:
        """Recommend jobs based on user location preference"""
        try:
            location = (user.profile.location or '').lower()
        except:
            location = ''

        if not location:
            return []

        # Extract city/region
        location_parts = location.split(',')
        if not location_parts:
            return []

        primary_location = location_parts[0].strip()

        # Find jobs in same location
        jobs = JobPost.objects.filter(
            location__icontains=primary_location,
            is_active=True
        ).exclude(id__in=exclude_ids).select_related('posted_by')[:20]

        recommendations = []
        for job in jobs:
            recommendations.append({
                'job': job,
                'score': 15,  # Lower score for location
                'match_type': 'location',
                'matched_skills': [],
                'match_details': f"Located in {job.location}"
            })

        return recommendations

    def _combine_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Combine duplicate jobs and sum their scores"""
        job_scores = defaultdict(lambda: {'score': 0, 'types': [], 'details': ''})

        for rec in recommendations:
            job_id = rec['job'].id
            job_scores[job_id]['score'] += rec['score']
            job_scores[job_id]['types'].append(rec['match_type'])
            job_scores[job_id]['details'] = rec['match_details']

        # Create final combined list
        combined = []
        seen_jobs = set()

        for rec in recommendations:
            job_id = rec['job'].id
            if job_id not in seen_jobs:
                seen_jobs.add(job_id)
                combined.append({
                    'job': rec['job'],
                    'score': min(job_scores[job_id]['score'], 100),  # Cap at 100
                    'match_types': list(set(job_scores[job_id]['types'])),
                    'match_details': job_scores[job_id]['details']
                })

        return combined

    def _ai_enhance_recommendations(self, user, skills: List[str], recommendations: List[Dict]) -> List[Dict]:
        """Use AI to enhance and re-rank recommendations"""
        # Simplified version - in production this would call OpenAI
        # to provide better matching and explanations

        # For now, just boost scores for jobs with good match
        for rec in recommendations:
            job = rec['job']
            job_text = f"{job.title} {job.description} {job.skills_required}".lower()

            # Boost for fresh jobs (posted in last 7 days)
            from django.utils import timezone
            from datetime import timedelta
            if (timezone.now() - job.created_at) < timedelta(days=7):
                rec['score'] = min(rec['score'] + 10, 100)
                rec['match_details'] += " • Recently posted"

            # Boost for high match percentage
            if 'skill' in rec['match_types'] and rec['score'] > 50:
                rec['match_details'] += " • Great skill match"

        return sorted(recommendations, key=lambda x: x['score'], reverse=True)

    def get_skill_based_jobs(self, skills: List[str], limit: int = 20) -> List[JobPost]:
        """Get jobs matching specific skills (for skill gap analysis)"""
        if not skills:
            return []

        query = Q()
        for skill in skills[:15]:
            query |= Q(skills_required__icontains=skill)

        return JobPost.objects.filter(
            query,
            is_active=True
        ).select_related('posted_by')[:limit]

    def get_recommendation_explanation(self, job: JobPost, user_id: int) -> str:
        """Get human-readable explanation for why a job was recommended"""
        try:
            user = AuthUser.objects.get(id=user_id)
        except:
            return "Based on available job listings"

        explanations = []

        # Check skill match
        user_skills = self._get_user_skills(user) + self._get_resume_skills(user)
        if user_skills:
            job_skills = (job.skills_required or '').lower()
            matched = [s for s in user_skills if s in job_skills]
            if matched:
                explanations.append(f"Your skills in {', '.join(matched[:3])} match this role")

        # Check location
        try:
            user_location = (user.profile.location or '').lower()
            if user_location and user_location.split(',')[0].strip() in job.location.lower():
                explanations.append("Matches your preferred location")
        except:
            pass

        # Check recent activity
        if explanations:
            return " • ".join(explanations)

        return "Matches your profile and preferences"


# Singleton instance
recommendation_engine = JobRecommendationEngine()


# =================== API FUNCTIONS ===================

def get_job_recommendations(user_id: int, limit: int = 10) -> List[Dict]:
    """Get job recommendations for a user"""
    return recommendation_engine.get_recommendations(user_id, limit)


def explain_recommendation(job_id: int, user_id: int) -> str:
    """Get explanation for a job recommendation"""
    try:
        job = JobPost.objects.get(id=job_id)
        return recommendation_engine.get_recommendation_explanation(job, user_id)
    except:
        return "Based on your profile"


def get_skill_matched_jobs(skills: List[str], limit: int = 20) -> List[JobPost]:
    """Get jobs matching specific skills"""
    return recommendation_engine.get_skill_based_jobs(skills, limit)