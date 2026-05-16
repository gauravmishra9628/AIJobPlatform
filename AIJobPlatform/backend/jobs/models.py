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
    requirements = models.JSONField(default=dict, blank=True)
    required_experience_years = models.PositiveIntegerField(default=0)
    required_education = models.CharField(max_length=180, blank=True)
    required_certifications = models.JSONField(default=list, blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    salary_range = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
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
    parsed_skills = models.JSONField(default=list, blank=True)
    experience_years = models.FloatField(default=0)
    education = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    ats_score = models.PositiveIntegerField(default=0)
    ai_suggestions = models.JSONField(default=list, blank=True)
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
    candidate_summary = models.TextField(blank=True)
    portfolio_url = models.URLField(blank=True)
    expected_salary = models.CharField(max_length=80, blank=True)
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
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name="ats_score_detail")
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


class SkillMapping(models.Model):
    skill_name = models.CharField(max_length=100, unique=True)
    skill_category = models.CharField(max_length=50, blank=True)
    synonyms = models.JSONField(default=list, blank=True)
    proficiency_levels = models.JSONField(default=list, blank=True)
    market_weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["skill_category", "skill_name"]

    def __str__(self):
        return self.skill_name


class ResumeJobComparison(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="comparisons")
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="resume_comparisons")
    match_percentage = models.FloatField(default=0)
    semantic_similarity = models.FloatField(default=0)
    tfidf_similarity = models.FloatField(default=0)
    skill_match = models.JSONField(default=dict, blank=True)
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    missing_certifications = models.JSONField(default=list, blank=True)
    experience_score = models.FloatField(default=0)
    ats_score = models.PositiveIntegerField(default=0)
    salary_prediction = models.FloatField(default=0)
    improvement_suggestions = models.JSONField(default=list, blank=True)
    career_recommendations = models.JSONField(default=list, blank=True)
    keyword_analysis = models.JSONField(default=dict, blank=True)
    heatmap = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("queued", "Queued"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")],
        default="completed",
    )
    error_message = models.TextField(blank=True)
    comparison_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["resume", "job"]
        ordering = ["-comparison_date"]
        indexes = [
            models.Index(fields=["resume", "-match_percentage"]),
            models.Index(fields=["job", "-match_percentage"]),
            models.Index(fields=["status", "-comparison_date"]),
        ]

    def __str__(self):
        return f"{self.resume.original_name} vs {self.job.title} ({self.match_percentage:.1f}%)"


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


class SkillVerificationBadge(models.Model):
    class BadgeTier(models.TextChoices):
        GOLD = "gold", "Gold"
        SILVER = "silver", "Silver"
        BRONZE = "bronze", "Bronze"

    class BadgeSource(models.TextChoices):
        TEST = "test", "Mini Test"
        CERTIFICATE = "certificate", "Certificate"
        GITHUB = "github", "GitHub"
        PORTFOLIO = "portfolio", "Portfolio"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_badges",
    )
    skill_name = models.CharField(max_length=120)
    badge_tier = models.CharField(max_length=20, choices=BadgeTier.choices)
    source = models.CharField(max_length=20, choices=BadgeSource.choices, default=BadgeSource.TEST)
    score = models.PositiveIntegerField(default=0)
    evidence_url = models.URLField(blank=True)
    note = models.CharField(max_length=255, blank=True)
    verified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-verified_at"]


# Recruiter query logging and results for AI assistant
class RecruiterQuery(models.Model):
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recruiter_queries"
    )
    query = models.TextField()
    query_type = models.CharField(max_length=50, blank=True)  # resume_search, skill_match, shortlist, etc.
    results_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Query by {self.recruiter.email} @ {self.created_at:%Y-%m-%d %H:%M}"


class QueryResult(models.Model):
    query = models.ForeignKey(RecruiterQuery, on_delete=models.CASCADE, related_name="results")
    candidate = models.ForeignKey(JobApplication, on_delete=models.CASCADE)
    relevance_score = models.FloatField(default=0.0)
    reasoning = models.TextField(blank=True)

    class Meta:
        unique_together = ["query", "candidate"]

    def __str__(self):
        return f"Result: {self.candidate} (score={self.relevance_score:.2f})"


