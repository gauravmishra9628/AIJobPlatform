import axios from "axios";

const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");
const API_AUTH_BASE = (
  import.meta.env.VITE_API_AUTH_BASE ||
  (API_URL ? `${API_URL}/api/auth` : "/api/auth")
).replace(/\/$/, "");
const API_JOBS_BASE = (
  import.meta.env.VITE_API_JOBS_BASE ||
  (API_URL ? `${API_URL}/api/jobs` : "/api/jobs")
).replace(/\/$/, "");

const api = axios.create({
  baseURL: API_URL || undefined,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

let refreshInFlight = null;
const responseCache = new Map();
const DEFAULT_CACHE_TTL = 60 * 1000;

function cacheKey(url, params = {}) {
  const query = new URLSearchParams(params).toString();
  return query ? `${url}?${query}` : url;
}

async function cachedGet(url, { headers = {}, params = {}, ttl = DEFAULT_CACHE_TTL } = {}) {
  const key = cacheKey(url, params);
  const cached = responseCache.get(key);
  if (cached && Date.now() - cached.createdAt < ttl) {
    return cached.data;
  }

  const { data } = await api.get(url, { headers, params });
  responseCache.set(key, { data, createdAt: Date.now() });
  return data;
}

export function clearApiCache() {
  responseCache.clear();
}

function getStoredTokens() {
  const raw = localStorage.getItem("aijob_tokens");
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function setStoredTokens(tokens) {
  if (!tokens) {
    localStorage.removeItem("aijob_tokens");
    return;
  }
  localStorage.setItem("aijob_tokens", JSON.stringify(tokens));
}

function getStoredUser() {
  const raw = localStorage.getItem("aijob_user");
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function setStoredUser(user) {
  if (!user) {
    localStorage.removeItem("aijob_user");
    return;
  }
  localStorage.setItem("aijob_user", JSON.stringify(user));
}

function withAuthHeaders() {
  const access = getStoredTokens()?.access;
  return access ? { Authorization: `Bearer ${access}` } : {};
}

async function refreshTokenInternal() {
  if (refreshInFlight) {
    return refreshInFlight;
  }

  const tokens = getStoredTokens();
  if (!tokens?.refresh) {
    throw new Error("No refresh token found.");
  }

  refreshInFlight = api
    .post(`${API_AUTH_BASE}/token/refresh/`, { refresh: tokens.refresh })
    .then(({ data }) => {
      if (data?.tokens) {
        setStoredTokens(data.tokens);
      }
      return data;
    })
    .finally(() => {
      refreshInFlight = null;
    });

  return refreshInFlight;
}

async function withSecureAuth(requestFn) {
  try {
    return await requestFn(withAuthHeaders());
  } catch (error) {
    if (error?.response?.status !== 401) {
      throw toError(error);
    }

    try {
      await refreshTokenInternal();
      return await requestFn(withAuthHeaders());
    } catch (refreshError) {
      setStoredTokens(null);
      throw toError(refreshError);
    }
  }
}

function toError(error) {
  const detail =
    error?.response?.data?.detail ||
    error?.response?.data?.email ||
    error?.response?.data?.password ||
    error?.message ||
    "Request failed.";
  return new Error(Array.isArray(detail) ? detail.join(", ") : String(detail));
}

export async function signup(data) {
  try {
    const { data: payload } = await api.post(`${API_AUTH_BASE}/signup/`, data);
    return payload;
  } catch (error) {
    throw toError(error);
  }
}

export async function login(data) {
  try {
    const { data: payload } = await api.post(`${API_AUTH_BASE}/login/`, data);
    if (payload?.tokens) {
      setStoredTokens(payload.tokens);
    }
    if (payload?.user) {
      setStoredUser(payload.user);
    }
    return payload;
  } catch (error) {
    throw toError(error);
  }
}

export async function refreshToken() {
  try {
    const payload = await refreshTokenInternal();
    if (payload?.tokens) {
      setStoredTokens(payload.tokens);
    }
    return payload;
  } catch (error) {
    throw toError(error);
  }
}

export async function getProfile() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_AUTH_BASE}/me/`, {
      headers,
    })
  );
  return data;
}

export async function updateProfile(profileData) {
  const { data } = await withSecureAuth((headers) =>
    api.patch(`${API_AUTH_BASE}/profile/`, profileData, {
      headers,
    })
  );
  clearApiCache();
  return data;
}

export async function getPublicProfile(userId) {
  const { data } = await api.get(`${API_AUTH_BASE}/profile/${userId}/`);
  return data;
}

export async function getUserBadges(userId) {
  const { data } = await api.get(`${API_AUTH_BASE}/users/${userId}/badges/`);
  return data;
}

export async function verifySkillBadge(userId, payload) {
  const { data } = await api.post(`${API_AUTH_BASE}/users/${userId}/badges/`, payload);
  return data;
}

export async function uploadSkillCertificate(userId, formData) {
  const { data } = await api.post(`${API_AUTH_BASE}/badges/upload/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function connectGitHubBadges() {
  const { data } = await api.post(`${API_AUTH_BASE}/badges/connect-github/`);
  return data;
}

export async function logout() {
  try {
    await api.post(
      `${API_AUTH_BASE}/logout/`,
      {},
      {
        headers: withAuthHeaders(),
      }
    );
  } catch {
    // Ignore logout API failures and always clear local tokens.
  } finally {
    setStoredTokens(null);
    setStoredUser(null);
  }
}

export async function listJobs() {
  return withSecureAuth((headers) => cachedGet(`${API_JOBS_BASE}/`, { headers, ttl: 30 * 1000 }));
}

export async function createJob(jobData) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/`, jobData, {
      headers,
    })
  );
  clearApiCache();
  return data;
}

export async function updateJob(jobId, jobData) {
  const { data } = await withSecureAuth((headers) =>
    api.patch(`${API_JOBS_BASE}/${jobId}/`, jobData, {
      headers,
    })
  );
  clearApiCache();
  return data;
}

export async function deleteJob(jobId) {
  const { data } = await withSecureAuth((headers) =>
    api.delete(`${API_JOBS_BASE}/${jobId}/`, {
      headers,
    })
  );
  clearApiCache();
  return data;
}

export async function myJobs() {
  return withSecureAuth((headers) => cachedGet(`${API_JOBS_BASE}/my/`, { headers, ttl: 30 * 1000 }));
}

export async function applyToJob(jobId, application = "") {
  const payload =
    typeof application === "string"
      ? { cover_note: application }
      : {
          cover_note: application.cover_note || "",
          candidate_summary: application.candidate_summary || "",
          portfolio_url: application.portfolio_url || "",
          expected_salary: application.expected_salary || "",
        };

  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/${jobId}/apply/`,
      payload,
      {
        headers,
      }
    )
  );
  clearApiCache();
  return data;
}

