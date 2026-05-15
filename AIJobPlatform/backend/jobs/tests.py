import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch

from accounts.models import User
from accounts.tokens import create_jwt
from .comparison_service import ResumeJobComparator
from .models import AutoApplyRun, JobPost, Notification, Resume


class JobWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = get_user_model().objects.create_user(
            email="student.workflow@example.com",
            password="StrongPassword123!",
            first_name="Student",
            role=User.Role.STUDENT,
            is_email_verified=True,
        )
        self.student.profile.skills = ["React", "Python", "Django"]
        self.student.profile.save()
        self.recruiter = get_user_model().objects.create_user(
            email="recruiter.workflow@example.com",
            password="StrongPassword123!",
            first_name="Recruiter",
            role=User.Role.RECRUITER,
            company_name="Workflow AI",
            is_email_verified=True,
        )
        self.student_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_jwt(self.student)}"}
        self.recruiter_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_jwt(self.recruiter)}"}

    def post_json(self, path, payload, **headers):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json", **headers)

    def patch_json(self, path, payload, **headers):
        return self.client.patch(path, data=json.dumps(payload), content_type="application/json", **headers)

    def test_application_guidance_and_messaging_flow(self):
        job_response = self.post_json(
            reverse("jobs:jobs-collection"),
            {
                "title": "Full Stack AI Engineer",
                "company": "Workflow AI",
                "location": "Remote",
                "description": "Build React and Django products with Python and AI workflows.",
                "skills_required": "React, Django, Python, AI",
                "employment_type": "full-time",
            },
            **self.recruiter_headers,
        )
        self.assertEqual(job_response.status_code, 201)
        job_id = job_response.json()["job"]["id"]

        apply_response = self.post_json(
            reverse("jobs:job-apply", kwargs={"job_id": job_id}),
            {"cover_note": "I have shipped React and Django projects."},
            **self.student_headers,
        )
        self.assertEqual(apply_response.status_code, 201)
        application_id = apply_response.json()["application"]["id"]

        applications_response = self.client.get(reverse("jobs:applications"), **self.recruiter_headers)
        self.assertEqual(applications_response.status_code, 200)
        self.assertEqual(len(applications_response.json()["applications"]), 1)

        status_response = self.patch_json(
            reverse("jobs:application-detail", kwargs={"application_id": application_id}),
            {"status": "shortlisted"},
            **self.recruiter_headers,
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["application"]["status"], "shortlisted")

        guidance_response = self.client.get(reverse("jobs:career-guidance"), **self.student_headers)
        self.assertEqual(guidance_response.status_code, 200)
        self.assertIn("roadmap", guidance_response.json())

        message_response = self.post_json(
            reverse("jobs:messages"),
            {"recipient_id": self.student.pk, "body": "You are shortlisted for the next round."},
            **self.recruiter_headers,
        )
        self.assertEqual(message_response.status_code, 201)

        inbox_response = self.client.get(reverse("jobs:messages"), **self.student_headers)
        self.assertEqual(inbox_response.status_code, 200)
        self.assertEqual(len(inbox_response.json()["messages"]), 1)

    def test_recruiter_can_edit_and_delete_posted_job(self):
        job_response = self.post_json(
            reverse("jobs:jobs-collection"),
            {
                "title": "Platform Engineer",
                "company": "Workflow AI",
                "location": "Remote",
                "description": "Build APIs and hiring tools.",
                "skills_required": "Django, React",
                "employment_type": "full-time",
            },
            **self.recruiter_headers,
        )
        self.assertEqual(job_response.status_code, 201)
        job_id = job_response.json()["job"]["id"]

        update_response = self.patch_json(
            reverse("jobs:job-detail", kwargs={"job_id": job_id}),
            {
                "title": "Senior Platform Engineer",
                "location": "Hybrid",
                "description": "Build APIs, hiring tools, and analytics.",
                "skills_required": "Django, React, PostgreSQL",
                "salary_range": "18-24 LPA",
            },
            **self.recruiter_headers,
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["job"]["title"], "Senior Platform Engineer")
        self.assertEqual(update_response.json()["job"]["is_active"], True)

        delete_response = self.client.delete(reverse("jobs:job-detail", kwargs={"job_id": job_id}), **self.recruiter_headers)
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["job"]["is_active"], False)


