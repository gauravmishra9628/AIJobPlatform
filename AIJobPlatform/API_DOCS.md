# API Docs

Base URLs:

- Auth: `/api/auth/`
- Jobs: `/api/jobs/`
- Companies: `/api/companies/`

Protected endpoints expect:

```http
Authorization: Bearer <access-token>
```

## Auth

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/auth/signup/` | Create student/recruiter account |
| POST | `/api/auth/login/` | Login and receive access/refresh tokens |
| POST | `/api/auth/logout/` | Logout |
| POST | `/api/auth/token/refresh/` | Rotate and refresh tokens |
| GET | `/api/auth/me/` | Current user/profile |
| PATCH | `/api/auth/profile/` | Update profile |
| GET | `/api/auth/verify-email/<token>/` | Verify email |
| POST | `/api/auth/password/forgot/` | Request password reset |
| POST | `/api/auth/password/reset/<token>/` | Reset password |
| POST | `/api/auth/oauth/google/` | Google OAuth login |
| POST | `/api/auth/otp/send/` | Send OTP |
| POST | `/api/auth/otp/verify/` | Verify OTP |
| GET/PUT | `/api/auth/theme/` | Read/update theme preference |

## Jobs & Applications

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/jobs/?page=1&page_size=20&q=react` | List/search jobs with pagination |
| POST | `/api/jobs/` | Recruiter/admin creates job |
| GET | `/api/jobs/my/` | Recruiter posted jobs |
| POST | `/api/jobs/<job_id>/apply/` | Student applies |
| GET | `/api/jobs/applications/` | Student/recruiter applications |
| PATCH | `/api/jobs/applications/<id>/` | Update application status |
| GET | `/api/jobs/applications/<id>/history/` | Application status history |

## Resume & AI

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/jobs/resume/upload/` | Upload validated resume file |
| GET | `/api/jobs/resume/latest/` | Latest resume |
| POST | `/api/jobs/resume/analyze-ats/` | ATS scoring |
| POST | `/api/jobs/resume/analyze-ai/` | AI resume feedback |
| POST | `/api/jobs/match/calculate/` | AI job/resume match |
| GET | `/api/jobs/recommendations/` | Personalized job recommendations |
| POST | `/api/jobs/skill-gap/analyze/` | Skill gap analysis |
| POST | `/api/jobs/career/plan/` | Career plan |
| POST | `/api/jobs/career/cover-letter/` | Cover letter generation |

## Communication & Analytics

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/jobs/messages/` | Network messages |
| POST | `/api/jobs/messages/` | Send network message |
| POST | `/api/jobs/chat/send/` | Send chat message |
| GET | `/api/jobs/chat/list/` | Chat list |
| GET | `/api/jobs/notifications/` | Notifications |
| POST | `/api/jobs/notifications/mark-read/` | Mark notification read |
| GET | `/api/jobs/analytics/` | Recruiter analytics |
| GET | `/api/jobs/admin/analytics/` | Admin analytics |

## Companies

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/companies/?q=acme` | Company directory |
| GET | `/api/companies/<id>/` | Company profile |
| POST | `/api/companies/<id>/reviews/` | Submit company review |
| GET | `/api/companies/<id>/badge/` | Company badge |
