import { useEffect, useState } from "react";
import {
  getRecruiterDashboard,
  updateRecruiterDashboard,
  saveFavoriteJob,
} from "../api";
import RecruiterAssistant from "./RecruiterAssistant";

export default function RecruiterDashboardEnhanced() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getRecruiterDashboard();
      setDashboard(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFavorite = async (jobId, isFavorited) => {
    try {
      await saveFavoriteJob(jobId, isFavorited ? "remove" : "add");
      await fetchDashboard();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className="dashboard card">Loading dashboard...</div>;
  }

  if (!dashboard) {
    return (
      <div className="dashboard card error">
        <p>{error || "Failed to load dashboard"}</p>
      </div>
    );
  }

  return (
    <div className="recruiter-dashboard card">
      <h2>📊 Recruiter Dashboard</h2>

      <div className="dashboard-tabs">
        <button
          className={activeTab === "overview" ? "active" : ""}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={activeTab === "favorites" ? "active" : ""}
          onClick={() => setActiveTab("favorites")}
        >
          Favorite Jobs
        </button>
        <button
          className={activeTab === "candidates" ? "active" : ""}
          onClick={() => setActiveTab("candidates")}
        >
          Saved Candidates
        </button>
        <button
          className={activeTab === "pipeline" ? "active" : ""}
          onClick={() => setActiveTab("pipeline")}
        >
          Pipeline
        </button>
        <button
          className={activeTab === "schedule" ? "active" : ""}
          onClick={() => setActiveTab("schedule")}
        >
          Schedule
        </button>
        <button
          className={activeTab === "assistant" ? "active" : ""}
          onClick={() => setActiveTab("assistant")}
        >
          AI Assistant
        </button>
      </div>

      <div className="dashboard-content">
        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="overview-section">
            <div className="stat-cards">
              <div className="stat-card">
                <h4>Active Postings</h4>
                <div className="stat-value">{dashboard.total_jobs_posted || 0}</div>
              </div>
              <div className="stat-card">
                <h4>Total Applications</h4>
                <div className="stat-value">
                  {dashboard.total_applications || 0}
                </div>
              </div>
              <div className="stat-card">
                <h4>Interviews Scheduled</h4>
                <div className="stat-value">
                  {dashboard.interviews_scheduled || 0}
                </div>
              </div>
              <div className="stat-card">
                <h4>Positions Filled</h4>
                <div className="stat-value">{dashboard.positions_filled || 0}</div>
              </div>
            </div>

            {dashboard.hiring_goals && Object.keys(dashboard.hiring_goals).length > 0 && (
              <div className="goals-section">
                <h4>Hiring Goals Progress</h4>
                <div className="goals-list">
                  {Object.entries(dashboard.hiring_goals).map(([role, progress]) => (
                    <div key={role} className="goal-item">
                      <div className="goal-header">
                        <span className="role">{role}</span>
                        <span className="progress-text">
                          {progress.filled}/{progress.target}
                        </span>
                      </div>
                      <div className="progress">
                        <div
                          style={{
                            width: `${(progress.filled / progress.target) * 100}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Favorites Tab */}
        {activeTab === "favorites" && (
          <div className="favorites-section">
            <h3>Favorite Jobs</h3>
            {dashboard.favorite_jobs && dashboard.favorite_jobs.length > 0 ? (
              <div className="jobs-grid">
                {dashboard.favorite_jobs.map((job) => (
                  <div key={job.id} className="job-card">
                    <div className="job-header">
                      <h4>{job.title}</h4>
                      <button
                        className="star-btn"
                        onClick={() => handleToggleFavorite(job.id, true)}
                      >
                        ★
                      </button>
                    </div>
                    <p className="company">{job.company}</p>
                    <p className="location">{job.location}</p>
                    <div className="job-stats">
                      <span>📍 {job.applications_count} Applications</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No favorite jobs saved yet</p>
            )}
          </div>
        )}

        {/* Saved Candidates Tab */}
        {activeTab === "candidates" && (
          <div className="candidates-section">
            <h3>Saved Candidates</h3>
            {dashboard.saved_candidates && dashboard.saved_candidates.length > 0 ? (
              <div className="candidates-list">
                {dashboard.saved_candidates.map((candidate) => (
                  <div key={candidate.id} className="candidate-item">
                    <div className="candidate-info">
                      <h4>{candidate.name}</h4>
                      <p className="role">{candidate.title}</p>
                      <p className="location">{candidate.location}</p>
                      {candidate.skills && (
                        <div className="skills">
                          {candidate.skills.slice(0, 3).map((skill, idx) => (
                            <span key={idx} className="skill-badge">
                              {skill}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="candidate-actions">
                      <button className="btn-primary">View Resume</button>
                      <button className="btn-secondary">Message</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No saved candidates yet</p>
            )}
          </div>
        )}

        {/* Pipeline Tab */}
        {activeTab === "pipeline" && (
          <div className="pipeline-section">
            <h3>Hiring Pipeline</h3>
            {dashboard.pipeline_stages && Object.keys(dashboard.pipeline_stages).length > 0 ? (
              <div className="pipeline">
                {Object.entries(dashboard.pipeline_stages).map(([stage, candidates]) => (
                  <div key={stage} className="pipeline-stage">
                    <h4>{stage}</h4>
                    <div className="candidate-count">{candidates.length}</div>
                    <div className="candidates">
                      {candidates.map((candidate, idx) => (
                        <div key={idx} className="candidate-badge">
                          {candidate.name}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No pipeline data available</p>
            )}
          </div>
        )}

        {/* Interview Schedule Tab */}
        {activeTab === "schedule" && (
          <div className="schedule-section">
            <h3>Interview Schedule</h3>
            {dashboard.interview_schedule &&
            dashboard.interview_schedule.length > 0 ? (
              <div className="schedule-list">
                {dashboard.interview_schedule.map((interview, idx) => (
                  <div key={idx} className="interview-item">
                    <div className="interview-time">
                      <div className="time">{interview.time}</div>
                      <div className="date">{interview.date}</div>
                    </div>
                    <div className="interview-details">
                      <h4>{interview.candidate_name}</h4>
                      <p className="position">{interview.position}</p>
                      <span className={`status ${interview.status}`}>
                        {interview.status}
                      </span>
                    </div>
                    <div className="interview-actions">
                      <button className="btn-primary">Join Interview</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No scheduled interviews</p>
            )}
          </div>
        )}

        {activeTab === "assistant" && (
          <div className="assistant-section">
            <RecruiterAssistant />
          </div>
        )}
      </div>
    </div>
  );
}
