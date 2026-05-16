"""
Health Check API Endpoint
Returns system status for monitoring/load balancers
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from django.conf import settings
import os


def health_check(request):
    """
    Health check endpoint for Kubernetes/Docker health probes
    Returns 200 if healthy, 503 if unhealthy
    """
    status = {
        'status': 'healthy',
        'checks': {}
    }
    http_status = 200

    # 1. Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['checks']['database'] = 'ok'
    except Exception as e:
        status['checks']['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
        http_status = 503

    # 2. Redis check
    try:
        if settings.USE_REDIS == "True" or settings.USE_REDIS is True:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                status['checks']['redis'] = 'ok'
            else:
                status['checks']['redis'] = 'degraded'
        else:
            status['checks']['redis'] = 'disabled'
    except Exception as e:
        status['checks']['redis'] = f'error: {str(e)}'

    # 3. Disk space check
    try:
        import shutil
        disk_usage = shutil.disk_usage("/")
        free_percent = (disk_usage.free / disk_usage.total) * 100
        if free_percent > 10:
            status['checks']['disk'] = f'ok ({free_percent:.1f}% free)'
        else:
            status['checks']['disk'] = f'warning ({free_percent:.1f}% free)'
    except Exception:
        pass

    # 4. Memory check
    try:
        import psutil
        memory = psutil.virtual_memory()
        status['checks']['memory'] = f'{memory.percent}% used'
    except ImportError:
        status['checks']['memory'] = 'not available'

    # 5. Environment info
    status['environment'] = os.environ.get('DJANGO_ENV', 'development')
    status['debug'] = settings.DEBUG

    return JsonResponse(status, status=http_status)


def readiness_check(request):
    """
    Readiness check - returns 200 when app is ready to serve traffic
    Used by Kubernetes before routing traffic
    """
    # Check if database is accessible
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({'ready': True})
    except Exception:
        return JsonResponse({'ready': False}, status=503)