class AutoApplyRun(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auto_apply_runs",
    )
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True)
    threshold = models.PositiveIntegerField(default=80)
    applied_jobs = models.JSONField(default=list, blank=True)
    skipped_jobs = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Auto-apply run for {self.user.email}"


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
        GOOGLE_JOBS = "google_jobs", "Google Jobs"
        LINKEDIN = "linkedin", "LinkedIn-style Jobs"

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


class CompanyProfile(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    industry = models.CharField(max_length=120, blank=True)
    employee_count = models.CharField(max_length=80, blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    location = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    website = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    recruiter_name = models.CharField(max_length=180, blank=True)
    verified_recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_company_profiles",
    )
    active_positions = models.PositiveIntegerField(default=0)
    hiring_urgency = models.CharField(max_length=20, default="medium")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CompanyReview(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_reviews",
    )
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=180)
    body = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    is_verified_employee = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company.name} review by {self.reviewer.email}"




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


class SubscriptionPlan(models.Model):
    class PlanCode(models.TextChoices):
        FREE = "free", "Free"
        PREMIUM = "premium", "Premium"
        RECRUITER = "recruiter", "Recruiter"

    code = models.CharField(max_length=30, choices=PlanCode.choices, unique=True)
    name = models.CharField(max_length=80)
    monthly_price_inr = models.PositiveIntegerField(default=0)
    monthly_price_usd = models.PositiveIntegerField(default=0)
    resume_credits = models.PositiveIntegerField(default=3)
    ai_usage_limit = models.PositiveIntegerField(default=10)
    job_post_limit = models.PositiveIntegerField(default=0)
    features = models.JSONField(default=list, blank=True)
    stripe_price_id = models.CharField(max_length=120, blank=True)
    razorpay_plan_id = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["monthly_price_inr", "name"]

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        TRIALING = "trialing", "Trialing"
        PAST_DUE = "past_due", "Past due"
        CANCELED = "canceled", "Canceled"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    provider = models.CharField(max_length=20, blank=True)
    provider_customer_id = models.CharField(max_length=150, blank=True)
    provider_subscription_id = models.CharField(max_length=150, blank=True)
    resume_credits_remaining = models.PositiveIntegerField(default=3)
    ai_usage_count = models.PositiveIntegerField(default=0)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.code}"


class UsageLedger(models.Model):
    class UsageType(models.TextChoices):
        AI = "ai", "AI"
        RESUME_CREDIT = "resume_credit", "Resume credit"
        JOB_POST = "job_post", "Job post"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage_ledger")
    usage_type = models.CharField(max_length=30, choices=UsageType.choices)
    amount = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "usage_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} {self.usage_type} x{self.amount}"


# ========== AI RESUME MATCH SCORE FEATURE ==========

class ResumeJobMatch(models.Model):
    """
    Stores detailed resume-to-job matching analysis
    Using AI and NLP for intelligent skill matching
    """
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="job_matches")
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="resume_matches")
    
    # Match scores
    match_percentage = models.FloatField(default=0.0)  # 0-100
    required_skills_match = models.FloatField(default=0.0)  # % of required skills matched
    nice_to_have_match = models.FloatField(default=0.0)  # % of nice-to-have skills matched
    experience_multiplier = models.FloatField(default=1.0)  # Experience adjustment factor
    
    # Skill analysis
    matched_skills = models.JSONField(default=list, blank=True)  # Skills in both resume & job
    missing_skills_required = models.JSONField(default=list, blank=True)  # Critical gaps
    missing_skills_nice = models.JSONField(default=list, blank=True)  # Optional gaps
    extracted_resume_skills = models.JSONField(default=list, blank=True)  # All skills found in resume
    extracted_job_skills = models.JSONField(default=list, blank=True)  # All skills required by job
    
    # Experience analysis
    candidate_experience_years = models.PositiveIntegerField(default=0)
    required_experience_level = models.CharField(
        max_length=20,
        choices=[("junior", "Junior"), ("mid", "Mid-level"), ("senior", "Senior")],
        default="mid"
    )
    experience_gap = models.IntegerField(default=0)  # Positive = excess, Negative = shortage
    
    # Match breakdown
    match_breakdown = models.JSONField(default=dict, blank=True)  # {required_match, nice_to_have_match, experience_multiplier}
    
    # Improvement suggestions
    improvement_suggestions = models.JSONField(default=list, blank=True)  # [{skill, importance, learning_time_weeks, resources}]
    
    # Metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ["resume", "job"]
        ordering = ["-match_percentage", "-analyzed_at"]
        indexes = [
            models.Index(fields=["resume", "-match_percentage"]),
            models.Index(fields=["job", "-match_percentage"]),
            models.Index(fields=["-analyzed_at"]),
        ]

    def __str__(self):
        return f"Match: {self.resume.original_name} vs {self.job.title} ({self.match_percentage:.1f}%)"


