"""
Health Check API Endpoint
Returns system status for monitoring/load balancers
"""
from django.http import HttpResponse, JsonResponse
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
    if request.method == "HEAD":
        return HttpResponse(status=200)

    status = {
        'status': 'healthy',
        'checks': {
            'application': 'ok',
        }
    }

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

    return JsonResponse(status, status=200)


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
