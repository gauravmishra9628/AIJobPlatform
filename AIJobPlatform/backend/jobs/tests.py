import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from accounts.tokens import create_jwt


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
