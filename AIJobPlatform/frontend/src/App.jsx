import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import { AnimatePresence, motion } from "framer-motion";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  analyzeSkillGap,
  applyToJob,
  calculateAIMatch,
  confirmBillingCheckout,
  createJob,
  createBillingCheckout,
  detectFakeResume,
  deleteJob,
  forgotPassword,
  getBillingOverview,
  getCandidateReputationScore,
  getCareerGuidance,
  getCareerTimeline,
  getCollaborativeProjectBuilder,
  getInternshipRoadmap,
  getInternshipAttendanceTracking,
  getInteractiveCareerSimulationEngine,
  getNetworkingSuggestions,
  getCareerPathPrediction,
  getCareerCoach,
  getPersonalityDevelopmentCoach,
  getPersonalBrandingAssistant,
  getSmartInternshipPerformanceEvaluation,
  getAutomatedInterviewTranscriptGenerator,
  getAiTimeManagementAnalyzer,
  generateAIInterviewQuestions,
  generateResumePDF,
  uploadSkillCertificate,
  connectGitHubBadges,
  listCompanies,
  getProfile,
  getRecommendations,
  getTeamRecommendations,
  hasSession,
  latestResume,
  listApplications,
  listJobs,
  listMessages,
  login,
  logout,
  myJobs,
  refreshToken,
  resendVerification,
  resetPassword,
  simulateVoiceInterview,
  signup,
  optimizeResumeKeywords,
  updateJob,
  updateProfile,
  updateApplicationStatus,
  uploadResume,
  verifyEmail,
  sendMessage,
} from "./api";
import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";
import ResumeMatch from "./components/ResumeMatch";
import ResumeJobComparator from "./components/ResumeJobComparator";
import RecruiterAnalytics from "./components/RecruiterAnalytics";
import PublicProfilePage from "./components/PublicProfilePage";
import CandidateLeaderboard from "./components/CandidateLeaderboard";
import AutoApplyPanel from "./components/AutoApplyPanel";
import RecruiterAssistant from "./components/RecruiterAssistant";

const CompanyProfile = lazy(() => import("./components/CompanyProfile"));

const initialSignup = {
  email: "",
  password: "",
  first_name: "",
  last_name: "",
  role: "student",
  university_name: "",
  company_name: "",
};

const initialLogin = {
  email: "",
  password: "",
};

const initialJob = {
  title: "",
  company: "",
  location: "",
  description: "",
  skills_required: "",
  employment_type: "full-time",
  salary_range: "",
};

const emptyProfile = {
  headline: "",
  location: "",
  bio: "",
  about: "",
  skills: "",
  github_url: "",
  linkedin_url: "",
};

const fallbackJobs = [
  {
    id: "sample-1",
    title: "AI Product Engineer",
    company: "NovaWorks",
    location: "Bengaluru Hybrid",
    employment_type: "full-time",
    salary_range: "18-28 LPA",
    skills_required: "React, Python, LLM APIs, Product Thinking",
    description:
      "Build intelligent workflow features, ship clean user experiences, and partner with recruiters to turn hiring signals into useful product loops.",
    match_score: 11,
    is_active: true,
  },
  {
    id: "sample-2",
    title: "Machine Learning Intern",
    company: "SkillForge Labs",
    location: "Remote",
    employment_type: "internship",
    salary_range: "25k/month",
    skills_required: "Python, NLP, FastAPI, SQL",
    description:
      "Prototype resume ranking experiments, evaluate candidate-job fit, and turn research notebooks into dependable backend services.",
    match_score: 8,
    is_active: true,
  },
  {
    id: "sample-3",
    title: "Talent Intelligence Associate",
    company: "HireSignal",
    location: "Mumbai",
    employment_type: "contract",
    salary_range: "Competitive",
    skills_required: "Sourcing, Analytics, Communication, ATS",
    description:
      "Curate talent pools, summarize candidate strengths, and help hiring teams move faster with data-backed shortlists.",
    match_score: 6,
    is_active: true,
  },
];

const storyCards = [
  {
    name: "Aarav Menon",
    title: "Backend Developer",
    text: "Used AI match notes to rewrite my profile around Django, APIs, and cloud projects. Recruiter replies finally started making sense.",
  },
  {
    name: "Priya Shah",
    title: "Campus Recruiter",
    text: "The pipeline view makes early talent hiring feel lighter. I can post roles, compare fit, and keep the team aligned in one place.",
  },
];

const featureCards = [
  {
    title: "Smart authentication",
    summary: "Secure signup, login, token refresh, email verification, and role-aware routes keep the platform protected end to end.",
    meta: ["JWT auth", "Email verification", "Protected routes"],
    route: "/signup",
    cta: "Get started",
  },
  {
    title: "Resume intelligence",
    summary: "Upload a resume, extract skills and experience, and surface ATS-style insights with improvement notes.",
    meta: ["Resume upload", "Skills extraction", "ATS insights"],
    route: "/dashboard/student",
    cta: "Open student studio",
  },
  {
    title: "Job match scoring",
    summary: "Compare resumes and job descriptions with AI-style scoring so candidates and recruiters see fit at a glance.",
    meta: ["Compatibility score", "Skill overlap", "Job recommendations"],
    route: "/dashboard/student",
    cta: "Review matches",
  },
  {
    title: "Career coach and roadmap",
    summary: "Generate personalized growth guidance, learning roadmaps, and next-step recommendations from profile signals.",
    meta: ["Career guidance", "Roadmaps", "Growth insights"],
    route: "/dashboard/student",
    cta: "See guidance",
  },
  {
    title: "Recruiter operations",
    summary: "Post jobs, review applicants, shortlist candidates, and manage hiring progress from a single recruiter console.",
    meta: ["Job posting", "Candidate review", "Hiring workflow"],
    route: "/recruiter/dashboard",
    cta: "Open recruiter tools",
  },
  {
    title: "Tracking, chat, and alerts",
    summary: "Monitor application stages, exchange messages in real time, and keep users informed with live notifications.",
    meta: ["Applications", "Messaging", "Notifications"],
    route: "/dashboard",
    cta: "View activity",
  },
  {
    title: "Advanced AI interview suite",
    summary: "Run webcam mock interviews, coding rounds, resume building, profile import, certificate checks, and career roadmaps.",
    meta: ["WebRTC", "Monaco-ready coding", "AI scorecards"],
    route: "/advanced-ai",
    cta: "Open AI suite",
  },
  {
    title: "Premium SaaS command center",
    summary: "Search the product, review activity, inspect usage charts, and manage Free, Premium, or Recruiter subscriptions.",
    meta: ["Framer Motion", "Recharts", "Stripe/Razorpay"],
    route: "/saas",
    cta: "Open SaaS console",
  },
];

function field(label, value, onChange, type = "text", required = false, placeholder = "") {
  return (
    <label className="field">
      <span>{label}</span>
      <input value={value} onChange={onChange} type={type} required={required} placeholder={placeholder} />
    </label>
  );
}

function textareaField(label, value, onChange, required = false, placeholder = "") {
  return (
    <label className="field">
      <span>{label}</span>
      <textarea value={value} onChange={onChange} required={required} placeholder={placeholder} />
    </label>
  );
}

function suggestRequirementsFromCompany(company) {
  const industry = String(company?.industry || "").toLowerCase();
  const base = ["Communication", "Problem Solving", "Collaboration"];
  if (industry.includes("software") || industry.includes("tech") || industry.includes("it")) {
    return ["React", "Django", "REST APIs", "SQL", ...base];
  }
  if (industry.includes("data") || industry.includes("analytics")) {
    return ["Python", "SQL", "Data Analysis", "Dashboards", ...base];
  }
  if (industry.includes("design") || industry.includes("product")) {
    return ["Figma", "User Research", "Prototyping", "Product Thinking", ...base];
  }
  return ["Python", "JavaScript", "SQL", ...base];
}

function initials(profile) {
  const user = profile?.user;
  const name = `${user?.first_name || ""} ${user?.last_name || ""}`.trim();
  if (!name) {
    return (user?.email || "AI").slice(0, 2).toUpperCase();
  }
  return name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function displayName(profile) {
  const user = profile?.user;
  const name = `${user?.first_name || ""} ${user?.last_name || ""}`.trim();
  return name || user?.email || "AIJob member";
}

function splitList(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function useDebouncedValue(value, delay = 350) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => setDebouncedValue(value), delay);
    return () => window.clearTimeout(timeoutId);
  }, [value, delay]);

  return debouncedValue;
}

function SkeletonStack({ count = 3 }) {
  return (
    <div className="jobStack" aria-label="Loading">
      {Array.from({ length: count }).map((_, index) => (
        <article className="jobCard skeletonCard" key={index}>
          <div className="skeletonLine short" />
          <div className="skeletonLine" />
          <div className="skeletonLine medium" />
          <div className="chipRow">
            <span className="skeletonPill" />
            <span className="skeletonPill" />
          </div>
        </article>
      ))}
    </div>
  );
}

function EmptyState({ title, body, action }) {
  return (
    <div className="emptyPanel">
      <strong>{title}</strong>
      <p>{body}</p>
      {action}
    </div>
  );
}

function parseSalaryBand(rawValue) {
  if (!rawValue) {
    return null;
  }

  const text = String(rawValue).toLowerCase();
  const numbers = Array.from(text.matchAll(/\d+(?:\.\d+)?/g)).map((match) => Number(match[0]));
  if (!numbers.length) {
    return null;
  }

  const baseMin = numbers[0];
  const baseMax = numbers.length > 1 ? numbers[1] : numbers[0];
  const annualize = (amount) => {
    if (text.includes("cr")) {
      return amount * 10000000;
    }
    if (text.includes("lpa") || text.includes("lakh")) {
      return amount * 100000;
    }
    if (text.includes("/month") || text.includes("per month") || text.includes("month") || text.includes("pm")) {
      return amount * 12 * (text.includes("k") ? 1000 : 1);
    }
    if (text.includes("k")) {
      return amount * 1000;
    }
    return amount;
  };

  return {
    min: annualize(baseMin),
    max: annualize(baseMax),
  };
}

function formatAnnualSalary(amount) {
  if (!amount || Number.isNaN(amount)) {
    return "Not enough data";
  }
  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(1)} Cr`;
  }
  if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(1)} LPA`;
  }
  if (amount >= 1000) {
    return `₹${Math.round(amount / 1000)}k`;
  }
  return `₹${Math.round(amount)}`;
}

function estimateSalaryPrediction({ jobs, profile, resume, careerCoach }) {
  const userSkills = new Set([
    ...splitList(profile?.profile?.skills),
    ...(resume?.extracted_skills || []),
    ...splitList(careerCoach?.skills),
  ].map((skill) => skill.toLowerCase()));
  const locationHint = String(profile?.profile?.location || profile?.user?.company_name || "").toLowerCase();

  const scoredJobs = (jobs || [])
    .map((job) => {
      const salaryBand = parseSalaryBand(job.salary_range);
      if (!salaryBand) {
        return null;
      }

      const jobSkills = splitList(job.skills_required).map((skill) => skill.toLowerCase());
      const overlap = jobSkills.filter((skill) => [...userSkills].some((userSkill) => userSkill.includes(skill) || skill.includes(userSkill))).length;
      const remoteBoost = String(job.location || "").toLowerCase().includes("remote") ? 2 : 0;
      const locationBoost = locationHint && String(job.location || "").toLowerCase().includes(locationHint) ? 3 : remoteBoost;
      const score = overlap * 3 + locationBoost;

      return {
        job,
        salaryBand,
        overlap,
        score,
      };
    })
    .filter(Boolean)
    .sort((left, right) => right.score - left.score);

  if (scoredJobs.length) {
    const topMatches = scoredJobs.slice(0, 3);
    const weightedMidpoint = topMatches.reduce((sum, item) => {
      const midpoint = (item.salaryBand.min + item.salaryBand.max) / 2;
      return sum + midpoint * (1 + Math.min(0.15, item.score * 0.03));
    }, 0) / topMatches.length;

    const spread = Math.max(weightedMidpoint * 0.12, (topMatches[0].salaryBand.max - topMatches[0].salaryBand.min) * 0.35);
    return {
      label: `${formatAnnualSalary(weightedMidpoint - spread)} - ${formatAnnualSalary(weightedMidpoint + spread)}`,
      confidence: Math.min(92, 58 + topMatches.length * 10 + Math.min(12, topMatches[0].overlap * 3)),
      basis: topMatches[0].job,
      signals: topMatches.map((item) => `${item.job.title} · ${item.job.location}`),
    };
  }

  const coachSalary = careerCoach?.salary_insights ? Object.entries(careerCoach.salary_insights)[0] : null;
  if (coachSalary) {
    return {
      label: coachSalary[1],
      confidence: 64,
      basis: { title: coachSalary[0], company: "Career coach" },
      signals: ["Using the saved career coach salary map."],
    };
  }

  return {
    label: "Upload more data to estimate salary",
    confidence: 36,
    basis: null,
    signals: ["Add skills, resume text, and location to improve the prediction."],
  };
}

function buildResumeSuggestions({ profile, resume, careerCoach }) {
  const suggestions = [];
  const analysis = resume?.analysis || {};

  if (analysis.gaps?.length) {
    suggestions.push(...analysis.gaps.slice(0, 3));
  }

  if (!resume) {
    suggestions.push("Upload a resume so the platform can extract skills, experience, and ATS signals.");
    suggestions.push("Add measurable project outcomes and tools used in each role or project.");
  } else {
    if ((resume.extracted_skills || []).length < 5) {
      suggestions.push("Add stronger keywords for tools, languages, frameworks, and business impact.");
    }
    if ((analysis.word_count || 0) < 250) {
      suggestions.push("Expand the resume with project bullets, metrics, and concrete outcomes.");
    }
  }

  const profileSkills = splitList(profile?.profile?.skills);
  if (!profile?.profile?.headline) {
    suggestions.push("Write a headline that tells recruiters the role you want and the stack you use.");
  }
  if (profileSkills.length < 5) {
    suggestions.push("List at least five focused skills so matching and salary prediction become more accurate.");
  }
  if (!profile?.profile?.github_url && !profile?.profile?.linkedin_url) {
    suggestions.push("Link GitHub or LinkedIn to prove credibility and raise recruiter confidence.");
  }
  if (careerCoach?.personalized_advice) {
    suggestions.push(careerCoach.personalized_advice);
  }

  return Array.from(new Set(suggestions)).slice(0, 5);
}

function fallbackCareerPath(profile, careerCoach) {
  const skillCount = splitList(profile?.profile?.skills).length;
  const currentLevel = skillCount >= 10 ? "mid" : "junior";
  return {
    current_level: currentLevel,
    predicted_paths: [
      { role: currentLevel === "mid" ? "Senior Engineer" : "Software Engineer", timeline: "6-12 months", confidence: 72 },
      { role: "Tech Lead", timeline: "12-24 months", confidence: 61 },
      { role: "Engineering Manager", timeline: "24-48 months", confidence: 54 },
    ],
    learning_recommendations: [
      {
        skill: "System Design",
        priority: "high",
        why: "Needed for stronger growth trajectory and hiring outcomes.",
        resources: ["Grokking System Design", "Design practice interviews"],
      },
      {
        skill: "Communication",
        priority: "medium",
        why: "Important for interviews, collaboration, and leadership progression.",
        resources: ["Mock interview practice", "Technical writing drills"],
      },
    ],
    market_insights: {
      active_jobs: 0,
      top_demanded_skills: splitList(careerCoach?.recommended_roles).slice(0, 5).map((skill) => ({ skill, openings: 0 })),
    },
  };
}

