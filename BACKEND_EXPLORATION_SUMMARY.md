# AIJobPlatform Backend - Comprehensive Exploration Summary
**Date**: May 12, 2026  
**Status**: Fully Explored

---

## 1. API ENDPOINTS SUMMARY

### Authentication Endpoints (accounts/urls.py)
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/auth/signup/` | POST | User registration (student/recruiter) | No |
| `/api/auth/login/` | POST | Email & password login | No |
| `/api/auth/logout/` | POST | User logout | ✅ JWT |
| `/api/auth/token/refresh/` | POST | Refresh JWT access token | No |
| `/api/auth/verify-email/<token>/` | GET | Email verification via token | No |
| `/api/auth/verify-email/resend/` | POST | Resend verification email | No |
| `/api/auth/password/forgot/` | POST | Request password reset | No |
| `/api/auth/password/reset/<token>/` | POST | Reset password with token | No |
| `/api/auth/me/` | GET | Get current user profile | ✅ JWT |
| `/api/auth/profile/` | GET/PUT/PATCH | Manage profile details | ✅ JWT |
| `/api/auth/dashboard/student/` | GET | Student dashboard data | ✅ JWT |
| `/api/auth/dashboard/recruiter/` | GET | Recruiter dashboard data | ✅ JWT |
| `/api/auth/dashboard/admin/` | GET | Admin dashboard data | ✅ JWT |

### Job Management Endpoints (jobs/urls.py - Core)
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/jobs/` | GET/POST | List/post jobs | POST: Recruiter role |
| `/api/jobs/my/` | GET | Recruiter's posted jobs | ✅ Recruiter |
| `/api/jobs/<job_id>/apply/` | POST | Apply to a job | ✅ Student |
| `/api/jobs/applications/` | GET | View applications (student/recruiter filtered) | ✅ JWT |
| `/api/jobs/applications/<app_id>/` | PATCH | Update application status (recruiter only) | ✅ Recruiter |
| `/api/jobs/resume/upload/` | POST | Upload resume | ✅ Student |
| `/api/jobs/resume/latest/` | GET | Get latest resume | ✅ JWT |
| `/api/jobs/recommendations/` | GET | Job recommendations | ✅ JWT |
| `/api/jobs/career-guidance/` | GET | Career guidance data | ✅ JWT |
| `/api/jobs/messages/` | GET | Network messages | ✅ JWT |

