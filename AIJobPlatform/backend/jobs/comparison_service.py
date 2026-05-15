import math
import re
from collections import Counter
from functools import lru_cache
from typing import Dict, Iterable, List, Optional

from django.conf import settings
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import SkillMapping


try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

try:
    import spacy
except Exception:
    spacy = None


@lru_cache(maxsize=1)
def get_nlp():
    if not spacy:
        return None
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_sentence_model():
    enabled = getattr(settings, "ENABLE_SENTENCE_TRANSFORMERS", False)
    if not enabled or SentenceTransformer is None:
        return None
    try:
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


class SkillMapper:
    """Canonicalizes skills and finds equivalent skills in parsed resume data."""

    DEFAULT_SYNONYMS = {
        "python": {"python", "py"},
        "javascript": {"javascript", "js", "ecmascript"},
        "typescript": {"typescript", "ts"},
        "react": {"react", "reactjs", "react.js"},
        "node.js": {"node", "nodejs", "node.js"},
        "django": {"django", "django rest framework", "drf"},
        "docker": {"docker", "containers", "containerization"},
        "kubernetes": {"kubernetes", "k8s"},
        "aws": {"aws", "amazon web services"},
        "gcp": {"gcp", "google cloud"},
        "azure": {"azure", "microsoft azure"},
        "sql": {"sql", "mysql", "postgresql", "postgres", "sqlite"},
        "machine learning": {"machine learning", "ml"},
        "artificial intelligence": {"artificial intelligence", "ai"},
        "nlp": {"nlp", "natural language processing"},
        "rest api": {"rest", "rest api", "restful api", "apis"},
        "git": {"git", "github", "gitlab"},
        "redis": {"redis", "cache", "caching"},
        "celery": {"celery", "background tasks", "task queue"},
    }

    def __init__(self):
        self.synonyms = {skill: set(aliases) for skill, aliases in self.DEFAULT_SYNONYMS.items()}
        self._load_database_mappings()

    def canonicalize(self, value: str) -> str:
        normalized = self.normalize(value)
        for canonical, aliases in self.synonyms.items():
            if normalized == canonical or normalized in aliases:
                return canonical
        return normalized

    def aliases_for(self, value: str) -> set:
        canonical = self.canonicalize(value)
        return {canonical, *self.synonyms.get(canonical, set())}

    def find_in_resume(self, canonical_skill: str, resume_data: Dict) -> Optional[str]:
        target_aliases = self.aliases_for(canonical_skill)
        for skill in resume_data.get("skills", []):
            if self.canonicalize(skill) in target_aliases or self.normalize(skill) in target_aliases:
                return skill

        raw_text = self.normalize(resume_data.get("raw_text", ""))
        for alias in target_aliases:
            if re.search(rf"\b{re.escape(alias)}\b", raw_text):
                return alias
        return None

    def normalize(self, value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "").lower()).strip()

    def _load_database_mappings(self):
        try:
            for mapping in SkillMapping.objects.all().only("skill_name", "synonyms"):
                canonical = self.normalize(mapping.skill_name)
                aliases = {self.normalize(item) for item in (mapping.synonyms or []) if item}
                self.synonyms.setdefault(canonical, set()).update(aliases)
        except Exception:
            pass


class OpenAIEmbeddings:
    """
    Lightweight similarity adapter.

    The name mirrors the roadmap, but this class intentionally uses local TF-IDF
    so comparisons work in development and tests without network access.
    """

    def similarity(self, text_a: str, text_b: str) -> float:
        if not text_a or not text_b:
            return 0.0
        normalized_a = str(text_a).strip().lower()
        normalized_b = str(text_b).strip().lower()
        if normalized_a == normalized_b:
            return 1.0
        try:
            matrix = TfidfVectorizer(ngram_range=(1, 2), analyzer="char_wb").fit_transform([text_a, text_b])
            return float(cosine_similarity(matrix[0], matrix[1])[0][0])
        except Exception:
            return 0.0


