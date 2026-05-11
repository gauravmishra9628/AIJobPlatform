import { useEffect, useMemo, useState } from "react";
import {
  applyToJob,
  createJob,
  detectFakeResume,
  forgotPassword,
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
  updateProfile,
  updateApplicationStatus,
  uploadResume,
  verifyEmail,
  sendMessage,
} from "./api";
import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";

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
    route: "/dashboard/recruiter",
    cta: "Open recruiter tools",
  },
  {
    title: "Tracking, chat, and alerts",
    summary: "Monitor application stages, exchange messages in real time, and keep users informed with live notifications.",
    meta: ["Applications", "Messaging", "Notifications"],
    route: "/dashboard",
    cta: "View activity",
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
      navigate("/dashboard/recruiter");
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
        { to: "/dashboard/student", label: "AI Match", studentOnly: true },
        { to: "/dashboard/recruiter", label: "Recruiter" },
        { to: "/profile", label: "Profile" },
      ]
    : [
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
  const [resume, setResume] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
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
    };

    return (
      <section className="panel">
        <div className="sectionHeader">
          <p className="eyebrow">AI career guidance</p>
          <h2>Roadmap and growth insights</h2>
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
    return (
      <div className="applyBox">
        <input
          disabled={alreadyApplied}
          placeholder="Optional note to recruiter"
          value={coverNotes[job.id] || ""}
          onChange={(event) => setCoverNotes({ ...coverNotes, [job.id]: event.target.value })}
        />
        <button
          className={alreadyApplied ? "ghostButton" : ""}
          disabled={loading || alreadyApplied || String(job.id).startsWith("sample")}
          type="button"
          onClick={() =>
            runAction(
              async () => {
                await applyToJob(job.id, coverNotes[job.id] || "");
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

  function RecruiterDashboardPage() {
    return (
      <div className="dashboardLayout twoColumns">
        <ProfileRail />
        <main className="feedColumn">
          <section className="panel">
            <div className="sectionHeader">
              <p className="eyebrow">Recruiter console</p>
              <h2>Post a modern job</h2>
            </div>
            <form
              className="jobForm"
              onSubmit={(event) => {
                event.preventDefault();
                runAction(
                  async () => {
                    await createJob(jobData);
                    setJobData(initialJob);
                    const jobsPayload = await listJobs();
                    setJobs(jobsPayload.jobs || []);
                    const postedPayload = await myJobs();
                    setPostedJobs(postedPayload.jobs || []);
                  },
                  "Job posted successfully."
                );
              }}
            >
              <div className="twoCol">
                {field("Job title", jobData.title, (event) => setJobData({ ...jobData, title: event.target.value }), "text", true, "Frontend Engineer")}
                {field("Company", jobData.company, (event) => setJobData({ ...jobData, company: event.target.value }), "text", false, profile?.user?.company_name || "Company")}
              </div>
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
              <button disabled={loading || !canPostJobs} type="submit">Publish job</button>
            </form>
          </section>

          <section className="panel">
            <div className="sectionHeader">
              <p className="eyebrow">Your jobs</p>
              <h2>Recruiter activity</h2>
            </div>
            <div className="jobStack">
              {(postedJobs.length ? postedJobs : dashboardJobs.slice(0, 2)).map((job) => (
                <JobCard key={job.id} job={job} />
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

          <ApplicationList recruiter />
          <NetworkingPanel />
        </main>
      </div>
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
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
        <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
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
                <RecruiterDashboardPage />
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
      </Routes>
    </main>
  );
}
