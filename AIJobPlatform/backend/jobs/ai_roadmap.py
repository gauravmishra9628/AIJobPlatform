"""
AI Career Roadmap Generator
Creates personalized learning roadmaps based on target career goals
"""
import json
from typing import Dict, List, Optional
from django.conf import settings


class RoadmapGenerator:
    """Generate personalized career roadmaps with resources"""

    # Career paths with skill progressions
    CAREER_PATHS = {
        'data_scientist': {
            'title': 'Data Scientist',
            'duration_months': 6,
            'prerequisites': ['Python basics', 'Math basics'],
            'skills': [
                {'name': 'Python Programming', 'weeks': 2, 'priority': 'high'},
                {'name': 'Statistics & Probability', 'weeks': 3, 'priority': 'high'},
                {'name': 'SQL & Databases', 'weeks': 2, 'priority': 'high'},
                {'name': 'Data Analysis (Pandas/NumPy)', 'weeks': 3, 'priority': 'high'},
                {'name': 'Data Visualization', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Machine Learning Basics', 'weeks': 4, 'priority': 'high'},
                {'name': 'Scikit-Learn', 'weeks': 3, 'priority': 'high'},
                {'name': 'Deep Learning Intro', 'weeks': 3, 'priority': 'medium'},
                {'name': 'MLOps Basics', 'weeks': 2, 'priority': 'medium'},
            ],
            'projects': [
                'Exploratory Data Analysis on Kaggle dataset',
                'Predictive Model for House Prices',
                'Customer Segmentation Clustering',
                'Recommendation System',
                'End-to-End ML Pipeline',
            ],
            'certifications': [
                'IBM Data Science Professional Certificate',
                'Google Data Analytics Certificate',
                'AWS Machine Learning Specialty',
            ]
        },
        'software_engineer': {
            'title': 'Software Engineer',
            'duration_months': 6,
            'prerequisites': ['Basic programming'],
            'skills': [
                {'name': 'Git & Version Control', 'weeks': 1, 'priority': 'high'},
                {'name': 'Data Structures & Algorithms', 'weeks': 4, 'priority': 'high'},
                {'name': 'Python/Java Mastery', 'weeks': 3, 'priority': 'high'},
                {'name': 'Web Development Basics', 'weeks': 3, 'priority': 'high'},
                {'name': 'Database Design (SQL)', 'weeks': 2, 'priority': 'high'},
                {'name': 'API Development (REST)', 'weeks': 2, 'priority': 'high'},
                {'name': 'Testing & Debugging', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Docker & Deployment', 'weeks': 2, 'priority': 'medium'},
                {'name': 'System Design Basics', 'weeks': 3, 'priority': 'medium'},
            ],
            'projects': [
                'Build a REST API',
                'Full-stack Web Application',
                'Command-line Tool',
                'Portfolio Website',
                'Open Source Contribution',
            ],
            'certifications': [
                'AWS Certified Developer',
                'GCP Professional Developer',
                'Meta Front-End Developer Certificate',
            ]
        },
        'frontend_developer': {
            'title': 'Frontend Developer',
            'duration_months': 4,
            'prerequisites': ['Basic HTML/CSS'],
            'skills': [
                {'name': 'HTML5 & CSS3', 'weeks': 2, 'priority': 'high'},
                {'name': 'JavaScript Fundamentals', 'weeks': 3, 'priority': 'high'},
                {'name': 'DOM Manipulation', 'weeks': 2, 'priority': 'high'},
                {'name': 'React.js', 'weeks': 4, 'priority': 'high'},
                {'name': 'State Management', 'weeks': 2, 'priority': 'high'},
                {'name': 'TypeScript', 'weeks': 2, 'priority': 'medium'},
                {'name': 'CSS Frameworks (Tailwind)', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Next.js', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Testing (Jest/React Testing)', 'weeks': 2, 'priority': 'low'},
            ],
            'projects': [
                'Personal Portfolio',
                'Todo App with React',
                'E-commerce UI Clone',
                'Weather Dashboard',
                'Blog with CMS',
            ],
            'certifications': [
                'Meta Front-End Developer',
                'freeCodeCamp Certifications',
                'React JS Certification',
            ]
        },
        'backend_developer': {
            'title': 'Backend Developer',
            'duration_months': 5,
            'prerequisites': ['Basic programming'],
            'skills': [
                {'name': 'Python/JavaScript Deep Dive', 'weeks': 3, 'priority': 'high'},
                {'name': 'REST API Design', 'weeks': 2, 'priority': 'high'},
                {'name': 'Database Design (SQL)', 'weeks': 3, 'priority': 'high'},
                {'name': 'NoSQL Databases', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Authentication & Security', 'weeks': 2, 'priority': 'high'},
                {'name': 'Django/FastAPI or Node.js', 'weeks': 4, 'priority': 'high'},
                {'name': 'Caching & Performance', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Docker & Deployment', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Message Queues', 'weeks': 2, 'priority': 'low'},
            ],
            'projects': [
                'REST API with Authentication',
                'User Management System',
                'E-commerce Backend',
                'Real-time Chat Server',
                'Job Board Backend',
            ],
            'certifications': [
                'AWS Certified Developer',
                'GCP Associate Cloud Developer',
                'Certified Django Developer',
            ]
        },
        'devops_engineer': {
            'title': 'DevOps Engineer',
            'duration_months': 5,
            'prerequisites': ['Basic Linux', 'Basic programming'],
            'skills': [
                {'name': 'Linux Fundamentals', 'weeks': 2, 'priority': 'high'},
                {'name': 'Shell Scripting', 'weeks': 2, 'priority': 'high'},
                {'name': 'Git & CI/CD', 'weeks': 2, 'priority': 'high'},
                {'name': 'Docker', 'weeks': 3, 'priority': 'high'},
                {'name': 'Kubernetes', 'weeks': 4, 'priority': 'high'},
                {'name': 'Cloud Platforms (AWS/GCP)', 'weeks': 3, 'priority': 'high'},
                {'name': 'Infrastructure as Code (Terraform)', 'weeks': 3, 'priority': 'medium'},
                {'name': 'Monitoring & Logging', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Security Best Practices', 'weeks': 2, 'priority': 'medium'},
            ],
            'projects': [
                'CI/CD Pipeline Setup',
                'Containerize an Application',
                'Deploy to Kubernetes',
                'Infrastructure Automation',
                'Monitoring Dashboard',
            ],
            'certifications': [
                'AWS DevOps Engineer Professional',
                'CKA (Certified Kubernetes Admin)',
                'GCP Professional DevOps Engineer',
            ]
        },
        'ai_engineer': {
            'title': 'AI/ML Engineer',
            'duration_months': 8,
            'prerequisites': ['Python', 'Math/Stats'],
            'skills': [
                {'name': 'Advanced Python', 'weeks': 2, 'priority': 'high'},
                {'name': 'Linear Algebra & Stats', 'weeks': 3, 'priority': 'high'},
                {'name': 'Machine Learning Deep Dive', 'weeks': 4, 'priority': 'high'},
                {'name': 'TensorFlow/PyTorch', 'weeks': 4, 'priority': 'high'},
                {'name': 'Computer Vision', 'weeks': 3, 'priority': 'medium'},
                {'name': 'NLP', 'weeks': 3, 'priority': 'medium'},
                {'name': 'MLOps', 'weeks': 3, 'priority': 'high'},
                {'name': 'Model Deployment', 'weeks': 2, 'priority': 'high'},
                {'name': 'LLMs & Prompt Engineering', 'weeks': 3, 'priority': 'high'},
            ],
            'projects': [
                'Image Classification Model',
                'Sentiment Analysis API',
                'Object Detection System',
                'Chatbot with LLM',
                'End-to-End ML Deployment',
            ],
            'certifications': [
                'DeepLearning.AI TensorFlow Developer',
                'AWS Machine Learning Specialty',
                'Google Cloud ML Engineer',
            ]
        },
        'product_manager': {
            'title': 'Product Manager',
            'duration_months': 4,
            'prerequisites': ['Basic business understanding'],
            'skills': [
                {'name': 'Product Thinking', 'weeks': 2, 'priority': 'high'},
                {'name': 'User Research', 'weeks': 2, 'priority': 'high'},
                {'name': 'Roadmapping & Prioritization', 'weeks': 2, 'priority': 'high'},
                {'name': 'Data Analysis', 'weeks': 3, 'priority': 'high'},
                {'name': 'Agile/Scrum', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Wireframing & Prototyping', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Stakeholder Management', 'weeks': 2, 'priority': 'medium'},
                {'name': 'Product Analytics', 'weeks': 2, 'priority': 'high'},
            ],
            'projects': [
                'Product Teardown Analysis',
                'User Research Report',
                'PRD Creation',
                'MVP Specification',
                'Product Launch Case Study',
            ],
            'certifications': [
                'Product School Certificate',
                'Google Product Management Certificate',
                'Meta Product Manager Certificate',
            ]
        }
    }

    # Resources by category
    RESOURCES = {
        'youtube_channels': {
            'data_science': [
                {'name': 'Kaggle', 'url': 'https://www.youtube.com/kaggle', 'subs': '500K+'},
                {'name': 'Sentdex', 'url': 'https://www.youtube.com/sentdex', 'subs': '400K+'},
                {'name': 'StatQuest with Josh Starmer', 'url': 'https://www.youtube.com/user/joshstarmer', 'subs': '1M+'},
                {'name': '3Blue1Brown', 'url': 'https://www.youtube.com/3blue1brown', 'subs': '5M+'},
                {'name': 'TechTFQ', 'url': 'https://www.youtube.com/@TechTFQ', 'subs': '200K+'},
            ],
            'software_engineer': [
                {'name': 'freeCodeCamp', 'url': 'https://www.youtube.com/freecodecamp', 'subs': '8M+'},
                {'name': 'Clever Programmer', 'url': 'https://www.youtube.com/cleverprogrammer', 'subs': '1M+'},
                {'name': 'Take U Forward', 'url': 'https://www.youtube.com/takeUforward', 'subs': '300K+'},
                {'name': 'CodeWithChris', 'url': 'https://www.youtube.com/CodeWithChris', 'subs': '500K+'},
            ],
            'web_dev': [
                {'name': 'Traversy Media', 'url': 'https://www.youtube.com/traversymedia', 'subs': '2M+'},
                {'name': 'The Net Ninja', 'url': 'https://www.youtube.com/netninja', 'subs': '1M+'},
                {'name': 'Academind', 'url': 'https://www.youtube.com/academind', 'subs': '1M+'},
            ]
        },
        'courses': {
            'free': [
                {'name': 'freeCodeCamp', 'url': 'https://www.freecodecamp.org', 'type': 'Full Stack'},
                {'name': 'Kaggle Learn', 'url': 'https://www.kaggle.com/learn', 'type': 'Data Science'},
                {'name': 'The Odin Project', 'url': 'https://www.theodinproject.com', 'type': 'Web Dev'},
                {'name': 'CS50', 'url': 'https://cs50.harvard.edu/x', 'type': 'Computer Science'},
            ],
            'paid': [
                {'name': 'Udemy Complete Courses', 'url': 'https://www.udemy.com', 'type': 'Various'},
                {'name': 'Coursera Specializations', 'url': 'https://www.coursera.org', 'type': 'Various'},
                {'name': 'DataCamp', 'url': 'https://www.datacamp.com', 'type': 'Data Science'},
            ]
        },
        'practice': {
            'coding': ['LeetCode', 'HackerRank', 'Codeforces', 'CodeChef'],
            'data_science': ['Kaggle', 'DrivenData', 'AI Crowd'],
            'projects': ['GitHub', 'Replit', 'CodeSandbox', 'Jupyter Notebooks']
        },
        'communities': [
            {'name': 'Reddit (r/learnprogramming)', 'url': 'https://reddit.com/r/learnprogramming'},
            {'name': 'Discord Dev Communities', 'url': 'https://discord.gg/programming'},
            {'name': 'Stack Overflow', 'url': 'https://stackoverflow.com'},
            {'name': 'LinkedIn Groups', 'url': 'https://linkedin.com'},
        ]
    }

    def __init__(self):
        self.openai_key = getattr(settings, 'OPENAI_API_KEY', None)

    def generate_roadmap(self, career_goal: str, current_skills: List[str] = None,
                         experience_level: str = 'beginner', timeframe: str = '6_months') -> Dict:
        """
        Generate a personalized career roadmap

        Args:
            career_goal: Target role (e.g., "Data Scientist")
            current_skills: List of skills user already has
            experience_level: 'beginner', 'intermediate', 'advanced'
            timeframe: '3_months', '6_months', '1_year'

        Returns:
            Complete roadmap with milestones, resources, projects
        """
        # Find matching career path
        career_key = self._match_career_path(career_goal)
        path_data = self.CAREER_PATHS.get(career_key)

        if not path_data:
            # Use AI to generate custom roadmap
            return self._generate_ai_roadmap(career_goal, current_skills, experience_level, timeframe)

        # Filter skills based on current skills
        filtered_skills = self._filter_skills(path_data['skills'], current_skills or [])

        # Generate weekly milestones
        milestones = self._generate_milestones(filtered_skills, timeframe, experience_level)

        # Get relevant resources
        resources = self._get_resources(career_key)

        return {
            'career_path': path_data['title'],
            'total_duration': path_data['duration_months'],
            'milestones': milestones,
            'skills_to_learn': filtered_skills,
            'projects': path_data['projects'],
            'certifications': path_data['certifications'],
            'resources': resources,
            'summary': self._generate_summary(career_key, filtered_skills, path_data['duration_months'])
        }

    def _match_career_path(self, career_goal: str) -> str:
        """Match user goal to predefined career path"""
        goal_lower = career_goal.lower()

        # Direct matches
        for key in self.CAREER_PATHS.keys():
            if key.replace('_', ' ') in goal_lower or key.replace('_', ' ') in goal_lower:
                return key

        # Keyword matching
        if any(word in goal_lower for word in ['data', 'science', 'data science', 'analytics']):
            return 'data_scientist'
        elif any(word in goal_lower for word in ['frontend', 'front-end', 'react', 'web developer']):
            return 'frontend_developer'
        elif any(word in goal_lower for word in ['backend', 'back-end', 'api', 'server']):
            return 'backend_developer'
        elif any(word in goal_lower for word in ['devops', 'sre', 'cloud']):
            return 'devops_engineer'
        elif any(word in goal_lower for word in ['ai', 'ml', 'machine learning', 'deep learning']):
            return 'ai_engineer'
        elif any(word in goal_lower for word in ['product manager', 'product management', 'pm']):
            return 'product_manager'
        else:
            return 'software_engineer'  # Default

    def _filter_skills(self, skills: List[Dict], current_skills: List[str]) -> List[Dict]:
        """Filter out skills user already has"""
        current_lower = [s.lower() for s in current_skills]

        filtered = []
        for skill in skills:
            # Check if user already has this skill
            skill_lower = skill['name'].lower()
            if not any(cskill in skill_lower or skill_lower in cskill for cskill in current_lower):
                filtered.append(skill)

        return filtered

    def _generate_milestones(self, skills: List[Dict], timeframe: str, level: str) -> List[Dict]:
        """Generate weekly milestones"""
        # Determine number of weeks based on timeframe
        weeks_map = {'3_months': 12, '6_months': 24, '1_year': 52}
        total_weeks = weeks_map.get(timeframe, 24)

        milestones = []
        current_week = 1

        for skill in skills:
            skill_weeks = skill.get('weeks', 2)

            if current_week + skill_weeks <= total_weeks:
                milestones.append({
                    'week': current_week,
                    'skill': skill['name'],
                    'duration_weeks': skill_weeks,
                    'priority': skill.get('priority', 'medium'),
                    'description': f"Learn {skill['name']} fundamentals and practical applications",
                    'deliverable': self._get_deliverable(skill['name'])
                })
                current_week += skill_weeks

        # Add final project milestone
        milestones.append({
            'week': current_week,
            'skill': 'Capstone Project',
            'duration_weeks': min(4, total_weeks - current_week + 1),
            'priority': 'high',
            'description': 'Build a complete project to showcase your skills',
            'deliverable': 'Portfolio-ready project with documentation'
        })

        return milestones

    def _get_deliverable(self, skill: str) -> str:
        """Get suggested deliverable for a skill"""
        deliverables = {
            'python': 'Build a small application or script',
            'statistics': 'Complete statistical analysis on a dataset',
            'sql': 'Design and query a database',
            'machine learning': 'Train and evaluate a model',
            'react': 'Build a React component or app',
            'docker': 'Containerize an application',
            'kubernetes': 'Deploy to a Kubernetes cluster',
            'api': 'Create a REST API',
        }

        skill_lower = skill.lower()
        for key, value in deliverables.items():
            if key in skill_lower:
                return value

        return f'Complete {skill} exercises and mini-projects'

    def _get_resources(self, career_key: str) -> Dict:
        """Get relevant resources for career path"""
        return {
            'youtube_channels': self.RESOURCES['youtube_channels'].get(career_key, []),
            'courses': self.RESOURCES['courses'],
            'practice_platforms': self.RESOURCES['practice'],
            'communities': self.RESOURCES['communities']
        }

    def _generate_summary(self, career_key: str, skills: List[Dict], duration: int) -> str:
        """Generate a summary of the roadmap"""
        skill_names = [s['name'] for s in skills[:5]]
        return f"Become a {self.CAREER_PATHS[career_key]['title']} in {duration} months by mastering {', '.join(skill_names)} and more."

    def _generate_ai_roadmap(self, career_goal: str, current_skills: List[str],
                            experience_level: str, timeframe: str) -> Dict:
        """Use AI to generate custom roadmap if no predefined path exists"""
        if not self.openai_key:
            return {'error': 'AI not available, please try a different career path'}

        import openai
        openai.api_key = self.openai_key

        prompt = f"""Generate a career roadmap for someone who wants to become a {career_goal}.

Current skills: {', '.join(current_skills) if current_skills else 'None'}
Experience level: {experience_level}
Timeframe: {timeframe}

Provide a JSON with:
{{
    "milestones": [{{"week": 1, "skill": "skill name", "description": "what to learn"}}],
    "skills": [{{"name": "skill", "weeks": 2, "priority": "high/medium/low"}}],
    "projects": ["project1", "project2"],
    "resources": {{"youtube": ["channel1"], "courses": ["course1"]}},
    "summary": "brief summary"
}}"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a career advisor specializing in tech careers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            content = response.choices[0].message.content
            # Parse JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content)
        except Exception as e:
            return {'error': str(e)}


# Singleton instance
roadmap_generator = RoadmapGenerator()


def generate_career_roadmap(career_goal: str, current_skills: List[str] = None,
                           experience_level: str = 'beginner', timeframe: str = '6_months') -> Dict:
    """Generate career roadmap"""
    return roadmap_generator.generate_roadmap(career_goal, current_skills, experience_level, timeframe)