# ========== SMART CAREER GRAPH MODELS ==========

class SkillNode(models.Model):
    class LevelChoices(models.TextChoices):
        BEGINNER = "1", "Beginner"
        INTERMEDIATE = "2", "Intermediate"
        EXPERT = "3", "Expert"

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50)  # "Backend", "Frontend", "ML", "Data", "DevOps"
    level = models.PositiveSmallIntegerField(choices=LevelChoices.choices, default=1)
    description = models.TextField(blank=True)
    market_demand = models.FloatField(default=1.0)  # 0.0 - 2.0 scale
    avg_salary = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.category})"


class SkillEdge(models.Model):
    """Prerequisite relationships between skills"""
    from_skill = models.ForeignKey(SkillNode, on_delete=models.CASCADE, related_name="prerequisites_for")
    to_skill = models.ForeignKey(SkillNode, on_delete=models.CASCADE, related_name="required_by")
    difficulty_jump = models.FloatField(default=0.5)  # 0.0 - 1.0
    typical_weeks = models.PositiveIntegerField(default=4)  # Estimated learning time
    is_critical = models.BooleanField(default=False)  # Critical path skill

    class Meta:
        unique_together = ["from_skill", "to_skill"]
        ordering = ["typical_weeks"]

    def __str__(self):
        return f"{self.from_skill.name} → {self.to_skill.name}"


class UserSkillProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_progress",
    )
    skill = models.ForeignKey(SkillNode, on_delete=models.CASCADE, related_name="user_progress")
    current_level = models.PositiveSmallIntegerField(default=1)  # 1-3
    target_level = models.PositiveSmallIntegerField(default=2)
    started_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    progress_percentage = models.FloatField(default=0.0)  # 0-100
    learning_resources = models.JSONField(default=list, blank=True)  # [{title, url, type}]
    milestones_completed = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ["user", "skill"]
        ordering = ["-progress_percentage"]

    def __str__(self):
        return f"{self.user.email} - {self.skill.name} ({self.progress_percentage}%)"


class CareerPathModel(models.Model):
    name = models.CharField(max_length=100, unique=True)  # "Senior React Developer", "ML Engineer"
    description = models.TextField(blank=True)
    required_skills = models.ManyToManyField(SkillNode, related_name="career_paths")
    optional_skills = models.ManyToManyField(SkillNode, related_name="optional_in_paths", blank=True)
    typical_years_experience = models.PositiveIntegerField(default=3)
    average_salary_min = models.PositiveIntegerField(default=0)
    average_salary_max = models.PositiveIntegerField(default=0)
    market_demand_score = models.FloatField(default=1.0)
    growth_trajectory = models.CharField(max_length=50, blank=True)  # "fast", "stable", "slow"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-market_demand_score", "name"]

    def __str__(self):
        return self.name


# Add skill_progress field to User model reference for easier access
class UserCareerPath(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_career_paths",
    )
    career_path = models.ForeignKey(CareerPathModel, on_delete=models.CASCADE, related_name="users")
    target_completion_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user.email} → {self.career_path.name}"


class PaymentTransaction(models.Model):
    class Provider(models.TextChoices):
        STRIPE = "stripe", "Stripe"
        RAZORPAY = "razorpay", "Razorpay"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_transactions")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="payment_transactions")
    provider = models.CharField(max_length=20, choices=Provider.choices)
    provider_reference = models.CharField(max_length=180, blank=True)
    amount = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default="INR")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider} {self.plan.code} {self.status}"


# ========== AI CODING TEST PLATFORM (Feature 4) ==========