export async function autoApplyJobs(payload = {}) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/applications/auto-apply/`, payload, { headers })
  );
  clearApiCache();
  return data;
}

export async function listApplications() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/applications/`, {
      headers,
    })
  );
  return data;
}

export async function getCandidateLeaderboard() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/leaderboard/`, { headers })
  );
  return data;
}

export async function updateApplicationStatus(applicationId, status) {
  const { data } = await withSecureAuth((headers) =>
    api.patch(
      `${API_JOBS_BASE}/applications/${applicationId}/`,
      { status },
      {
        headers,
      }
    )
  );
  clearApiCache();
  return data;
}

export async function uploadResume(file) {
  const formData = new FormData();
  formData.append("resume", file);

  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/resume/upload/`, formData, {
      headers: {
        ...headers,
        "Content-Type": "multipart/form-data",
      },
    })
  );
  clearApiCache();
  return data;
}

export async function latestResume() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/resume/latest/`, {
      headers,
    })
  );
  return data;
}

export async function getRecommendations() {
  return withSecureAuth((headers) => cachedGet(`${API_JOBS_BASE}/recommendations/`, { headers, ttl: 45 * 1000 }));
}

export async function getCareerGuidance() {
  return withSecureAuth((headers) => cachedGet(`${API_JOBS_BASE}/career-guidance/`, { headers, ttl: 45 * 1000 }));
}

export async function listMessages() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/messages/`, {
      headers,
    })
  );
  return data;
}