class ResumeJobComparator:
    """Roadmap-facing resume-to-job comparator with deterministic fallbacks."""

    BASE_SKILLS = {
        "python", "java", "javascript", "typescript", "react", "vue", "angular", "node.js",
        "django", "flask", "fastapi", "sql", "postgresql", "mysql", "mongodb", "redis",
        "docker", "kubernetes", "aws", "azure", "gcp", "git", "rest api", "graphql",
        "html", "css", "tailwind", "celery", "rabbitmq", "kafka", "machine learning",
        "deep learning", "artificial intelligence", "nlp", "tensorflow", "pytorch",
        "scikit-learn", "pandas", "numpy", "linux", "ci/cd", "terraform", "excel",
        "power bi", "tableau", "communication", "leadership", "problem solving",
        "microservices", "agile", "scrum", "figma",
    }

    CERTIFICATIONS = {
        "aws certified", "azure certified", "google cloud certified", "pmp",
        "scrum master", "cka", "ckad", "security+", "cissp",
    }

    LOCATION_MULTIPLIERS = {
        "remote": 1.0,
        "bangalore": 1.12,
        "bengaluru": 1.12,
        "mumbai": 1.15,
        "delhi": 1.08,
        "hyderabad": 1.05,
        "pune": 1.03,
        "chennai": 1.0,
        "kolkata": 0.95,
    }

    def __init__(self):
        self.skill_mapper = SkillMapper()
        self.embedder = OpenAIEmbeddings()

    def extract_resume_data(self, resume_text: str) -> Dict:
        """Extract structured resume data from plain text parsed from PDF/DOCX/TXT."""
        resume_text = resume_text or ""
        return {
            "skills": self.extract_skills(resume_text),
            "experience_years": self.extract_experience_years(resume_text),
            "education": self.extract_education(resume_text),
            "certifications": self.extract_certifications(resume_text),
            "keywords": self.extract_keywords(resume_text),
            "raw_text": resume_text[:5000],
        }

    def extract_job_requirements(self, job) -> Dict:
        """Extract required skills, nice-to-have skills, certificates, and experience from a JobPost-like object."""
        description = getattr(job, "description", "") or ""
        skills_text = getattr(job, "skills_required", "") or ""
        requirements = getattr(job, "requirements", None) or {}
        if not isinstance(requirements, dict):
            requirements = {}

        explicit_required = self._split_skills(skills_text)
        explicit_must = self._normalize_list(requirements.get("must_have") or requirements.get("required_skills"))
        explicit_nice = self._normalize_list(requirements.get("nice_to_have") or requirements.get("preferred_skills"))

        extracted = self.extract_skills(description)
        required_from_text, nice_from_text = self._classify_job_skills(description, extracted)
        required_skills = sorted(set(explicit_required + explicit_must + required_from_text))
        nice_to_have = sorted(set(explicit_nice + [skill for skill in nice_from_text if skill not in required_skills]))
        must_have = sorted(set(explicit_must or required_skills))

        return {
            "required_skills": required_skills,
            "nice_to_have": nice_to_have,
            "must_have": must_have,
            "must_have_certs": self._normalize_list(
                requirements.get("certifications") or getattr(job, "required_certifications", []) or []
            ),
            "experience_years": getattr(job, "required_experience_years", 0) or self.extract_required_experience(description),
            "education": getattr(job, "required_education", "") or self.extract_required_education(description),
            "keywords": self.extract_keywords(description),
            "salary_min": getattr(job, "salary_min", None),
            "salary_max": getattr(job, "salary_max", None),
            "salary_range": getattr(job, "salary_range", ""),
            "location": getattr(job, "location", ""),
            "raw_text": description[:5000],
        }

    def calculate_match_score(self, resume_data: Dict, job_data: Dict) -> Dict:
        """
        Calculate overall match, skill-by-skill scores, missing critical skills,
        experience gap, and certification gap.
        """
        required_skills = job_data.get("required_skills", [])
        must_have = {self.skill_mapper.canonicalize(skill) for skill in job_data.get("must_have", [])}
        matched_skills = []
        missing_skills = []
        weighted_scores = []

        for req_skill in required_skills:
            canonical_skill = self.skill_mapper.canonicalize(req_skill)
            resume_skill = self.skill_mapper.find_in_resume(canonical_skill, resume_data)
            weight = 1.4 if canonical_skill in must_have else 1.0

            if resume_skill:
                score = max(0.78, self.embedder.similarity(req_skill, resume_skill))
                matched_skills.append({
                    "skill": req_skill,
                    "score": round(score * 100, 1),
                    "candidate_skill": resume_skill,
                    "impact": "critical" if canonical_skill in must_have else "standard",
                })
                weighted_scores.append(score * weight)
            else:
                missing_skills.append({
                    "skill": req_skill,
                    "impact": "critical" if canonical_skill in must_have else "nice_to_have",
                })
                weighted_scores.append(0)

        denominator = sum(1.4 if self.skill_mapper.canonicalize(skill) in must_have else 1.0 for skill in required_skills)
        skill_pct = (sum(weighted_scores) / denominator * 100) if denominator else 50.0
        experience_gap = self.calculate_exp_gap(resume_data, job_data)
        certification_gap = self.calculate_cert_gap(resume_data, job_data)
        experience_adjustment = -min(18, abs(experience_gap) * 6) if experience_gap < 0 else min(8, experience_gap * 2)
        cert_penalty = min(12, len(certification_gap) * 4)
        match_pct = np.clip(skill_pct + experience_adjustment - cert_penalty, 0, 100)

        return {
            "match_percentage": round(float(match_pct), 1),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "experience_gap": experience_gap,
            "certification_gap": certification_gap,
            "skill_match_percentage": round(skill_pct, 1),
        }

    def predict_salary(self, match_score: float, job_salary: float, experience_years: int, location: str) -> Dict:
        """Predict a salary band from job salary, match quality, experience, and location."""
        base = float(job_salary or 900000)
        match_multiplier = 0.82 + (max(0, min(match_score, 100)) / 100 * 0.28)
        experience_multiplier = 1 + min(max(experience_years, 0), 12) * 0.025
        location_multiplier = self._location_multiplier(location)
        prediction = base * match_multiplier * experience_multiplier * location_multiplier
        spread = 0.08 if match_score >= 75 else 0.12

        return {
            "predicted_salary": round(prediction, 2),
            "salary_min": round(prediction * (1 - spread), 2),
            "salary_max": round(prediction * (1 + spread), 2),
            "currency": "INR",
            "confidence": "high" if match_score >= 80 else "medium" if match_score >= 55 else "low",
            "factors": {
                "match_score": match_score,
                "experience_years": experience_years,
                "location_multiplier": location_multiplier,
            },
        }

    def generate_improvement_suggestions(self, missing_skills: List, experience_gap: float) -> List[Dict]:
        """Return prioritized recommendations with rough time estimates."""
        suggestions = []
        normalized_missing = [
            item if isinstance(item, dict) else {"skill": item, "impact": "standard"}
            for item in missing_skills
        ]
        critical = [item for item in normalized_missing if item.get("impact") == "critical"]
        standard = [item for item in normalized_missing if item.get("impact") != "critical"]

        for item in (critical + standard)[:6]:
            skill = item.get("skill", "")
            is_critical = item.get("impact") == "critical"
            suggestions.append({
                "type": "skill",
                "title": f"Build a {skill.title()} proof project",
                "skill": skill,
                "priority": "high" if is_critical else "medium",
                "time_estimate": "2-4 weeks" if is_critical else "1-2 weeks",
                "impact": 18 if is_critical else 9,
                "message": f"Add one measurable project or work bullet showing {skill} in a production-like context.",
            })

        if experience_gap < 0:
            suggestions.append({
                "type": "experience",
                "title": "Close the experience signal gap",
                "priority": "high",
                "time_estimate": "4-8 weeks",
                "impact": min(20, int(abs(experience_gap) * 6)),
                "message": "Create a scoped portfolio project and quantify ownership, scale, and outcomes in resume bullets.",
            })

        return suggestions[:8]

    def calculate_exp_gap(self, resume_data: Dict, job_data: Dict) -> float:
        return round(float(resume_data.get("experience_years", 0)) - float(job_data.get("experience_years", 0)), 1)

    def calculate_cert_gap(self, resume_data: Dict, job_data: Dict) -> List[str]:
        resume_certs = {self.skill_mapper.normalize(cert) for cert in resume_data.get("certifications", [])}
        return [
            cert for cert in job_data.get("must_have_certs", [])
            if self.skill_mapper.normalize(cert) not in resume_certs
        ]

    def extract_skills(self, text: str) -> List[str]:
        normalized = self.skill_mapper.normalize(text)
        skills = set()
        for skill in self.BASE_SKILLS:
            if any(re.search(rf"\b{re.escape(alias)}\b", normalized) for alias in self.skill_mapper.aliases_for(skill)):
                skills.add(self.skill_mapper.canonicalize(skill))
        return sorted(skills)

    def extract_experience_years(self, text: str) -> float:
        patterns = [
            r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
            r"experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
        ]
        matches = []
        for pattern in patterns:
            matches.extend(float(value) for value in re.findall(pattern, text or "", re.IGNORECASE))
        return max(matches) if matches else 0

    def extract_required_experience(self, text: str) -> int:
        match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text or "", re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def extract_education(self, text: str) -> List[str]:
        degrees = ["bachelor", "master", "phd", "b.tech", "m.tech", "bsc", "msc", "mba", "degree", "diploma"]
        normalized = self.skill_mapper.normalize(text)
        return [degree for degree in degrees if degree in normalized]

    def extract_required_education(self, text: str) -> str:
        education = self.extract_education(text)
        return education[0] if education else ""

    def extract_certifications(self, text: str) -> List[str]:
        normalized = self.skill_mapper.normalize(text)
        return [cert for cert in self.CERTIFICATIONS if cert in normalized]

    def extract_keywords(self, text: str, limit: int = 30) -> List[str]:
        words = re.findall(r"[a-zA-Z][a-zA-Z+#.]{2,}", self.skill_mapper.normalize(text))
        stop = {"and", "the", "for", "with", "you", "our", "are", "will", "from", "that", "this", "your"}
        counts = Counter(word for word in words if word not in stop)
        return [word for word, _ in counts.most_common(limit)]

    def _classify_job_skills(self, description: str, skills: List[str]) -> tuple:
        required = []
        nice = []
        normalized = self.skill_mapper.normalize(description)
        sentences = [self.skill_mapper.normalize(sentence) for sentence in re.split(r"[.!?\n]+", normalized)]
        required_terms = ("required", "must have", "mandatory", "essential")
        nice_terms = ("nice to have", "preferred", "bonus", "good to have")
        for skill in skills:
            aliases = self.skill_mapper.aliases_for(skill)
            contexts = [sentence for sentence in sentences if any(alias in sentence for alias in aliases)]
            required_hit = any(term in sentence for sentence in contexts for term in required_terms)
            nice_hit = any(term in sentence for sentence in contexts for term in nice_terms)
            if required_hit or not nice_hit:
                required.append(skill)
            else:
                nice.append(skill)
        return required, nice

    def _split_skills(self, skills_text: str) -> List[str]:
        return [self.skill_mapper.canonicalize(part) for part in re.split(r"[,;|/\n]", skills_text or "") if part.strip()]

    def _normalize_list(self, value) -> List[str]:
        if isinstance(value, str):
            return self._split_skills(value)
        if isinstance(value, (list, tuple, set)):
            return [self.skill_mapper.canonicalize(item) for item in value if item]
        return []

    def _location_multiplier(self, location: str) -> float:
        normalized = self.skill_mapper.normalize(location)
        for key, multiplier in self.LOCATION_MULTIPLIERS.items():
            if key in normalized:
                return multiplier
        return 1.0


