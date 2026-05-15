from django.urls import path

from . import company_views

app_name = "companies"

urlpatterns = [
    path("", company_views.list_companies, name="company-list"),
    path("<int:company_id>/", company_views.company_detail, name="company-detail"),
    path("<int:company_id>/reviews/", company_views.company_reviews, name="company-reviews"),
    path("<int:company_id>/badge/", company_views.company_badge, name="company-badge"),
]