export async function sendMessage(recipientId, body) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/messages/`,
      { recipient_id: recipientId, body },
      {
        headers,
      }
    )
  );
  return data;
}

export async function resendVerification(email) {
  try {
    const { data } = await api.post(`${API_AUTH_BASE}/verify-email/resend/`, { email });
    return data;
  } catch (error) {
    throw toError(error);
  }
}

export async function verifyEmail(token) {
  try {
    const { data } = await api.get(`${API_AUTH_BASE}/verify-email/${token}/`);
    return data;
  } catch (error) {
    throw toError(error);
  }
}

export async function forgotPassword(email) {
  try {
    const { data } = await api.post(`${API_AUTH_BASE}/password/forgot/`, { email });
    return data;
  } catch (error) {
    throw toError(error);
  }
}

export async function resetPassword(token, password) {
  try {
    const { data } = await api.post(`${API_AUTH_BASE}/password/reset/${token}/`, { password });
    return data;
  } catch (error) {
    throw toError(error);
  }
}

// ========== ATS SCORING API ==========
export async function analyzeResumeAts(resumeId, jobId = null) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/resume/analyze-ats/`,
      { resume_id: resumeId, job_id: jobId },
      { headers }
    )
  );
  return data;
}

export async function getAtsScore(scoreId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/ats-score/${scoreId}/`, { headers })
  );
  return data;
}

// ========== JOB BOOKMARKS API ==========
export async function bookmarkJob(jobId, action = "add", notes = "") {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/bookmarks/toggle/`,
      { job_id: jobId, action, notes },
      { headers }
    )
  );
  return data;
}

export async function listBookmarks() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/bookmarks/`, { headers })
  );
  return data;
}

// ========== APPLICATION TRACKING API ==========
export async function updateApplicationStage(appId, stage, notes = "") {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/applications/stage/update/`,
      { application_id: appId, stage, notes },
      { headers }
    )
  );
  return data;
}

export async function getApplicationHistory(appId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/applications/${appId}/history/`, { headers })
  );
  return data;
}

// ========== SKILL GAP ANALYSIS API ==========
export async function analyzeSkillGap(targetRole) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/skill-gap/analyze/`,
      { target_role: targetRole },
      { headers }
    )
  );
  return data;
}

export async function getSkillGap() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/skill-gap/`, { headers })
  );
  return data;
}

// ========== NOTIFICATIONS API ==========
export async function listNotifications(unread = false) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/notifications/?unread=${unread}`, { headers })
  );
  return data;
}

export async function markNotificationRead(notificationId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/notifications/mark-read/`,
      { notification_id: notificationId },
      { headers }
    )
  );
  return data;
}

// ========== INTERVIEW PREPARATION API ==========
export async function generateInterviewPrep(appId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/interview-prep/generate/`,
      { application_id: appId },
      { headers }
    )
  );
  return data;
}

export async function getInterviewPrep(prepId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/interview-prep/${prepId}/`, { headers })
  );
  return data;
}

// ========== RECRUITER ANALYTICS API ==========
export async function getRecruiterAnalytics() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/analytics/`, { headers })
  );
  return data;
}

export async function getHiringTrends(days = 30) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/analytics/trends/?days=${days}`, { headers })
  );
  return data;
}

// ========== RECRUITER ASSISTANT API ==========
export async function submitRecruiterQuery(queryText) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/recruiter/query/`,
      { query_text: queryText },
      { headers }
    )
  );
  return data;
}

