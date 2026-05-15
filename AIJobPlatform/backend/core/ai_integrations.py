"""
AI Integration Module - OpenAI & Google Gemini
Handles all AI-powered features with fallback logic
"""

import os
import json
from typing import Optional, List, Dict
import openai
from django.conf import settings

# Initialize OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY


class AIIntegrationService:
    """Service class for all AI integrations with fallback logic"""
    
    @staticmethod
    def analyze_resume_with_ai(resume_text: str, job_description: Optional[str] = None) -> Dict:
        """
        Analyze resume using OpenAI GPT-4 or GPT-3.5
        Falls back to rule-based analysis if API fails
        """
        try:
            prompt = f"""Analyze this resume and provide detailed feedback in JSON format:

RESUME TEXT:
{resume_text}

{f'TARGET JOB DESCRIPTION:{job_description}' if job_description else ''}

Provide response as valid JSON with exactly these keys:
{{
    "overall_rating": <0-100>,
    "strengths": [<list of 3-5 strengths>],
    "weaknesses": [<list of 3-5 weaknesses>],
    "readability_score": <0-100>,
    "impact_score": <0-100>,
    "recommendations": [<list of 3-5 actionable recommendations>],
    "detailed_feedback": "<2-3 sentences of professional feedback>",
    "extracted_skills": [<list of identified skills>],
    "ats_compatibility": <0-100>
}}"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert resume reviewer and HR consultant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content
            # Clean response - remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            return {
                "success": True,
                "data": result,
                "model": "gpt-3.5-turbo"
            }
            
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            # Return rule-based analysis as fallback
            return AIIntegrationService._rule_based_resume_analysis(resume_text)

    @staticmethod
    def _rule_based_resume_analysis(resume_text: str) -> Dict:
        """Rule-based fallback for resume analysis"""
        resume_lower = resume_text.lower()
        
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Strengths detection
        if len(resume_text) > 800:
            strengths.append("Comprehensive and detailed resume content")
        if any(kw in resume_lower for kw in ["led", "managed", "achieved", "implemented", "developed"]):
            strengths.append("Strong action verbs showing impact")
        if any(kw in resume_lower for kw in ["%", "increased", "reduced", "grew", "saved", "$"]):
            strengths.append("Quantified achievements and metrics")
        
        # Weaknesses detection
        if len(resume_text) < 300:
            weaknesses.append("Resume too brief - consider adding more detail")
        if not any(kw in resume_lower for kw in ["experience", "project", "achievement"]):
            weaknesses.append("Lacks specific examples and measurable results")
        if resume_lower.count("\n") < 5:
            weaknesses.append("Poor formatting and structure")
        
        # Scoring
        readability_score = min(100, (len(resume_text) // 8))
        impact_score = 60
        
        if any(m in resume_lower for m in ["increased", "reduced", "improved", "achieved"]):
            impact_score += 15
        if len(resume_text) > 500:
            impact_score += 10
        
        # Recommendations
        if readability_score < 70:
            recommendations.append("Use consistent formatting and clear section headers")
        if impact_score < 75:
            recommendations.append("Add quantifiable results and specific achievements")
        recommendations.append("Ensure ATS compatibility with standard formatting")
        recommendations.append("Tailor resume content to target job requirements")
        
        return {
            "success": False,
            "fallback": True,
            "data": {
                "overall_rating": (readability_score + impact_score) // 2,
                "strengths": strengths[:3],
                "weaknesses": weaknesses[:3],
                "readability_score": readability_score,
                "impact_score": impact_score,
                "recommendations": recommendations,
                "detailed_feedback": "Resume analysis completed using rule-based engine.",
                "extracted_skills": [],
                "ats_compatibility": impact_score
            },
            "model": "rule-based"
        }

    @staticmethod
    def generate_interview_questions(job_title: str, skills: List[str]) -> Dict:
        """Generate interview questions using OpenAI"""
        try:
            prompt = f"""Generate 5 tough interview questions for a {job_title} position.
Candidate skills: {', '.join(skills)}

Return as JSON:
{{
    "technical_questions": [<list of 2-3 technical questions>],
    "hr_questions": [<list of 2-3 HR/behavioral questions>],
    "tips": [<list of interview tips>]
}}"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            
            return {"success": True, "data": json.loads(content)}
            
        except Exception as e:
            print(f"Interview questions generation error: {str(e)}")
            return {
                "success": False,
                "data": {
                    "technical_questions": ["Tell us about your experience with this role"],
                    "hr_questions": ["Why are you interested in this position?"],
                    "tips": ["Practice mock interviews", "Research the company beforehand"]
                }
            }

    @staticmethod
    def generate_skill_gap_analysis(current_skills: List[str], target_role: str) -> Dict:
        """Generate skill gap analysis using OpenAI"""
        try:
            prompt = f"""Analyze skill gap for someone with skills: {', '.join(current_skills)}
who wants to become a {target_role}.

Return as JSON:
{{
    "missing_skills": [<critical skills to learn>],
    "learning_paths": [<resources or courses to learn each missing skill>],
    "estimated_months_to_ready": <number>,
    "career_progression": [<step-by-step progression>],
    "top_companies_hiring": [<companies hiring for this role>]
}}"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            
            return {"success": True, "data": json.loads(content)}
            
        except Exception as e:
            print(f"Skill gap analysis error: {str(e)}")
            return {
                "success": False,
                "data": {
                    "missing_skills": ["Advanced skill 1", "Advanced skill 2"],
                    "learning_paths": ["Online course for skill 1", "Project-based learning for skill 2"],
                    "estimated_months_to_ready": 6,
                    "career_progression": ["Current role", "Mid-level role", "Target role"],
                    "top_companies_hiring": ["Company A", "Company B", "Company C"]
                }
            }

    @staticmethod
    def generate_job_recommendations(user_profile: Dict, top_n: int = 5) -> List[Dict]:
        """Generate personalized job recommendations using AI logic"""
        # This uses rule-based matching for now, can be enhanced with AI
        try:
            skills = user_profile.get("skills", [])
            experience = user_profile.get("experience", "junior")
            
            # Would call OpenAI here for semantic matching
            # For now, returning structured format for frontend
            return {
                "success": True,
                "recommendations": [
                    {
                        "reason": f"Strong match for your {', '.join(skills[:3])} skills",
                        "match_score": 85
                    }
                ]
            }
        except Exception as e:
            print(f"Job recommendation error: {str(e)}")
            return {"success": False, "recommendations": []}

    @staticmethod
    def generate_cover_letter(user_name: str, job_title: str, company: str, skills: List[str]) -> Dict:
        """Generate personalized cover letter using OpenAI"""
        try:
            prompt = f"""Write a professional cover letter for {user_name} applying for a {job_title} position at {company}.
Key skills: {', '.join(skills)}

Format as:
[Opening paragraph with enthusiasm]
[Skills paragraph mentioning relevant experience]
[Closing paragraph with call to action]"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=600
            )
            
            cover_letter = response.choices[0].message.content
            return {"success": True, "cover_letter": cover_letter}
            
        except Exception as e:
            print(f"Cover letter generation error: {str(e)}")
            return {
                "success": False,
                "cover_letter": f"Dear Hiring Manager,\n\nI am interested in the {job_title} position at {company}..."
            }
