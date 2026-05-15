from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0012_jobpost_views_count"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SkillVerificationBadge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("skill_name", models.CharField(max_length=120)),
                ("badge_tier", models.CharField(choices=[("gold", "Gold"), ("silver", "Silver"), ("bronze", "Bronze")], max_length=20)),
                ("source", models.CharField(choices=[("test", "Mini Test"), ("certificate", "Certificate"), ("github", "GitHub"), ("portfolio", "Portfolio")], default="test", max_length=20)),
                ("score", models.PositiveIntegerField(default=0)),
                ("evidence_url", models.URLField(blank=True)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("verified_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skill_badges", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-verified_at"],
                "unique_together": {("user", "skill_name", "badge_tier")},
            },
        ),
        migrations.CreateModel(
            name="AutoApplyRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("threshold", models.PositiveIntegerField(default=80)),
                ("applied_jobs", models.JSONField(blank=True, default=list)),
                ("skipped_jobs", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resume", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="jobs.resume")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="auto_apply_runs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]