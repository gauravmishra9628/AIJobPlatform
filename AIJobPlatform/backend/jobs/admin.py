from django.contrib import admin

from .models import JobApplication, JobPost, NetworkMessage, Resume


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "posted_by", "is_active", "created_at")
    list_filter = ("employment_type", "is_active", "created_at")
    search_fields = ("title", "company", "location", "skills_required")


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("original_name", "user", "uploaded_at")
    search_fields = ("original_name", "user__email", "extracted_text")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "match_score", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("job__title", "applicant__email")


@admin.register(NetworkMessage)
class NetworkMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
