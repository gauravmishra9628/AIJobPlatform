"""
AI Resume Analyzer - Comprehensive resume analysis with ATS scoring
"""
import re
import io
import json
from typing import Dict, List, Optional
from django.conf import settings
from jobs.models import Resume, AIResumeAnalysis, ResumeAtsScore

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        nlp = None
except ImportError:
    nlp = None


class ResumeAnalyzer:
    """Comprehensive AI Resume Analyzer"""

    # Common ATS keywords by category
    ATS_KEYWORDS = {
        'programming': ['python', 'java', 'javascript', 'c++', 'ruby', 'golang', 'rust', 'php'],
        'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node.js'],
        'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle'],
        'cloud': ['aws', 'azure', 'gcp', 'kubernetes', 'docker', 'terraform'],
        'data_science': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'numpy'],
        'soft_skills': ['leadership', 'communication', 'teamwork', 'problem-solving', 'agile'],
        'tools': ['git', 'jira', 'jenkins', 'ci/cd', 'docker'],
    }

    # Common grammar mistakes
    GRAMMAR_PATTERNS = {
        'passive_voice': [r'\b(was|were|been|being)\s+\w+ed\b'],
        'repeated_words': [r'\b(\w+)\s+\1\b'],
        'long_sentences': r'[.;]\s*',  # Will count sentences
    }

    def __init__(self):
        self.openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.gemini_key = getattr(settings, 'GOOGLE_GEMINI_KEY', None)

    def extract_text_from_pdf(self, file) -> str:
        """Extract text from PDF file"""
        if pdfplumber is None:
            return self._fallback_text_extraction(file)

        try:
            with pdfplumber.open(file) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''
                return text
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return self._fallback_text_extraction(file)

    def _fallback_text_extraction(self, file) -> str:
        """Fallback text extraction"""
        try:
            # Try reading as plain text
            return file.read().decode('utf-8', errors='ignore')
        except:
            return ""

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []

        for category, keywords in self.ATS_KEYWORDS.items():
            for skill in keywords:
                if skill in text_lower:
                    found_skills.append(skill.title())

        # Use spaCy for additional skill extraction
        if nlp:
            doc = nlp(text)
            # Extract proper nouns that might be tools/technologies
            for ent in doc.ents:
                if ent.label_ == 'PRODUCT' or ent.label_ == 'ORG':
                    skill = ent.text.strip()
                    if skill and len(skill) > 2 and skill.lower() not in found_skills:
                        found_skills.append(skill)

        return list(set(found_skills))

    def calculate_ats_score(self, text: str, job_description: str = None) -> Dict:
        """Calculate ATS compatibility score"""
        text_lower = text.lower()

        scores = {
            'keyword_match': 0,
            'format_score': 0,
            'content_score': 0,
            'overall': 0
        }

        # Keyword match score
        total_keywords = 0
        matched_keywords = 0

        for category, keywords in self.ATS_KEYWORDS.items():
            for keyword in keywords:
                total_keywords += 1
                if keyword in text_lower:
                    matched_keywords += 1

        if total_keywords > 0:
            scores['keyword_match'] = min(100, int((matched_keywords / total_keywords) * 100))

        # Format score
        format_checks = {
            'has_email': bool(re.search(r'\b[\w.-]+@[\w.-]+\.\w+', text)),
            'has_phone': bool(re.search(r'\b\d{10,}\b', text)),
            'has_education': bool(re.search(r'(bachelor|master|phd|degree|university|college)', text_lower)),
            'has_experience': bool(re.search(r'(experience|worked|job|position|role)', text_lower)),
            'has_skills': bool(re.search(r'(skills|technologies|tools|proficient)', text_lower)),
        }

        format_score = sum(format_checks.values()) / len(format_checks) * 100
        scores['format_score'] = int(format_score)

        # Content score (based on length and structure)
        word_count = len(text.split())
        if 300 <= word_count <= 1500:
            scores['content_score'] = 80
        elif word_count > 1500:
            scores['content_score'] = 70
        elif word_count > 150:
            scores['content_score'] = 60
        else:
            scores['content_score'] = 40

        # Overall score
        scores['overall'] = int(
            (scores['keyword_match'] * 0.4) +
            (scores['format_score'] * 0.3) +
            (scores['content_score'] * 0.3)
        )

        return scores

    def find_missing_skills(self, text: str, target_role: str = None) -> List[Dict]:
        """Find missing skills based on common role requirements"""
        text_lower = text.lower()
        current_skills = set()

        for category, keywords in self.ATS_KEYWORDS.items():
            for skill in keywords:
                if skill in text_lower:
                    current_skills.add(skill)

        # Define role-based skill requirements
        role_requirements = {
            'software engineer': ['python', 'git', 'sql', 'java', 'javascript'],
            'data scientist': ['python', 'machine learning', 'sql', 'pandas', 'tensorflow'],
            'frontend developer': ['javascript', 'react', 'css', 'html', 'typescript'],
            'backend developer': ['python', 'sql', 'django', 'api', 'git'],
            'devops': ['aws', 'docker', 'kubernetes', 'ci/cd', 'linux'],
            'ml engineer': ['python', 'tensorflow', 'pytorch', 'machine learning', 'sql'],
        }

        # Default requirements
        required = role_requirements.get(target_role.lower() if target_role else 'software engineer',
                                         ['python', 'git', 'sql', 'api'])

        missing = []
        for skill in required:
            if skill not in current_skills:
                missing.append({
                    'skill': skill.title(),
                    'category': self._get_skill_category(skill),
                    'importance': 'high' if skill in ['python', 'git', 'sql'] else 'medium'
                })

        return missing

    def _get_skill_category(self, skill: str) -> str:
        """Get category for a skill"""
        skill_lower = skill.lower()
        for category, keywords in self.ATS_KEYWORDS.items():
            if skill_lower in keywords:
                return category.replace('_', ' ').title()
        return 'General'

    def check_grammar_issues(self, text: str) -> List[Dict]:
        """Check for common grammar issues"""
        issues = []

        # Check for passive voice
        for pattern in self.GRAMMAR_PATTERNS['passive_voice']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': 'Passive Voice',
                    'text': match.group(),
                    'suggestion': 'Consider using active voice',
                    'severity': 'low'
                })

        # Check for very long sentences (potential readability issue)
        sentences = re.split(r'[.!?]', text)
        for i, sentence in enumerate(sentences):
            word_count = len(sentence.split())
            if word_count > 40:
                issues.append({
                    'type': 'Long Sentence',
                    'text': sentence[:100] + '...' if len(sentence) > 100 else sentence,
                    'suggestion': f'Split into shorter sentences (currently {word_count} words)',
                    'severity': 'medium'
                })

        # Check for repeated words
        words = text.split()
        for i in range(len(words) - 1):
            if words[i].lower() == words[i + 1].lower() and words[i].lower() not in ['the', 'a', 'an']:
                issues.append({
                    'type': 'Repeated Word',
                    'text': f"{words[i]} {words[i+1]}",
                    'suggestion': 'Remove duplicate word',
                    'severity': 'medium'
                })

        return issues[:10]  # Return top 10 issues

    def calculate_strength_meter(self, text: str) -> Dict:
        """Calculate resume strength meter"""
        strengths = []

        # Check various strength indicators
        if len(re.findall(r'\b\d+%?\b', text)) > 3:  # Has quantifiable achievements
            strengths.append('Quantified achievements')

        if re.search(r'(led|managed|created|built|designed|implemented)', text, re.I):
            strengths.append('Strong action verbs')

        if re.search(r'(python|java|javascript|react|aws)', text, re.I):
            strengths.append('Relevant technical skills')

        if re.search(r'(education|bachelor|master|degree)', text, re.I):
            strengths.append('Education section')

        if re.search(r'(project|developed|built)', text, re.I):
            strengths.append('Project experience')

        if re.search(r'(certification|certified|aws|google|microsoft)', text, re.I):
            strengths.append('Professional certifications')

        # Calculate strength score
        strength_score = min(100, len(strengths) * 15 + 20)

        return {
            'score': strength_score,
            'strengths': strengths,
            'recommendations': self._get_strength_recommendations(strengths)
        }

    def _get_strength_recommendations(self, strengths: List[str]) -> List[str]:
        """Get recommendations based on current strengths"""
        recommendations = []

        if 'Quantified achievements' not in strengths:
            recommendations.append('Add measurable achievements (e.g., "Increased sales by 25%"')
        if 'Strong action verbs' not in strengths:
            recommendations.append('Use strong action verbs like Led, Built, Created')
        if 'Professional certifications' not in strengths:
            recommendations.append('Consider adding relevant certifications')
        if 'Project experience' not in strengths:
            recommendations.append('Include a projects section with key achievements')

        return recommendations

    def analyze_with_ai(self, text: str, job_description: str = None) -> Dict:
        """Use OpenAI/Gemini for deep analysis"""
        if not self.openai_key and not self.gemini_key:
            return {'error': 'No AI API key configured', 'fallback': True}

        try:
            # Use OpenAI if available
            if self.openai_key:
                return self._analyze_with_openai(text, job_description)
            else:
                return self._analyze_with_gemini(text, job_description)
        except Exception as e:
            print(f"AI analysis error: {e}")
            return {'error': str(e), 'fallback': True}

    def _analyze_with_openai(self, text: str, job_description: str = None) -> Dict:
        """Analyze using OpenAI"""
        import openai
        openai.api_key = self.openai_key

        prompt = f"""Analyze this resume and provide detailed feedback in JSON format:

RESUME:
{text[:2000]}

{f'JOB DESCRIPTION:\n{job_description}' if job_description else ''}

Provide JSON with:
{{
    "overall_rating": <0-100>,
    "strengths": [<3-5 key strengths>],
    "weaknesses": [<3-5 key weaknesses>],
    "readability_score": <0-100>,
    "impact_score": <0-100>,
    "recommendations": [<3-5 actionable recommendations>],
    "detailed_feedback": "<2-3 sentences>",
    "role_alignment": "<job title if matches>"
}}"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert resume reviewer and career consultant."},
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
            return {"error": str(e), "fallback": True}

    def _analyze_with_gemini(self, text: str, job_description: str = None) -> Dict:
        """Analyze using Google Gemini"""
        # Similar implementation for Gemini
        return {"error": "Gemini not implemented", "fallback": True}

    def calculate_job_match(self, resume_text: str, job_description: str) -> Dict:
        """Calculate match percentage with a specific job"""
        # Extract keywords from job description
        job_keywords = set(re.findall(r'\b\w{3,}\b', job_description.lower()))

        # Extract resume keywords
        resume_words = set(re.findall(r'\b\w{3,}\b', resume_text.lower()))

        # Filter to meaningful words (not common stopwords)
        stopwords = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'are', 'were', 'been', 'have', 'has', 'had'}
        job_keywords = job_keywords - stopwords
        resume_words = resume_words - stopwords

        # Calculate match
        if len(job_keywords) == 0:
            return {'match_percentage': 0, 'matched_keywords': [], 'missing_keywords': []}

        matched = job_keywords & resume_words
        missing = job_keywords - resume_words

        match_percentage = int((len(matched) / len(job_keywords)) * 100)

        return {
            'match_percentage': match_percentage,
            'matched_keywords': list(matched)[:20],
            'missing_keywords': list(missing)[:20],
            'score': match_percentage
        }

    def full_analysis(self, resume: Resume, job_description: str = None) -> Dict:
        """Perform complete resume analysis"""
        text = resume.extracted_text or ""

        if not text and resume.file:
            # Extract text from PDF if not already extracted
            try:
                text = self.extract_text_from_pdf(resume.file)
            except:
                text = ""

        results = {
            'resume_id': resume.id,
            'ats_score': self.calculate_ats_score(text, job_description),
            'skills': self.extract_skills(text),
            'missing_skills': self.find_missing_skills(text),
            'grammar_issues': self.check_grammar_issues(text),
            'strength_meter': self.calculate_strength_meter(text),
        }

        # Add AI analysis if available
        ai_analysis = self.analyze_with_ai(text, job_description)
        if not ai_analysis.get('fallback'):
            results['ai_analysis'] = ai_analysis
            results['overall_rating'] = ai_analysis.get('overall_rating', results['ats_score']['overall'])

        # Add job match if job description provided
        if job_description:
            results['job_match'] = self.calculate_job_match(text, job_description)

        # Ensure overall rating exists
        if 'overall_rating' not in results:
            results['overall_rating'] = results['ats_score']['overall']

        return results


# Singleton instance
resume_analyzer = ResumeAnalyzer()


def analyze_resume(resume_id: int, job_description: str = None) -> Dict:
    """Convenience function for resume analysis"""
    try:
        resume = Resume.objects.get(id=resume_id)
        return resume_analyzer.full_analysis(resume, job_description)
    except Resume.DoesNotExist:
        return {'error': 'Resume not found'}
    except Exception as e:
        return {'error': str(e)}