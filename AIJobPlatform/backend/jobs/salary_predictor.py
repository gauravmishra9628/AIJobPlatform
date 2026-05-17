"""
AI Salary Prediction Service
Predicts salary based on skills, experience, location, and role
"""
from django.db.models import Avg, Max, Min
from jobs.models import JobPost, SkillMapping, Resume
from django.conf import settings
import numpy as np
from collections import defaultdict


class SalaryPredictor:
    """Predict salary based on various factors"""

    # Salary multipliers by experience
    EXPERIENCE_MULTIPLIERS = {
        0: 0.6,   # Entry level
        1: 0.7,   # 1 year
        2: 0.8,   # 2 years
        3: 0.9,   # 3 years
        5: 1.0,   # 5 years (baseline)
        7: 1.2,   # 7 years
        10: 1.4,  # 10 years
        15: 1.6,  # 15 years
        20: 1.8,  # 20+ years
    }

    # Location multipliers
    LOCATION_MULTIPLIERS = {
        # Tier 1 cities (highest)
        'san francisco': 1.5, 'new york': 1.45, 'seattle': 1.4,
        'los angeles': 1.3, 'boston': 1.25, 'washington': 1.2,
        # Tier 2 cities
        'austin': 1.15, 'chicago': 1.1, 'denver': 1.1,
        'denver': 1.1, 'atlanta': 1.0, 'dallas': 1.0,
        'phoenix': 0.95, 'miami': 0.95, 'portland': 0.95,
        # India
        'bangalore': 0.6, 'hyderabad': 0.55, 'pune': 0.55,
        'mumbai': 0.6, 'delhi': 0.55, 'chennai': 0.5,
    }

    # Skill salary weights
    SKILL_WEIGHTS = {
        # High-value skills
        'machine learning': 1.4, 'deep learning': 1.4, 'ai': 1.35,
        'data science': 1.3, 'blockchain': 1.25, 'docker': 1.15,
        'kubernetes': 1.2, 'aws': 1.15, 'gcp': 1.15,
        'azure': 1.1, 'python': 1.1, 'golang': 1.15,
        'rust': 1.2, 'scala': 1.15, 'spark': 1.2,
        # Medium-value skills
        'react': 1.05, 'angular': 1.0, 'vue': 1.0,
        'node': 1.05, 'django': 1.0, 'flask': 1.0,
        'sql': 1.0, 'postgresql': 1.05, 'mongodb': 1.0,
        'typescript': 1.05, 'javascript': 1.0,
    }

    BASE_SALARY = {
        'software engineer': 80000,
        'data scientist': 95000,
        'ml engineer': 110000,
        'devops engineer': 90000,
        'frontend developer': 75000,
        'backend developer': 85000,
        'full stack developer': 90000,
        'product manager': 95000,
        'data analyst': 65000,
        'ai engineer': 120000,
    }

    def __init__(self):
        self._load_skill_data()

    def _load_skill_data(self):
        """Load skill mapping data from database"""
        try:
            self.skill_mappings = {
                s.skill_name.lower(): s.market_weight
                for s in SkillMapping.objects.all()
            }
        except Exception:
            self.skill_mappings = {}

    def predict(self, role, skills, experience_years, location, employment_type='full-time'):
        """
        Predict salary for a given profile

        Args:
            role: Job title/role (e.g., 'Python Developer')
            skills: List of skills ['Python', 'Django', 'AWS']
            experience_years: Years of experience (int)
            location: City name
            employment_type: 'full-time', 'part-time', 'internship'

        Returns:
            dict with min, max, median salary and confidence
        """
        # Get base salary for role
        base = self._get_base_salary(role)

        # Calculate experience multiplier
        exp_mult = self._get_experience_multiplier(experience_years)

        # Calculate location multiplier
        loc_mult = self._get_location_multiplier(location)

        # Calculate skill multiplier
        skill_mult = self._get_skill_multiplier(skills)

        # Employment type adjustment
        type_mult = {
            'full-time': 1.0,
            'part-time': 0.5,
            'internship': 0.35,
            'contract': 0.8,
        }.get(employment_type, 1.0)

        # Calculate final salary range
        median = base * exp_mult * loc_mult * skill_mult * type_mult
        min_salary = median * 0.85
        max_salary = median * 1.15

        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(
            role, skills, experience_years, location
        )

        return {
            'min_salary': int(min_salary),
            'max_salary': int(max_salary),
            'median_salary': int(median),
            'currency': 'USD',
            'confidence': confidence,
            'breakdown': {
                'base': base,
                'experience_impact': f"{((exp_mult-1)*100):+.0f}%",
                'location_impact': f"{((loc_mult-1)*100):+.0f}%",
                'skill_impact': f"{((skill_mult-1)*100):+.0f}%",
            },
            'factors': {
                'experience_years': experience_years,
                'location': location.title(),
                'top_skills': skills[:5],
            }
        }

    def _get_base_salary(self, role):
        """Get base salary for role"""
        role_lower = role.lower()

        # Direct match
        for key, salary in self.BASE_SALARY.items():
            if key in role_lower:
                return salary

        # Partial match
        if 'data' in role_lower and 'science' in role_lower:
            return self.BASE_SALARY['data scientist']
        if 'ml' in role_lower or 'machine learning' in role_lower:
            return self.BASE_SALARY['ml engineer']
        if 'frontend' in role_lower or 'react' in role_lower:
            return self.BASE_SALARY['frontend developer']
        if 'backend' in role_lower or 'python' in role_lower:
            return self.BASE_SALARY['backend developer']
        if 'full stack' in role_lower:
            return self.BASE_SALARY['full stack developer']
        if 'devops' in role_lower or 'cloud' in role_lower:
            return self.BASE_SALARY['devops engineer']
        if 'product' in role_lower:
            return self.BASE_SALARY['product manager']
        if 'ai' in role_lower or 'artificial' in role_lower:
            return self.BASE_SALARY['ai engineer']

        return self.BASE_SALARY['software engineer']  # Default

    def _get_experience_multiplier(self, years):
        """Calculate experience multiplier"""
        if years <= 0:
            return self.EXPERIENCE_MULTIPLIERS[0]
        if years >= 20:
            return self.EXPERIENCE_MULTIPLIERS[20]

        # Interpolate between known points
        exp_levels = sorted(self.EXPERIENCE_MULTIPLIERS.keys())
        for i, level in enumerate(exp_levels):
            if years <= level:
                if i == 0:
                    return self.EXPERIENCE_MULTIPLIERS[level]
                prev_level = exp_levels[i-1]
                ratio = (years - prev_level) / (level - prev_level)
                return self.EXPERIENCE_MULTIPLIERS[prev_level] + \
                    ratio * (self.EXPERIENCE_MULTIPLIERS[level] - self.EXPERIENCE_MULTIPLIERS[prev_level])
        return 1.0

    def _get_location_multiplier(self, location):
        """Calculate location multiplier"""
        if not location:
            return 1.0

        loc_lower = location.lower()

        for key, mult in self.LOCATION_MULTIPLIERS.items():
            if key in loc_lower:
                return mult

        return 1.0  # Default for unknown locations

    def _get_skill_multiplier(self, skills):
        """Calculate skill-based multiplier"""
        if not skills:
            return 1.0

        total_weight = 0
        for skill in skills:
            skill_lower = skill.lower()

            # Check database mappings first
            if skill_lower in self.skill_mappings:
                total_weight += self.skill_mappings[skill_lower]
            # Check hardcoded weights
            elif skill_lower in self.SKILL_WEIGHTS:
                total_weight += self.SKILL_WEIGHTS[skill_lower]
            else:
                total_weight += 1.0

        # Normalize - average skill weight
        avg_weight = total_weight / len(skills)

        # Cap the multiplier
        return min(max(avg_weight, 0.8), 1.8)

    def _calculate_confidence(self, role, skills, experience, location):
        """Calculate prediction confidence"""
        score = 0.5  # Base confidence

        # Role known?
        if any(k in role.lower() for k in self.BASE_SALARY.keys()):
            score += 0.15

        # Has skills?
        if skills:
            score += min(len(skills) * 0.03, 0.2)

        # Has location?
        if location:
            score += 0.1

        # Has reasonable experience?
        if 0 <= experience <= 20:
            score += 0.1

        return min(score, 0.95)  # Cap at 95%

    def get_market_trends(self, role, location=None):
        """Get market salary trends for a role"""
        jobs = JobPost.objects.filter(
            title__icontains=role,
            is_active=True
        )

        if location:
            jobs = jobs.filter(location__icontains=location)

        salaries = []
        for job in jobs:
            if job.salary_min and job.salary_max:
                salaries.append((job.salary_min + job.salary_max) / 2)

        if not salaries:
            return {
                'trends': 'insufficient_data',
                'sample_size': 0
            }

        return {
            'average': int(np.mean(salaries)),
            'median': int(np.median(salaries)),
            'min': int(min(salaries)),
            'max': int(max(salaries)),
            'sample_size': len(salaries),
            'trend': 'stable',  # Could implement trend analysis
        }


# Singleton instance
salary_predictor = SalaryPredictor()


def predict_salary(role, skills, experience, location, employment_type='full-time'):
    """Convenience function"""
    return salary_predictor.predict(role, skills, experience, location, employment_type)


def get_salary_trends(role, location=None):
    """Get market trends for a role"""
    return salary_predictor.get_market_trends(role, location)