export async function refineRecruiterQuery(queryId, payload = {}) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/recruiter/query/${queryId}/refine/`, payload, { headers })
  );
  return data;
}

export async function autoShortlistCandidates(jobId, count = 10) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/recruiter/shortlist/auto/`, { job_id: jobId, count }, { headers })
  );
  return data;
}

export async function getRecruiterQueryPatterns() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/recruiter/analytics/query-patterns/`, { headers })
  );
  return data;
}

// ========== AI RESUME ANALYZER API ==========
export async function analyzeResumeAI(resumeId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/resume/analyze-ai/`,
      { resume_id: resumeId },
      { headers }
    )
  );
  return data;
}

export async function getResumeAnalysis(resumeId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/resume/${resumeId}/ai-analysis/`, { headers })
  );
  return data;
}

// ========== AI MATCH SCORING API ==========
export async function calculateAIMatch(jobId, resumeId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/match/calculate/`,
      { job_id: jobId, resume_id: resumeId },
      { headers }
    )
  );
  return data;
}

export async function getJobMatches(jobId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/jobs/${jobId}/matches/`, { headers })
  );
  return data;
}

// ========== AI CAREER COACH API ==========
export async function generateCareerPlan(targetRole, currentLevel, goals = "") {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/career/plan/`,
      { target_role: targetRole, current_level: currentLevel, goals },
      { headers }
    )
  );
  return data;
}

export async function generateAIInterviewQuestions(payload) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/career/interview-questions/`, payload, { headers })
  );
  return data;
}

export async function getCareerCoach() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/coach/`, { headers })
  );
  return data;
}

export async function getCareerPathPrediction() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/predict/`, { headers })
  );
  return data;
}

export async function getCareerTimeline() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/timeline/`, { headers })
  );
  return data;
}

export async function getPersonalityDevelopmentCoach() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/personality-coach/`, { headers })
  );
  return data;
}

export async function getInteractiveCareerSimulationEngine() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/simulation-engine/`, { headers })
  );
  return data;
}

export async function getSmartInternshipPerformanceEvaluation() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/internship-performance/`, { headers })
  );
  return data;
}

export async function getInternshipAttendanceTracking() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/attendance-tracking/`, { headers })
  );
  return data;
}

export async function getNetworkingSuggestions() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/networking-suggestions/`, { headers })
  );
  return data;
}

export async function getInternshipRoadmap() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/internship-roadmap/`, { headers })
  );
  return data;
}

export async function getCandidateReputationScore() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/reputation-score/`, { headers })
  );
  return data;
}

export async function getTeamRecommendations() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/team-recommendations/`, { headers })
  );
  return data;
}

export async function optimizeResumeKeywords() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/resume/optimize-keywords/`, { headers })
  );
  return data;
}

export async function detectFakeResume() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/resume/fake-detection/`, { headers })
  );
  return data;
}

export async function translateResume(targetLanguage = "es") {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/resume/translate/`,
      { target_language: targetLanguage },
      { headers }
    )
  );
  return data;
}

export async function getHiringHeatmap() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/market/hiring-heatmap/`, { headers })
  );
  return data;
}

export async function getCollaborativeProjectBuilder() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/projects/collaborative-builder/`, { headers })
  );
  return data;
}

export async function getAutomatedInterviewTranscriptGenerator(role = "Software Engineer") {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/interview/transcript-generator/`, {
      headers,
      params: { role },
    })
  );
  return data;
}

export async function simulateVoiceInterview(role, transcript) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/interview/voice-simulator/`,
      { role, transcript },
      { headers }
    )
  );
  return data;
}

export async function analyzeMockInterview(payload) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/interview/mock-analyze/`, payload, { headers })
  );
  return data;
}

export async function simulateGroupDiscussion(topic, candidateResponse) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/interview/gd-simulator/`,
      { topic, candidate_response: candidateResponse },
      { headers }
    )
  );
  return data;
}

export async function evaluateCompetitiveCoding(payload) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/coding/evaluate/`, payload, { headers })
  );
  return data;
}