class AIComparisonService:
    SKILL_SYNONYMS = {
        "python": {"python", "py"},
        "javascript": {"javascript", "js", "ecmascript"},
        "typescript": {"typescript", "ts"},
        "react": {"react", "reactjs", "react.js"},
        "node.js": {"node", "nodejs", "node.js"},
        "django": {"django", "django rest framework", "drf"},
        "docker": {"docker", "containers", "containerization"},
        "kubernetes": {"kubernetes", "k8s"},
        "aws": {"aws", "amazon web services"},
        "sql": {"sql", "mysql", "postgresql", "postgres", "sqlite"},
        "machine learning": {"machine learning", "ml"},
        "artificial intelligence": {"artificial intelligence", "ai"},
        "nlp": {"nlp", "natural language processing"},
        "rest api": {"rest", "rest api", "restful api", "apis"},
        "git": {"git", "github", "gitlab"},
        "redis": {"redis", "cache", "caching"},
        "celery": {"celery", "background tasks", "task queue"},
    }

    BASE_SKILLS = {
        "python", "java", "javascript", "typescript", "react", "vue", "angular", "node.js",
        "django", "flask", "fastapi", "sql", "postgresql", "mysql", "mongodb", "redis",
        "docker", "kubernetes", "aws", "azure", "gcp", "git", "rest api", "graphql",
        "html", "css", "tailwind", "celery", "rabbitmq", "kafka", "machine learning",
        "deep learning", "artificial intelligence", "nlp", "tensorflow", "pytorch",
        "scikit-learn", "pandas", "numpy", "linux", "ci/cd", "terraform", "excel",
        "power bi", "tableau", "communication", "leadership", "problem solving",
    }

    IMPACT_VERBS = {
        "built", "launched", "improved", "reduced", "increased", "optimized", "automated",
        "designed", "implemented", "scaled", "migrated", "delivered", "owned",
    }

    def parse_resume(self, text: str) -> Dict:
        text = text or ""
        return {
            "skills": self.extract_skills(text),
            "experience_years": self.extract_experience_years(text),
            "education": self.extract_education(text),
            "certifications": self.extract_certifications(text),
            "keywords": self.extract_keywords(text),
            "ats_score": self.score_ats(text),
        }

    def parse_job(self, job) -> Dict:
        description = getattr(job, "description", "") or ""
        explicit_skills = self._split_skills(getattr(job, "skills_required", "") or "")
        required_skills = sorted(set(explicit_skills + self.extract_skills(description)))
        requirements = getattr(job, "requirements", None) or {}
        certifications = requirements.get("certifications") or getattr(job, "required_certifications", []) or []
        return {
            "skills": required_skills,
            "experience_years": getattr(job, "required_experience_years", 0) or self.extract_required_experience(description),
            "education": getattr(job, "required_education", "") or self.extract_required_education(description),
            "certifications": certifications,
            "keywords": self.extract_keywords(description),
            "salary_min": getattr(job, "salary_min", None),
            "salary_max": getattr(job, "salary_max", None),
        }

    def compare(self, resume, job) -> Dict:
        resume_text = resume.extracted_text or ""
        job_text = f"{job.title}\n{job.description}\n{job.skills_required}"
        resume_data = self.parse_resume(resume_text)
        job_data = self.parse_job(job)

        tfidf = self.tfidf_similarity(resume_text, job_text)
        semantic = self.semantic_similarity(resume_text, job_text)
        skill_result = self.match_skills(resume_data["skills"], job_data["skills"])
        experience_score = self.score_experience(resume_data["experience_years"], job_data["experience_years"])
        ats_score = self.score_ats(resume_text, job_data["keywords"])
        salary = self.estimate_salary(job, resume_data, skill_result["match_percentage"])

        match_percentage = round(
            (skill_result["match_percentage"] * 0.42)
            + (experience_score * 0.18)
            + (ats_score * 0.16)
            + (tfidf * 100 * 0.14)
            + (semantic * 100 * 0.10),
            1,
        )

        missing_certs = self.detect_missing_certifications(
            resume_data["certifications"], job_data["certifications"]
        )
        suggestions = self.generate_improvement_suggestions(
            skill_result["missing_skills"], missing_certs, ats_score, resume_data, job_data
        )

        return {
            "match_percentage": min(100, max(0, match_percentage)),
            "semantic_similarity": round(semantic, 4),
            "tfidf_similarity": round(tfidf, 4),
            "skill_match": skill_result["skill_match"],
            "matched_skills": skill_result["matched_skills"],
            "missing_skills": skill_result["missing_skills"],
            "missing_certifications": missing_certs,
            "experience_score": round(experience_score, 1),
            "ats_score": ats_score,
            "salary_prediction": salary,
            "improvement_suggestions": suggestions,
            "career_recommendations": self.recommend_career_path(skill_result["missing_skills"], match_percentage),
            "keyword_analysis": self.keyword_analysis(resume_data["keywords"], job_data["keywords"]),
            "heatmap": self.job_fit_heatmap(skill_result, experience_score, ats_score, tfidf, semantic),
            "resume_data": resume_data,
            "job_data": job_data,
        }

    def extract_skills(self, text: str) -> List[str]:
        normalized = self.normalize(text)
        skills = set()
        for skill in self.BASE_SKILLS:
            aliases = self.SKILL_SYNONYMS.get(skill, {skill})
            if any(re.search(rf"\b{re.escape(alias)}\b", normalized) for alias in aliases):
                skills.add(skill)

        nlp = get_nlp()
        if nlp:
            doc = nlp(text[:6000])
            for chunk in doc.noun_chunks:
                phrase = self.canonical_skill(chunk.text)
                if phrase in self.BASE_SKILLS:
                    skills.add(phrase)
        return sorted(skills)

    def extract_keywords(self, text: str, limit: int = 30) -> List[str]:
        words = re.findall(r"[a-zA-Z][a-zA-Z+#.]{2,}", self.normalize(text))
        stop = {"and", "the", "for", "with", "you", "our", "are", "will", "from", "that", "this", "your"}
        counts = Counter(word for word in words if word not in stop)
        return [word for word, _ in counts.most_common(limit)]

    def extract_experience_years(self, text: str) -> float:
        patterns = [
            r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
            r"experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
        ]
        matches = []
        for pattern in patterns:
            matches.extend(float(value) for value in re.findall(pattern, text, re.IGNORECASE))
        return max(matches) if matches else 0

    def extract_required_experience(self, text: str) -> int:
        match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text or "", re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def extract_education(self, text: str) -> List[str]:
        degrees = ["bachelor", "master", "phd", "b.tech", "m.tech", "bsc", "msc", "mba", "degree", "diploma"]
        normalized = self.normalize(text)
        return [degree for degree in degrees if degree in normalized]

    def extract_required_education(self, text: str) -> str:
        education = self.extract_education(text)
        return education[0] if education else ""

    def extract_certifications(self, text: str) -> List[str]:
        patterns = ["aws certified", "azure certified", "pmp", "scrum master", "cka", "ckad", "security+"]
        normalized = self.normalize(text)
        return [cert for cert in patterns if cert in normalized]

    def match_skills(self, resume_skills: Iterable[str], job_skills: Iterable[str]) -> Dict:
        resume_set = {self.canonical_skill(skill) for skill in resume_skills}
        job_set = {self.canonical_skill(skill) for skill in job_skills if skill}
        matched = sorted(resume_set & job_set)
        missing = sorted(job_set - resume_set)
        denominator = max(len(job_set), 1)
        skill_match = {
            skill: {"match_score": 100 if skill in resume_set else 0, "required": True}
            for skill in sorted(job_set)
        }
        return {
            "match_percentage": round((len(matched) / denominator) * 100, 1),
            "matched_skills": matched,
            "missing_skills": missing,
            "skill_match": skill_match,
        }

    def detect_missing_certifications(self, resume_certs: Iterable[str], job_certs: Iterable[str]) -> List[str]:
        resume_set = {self.normalize(cert) for cert in resume_certs}
        return [cert for cert in job_certs if self.normalize(str(cert)) not in resume_set]

    def score_experience(self, candidate_years: float, required_years: float) -> float:
        if not required_years:
            return 80 if candidate_years else 65
        if candidate_years >= required_years:
            return min(100, 85 + ((candidate_years - required_years) * 3))
        return max(25, (candidate_years / required_years) * 80)

    def score_ats(self, resume_text: str, target_keywords: Optional[List[str]] = None) -> int:
        text = resume_text or ""
        normalized = self.normalize(text)
        score = 45
        if "@" in text:
            score += 8
        if re.search(r"\+?\d[\d\s\-()]{7,}", text):
            score += 6
        if any(section in normalized for section in ["experience", "work history", "employment"]):
            score += 10
        if any(section in normalized for section in ["education", "projects", "skills"]):
            score += 10
        if any(verb in normalized for verb in self.IMPACT_VERBS):
            score += 8
        if re.search(r"\d+%|\$\d+|\d+x|\d+\s*(users|customers|requests)", normalized):
            score += 8
        if target_keywords:
            present = [kw for kw in target_keywords if kw in normalized]
            score += min(15, int((len(present) / max(len(target_keywords), 1)) * 15))
        if len(text) < 500:
            score -= 12
        return int(max(0, min(100, score)))

    def tfidf_similarity(self, text_a: str, text_b: str) -> float:
        if not text_a or not text_b:
            return 0.0
        try:
            matrix = TfidfVectorizer(max_features=1200, ngram_range=(1, 2), stop_words="english").fit_transform(
                [text_a, text_b]
            )
            return float(cosine_similarity(matrix[0], matrix[1])[0][0])
        except Exception:
            return 0.0

    def semantic_similarity(self, text_a: str, text_b: str) -> float:
        model = get_sentence_model()
        if not model or not text_a or not text_b:
            return self.tfidf_similarity(text_a, text_b)
        try:
            vectors = model.encode([text_a[:4000], text_b[:4000]])
            numerator = float(sum(a * b for a, b in zip(vectors[0], vectors[1])))
            denominator = math.sqrt(sum(a * a for a in vectors[0])) * math.sqrt(sum(b * b for b in vectors[1]))
            return numerator / denominator if denominator else 0.0
        except Exception:
            return self.tfidf_similarity(text_a, text_b)

    def estimate_salary(self, job, resume_data: Dict, skill_match: float) -> float:
        minimum = getattr(job, "salary_min", None)
        maximum = getattr(job, "salary_max", None)
        if minimum and maximum:
            base = (minimum + maximum) / 2
        else:
            text_salary = self._salary_from_text(getattr(job, "salary_range", "") or "")
            base = text_salary or 900000
        experience_bonus = min(resume_data.get("experience_years", 0), 10) * 25000
        skill_multiplier = 0.85 + (skill_match / 100 * 0.25)
        return round((base + experience_bonus) * skill_multiplier, 2)

    def generate_improvement_suggestions(self, missing_skills, missing_certs, ats_score, resume_data, job_data) -> List[Dict]:
        suggestions = []
        for skill in missing_skills[:5]:
            suggestions.append({
                "type": "skill",
                "title": f"Learn {skill.title()}",
                "impact": min(25, 8 + len(missing_skills) * 3),
                "message": f"Add a hands-on {skill} project and mention measurable outcomes to improve this match.",
                "example": f"Learn {skill.title()} to increase match by an estimated {min(23, 10 + len(missing_skills) * 2)}%.",
            })
        for cert in missing_certs[:3]:
            suggestions.append({
                "type": "certification",
                "title": f"Add {cert}",
                "impact": 8,
                "message": "This certification appears in the job requirements and can improve recruiter confidence.",
            })
        if ats_score < 75:
            suggestions.append({
                "type": "ats",
                "title": "Improve ATS compatibility",
                "impact": 12,
                "message": "Use standard section headings, add role keywords, and rewrite weak bullets with action verbs plus metrics.",
            })
        if not resume_data.get("experience_years") and job_data.get("experience_years"):
            suggestions.append({
                "type": "experience",
                "title": "Clarify experience years",
                "impact": 10,
                "message": "Mention total relevant experience near the summary so screening systems can detect it.",
            })
        return suggestions[:8]

    def recommend_career_path(self, missing_skills: List[str], match_percentage: float) -> List[Dict]:
        if match_percentage >= 80:
            return [{"role": "Interview-ready candidate", "timeline": "2-4 weeks", "next_step": "Prepare role-specific stories and system design examples."}]
        if {"react", "docker"} & set(missing_skills):
            return [{"role": "Backend Engineer", "timeline": "8 months", "next_step": "Build Dockerized APIs, deploy them, and add React dashboard basics."}]
        return [{"role": "Target-role ready", "timeline": "3-6 months", "next_step": "Close the top skill gaps with one portfolio project per skill."}]

    def keyword_analysis(self, resume_keywords: List[str], job_keywords: List[str]) -> Dict:
        resume_set = set(resume_keywords)
        job_set = set(job_keywords)
        return {
            "matched_keywords": sorted(resume_set & job_set)[:20],
            "missing_keywords": sorted(job_set - resume_set)[:20],
            "keyword_coverage": round((len(resume_set & job_set) / max(len(job_set), 1)) * 100, 1),
        }

    def job_fit_heatmap(self, skill_result: Dict, experience_score: float, ats_score: int, tfidf: float, semantic: float) -> List[Dict]:
        return [
            {"name": "Skills", "score": skill_result["match_percentage"]},
            {"name": "Experience", "score": round(experience_score, 1)},
            {"name": "ATS", "score": ats_score},
            {"name": "Keywords", "score": round(tfidf * 100, 1)},
            {"name": "Semantic Fit", "score": round(semantic * 100, 1)},
        ]

    def canonical_skill(self, value: str) -> str:
        normalized = self.normalize(value)
        for canonical, aliases in self.SKILL_SYNONYMS.items():
            if normalized in aliases:
                return canonical
        return normalized

    def normalize(self, value: str) -> str:
        return re.sub(r"\s+", " ", str(value or "").lower()).strip()

    def _split_skills(self, skills_text: str) -> List[str]:
        return [self.canonical_skill(part) for part in re.split(r"[,;|/\n]", skills_text) if part.strip()]

    def _salary_from_text(self, value: str) -> Optional[float]:
        numbers = [int(num.replace(",", "")) for num in re.findall(r"\d[\d,]{4,}", value or "")]
        if not numbers:
            return None
        return sum(numbers) / len(numbers)
