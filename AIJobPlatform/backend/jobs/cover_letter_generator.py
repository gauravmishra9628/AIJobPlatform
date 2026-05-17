"""
AI Cover Letter Generator
Generate personalized cover letters based on job requirements and user profile
"""
from typing import Dict, Optional
import random


class CoverLetterGenerator:
    """AI-powered cover letter generator"""

    # Professional phrases for different sections
    OPENING_PHRASES = [
        "I am writing to express my strong interest in the {position} position at {company}.",
        "With great enthusiasm, I submit my application for the {position} role at {company}.",
        "Having followed {company}'s innovative work, I am excited to apply for the {position} position.",
        "Your job posting for {position} immediately caught my attention, and I am eager to apply.",
    ]

    BODY_PARAGRAPHS = {
        'experience': [
            "My background in {experience} has prepared me well for this role. Through my work at {past_company}, I developed skills directly applicable to your needs.",
            "With {years} years of experience in {field}, I have honed my abilities to {skill}. This expertise directly aligns with your requirements.",
            "In my previous role at {past_company}, I {achievement}. This experience positions me to contribute meaningfully to your team.",
        ],
        'skills': [
            "My technical proficiency in {skills} complements my strong analytical abilities. I am confident these skills will allow me to excel in this position.",
            "I bring a unique combination of {skills} that I believe will bring immediate value to your organization.",
            "My expertise in {skills} has been developed through both professional experience and continuous learning.",
        ],
        'motivation': [
            "What excites me most about {company} is {company_value}. I am drawn to your mission and the innovative work your team does.",
            "Your company's commitment to {value} resonates deeply with my professional values. I am eager to contribute to such a forward-thinking organization.",
            "The opportunity to {specific_goal} at {company} is exactly the kind of challenge I have been seeking.",
        ],
    }

    CLOSING_PARAGRAPHS = [
        "I would welcome the opportunity to discuss how my background, skills, and enthusiasm would benefit your team.",
        "I am eager to bring my passion and expertise to {company} and contribute to your continued success.",
        "Thank you for considering my application. I look forward to the possibility of discussing this opportunity further.",
    ]

    def generate(
        self,
        user_id: int,
        job_id: int = None,
        company_name: str = None,
        position: str = None,
        job_description: str = None,
        tone: str = 'professional'
    ) -> Dict:
        """Generate a personalized cover letter"""

        # Get user profile data
        user_data = self._get_user_profile(user_id)

        if not company_name or not position:
            return {'error': 'Company name and position are required'}

        # Build the cover letter
        letter_parts = []

        # Header (optional - would include address in real implementation)
        letter_parts.append(self._generate_header(user_data, company_name))

        # Opening paragraph
        opening = random.choice(self.OPENING_PHRASES).format(
            position=position,
            company=company_name
        )
        letter_parts.append(opening)

        # Body paragraphs
        body_paragraphs = self._generate_body(
            user_data,
            company_name,
            job_description,
            tone
        )
        letter_parts.extend(body_paragraphs)

        # Closing paragraph
        closing = random.choice(self.CLOSING_PARAGRAPHS).format(
            company=company_name
        )
        letter_parts.append(closing)

        # Signature
        signature = self._generate_signature(user_data)
        letter_parts.append(signature)

        return {
            'success': True,
            'cover_letter': '\n\n'.join(letter_parts),
            'metadata': {
                'company': company_name,
                'position': position,
                'tone': tone,
                'word_count': sum(len(p.split()) for p in letter_parts),
                'generated_at': self._get_timestamp(),
            }
        }

    def _get_user_profile(self, user_id: int) -> Dict:
        """Get user profile data"""
        try:
            from accounts.models import User
            user = User.objects.get(id=user_id)
            profile = user.profile

            # Get user skills
            skills = profile.skills or []

            # Get resume experience if available
            experience = []
            from jobs.models import Resume
            resumes = Resume.objects.filter(user=user)[:1]
            if resumes:
                resume = resumes[0]
                if resume.parsed_experience:
                    experience = resume.parsed_experience

            return {
                'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'email': user.email,
                'headline': profile.headline or '',
                'skills': skills,
                'experience': experience,
                'location': profile.location or '',
            }
        except:
            return {
                'name': 'Your Name',
                'email': 'your.email@example.com',
                'headline': '',
                'skills': [],
                'experience': [],
                'location': '',
            }

    def _generate_header(self, user_data: Dict, company: str) -> str:
        """Generate letter header"""
        return f"{user_data.get('name', '')}\n{user_data.get('email', '')}\n{user_data.get('location', '')}\n\n"

    def _generate_body(
        self,
        user_data: Dict,
        company: str,
        job_description: str,
        tone: str
    ) -> list:
        """Generate body paragraphs"""

        paragraphs = []

        # Extract key requirements from job description if provided
        key_skills = self._extract_skills(job_description) if job_description else []

        # Match user skills to job requirements
        matched_skills = [s for s in user_data.get('skills', []) if any(
            k.lower() in s.lower() or s.lower() in k.lower()
            for k in key_skills
        )]

        # Paragraph 1: Experience
        exp_para = random.choice(self.BODY_PARAGRAPHS['experience']).format(
            experience=key_skills[0] if key_skills else 'software development',
            past_company='my previous organization',
            years='3+',
            field=key_skills[0] if key_skills else 'technology',
            skill='deliver impactful solutions',
            achievement='consistently exceeded targets and led successful projects'
        )
        paragraphs.append(exp_para)

        # Paragraph 2: Skills
        if matched_skills:
            skills_text = ', '.join(matched_skills[:3])
        else:
            skills_text = ', '.join(user_data.get('skills', [])[:3]) or 'Python, JavaScript, SQL'

        skill_para = random.choice(self.BODY_PARAGRAPHS['skills']).format(
            skills=skills_text
        )
        paragraphs.append(skill_para)

        # Paragraph 3: Motivation
        motivation_para = random.choice(self.BODY_PARAGRAPHS['motivation']).format(
            company=company,
            company_value='innovation and excellence',
            value='continuous improvement',
            specific_goal='make a meaningful impact'
        )
        paragraphs.append(motivation_para)

        return paragraphs

    def _generate_signature(self, user_data: Dict) -> str:
        """Generate closing signature"""
        return f"\nSincerely,\n\n{user_data.get('name', 'Your Name')}"

    def _extract_skills(self, job_description: str) -> list:
        """Extract key skills from job description"""
        common_skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue',
            'django', 'flask', 'spring', 'node', 'express',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'aws', 'gcp', 'azure', 'docker', 'kubernetes',
            'git', 'ci/cd', 'agile', 'scrum',
            'machine learning', 'data science', 'analytics',
            'html', 'css', 'typescript', 'rest', 'api'
        ]

        desc_lower = job_description.lower()
        found_skills = [s for s in common_skills if s in desc_lower]

        return found_skills[:5] if found_skills else ['technology', 'software development']

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from django.utils import timezone
        return timezone.now().strftime('%Y-%m-%d %H:%M:%S')

    def generate_multiple(
        self,
        user_id: int,
        jobs: list
    ) -> list:
        """Generate cover letters for multiple jobs"""

        letters = []
        for job in jobs:
            result = self.generate(
                user_id=user_id,
                company_name=job.get('company', ''),
                position=job.get('position', ''),
                job_description=job.get('description', ''),
                tone=job.get('tone', 'professional')
            )
            letters.append({
                'job_id': job.get('id'),
                'letter': result.get('cover_letter', ''),
            })

        return letters


# Singleton
cover_letter_generator = CoverLetterGenerator()


# =================== API FUNCTION ===================

def generate_cover_letter(
    user_id: int,
    company_name: str = None,
    position: str = None,
    job_description: str = None,
    job_id: int = None,
    tone: str = 'professional'
) -> Dict:
    """API function to generate cover letter"""

    # Get job details if job_id provided
    if job_id and (not company_name or not position):
        try:
            from jobs.models import JobPost
            job = JobPost.objects.get(id=job_id)
            company_name = company_name or job.company_name
            position = position or job.title
            job_description = job_description or job.description
        except:
            pass

    return cover_letter_generator.generate(
        user_id=user_id,
        company_name=company_name,
        position=position,
        job_description=job_description,
        tone=tone
    )