export async function getAiTimeManagementAnalyzer() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/productivity/time-management/`, { headers })
  );
  return data;
}

export async function getRecruiterTrustBadge() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/recruiter/trust-badge/`, { headers })
  );
  return data;
}

export async function getPersonalBrandingAssistant() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/branding/assistant/`, { headers })
  );
  return data;
}

export async function generateCoverLetter(payload) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/career/cover-letter/`, payload, { headers })
  );
  return data;
}

export async function predictSalary(payload = {}) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/career/salary-prediction/`, payload, { headers })
  );
  return data;
}

// ========== SMART CAREER GRAPH API ==========

export async function getCareerGraph() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/graph/`, { headers })
  );
  return data;
}

export async function getCareerPaths() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/career/paths/`, { headers })
  );
  return data;
}

export async function generateCareerPath(targetRole) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/career/path/generate/`, { target_role: targetRole }, { headers })
  );
  return data;
}

export async function updateSkillProgress(skillId, progress, milestones = []) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/career/skill/update-progress/`,
      { skill_id: skillId, progress, milestones },
      { headers })
  );
  return data;
}

export async function getSkillNodes(category = "") {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/skills/`, { headers, params: category ? { category } : {} })
  );
  return data;
}

// ========== RESUME vs JOB COMPARATOR ==========

export async function compareResumeJob(resumeId, jobId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/compare/resume-job/`,
      { resume_id: resumeId, job_id: jobId },
      { headers })
  );
  return data;
}

// ========== RECRUITER CANDIDATE SEARCH ==========

export async function searchRecruiterCandidates(query = "", filters = {}) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/recruiter/candidates/`,
      { headers, params: { q: query, ...filters } })
  );
  return data;
}

// ========== AI CODING TEST PLATFORM ==========

export async function getCodingQuestions(filters = {}) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/coding/questions/`, { headers, params: filters })
  );
  return data;
}

export async function getCodingQuestionDetail(questionId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/coding/questions/${questionId}/`, { headers })
  );
  return data;
}

export async function submitCode(questionId, code, language) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/coding/submit/`,
      { question_id: questionId, code, language },
      { headers })
  );
  return data;
}

export async function getCodeSubmissions(userId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/coding/submissions/`, { headers, params: { user_id: userId } })
  );
  return data;
}

export async function getCodingContests() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/coding/contests/`, { headers })
  );
  return data;
}

export async function joinContest(contestId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/coding/contests/${contestId}/join/`, {}, { headers })
  );
  return data;
}

export async function getContestLeaderboard(contestId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/coding/contests/${contestId}/leaderboard/`, { headers })
  );
  return data;
}

// ========== VOICE CAREER COACH ==========

export async function startVoiceSession(sessionType) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/voice/session/start/`, { session_type: sessionType }, { headers })
  );
  return data;
}

export async function processVoiceTranscript(sessionId, transcript) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/voice/transcript/process/`,
      { session_id: sessionId, transcript },
      { headers })
  );
  return data;
}

export async function endVoiceSession(sessionId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/voice/session/end/`, { session_id: sessionId }, { headers })
  );
  return data;
}

export async function getVoiceSessions() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/voice/sessions/`, { headers })
  );
  return data;
}

// ========== PERSONALITY ANALYZER ==========

export async function analyzePersonality(userId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/personality/analyze/`, { user_id: userId }, { headers })
  );
  return data;
}

export async function getPersonalityProfile(userId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/personality/profile/${userId}/`, { headers })
  );
  return data;
}

// ========== GAMIFICATION SYSTEM ==========

export async function getGameProfile() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/game/profile/`, { headers })
  );
  return data;
}

export async function awardXP(activityType) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/game/xp/award/`, { activity_type: activityType }, { headers })
  );
  return data;
}

export async function getGameLeaderboard(timeframe = "all") {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/game/leaderboard/`, { headers, params: { timeframe } })
  );
  return data;
}