class ResumeJobComparatorServiceTests(TestCase):
    def test_comparator_extracts_matches_gaps_salary_and_suggestions(self):
        recruiter = get_user_model().objects.create_user(
            email="recruiter.comparator@example.com",
            password="StrongPassword123!",
            first_name="Recruiter",
            role=User.Role.RECRUITER,
            company_name="Comparator AI",
            is_email_verified=True,
        )
        job = JobPost.objects.create(
            posted_by=recruiter,
            title="ML Platform Engineer",
            company="Comparator AI",
            location="Bangalore",
            description="Must have Machine Learning, AWS, and Docker. Nice to have Kubernetes. 5 years experience.",
            skills_required="Machine Learning, AWS, Docker",
            required_experience_years=5,
            required_certifications=["AWS Certified"],
            salary_min=1800000,
            salary_max=2400000,
            employment_type="full-time",
        )
        comparator = ResumeJobComparator()

        resume_data = comparator.extract_resume_data(
            "Python ML engineer with 3 years of experience building AWS services. Bachelor degree."
        )
        job_data = comparator.extract_job_requirements(job)
        result = comparator.calculate_match_score(resume_data, job_data)
        salary = comparator.predict_salary(
            result["match_percentage"],
            (job.salary_min + job.salary_max) / 2,
            resume_data["experience_years"],
            job.location,
        )
        suggestions = comparator.generate_improvement_suggestions(result["missing_skills"], result["experience_gap"])

        self.assertIn("machine learning", resume_data["skills"])
        self.assertIn("machine learning", job_data["required_skills"])
        self.assertIn("aws", [item["skill"] for item in result["matched_skills"]])
        self.assertIn("docker", [item["skill"] for item in result["missing_skills"]])
        self.assertEqual(result["experience_gap"], -2)
        self.assertEqual(result["certification_gap"], ["aws certified"])
        self.assertGreater(salary["predicted_salary"], 0)
        self.assertTrue(suggestions)


class ExternalJobsApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = get_user_model().objects.create_user(
            email="student.external@example.com",
            password="StrongPassword123!",
            first_name="Student",
            role=User.Role.STUDENT,
            is_email_verified=True,
        )
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {create_jwt(self.student)}"}

    @patch("jobs.feature_views.fetch_internship_jobs")
    @patch("jobs.feature_views.fetch_remotive_jobs")
    @patch("jobs.feature_views.fetch_linkedin_style_jobs")
    @patch("jobs.feature_views.fetch_google_jobs")
    def test_external_jobs_can_search_all_live_sources(
        self,
        fetch_google_jobs,
        fetch_linkedin_style_jobs,
        fetch_remotive_jobs,
        fetch_internship_jobs,
    ):
        fetch_google_jobs.return_value = [{"source": "google_jobs", "title": "Google role"}]
        fetch_linkedin_style_jobs.return_value = [{"source": "linkedin", "title": "LinkedIn role"}]
        fetch_remotive_jobs.return_value = [{"source": "remotive", "title": "Remote role", "is_remote": True}]
        fetch_internship_jobs.return_value = [{"source": "jsearch", "title": "Internship", "is_internship": True}]

        response = self.client.get(
            reverse("jobs:external-jobs"),
            {"q": "python", "location": "Remote"},
            **self.headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 4)
        self.assertEqual(payload["sources"], ["google", "linkedin", "remote", "internships"])

    @patch("jobs.feature_views.fetch_google_jobs")
    def test_external_jobs_filters_google_internships(self, fetch_google_jobs):
        fetch_google_jobs.return_value = [
            {"source": "google_jobs", "title": "Software Engineer", "is_internship": False},
            {"source": "google_jobs", "title": "Software Intern", "is_internship": True},
        ]

        response = self.client.get(
            reverse("jobs:external-jobs"),
            {"q": "software", "source": "google", "type": "internship"},
            **self.headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["title"], "Software Intern")


class CompanyAndAIFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = get_user_model().objects.create_user(
            email="student.company@example.com",
            password="StrongPassword123!",
            first_name="Student",
            role=User.Role.STUDENT,
            is_email_verified=True,
        )
        self.recruiter = get_user_model().objects.create_user(
            email="recruiter.company@example.com",
            password="StrongPassword123!",
            first_name="Recruiter",
            role=User.Role.RECRUITER,
            company_name="Acme Labs",
            is_email_verified=True,
        )
        self.student_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_jwt(self.student)}"}
        self.recruiter_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_jwt(self.recruiter)}"}

    def post_json(self, path, payload, **headers):
        return self.client.post(path, data=json.dumps(payload), content_type="application/json", **headers)

    def test_company_profiles_are_exposed_from_jobs(self):
        self.post_json(
            reverse("jobs:jobs-collection"),
            {
                "title": "Backend Engineer",
                "company": "Acme Labs",
                "location": "Remote",
                "description": "Build APIs for hiring workflows.",
                "skills_required": "Django, Python, APIs",
                "employment_type": "full-time",
            },
            HTTP_AUTHORIZATION=f"Bearer {create_jwt(self.recruiter)}",
        )

        list_response = self.client.get("/api/companies/")
        self.assertEqual(list_response.status_code, 200)
        companies = list_response.json()["companies"]
        self.assertGreaterEqual(len(companies), 1)
        self.assertEqual(companies[0]["name"], "Acme Labs")

        company_id = companies[0]["id"]
        detail_response = self.client.get(f"/api/companies/{company_id}/")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["company"]["name"], "Acme Labs")

    @patch("jobs.ai_views.AIIntegrationService.generate_cover_letter")
    def test_cover_letter_endpoint_uses_ai_service(self, generate_cover_letter):
        generate_cover_letter.return_value = {
            "success": True,
            "cover_letter": "Dear Hiring Manager, I would like to apply.",
        }

        response = self.post_json(
            reverse("jobs:generate-cover-letter"),
            {
                "job_title": "Platform Engineer",
                "company": "Acme Labs",
                "skills": ["Django", "Python"],
            },
            **self.student_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)
        self.assertIn("Dear Hiring Manager", response.json()["cover_letter"])

    def test_salary_prediction_returns_band(self):
        response = self.client.get(
            reverse("jobs:predict-salary"),
            {"target_role": "Senior Software Engineer"},
            **self.student_headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("salary_min", payload)
        self.assertIn("salary_max", payload)
        self.assertIn("label", payload)

    def test_ai_match_returns_skill_recommendations(self):
        job = JobPost.objects.create(
            posted_by=self.recruiter,
            title="Senior Platform Engineer",
            company="Acme Labs",
            location="Remote",
            description="Build Django APIs, Docker workflows, and AWS-powered services with measurable impact.",
            skills_required="Django, Python, Docker, AWS",
            employment_type="full-time",
        )
        resume = Resume.objects.create(
            user=self.student,
            file=SimpleUploadedFile("resume.txt", b"resume content"),
            original_name="resume.txt",
            extracted_text="Python and Django engineer with React experience, 4 years building products and APIs.",
            extracted_skills=["Python", "Django", "React"],
        )

        response = self.post_json(
            reverse("jobs:calculate-match"),
            {"job_id": job.id, "resume_id": resume.id},
            **self.student_headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("match_percentage", payload)
        self.assertIn("semantic_similarity", payload)
        self.assertIn("skill_recommendations", payload)
        self.assertGreaterEqual(len(payload["skill_recommendations"]), 1)
        self.assertIn("missing_skills_required", payload)
        self.assertIn("Docker", payload["missing_skills_required"])

    def test_high_match_creates_job_match_notification(self):
        job = JobPost.objects.create(
            posted_by=self.recruiter,
            title="AI Product Engineer",
            company="Acme Labs",
            location="Remote",
            description="Build AI products with Python, Django, React, and AWS.",
            skills_required="Python, Django, React, AWS",
            employment_type="full-time",
        )
        resume = Resume.objects.create(
            user=self.student,
            file=SimpleUploadedFile("resume.txt", b"resume content"),
            original_name="resume.txt",
            extracted_text="Python Django React AWS engineer with 5 years building AI products and APIs.",
            extracted_skills=["Python", "Django", "React", "AWS"],
        )

        response = self.post_json(
            reverse("jobs:calculate-match"),
            {"job_id": job.id, "resume_id": resume.id},
            **self.student_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Notification.objects.filter(
                user=self.student,
                related_job=job,
                type=Notification.NotificationType.JOB_MATCH,
            ).exists()
        )

    def test_career_guidance_includes_dashboard_signals(self):
        Resume.objects.create(
            user=self.student,
            file=SimpleUploadedFile("resume.txt", b"resume content"),
            original_name="resume.txt",
            extracted_text="Python developer with Django and React projects.",
            extracted_skills=["Python", "Django", "React"],
        )

        response = self.client.get(reverse("jobs:career-guidance"), **self.student_headers)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("profile_strength", payload)
        self.assertIn("resume_rating", payload)
        self.assertIn("weekly_tips", payload)
        self.assertIn("job_alerts", payload)

    def test_recruiter_dashboard_reports_views_and_candidate_ranking(self):
        job = JobPost.objects.create(
            posted_by=self.recruiter,
            title="Data Platform Engineer",
            company="Acme Labs",
            location="Remote",
            description="Build pipelines and analytics tools.",
            skills_required="Python, SQL, AWS",
            employment_type="full-time",
        )
        application = self.client.post(
            reverse("jobs:job-apply", kwargs={"job_id": job.id}),
            data=json.dumps({"cover_note": "Strong pipeline experience."}),
            content_type="application/json",
            **self.student_headers,
        )
        self.assertEqual(application.status_code, 201)

        self.client.get(reverse("jobs:job-detail", kwargs={"job_id": job.id}), **self.recruiter_headers)

        dashboard_response = self.client.get(reverse("jobs:recruiter-dashboard"), **self.recruiter_headers)
        self.assertEqual(dashboard_response.status_code, 200)
        payload = dashboard_response.json()
        self.assertGreaterEqual(payload["analytics"]["total_views"], 1)
        self.assertTrue(payload["most_viewed_jobs"])
        self.assertTrue(payload["candidate_ranking"])

    def test_public_profile_and_badges_workflow(self):
        self.student.profile.headline = "AI Product Engineer"
        self.student.profile.skills = ["Python", "React"]
        self.student.profile.portfolio_items = [
            {"name": "Hiring AI", "description": "Portfolio project", "link": "https://example.com"}
        ]
        self.student.profile.save()

        profile_response = self.client.get(reverse("accounts:public-profile", kwargs={"user_id": self.student.id}))
        self.assertEqual(profile_response.status_code, 200)
        self.assertIn("profile_strength", profile_response.json())

        badge_response = self.client.post(
            reverse("accounts:user-badges", kwargs={"user_id": self.student.id}),
            data=json.dumps({"skill_name": "Python", "score": 92, "source": "test", "note": "Mini test passed"}),
            content_type="application/json",
        )
        self.assertEqual(badge_response.status_code, 201)
        self.assertIn("badge", badge_response.json())

    def test_auto_apply_runs_on_high_match_jobs(self):
        job = JobPost.objects.create(
            posted_by=self.recruiter,
            title="React Python Engineer",
            company="Acme Labs",
            location="Remote",
            description="Build products with Python, React, and Django.",
            skills_required="Python, React, Django",
            employment_type="full-time",
        )
        Resume.objects.create(
            user=self.student,
            file=SimpleUploadedFile("resume.txt", b"resume content"),
            original_name="resume.txt",
            extracted_text="Python React Django engineer with 5 years building products.",
            extracted_skills=["Python", "React", "Django"],
        )

        response = self.post_json(
            reverse("jobs:auto-apply-jobs"),
            {"threshold": 1, "limit": 5},
            **self.student_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(AutoApplyRun.objects.filter(user=self.student).exists())
        self.assertTrue(JobPost.objects.filter(pk=job.pk).exists())
