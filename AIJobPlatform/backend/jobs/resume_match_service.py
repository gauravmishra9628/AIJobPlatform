"""
Resume-Job Matching Service
Uses OpenAI/Gemini API + spaCy NLP for intelligent skill extraction and matching
"""

import re
import json
from typing import Dict, List, Tuple
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.conf import settings
import openai
from functools import lru_cache

# Load spaCy model for NLP
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # Fallback if model not installed
    nlp = None


class ResumeMatchService:
    """Service for matching resumes against job descriptions using AI and NLP"""
    
    # Common skill synonyms mapping
    SKILL_SYNONYMS = {
        "ml": ["machine learning", "ml"],
        "ai": ["artificial intelligence", "ai"],
        "nlp": ["natural language processing", "nlp"],
        "ds": ["data science", "ds"],
        "python": ["python", "py"],
        "js": ["javascript", "js"],
        "ts": ["typescript", "ts"],
        "react": ["reactjs", "react"],
        "vue": ["vuejs", "vue"],
        "sql": ["sql", "mysql", "postgresql"],
        "nosql": ["nosql", "mongodb", "dynamodb"],
        "aws": ["amazon web services", "aws"],
        "gcp": ["google cloud", "gcp"],
        "docker": ["docker", "container"],
        "k8s": ["kubernetes", "k8s"],
    }
    
    # Create reverse mapping for fast lookup
    CANONICAL_SKILLS = {}
    for canonical, synonyms in SKILL_SYNONYMS.items():
        for synonym in synonyms:
            CANONICAL_SKILLS[synonym.lower()] = canonical
    
    def __init__(self):
        self.openai_key = settings.OPENAI_API_KEY
        if self.openai_key:
            openai.api_key = self.openai_key
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract skills from resume/job description text
        Uses both NLP and keyword matching
        """
        if not text:
            return []
        
        text_lower = text.lower()
        extracted_skills = set()
        
        # Keyword-based extraction
        skill_keywords = self._get_skill_keywords()
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                # Canonicalize the skill
                canonical = self.CANONICAL_SKILLS.get(skill.lower(), skill)
                extracted_skills.add(canonical)
        
        # NLP-based extraction using spaCy if available
        if nlp:
            doc = nlp(text[:5000])  # Limit text for performance
            for token in doc:
                if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2:
                    skill_text = token.text.lower()
                    if skill_text in skill_keywords:
                        canonical = self.CANONICAL_SKILLS.get(skill_text, skill_text)
                        extracted_skills.add(canonical)
        
        return sorted(list(extracted_skills))
    
    def extract_resume_data(self, resume_text: str) -> Dict:
        """Parse resume and extract structured data"""
        if not resume_text:
            return {"skills": [], "experience_years": 0, "education": []}
        
        # Extract skills
        skills = self.extract_skills_from_text(resume_text)
        
        # Extract years of experience using regex
        experience_match = re.search(r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)', 
                                     resume_text, re.IGNORECASE)
        experience_years = int(experience_match.group(1)) if experience_match else 0
        
        # Extract education
        education = self._extract_education(resume_text)
        
        return {
            "skills": skills,
            "experience_years": experience_years,
            "education": education,
            "raw_text": resume_text[:2000]  # Keep first 2000 chars for context
        }
    
    def extract_job_requirements(self, job_description: str) -> Dict:
        """Extract structured requirements from job description"""
        if not job_description:
            return {"required_skills": [], "nice_to_have": [], "experience_level": "mid"}
        
        # Extract all skills
        all_skills = self.extract_skills_from_text(job_description)
        
        # Determine which skills are required vs nice-to-have using keywords
        required_skills = []
        nice_to_have = []
        
        job_lower = job_description.lower()
        
        for skill in all_skills:
            # Check proximity to "must have", "required", "essential"
            if any(req_keyword in job_lower for req_keyword in 
                   ["must have", "required", "essential", "mandatory"]):
                required_skills.append(skill)
            else:
                nice_to_have.append(skill)
        
        # Determine experience level
        experience_level = self._determine_experience_level(job_description)
        
        return {
            "required_skills": required_skills,
            "nice_to_have": nice_to_have,
            "experience_level": experience_level,
            "raw_text": job_description[:2000]
        }
    
    def calculate_match_score(self, resume_data: Dict, job_requirements: Dict) -> Dict:
        """
        Calculate detailed match score between resume and job
        Returns: match %, matched skills, missing skills, recommendations
        """
        resume_skills = set(resume_data.get("skills", []))
        required_skills = set(job_requirements.get("required_skills", []))
        nice_to_have = set(job_requirements.get("nice_to_have", []))
        
        # Calculate matches
        matched_required = resume_skills.intersection(required_skills)
        matched_nice = resume_skills.intersection(nice_to_have)
        missing_required = required_skills - resume_skills
        missing_nice = nice_to_have - resume_skills
        
        # Calculate match percentage
        if required_skills:
            required_match_pct = (len(matched_required) / len(required_skills)) * 100
        else:
            required_match_pct = 100
        
        # Weight: required skills (70%) + nice-to-have (30%)
        total_skills = required_skills.union(nice_to_have)
        if total_skills:
            total_matched = matched_required.union(matched_nice)
            overall_match = (len(total_matched) / len(total_skills)) * 100
        else:
            overall_match = 50
        
        # Experience check
        experience_multiplier = self._calculate_experience_multiplier(
            resume_data.get("experience_years", 0),
            job_requirements.get("experience_level", "mid")
        )
        
        # Final score (0-100)
        final_score = min(100, overall_match * experience_multiplier)
        
        return {
            "match_percentage": round(final_score, 1),
            "matched_skills": sorted(list(matched_required)),
            "missing_skills_required": sorted(list(missing_required)),
            "missing_skills_nice": sorted(list(missing_nice)),
            "experience_gap": max(0, resume_data.get("experience_years", 0) - 
                                 self._exp_level_to_years(job_requirements.get("experience_level", "mid"))),
            "match_breakdown": {
                "required_match": round(required_match_pct, 1),
                "nice_to_have_match": round(
                    (len(matched_nice) / len(nice_to_have) * 100) if nice_to_have else 0, 1
                ),
                "experience_multiplier": round(experience_multiplier, 2)
            }
        }
    
    def generate_improvement_suggestions(self, missing_skills: List[str], 
                                         job_description: str) -> List[Dict]:
        """
        Generate actionable improvement suggestions using LLM
        """
        if not missing_skills:
            return []
        
        if not self.openai_key:
            # Fallback if no API key
            return [
                {
                    "skill": skill,
                    "importance": "high" if skill in missing_skills[:3] else "medium",
                    "learning_time_weeks": 4,
                    "resources": [
                        f"Search for '{skill}' courses on Udemy or Coursera"
                    ]
                }
                for skill in missing_skills[:5]
            ]
        
        try:
            prompt = f"""
            Based on the job description and missing skills, suggest how to improve.
            
            Missing skills: {', '.join(missing_skills[:5])}
            Job description: {job_description[:1000]}
            
            Provide 3-5 specific, actionable suggestions in JSON format:
            [
                {{
                    "skill": "skill name",
                    "importance": "high/medium/low",
                    "learning_time_weeks": 4,
                    "resources": ["resource 1", "resource 2"],
                    "tips": "specific tips"
                }}
            ]
            
            Only return valid JSON, no other text.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            suggestions_text = response.choices[0].message.content.strip()
            # Try to parse JSON from response
            try:
                suggestions = json.loads(suggestions_text)
                return suggestions[:5]  # Limit to 5 suggestions
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return []
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return []
    
    def get_similarity_score(self, text1: str, text2: str) -> float:
        """Calculate TF-IDF cosine similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        vectorizer = TfidfVectorizer(max_features=100)
        try:
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
            return float(similarity)
        except:
            return 0.0
    
    # Helper methods
    
    @staticmethod
    @lru_cache(maxsize=1)
    def _get_skill_keywords() -> set:
        """Get comprehensive list of skill keywords"""
        return {
            "python", "java", "javascript", "typescript", "cpp", "c#", "go", "rust",
            "react", "vue", "angular", "svelte", "nodejs", "django", "flask", "fastapi",
            "sql", "mysql", "postgresql", "mongodb", "dynamodb", "cassandra", "elasticsearch",
            "aws", "gcp", "azure", "docker", "kubernetes", "jenkins", "gitlab",
            "machine learning", "deep learning", "nlp", "computer vision", "tensorflow",
            "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib",
            "git", "github", "gitlab", "bitbucket",
            "agile", "scrum", "kanban",
            "rest", "graphql", "api", "microservices",
            "html", "css", "sass", "tailwind",
            "linux", "windows", "macos",
            "communication", "leadership", "teamwork", "problem solving",
            "devops", "ci/cd", "terraform", "ansible",
            "redis", "rabbitmq", "kafka",
            "excel", "power bi", "tableau", "looker",
            "figma", "sketch", "adobe", "xd",
        }
    
    @staticmethod
    def _extract_education(text: str) -> List[str]:
        """Extract education details from resume text"""
        education_keywords = ["bachelor", "master", "phd", "diploma", "bs", "ms", "btech", "mtech"]
        education = []
        
        for keyword in education_keywords:
            if keyword in text.lower():
                # Simple extraction - could be enhanced
                education.append(keyword.title())
        
        return education
    
    @staticmethod
    def _determine_experience_level(job_description: str) -> str:
        """Determine required experience level from job description"""
        text_lower = job_description.lower()
        
        if any(word in text_lower for word in ["senior", "lead", "principal", "expert"]):
            return "senior"
        elif any(word in text_lower for word in ["junior", "entry", "graduate", "fresher"]):
            return "junior"
        else:
            return "mid"
    
    @staticmethod
    def _calculate_experience_multiplier(candidate_years: int, required_level: str) -> float:
        """Calculate multiplier based on experience alignment"""
        level_years = {
            "junior": 1,
            "mid": 3,
            "senior": 5
        }
        
        required_years = level_years.get(required_level, 3)
        
        if candidate_years < required_years:
            # Penalty for insufficient experience
            return max(0.5, 1.0 - (required_years - candidate_years) * 0.1)
        else:
            # Bonus for extra experience
            return min(1.2, 1.0 + (candidate_years - required_years) * 0.05)
    
    @staticmethod
    def _exp_level_to_years(level: str) -> int:
        """Convert experience level to years"""
        mapping = {"junior": 1, "mid": 3, "senior": 5}
        return mapping.get(level, 3)
