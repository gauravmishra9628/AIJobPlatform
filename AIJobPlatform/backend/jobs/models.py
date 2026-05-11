from django.conf import settings
from django.db import models


class JobPost(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "full-time", "Full-time"
        PART_TIME = "part-time", "Part-time"
        INTERNSHIP = "internship", "Internship"
        CONTRACT = "contract", "Contract"

    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posted_jobs",
    )
    title = models.CharField(max_length=180)
    company = models.CharField(max_length=180)
    location = models.CharField(max_length=180)
    description = models.TextField()
    skills_required = models.TextField(blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    salary_range = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} at {self.company}"


class Resume(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    file = models.FileField(upload_to="resumes/")
    original_name = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)
    extracted_skills = models.JSONField(default=list, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.user.email} - {self.original_name}"


class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        REVIEWING = "reviewing", "Reviewing"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"

    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, blank=True, null=True)
    cover_note = models.TextField(blank=True)
    match_score = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["job", "applicant"], name="unique_job_application"),
        ]

    def __str__(self):
        return f"{self.applicant.email} -> {self.job.title}"


class NetworkMessage(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_network_messages",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_network_messages",
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.email} to {self.recipient.email}"


# ATS Scoring Feature
class ResumeAtsScore(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name="ats_score")
    job = models.ForeignKey(JobPost, on_delete=models.SET_NULL, null=True, blank=True)
    overall_score = models.PositiveIntegerField(default=0)  # 0-100
    keyword_match_score = models.PositiveIntegerField(default=0)
    skills_match_score = models.PositiveIntegerField(default=0)
    experience_score = models.PositiveIntegerField(default=0)
    format_score = models.PositiveIntegerField(default=0)
    missing_keywords = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    improvement_suggestions = models.JSONField(default=list, blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ATS Score for {self.resume} - {self.overall_score}"


# Job Bookmark Feature
class JobBookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_bookmarks",
    )
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="bookmarks")
    bookmarked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ["user", "job"]
        ordering = ["-bookmarked_at"]

    def __str__(self):
        return f"{self.user.email} bookmarked {self.job.title}"


# Application Tracking Enhancement
class ApplicationStageLog(models.Model):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="stage_logs",
    )
    from_stage = models.CharField(max_length=20, blank=True)
    to_stage = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="stage_changes_made",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.application} - {self.to_stage}"


# Skill Gap Analysis
class SkillGapAnalysis(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_gap_analysis",
    )
    current_skills = models.JSONField(default=list, blank=True)
    target_role = models.CharField(max_length=180, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    learning_paths = models.JSONField(default=list, blank=True)  # Recommended courses/resources
    proficiency_levels = models.JSONField(default=dict, blank=True)  # {skill: level}
    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Skill Gap for {self.user.email}"


# Real-Time Notifications
class Notification(models.Model):
    class NotificationType(models.TextChoices):
        APPLICATION = "application", "Application"
        MESSAGE = "message", "Message"
        INTERVIEW = "interview", "Interview"
        JOB_MATCH = "job_match", "Job Match"
        PROFILE_UPDATE = "profile_update", "Profile Update"
        SKILL_RECOMMENDATION = "skill_rec", "Skill Recommendation"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_application = models.ForeignKey(
        JobApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    related_job = models.ForeignKey(
        JobPost,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} for {self.user.email}"


# Interview Preparation
class InterviewPreparation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_preps",
    )
    job_application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="interview_preps",
    )
    role = models.CharField(max_length=180)
    generated_questions = models.JSONField(default=list, blank=True)
    coding_problems = models.JSONField(default=list, blank=True)
    tips_and_tricks = models.JSONField(default=list, blank=True)
    preparation_resources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Interview prep for {self.user.email} - {self.role}"


# Analytics Data for Recruiters
class RecruiterAnalytics(models.Model):
    recruiter = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter_analytics",
    )
    total_jobs_posted = models.PositiveIntegerField(default=0)
    total_applications = models.PositiveIntegerField(default=0)
    total_hired = models.PositiveIntegerField(default=0)
    average_time_to_hire = models.PositiveIntegerField(default=0)  # in days
    engagement_rate = models.FloatField(default=0)  # percentage
    top_performing_jobs = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.recruiter.email}"


# ========== NEW AI FEATURES ==========

