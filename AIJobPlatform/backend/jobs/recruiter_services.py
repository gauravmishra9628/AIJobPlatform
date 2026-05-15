from typing import List, Dict, Optional
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.embeddings.openai import OpenAIEmbeddings
except Exception:
    ChatOpenAI = None
    OpenAIEmbeddings = None

try:
    from supabase import create_client as create_supabase_client
except Exception:
    create_supabase_client = None

from .models import JobApplication, JobPost, Resume


def _split_skills(text: Optional[str]) -> List[str]:
    if not text:
        return []
    return [s.strip().lower() for s in text.split(",") if s.strip()]


class RecruiterAssistant:
    """Small service wrapper for recruiter assistant features.

    This implementation prefers configured AI/Vector services (Supabase + OpenAI)
    but falls back to simple Django ORM filters when not available so it is
    safe to run in development without external creds.
    """

    def __init__(self, cache_ttl: int = 86400):
        self.cache_ttl = cache_ttl

        self.supabase = None
        if getattr(settings, "SUPABASE_URL", None) and getattr(settings, "SUPABASE_KEY", None) and create_supabase_client:
            try:
                self.supabase = create_supabase_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            except Exception:
                self.supabase = None

        self.embeddings = None
        if OpenAIEmbeddings is not None and getattr(settings, "OPENAI_API_KEY", None):
            try:
                self.embeddings = OpenAIEmbeddings()
            except Exception:
                self.embeddings = None

        self.llm = None
        if ChatOpenAI is not None and getattr(settings, "OPENAI_API_KEY", None):
            try:
                self.llm = ChatOpenAI(model=getattr(settings, "AI_LLM_MODEL", "gpt-4"), temperature=0.0)
            except Exception:
                self.llm = None

    def parse_query(self, query_text: str) -> dict:
        """Return a small intent dict: {intent, filters, sort_by, limit}.

        Uses LLM when available, otherwise simple heuristics.
        """
        if not query_text:
            return {"intent": "unknown", "filters": {}, "sort_by": "score", "limit": 20}

        # Heuristic defaults
        q = query_text.lower()
        intent = "search"
        filters = {}
        if "shortlist" in q or "auto-shortlist" in q:
            intent = "shortlist"
        if "ats" in q:
            filters["ats_top"] = True
        if "remote" in q:
            filters["remote"] = True

        # lightweight skill tokens extraction
        skills = []
        for part in ["react", "django", "python", "aws", "docker", "sql", "node", "javascript"]:
            if part in q:
                skills.append(part)
        if skills:
            filters["skills"] = skills

        # Use LLM to return a JSON {intent, filters, sort_by, limit} when available
        if self.llm:
            try:
                prompt = (
                    "You are a classifier. Given a recruiter's natural-language query, "
                    "return a JSON object with keys: intent (one of 'search'|'shortlist'|'analytics'), "
                    "filters (simple dict like {\"skills\": [..], \"remote\": True}), sort_by (string), and limit (int).\n\n"
                    f"Query: {query_text}\n\nRespond only with valid JSON."
                )
                raw = self.llm.predict(prompt)
                import json
                parsed = json.loads(raw)
                # Merge safely
                intent = parsed.get("intent", intent)
                parsed_filters = parsed.get("filters") or {}
                filters.update(parsed_filters)
                sort_by = parsed.get("sort_by", "relevance")
                limit = int(parsed.get("limit", 20))
                return {"intent": intent, "filters": filters, "sort_by": sort_by, "limit": limit}
            except Exception:
                # ignore LLM errors and fall back to heuristics
                pass

        return {"intent": intent, "filters": filters, "sort_by": "relevance", "limit": 20}

    def search_candidates(self, filters: dict) -> List[Dict]:
        """Search candidates using vector search when configured, otherwise ORM fallback.

        Expected filters: skills (list), remote (bool), ats_top (bool), job_id, limit
        """
        cache_key = f"recruiter_search:{hash(frozenset((filters or {}).items()))}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        limit = int(filters.get("limit", 20))
        skills = [s.lower() for s in filters.get("skills", [])]

        results = []

        # Prefer Supabase vector search when available and embeddings present
        if self.supabase and self.embeddings:
            try:
                # Build a textual query from filters if skills present, else use job_id
                query_text = " ".join(skills) if skills else filters.get("job_text") or ""
                emb = None
                if hasattr(self.embeddings, "embed_query"):
                    try:
                        emb = self.embeddings.embed_query(query_text)
                    except Exception:
                        emb = None
                elif hasattr(self.embeddings, "embed_documents"):
                    try:
                        emb = self.embeddings.embed_documents([query_text])[0]
                    except Exception:
                        emb = None

                if emb is not None:
                    # Try RPC match function if configured
                    try:
                        resp = self.supabase.rpc("match_resumes", {"query_embedding": emb, "match_count": limit}).execute()
                        rows = resp.data or []
                        for row in rows:
                            results.append({
                                "candidate_id": row.get("application_id") or row.get("id"),
                                "applicant_email": row.get("applicant_email"),
                                "score": row.get("score", 0),
                            })
                        cache.set(cache_key, results, self.cache_ttl)
                        return results
                    except Exception:
                        # Fall back to table search if RPC not available
                        try:
                            # Assume a 'resumes' table with 'embedding' column and application join
                            table = self.supabase.table("resumes")
                            # This is provider-specific; if it fails, we fallback to ORM below
                            resp = table.select("id, user_email, application_id, score").execute()
                            rows = resp.data or []
                            for row in rows[:limit]:
                                results.append({
                                    "candidate_id": row.get("application_id") or row.get("id"),
                                    "applicant_email": row.get("user_email"),
                                    "score": row.get("score", 0),
                                })
                            cache.set(cache_key, results, self.cache_ttl)
                            return results
                        except Exception:
                            pass
            except Exception:
                # fall through to ORM
                pass

        # ORM fallback: simple skills substring match on resume.extracted_skills or resume.extracted_text
        qs = JobApplication.objects.select_related("applicant", "resume").all()
        if skills:
            q_filters = Q()
            for s in skills:
                q_filters |= Q(resume__extracted_skills__icontains=s) | Q(resume__extracted_text__icontains=s)
            qs = qs.filter(q_filters)

        if filters.get("job_id"):
            qs = qs.filter(job__id=filters.get("job_id"))

        if filters.get("ats_top"):
            qs = qs.order_by("-match_score")
        else:
            qs = qs.order_by("-match_score")

        qs = qs[:limit]
        for app in qs:
            results.append({
                "candidate_id": app.id,
                "applicant_email": app.applicant.email,
                "score": float(getattr(app, "match_score", 0)),
            })

        cache.set(cache_key, results, self.cache_ttl)
        return results

    def auto_shortlist(self, job_id: int, count: int = 10) -> List[int]:
        """Return top candidate application ids for given job_id."""
        try:
            job = JobPost.objects.get(id=job_id)
        except JobPost.DoesNotExist:
            return []

        # Build filters from job
        skills = _split_skills(job.skills_required)
        filters = {"skills": skills, "job_id": job_id, "limit": count}
        results = self.search_candidates(filters)
        return [r.get("candidate_id") for r in results][:count]
