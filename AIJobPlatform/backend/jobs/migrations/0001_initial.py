# Generated manually for jobs app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="JobPost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("company", models.CharField(max_length=180)),
                ("location", models.CharField(max_length=180)),
                ("description", models.TextField()),
                ("skills_required", models.TextField(blank=True)),
                (
                    "employment_type",
                    models.CharField(
                        choices=[
                            ("full-time", "Full-time"),
                            ("part-time", "Part-time"),
                            ("internship", "Internship"),
                            ("contract", "Contract"),
                        ],
                        default="full-time",
                        max_length=20,
                    ),
                ),
                ("salary_range", models.CharField(blank=True, max_length=120)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "posted_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="posted_jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Resume",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="resumes/")),
                ("original_name", models.CharField(max_length=255)),
                ("extracted_text", models.TextField(blank=True)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="resumes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
    ]