### Advanced Features Endpoints (jobs/urls.py - advanced_views.py)
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/jobs/resume/analyze-ats/` | POST | ATS resume analysis | ✅ Student |
| `/api/jobs/ats-score/<score_id>/` | GET | Get ATS score details | ✅ Student |
| `/api/jobs/bookmarks/` | GET | List bookmarked jobs | ✅ JWT |
| `/api/jobs/bookmarks/toggle/` | POST | Toggle job bookmark | ✅ JWT |
| `/api/jobs/applications/<app_id>/history/` | GET | Application tracking history | ✅ JWT |
| `/api/jobs/applications/stage/update/` | POST | Update application stage | ✅ JWT |
| `/api/jobs/skill-gap/analyze/` | POST | Analyze skill gaps | ✅ JWT |
| `/api/jobs/skill-gap/` | GET | Get skill gap analysis | ✅ JWT |
| `/api/jobs/notifications/` | GET | List notifications | ✅ JWT |
| `/api/jobs/notifications/mark-read/` | POST | Mark notification as read | ✅ JWT |
| `/api/jobs/interview-prep/generate/` | POST | Generate interview prep | ✅ JWT |
| `/api/jobs/interview-prep/<prep_id>/` | GET | Get interview prep details | ✅ JWT |
| `/api/jobs/analytics/` | GET | Recruiter analytics | ✅ Recruiter |
| `/api/jobs/analytics/trends/` | GET | Hiring trends analytics | ✅ Recruiter |

### AI Features Endpoints (jobs/urls.py - ai_views.py)
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/jobs/resume/analyze-ai/` | POST | AI-powered resume analysis | ✅ Student |
| `/api/jobs/resume/<resume_id>/ai-analysis/` | GET | Get AI analysis results | ✅ Student |
| `/api/jobs/match/calculate/` | POST | Calculate AI match score (job-resume) | ✅ JWT |
| `/api/jobs/jobs/<job_id>/matches/` | GET | Get top matching resumes | ✅ Recruiter |
| `/api/jobs/career/plan/` | POST | Generate AI career plan | ✅ Student |
| `/api/jobs/career/coach/` | GET | Get career coach plan | ✅ Student |
| `/api/jobs/career/predict/` | GET | Predict career path & opportunities | ✅ Student |
| `/api/jobs/career/internship-roadmap/` | POST | Generate internship roadmap | ✅ Student |
| `/api/jobs/career/reputation-score/` | GET | Calculate candidate reputation | ✅ JWT |
| `/api/jobs/career/team-recommendations/` | GET | Get team recommendations | ✅ JWT |
| `/api/jobs/career/networking-suggestions/` | GET | Networking suggestions | ✅ JWT |
| `/api/jobs/career/timeline/` | GET | Career timeline visualization | ✅ JWT |
| `/api/jobs/career/attendance-tracking/` | POST | Internship attendance tracking | ✅ Student |
| `/api/jobs/resume/optimize-keywords/` | POST | AI keyword optimization | ✅ Student |
| `/api/jobs/resume/fake-detection/` | POST | Detect fake resume signals | ✅ JWT |
| `/api/jobs/resume/translate/` | POST | Resume translation | ✅ JWT |
| `/api/jobs/market/hiring-heatmap/` | GET | Company hiring heatmaps | ✅ JWT |
| `/api/jobs/interview/voice-simulator/` | POST | Voice interview simulator | ✅ Student |
| `/api/jobs/interview/gd-simulator/` | POST | Group discussion simulator | ✅ Student |
| `/api/jobs/interview/transcript-generator/` | POST | Interview transcript generator | ✅ JWT |
| `/api/jobs/coding/evaluate/` | POST | Competitive coding evaluation | ✅ Student |
| `/api/jobs/career/personality-coach/` | GET | Personality development coach | ✅ JWT |
| `/api/jobs/career/simulation-engine/` | POST | Interactive career simulation | ✅ JWT |
| `/api/jobs/career/internship-performance/` | POST | Smart internship performance eval | ✅ Student |
| `/api/jobs/projects/collaborative-builder/` | POST | Collaborative project builder | ✅ JWT |
| `/api/jobs/productivity/time-management/` | POST | AI time management analyzer | ✅ JWT |
| `/api/jobs/recruiter/trust-badge/` | POST | Recruiter trust badge | ✅ JWT |
| `/api/jobs/branding/assistant/` | GET | Personal branding assistant | ✅ JWT |
| `/api/jobs/chat/send/` | POST | Send chat message | ✅ JWT |
| `/api/jobs/chat/<user_id>/` | GET | Get chat messages with user | ✅ JWT |
| `/api/jobs/chat/list/` | GET | Get chat list | ✅ JWT |
| `/api/jobs/dashboard/` | GET | Get recruiter dashboard | ✅ Recruiter |
| `/api/jobs/dashboard/update/` | POST | Update recruiter dashboard | ✅ Recruiter |
| `/api/jobs/dashboard/favorite/` | POST | Save favorite job to dashboard | ✅ Recruiter |

### External APIs & Features (jobs/urls.py - feature_views.py)
| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/jobs/external-jobs/` | GET | Fetch jobs from external APIs | ✅ JWT |
| `/api/jobs/auth/send-otp/` | POST | Send email OTP verification | No |

---

## 2. EXTERNAL API INTEGRATIONS

### Implemented Integrations

#### JSearch API (RapidAPI)
- **Function**: `fetch_jsearch_jobs(query, location, job_type, source_label)`
- **Configuration Required**: `JSEARCH_API_KEY` in settings
- **API Endpoint**: `https://jsearch.p.rapidapi.com/search`
- **Features**:
  - Job search with query and location
  - Supports internship and remote filters
  - Returns: job_id, title, company, location, description, employment_type, salary info

