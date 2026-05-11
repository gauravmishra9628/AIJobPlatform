import json

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import User
from .tokens import make_signed_token


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEBUG=True)
class AuthenticationApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def post_json(self, path, payload, **headers):
        return self.client.post(
            path,
            data=json.dumps(payload),
            content_type="application/json",
            **headers,
        )

    def test_student_signup_verify_login_and_dashboard(self):
        signup_response = self.post_json(
            reverse("accounts:signup"),
            {
                "email": "student@example.com",
                "password": "StrongPassword123!",
                "first_name": "Asha",
                "role": "student",
                "university_name": "Example University",
            },
        )

        self.assertEqual(signup_response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verification_path", signup_response.json()["debug"])

        login_blocked = self.post_json(
            reverse("accounts:login"),
            {"email": "student@example.com", "password": "StrongPassword123!"},
        )
        self.assertEqual(login_blocked.status_code, 403)

        user = get_user_model().objects.get(email="student@example.com")
        token, _ = make_signed_token(user, "email-verification")
        verify_response = self.client.get(reverse("accounts:verify-email", kwargs={"token": token}))
        self.assertEqual(verify_response.status_code, 200)

        login_response = self.post_json(
            reverse("accounts:login"),
            {"email": "student@example.com", "password": "StrongPassword123!"},
        )
        self.assertEqual(login_response.status_code, 200)
        access = login_response.json()["tokens"]["access"]
        refresh = login_response.json()["tokens"]["refresh"]

        dashboard_response = self.client.get(
            reverse("accounts:student-dashboard"),
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(dashboard_response.json()["dashboard"], "student")

        recruiter_dashboard = self.client.get(
            reverse("accounts:recruiter-dashboard"),
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(recruiter_dashboard.status_code, 403)

        refresh_response = self.post_json(reverse("accounts:token-refresh"), {"refresh": refresh})
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access", refresh_response.json()["tokens"])

    def test_recruiter_signup_and_password_reset(self):
        get_user_model().objects.create_user(
            email="recruiter@example.com",
            password="OldPassword123!",
            role=User.Role.RECRUITER,
            company_name="Example AI",
            is_email_verified=True,
        )

        forgot_response = self.post_json(
            reverse("accounts:forgot-password"),
            {"email": "recruiter@example.com"},
        )
        self.assertEqual(forgot_response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset_path", forgot_response.json()["debug"])

        user = get_user_model().objects.get(email="recruiter@example.com")
        token, _ = make_signed_token(user, "password-reset")
        reset_response = self.post_json(
            reverse("accounts:password-reset-confirm", kwargs={"token": token}),
            {"password": "NewPassword123!"},
        )
        self.assertEqual(reset_response.status_code, 200)

        login_response = self.post_json(
            reverse("accounts:login"),
            {"email": "recruiter@example.com", "password": "NewPassword123!"},
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["user"]["role"], "recruiter")