# AI Resume Analyzer
class AIResumeAnalysis(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name="ai_analysis")
    overall_rating = models.PositiveIntegerField(default=0)  # 0-100
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    detailed_feedback = models.TextField(blank=True)
    readability_score = models.PositiveIntegerField(default=0)
    impact_score = models.PositiveIntegerField(default=0)
    recommendations = models.JSONField(default=list, blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AI Analysis for {self.resume}"


# AI Match Scoring
class AIMatchScore(models.Model):
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="ai_matches")
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="ai_matches")
    match_percentage = models.PositiveIntegerField(default=0)  # 0-100
    skills_alignment = models.PositiveIntegerField(default=0)
    experience_alignment = models.PositiveIntegerField(default=0)
    culture_fit = models.PositiveIntegerField(default=0)
    growth_potential = models.PositiveIntegerField(default=0)
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    bonus_skills = models.JSONField(default=list, blank=True)
    match_reasons = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["job", "resume"]
        ordering = ["-match_percentage"]

    def __str__(self):
        return f"Match: {self.resume} - {self.job} ({self.match_percentage}%)"


# AI Career Coach
class AICareerCoach(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="career_coach",
    )
    career_goals = models.TextField(blank=True)
    current_level = models.CharField(max_length=50, blank=True)  # junior, mid, senior, lead
    target_level = models.CharField(max_length=50, blank=True)
    recommended_roles = models.JSONField(default=list, blank=True)
    skill_development_plan = models.JSONField(default=list, blank=True)
    career_milestones = models.JSONField(default=list, blank=True)
    personalized_advice = models.TextField(blank=True)
    job_recommendations = models.JSONField(default=list, blank=True)
    salary_insights = models.JSONField(default=dict, blank=True)  # {role: range}
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Career Coach for {self.user.email}"


# Real Chat/Messaging
class ChatMessage(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_chat_messages",
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["sender", "recipient"]),
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"Chat: {self.sender.email} → {self.recipient.email}"


# Enhanced Recruiter Dashboard
class RecruiterDashboard(models.Model):
    recruiter = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard",
    )
    favorite_jobs = models.JSONField(default=list, blank=True)  # List of job IDs
    saved_candidates = models.JSONField(default=list, blank=True)  # List of user IDs
    pipeline_stages = models.JSONField(default=dict, blank=True)  # Custom pipeline
    hiring_goals = models.JSONField(default=dict, blank=True)  # Goals and progress
    interview_schedule = models.JSONField(default=list, blank=True)
    team_members = models.JSONField(default=list, blank=True)
    notifications_settings = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dashboard for {self.recruiter.email}"


# External Job API Integration
class ExternalJobListing(models.Model):
    class APISource(models.TextChoices):
        JSEARCH = "jsearch", "JSearch API"
        ADZUNA = "adzuna", "Adzuna API"
        REMOTIVE = "remotive", "Remotive API"

    external_id = models.CharField(max_length=255, unique=True)
    source = models.CharField(max_length=20, choices=APISource.choices)
    title = models.CharField(max_length=180)
    company = models.CharField(max_length=180)
    location = models.CharField(max_length=180)
    description = models.TextField()
    skills_required = models.JSONField(default=list, blank=True)
    employment_type = models.CharField(max_length=50, blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    job_url = models.URLField()
    is_remote = models.BooleanField(default=False)
    is_internship = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} at {self.company} (from {self.source})"




# Resume Template for PDF Generation
class ResumeTemplate(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resume_template",
    )
    full_name = models.CharField(max_length=180)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=180, blank=True)
    professional_summary = models.TextField(blank=True)
    experience = models.JSONField(
        default=list,
        blank=True,
        help_text="List of {title, company, duration, description}",
    )
    education = models.JSONField(
        default=list,
        blank=True,
        help_text="List of {degree, field, institution, year}",
    )
    skills = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    projects = models.JSONField(
        default=list,
        blank=True,
        help_text="List of {name, description, link, skills_used}",
    )
    template_style = models.CharField(
        max_length=50,
        default="modern",
        choices=[
            ("modern", "Modern"),
            ("classic", "Classic"),
            ("creative", "Creative"),
        ],
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Resume Template for {self.user.email}"


# OTP Verification for Authentication
class OTPVerification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otp_verifications",
    )
    otp = models.CharField(max_length=6)
    email = models.EmailField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.email}"


# Password Reset Token
class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=255, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Reset Token for {self.user.email}"