#### Adzuna API
- **Function**: `fetch_adzuna_jobs(query, location, job_type)`
- **Configuration Required**: `ADZUNA_API_ID`, `ADZUNA_API_KEY` in settings
- **API Endpoint**: `https://api.adzuna.com/v1/api/jobs/{location}/search/1`
- **Features**:
  - Job search with salary data
  - Supports internship and remote filters
  - Returns: salary_min, salary_max, contract_type

#### Remotive API (Free, No Auth)
- **Function**: `fetch_remotive_jobs(query)`
- **Configuration Required**: None (public API)
- **API Endpoint**: `https://remotive.com/api/remote-jobs`
- **Features**:
  - Remote jobs only
  - Returns: title, company_name, description, job_type

#### Google Jobs (via SerpApi)
- **Function**: `fetch_google_jobs(query, location, job_type)`
- **Configuration Required**: `SERPAPI_API_KEY` or `GOOGLE_JOBS_API_KEY` in settings
- **Fallback**: Uses JSearch if key not configured
- **API Endpoint**: `https://serpapi.com/search.json` (engine: google_jobs)
- **Features**:
  - Integrates with Google search results
  - Returns: schedule_type, apply_options

#### LinkedIn Jobs (via RapidAPI)
- **Function**: `fetch_linkedin_style_jobs(query, location, job_type)`
- **Configuration Required**: `LINKEDIN_JOBS_API_KEY` in settings
- **Fallback**: Uses JSearch with LinkedIn query if key not configured
- **API Endpoint**: `https://linkedin-jobs-search.p.rapidapi.com/`
- **Features**:
  - LinkedIn-style job listings
  - Returns: job_title, job_description, job_type, job_location

### Not Yet Implemented
- Google OAuth login
- GitHub API integration
- Twilio SMS (dependency in requirements but not used)

---

## 3. AUTHENTICATION ENDPOINTS DETAILED

### Email-Based Authentication
1. **Signup** (`POST /api/auth/signup/`)
   - Fields: email, password, first_name, last_name, role (student/recruiter), company_name or university_name
   - Returns: user payload, profile payload, verification email URL (debug mode)
   - Auto-creates Profile on signup

2. **Login** (`POST /api/auth/login/`)
   - Fields: email, password
   - Returns: user payload, access/refresh JWT tokens
   - Sets httpOnly session cookie
   - Requires email verification

3. **Token Refresh** (`POST /api/auth/token/refresh/`)
   - Fields: refresh_token
   - Returns: new access/refresh token pair
   - Uses JWT decode for validation

4. **Email Verification** (`GET /api/auth/verify-email/<token>/`)
   - Validates signed token (24-hour expiry)
   - Sets `is_email_verified = True`
   - Can resend via `POST /api/auth/verify-email/resend/`

5. **Password Reset Flow**
   - Request: `POST /api/auth/password/forgot/` (email)
   - Confirm: `POST /api/auth/password/reset/<token>/` (new password)
   - Token expires in 1 hour
   - Uses Django password validation

### JWT Token Structure
- **Access Token**: 15-minute lifetime
- **Refresh Token**: 7-day lifetime
- **Token Type**: HS256 signed
- **Payload**: user_id, email, role, token_type

### OAuth/OTP Ready (Not Connected)
- Models exist: `OTPVerification`, `PasswordResetToken`
- Models support Google/LinkedIn: `User.google_id`, `User.linkedin_id`, `User.oauth_provider`
- Feature endpoint `send_email_otp` is defined but partial

---

## 4. AI FEATURES & INTEGRATIONS

### AI APIs Available (in settings but NOT YET CONNECTED)
```python
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GOOGLE_GEMINI_KEY = os.environ.get("GOOGLE_GEMINI_KEY", "")
```

### AI Features Implemented (Without LLM Connection)

#### AI Resume Analysis
- **Model**: `AIResumeAnalysis`
- **Scoring**: Text analysis (no LLM yet)
- **Metrics**:
  - `overall_rating` (0-100)
  - `readability_score` (based on word count)
  - `impact_score` (based on action verbs & metrics)
  - Strengths/weaknesses detection
  - Recommendations generation