class CodingQuestion(models.Model):
    class DifficultyChoices(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DifficultyChoices.choices, default=DifficultyChoices.MEDIUM)
    topics = models.JSONField(default=list, blank=True)
    test_cases = models.JSONField(default=list, blank=True)
    starter_code = models.JSONField(default=dict, blank=True)
    solution = models.JSONField(default=dict, blank=True)
    similar_problems = models.JSONField(default=list, blank=True)
    acceptance_rate = models.FloatField(default=0.0)
    likes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-likes", "difficulty"]

    def __str__(self):
        return f"{self.title} ({self.difficulty})"


class CodeSubmission(models.Model):
    class StatusChoices(models.TextChoices):
        ACCEPTED = "accepted", "Accepted"
        WRONG_ANSWER = "wrong", "Wrong Answer"
        TIME_LIMIT = "tle", "Time Limit Exceeded"
        RUNTIME_ERROR = "error", "Runtime Error"
        PENDING = "pending", "Pending"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="code_submissions")
    question = models.ForeignKey(CodingQuestion, on_delete=models.CASCADE, related_name="submissions")
    language = models.CharField(max_length=20, default="python")
    code = models.TextField()
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    runtime_ms = models.IntegerField(default=0)
    memory_mb = models.IntegerField(default=0)
    plagiarism_score = models.FloatField(null=True, blank=True)
    test_cases_passed = models.PositiveIntegerField(default=0)
    total_test_cases = models.PositiveIntegerField(default=0)
    submission_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submission_date"]

    def __str__(self):
        return f"{self.user.email} - {self.question.title} ({self.status})"


class CodingContest(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    questions = models.ManyToManyField(CodingQuestion, related_name="contests")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    max_participants = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return self.title


class ContestParticipant(models.Model):
    contest = models.ForeignKey(CodingContest, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contest_participations")
    score = models.PositiveIntegerField(default=0)
    questions_solved = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["contest", "user"]
        ordering = ["rank"]

    def __str__(self):
        return f"{self.user.email} in {self.contest.title} (#{self.rank})"


# ========== VOICE-BASED CAREER COACH (Feature 5) ==========

class VoiceSession(models.Model):
    class SessionTypeChoices(models.TextChoices):
        ADVICE = "advice", "Career Advice"
        INTERVIEW = "interview", "Interview Practice"
        SKILL = "skill", "Skill Guidance"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="voice_sessions")
    session_type = models.CharField(max_length=20, choices=SessionTypeChoices.choices, default=SessionTypeChoices.ADVICE)
    start_time = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.IntegerField(default=0)
    transcript = models.TextField(blank=True)
    ai_response = models.TextField(blank=True)
    mood_detected = models.CharField(max_length=20, blank=True)
    key_insights = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.user.email} - {self.session_type} @ {self.start_time}"


class InterviewPracticeSession(models.Model):
    voice_session = models.ForeignKey(VoiceSession, on_delete=models.CASCADE, related_name="interview_practice")
    position = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    questions = models.JSONField(default=list, blank=True)
    answers = models.JSONField(default=list, blank=True)
    scores = models.JSONField(default=dict, blank=True)
    overall_score = models.FloatField(default=0.0)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ["-voice_session__start_time"]

    def __str__(self):
        return f"Interview practice for {self.position} at {self.company}"


# ========== REALTIME COLLABORATION DASHBOARD (Feature 6) ==========

class CollaborativeReview(models.Model):
    class RatingChoices(models.IntegerChoices):
        STRONG_REJECT = 1, "Strong Reject"
        WEAK_REJECT = 2, "Weak Reject"
        MAYBE = 3, "Maybe"
        STRONG_ACCEPT = 4, "Strong Accept"

    candidate = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name="collaborative_reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_given")
    team_id = models.PositiveIntegerField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(choices=RatingChoices.choices, default=3)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.candidate}"


class ReviewComment(models.Model):
    review = models.ForeignKey(CollaborativeReview, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_comments")
    content = models.TextField()
    mentions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.email} on review {self.review.id}"


class InterviewSession(models.Model):
    class StatusChoices(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="interview_sessions")
    interviewers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="interviews_conducted")
    scheduled_start = models.DateTimeField()
    video_room_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.SCHEDULED)
    recording_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_start"]

    def __str__(self):
        return f"Interview with {self.candidate.email}"


class InterviewNotes(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name="notes")
    content = models.TextField()
    version = models.PositiveIntegerField(default=1)
    last_modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version"]

    def __str__(self):
        return f"Notes for session {self.session.id} (v{self.version})"


