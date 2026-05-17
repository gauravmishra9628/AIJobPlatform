"""
AI Career Path Predictor
Predict career progression and suggest next steps based on current role and skills
"""
from typing import Dict, List, Optional
from django.db.models import Q
from jobs.models import JobPost, SkillProgress
from accounts.models import User


class CareerPathPredictor:
    """AI-powered career path prediction"""

    # Career paths with levels and transitions
    CAREER_PATHS = {
        'software': {
            'name': 'Software Engineering',
            'levels': [
                {'title': 'Junior Developer', 'exp_range': '0-2 years', 'salary_range': '3-8 LPA'},
                {'title': 'Software Developer', 'exp_range': '2-4 years', 'salary_range': '6-15 LPA'},
                {'title': 'Senior Developer', 'exp_range': '4-7 years', 'salary_range': '12-25 LPA'},
                {'title': 'Staff Engineer', 'exp_range': '7-10 years', 'salary_range': '20-40 LPA'},
                {'title': 'Principal Engineer', 'exp_range': '10+ years', 'salary_range': '35-80 LPA'},
                {'title': 'CTO / VP Engineering', 'exp_range': '15+ years', 'salary_range': '50-200 LPA'},
            ],
            'transitions': {
                'Junior Developer': ['Software Developer', 'Full Stack Developer', 'Backend Developer'],
                'Software Developer': ['Senior Developer', 'Full Stack Developer', 'Backend Developer'],
                'Senior Developer': ['Staff Engineer', 'Tech Lead', 'Engineering Manager'],
                'Staff Engineer': ['Principal Engineer', 'Engineering Manager', 'Technical Architect'],
            },
        },
        'data': {
            'name': 'Data Science & ML',
            'levels': [
                {'title': 'Junior Data Analyst', 'exp_range': '0-2 years', 'salary_range': '3-7 LPA'},
                {'title': 'Data Analyst', 'exp_range': '2-4 years', 'salary_range': '6-12 LPA'},
                {'title': 'Data Scientist', 'exp_range': '3-6 years', 'salary_range': '10-22 LPA'},
                {'title': 'Senior Data Scientist', 'exp_range': '5-8 years', 'salary_range': '18-35 LPA'},
                {'title': 'ML Engineer', 'exp_range': '4-7 years', 'salary_range': '15-30 LPA'},
                {'title': 'Principal ML Engineer', 'exp_range': '8+ years', 'salary_range': '25-60 LPA'},
            ],
            'transitions': {
                'Junior Data Analyst': ['Data Analyst', 'Business Analyst'],
                'Data Analyst': ['Data Scientist', 'Business Analyst'],
                'Data Scientist': ['Senior Data Scientist', 'ML Engineer', 'Research Scientist'],
                'ML Engineer': ['Principal ML Engineer', 'ML Platform Lead'],
            },
        },
        'product': {
            'name': 'Product Management',
            'levels': [
                {'title': 'Associate PM', 'exp_range': '0-2 years', 'salary_range': '8-15 LPA'},
                {'title': 'Product Manager', 'exp_range': '3-6 years', 'salary_range': '15-30 LPA'},
                {'title': 'Senior PM', 'exp_range': '6-9 years', 'salary_range': '25-45 LPA'},
                {'title': 'Group PM', 'exp_range': '9-12 years', 'salary_range': '40-70 LPA'},
                {'title': 'Director of Product', 'exp_range': '12+ years', 'salary_range': '60-120 LPA'},
                {'title': 'VP Product / CPO', 'exp_range': '15+ years', 'salary_range': '80-200 LPA'},
            ],
            'transitions': {
                'Associate PM': ['Product Manager', 'Technical PM'],
                'Product Manager': ['Senior PM', 'Group PM'],
                'Senior PM': ['Group PM', 'Director of Product'],
            },
        },
    }

    # Skills required for each role
    ROLE_SKILLS = {
        'Junior Developer': ['python', 'javascript', 'git', 'sql', 'data structures'],
        'Software Developer': ['python', 'javascript', 'git', 'sql', 'api', 'agile'],
        'Senior Developer': ['system design', 'architecture', 'leadership', 'code review', 'mentoring'],
        'Staff Engineer': ['system architecture', 'technical strategy', 'cross-team leadership'],
        'Junior Data Analyst': ['excel', 'sql', 'python', 'visualization', 'statistics'],
        'Data Analyst': ['sql', 'python', 'tableau', 'statistics', 'analytics'],
        'Data Scientist': ['python', 'machine learning', 'statistics', 'sql', 'deep learning'],
        'ML Engineer': ['python', 'tensorflow', 'pytorch', 'mlops', 'docker', 'kubernetes'],
    }

    def predict(self, user_id: int, current_role: str = None) -> Dict:
        """Predict career path for user"""

        user = self._get_user(user_id)
        if not user:
            return {'error': 'User not found'}

        # Determine career path based on user profile
        career_path_type = self._determine_career_path(user, current_role)
        path_data = self.CAREER_PATHS.get(career_path_type, self.CAREER_PATHS['software'])

        # Get user's current level
        current_level = self._get_current_level(user, current_role, path_data)

        # Generate predictions
        predictions = self._generate_predictions(user, path_data, current_level)

        # Calculate timeline
        timeline = self._calculate_timeline(path_data, current_level)

        # Get skill gaps
        skill_gaps = self._analyze_skill_gaps(user, current_role, current_level)

        return {
            'success': True,
            'career_path': {
                'type': career_path_type,
                'name': path_data['name'],
            },
            'current_level': current_level,
            'predictions': predictions,
            'timeline': timeline,
            'skill_gaps': skill_gaps,
            'milestones': self._generate_milestones(path_data, current_level),
        }

    def _get_user(self, user_id: int):
        try:
            return User.objects.get(id=user_id)
        except:
            return None

    def _determine_career_path(self, user, current_role: str = None) -> str:
        """Determine which career path the user is on"""

        if current_role:
            role_lower = current_role.lower()
            if any(k in role_lower for k in ['data', 'analyst', 'scientist', 'ml']):
                return 'data'
            elif any(k in role_lower for k in ['product', 'pm', 'manager']):
                return 'product'

        # Check user skills
        try:
            profile = user.profile
            skills = (profile.skills or [])

            skill_str = ' '.join(skills).lower()
            if any(k in skill_str for k in ['machine learning', 'tensorflow', 'pytorch', 'data science']):
                return 'data'
            elif any(k in skill_str for k in ['product', 'roadmap', 'stakeholder']):
                return 'product'
        except:
            pass

        return 'software'

    def _get_current_level(self, user, current_role: str, path_data: Dict) -> Dict:
        """Determine user's current career level"""

        # Default to first level if no current role
        if not current_role:
            return {
                'title': path_data['levels'][0]['title'],
                'level': 0,
                'exp_range': path_data['levels'][0]['exp_range'],
            }

        # Find matching level
        for i, level in enumerate(path_data['levels']):
            if level['title'].lower() in current_role.lower():
                return {
                    'title': level['title'],
                    'level': i,
                    'exp_range': level['exp_range'],
                }

        # Default to first level
        return {
            'title': path_data['levels'][0]['title'],
            'level': 0,
            'exp_range': path_data['levels'][0]['exp_range'],
        }

    def _generate_predictions(self, user, path_data: Dict, current_level: Dict) -> List[Dict]:
        """Generate career predictions"""

        level_index = current_level['level']
        predictions = []

        # Next 3 positions
        for i in range(1, 4):
            next_index = level_index + i
            if next_index < len(path_data['levels']):
                next_level = path_data['levels'][next_index]
                transitions = path_data['transitions'].get(current_level['title'], [])

                predictions.append({
                    'title': next_level['title'],
                    'exp_range': next_level['exp_range'],
                    'salary_range': next_level['salary_range'],
                    'time_to_reach': self._estimate_time(level_index, next_index),
                    'possible_titles': transitions[i-1:i] if transitions else [next_level['title']],
                })

        return predictions

    def _estimate_time(self, from_level: int, to_level: int) -> str:
        """Estimate time to reach next level"""
        levels_diff = to_level - from_level

        if levels_diff == 1:
            return "1-2 years"
        elif levels_diff == 2:
            return "2-3 years"
        else:
            return "3-5 years"

    def _calculate_timeline(self, path_data: Dict, current_level: Dict) -> List[Dict]:
        """Calculate career timeline"""

        level_index = current_level['level']
        timeline = []

        for i, level in enumerate(path_data['levels'][level_index:], level_index):
            timeline.append({
                'level': i,
                'title': level['title'],
                'salary_range': level['salary_range'],
                'is_current': i == level_index,
                'years_from_now': i - level_index,
            })

        return timeline

    def _analyze_skill_gaps(self, user, current_role: str, current_level: Dict) -> List[Dict]:
        """Analyze skills needed for next levels"""

        level_title = current_level['title']
        required_skills = self.ROLE_SKILLS.get(level_title, [])

        # Get user's current skills
        user_skills = []
        try:
            profile = user.profile
            user_skills = [s.lower() for s in (profile.skills or [])]
        except:
            pass

        # Find skill gaps
        gaps = []
        for skill in required_skills:
            if not any(skill in us or us in skill for us in user_skills):
                gaps.append({
                    'skill': skill,
                    'priority': 'high' if required_skills.index(skill) < 3 else 'medium',
                    'resources': self._get_skill_resources(skill),
                })

        return gaps

    def _get_skill_resources(self, skill: str) -> Dict:
        """Get resources to learn a skill"""
        resources = {
            'system design': {
                'courses': ['System Design Primer', 'Grokking the System Design'],
                'books': ['Designing Data-Intensive Applications'],
            },
            'architecture': {
                'courses': ['Software Architecture Patterns', 'Cloud Architecture'],
                'books': ['Pattern of Enterprise Application Architecture'],
            },
            'leadership': {
                'courses': ['Engineering Leadership', 'Managing Tech Teams'],
                'books': ['The Manager\'s Path', 'The Pragmatic Manager'],
            },
            'machine learning': {
                'courses': ['Andrew Ng ML Course', 'Fast.ai'],
                'projects': ['Kaggle competitions', 'Personal ML projects'],
            },
        }
        return resources.get(skill.lower(), {'courses': ['Online courses', 'Documentation']})

    def _generate_milestones(self, path_data: Dict, current_level: Dict) -> List[Dict]:
        """Generate career milestones"""

        level_index = current_level['level']
        milestones = []

        for i, level in enumerate(path_data['levels'][level_index:], level_index):
            milestone = {
                'level': i,
                'title': level['title'],
                'key_skills': self.ROLE_SKILLS.get(level['title'], []),
                'is_current': i == level_index,
            }

            # Add special milestones
            if i == level_index:
                milestone['status'] = 'current'
            elif i == level_index + 1:
                milestone['status'] = 'next'
            else:
                milestone['status'] = 'future'

            milestones.append(milestone)

        return milestones


# Singleton
career_predictor = CareerPathPredictor()


# =================== API FUNCTION ===================

def predict_career_path(user_id: int, current_role: str = None) -> Dict:
    """API function to predict career path"""
    return career_predictor.predict(user_id, current_role)