#### AI Match Scoring
- **Model**: `AIMatchScore`
- **Algorithm**: Token-based matching (no ML/LLM)
- **Metrics**:
  - `skills_alignment` (40% weight)
  - `experience_alignment` (30% weight)
  - `culture_fit` (20% weight)
  - `growth_potential` (10% weight)
  - Match percentage (0-100)

#### Career Coach & Path Prediction
- **Model**: `AICareerCoach`
- **Features**:
  - Role trajectory mapping (junior → mid → senior → lead)
  - Skill development planning
  - Career milestones
  - Salary insights by role
  - Learning recommendations

#### Interview Preparation
- **Model**: `InterviewPreparation`
- **Includes**:
  - Generated interview questions (template-based)
  - Coding problems recommendations
  - Tips and tricks
  - Preparation resources

#### Voice Interview Simulator
- **Function**: `simulate_voice_interview()`
- **Scoring Metrics**:
  - Fluency score (filler word analysis)
  - Communication score (structure & clarity)
  - Confidence score (action verb presence)
  - Returns: instant evaluation & feedback

### AI Features Defined But Minimally Implemented
- Resume keyword optimization
- Fake resume detection
- Resume translation
- Hiring heatmaps
- Group discussion simulator
- Competitive coding evaluation
- Personality development coach
- Career simulation engine
- Internship performance evaluation
- Collaborative project builder
- Time management analyzer
- Personal branding assistant

---

## 5. DATABASE MODELS

### Core Models
- **User** (Custom: email-based, roles: student/recruiter/admin)
- **Profile** (user profile with skills, bio, links)
- **JobPost** (recruiter posts jobs)
- **JobApplication** (student applies to jobs)
- **Resume** (user resumes with text extraction)
- **NetworkMessage** (direct messaging)

### Advanced Feature Models
- **ResumeAtsScore** (ATS compatibility analysis)
- **JobBookmark** (bookmarked jobs)
- **ApplicationStageLog** (hiring pipeline tracking)
- **SkillGapAnalysis** (skill gap assessment)
- **Notification** (system notifications with types)
- **InterviewPreparation** (interview prep material)
- **RecruiterAnalytics** (hiring metrics)

### AI Feature Models
- **AIResumeAnalysis** (AI resume evaluation)
- **AIMatchScore** (job-resume match)
- **AICareerCoach** (career planning)
- **ChatMessage** (real-time chat with indexes)
- **RecruiterDashboard** (recruiter workspace)

### Integration Models
- **ExternalJobListing** (jobs from external APIs - 5 sources)
- **ResumeTemplate** (PDF generation)
- **OTPVerification** (OTP auth - with expiry)
- **PasswordResetToken** (password reset tokens - with expiry)

---

## 6. MISSING IMPLEMENTATIONS

### Critical Missing
1. **OpenAI/Gemini Integration**
   - Keys configured but not used
   - No API calls in any views
   - AI features use rule-based logic only

2. **Email/OTP Authentication**
   - `send_email_otp()` endpoint defined but incomplete
   - OTP model exists, but no send/verify logic
   - Twilio dependency installed but unused

3. **Google/LinkedIn OAuth**
   - `User.google_id`, `User.linkedin_id` fields exist
   - No OAuth flow implemented
   - No callback handlers

4. **WebSocket Chat** (Partial)
   - Channels + Redis configured
   - `chat/` endpoints return HTTP responses
   - WebSocket consumer undefined

5. **PDF Generation**
   - `ResumeTemplate` model exists
   - Dependencies: pdfkit, reportlab, PyPDF2 installed
   - No endpoint to generate/download PDF

### Medium Priority Missing
- Skill verification badges (GitHub integration)
- Company profile pages
- Dark mode persistence (UI ready, backend not)
- Admin analytics dashboard
- Real-time notifications (WebSocket)
- File uploads validation
- Rate limiting on API calls
- Comprehensive error handling

### Testing Coverage
- Only basic test stubs exist in `jobs/tests.py`
- No test coverage for auth flows
- No integration tests

---

## 7. CONFIGURATION STATUS