export async function getDailyChallenges() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/game/challenges/daily/`, { headers })
  );
  return data;
}

export async function completeChallenge(challengeId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/game/challenges/complete/`, { challenge_id: challengeId }, { headers })
  );
  return data;
}

// ========== ADVANCED SEARCH ==========

export async function advancedJobSearch(query, filters = {}) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/search/`, { headers, params: { q: query, ...filters } })
  );
  return data;
}

export async function getSearchSuggestions(prefix) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/search/suggestions/`, { headers, params: { prefix } })
  );
  return data;
}

// ========== AI AUTO APPLY ==========

export async function setAutoApplyPreferences(prefs) {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/auto-apply/preferences/`, prefs, { headers })
  );
  return data;
}

export async function getAutoApplyPreferences() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/auto-apply/preferences/get/`, { headers })
  );
  return data;
}

export async function getAutoApplyHistory() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/auto-apply/history/`, { headers })
  );
  return data;
}

export async function getCompanyProfile(companyId) {
  const { data } = await api.get(`/api/companies/${companyId}/`);
  return data;
}

export async function listCompanies(query = "") {
  return cachedGet("/api/companies/", { params: query ? { q: query } : {}, ttl: 60 * 1000 });
}

export async function submitCompanyReview(companyId, review) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `/api/companies/${companyId}/reviews/`,
      review,
      { headers }
    )
  );
  return data;
}

export async function getCompanyBadge(companyId) {
  const { data } = await api.get(`/api/companies/${companyId}/badge/`);
  return data;
}

// ========== REAL CHAT API ==========
export async function sendChatMessage(recipientId, message) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/chat/send/`,
      { recipient_id: recipientId, message },
      { headers }
    )
  );
  return data;
}

export async function getChatMessages(userId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/chat/${userId}/`, { headers })
  );
  return data;
}

export async function getChatList() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/chat/list/`, { headers })
  );
  return data;
}

// ========== RECRUITER DASHBOARD API ==========
export async function getRecruiterDashboard() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/dashboard/`, { headers })
  );
  return data;
}

export async function updateRecruiterDashboard(updates) {
  const { data } = await withSecureAuth((headers) =>
    api.put(`${API_JOBS_BASE}/dashboard/update/`, updates, { headers })
  );
  return data;
}

// ========== AI RESUME MATCH SCORE API ==========
export async function uploadMatchResume(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/resume/match/upload/`, formData, {
      headers: {
        ...headers,
        'Content-Type': 'multipart/form-data'
      }
    })
  );
  clearApiCache();
  return data;
}

export async function calculateResumeMatch(resumeId, jobDescription) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/resume/match/calculate/`,
      {
        resume_id: resumeId,
        job_description: jobDescription
      },
      { headers }
    )
  );
  return data;
}

export async function getUserResumes() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/resume/match/list/`, { headers })
  );
  return data;
}

export async function getResumeMatches(resumeId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/resume/${resumeId}/matches/`, { headers })
  );
  return data;
}

export async function getMatchDetails(matchId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/resume-match/${matchId}/`, { headers })
  );
  return data;
}

export async function uploadComparatorResume(file) {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await withSecureAuth((headers) =>
    api.post("/api/resume/upload/", formData, {
      headers: {
        ...headers,
        "Content-Type": "multipart/form-data",
      },
    })
  );
  clearApiCache();
  return data;
}

export async function compareResumeToJob(resumeId, jobId, asyncProcess = false) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      "/api/compare/",
      { resume_id: resumeId, job_id: jobId, async_process: asyncProcess },
      { headers }
    )
  );
  return data;
}

export async function aiMatchResumeToJob(resumeId, jobId) {
  const { data } = await withSecureAuth((headers) =>
    api.post("/api/ai/match/", { resume_id: resumeId, job_id: jobId }, { headers })
  );
  return data;
}

