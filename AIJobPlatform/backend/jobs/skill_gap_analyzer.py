"""
AI Skill Gap Analysis
Compare current skills with required skills and generate learning recommendations
"""
from typing import Dict, List, Optional
from django.db.models import Q
from jobs.models import JobPost, SkillMapping, Resume
from accounts.models import User


class SkillGapAnalyzer:
    """Analyze skill gaps and generate learning recommendations"""

    # Skill prerequisites and learning paths
    SKILL_PREREQUISITES = {
        'python': {'prerequisites': [], 'difficulty': 'beginner', 'weeks': 2},
        'django': {'prerequisites': ['python'], 'difficulty': 'intermediate', 'weeks': 3},
        'react': {'prerequisites': ['javascript', 'html', 'css'], 'difficulty': 'intermediate', 'weeks': 4},
        'machine learning': {'prerequisites': ['python', 'statistics', 'linear algebra'], 'difficulty': 'advanced', 'weeks': 8},
        'deep learning': {'prerequisites': ['machine learning', 'python', 'numpy'], 'difficulty': 'advanced', 'weeks': 6},
        'sql': {'prerequisites': [], 'difficulty': 'beginner', 'weeks': 2},
        'docker': {'prerequisites': ['linux'], 'difficulty': 'intermediate', 'weeks': 3},
        'kubernetes': {'prerequisites': ['docker'], 'difficulty': 'advanced', 'weeks': 4},
        'aws': {'prerequisites': ['linux', 'networking'], 'difficulty': 'intermediate', 'weeks': 4},
        'javascript': {'prerequisites': ['html', 'css'], 'difficulty': 'beginner', 'weeks': 3},
        'typescript': {'prerequisites': ['javascript'], 'difficulty': 'intermediate', 'weeks': 2},
        'node': {'prerequisites': ['javascript'], 'difficulty': 'intermediate', 'weeks': 3},
        'mongodb': {'prerequisites': ['sql'], 'difficulty': 'intermediate', 'weeks': 2},
        'tensorflow': {'prerequisites': ['python', 'machine learning'], 'difficulty': 'advanced', 'weeks': 6},
        'nlp': {'prerequisites': ['machine learning', 'python'], 'difficulty': 'advanced', 'weeks': 5},
    }

    # Resources for each skill
    SKILL_RESOURCES = {
        'python': {
            'youtube': ['Corey Schafer', 'Clever Programmer', 'freeCodeCamp'],
            'courses': ['Python.org tutorials', 'Automate the Boring Stuff'],
            'practice': ['LeetCode', 'HackerRank'],
        },
        'machine learning': {
            'youtube': ['StatQuest', '3Blue1Brown', 'Kaggle'],
            'courses': ['Andrew Ng ML Course', 'Fast.ai'],
            'projects': ['Kaggle competitions', 'Personal projects'],
        },
        # Add more as needed
    }

    def analyze(self, user_id: int, target_role: str = None, job_id: int = None) -> Dict:
        """Perform complete skill gap analysis"""
        # Get user skills
        user_skills = self._get_user_skills(user_id)

        # Get target skills (from job or role)
        if job_id:
            target_skills = self._get_job_skills(job_id)
        elif target_role:
            target_skills = self._get_role_skills(target_role)
        else:
            return {'error': 'Please provide job_id or target_role'}

        # Find gaps and priorities
        missing_skills = self._find_missing_skills(user_skills, target_skills)
        matched_skills = [s for s in target_skills if s.lower() in [us.lower() for us in user_skills]]

        # Generate learning path
        learning_path = self._generate_learning_path(missing_skills)

        # Calculate gap percentage
        if target_skills:
            match_percentage = len(matched_skills) / len(target_skills) * 100
        else:
            match_percentage = 0

        return {
            'current_skills': user_skills,
            'target_skills': target_skills,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'match_percentage': round(match_percentage, 1),
            'learning_path': learning_path,
            'estimated_time': self._calculate_time(learning_path),
            'recommendations': self._get_recommendations(matched_skills, missing_skills),
        }

    def _get_user_skills(self, user_id: int) -> List[str]:
        """Get user's current skills"""
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
            skills = profile.skills or []

            # Also check resume skills
            resume_skills = []
            for resume in Resume.objects.filter(user=user):
                if resume.extracted_skills:
                    resume_skills.extend(resume.extracted_skills)

            # Combine and deduplicate
            all_skills = list(set(skills + resume_skills))
            return [s for s in all_skills if s]
        except:
            return []

    def _get_job_skills(self, job_id: int) -> List[str]:
        """Extract skills from job posting"""
        try:
            job = JobPost.objects.get(id=job_id)
            skills_text = job.skills_required or ''

            # Simple extraction - split by common delimiters
            skills = []
            for delimiter in [',', ' ', '|', '/']:
                skills.extend([s.strip() for s in skills_text.split(delimiter) if s.strip()])

            return list(set([s.lower() for s in skills if len(s) > 2]))
        except:
            return []

    def _get_role_skills(self, role: str) -> List[str]:
        """Get required skills for a role"""
        role_skills = {
            'data scientist': ['python', 'sql', 'machine learning', 'statistics', 'pandas', 'visualization', 'deep learning'],
            'software engineer': ['python', 'javascript', 'git', 'sql', 'data structures', 'algorithms', 'api'],
            'frontend developer': ['javascript', 'react', 'html', 'css', 'typescript', 'responsive design'],
            'backend developer': ['python', 'django', 'sql', 'api', 'rest', 'authentication', 'docker'],
            'devops': ['docker', 'kubernetes', 'aws', 'linux', 'ci/cd', 'terraform', 'monitoring'],
            'ml engineer': ['python', 'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'mlops'],
            'data analyst': ['python', 'sql', 'excel', 'tableau', 'statistics', 'pandas'],
        }

        role_lower = role.lower()
        for key, skills in role_skills.items():
            if key in role_lower:
                return skills

        return []

    def _find_missing_skills(self, user_skills: List[str], target_skills: List[str]) -> List[Dict]:
        """Find missing skills with priority"""
        user_skills_lower = [s.lower() for s in user_skills]

        missing = []
        for skill in target_skills:
            if skill.lower() not in user_skills_lower:
                skill_info = self.SKILL_PREREQUISITES.get(skill.lower(), {})

                # Determine if prerequisites are met
                prereqs = skill_info.get('prerequisites', [])
                prereqs_met = all(p.lower() in user_skills_lower for p in prereqs) if prereqs else True

                missing.append({
                    'skill': skill.title(),
                    'difficulty': skill_info.get('difficulty', 'intermediate'),
                    'weeks': skill_info.get('weeks', 3),
                    'prerequisites': prereqs,
                    'prerequisites_met': prereqs_met,
                    'priority': 'high' if prereqs_met else 'medium',
                })

        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        return sorted(missing, key=lambda x: (priority_order.get(x['priority'], 3), x['weeks']))

    def _generate_learning_path(self, missing_skills: List[Dict]) -> List[Dict]:
        """Generate prioritized learning path"""
        path = []
        current_week = 1

        for skill_info in missing_skills:
            # Check if we should learn prerequisites first
            if not skill_info['prerequisites_met']:
                for prereq in skill_info['prerequisites']:
                    prereq_info = self.SKILL_PREREQUISITES.get(prereq.lower(), {})
                    if prereq not in [s['skill'] for s in path]:
                        path.append({
                            'week': current_week,
                            'skill': prereq.title(),
                            'type': 'prerequisite',
                            'difficulty': prereq_info.get('difficulty', 'beginner'),
                            'duration_weeks': prereq_info.get('weeks', 2),
                        })
                        current_week += prereq_info.get('weeks', 2)

            # Add main skill
            path.append({
                'week': current_week,
                'skill': skill_info['skill'],
                'type': 'main',
                'difficulty': skill_info['difficulty'],
                'duration_weeks': skill_info['weeks'],
            })
            current_week += skill_info['weeks']

        return path

    def _calculate_time(self, learning_path: List[Dict]) -> Dict:
        """Calculate estimated time to learn"""
        total_weeks = sum(item['duration_weeks'] for item in learning_path)

        return {
            'total_weeks': total_weeks,
            'months': round(total_weeks / 4, 1),
            'hours_per_week': 10,
            'total_hours': total_weeks * 10,
        }

    def _get_recommendations(self, matched: List[str], missing: List[Dict]) -> List[str]:
        """Get personalized recommendations"""
        recommendations = []

        if len(matched) > 5:
            recommendations.append("You have a strong foundation! Focus on deepening your expertise.")

        if missing:
            most_urgent = missing[0]
            recommendations.append(f"Start by learning {most_urgent['skill']} - it takes ~{most_urgent['weeks']} weeks.")

            # Add resource suggestion
            skill_lower = most_urgent['skill'].lower()
            if skill_lower in self.SKILL_RESOURCES:
                resources = self.SKILL_RESOURCES[skill_lower]
                if resources.get('youtube'):
                    recommendations.append(f"Check out {resources['youtube'][0]} on YouTube for {most_urgent['skill']}")

        return recommendations


# Singleton
skill_gap_analyzer = SkillGapAnalyzer()


def analyze_skill_gap(user_id: int, target_role: str = None, job_id: int = None) -> Dict:
    """API function"""
    return skill_gap_analyzer.analyze(user_id, target_role, job_id)