### Environment Variables Needed
```bash
# Core
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
DJANGO_SESSION_COOKIE_SECURE
DJANGO_CSRF_COOKIE_SECURE
DJANGO_SECURE_SSL_REDIRECT
DJANGO_CSRF_TRUSTED_ORIGINS

# Email
EMAIL_BACKEND
EMAIL_HOST
EMAIL_PORT
EMAIL_USE_TLS
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL

# External Job APIs
JSEARCH_API_KEY (Required)
ADZUNA_API_ID (Required)
ADZUNA_API_KEY (Required)
SERPAPI_API_KEY (Optional - Google fallback to JSearch)
GOOGLE_JOBS_API_KEY (Optional - Google fallback to JSearch)
LINKEDIN_JOBS_API_KEY (Optional - LinkedIn fallback to JSearch)

# AI APIs (Not Connected)
OPENAI_API_KEY
GOOGLE_GEMINI_KEY
```

### Database
- **Current**: SQLite (development)
- **Production**: Needs migration to PostgreSQL
- **Migrations**: All auto-created, no manual migrations needed

### CORS & Security
- CORS origins configured from env
- CSRF protection enabled
- XSS filter enabled
- HTTPS recommended for production
- Session cookies: 2-hour timeout

---

## 8. API RESPONSE PATTERNS

### Success Response
```json
{
  "detail": "Operation successful",
  "data": { ... },
  "tokens": { "access": "...", "refresh": "..." }
}
```

### Error Response
```json
{
  "detail": "Error message",
  "error": "Specific error",
  "field": ["Field error message"]
}
```

### Pagination
- Not implemented (all results returned)
- Should add for large datasets

### Rate Limiting
- Not implemented
- External APIs have their own limits

---

## 9. TECHNOLOGY STACK

### Backend
- **Framework**: Django 5.1 (DRF 3.15)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Auth**: JWT + Custom tokens
- **Real-time**: Django Channels + Redis
- **APIs**: Requests library for external calls

### Dependencies
```
Django>=5.1,<6.0
djangorestframework>=3.15
PyJWT>=2.8
requests>=2.31.0
google-auth>=2.26.2
openai>=1.3.0
google-generativeai>=0.3.0
channels>=4.0.0
redis>=5.0.0
Pillow>=10.2.0
pdfkit>=1.0.0
PyPDF2>=3.0.0
reportlab>=4.0.0
twilio>=8.0.0
```

### Frontend
- **Framework**: React + Vite
- **Build**: esbuild
- **Styling**: CSS
- **HTTP**: Axios
- **WebSocket**: Ready for Channels

---

## 10. QUICK REFERENCE - WHAT'S WORKING

✅ **Fully Working**
- Email signup/login with JWT
- Email verification flow
- Password reset flow
- Profile management
- Job posting (recruiter only)
- Job applications (student only)
- Resume upload
- Basic resume analysis (rule-based)
- Bookmark jobs
- View applications
- Notifications model setup
- Interview prep model setup

🟡 **Partially Working**
- External job fetching (needs API keys)
- ATS resume analysis (rule-based, not ML)
- Job matching (token-based, not AI)
- Career coaching (template-based, not AI)
- Chat messaging (HTTP only, WebSocket ready)
- Recruiter dashboard (model exists, limited functionality)

❌ **Not Working**
- OpenAI/Gemini LLM features
- Google/LinkedIn OAuth
- Email OTP verification
- PDF resume generation
- Real-time WebSocket chat
- GitHub integration
- Skill badge verification
- Dark mode persistence
- Most advanced AI features

---

## RECOMMENDATIONS FOR NEXT STEPS

### Immediate (High ROI)
1. **Connect OpenAI API** → Enhance AI resume analysis & recommendations
2. **Setup Email OTP** → Add OTP verification endpoint
3. **Add Google OAuth** → Enable 1-click signup/login
4. **Generate Resume PDFs** → Use reportlab/pdfkit for downloads

### Short-term (Next Week)
5. **Real-time Chat** → Complete WebSocket implementation
6. **Comprehensive Tests** → Add test coverage for critical paths
7. **Error Handling** → Standardize error responses
8. **Validation** → Add input validation on all endpoints

### Medium-term (Production Ready)
9. **PostgreSQL Migration** → Production database
10. **Rate Limiting** → Protect API from abuse
11. **Caching** → Redis for frequently accessed data
12. **Monitoring** → Error tracking & logging