export async function getComparatorSkillGap(payload) {
  const { data } = await withSecureAuth((headers) =>
    api.post("/api/skill-gap/", payload, { headers })
  );
  return data;
}

export async function predictComparatorSalary(payload) {
  const { data } = await withSecureAuth((headers) =>
    api.post("/api/salary-predict/", payload, { headers })
  );
  return data;
}

export async function saveFavoriteJob(jobId, action = "add") {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/dashboard/favorite/`,
      { job_id: jobId, action },
      { headers }
    )
  );
  return data;
}

export function hasSession() {
  return Boolean(getStoredTokens()?.access);
}

export function getAuthenticatedUser() {
  return getStoredUser();
}

// ========== NEW FEATURE API HELPERS ==========

// 1. External Jobs API
export async function fetchExternalJobs(query, location = "", jobType = "", source = "all") {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/external-jobs/`, {
      params: { q: query, location, type: jobType, source },
      headers,
    })
  );
  return data;
}

// 2. Authentication Features
export async function sendEmailOTP(email) {
  const { data } = await api.post(`${API_JOBS_BASE}/auth/send-otp/`, { email });
  return data;
}

export async function verifyEmailOTP(email, otp, password, role = "student") {
  const { data } = await api.post(`${API_JOBS_BASE}/auth/verify-otp/`, {
    email,
    otp,
    password,
    role,
  });
  return data;
}

export async function sendPasswordResetEmail(email) {
  const { data } = await api.post(`${API_JOBS_BASE}/auth/forgot-password/`, { email });
  return data;
}

export async function resetPasswordViaJobsApi(token, newPassword) {
  const { data } = await api.post(`${API_JOBS_BASE}/auth/reset-password/`, {
    token,
    new_password: newPassword,
  });
  return data;
}

// 3. Dashboards
export async function getLiveRecruiterDashboard() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/recruiter/dashboard/`, { headers })
  );
  return data;
}

export async function getStudentDashboard() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/student/dashboard/`, { headers })
  );
  return data;
}

// 4. Resume PDF
export async function generateResumePDF(templateData, style = "modern") {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/resume/generate-pdf/`,
      { template: templateData, style },
      { headers }
    )
  );
  return data;
}

// 5. Admin Analytics
export async function getAdminAnalytics() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/admin/analytics/`, { headers })
  );
  return data;
}

// 6. Theme Toggle
export async function toggleTheme(theme) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/user/toggle-theme/`,
      { theme },
      { headers }
    )
  );
  return data;
}

// 7. Notifications
export async function getUserNotifications() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/user/notifications/`, { headers })
  );
  return data;
}

export async function markNotificationReadViaJobsApi(notificationId) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/user/notifications/mark-read/`,
      { notification_id: notificationId },
      { headers }
    )
  );
  return data;
}

// 8. Chat
export async function getChatHistory(recipientId) {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/chat/history/${recipientId}/`, { headers })
  );
  return data;
}

export async function getBillingOverview() {
  const { data } = await withSecureAuth((headers) =>
    api.get(`${API_JOBS_BASE}/billing/overview/`, { headers })
  );
  return data;
}

export async function createBillingCheckout(plan, provider = "stripe") {
  const { data } = await withSecureAuth((headers) =>
    api.post(`${API_JOBS_BASE}/billing/checkout/`, { plan, provider }, { headers })
  );
  return data;
}

export async function confirmBillingCheckout(transactionId, providerPayload = {}) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/billing/checkout/confirm/`,
      { transaction_id: transactionId, ...providerPayload },
      { headers }
    )
  );
  return data;
}

export async function recordUsage(usageType = "ai", amount = 1, metadata = {}) {
  const { data } = await withSecureAuth((headers) =>
    api.post(
      `${API_JOBS_BASE}/billing/usage/`,
      { usage_type: usageType, amount, metadata },
      { headers }
    )
  );
  return data;
}

export default api;
