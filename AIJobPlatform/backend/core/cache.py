"""
Redis Cache Service for AI Job Platform
Provides caching for expensive operations
"""
from django.core.cache import cache
from django.conf import settings
import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional


class CacheService:
    """Centralized cache service"""

    # Cache key prefixes
    USER_PREFIX = 'user'
    JOB_PREFIX = 'job'
    RESUME_PREFIX = 'resume'
    AI_PREFIX = 'ai'
    SEARCH_PREFIX = 'search'

    # Default TTL (seconds)
    DEFAULT_TTL = 300  # 5 minutes
    SHORT_TTL = 60    # 1 minute
    LONG_TTL = 3600   # 1 hour

    @staticmethod
    def generate_key(*args) -> str:
        """Generate cache key from arguments"""
        key_string = ':'.join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()

    @staticmethod
    def get(key: str, default=None) -> Any:
        """Get value from cache"""
        try:
            value = cache.get(key)
            if value is None:
                return default
            return json.loads(value) if isinstance(value, str) else value
        except Exception:
            return default

    @staticmethod
    def set(key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or CacheService.DEFAULT_TTL
            serialized = json.dumps(value) if not isinstance(value, str) else value
            cache.set(key, serialized, ttl)
            return True
        except Exception:
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache"""
        try:
            cache.delete(key)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            # Django cache doesn't support pattern deletion natively
            # This is a limitation - consider using Redis directly
            return 0
        except Exception:
            return 0

    # === User Cache ===

    @staticmethod
    def get_user_profile(user_id: int) -> Optional[dict]:
        """Get cached user profile"""
        key = f"{CacheService.USER_PREFIX}:profile:{user_id}"
        return CacheService.get(key)

    @staticmethod
    def set_user_profile(user_id: int, data: dict, ttl: int = None):
        """Cache user profile"""
        key = f"{CacheService.USER_PREFIX}:profile:{user_id}"
        return CacheService.set(key, data, ttl or CacheService.SHORT_TTL)

    @staticmethod
    def invalidate_user_profile(user_id: int):
        """Invalidate user profile cache"""
        key = f"{CacheService.USER_PREFIX}:profile:{user_id}"
        return CacheService.delete(key)

    # === Job Cache ===

    @staticmethod
    def get_job_list(page: int, filters: dict) -> Optional[dict]:
        """Get cached job list"""
        key = f"{CacheService.JOB_PREFIX}:list:{page}:{CacheService.generate_key(filters)}"
        return CacheService.get(key)

    @staticmethod
    def set_job_list(page: int, filters: dict, data: dict):
        """Cache job list"""
        key = f"{CacheService.JOB_PREFIX}:list:{page}:{CacheService.generate_key(filters)}"
        return CacheService.set(key, data, CacheService.SHORT_TTL)

    @staticmethod
    def get_job_detail(job_id: int) -> Optional[dict]:
        """Get cached job detail"""
        key = f"{CacheService.JOB_PREFIX}:detail:{job_id}"
        return CacheService.get(key)

    @staticmethod
    def set_job_detail(job_id: int, data: dict):
        """Cache job detail"""
        key = f"{CacheService.JOB_PREFIX}:detail:{job_id}"
        return CacheService.set(key, data, CacheService.LONG_TTL)

    @staticmethod
    def invalidate_job(job_id: int):
        """Invalidate job cache"""
        CacheService.delete(f"{CacheService.JOB_PREFIX}:detail:{job_id}")

    # === AI Cache ===

    @staticmethod
    def get_ai_analysis(resume_id: int, job_id: int = None) -> Optional[dict]:
        """Get cached AI analysis"""
        suffix = f"_{job_id}" if job_id else ""
        key = f"{CacheService.AI_PREFIX}:analysis:{resume_id}{suffix}"
        return CacheService.get(key)

    @staticmethod
    def set_ai_analysis(resume_id: int, data: dict, job_id: int = None):
        """Cache AI analysis"""
        suffix = f"_{job_id}" if job_id else ""
        key = f"{CacheService.AI_PREFIX}:analysis:{resume_id}{suffix}"
        # AI analysis takes longer to compute - cache longer
        return CacheService.set(key, data, CacheService.LONG_TTL * 2)

    # === Search Cache ===

    @staticmethod
    def get_search_results(query: str, filters: dict) -> Optional[dict]:
        """Get cached search results"""
        key = f"{CacheService.SEARCH_PREFIX}:{CacheService.generate_key(query, filters)}"
        return CacheService.get(key)

    @staticmethod
    def set_search_results(query: str, filters: dict, data: dict):
        """Cache search results"""
        key = f"{CacheService.SEARCH_PREFIX}:{CacheService.generate_key(query, filters)}"
        return CacheService.set(key, data, CacheService.SHORT_TTL)


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results

    Usage:
        @cached(ttl=60, key_prefix="user")
        def get_user_data(user_id):
            # Expensive operation
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{CacheService.generate_key(args, kwargs)}"

            # Try to get from cache
            cached_result = CacheService.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheService.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def invalidate_cache(prefix: str, identifier: Any = None):
    """
    Decorator to invalidate cache after function execution

    Usage:
        @invalidate_cache("user", "user_id")
        def update_user_profile(user_id, data):
            # Update profile
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Invalidate related cache
            if identifier:
                # Try to extract identifier from kwargs
                id_value = kwargs.get(identifier) or (args[1] if len(args) > 1 else None)
                if id_value:
                    key = f"{prefix}:{identifier}:{id_value}"
                    CacheService.delete(key)

            return result
        return wrapper
    return decorator