# ========== AI PERSONALITY ANALYZER (Feature 7) ==========

class PersonalityProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="personality_profile")

    openness = models.FloatField(default=50.0)
    conscientiousness = models.FloatField(default=50.0)
    extraversion = models.FloatField(default=50.0)
    agreeableness = models.FloatField(default=50.0)
    neuroticism = models.FloatField(default=50.0)

    communication = models.FloatField(default=50.0)
    leadership = models.FloatField(default=50.0)
    teamwork = models.FloatField(default=50.0)
    problem_solving = models.FloatField(default=50.0)
    adaptability = models.FloatField(default=50.0)

    mbti_type = models.CharField(max_length=4, default="INTJ")
    team_fit_score = models.FloatField(default=50.0)
    confidence_level = models.FloatField(default=50.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Personality: {self.user.email} ({self.mbti_type})"


class PersonalityInsight(models.Model):
    profile = models.ForeignKey(PersonalityProfile, on_delete=models.CASCADE, related_name="insights")
    trait = models.CharField(max_length=50)
    description = models.TextField()
    recommendation = models.TextField()
    evidence = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile.user.email} - {self.trait}"


# ========== GAMIFICATION SYSTEM (Feature 8) ==========

class UserGameProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="game_profile")
    total_xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-total_xp"]

    def __str__(self):
        return f"{self.user.email} - Lv.{self.level} ({self.total_xp} XP)"


class XPTransaction(models.Model):
    class ActivityTypeChoices(models.TextChoices):
        JOB_APPLY = "job_apply", "Job Application"
        PROFILE_COMPLETE = "profile_complete", "Complete Profile"
        SKILL_VERIFIED = "skill_verified", "Skill Verified"
        DSA_SOLVED = "dsa_solved", "DSA Problem Solved"
        INTERVIEW_PREP = "interview_prep", "Interview Practice"
        PORTFOLIO_UPDATE = "portfolio_update", "Portfolio Update"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="xp_transactions")
    activity_type = models.CharField(max_length=20, choices=ActivityTypeChoices.choices)
    xp_earned = models.PositiveIntegerField()
    multiplier = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} +{self.xp_earned} XP ({self.activity_type})"


class Badge(models.Model):
    class CategoryChoices(models.TextChoices):
        SKILL = "skill", "Skill"
        ACHIEVEMENT = "achievement", "Achievement"
        MILESTONE = "milestone", "Milestone"

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon_url = models.URLField(blank=True)
    required_xp = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=20, choices=CategoryChoices.choices, default=CategoryChoices.ACHIEVEMENT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["required_xp"]

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="earners")
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "badge"]

    def __str__(self):
        return f"{self.user.email} earned {self.badge.name}"


class DailyChallenge(models.Model):
    class DifficultyChoices(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    title = models.CharField(max_length=200)
    description = models.TextField()
    objective = models.CharField(max_length=500)
    xp_reward = models.PositiveIntegerField(default=10)
    date = models.DateField()
    difficulty = models.CharField(max_length=10, choices=DifficultyChoices.choices, default=DifficultyChoices.EASY)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} ({self.date})"


class UserChallenge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenges")
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE, related_name="participants")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["user", "challenge"]

    def __str__(self):
        return f"{self.user.email} - {self.challenge.title}"


# ========== AI AUTO APPLY SYSTEM (Feature 10) ==========

class AutoApplyPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auto_apply_prefs")
    enabled = models.BooleanField(default=False)

    target_roles = models.JSONField(default=list, blank=True)
    preferred_companies = models.JSONField(default=list, blank=True)
    min_salary = models.PositiveIntegerField(default=0)
    max_salary = models.PositiveIntegerField(default=0)
    preferred_locations = models.JSONField(default=list, blank=True)
    work_type_preferences = models.JSONField(default=list, blank=True)
    skill_requirements = models.JSONField(default=list, blank=True)

    max_applications_per_day = models.PositiveIntegerField(default=5)
    min_match_score = models.FloatField(default=0.7)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Auto-apply prefs for {self.user.email} ({self.enabled})"


class AutoApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="auto_applications")
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="auto_applications")
    match_score = models.FloatField(default=0.0)
    auto_filled_fields = models.JSONField(default=dict, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.user.email} auto-applied to {self.job.title}"
