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

from .views import api_root
from jobs import comparison_views

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/compare/', comparison_views.compare_api, name='api-compare'),
    path('api/resume/upload/', comparison_views.upload_resume_api, name='api-resume-upload'),
    path('api/ai/match/', comparison_views.ai_match_api, name='api-ai-match'),
    path('api/skill-gap/', comparison_views.skill_gap_api, name='api-skill-gap'),
    path('api/salary-predict/', comparison_views.salary_predict_api, name='api-salary-predict'),
    path('api/jobs/', include('jobs.urls')),
    path('api/companies/', include('jobs.company_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
