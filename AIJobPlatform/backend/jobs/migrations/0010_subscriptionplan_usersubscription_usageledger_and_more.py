from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_subscription_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("jobs", "SubscriptionPlan")
    plans = [
        {
            "code": "free",
            "name": "Free",
            "monthly_price_inr": 0,
            "monthly_price_usd": 0,
            "resume_credits": 3,
            "ai_usage_limit": 10,
            "job_post_limit": 1,
            "features": ["Basic profile", "3 resume credits", "10 AI actions"],
        },
        {
            "code": "premium",
            "name": "Premium",
            "monthly_price_inr": 79900,
            "monthly_price_usd": 999,
            "resume_credits": 40,
            "ai_usage_limit": 300,
            "job_post_limit": 5,
            "features": ["Unlimited dashboard charts", "AI resume builder", "Mock interview analytics"],
        },
        {
            "code": "recruiter",
            "name": "Recruiter Pro",
            "monthly_price_inr": 249900,
            "monthly_price_usd": 2999,
            "resume_credits": 100,
            "ai_usage_limit": 1000,
            "job_post_limit": 50,
            "features": ["Recruiter monitoring", "Team collaboration", "Candidate pipeline analytics"],
        },
    ]
    for plan in plans:
        SubscriptionPlan.objects.update_or_create(code=plan["code"], defaults=plan)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("jobs", "0009_jobapplication_candidate_summary_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubscriptionPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(choices=[("free", "Free"), ("premium", "Premium"), ("recruiter", "Recruiter")], max_length=30, unique=True)),
                ("name", models.CharField(max_length=80)),
                ("monthly_price_inr", models.PositiveIntegerField(default=0)),
                ("monthly_price_usd", models.PositiveIntegerField(default=0)),
                ("resume_credits", models.PositiveIntegerField(default=3)),
                ("ai_usage_limit", models.PositiveIntegerField(default=10)),
                ("job_post_limit", models.PositiveIntegerField(default=0)),
                ("features", models.JSONField(blank=True, default=list)),
                ("stripe_price_id", models.CharField(blank=True, max_length=120)),
                ("razorpay_plan_id", models.CharField(blank=True, max_length=120)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["monthly_price_inr", "name"]},
        ),
        migrations.CreateModel(
            name="UserSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("active", "Active"), ("trialing", "Trialing"), ("past_due", "Past due"), ("canceled", "Canceled")], default="active", max_length=20)),
                ("provider", models.CharField(blank=True, max_length=20)),
                ("provider_customer_id", models.CharField(blank=True, max_length=150)),
                ("provider_subscription_id", models.CharField(blank=True, max_length=150)),
                ("resume_credits_remaining", models.PositiveIntegerField(default=3)),
                ("ai_usage_count", models.PositiveIntegerField(default=0)),
                ("current_period_start", models.DateTimeField(blank=True, null=True)),
                ("current_period_end", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="jobs.subscriptionplan")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="subscription", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="UsageLedger",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("usage_type", models.CharField(choices=[("ai", "AI"), ("resume_credit", "Resume credit"), ("job_post", "Job post")], max_length=30)),
                ("amount", models.PositiveIntegerField(default=1)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="usage_ledger", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="PaymentTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(choices=[("stripe", "Stripe"), ("razorpay", "Razorpay")], max_length=20)),
                ("provider_reference", models.CharField(blank=True, max_length=180)),
                ("amount", models.PositiveIntegerField(default=0)),
                ("currency", models.CharField(default="INR", max_length=8)),
                ("status", models.CharField(choices=[("created", "Created"), ("paid", "Paid"), ("failed", "Failed")], default="created", max_length=20)),
                ("raw_response", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payment_transactions", to="jobs.subscriptionplan")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payment_transactions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="usageledger",
            index=models.Index(fields=["user", "usage_type", "created_at"], name="jobs_usagel_user_id_33127b_idx"),
        ),
        migrations.RunPython(seed_subscription_plans, migrations.RunPython.noop),
    ]
