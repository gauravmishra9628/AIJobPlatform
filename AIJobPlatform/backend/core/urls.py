"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from .views import api_root
from .health import health_check, readiness_check
from jobs import comparison_views

# Swagger schema configuration
swagger_info = openapi.Info(
    title="AI Job Platform API",
    default_version='v1',
    description="AI-powered career platform API for students, recruiters, and professionals",
    contact=openapi.Contact(email="support@aijobplatform.com"),
    license=openapi.License(name="Proprietary"),
)

schema_view = get_schema_view(swagger_info, public=True)

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    # Health checks for K8s/Docker
    path('health/', health_check, name='health-check'),
    path('ready/', readiness_check, name='readiness-check'),
    path('api/auth/', include('accounts.urls')),
    path('api/compare/', comparison_views.compare_api, name='api-compare'),
    path('api/resume/upload/', comparison_views.upload_resume_api, name='api-resume-upload'),
    path('api/ai/match/', comparison_views.ai_match_api, name='api-ai-match'),
    path('api/skill-gap/', comparison_views.skill_gap_api, name='api-skill-gap'),
    path('api/salary-predict/', comparison_views.salary_predict_api, name='api-salary-predict'),
    path('api/jobs/', include('jobs.urls')),
    path('api/companies/', include('jobs.company_urls')),
    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