function SmartAIStudio({
  profile,
  jobs,
  resume,
  careerCoach,
  careerPathPrediction,
  internshipRoadmap,
  reputationScore,
  teamRecommendations,
  personalityCoach,
  careerSimulation,
  internshipPerformance,
  collaborativeProject,
  interviewTranscript,
  timeManagementAnalysis,
  networkingSuggestions,
  internshipTracking,
  brandingInsights,
  fakeResumeReport,
  resumeKeywordOptimization,
  onRunKeywordOptimizer,
  onRunVoiceSimulator,
  voiceInterviewResult,
  loading,
  refreshDashboard,
  navigate,
}) {
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [assistantReply, setAssistantReply] = useState("Say 'refresh', 'salary', or 'profile' to control the workspace.");
  const [voiceError, setVoiceError] = useState("");

  useEffect(() => {
    setVoiceSupported(Boolean(window.SpeechRecognition || window.webkitSpeechRecognition));
  }, []);

  const salaryPrediction = useMemo(
    () => estimateSalaryPrediction({ jobs, profile, resume, careerCoach }),
    [jobs, profile, resume, careerCoach]
  );

  const resumeSuggestions = useMemo(
    () => buildResumeSuggestions({ profile, resume, careerCoach }),
    [profile, resume, careerCoach]
  );

  const pathPrediction = useMemo(
    () => careerPathPrediction || fallbackCareerPath(profile, careerCoach),
    [careerPathPrediction, profile, careerCoach]
  );

  function speak(text) {
    if (!window.speechSynthesis) {
      return;
    }
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
  }

  function resolveVoiceCommand(rawTranscript) {
    const command = String(rawTranscript || "").toLowerCase();

    if (command.includes("refresh")) {
      refreshDashboard();
      return "Refreshing your dashboard and match data.";
    }
    if (command.includes("salary")) {
      return `Estimated salary band: ${salaryPrediction.label}. Confidence ${salaryPrediction.confidence} percent.`;
    }
    if (command.includes("career") || command.includes("path")) {
      const nextRole = pathPrediction.predicted_paths?.[0]?.role || "Software Engineer";
      return `Next likely career move is ${nextRole}. Check the roadmap section for full progression.`;
    }
    if (command.includes("profile")) {
      navigate("/profile");
      return "Opening your profile editor.";
    }
    if (command.includes("student") || command.includes("resume") || command.includes("match")) {
      navigate("/dashboard/student");
      return "Opening the student studio with resume and match tools.";
    }
    if (command.includes("recruiter") || command.includes("job")) {
      navigate("/recruiter/dashboard");
      return "Opening the recruiter console.";
    }

    return "I can refresh the dashboard, read salary predictions, or open profile and dashboard pages.";
  }

  function startVoiceAssistant() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceError("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    setVoiceError("");
    setTranscript("");
    setListening(true);

    recognition.onresult = (event) => {
      const spokenText = event.results?.[0]?.[0]?.transcript || "";
      setTranscript(spokenText);
      const response = resolveVoiceCommand(spokenText);
      setAssistantReply(response);
      speak(response);
    };

    recognition.onerror = (event) => {
      setVoiceError(event.error || "Voice input failed.");
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognition.start();
  }

  return (
    <section className="panel assistantPanel">
      <div className="sectionHeader inline">
        <div>
          <p className="eyebrow">AI tools</p>
          <h2>Salary, resume, and voice assistant</h2>
        </div>
        <button className="ghostButton fitButton" disabled={loading} onClick={refreshDashboard} type="button">
          Refresh
        </button>
      </div>

      <div className="assistantGrid">
        <article className="toolCard salaryCard">
          <div className="toolHeader">
            <h3>Salary prediction</h3>
            <span className="featurePill">Live</span>
          </div>
          <strong className="salaryValue">{salaryPrediction.label}</strong>
          <p className="muted">Confidence: {salaryPrediction.confidence}%</p>
          <p>{salaryPrediction.basis ? `Best signal: ${salaryPrediction.basis.title} · ${salaryPrediction.basis.company}` : "Prediction is based on profile and resume signal."}</p>
          <div className="skillLine compact">
            {salaryPrediction.signals.map((signal) => (
              <span key={signal}>{signal}</span>
            ))}
          </div>
        </article>

        <article className="toolCard resumeCard">
          <div className="toolHeader">
            <h3>Resume improvements</h3>
            <span className="featurePill">ATS</span>
          </div>
          <ul className="bulletList">
            {resumeSuggestions.map((suggestion) => (
              <li key={suggestion}>{suggestion}</li>
            ))}
          </ul>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Career path prediction</h3>
            <span className="featurePill">AI path</span>
          </div>
          <p className="muted">Current level: {String(pathPrediction.current_level || "junior").toUpperCase()}</p>
          <div className="roadmapListInline">
            {(pathPrediction.predicted_paths || []).map((step) => (
              <div className="roadmapStep" key={`${step.role}-${step.timeline}`}>
                <strong>{step.role}</strong>
                <span>{step.timeline}</span>
                <small>{step.confidence}% confidence</small>
              </div>
            ))}
          </div>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Learning recommendations</h3>
            <span className="featurePill">Personalized</span>
          </div>
          <ul className="bulletList">
            {(pathPrediction.learning_recommendations || []).slice(0, 4).map((item) => (
              <li key={item.skill}>
                <strong>{item.skill}:</strong> {item.why}
              </li>
            ))}
          </ul>
          <div className="skillLine compact">
            {(pathPrediction.market_insights?.top_demanded_skills || []).slice(0, 5).map((skillItem) => (
              <span key={`${skillItem.skill}-${skillItem.openings}`}>{skillItem.skill}</span>
            ))}
          </div>
        </article>

        <article className="toolCard voiceCard">
          <div className="toolHeader">
            <h3>Voice assistant</h3>
            <span className={voiceSupported ? "featurePill" : "featurePill mutedPill"}>
              {voiceSupported ? "Supported" : "Text only"}
            </span>
          </div>
          <p className="muted">Try commands like salary, refresh, profile, recruiter, or resume.</p>
          <button className="ghostButton" disabled={loading || listening || !voiceSupported} onClick={startVoiceAssistant} type="button">
            {listening ? "Listening..." : "Start voice command"}
          </button>
          {transcript ? <p className="assistantTranscript"><strong>Heard:</strong> {transcript}</p> : null}
          <p className="assistantReply">{assistantReply}</p>
          {voiceError ? <p className="errorText">{voiceError}</p> : null}
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Voice interview simulator</h3>
            <span className="featurePill">Mock</span>
          </div>
          <button className="ghostButton" type="button" disabled={loading} onClick={onRunVoiceSimulator}>
            Run instant simulation
          </button>
          {voiceInterviewResult ? (
            <>
              <p className="muted">Overall: {voiceInterviewResult.overall_score}%</p>
              <div className="skillLine compact">
                <span>Fluency {voiceInterviewResult.fluency_score}%</span>
                <span>Communication {voiceInterviewResult.communication_score}%</span>
                <span>Confidence {voiceInterviewResult.confidence_score}%</span>
              </div>
            </>
          ) : (
            <p className="muted">Simulate realistic interview response quality with instant feedback.</p>
          )}
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Resume keyword optimizer</h3>
            <span className="featurePill">ATS+</span>
          </div>
          <button className="ghostButton" type="button" disabled={loading || !resume} onClick={onRunKeywordOptimizer}>
            Optimize keywords
          </button>
          <div className="skillLine compact">
            {(resumeKeywordOptimization?.missing_keywords || []).slice(0, 5).map((keyword) => (
              <span key={keyword}>{keyword}</span>
            ))}
          </div>
          <p className="muted">{resumeKeywordOptimization?.summary_hint || "Upload a resume to unlock keyword optimization."}</p>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Internship roadmap</h3>
            <span className="featurePill">Semester</span>
          </div>
          <p className="muted">Readiness: {internshipRoadmap?.readiness_score ?? 0}%</p>
          <ul className="bulletList">
            {(internshipRoadmap?.roadmap || []).slice(0, 2).map((item) => (
              <li key={item.semester}><strong>{item.semester}:</strong> {item.focus}</li>
            ))}
          </ul>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Candidate reputation</h3>
            <span className="featurePill">Credibility</span>
          </div>
          <p className="salaryValue">{reputationScore?.reputation_score ?? 0}%</p>
          <p className="muted">Band: {reputationScore?.band || "Emerging"}</p>
          <p>{reputationScore?.improvement_tip || "Keep profile and applications active to build reputation."}</p>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>AI team recommendations</h3>
            <span className="featurePill">Network</span>
          </div>
          <ul className="bulletList">
            {(teamRecommendations?.recommendations || []).slice(0, 3).map((person) => (
              <li key={person.user_id}>
                <strong>{person.name}:</strong> {(person.shared_skills || []).slice(0, 2).join(", ") || "Complementary profile"}
              </li>
            ))}
          </ul>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Networking suggestions</h3>
            <span className="featurePill">Mentors</span>
          </div>
          <ul className="bulletList">
            {(networkingSuggestions?.recommendations || []).slice(0, 3).map((person) => (
              <li key={person.user_id}>
                <strong>{person.name}:</strong> {person.persona || "Potential strong connector"}
              </li>
            ))}
          </ul>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Internship tracking</h3>
            <span className="featurePill">Progress</span>
          </div>
          <div className="skillLine compact">
            <span>Total {internshipTracking?.total_internships ?? 0}</span>
            <span>Active {internshipTracking?.active_internships ?? 0}</span>
            <span>Shortlisted {internshipTracking?.completed_or_shortlisted ?? 0}</span>
          </div>
          <p className="muted">Attendance score: {internshipTracking?.attendance_score ?? 0}%</p>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Personal branding</h3>
            <span className="featurePill">Profile</span>
          </div>
          <p className="salaryValue">{brandingInsights?.brand_strength ?? 0}%</p>
          <p>{brandingInsights?.headline_suggestion || "Add measurable outcomes to your headline."}</p>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Resume authenticity</h3>
            <span className="featurePill">Integrity</span>
          </div>
          <p className="muted">Verdict: {fakeResumeReport?.verdict || "No report"}</p>
          <p className="salaryValue">{fakeResumeReport?.authenticity_confidence ?? 0}% confidence</p>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Personality development coach</h3>
            <span className="featurePill">Growth</span>
          </div>
          <p className="salaryValue">{personalityCoach?.coach_score ?? 0}%</p>
          <p className="muted">Focus: {personalityCoach?.focus_area || "communication"}</p>
          <ul className="bulletList">
            {(personalityCoach?.development_plan || []).slice(0, 2).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Interactive career simulation</h3>
            <span className="featurePill">Scenario</span>
          </div>
          <p className="salaryValue">{careerSimulation?.simulation_score ?? 0}%</p>
          <ul className="bulletList">
            {(careerSimulation?.scenarios || []).slice(0, 2).map((scenario) => (
              <li key={scenario.phase}>
                <strong>{scenario.phase}:</strong> {scenario.recommended_action}
              </li>
            ))}
          </ul>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Smart internship performance</h3>
            <span className="featurePill">Internship</span>
          </div>
          <p className="salaryValue">{internshipPerformance?.performance_score ?? 0}%</p>
          <div className="skillLine compact">
            <span>Attendance {internshipPerformance?.attendance_score ?? 0}%</span>
            <span>Completion {internshipPerformance?.project_completion_score ?? 0}%</span>
            <span>Comm {internshipPerformance?.communication_score ?? 0}%</span>
          </div>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Collaborative project builder</h3>
            <span className="featurePill">Builder</span>
          </div>
          <p className="muted">{collaborativeProject?.project_title || "Project Builder"}</p>
          <ul className="bulletList">
            {(collaborativeProject?.team_roles || []).slice(0, 2).map((role) => (
              <li key={role.role}><strong>{role.role}:</strong> {role.focus}</li>
            ))}
          </ul>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Interview transcript generator</h3>
            <span className="featurePill">Transcript</span>
          </div>
          <p className="muted">{interviewTranscript?.summary || "Auto-generated interview flow."}</p>
          <ul className="bulletList">
            {(interviewTranscript?.transcript || []).slice(0, 2).map((line, index) => (
              <li key={`${line.speaker}-${index}`}><strong>{line.speaker}:</strong> {line.text}</li>
            ))}
          </ul>
        </article>

        <article className="toolCard">
          <div className="toolHeader">
            <h3>Time management analyzer</h3>
            <span className="featurePill">Planner</span>
          </div>
          <p className="salaryValue">{timeManagementAnalysis?.focus_score ?? 0}%</p>
          <ul className="bulletList">
            {(timeManagementAnalysis?.priorities || []).slice(0, 2).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}

function ProtectedRoute({ profile, children }) {
  if (!hasSession()) {
    return <Navigate to="/login" replace />;
  }
  if (!profile) {
    return (
      <main className="appShell">
        <p className="status">Loading your workspace...</p>
      </main>
    );
  }
  return children;
}

function RoleRoute({ profile, roles, children }) {
  if (!profile || !roles.includes(profile?.user?.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

function TopNav({ profile, onLogout, loading }) {
  const location = useLocation();
  const navItems = profile
    ? [
        { to: "/dashboard", label: "Home" },
        { to: "/opportunities", label: "Opportunities" },
        { to: "/companies", label: "Companies" },
        { to: "/advanced-ai", label: "AI Suite" },
        { to: "/saas", label: "SaaS" },
        { to: "/dashboard/student", label: "AI Match", studentOnly: true },
        { to: "/recruiter/dashboard", label: "Recruiter" },
        { to: "/profile", label: "Profile" },
      ]
    : [
        { to: "/opportunities", label: "Opportunities" },
        { to: "/companies", label: "Companies" },
        { to: "/advanced-ai", label: "AI Suite" },
        { to: "/saas", label: "SaaS" },
        { to: "/login", label: "Login" },
        { to: "/signup", label: "Join now" },
      ];

  return (
    <header className="topNav">
      <Link className="brand" to="/">
        <span className="brandMark">AI</span>
        <span>
          <strong>AIJobPlatform</strong>
          <small>Modern career network</small>
        </span>
      </Link>
      <nav>
        {navItems
          .filter((item) => !item.studentOnly || profile?.user?.role === "student")
          .map((item) => (
            <Link className={location.pathname === item.to ? "active" : ""} key={item.to} to={item.to}>
              {item.label}
            </Link>
          ))}
      </nav>
      {profile ? (
        <button className="ghostButton navButton" disabled={loading} onClick={onLogout} type="button">
          Logout
        </button>
      ) : null}
    </header>
  );
}

function JobCard({ job, featured = false }) {
  const skills = splitList(job.skills_required).slice(0, 5);
  return (
    <article className={featured ? "jobCard featured" : "jobCard"}>
      <div className="jobHeader">
        <div className="companyLogo">{String(job.company || "AI").slice(0, 2).toUpperCase()}</div>
        <div>
          <h3>{job.title}</h3>
          <p>{job.company} · {job.location}</p>
        </div>
      </div>
      <p className="jobDescription">{job.description}</p>
      <div className="chipRow">
        <span className="chip">{job.employment_type}</span>
        {job.salary_range ? <span className="chip">{job.salary_range}</span> : null}
        {typeof job.match_score !== "undefined" ? <span className="chip strong">{job.match_score} match points</span> : null}
      </div>
      {skills.length ? (
        <div className="skillLine">
          {skills.map((skill) => (
            <span key={`${job.id}-${skill}`}>{skill}</span>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function LandingPage({ jobs }) {
  const featuredJobs = jobs.length ? jobs.slice(0, 3) : fallbackJobs;
  return (
    <section className="landing">
      <div className="heroPanel">
        <div className="heroCopy">
          <p className="eyebrow">AI-first hiring network</p>
          <h1>AIJobPlatform</h1>
          <p>
            A LinkedIn-style workspace for students, recruiters, and admins: polished profiles, smart job discovery,
            resume matching, and recruiter posting tools in one product.
          </p>
          <div className="heroActions">
            <Link className="primaryLink" to="/signup">Build your profile</Link>
            <Link className="secondaryLink" to="/login">Open dashboard</Link>
          </div>
        </div>
        <div className="heroVisual" aria-hidden="true">
          <div className="networkCard large">
            <span className="avatarRing">AR</span>
            <strong>AI match ready</strong>
            <small>Resume parsed · 82% role fit</small>
          </div>
          <div className="networkCard small top">12 recruiter views</div>
          <div className="networkCard small bottom">4 warm intros</div>
        </div>
      </div>

      <section className="sectionBand">
        <div className="sectionHeader">
          <p className="eyebrow">Live opportunities</p>
          <h2>Find signal, not noise</h2>
        </div>
        <div className="jobGrid">
          {featuredJobs.map((job) => (
            <JobCard featured key={job.id} job={job} />
          ))}
        </div>
      </section>

      <section className="storyGrid">
        {storyCards.map((story) => (
          <article className="storyCard" key={story.name}>
            <div className="miniAvatar">{story.name.split(" ").map((part) => part[0]).join("")}</div>
            <p>{story.text}</p>
            <strong>{story.name}</strong>
            <span>{story.title}</span>
          </article>
        ))}
      </section>

      <section className="sectionBand featureBand">
        <div className="sectionHeader">
          <p className="eyebrow">Platform capabilities</p>
          <h2>Everything the hiring network needs</h2>
          <p className="sectionLead">
            The product combines secure authentication, AI resume analysis, intelligent matching, recruiter tools,
            chat, notifications, and profile management in one responsive workspace.
          </p>
        </div>
        <div className="featureGrid">
          {featureCards.map((feature) => (
            <article className="featureCard" key={feature.title}>
              <div className="featureCardTop">
                <h3>{feature.title}</h3>
                <span className="featurePill">Live</span>
              </div>
              <p>{feature.summary}</p>
              <div className="featureMeta">
                {feature.meta.map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </div>
              <Link className="featureLink" to={feature.route}>
                {feature.cta}
              </Link>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}

const interviewQuestionBank = [
  "Tell me about a project where you solved a hard problem.",
  "How would you design a job recommendation engine for students?",
  "Describe a time you received feedback and changed your approach.",
  "What tradeoffs would you make when shipping an AI feature quickly?",
];

const resumeSectionsSeed = [
  { id: "summary", title: "Summary", body: "Full-stack developer focused on React, Django, AI tooling, and measurable product outcomes." },
  { id: "skills", title: "Skills", body: "React, Django, Python, REST APIs, SQL, GitHub Actions, prompt engineering." },
  { id: "projects", title: "Projects", body: "AI job matcher, resume parser, recruiter dashboard, portfolio generator." },
  { id: "experience", title: "Experience", body: "Built production-style features with authentication, analytics, and real-time workflows." },
];

const aiStartupFeatures = [
  "Resume Analyzer",
  "Career Roadmap",
  "Skill Gap Engine",
  "Mock Interview",
  "Video Resume",
  "Personality Match",
  "Career Chatbot",
  "Gamification",
  "Public Portfolio",
  "AI Job Search",
  "Resume Builder",
  "Recruiter Intelligence",
  "Auto Apply",
  "Coding Evaluator",
  "Certificate Verification",
  "Marketplace",
  "Learning Engine",
  "Project Generator",
  "Networking",
  "Hiring Prediction",
];

const marketSkillBank = [
  "python",
  "django",
  "react",
  "sql",
  "rest api",
  "docker",
  "aws",
  "redis",
  "git",
  "typescript",
  "node",
  "fastapi",
  "mongodb",
  "kubernetes",
  "communication",
  "leadership",
];

function uniqueTokens(text) {
  return Array.from(
    new Set(
      String(text || "")
        .toLowerCase()
        .replace(/[^a-z0-9+#.\s-]/g, " ")
        .split(/[\s,;/|]+/)
        .map((item) => item.trim())
        .filter(Boolean)
    )
  );
}

function detectSkillSet(text) {
  const lower = String(text || "").toLowerCase();
  return marketSkillBank.filter((skill) => lower.includes(skill));
}

function analyzeResumeDraft(resumeText, jobText = "") {
  const lower = String(resumeText || "").toLowerCase();
  const words = uniqueTokens(resumeText);
  const resumeSkills = detectSkillSet(resumeText);
  const jobSkills = detectSkillSet(jobText);
  const missingKeywords = jobSkills.filter((skill) => !resumeSkills.includes(skill));
  const hasMetrics = /\d+%|\d+\+|\d+x|reduced|increased|improved|saved|launched/i.test(resumeText);
  const weakPoints = [];

  if (!lower.includes("project")) weakPoints.push("Add 2-3 project bullets with links or outcomes.");
  if (!hasMetrics) weakPoints.push("Add quantified achievements like users, latency, revenue, or time saved.");
  if (resumeSkills.length < 6) weakPoints.push("Add a tighter technical skills section.");
  if (!/led|owned|built|shipped|designed|implemented/i.test(resumeText)) weakPoints.push("Use stronger action verbs in experience bullets.");

  const grammarIssues = [
    lower.includes("i am") ? "Replace first-person resume phrasing with direct achievement bullets." : null,
    lower.includes("responsible for") ? "Replace 'responsible for' with specific ownership and result." : null,
    /[a-z]\s{2,}[a-z]/.test(resumeText) ? "Remove extra spaces for ATS readability." : null,
  ].filter(Boolean);

  const atsScore = Math.max(
    38,
    Math.min(
      98,
      52 + Math.min(18, resumeSkills.length * 3) + (hasMetrics ? 12 : 0) + (lower.includes("project") ? 8 : 0) - missingKeywords.length * 4 - grammarIssues.length * 3
    )
  );

  return {
    atsScore,
    resumeSkills,
    missingKeywords,
    weakPoints: weakPoints.length ? weakPoints : ["Resume has a solid baseline. Tailor it more tightly to the target JD."],
    grammarIssues: grammarIssues.length ? grammarIssues : ["No major grammar red flags detected in this quick pass."],
    suggestions: [
      "Add projects with tech stack, links, and measurable outcome.",
      "Move the most relevant skills into the first third of the resume.",
      missingKeywords[0] ? `Add truthful evidence for ${missingKeywords[0].toUpperCase()}.` : "Keep keywords truthful and backed by project proof.",
    ],
  };
}

function buildSkillRoadmap(skillsText, targetRole) {
  const skills = uniqueTokens(skillsText);
  const role = String(targetRole || "backend developer").toLowerCase();
  const steps = [];
  const pushIfMissing = (skill, label) => {
    if (!skills.includes(skill)) steps.push(label);
  };

  if (role.includes("backend")) {
    pushIfMissing("rest", "Learn REST APIs and authentication patterns.");
    pushIfMissing("docker", "Learn Docker and deploy one Django/FastAPI service.");
    pushIfMissing("redis", "Add Redis caching and background jobs.");
    pushIfMissing("aws", "Deploy projects on AWS or Render with monitoring.");
  } else if (role.includes("data")) {
    pushIfMissing("python", "Strengthen Python, statistics, and pandas.");
    pushIfMissing("sql", "Practice SQL joins, windows, and analytics queries.");
    steps.push("Build one dashboard and one ML notebook with clear business metrics.");
  } else {
    pushIfMissing("react", "Build polished React workflows with API integration.");
    pushIfMissing("typescript", "Add TypeScript and component testing.");
    steps.push("Ship a portfolio project with auth, analytics, and deployment.");
  }

  steps.push(`Apply for ${targetRole || "target"} roles with a tailored resume and portfolio.`);
  return steps.slice(0, 6);
}

function chatbotAnswer(question, analysis, roadmap) {
  const text = String(question || "").toLowerCase();
  if (text.includes("job")) {
    return `Apply to roles where your resume already covers ${analysis.resumeSkills.slice(0, 3).join(", ") || "your strongest skills"}. Avoid roles missing more than 4 must-have skills.`;
  }
  if (text.includes("resume")) {
    return `Your quick ATS score is ${analysis.atsScore}/100. Biggest move: ${analysis.suggestions[0]}`;
  }
  if (text.includes("roadmap") || text.includes("backend")) {
    return roadmap[0] || "Start with one deployable project, then add Docker, cloud, and interview practice.";
  }
  return "Tell me your target role, current skills, or paste a JD. I can suggest jobs, resume fixes, and a learning path.";
}

function generateSmartJobs(query) {
  const lower = String(query || "").toLowerCase();
  const remote = lower.includes("remote");
  const lpaMatch = lower.match(/under\s+(\d+)\s*lpa|(\d+)\s*lpa/i);
  const salary = lpaMatch ? `${lpaMatch[1] || lpaMatch[2]} LPA cap` : "Market salary";
  const role = lower.includes("python") ? "Python Backend Developer" : lower.includes("data") ? "Data Analyst" : "Full Stack Engineer";
  return [
    { title: role, company: "CloudHire Labs", location: remote ? "Remote" : "Bengaluru", salary, match: 91 },
    { title: `${role} Intern`, company: "SkillSprint", location: remote ? "Remote" : "Pune", salary: "Internship stipend", match: 84 },
    { title: `Junior ${role}`, company: "LaunchStack", location: remote ? "Remote" : "Hyderabad", salary, match: 78 },
  ];
}

function predictHiringFromJd(jdText) {
  const skills = detectSkillSet(jdText);
  const strictness = /senior|lead|architect|5\+|7\+/i.test(jdText) ? 12 : 0;
  const success = Math.max(42, Math.min(91, 72 + skills.length * 2 - strictness));
  return {
    success,
    availability: success >= 78 ? "High" : success >= 62 ? "Medium" : "Low",
    recommendation: skills.includes("docker") && skills.includes("aws") ? "Strong cloud-ready JD. Keep salary transparent." : "Add cloud/deployment clarity to attract stronger candidates.",
  };
}

function AdvancedAISuitePage() {
  const videoRef = useRef(null);
  const recorderRef = useRef(null);
  const timerRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [recording, setRecording] = useState(false);
  const [recordingUrl, setRecordingUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [currentQuestion, setCurrentQuestion] = useState(interviewQuestionBank[0]);
  const [interviewSeconds, setInterviewSeconds] = useState(0);
  const [code, setCode] = useState("function solve(input) {\n  return input.trim().split('').reverse().join('');\n}\n\nreturn solve(input);");
  const [codeOutput, setCodeOutput] = useState("Run code to see output.");
  const [sections, setSections] = useState(resumeSectionsSeed);
  const [resumeTheme, setResumeTheme] = useState("modern");
  const [githubHandle, setGithubHandle] = useState("");
  const [githubImport, setGithubImport] = useState(null);
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [certificate, setCertificate] = useState({ name: "", issuer: "", id: "" });
  const [certificateHash, setCertificateHash] = useState("");
  const [notes, setNotes] = useState([
    { author: "Recruiter", text: "Strong React fundamentals. Need deeper system design follow-up." },
    { author: "Panel", text: "Portfolio shows ownership and clean documentation." },
  ]);
  const [noteDraft, setNoteDraft] = useState("");
  const [roadmapGoal, setRoadmapGoal] = useState("Become Full Stack Developer in 6 months");
  const [roadmap, setRoadmap] = useState([]);

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  useEffect(() => () => {
    stream?.getTracks().forEach((track) => track.stop());
    window.clearInterval(timerRef.current);
  }, [stream]);

  const words = splitList(transcript.replace(/[.\n]/g, " "));
  const speechSpeed = interviewSeconds ? Math.round((words.length / Math.max(interviewSeconds, 1)) * 60) : 0;
  const confidenceScore = Math.min(96, Math.max(42, 58 + Math.min(words.length, 90) * 0.28 - Math.max(0, speechSpeed - 170) * 0.12));
  const eyeContactScore = stream ? Math.min(94, 68 + Math.floor((interviewSeconds % 13) * 1.7)) : 0;
  const interviewScore = Math.round((confidenceScore + Math.min(speechSpeed || 120, 180) / 2 + eyeContactScore) / 3);

  async function startInterview() {
    const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    setStream(mediaStream);
    setInterviewSeconds(0);
    window.clearInterval(timerRef.current);
    timerRef.current = window.setInterval(() => setInterviewSeconds((value) => value + 1), 1000);

    const recorder = new MediaRecorder(mediaStream);
    const chunks = [];
    recorder.ondataavailable = (event) => chunks.push(event.data);
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: "video/webm" });
      setRecordingUrl(URL.createObjectURL(blob));
    };
    recorder.start();
    recorderRef.current = recorder;
    setRecording(true);
  }

  function stopInterview() {
    recorderRef.current?.stop();
    stream?.getTracks().forEach((track) => track.stop());
    setStream(null);
    setRecording(false);
    window.clearInterval(timerRef.current);
  }

  function listenForAnswer() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setTranscript((value) => `${value}\nSpeech recognition is not supported in this browser. Type or paste the answer here.`);
      return;
    }
    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const spokenText = event.results?.[0]?.[0]?.transcript || "";
      setTranscript((value) => `${value}${value ? "\n" : ""}${spokenText}`);
      const lower = spokenText.toLowerCase();
      const nextQuestion = lower.includes("project")
        ? "What measurable impact did that project create?"
        : lower.includes("team")
          ? "How did you handle disagreement inside the team?"
          : interviewQuestionBank[(interviewQuestionBank.indexOf(currentQuestion) + 1) % interviewQuestionBank.length];
      setCurrentQuestion(nextQuestion);
    };
    recognition.start();
  }

  function runCode() {
    try {
      const input = "AIJobPlatform";
      const result = Function("input", code)(input);
      const passed = String(result) === "mroftalPboJIA";
      setCodeOutput(`${passed ? "Passed" : "Check output"}\nInput: ${input}\nExpected: mroftalPboJIA\nReceived: ${String(result)}`);
    } catch (error) {
      setCodeOutput(`Runtime error: ${error.message}`);
    }
  }

  function moveSection(index, direction) {
    const nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= sections.length) {
      return;
    }
    const nextSections = [...sections];
    [nextSections[index], nextSections[nextIndex]] = [nextSections[nextIndex], nextSections[index]];
    setSections(nextSections);
  }

  async function importGithubProfile() {
    if (!githubHandle.trim()) {
      return;
    }
    const response = await fetch(`https://api.github.com/users/${githubHandle.trim()}`);
    const profile = await response.json();
    const reposResponse = await fetch(`https://api.github.com/users/${githubHandle.trim()}/repos?sort=updated&per_page=5`);
    const repos = await reposResponse.json();
    setGithubImport({
      name: profile.name || githubHandle,
      publicRepos: profile.public_repos || 0,
      followers: profile.followers || 0,
      skills: Array.isArray(repos) ? Array.from(new Set(repos.map((repo) => repo.language).filter(Boolean))).slice(0, 6) : [],
      projects: Array.isArray(repos) ? repos.map((repo) => repo.name).slice(0, 5) : [],
    });
  }

  async function verifyCertificate() {
    const raw = `${certificate.name}|${certificate.issuer}|${certificate.id}`;
    const encoded = new TextEncoder().encode(raw);
    const digest = await crypto.subtle.digest("SHA-256", encoded);
    setCertificateHash(Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, "0")).join(""));
  }

  function generateRoadmap() {
    const monthMatch = roadmapGoal.match(/(\d+)\s*month/i);
    const months = monthMatch ? Number(monthMatch[1]) : 6;
    const weeks = Math.max(4, months * 4);
    setRoadmap(Array.from({ length: Math.min(weeks, 12) }).map((_, index) => ({
      week: index + 1,
      goal: index < 4 ? "Core HTML, CSS, JavaScript, Git, and React practice" : index < 8 ? "Backend APIs, databases, auth, and deployment" : "Portfolio projects, mock interviews, and job applications",
      daily: "90 min coding, 30 min notes, 30 min interview practice",
      proof: index % 3 === 2 ? "Ship one portfolio milestone" : "Complete exercises and commit progress",
    })));
  }

  const portfolioMarkup = sections.map((section) => `${section.title}: ${section.body}`).join("\n\n");
  const qrBits = certificateHash ? certificateHash.slice(0, 64).split("").map((char) => parseInt(char, 16) % 2 === 0) : [];

  return (
    <section className="landing advancedSuite">
      <section className="panel suiteHero">
        <div>
          <p className="eyebrow">Advanced AI hiring lab</p>
          <h1>AI Mock Interview System</h1>
          <p className="sectionLead">
            Browser-powered prototypes for WebRTC interviews, speech-to-text, code rounds, resume editing,
            GitHub import, recordings, scorecards, verification, collaboration, and AI roadmaps.
          </p>
        </div>
        <div className="scoreDial">
          <strong>{interviewScore || 0}</strong>
          <span>Interview score</span>
        </div>
      </section>

      <section className="suiteGrid">
        <article className="panel suiteCard wide">
          <div className="sectionHeader inline">
            <div>
              <p className="eyebrow">WebRTC + speech</p>
              <h2>Live mock interview</h2>
            </div>
            <span className="featurePill">{recording ? "Recording" : "Ready"}</span>
          </div>
          <div className="interviewGrid">
            <video ref={videoRef} autoPlay muted playsInline className="interviewVideo" />
            <div className="metricStack">
              <strong>{currentQuestion}</strong>
              <button type="button" onClick={recording ? stopInterview : startInterview}>
                {recording ? "Stop interview" : "Start webcam + mic"}
              </button>
              <button className="ghostButton" type="button" onClick={listenForAnswer}>Capture answer</button>
              <textarea value={transcript} onChange={(event) => setTranscript(event.target.value)} placeholder="Transcript appears here..." />
            </div>
          </div>
          <div className="scoreGrid">
            <span>Confidence {Math.round(confidenceScore)}%</span>
            <span>Speech speed {speechSpeed} WPM</span>
            <span>Eye contact proxy {eyeContactScore}%</span>
            <span>Emotion {confidenceScore > 76 ? "Calm" : "Nervous"}</span>
            <span>Timer {Math.floor(interviewSeconds / 60)}:{String(interviewSeconds % 60).padStart(2, "0")}</span>
          </div>
          {recordingUrl ? <video src={recordingUrl} controls className="playbackVideo" /> : null}
        </article>

        <article className="panel suiteCard">
          <p className="eyebrow">Monaco Editor</p>
          <h2>Live coding interview</h2>
          <div className="monacoShell">
            <Editor
              height="260px"
              defaultLanguage="javascript"
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value || "")}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                scrollBeyondLastLine: false,
                wordWrap: "on",
              }}
            />
          </div>
          <div className="buttonRow">
            <button type="button" onClick={runCode}>Run code</button>
            <button className="ghostButton" type="button" onClick={() => setCodeOutput("Recruiter is watching typing, timer, output, and testcase status.")}>Monitor view</button>
          </div>
          <pre className="codeOutput">{codeOutput}</pre>
        </article>

        <article className="panel suiteCard">
          <p className="eyebrow">Canva-style builder</p>
          <h2>AI resume builder</h2>
          <select value={resumeTheme} onChange={(event) => setResumeTheme(event.target.value)}>
            <option value="modern">Modern green</option>
            <option value="classic">Classic ink</option>
            <option value="startup">Startup coral</option>
          </select>
          <div className={`resumePreview ${resumeTheme}`}>
            {sections.map((section, index) => (
              <div className="resumeBlock" key={section.id}>
                <strong>{section.title}</strong>
                <p>{section.body}</p>
                <div className="miniActions">
                  <button className="ghostButton" type="button" onClick={() => moveSection(index, -1)}>Up</button>
                  <button className="ghostButton" type="button" onClick={() => moveSection(index, 1)}>Down</button>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel suiteCard">
          <p className="eyebrow">GitHub API + LinkedIn</p>
          <h2>Profile import</h2>
          <input value={githubHandle} onChange={(event) => setGithubHandle(event.target.value)} placeholder="GitHub username" />
          <input value={linkedinUrl} onChange={(event) => setLinkedinUrl(event.target.value)} placeholder="LinkedIn profile URL for OAuth handoff" />
          <button type="button" onClick={importGithubProfile}>Fetch GitHub profile</button>
          {githubImport ? (
            <div className="importSummary">
              <strong>{githubImport.name}</strong>
              <span>{githubImport.publicRepos} repos - {githubImport.followers} followers</span>
              <div className="skillLine">{githubImport.skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
            </div>
          ) : null}
        </article>

        <article className="panel suiteCard">
          <p className="eyebrow">Portfolio generator</p>
          <h2>Resume to website</h2>
          <pre className="portfolioPreview">{portfolioMarkup}</pre>
          <button type="button" onClick={() => navigator.clipboard?.writeText(portfolioMarkup)}>One-click deployment draft</button>
        </article>

        <article className="panel suiteCard">
          <p className="eyebrow">Smart job feed</p>
          <h2>Recommendation engine</h2>
          <div className="rankingList">
            {["Full Stack Developer", "AI Product Engineer", "Frontend Intern"].map((role, index) => (
              <span key={role}>{index + 1}. {role} - {92 - index * 8}% fit - trending</span>
            ))}
          </div>
        </article>

        <article className="panel suiteCard">
          <p className="eyebrow">QR + validation</p>
          <h2>Certificate verification</h2>
          <input value={certificate.name} onChange={(event) => setCertificate({ ...certificate, name: event.target.value })} placeholder="Certificate name" />
          <input value={certificate.issuer} onChange={(event) => setCertificate({ ...certificate, issuer: event.target.value })} placeholder="Issuer" />
          <input value={certificate.id} onChange={(event) => setCertificate({ ...certificate, id: event.target.value })} placeholder="Certificate ID" />
          <button type="button" onClick={verifyCertificate}>Generate verification hash</button>
          {certificateHash ? (
            <div className="certificateResult">
              <div className="qrPreview" aria-label="Certificate QR verification preview">
                {qrBits.map((active, index) => <span className={active ? "active" : ""} key={index} />)}
              </div>
              <code className="hashBox">{certificateHash.slice(0, 32)}...</code>
            </div>
          ) : null}
        </article>

        <article className="panel suiteCard">
          <p className="eyebrow">Realtime collaboration</p>
          <h2>Recruiter team notes</h2>
          <div className="noteStack">
            {notes.map((note, index) => <p key={`${note.author}-${index}`}><strong>{note.author}:</strong> {note.text}</p>)}
          </div>
          <div className="buttonRow">
            <input value={noteDraft} onChange={(event) => setNoteDraft(event.target.value)} placeholder="Add interview feedback" />
            <button type="button" onClick={() => {
              if (noteDraft.trim()) {
                setNotes([...notes, { author: "You", text: noteDraft.trim() }]);
                setNoteDraft("");
              }
            }}>Add</button>
          </div>
        </article>

        <article className="panel suiteCard wide">
          <p className="eyebrow">AI roadmap generator</p>
          <h2>Daily plan, weekly goals, courses, practice tasks</h2>
          <div className="buttonRow">
            <input value={roadmapGoal} onChange={(event) => setRoadmapGoal(event.target.value)} />
            <button type="button" onClick={generateRoadmap}>Generate roadmap</button>
          </div>
          <div className="roadmapCards">
            {roadmap.map((item) => (
              <div className="roadmapStep" key={item.week}>
                <strong>Week {item.week}</strong>
                <span>{item.goal}</span>
                <small>{item.daily}</small>
                <small>{item.proof}</small>
              </div>
            ))}
          </div>
        </article>
      </section>
    </section>
  );
}

const saasFallback = {
  subscription: {
    plan: {
      code: "free",
      name: "Free",
      resume_credits: 3,
      ai_usage_limit: 10,
      job_post_limit: 1,
    },
    status: "active",
    resume_credits_remaining: 2,
    ai_usage_count: 6,
    ai_usage_limit: 10,
    ai_usage_remaining: 4,
  },
  plans: [
    {
      code: "free",
      name: "Free",
      monthly_price_inr: 0,
      resume_credits: 3,
      ai_usage_limit: 10,
      job_post_limit: 1,
      features: ["Basic profile", "3 resume credits", "10 AI actions"],
    },
    {
      code: "premium",
      name: "Premium",
      monthly_price_inr: 79900,
      resume_credits: 40,
      ai_usage_limit: 300,
      job_post_limit: 5,
      features: ["AI resume builder", "Mock interview analytics", "Dashboard charts"],
    },
    {
      code: "recruiter",
      name: "Recruiter Pro",
      monthly_price_inr: 249900,
      resume_credits: 100,
      ai_usage_limit: 1000,
      job_post_limit: 50,
      features: ["Team monitoring", "Pipeline collaboration", "Candidate analytics"],
    },
  ],
  activity: [
    { type: "ai", amount: 1, metadata: { event: "Mock interview scorecard" }, created_at: new Date().toISOString() },
    { type: "resume_credit", amount: 1, metadata: { event: "Resume PDF generated" }, created_at: new Date(Date.now() - 86400000).toISOString() },
    { type: "job_post", amount: 1, metadata: { event: "Frontend Engineer posted" }, created_at: new Date(Date.now() - 172800000).toISOString() },
  ],
};

function ModernSaaSPage() {
  const navigate = useNavigate();
  const [billing, setBilling] = useState(saasFallback);
  const [query, setQuery] = useState("");
  const [companySearch, setCompanySearch] = useState("");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [provider, setProvider] = useState("stripe");
  const [status, setStatus] = useState("Open the command palette with Ctrl+K.");
  const [loadingBilling, setLoadingBilling] = useState(false);

  const commands = [
    { label: "Open Dashboard", route: "/dashboard", hint: "Home workspace" },
    { label: "Open AI Suite", route: "/advanced-ai", hint: "Interview and coding tools" },
    { label: "Open Opportunities", route: "/opportunities", hint: "Search jobs" },
    { label: "Open Companies", route: "/companies", hint: "Company directory" },
    { label: "Open Profile", route: "/profile", hint: "Edit identity" },
  ];

  useEffect(() => {
    const handleKeydown = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((value) => !value);
      }
      if (event.key === "Escape") {
        setPaletteOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  }, []);

  useEffect(() => {
    if (!hasSession()) {
      return;
    }
    setLoadingBilling(true);
    getBillingOverview()
      .then((payload) => setBilling(payload))
      .catch((error) => setStatus(error.message || "Using demo billing data."))
      .finally(() => setLoadingBilling(false));
  }, []);

  const filteredCommands = commands.filter((command) =>
    `${command.label} ${command.hint}`.toLowerCase().includes(query.toLowerCase())
  );

  const searchResults = [
    ...fallbackJobs.map((job) => ({ title: job.title, meta: `${job.company} - ${job.location}`, route: "/opportunities" })),
    ...commands.map((command) => ({ title: command.label, meta: command.hint, route: command.route })),
    ...billing.plans.map((plan) => ({ title: `${plan.name} plan`, meta: `${plan.ai_usage_limit} AI actions`, route: "/saas" })),
  ].filter((item) => `${item.title} ${item.meta}`.toLowerCase().includes(query.toLowerCase()));

  const usageChartData = [
    { name: "Mon", ai: 18, resumes: 3 },
    { name: "Tue", ai: 28, resumes: 4 },
    { name: "Wed", ai: 22, resumes: 6 },
    { name: "Thu", ai: 34, resumes: 5 },
    { name: "Fri", ai: 46, resumes: 8 },
    { name: "Sat", ai: 31, resumes: 4 },
    { name: "Sun", ai: 39, resumes: 7 },
  ];
  const funnelData = [
    { stage: "Views", value: 420 },
    { stage: "Applies", value: 156 },
    { stage: "Shortlist", value: 48 },
    { stage: "Interviews", value: 19 },
    { stage: "Offers", value: 6 },
  ];

  async function startCheckout(planCode) {
    if (!hasSession()) {
      navigate("/login");
      return;
    }
    setLoadingBilling(true);
    try {
      const checkoutPayload = await createBillingCheckout(planCode, provider);
      const transactionId = checkoutPayload.checkout.transaction_id;
      const confirmed = await confirmBillingCheckout(transactionId, { simulated: true });
      setBilling((current) => ({ ...current, subscription: confirmed.subscription }));
      setStatus(`${provider === "stripe" ? "Stripe" : "Razorpay"} checkout confirmed for ${planCode}.`);
    } catch (error) {
      setStatus(error.message || "Checkout failed.");
    } finally {
      setLoadingBilling(false);
    }
  }

  return (
    <section className="landing saasConsole">
      <motion.section
        className="panel suiteHero"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <div>
          <p className="eyebrow">Modern UI additions</p>
          <h1>Premium SaaS Command Center</h1>
          <p className="sectionLead">
            Framer Motion interactions, global search, command palette, activity timeline,
            Recharts dashboards, subscriptions, credits, and AI usage controls.
          </p>
        </div>
        <button className="ghostButton" type="button" onClick={() => setPaletteOpen(true)}>
          Command palette
        </button>
      </motion.section>

      <section className="panel globalSearchPanel">
        <label className="field">
          <span>Global search</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search jobs, pages, plans, candidates..." />
        </label>
        {query ? (
          <div className="searchResults">
            {searchResults.slice(0, 6).map((item) => (
              <button className="searchResult" key={`${item.title}-${item.meta}`} type="button" onClick={() => navigate(item.route)}>
                <strong>{item.title}</strong>
                <span>{item.meta}</span>
              </button>
            ))}
          </div>
        ) : null}
      </section>

      <section className="saasGrid">
        <motion.article className="panel suiteCard" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <p className="eyebrow">Usage limits</p>
          <h2>{billing.subscription.plan.name} plan</h2>
          {loadingBilling ? <SkeletonStack count={1} /> : (
            <div className="usageMeters">
              <div>
                <span>AI usage</span>
                <strong>{billing.subscription.ai_usage_count}/{billing.subscription.ai_usage_limit}</strong>
                <div className="progressTrack"><span style={{ width: `${Math.min((billing.subscription.ai_usage_count / billing.subscription.ai_usage_limit) * 100, 100)}%` }} /></div>
              </div>
              <div>
                <span>Resume credits</span>
                <strong>{billing.subscription.resume_credits_remaining}</strong>
                <div className="progressTrack"><span style={{ width: `${Math.min((billing.subscription.resume_credits_remaining / billing.subscription.plan.resume_credits) * 100, 100)}%` }} /></div>
              </div>
            </div>
          )}
          <p className="status compactStatus">{status}</p>
        </motion.article>

        <motion.article className="panel suiteCard" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <p className="eyebrow">Activity timeline</p>
          <h2>Recent product events</h2>
          <div className="activityTimeline">
            {billing.activity.map((item, index) => (
              <div className="timelineEntry" key={`${item.type}-${index}`}>
                <span />
                <div>
                  <strong>{item.metadata?.event || item.type}</strong>
                  <small>{new Date(item.created_at).toLocaleString()}</small>
                </div>
              </div>
            ))}
          </div>
        </motion.article>

        <article className="panel suiteCard wide">
          <div className="sectionHeader">
            <p className="eyebrow">Dashboard charts</p>
            <h2>AI usage and hiring funnel</h2>
          </div>
          <div className="chartGrid">
            <div className="chartBox">
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={usageChartData}>
                  <defs>
                    <linearGradient id="aiUsage" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#113d34" stopOpacity={0.7} />
                      <stop offset="95%" stopColor="#113d34" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e1dbcf" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="ai" stroke="#113d34" fill="url(#aiUsage)" />
                  <Area type="monotone" dataKey="resumes" stroke="#bf6030" fill="#f5dfd3" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="chartBox">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={funnelData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e1dbcf" />
                  <XAxis dataKey="stage" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#bf6030" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </article>

        <article className="panel suiteCard wide">
          <div className="sectionHeader inline">
            <div>
              <p className="eyebrow">Subscriptions</p>
              <h2>Free, Premium, and Recruiter plans</h2>
            </div>
            <select className="providerSelect" value={provider} onChange={(event) => setProvider(event.target.value)}>
              <option value="stripe">Stripe</option>
              <option value="razorpay">Razorpay</option>
            </select>
          </div>
          <div className="pricingGrid">
            {billing.plans.map((plan) => (
              <motion.article className="priceCard" key={plan.code} whileHover={{ y: -4 }}>
                <span className="featurePill">{plan.code === billing.subscription.plan.code ? "Current" : "Upgrade"}</span>
                <h3>{plan.name}</h3>
                <strong className="priceValue">Rs {(plan.monthly_price_inr / 100).toLocaleString("en-IN")}/mo</strong>
                <div className="skillLine">
                  <span>{plan.resume_credits} resume credits</span>
                  <span>{plan.ai_usage_limit} AI actions</span>
                  <span>{plan.job_post_limit} job posts</span>
                </div>
                <ul className="bulletList">
                  {plan.features.map((feature) => <li key={feature}>{feature}</li>)}
                </ul>
                <button disabled={loadingBilling || plan.code === billing.subscription.plan.code} type="button" onClick={() => startCheckout(plan.code)}>
                  {plan.code === billing.subscription.plan.code ? "Active plan" : `Pay with ${provider}`}
                </button>
              </motion.article>
            ))}
          </div>
        </article>
      </section>

      <AnimatePresence>
        {paletteOpen ? (
          <motion.div className="commandOverlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <motion.div className="commandPalette" initial={{ scale: 0.96, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.96, y: 20 }}>
              <input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Type a command or search..." />
              <div className="commandList">
                {filteredCommands.map((command) => (
                  <button key={command.route} type="button" onClick={() => {
                    navigate(command.route);
                    setPaletteOpen(false);
                  }}>
                    <strong>{command.label}</strong>
                    <span>{command.hint}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}

function CompanyDirectoryPage() {
  const [companies, setCompanies] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const debouncedQuery = useDebouncedValue(query);

  const loadCompanies = async (search = "") => {
    setLoading(true);
    setError("");
    try {
      const payload = await listCompanies(search);
      setCompanies(payload.companies || []);
    } catch (err) {
      setError(err.message || "Failed to load companies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCompanies();
  }, []);

  useEffect(() => {
    loadCompanies(debouncedQuery);
  }, [debouncedQuery]);

  return (
    <section className="landing">
      <div className="heroPanel">
        <div className="heroCopy">
          <p className="eyebrow">Company insights</p>
          <h1>Ratings, reviews, and hiring badges</h1>
          <p>
            Explore companies, compare their ratings, and open detailed profiles with recruiter verification and employee reviews.
          </p>
          <div className="heroActions">
            <button className="primaryLink" type="button" onClick={() => loadCompanies(query)}>
              Refresh directory
            </button>
          </div>
        </div>
      </div>

      <section className="panel">
        <div className="sectionHeader inline">
          <div>
            <p className="eyebrow">Browse companies</p>
            <h2>Find the best place to work</h2>
          </div>
          <label className="field" style={{ minWidth: 280 }}>
            <span>Search company</span>
            <input value={companySearch} onChange={(event) => setCompanySearch(event.target.value)} placeholder="Acme Labs" />
          </label>
          <button className="ghostButton fitButton" type="button" onClick={() => loadCompanies(companySearch)}>
            Search
          </button>
        </div>

        {loading ? (
          <SkeletonStack />
        ) : error ? (
          <p className="status errorText">{error}</p>
        ) : companies.length ? (
          <div className="jobStack">
            {companies.map((company) => (
              <article className="jobCard featured" key={company.id}>
                <div className="jobHeader">
                  <div className="companyLogo">{String(company.name || "CO").slice(0, 2).toUpperCase()}</div>
                  <div>
                    <h3>{company.name}</h3>
                    <p>{company.industry || "Company profile"} · {company.location || "Remote"}</p>
                  </div>
                </div>
                <p className="jobDescription">{company.description || "Company details and hiring reputation are available in the full profile."}</p>
                <div className="chipRow">
                  <span className="chip strong">{Number(company.average_rating || 0).toFixed(1)} rating</span>
                  <span className="chip">{company.review_count || 0} reviews</span>
                  <span className="chip">{company.badge_label || "Hiring badge"}</span>
                  <span className="chip">{company.hiring_urgency || "medium"}</span>
                </div>
                <div className="heroActions">
                  <Link className="primaryLink" to={`/company/${company.id}`}>
                    View profile
                  </Link>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No companies found"
            body="Try a different search or publish a job to seed the company directory."
            action={
              <button className="ghostButton fitButton" type="button" onClick={() => loadCompanies("")}>
                Reset search
              </button>
            }
          />
        )}
      </section>
    </section>
  );
}

function AuthLayout({ children, message }) {
  return (
    <section className="authLayout">
      <div className="authAside">
        <p className="eyebrow">Welcome to AIJobPlatform</p>
        <h1>Career networking with an AI co-pilot.</h1>
        <p>
          Create a profile, upload your resume, discover matched jobs, or post openings as a recruiter. Your backend
          auth and role system are wired into this interface.
        </p>
        <p className="status">{message}</p>
      </div>
      {children}
    </section>
  );
}

export default function App() {
  const navigate = useNavigate();
  const [signupData, setSignupData] = useState(initialSignup);
  const [loginData, setLoginData] = useState(initialLogin);
  const [resendEmail, setResendEmail] = useState("");
  const [forgotEmail, setForgotEmail] = useState("");
  const [resetPasswordValue, setResetPasswordValue] = useState("");
  const [debugVerificationPath, setDebugVerificationPath] = useState("");
  const [debugResetPath, setDebugResetPath] = useState("");
  const [jobData, setJobData] = useState(initialJob);
  const [profileForm, setProfileForm] = useState(emptyProfile);
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [postedJobs, setPostedJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [careerGuidance, setCareerGuidance] = useState(null);
  const [careerCoach, setCareerCoach] = useState(null);
  const [careerPathPrediction, setCareerPathPrediction] = useState(null);
  const [internshipRoadmap, setInternshipRoadmap] = useState(null);
  const [reputationScore, setReputationScore] = useState(null);
  const [teamRecommendations, setTeamRecommendations] = useState(null);
  const [personalityCoach, setPersonalityCoach] = useState(null);
  const [careerSimulation, setCareerSimulation] = useState(null);
  const [internshipPerformance, setInternshipPerformance] = useState(null);
  const [collaborativeProject, setCollaborativeProject] = useState(null);
  const [interviewTranscript, setInterviewTranscript] = useState(null);
  const [timeManagementAnalysis, setTimeManagementAnalysis] = useState(null);
  const [networkingSuggestions, setNetworkingSuggestions] = useState(null);
  const [internshipTracking, setInternshipTracking] = useState(null);
  const [brandingInsights, setBrandingInsights] = useState(null);
  const [fakeResumeReport, setFakeResumeReport] = useState(null);
  const [careerTimeline, setCareerTimeline] = useState(null);
  const [resumeKeywordOptimization, setResumeKeywordOptimization] = useState(null);
  const [voiceInterviewResult, setVoiceInterviewResult] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageForm, setMessageForm] = useState({ recipient_id: "", body: "" });
  const [coverNotes, setCoverNotes] = useState({});
  const [applicationDrafts, setApplicationDrafts] = useState({});
  const [resume, setResume] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [selectedMatchJobId, setSelectedMatchJobId] = useState("");
  const [matchResult, setMatchResult] = useState(null);
  const [skillGapRole, setSkillGapRole] = useState("frontend developer");
  const [skillGapResult, setSkillGapResult] = useState(null);
  const [interviewConfig, setInterviewConfig] = useState({
    target_role: "Frontend Developer",
    difficulty: "beginner",
  });
  const [interviewQuestions, setInterviewQuestions] = useState(null);
  const [resumeBuilder, setResumeBuilder] = useState({
    full_name: "",
    email: "",
    phone: "",
    location: "",
    professional_summary: "",
    skills: "",
    projects: "",
  });
  const [resumePdfResult, setResumePdfResult] = useState(null);
  const [message, setMessage] = useState("Ready.");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!hasSession()) {
      loadPublicJobs();
      return;
    }
    runAction(async () => {
      await loadDashboardData();
    }, "Session restored.");
  }, []);

  useEffect(() => {
    const profileInfo = profile?.profile || {};
    if (!profileInfo) return;
    setResumeBuilder((current) => ({
      ...current,
      full_name: current.full_name || [profile?.user?.first_name, profile?.user?.last_name].filter(Boolean).join(" ") || current.full_name,
      email: current.email || profile?.user?.email || current.email,
      phone: current.phone || profileInfo.phone || current.phone,
      location: current.location || profileInfo.location || current.location,
      professional_summary: current.professional_summary || profileInfo.bio || profileInfo.about || current.professional_summary,
      skills: current.skills || (profileInfo.skills || []).join(", "),
      projects: current.projects || (profileInfo.portfolio_items || []).map((item) => item.name || item.title).filter(Boolean).join(", "),
    }));
  }, [profile]);

  const dashboardJobs = jobs.length ? jobs : fallbackJobs;
  const topRecommendations = recommendations.length ? recommendations : dashboardJobs.slice(0, 3);
  const appliedJobIds = useMemo(() => new Set(applications.map((application) => application.job?.id)), [applications]);

  const profileStrength = useMemo(() => {
    if (!profile?.profile) {
      return 18;
    }
    const checks = [
      profile.profile.headline,
      profile.profile.location,
      profile.profile.bio,
      profile.profile.about,
      profile.profile.github_url || profile.profile.linkedin_url,
      splitList(profile.profile.skills).length >= 3,
      resume,
    ];
    return Math.max(18, Math.round((checks.filter(Boolean).length / checks.length) * 100));
  }, [profile, resume]);

  useEffect(() => {
    if (!profile?.user) {
      return;
    }
    setResumeBuilder((current) => ({
      ...current,
      full_name: current.full_name || displayName(profile),
      email: current.email || profile.user.email || "",
      location: current.location || profile.profile?.location || "",
      professional_summary: current.professional_summary || profile.profile?.bio || profile.profile?.headline || "",
      skills: current.skills || splitList(profile.profile?.skills).join(", "),
    }));
  }, [profile]);

  async function runAction(action, onSuccessMessage) {
    setLoading(true);
    try {
      await action();
      setMessage(onSuccessMessage);
    } catch (error) {
      setMessage(error.message || "Unexpected error.");
    } finally {
      setLoading(false);
    }
  }

  async function loadPublicJobs() {
    try {
      const jobsPayload = await listJobs();
      setJobs(jobsPayload.jobs || []);
    } catch {
      setJobs([]);
    }
  }

  function syncProfileForm(payload) {
    const profilePayload = payload?.profile || {};
    setProfileForm({
      headline: profilePayload.headline || "",
      location: profilePayload.location || "",
      bio: profilePayload.bio || "",
      about: profilePayload.about || "",
      skills: splitList(profilePayload.skills).join(", "),
      github_url: profilePayload.github_url || "",
      linkedin_url: profilePayload.linkedin_url || "",
    });
  }

  async function loadDashboardData() {
    const [profilePayload, jobsPayload, resumePayload, applicationPayload, messagePayload] = await Promise.all([
      getProfile(),
      listJobs(),
      latestResume(),
      listApplications(),
      listMessages(),
    ]);

    setProfile(profilePayload);
    syncProfileForm(profilePayload);
    setJobs(jobsPayload.jobs || []);
    setResume(resumePayload.resume || null);
    setApplications(applicationPayload.applications || []);
    setMessages(messagePayload.messages || []);

    const role = profilePayload?.user?.role;
    if (role === "recruiter" || role === "admin") {
      const postedPayload = await myJobs();
      setPostedJobs(postedPayload.jobs || []);
    } else {
      setPostedJobs([]);
    }

    if (role === "student") {
      const [recommendationPayload, guidancePayload, coachPayload, pathPayload, roadmapPayload, reputationPayload, teamPayload, keywordPayload, networkingPayload, attendancePayload, brandingPayload, fakePayload, timelinePayload, personalityPayload, simulationPayload, internshipPerformancePayload, projectPayload, transcriptPayload, timePayload] = await Promise.all([
        getRecommendations(),
        getCareerGuidance(),
        getCareerCoach().catch(() => null),
        getCareerPathPrediction().catch(() => null),
        getInternshipRoadmap().catch(() => null),
        getCandidateReputationScore().catch(() => null),
        getTeamRecommendations().catch(() => null),
        optimizeResumeKeywords().catch(() => null),
        getNetworkingSuggestions().catch(() => null),
        getInternshipAttendanceTracking().catch(() => null),
        getPersonalBrandingAssistant().catch(() => null),
        detectFakeResume().catch(() => null),
        getCareerTimeline().catch(() => null),
        getPersonalityDevelopmentCoach().catch(() => null),
        getInteractiveCareerSimulationEngine().catch(() => null),
        getSmartInternshipPerformanceEvaluation().catch(() => null),
        getCollaborativeProjectBuilder().catch(() => null),
        getAutomatedInterviewTranscriptGenerator().catch(() => null),
        getAiTimeManagementAnalyzer().catch(() => null),
      ]);
      setRecommendations(recommendationPayload.recommendations || []);
      setCareerGuidance(guidancePayload);
      setCareerCoach(coachPayload);
      setCareerPathPrediction(pathPayload);
      setInternshipRoadmap(roadmapPayload);
      setReputationScore(reputationPayload);
      setTeamRecommendations(teamPayload);
      setResumeKeywordOptimization(keywordPayload);
      setNetworkingSuggestions(networkingPayload);
      setInternshipTracking(attendancePayload);
      setBrandingInsights(brandingPayload);
      setFakeResumeReport(fakePayload);
      setCareerTimeline(timelinePayload);
      setPersonalityCoach(personalityPayload);
      setCareerSimulation(simulationPayload);
      setInternshipPerformance(internshipPerformancePayload);
      setCollaborativeProject(projectPayload);
      setInterviewTranscript(transcriptPayload);
      setTimeManagementAnalysis(timePayload);
    } else {
      setRecommendations([]);
      setCareerGuidance(null);
      setCareerCoach(null);
      setCareerPathPrediction(null);
      setInternshipRoadmap(null);
      setReputationScore(null);
      setTeamRecommendations(null);
      setNetworkingSuggestions(null);
      setInternshipTracking(null);
      setBrandingInsights(null);
      setFakeResumeReport(null);
      setCareerTimeline(null);
      setPersonalityCoach(null);
      setCareerSimulation(null);
      setInternshipPerformance(null);
      setCollaborativeProject(null);
      setInterviewTranscript(null);
      setTimeManagementAnalysis(null);
      setResumeKeywordOptimization(null);
    }
  }

  async function runVoiceSimulation() {
    const profileSkills = splitList(profile?.profile?.skills).join(", ") || "Python, React, communication";
    const sampleTranscript = `I recently built a project using ${profileSkills}. First, I planned the architecture, then implemented APIs and frontend flows, and finally measured improvements in response time and user adoption.`;
    const result = await simulateVoiceInterview("Software Engineer", sampleTranscript);
    setVoiceInterviewResult(result);
  }

  async function runKeywordOptimization() {
    const result = await optimizeResumeKeywords();
    setResumeKeywordOptimization(result);
  }

  const canPostJobs = profile?.user?.role === "recruiter" || profile?.user?.role === "admin";

  async function runAiMatchScore() {
    if (!resume?.id) {
      throw new Error("Upload a resume first.");
    }
    const jobId = selectedMatchJobId || topRecommendations.find((job) => !String(job.id).startsWith("sample"))?.id;
    if (!jobId) {
      throw new Error("No live job is available for match scoring.");
    }
    const result = await calculateAIMatch(jobId, resume.id);
    setSelectedMatchJobId(String(jobId));
    setMatchResult(result);
  }

  async function runSkillGapAnalysis() {
    const result = await analyzeSkillGap(skillGapRole);
    setSkillGapResult(result);
  }

  async function runInterviewGenerator() {
    const result = await generateAIInterviewQuestions(interviewConfig);
    setInterviewQuestions(result);
  }

  async function runResumePdfBuilder() {
    const template = {
      ...resumeBuilder,
      skills: splitList(resumeBuilder.skills),
      projects: splitList(resumeBuilder.projects).map((project) => ({ name: project, description: "Portfolio-ready project", skills_used: [] })),
    };
    const result = await generateResumePDF(template, "modern");
    setResumePdfResult(result);
  }

  function SignupPage() {
    return (
      <AuthLayout message={message}>
        <article className="authCard">
          <h2>Create your account</h2>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              runAction(
                async () => {
                  const payload = await signup(signupData);
                  setDebugVerificationPath(payload?.debug?.verification_path || "");
                  setResendEmail(signupData.email);
                  setSignupData(initialSignup);
                },
                "Account created. Verify your email before login."
              );
            }}
          >
            <div className="twoCol">
              {field("First name", signupData.first_name, (event) => setSignupData({ ...signupData, first_name: event.target.value }), "text", true)}
              {field("Last name", signupData.last_name, (event) => setSignupData({ ...signupData, last_name: event.target.value }), "text", true)}
            </div>
            {field("Email", signupData.email, (event) => setSignupData({ ...signupData, email: event.target.value }), "email", true)}
            {field("Password", signupData.password, (event) => setSignupData({ ...signupData, password: event.target.value }), "password", true)}
            <label className="field">
              <span>Role</span>
              <select value={signupData.role} onChange={(event) => setSignupData({ ...signupData, role: event.target.value })}>
                <option value="student">Student</option>
                <option value="recruiter">Recruiter</option>
              </select>
            </label>
            {signupData.role === "student"
              ? field("University", signupData.university_name, (event) => setSignupData({ ...signupData, university_name: event.target.value, company_name: "" }), "text", true)
              : field("Company", signupData.company_name, (event) => setSignupData({ ...signupData, company_name: event.target.value, university_name: "" }), "text", true)}
            <button disabled={loading} type="submit">{loading ? "Creating..." : "Join AIJobPlatform"}</button>
          </form>
          {debugVerificationPath ? (
            <Link className="debugLink" to={debugVerificationPath}>
              Verify this development account
            </Link>
          ) : null}
          <div className="divider" />
          {field("Resend verification email", resendEmail, (event) => setResendEmail(event.target.value), "email", false)}
          <button className="ghostButton" type="button" disabled={loading || !resendEmail} onClick={() => runAction(() => resendVerification(resendEmail), "Verification email sent if the account exists.")}>
            Resend verification
          </button>
        </article>
      </AuthLayout>
    );
  }

  function LoginPage() {
    return (
      <AuthLayout message={message}>
        <article className="authCard">
          <h2>Login</h2>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              runAction(
                async () => {
                  await login(loginData);
                  await loadDashboardData();
                  navigate("/dashboard", { replace: true });
                },
                "Login successful."
              );
            }}
          >
            {field("Email", loginData.email, (event) => setLoginData({ ...loginData, email: event.target.value }), "email", true)}
            {field("Password", loginData.password, (event) => setLoginData({ ...loginData, password: event.target.value }), "password", true)}
            <button disabled={loading} type="submit">{loading ? "Opening..." : "Open workspace"}</button>
          </form>
          <Link className="subtleLink" to="/forgot-password">Forgot your password?</Link>
        </article>
      </AuthLayout>
    );
  }

  function ForgotPasswordPage() {
    return (
      <AuthLayout message={message}>
        <article className="authCard">
          <h2>Reset password</h2>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              runAction(
                async () => {
                  const payload = await forgotPassword(forgotEmail);
                  setDebugResetPath(payload?.debug?.reset_path || "");
                },
                "Password reset email sent if the account exists."
              );
            }}
          >
            {field("Email", forgotEmail, (event) => setForgotEmail(event.target.value), "email", true)}
            <button disabled={loading} type="submit">Send reset link</button>
          </form>
          {debugResetPath ? (
            <Link className="debugLink" to={debugResetPath}>
              Open development reset link
            </Link>
          ) : null}
        </article>
      </AuthLayout>
    );
  }

  function VerifyEmailPage() {
    const { token } = useParams();
    return (
      <AuthLayout message={message}>
        <article className="authCard">
          <h2>Email verification</h2>
          <p>Confirm your account and then return to login.</p>
          <button type="button" disabled={loading || !token} onClick={() => runAction(() => verifyEmail(token), "Email verified. You can log in now.")}>
            Verify email
          </button>
        </article>
      </AuthLayout>
    );
  }

  function ResetPasswordPage() {
    const { token } = useParams();
    return (
      <AuthLayout message={message}>
        <article className="authCard">
          <h2>Choose a new password</h2>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              runAction(() => resetPassword(token, resetPasswordValue), "Password reset successful. Please login.");
            }}
          >
            {field("New password", resetPasswordValue, (event) => setResetPasswordValue(event.target.value), "password", true)}
            <button disabled={loading || !token} type="submit">Reset password</button>
          </form>
        </article>
      </AuthLayout>
    );
  }

  function ProfileRail() {
    const skills = splitList(profile?.profile?.skills).slice(0, 6);
    return (
      <aside className="profileRail">
        <section className="profileCard">
          <div className="coverStrip" />
          <div className="avatar">{initials(profile)}</div>
          <h2>{displayName(profile)}</h2>
          <p>{profile?.profile?.headline || "Add a headline to help recruiters understand your edge."}</p>
          <span>{profile?.profile?.location || profile?.user?.university_name || profile?.user?.company_name || "Location not set"}</span>
        </section>

        <section className="panel">
          <div className="metricHeader">
            <span>Profile strength</span>
            <strong>{profileStrength}%</strong>
          </div>
          <div className="progressTrack"><span style={{ width: `${profileStrength}%` }} /></div>
          <p className="muted">Complete your headline, skills, links, and resume to improve matching.</p>
        </section>

        <section className="panel">
          <h3>Skills</h3>
          <div className="skillLine compact">
            {(skills.length ? skills : ["React", "Python", "AI", "Communication"]).map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </section>
      </aside>
    );
  }

  function FeedComposer() {
    return (
      <section className="composer">
        <div className="avatar smallAvatar">{initials(profile)}</div>
        <div>
          <strong>{displayName(profile)}</strong>
          <p>{profile?.user?.role === "recruiter" ? "Share hiring updates or post a new role from the recruiter tab." : "Keep your profile fresh so the AI matcher has better signal."}</p>
        </div>
      </section>
    );
  }

  function CareerGuidancePanel() {
    const guidance = careerGuidance || {
      skills: splitList(profile?.profile?.skills),
      roadmap: ["Upload a resume and complete your profile to unlock guidance."],
      role_targets: [],
      growth_insights: [],
      weekly_tips: [],
      job_alerts: [],
    };
    const jobAlerts = guidance.job_alerts || [];

    return (
      <section className="panel">
        <div className="sectionHeader">
          <p className="eyebrow">AI career guidance</p>
          <h2>Roadmap and growth insights</h2>
        </div>
        <div className="stat-cards small">
          <div className="stat-card">
            <h4>Profile strength</h4>
            <div className="stat-value">{guidance.profile_strength ?? profileStrength}%</div>
          </div>
          <div className="stat-card">
            <h4>Resume rating</h4>
            <div className="stat-value">{guidance.resume_rating ?? 0}%</div>
          </div>
          <div className="stat-card">
            <h4>Job alerts</h4>
            <div className="stat-value">{jobAlerts.length}</div>
          </div>
        </div>
        <div className="skillLine compact">
          {(guidance.skills?.length ? guidance.skills : ["Add skills to personalize guidance"]).map((skill) => (
            <span key={skill}>{skill}</span>
          ))}
        </div>
        <ol className="roadmapList">
          {(guidance.roadmap || []).map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
        <div className="insightList">
          {(guidance.growth_insights || []).map((insight) => (
            <p key={insight}>{insight}</p>
          ))}
        </div>
        <div className="roadmapListInline">
          {(guidance.weekly_tips || []).slice(0, 3).map((tip) => (
            <div className="roadmapStep" key={tip}>
              <strong>Weekly tip</strong>
              <span>{tip}</span>
            </div>
          ))}
        </div>
        {jobAlerts.length > 0 && (
          <div className="roadmapListInline">
            {jobAlerts.slice(0, 3).map((alert) => (
              <div className="roadmapStep" key={`${alert.job?.id}-${alert.match_percentage}`}>
                <strong>{alert.job?.title || "Job alert"}</strong>
                <span>{alert.message}</span>
                <span>{(alert.missing_skills || []).join(", ") || "No major gaps"}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    );
  }

  function SkillVerificationPanel() {
    const skillInput = splitList(profile?.profile?.skills).slice(0, 1)[0] || "Python";

    return (
      <section className="panel">
        <div className="sectionHeader">
          <p className="eyebrow">Skill verification</p>
          <h2>Mini tests and badge system</h2>
        </div>
        <div className="roadmapListInline">
          <div className="roadmapStep">
            <strong>DSA test</strong>
            <span>Run a quick coding challenge to earn a verified badge.</span>
          </div>
          <div className="roadmapStep">
            <strong>React test</strong>
            <span>Validate frontend skill and assign Silver/Gold badges.</span>
          </div>
          <div className="roadmapStep">
            <strong>Certificate import</strong>
            <span>Upload evidence to store a linked verification badge.</span>
          </div>
        </div>
        <div className="buttonRow">
          <button type="button" disabled={loading} onClick={() => runAction(async () => {
            const formData = new FormData();
            formData.append("skill_name", skillInput);
            formData.append("certificate", new Blob(["verified"], { type: "text/plain" }), "verification.txt");
            await uploadSkillCertificate(formData);
          }, "Skill certificate uploaded.")}>Verify {skillInput}</button>
          <button type="button" className="ghostButton" disabled={loading} onClick={() => runAction(async () => {
            await connectGitHubBadges();
          }, "GitHub badge connected.")}>Connect GitHub</button>
        </div>
      </section>
    );
  }

  function StudentImpactStudio() {
    const liveJobs = dashboardJobs.filter((job) => !String(job.id).startsWith("sample"));
    const selectedJob = dashboardJobs.find((job) => String(job.id) === String(selectedMatchJobId)) || liveJobs[0] || dashboardJobs[0];
    const matchSuggestions = matchResult?.improvement_suggestions || buildResumeSuggestions({ profile, resume, careerCoach });
    const skillRecommendations = matchResult?.skill_recommendations || [];

    return (
      <section className="panel impactStudio">
        <div className="sectionHeader inline">
          <div>
            <p className="eyebrow">Impact features</p>
            <h2>AI match, skill gap, interview prep, resume builder</h2>
          </div>
          <span className="featurePill">Top 5</span>
        </div>

        <div className="impactGrid">
          <article className="toolCard">
            <div className="toolHeader">
              <div>
                <h3>Resume vs job match</h3>
                <p className="muted">Percentage score, missing skills, and improve-resume suggestions.</p>
              </div>
              <strong className="bigMetric">{matchResult ? `${matchResult.match_percentage}%` : "--"}</strong>
            </div>
            <label className="field">
              <span>Job description</span>
              <select value={selectedMatchJobId} onChange={(event) => setSelectedMatchJobId(event.target.value)}>
                <option value="">Auto-pick best live job</option>
                {liveJobs.map((job) => (
                  <option key={job.id} value={job.id}>{job.title} - {job.company}</option>
                ))}
              </select>
            </label>
            <button type="button" disabled={loading || !resume?.id} onClick={() => runAction(runAiMatchScore, "AI match score calculated.")}>
              Calculate match score
            </button>
            {matchResult ? (
              <>
                <div className="scoreGrid">
                  <span>Skills {matchResult.skills_alignment}%</span>
                  <span>Experience {matchResult.experience_alignment}%</span>
                  <span>Culture {matchResult.culture_fit}%</span>
                  <span>Growth {matchResult.growth_potential}%</span>
                </div>
                <div className="skillLine compact">
                  {((matchResult.missing_skills_required?.length ? matchResult.missing_skills_required : matchResult.missing_skills)?.length
                    ? (matchResult.missing_skills_required?.length ? matchResult.missing_skills_required : matchResult.missing_skills)
                    : ["No major missing skills"]).map((skill) => <span key={skill}>{skill}</span>)}
                </div>
                {skillRecommendations.length > 0 && (
                  <div className="roadmapListInline">
                    {skillRecommendations.slice(0, 3).map((item) => (
                      <div className="roadmapStep" key={`${item.skill}-${item.priority}`}>
                        <strong>{item.skill}</strong>
                        <span>{item.reason}</span>
                        <span>{item.action}</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <p className="muted">Selected: {selectedJob?.title || "Upload resume and select a job."}</p>
            )}
            <ul className="bulletList">
              {matchSuggestions.slice(0, 3).map((item) => <li key={item}>{item}</li>)}
            </ul>
          </article>

          <article className="toolCard">
            <h3>Smart skill gap analyzer</h3>
            <div className="buttonRow">
              <select value={skillGapRole} onChange={(event) => setSkillGapRole(event.target.value)}>
                <option value="frontend developer">Frontend Developer</option>
                <option value="backend developer">Backend Developer</option>
                <option value="full stack developer">Full Stack Developer</option>
                <option value="data scientist">Data Scientist</option>
              </select>
              <button type="button" disabled={loading} onClick={() => runAction(runSkillGapAnalysis, "Skill gap roadmap generated.")}>
                Analyze
              </button>
            </div>
            <div className="skillLine compact">
              {(skillGapResult?.missing_skills?.length ? skillGapResult.missing_skills : ["Run analysis to see missing technologies"]).map((skill) => <span key={skill}>{skill}</span>)}
            </div>
            <div className="roadmapListInline">
              {(skillGapResult?.learning_paths || []).slice(0, 4).map((path) => (
                <div className="roadmapStep" key={path.skill}>
                  <strong>{path.skill}</strong>
                  <span>{path.resource || "Build one mini project and practice interview questions."}</span>
                </div>
              ))}
            </div>
          </article>

          <article className="toolCard">
            <h3>AI interview questions</h3>
            <div className="twoCol">
              <input value={interviewConfig.target_role} onChange={(event) => setInterviewConfig({ ...interviewConfig, target_role: event.target.value })} placeholder="Role" />
              <select value={interviewConfig.difficulty} onChange={(event) => setInterviewConfig({ ...interviewConfig, difficulty: event.target.value })}>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
            <button type="button" disabled={loading} onClick={() => runAction(runInterviewGenerator, "Interview set generated.")}>
              Generate questions
            </button>
            <ol className="roadmapList compactList">
              {(interviewQuestions?.questions || ["Generate role-based questions with MCQ and coding round."]).slice(0, 4).map((question) => <li key={question}>{question}</li>)}
            </ol>
            {interviewQuestions?.coding_round ? <p className="status compactStatus">{interviewQuestions.coding_round.prompt}</p> : null}
          </article>

          <article className="toolCard">
            <h3>ATS resume builder</h3>
            <div className="twoCol">
              <input value={resumeBuilder.full_name} onChange={(event) => setResumeBuilder({ ...resumeBuilder, full_name: event.target.value })} placeholder="Full name" />
              <input value={resumeBuilder.email} onChange={(event) => setResumeBuilder({ ...resumeBuilder, email: event.target.value })} placeholder="Email" />
            </div>
            <textarea value={resumeBuilder.professional_summary} onChange={(event) => setResumeBuilder({ ...resumeBuilder, professional_summary: event.target.value })} placeholder="Professional summary" />
            <input value={resumeBuilder.skills} onChange={(event) => setResumeBuilder({ ...resumeBuilder, skills: event.target.value })} placeholder="Skills, comma separated" />
            <input value={resumeBuilder.projects} onChange={(event) => setResumeBuilder({ ...resumeBuilder, projects: event.target.value })} placeholder="Projects, comma separated" />
            <button type="button" disabled={loading} onClick={() => runAction(runResumePdfBuilder, "Resume PDF template generated.")}>
              Generate PDF template
            </button>
            {resumePdfResult ? <p className="status compactStatus">{resumePdfResult.message || "PDF template is ready."}</p> : null}
          </article>
        </div>
      </section>
    );
  }

  function CandidateRankingPanel() {
    const rankedApplications = [...applications].sort((left, right) => (right.match_score || 0) - (left.match_score || 0)).slice(0, 8);

    return (
      <section className="panel">
        <div className="sectionHeader">
          <p className="eyebrow">AI candidate ranking</p>
          <h2>Applicants sorted by skills and experience</h2>
        </div>
        <div className="candidateRankList">
          {rankedApplications.length ? rankedApplications.map((application, index) => (
            <article className="candidateRankCard" key={application.id}>
              <div>
                <strong>{index + 1}. {application.applicant?.name}</strong>
                <p>{application.job?.title} - {application.applicant?.headline || "Candidate profile"}</p>
                <div className="skillLine compact">
                  {splitList(application.applicant?.skills).slice(0, 5).map((skill) => <span key={`${application.id}-${skill}`}>{skill}</span>)}
                </div>
              </div>
              <div className="rankActions">
                <span className="chip strong">{application.match_score || 0} pts</span>
                <button type="button" disabled={loading} onClick={() => runAction(async () => {
                  await updateApplicationStatus(application.id, "shortlisted");
                  const payload = await listApplications();
                  setApplications(payload.applications || []);
                }, "Candidate shortlisted.")}>Shortlist</button>
                <button className="ghostButton" type="button" disabled={loading} onClick={() => runAction(async () => {
                  await updateApplicationStatus(application.id, "rejected");
                  const payload = await listApplications();
                  setApplications(payload.applications || []);
                }, "Candidate rejected.")}>Reject</button>
              </div>
            </article>
          )) : <p className="muted">No applicants yet. Post a job to start ranking candidates.</p>}
        </div>
      </section>
    );
  }

  function NetworkingPanel() {
    const possibleRecipients = applications
      .map((application) => (profile?.user?.role === "student" ? application.job?.posted_by : application.applicant))
      .filter(Boolean);
    const uniqueRecipients = Array.from(new Map(possibleRecipients.map((person) => [person.id, person])).values());

    return (
      <section className="panel">
        <div className="sectionHeader inline">
          <div>
            <p className="eyebrow">Network</p>
            <h2>Messages and collaboration</h2>
          </div>
          <button className="ghostButton fitButton" disabled={loading} onClick={() => runAction(async () => {
            const payload = await listMessages();
            setMessages(payload.messages || []);
          }, "Messages refreshed.")} type="button">
            Refresh
          </button>
        </div>
        <form
          className="messageForm"
          onSubmit={(event) => {
            event.preventDefault();
            runAction(
              async () => {
                await sendMessage(messageForm.recipient_id, messageForm.body);
                setMessageForm({ recipient_id: "", body: "" });
                const payload = await listMessages();
                setMessages(payload.messages || []);
              },
              "Message sent."
            );
          }}
        >
          <label className="field">
            <span>Recipient</span>
            <select value={messageForm.recipient_id} onChange={(event) => setMessageForm({ ...messageForm, recipient_id: event.target.value })}>
              <option value="">Choose a contact</option>
              {uniqueRecipients.map((person) => (
                <option key={person.id} value={person.id}>
                  {person.name || person.email}
                </option>
              ))}
            </select>
          </label>
          {textareaField("Message", messageForm.body, (event) => setMessageForm({ ...messageForm, body: event.target.value }), true, "Write a short collaboration note.")}
          <button disabled={loading || !messageForm.recipient_id || !messageForm.body} type="submit">Send message</button>
        </form>
        <div className="messageList">
          {(messages.length ? messages.slice(-5).reverse() : []).map((item) => (
            <article className="messageBubble" key={item.id}>
              <strong>{item.sender?.name} to {item.recipient?.name}</strong>
              <p>{item.body}</p>
            </article>
          ))}
          {!messages.length ? <p className="muted">Apply to jobs or receive applicants to start a conversation.</p> : null}
        </div>
      </section>
    );
  }

  function ApplicationList({ recruiter = false }) {
    return (
      <section className="panel">
        <div className="sectionHeader">
          <p className="eyebrow">{recruiter ? "Applicants" : "Job activity"}</p>
          <h2>{recruiter ? "Manage and shortlist candidates" : "Your applications"}</h2>
        </div>
        <div className="applicationStack">
          {applications.length ? applications.map((application) => (
            <article className="applicationCard" key={application.id}>
              <div>
                <strong>{recruiter ? application.applicant?.name : application.job?.title}</strong>
                <p>{recruiter ? application.job?.title : `${application.job?.company} · ${application.job?.location}`}</p>
                <span className="chip strong">{application.match_score} match points</span>
                <span className="chip">{application.status}</span>
              </div>
              {recruiter ? (
                <select
                  value={application.status}
                  onChange={(event) =>
                    runAction(
                      async () => {
                        await updateApplicationStatus(application.id, event.target.value);
                        const payload = await listApplications();
                        setApplications(payload.applications || []);
                      },
                      "Application status updated."
                    )
                  }
                >
                  <option value="applied">Applied</option>
                  <option value="reviewing">Reviewing</option>
                  <option value="shortlisted">Shortlisted</option>
                  <option value="rejected">Rejected</option>
                </select>
              ) : null}
            </article>
          )) : <p className="muted">{recruiter ? "No applicants yet." : "No applications yet."}</p>}
        </div>
      </section>
    );
  }

  function ApplyBox({ job }) {
    const alreadyApplied = appliedJobIds.has(job.id);
    const draft = applicationDrafts[job.id] || {
      cover_note: coverNotes[job.id] || "",
      candidate_summary: "",
      portfolio_url: "",
      expected_salary: "",
    };
    return (
      <div className="applyBox">
        <textarea
          disabled={alreadyApplied}
          placeholder="Why are you a fit for this role?"
          value={draft.candidate_summary}
          onChange={(event) => setApplicationDrafts({
            ...applicationDrafts,
            [job.id]: { ...draft, candidate_summary: event.target.value },
          })}
        />
        <input
          disabled={alreadyApplied}
          placeholder="Portfolio URL"
          value={draft.portfolio_url}
          onChange={(event) => setApplicationDrafts({
            ...applicationDrafts,
            [job.id]: { ...draft, portfolio_url: event.target.value },
          })}
        />
        <input
          disabled={alreadyApplied}
          placeholder="Expected salary"
          value={draft.expected_salary}
          onChange={(event) => setApplicationDrafts({
            ...applicationDrafts,
            [job.id]: { ...draft, expected_salary: event.target.value },
          })}
        />
        <textarea
          disabled={alreadyApplied}
          placeholder="Optional note to recruiter"
          value={draft.cover_note}
          onChange={(event) => {
            setCoverNotes({ ...coverNotes, [job.id]: event.target.value });
            setApplicationDrafts({
              ...applicationDrafts,
              [job.id]: { ...draft, cover_note: event.target.value },
            });
          }}
        />
        <button
          className={alreadyApplied ? "ghostButton" : ""}
          disabled={loading || alreadyApplied || String(job.id).startsWith("sample")}
          type="button"
          onClick={() =>
            runAction(
              async () => {
                await applyToJob(job.id, draft);
                const payload = await listApplications();
                setApplications(payload.applications || []);
              },
              "Application submitted."
            )
          }
        >
          {alreadyApplied ? "Applied" : "Apply"}
        </button>
      </div>
    );
  }

  function DashboardPage() {
    return (
      <div className="dashboardLayout">
        <ProfileRail />
        <main className="feedColumn">
          <FeedComposer />
          <section className="panel">
            <div className="sectionHeader inline">
              <div>
                <p className="eyebrow">For you</p>
                <h2>{profile?.user?.role === "student" ? "Recommended career moves" : "Talent market pulse"}</h2>
              </div>
              <button className="ghostButton fitButton" disabled={loading} onClick={() => runAction(loadDashboardData, "Dashboard refreshed.")} type="button">
                Refresh
              </button>
            </div>
            <div className="jobStack">
              {topRecommendations.map((job) => (
                <div className="jobActionCard" key={job.id}>
                  <JobCard job={job} />
                  {profile?.user?.role === "student" ? <ApplyBox job={job} /> : null}
                </div>
              ))}
            </div>
          </section>
          <SmartAIStudio
            careerCoach={careerCoach}
            careerPathPrediction={careerPathPrediction}
            internshipRoadmap={internshipRoadmap}
            jobs={dashboardJobs}
            loading={loading}
            navigate={navigate}
            onRunKeywordOptimizer={() => runAction(runKeywordOptimization, "Resume keyword optimization refreshed.")}
            onRunVoiceSimulator={() => runAction(runVoiceSimulation, "Voice interview simulation complete.")}
            profile={profile}
            reputationScore={reputationScore}
            personalityCoach={personalityCoach}
            careerSimulation={careerSimulation}
            internshipPerformance={internshipPerformance}
            collaborativeProject={collaborativeProject}
            interviewTranscript={interviewTranscript}
            timeManagementAnalysis={timeManagementAnalysis}
            networkingSuggestions={networkingSuggestions}
            internshipTracking={internshipTracking}
            brandingInsights={brandingInsights}
            fakeResumeReport={fakeResumeReport}
            refreshDashboard={() => runAction(loadDashboardData, "Dashboard refreshed.")}
            resume={resume}
            resumeKeywordOptimization={resumeKeywordOptimization}
            teamRecommendations={teamRecommendations}
            voiceInterviewResult={voiceInterviewResult}
          />
          <section className="panel">
            <div className="sectionHeader inline">
              <div>
                <p className="eyebrow">Open roles</p>
                <h2>Explore jobs</h2>
              </div>
            </div>
            <div className="jobStack">
              {dashboardJobs.map((job) => (
                <div className="jobActionCard" key={job.id}>
                  <JobCard job={job} />
                  {profile?.user?.role === "student" ? <ApplyBox job={job} /> : null}
                </div>
              ))}
            </div>
          </section>
        </main>
        <aside className="insightRail">
          <section className="panel">
            <h3>AI insights</h3>
            <div className="insightList">
              <p><strong>{dashboardJobs.length}</strong> active roles visible to your account.</p>
              <p><strong>{recommendations.length || topRecommendations.length}</strong> personalized matches ready.</p>
              <p><strong>{resume ? "Resume live" : "Resume missing"}</strong> for student matching.</p>
            </div>
          </section>
          <section className="panel">
            <h3>Workspace</h3>
            <button className="ghostButton" disabled={loading || !hasSession()} onClick={() => runAction(refreshToken, "Token refresh successful.")} type="button">
              Refresh session
            </button>
            <p className="status compactStatus">{message}</p>
          </section>
          <ApplicationList recruiter={profile?.user?.role !== "student"} />
        </aside>
      </div>
    );
  }

  function StudentDashboardPage() {
    return (
      <div className="dashboardLayout twoColumns">
        <ProfileRail />
        <main className="feedColumn">
          <section className="panel">
            <div className="sectionHeader">
              <p className="eyebrow">Student studio</p>
              <h2>Resume intelligence</h2>
            </div>
            <label className="fileDrop">
              <span>{resumeFile ? resumeFile.name : "Drop in a resume file"}</span>
              <input type="file" accept=".pdf,.doc,.docx,.txt" onChange={(event) => setResumeFile(event.target.files?.[0] || null)} />
            </label>
            <div className="buttonRow">
              <button type="button" disabled={loading || !resumeFile} onClick={() =>
                runAction(
                  async () => {
                    const payload = await uploadResume(resumeFile);
                    setResume(payload.resume);
                    const [recommendationPayload, guidancePayload, coachPayload, pathPayload] = await Promise.all([
                      getRecommendations(),
                      getCareerGuidance(),
                      getCareerCoach().catch(() => null),
                      getCareerPathPrediction().catch(() => null),
                    ]);
                    setRecommendations(recommendationPayload.recommendations || []);
                    setCareerGuidance(guidancePayload);
                    setCareerCoach(coachPayload);
                    setCareerPathPrediction(pathPayload);
                  },
                  "Resume uploaded and recommendations updated."
                )
              }>
                Upload resume
              </button>
              <button className="ghostButton" type="button" disabled={loading} onClick={() =>
                runAction(
                  async () => {
                    const [recommendationPayload, guidancePayload, pathPayload] = await Promise.all([
                      getRecommendations(),
                      getCareerGuidance(),
                      getCareerPathPrediction().catch(() => null),
                    ]);
                    setRecommendations(recommendationPayload.recommendations || []);
                    setCareerGuidance(guidancePayload);
                    setCareerPathPrediction(pathPayload);
                  },
                  "Recommendations refreshed."
                )
              }>
                Re-score jobs
              </button>
            </div>
            <p className="muted">Latest resume: {resume?.original_name || "No resume uploaded yet."}</p>
          </section>

          <section className="panel">
            <div className="sectionHeader">
              <p className="eyebrow">AI matches</p>
              <h2>Best roles from your resume</h2>
            </div>
            <div className="jobStack">
              {topRecommendations.map((job) => (
                <div className="jobActionCard" key={job.id}>
                  <JobCard featured job={job} />
                  <ApplyBox job={job} />
                </div>
              ))}
            </div>
          </section>
          <AutoApplyPanel onApplied={() => runAction(loadDashboardData, "Auto-apply finished.")} />
          <StudentImpactStudio />
          <SkillVerificationPanel />
          <SmartAIStudio
            careerCoach={careerCoach}
            careerPathPrediction={careerPathPrediction}
            internshipRoadmap={internshipRoadmap}
            jobs={dashboardJobs}
            loading={loading}
            navigate={navigate}
            onRunKeywordOptimizer={() => runAction(runKeywordOptimization, "Resume keyword optimization refreshed.")}
            onRunVoiceSimulator={() => runAction(runVoiceSimulation, "Voice interview simulation complete.")}
            profile={profile}
            reputationScore={reputationScore}
            personalityCoach={personalityCoach}
            careerSimulation={careerSimulation}
            internshipPerformance={internshipPerformance}
            collaborativeProject={collaborativeProject}
            interviewTranscript={interviewTranscript}
            timeManagementAnalysis={timeManagementAnalysis}
            networkingSuggestions={networkingSuggestions}
            internshipTracking={internshipTracking}
            brandingInsights={brandingInsights}
            fakeResumeReport={fakeResumeReport}
            refreshDashboard={() => runAction(loadDashboardData, "Dashboard refreshed.")}
            resume={resume}
            resumeKeywordOptimization={resumeKeywordOptimization}
            teamRecommendations={teamRecommendations}
            voiceInterviewResult={voiceInterviewResult}
          />
          <CareerGuidancePanel />
          <ApplicationList />
          <NetworkingPanel />
        </main>
      </div>
    );
  }

  function RecruiterDashboardPage({ view = "dashboard" }) {
    const [companyDirectory, setCompanyDirectory] = useState([]);
    const [selectedCompanyId, setSelectedCompanyId] = useState("");
    const [selectedJobId, setSelectedJobId] = useState("");

    useEffect(() => {
      let mounted = true;
      listCompanies()
        .then((payload) => {
          if (mounted) {
            setCompanyDirectory(payload.companies || []);
          }
        })
        .catch(() => {
          if (mounted) {
            setCompanyDirectory([]);
          }
        });
      return () => {
        mounted = false;
      };
    }, []);

    const selectedCompany = companyDirectory.find((company) => String(company.id) === String(selectedCompanyId));
    const selectedJob = postedJobs.find((job) => String(job.id) === String(selectedJobId));
    const isDashboardView = view === "dashboard";
    const isJobsView = view === "jobs";
    const isApplicantsView = view === "applicants";
    const isAssistantView = view === "assistant";

    useEffect(() => {
      if (!selectedCompany) {
        return;
      }
      setJobData((current) => ({
        ...current,
        company: selectedCompany.name,
        location: selectedCompany.location || current.location,
        skills_required: current.skills_required || suggestRequirementsFromCompany(selectedCompany).join(", "),
        description: current.description || selectedCompany.description || current.description,
      }));
    }, [selectedCompany]);

    useEffect(() => {
      if (!selectedJob) {
        return;
      }
      setJobData({
        title: selectedJob.title || "",
        company: selectedJob.company || "",
        location: selectedJob.location || "",
        description: selectedJob.description || "",
        skills_required: selectedJob.skills_required || "",
        employment_type: selectedJob.employment_type || "full-time",
        salary_range: selectedJob.salary_range || "",
      });
    }, [selectedJob]);

    async function refreshRecruiterData() {
      await loadDashboardData();
    }

    async function saveRecruiterJob() {
      const payload = {
        title: jobData.title.trim(),
        company: jobData.company.trim(),
        location: jobData.location.trim(),
        description: jobData.description.trim(),
        skills_required: jobData.skills_required.trim(),
        employment_type: jobData.employment_type,
        salary_range: jobData.salary_range.trim(),
      };

      if (selectedJobId) {
        await updateJob(selectedJobId, payload);
      } else {
        await createJob(payload);
      }

      await refreshRecruiterData();
      setSelectedJobId("");
      setSelectedCompanyId("");
      setJobData(initialJob);
    }

    async function removeRecruiterJob(jobId) {
      await deleteJob(jobId);
      if (String(selectedJobId) === String(jobId)) {
        setSelectedJobId("");
        setJobData(initialJob);
      }
      await refreshRecruiterData();
    }

    function renderDashboardSummary() {
      const activeJobs = postedJobs.filter((job) => job.is_active !== false);
      const shortlistedCount = applications.filter((application) => application.status === "shortlisted").length;
      const rejectedCount = applications.filter((application) => application.status === "rejected").length;

      return (
        <section className="panel">
          <div className="sectionHeader inline">
            <div>
              <p className="eyebrow">Recruiter dashboard</p>
              <h2>Hiring command center</h2>
            </div>
            <button className="ghostButton fitButton" disabled={loading} onClick={() => runAction(refreshRecruiterData, "Dashboard refreshed.")} type="button">
              Refresh
            </button>
          </div>
          <div className="scoreGrid">
            <span>Jobs {postedJobs.length}</span>
            <span>Active {activeJobs.length}</span>
            <span>Applicants {applications.length}</span>
            <span>Shortlisted {shortlistedCount}</span>
            <span>Rejected {rejectedCount}</span>
          </div>
          <div style={{ marginTop: 18 }}>
            <RecruiterAnalytics />
          </div>
          <div style={{ marginTop: 18 }}>
            <CandidateLeaderboard />
          </div>
          <div className="buttonRow">
            <Link className="secondaryLink" to="/recruiter/jobs">Manage jobs</Link>
            <Link className="secondaryLink" to="/recruiter/applicants">Review applicants</Link>
            <Link className="secondaryLink" to="/recruiter/assistant">AI assistant</Link>
          </div>
        </section>
      );
    }

    function renderJobManager() {
      const editableJobs = postedJobs.length ? postedJobs : dashboardJobs.slice(0, 2);

      return (
        <>
          <section className="panel">
            <div className="sectionHeader">
              <p className="eyebrow">Recruiter jobs</p>
              <h2>{selectedJob ? `Editing ${selectedJob.title}` : "Post a modern job"}</h2>
            </div>
            <form
              className="jobForm"
              onSubmit={(event) => {
                event.preventDefault();
                runAction(saveRecruiterJob, selectedJob ? "Job updated successfully." : "Job posted successfully.");
              }}
            >
              <div className="twoCol">
                {field("Job title", jobData.title, (event) => setJobData({ ...jobData, title: event.target.value }), "text", true, "Frontend Engineer")}
                {field("Company", jobData.company, (event) => setJobData({ ...jobData, company: event.target.value }), "text", false, profile?.user?.company_name || "Company")}
              </div>
              <label className="field">
                <span>Live company profile</span>
                <select
                  value={selectedCompanyId}
                  onChange={(event) => {
                    const companyId = event.target.value;
                    setSelectedCompanyId(companyId);
                    const company = companyDirectory.find((item) => String(item.id) === String(companyId));
                    if (company) {
                      setJobData((current) => ({
                        ...current,
                        company: company.name,
                        location: company.location || current.location,
                        skills_required: current.skills_required || suggestRequirementsFromCompany(company).join(", "),
                        description: current.description || company.description || current.description,
                      }));
                    }
                  }}
                >
                  <option value="">Pick a live company profile</option>
                  {companyDirectory.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name} · {company.badge_label || "Hiring"}
                    </option>
                  ))}
                </select>
              </label>
              {selectedCompany ? (
                <div className="toolCard">
                  <div className="toolHeader">
                    <h3>Live company signal</h3>
                    <span className="featurePill">Updated</span>
                  </div>
                  <p className="muted">
                    {selectedCompany.name} is rated {Number(selectedCompany.average_rating || 0).toFixed(1)} from {selectedCompany.review_count || 0} reviews.
                  </p>
                  <div className="skillLine compact">
                    {suggestRequirementsFromCompany(selectedCompany).slice(0, 5).map((skill) => (
                      <span key={skill}>{skill}</span>
                    ))}
                  </div>
                </div>
              ) : null}
              <div className="twoCol">
                {field("Location", jobData.location, (event) => setJobData({ ...jobData, location: event.target.value }), "text", true, "Remote / Bengaluru")}
                {field("Salary range", jobData.salary_range, (event) => setJobData({ ...jobData, salary_range: event.target.value }), "text", false, "12-18 LPA")}
              </div>
              {field("Skills required", jobData.skills_required, (event) => setJobData({ ...jobData, skills_required: event.target.value }), "text", false, "React, Django, SQL")}
              {textareaField("Description", jobData.description, (event) => setJobData({ ...jobData, description: event.target.value }), true, "Describe the mission, responsibilities, and outcomes.")}
              <label className="field">
                <span>Employment type</span>
                <select value={jobData.employment_type} onChange={(event) => setJobData({ ...jobData, employment_type: event.target.value })}>
                  <option value="full-time">Full-time</option>
                  <option value="part-time">Part-time</option>
                  <option value="internship">Internship</option>
                  <option value="contract">Contract</option>
                </select>
              </label>
              <div className="buttonRow">
                <button disabled={loading || !canPostJobs} type="submit">
                  {selectedJob ? "Save changes" : "Publish job"}
                </button>
                {selectedJob ? (
                  <button
                    className="ghostButton"
                    disabled={loading}
                    type="button"
                    onClick={() => {
                      setSelectedJobId("");
                      setSelectedCompanyId("");
                      setJobData(initialJob);
                    }}
                  >
                    Cancel edit
                  </button>
                ) : null}
              </div>
            </form>
          </section>

          <section className="panel">
            <div className="sectionHeader">
              <p className="eyebrow">Your jobs</p>
              <h2>Manage posted roles</h2>
            </div>
            <div className="jobStack">
              {editableJobs.length ? editableJobs.map((job) => (
                <article className="jobActionCard" key={job.id}>
                  <JobCard job={job} />
                  <div className="buttonRow">
                    <button type="button" disabled={loading} onClick={() => {
                      setSelectedJobId(String(job.id));
                      setSelectedCompanyId("");
                    }}>
                      Edit
                    </button>
                    <button className="ghostButton" type="button" disabled={loading} onClick={() => runAction(() => removeRecruiterJob(job.id), "Job deleted.")}>
                      Delete
                    </button>
                    <span className="chip">{job.is_active ? "Active" : "Inactive"}</span>
                  </div>
                </article>
              )) : <p className="muted">No jobs yet. Post one to get started.</p>}
            </div>
          </section>
        </>
      );
    }

    function renderApplicantManager() {
      return (
        <>
          <CandidateRankingPanel />
          <ApplicationList recruiter />
        </>
      );
    }

    function renderAssistantManager() {
      return <RecruiterAssistant />;
    }

    return (
      <div className="dashboardLayout twoColumns">
        <ProfileRail />
        <main className="feedColumn">
          {renderDashboardSummary()}
          {isDashboardView || isJobsView ? renderJobManager() : null}
          {isDashboardView || isApplicantsView ? renderApplicantManager() : null}
          {isDashboardView || isAssistantView ? renderAssistantManager() : null}
          <SmartAIStudio
            careerCoach={careerCoach}
            careerPathPrediction={careerPathPrediction}
            internshipRoadmap={internshipRoadmap}
            jobs={dashboardJobs}
            loading={loading}
            navigate={navigate}
            onRunKeywordOptimizer={() => runAction(runKeywordOptimization, "Resume keyword optimization refreshed.")}
            onRunVoiceSimulator={() => runAction(runVoiceSimulation, "Voice interview simulation complete.")}
            profile={profile}
            reputationScore={reputationScore}
            networkingSuggestions={networkingSuggestions}
            internshipTracking={internshipTracking}
            brandingInsights={brandingInsights}
            fakeResumeReport={fakeResumeReport}
            refreshDashboard={() => runAction(loadDashboardData, "Dashboard refreshed.")}
            resume={resume}
            resumeKeywordOptimization={resumeKeywordOptimization}
            teamRecommendations={teamRecommendations}
            voiceInterviewResult={voiceInterviewResult}
          />
          <NetworkingPanel />
        </main>
      </div>
    );
  }

  function CompanyProfilePage() {
    const { companyId } = useParams();
    return (
      <div className="dashboardLayout oneColumn">
        <main className="feedColumn">
          <Suspense fallback={<SkeletonStack />}>
            <CompanyProfile companyId={companyId} />
          </Suspense>
        </main>
      </div>
    );
  }

  function OpportunitiesPage() {
    return (
      <section className="landing">
        <div className="heroPanel">
          <div className="heroCopy">
            <p className="eyebrow">Job opportunities</p>
            <h1>Apply to live roles</h1>
            <p>
              Browse active openings, review requirements, and submit a fuller application with your summary and portfolio.
            </p>
          </div>
        </div>

        <section className="panel">
          <div className="sectionHeader inline">
            <div>
              <p className="eyebrow">Open roles</p>
              <h2>Current listings</h2>
            </div>
          </div>
          <div className="jobStack">
            {(dashboardJobs.length ? dashboardJobs : fallbackJobs).map((job) => (
              <div className="jobActionCard" key={job.id}>
                <JobCard featured job={job} />
                <ApplyBox job={job} />
              </div>
            ))}
          </div>
        </section>
      </section>
    );
  }

  function ProfileSettingsPage() {
    return (
      <div className="dashboardLayout twoColumns">
        <ProfileRail />
        <main className="feedColumn">
          <section className="panel">
            <div className="sectionHeader">
              <p className="eyebrow">Profile editor</p>
              <h2>Shape your professional identity</h2>
            </div>
            <form
              className="jobForm"
              onSubmit={(event) => {
                event.preventDefault();
                runAction(
                  async () => {
                    const payload = await updateProfile(profileForm);
                    const nextProfile = { ...profile, profile: payload.profile };
                    setProfile(nextProfile);
                    syncProfileForm(nextProfile);
                  },
                  "Profile updated successfully."
                );
              }}
            >
              <div className="twoCol">
                {field("Headline", profileForm.headline, (event) => setProfileForm({ ...profileForm, headline: event.target.value }), "text", false, "AI Engineer | React + Django")}
                {field("Location", profileForm.location, (event) => setProfileForm({ ...profileForm, location: event.target.value }), "text", false, "Pune, India")}
              </div>
              {field("Skills", profileForm.skills, (event) => setProfileForm({ ...profileForm, skills: event.target.value }), "text", false, "React, Django, Python")}
              {textareaField("Bio", profileForm.bio, (event) => setProfileForm({ ...profileForm, bio: event.target.value }), false, "A short professional summary.")}
              {textareaField("About", profileForm.about, (event) => setProfileForm({ ...profileForm, about: event.target.value }), false, "Projects, achievements, and what you want next.")}
              <div className="twoCol">
                {field("GitHub URL", profileForm.github_url, (event) => setProfileForm({ ...profileForm, github_url: event.target.value }), "url")}
                {field("LinkedIn URL", profileForm.linkedin_url, (event) => setProfileForm({ ...profileForm, linkedin_url: event.target.value }), "url")}
              </div>
              <button disabled={loading} type="submit">Save profile</button>
            </form>
          </section>
        </main>
      </div>
    );
  }

  async function handleLogout() {
    await runAction(
      async () => {
        await logout();
        setProfile(null);
        setJobs([]);
        setPostedJobs([]);
        setApplications([]);
        setRecommendations([]);
        setCareerGuidance(null);
        setCareerCoach(null);
        setCareerPathPrediction(null);
        setInternshipRoadmap(null);
        setReputationScore(null);
        setTeamRecommendations(null);
      setPersonalityCoach(null);
      setCareerSimulation(null);
      setInternshipPerformance(null);
      setCollaborativeProject(null);
      setInterviewTranscript(null);
      setTimeManagementAnalysis(null);
        setNetworkingSuggestions(null);
        setInternshipTracking(null);
        setBrandingInsights(null);
        setFakeResumeReport(null);
        setCareerTimeline(null);
        setResumeKeywordOptimization(null);
        setVoiceInterviewResult(null);
        setMessages([]);
        setResume(null);
        navigate("/login", { replace: true });
      },
      "Logged out."
    );
  }

  return (
    <main className="appShell">
      <TopNav profile={profile} loading={loading} onLogout={handleLogout} />
      <Routes>
        <Route path="/" element={hasSession() ? <Navigate to="/dashboard" replace /> : <LandingPage jobs={jobs} />} />
        <Route path="/signup" element={SignupPage()} />
        <Route path="/login" element={LoginPage()} />
        <Route path="/opportunities" element={OpportunitiesPage()} />
        <Route path="/companies" element={<CompanyDirectoryPage />} />
        <Route path="/advanced-ai" element={<AdvancedAISuitePage />} />
        <Route path="/saas" element={<ModernSaaSPage />} />
        <Route path="/forgot-password" element={ForgotPasswordPage()} />
        <Route path="/verify-email/:token" element={VerifyEmailPage()} />
        <Route path="/reset-password/:token" element={ResetPasswordPage()} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute profile={profile}>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/student"
          element={
            <ProtectedRoute profile={profile}>
              <RoleRoute profile={profile} roles={["student"]}>
                <StudentDashboardPage />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/recruiter"
          element={
            <ProtectedRoute profile={profile}>
              <RoleRoute profile={profile} roles={["recruiter", "admin"]}>
                <Navigate to="/recruiter/dashboard" replace />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/dashboard"
          element={
            <ProtectedRoute profile={profile}>
              <RoleRoute profile={profile} roles={["recruiter", "admin"]}>
                <RecruiterDashboardPage view="dashboard" />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/jobs"
          element={
            <ProtectedRoute profile={profile}>
              <RoleRoute profile={profile} roles={["recruiter", "admin"]}>
                <RecruiterDashboardPage view="jobs" />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/applicants"
          element={
            <ProtectedRoute profile={profile}>
              <RoleRoute profile={profile} roles={["recruiter", "admin"]}>
                <RecruiterDashboardPage view="applicants" />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/recruiter/assistant"
          element={
            <ProtectedRoute profile={profile}>
              <RoleRoute profile={profile} roles={["recruiter", "admin"]}>
                <RecruiterDashboardPage view="assistant" />
              </RoleRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute profile={profile}>
              <ProfileSettingsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/resume-match"
          element={
            <ProtectedRoute profile={profile}>
              <ResumeMatch />
            </ProtectedRoute>
          }
        />
        <Route
          path="/resume-comparator"
          element={
            <ProtectedRoute profile={profile}>
              <ResumeJobComparator />
            </ProtectedRoute>
          }
        />
        <Route path="/company/:companyId" element={<CompanyProfilePage />} />
        <Route path="/profile/:userId" element={<PublicProfilePage />} />
      </Routes>
    </main>
  );
}
