/**
 * AI Resume Match Score Component
 * Frontend for resume-to-job matching with AI analysis
 */

import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, Send, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';
import '../styles/ResumeMatch.css';

const API_BASE = '/api';

export default function ResumeMatch() {
  // State management
  const [resume, setResume] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [matchResult, setMatchResult] = useState(null);
  const [error, setError] = useState('');
  const [userResumes, setUserResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState(null);
  const fileInputRef = useRef(null);

  // Load user's resumes on component mount
  React.useEffect(() => {
    fetchUserResumes();
  }, []);

  // Fetch user's existing resumes
  const fetchUserResumes = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/jobs/resume/match/list/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserResumes(response.data || []);
    } catch (err) {
      console.error('Error fetching resumes:', err);
      setUserResumes([]);
    }
  };

  // Handle resume file upload
  const handleResumeUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE}/jobs/resume/match/upload/`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setResume(response.data);
      setSelectedResumeId(response.data.id);
      fetchUserResumes(); // Refresh list
      setError('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload resume');
    } finally {
      setLoading(false);
    }
  };

  // Handle resume selection from existing list
  const handleSelectResume = (resumeId) => {
    const selected = userResumes.find(r => r.id === resumeId);
    setSelectedResumeId(resumeId);
    setResume(selected);
  };

  // Calculate match score
  const handleCalculateMatch = async () => {
    if (!selectedResumeId || !jobDescription.trim()) {
      setError('Please select a resume and enter a job description');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE}/jobs/resume/match/calculate/`,
        {
          resume_id: selectedResumeId,
          job_description: jobDescription
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setMatchResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to calculate match');
    } finally {
      setLoading(false);
    }
  };

  // Get color based on score
  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981'; // Green
    if (score >= 60) return '#f59e0b'; // Amber
    return '#ef4444'; // Red
  };

  // Render match percentage UI
  const MatchMeter = ({ percentage }) => (
    <div className="match-meter">
      <div className="meter-circle">
        <svg viewBox="0 0 100 100" className="meter-svg">
          <circle cx="50" cy="50" r="45" className="meter-bg" />
          <circle
            cx="50"
            cy="50"
            r="45"
            className="meter-progress"
            style={{
              strokeDasharray: `${percentage * 2.827} 282.7`,
              stroke: getScoreColor(percentage)
            }}
          />
        </svg>
        <div className="meter-text">
          <span className="meter-percentage" style={{ color: getScoreColor(percentage) }}>
            {percentage.toFixed(1)}%
          </span>
          <span className="meter-label">Match</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="resume-match-container">
      <div className="page-header">
        <h1>AI Resume Match Score</h1>
        <p>Get intelligent analysis of how well your resume matches a job</p>
      </div>

      {error && (
        <div className="error-alert">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      <div className="match-grid">
        {/* Left Column: Resume Upload */}
        <div className="match-section resume-section">
          <h2>📄 Select Your Resume</h2>

          {/* Upload New */}
          <div className="upload-area" onClick={() => fileInputRef.current?.click()}>
            <Upload size={32} />
            <p>Click to upload a resume (PDF, DOCX, TXT)</p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleResumeUpload}
              style={{ display: 'none' }}
            />
          </div>

          {/* Existing Resumes */}
          {userResumes.length > 0 && (
            <div className="resumes-list">
              <h3>Your Resumes</h3>
              {userResumes.map((r) => (
                <div
                  key={r.id}
                  className={`resume-item ${selectedResumeId === r.id ? 'active' : ''}`}
                  onClick={() => handleSelectResume(r.id)}
                >
                  <span className="resume-name">{r.original_name}</span>
                  <span className="resume-skills">
                    {r.extracted_skills?.length || 0} skills found
                  </span>
                </div>
              ))}
            </div>
          )}

          {resume && (
            <div className="resume-selected">
              <CheckCircle size={20} className="check-icon" />
              <p>
                <strong>{resume.original_name}</strong>
              </p>
              <span className="skill-count">
                {resume.extracted_skills?.length || 0} skills extracted
              </span>
            </div>
          )}
        </div>

        {/* Right Column: Job Description */}
        <div className="match-section job-section">
          <h2>💼 Job Description</h2>
          <textarea
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            className="job-textarea"
            rows={15}
          />
          <button
            onClick={handleCalculateMatch}
            disabled={loading || !resume || !jobDescription.trim()}
            className="match-button"
          >
            {loading ? 'Analyzing...' : 'Calculate Match Score'}
            <Send size={18} />
          </button>
        </div>
      </div>

      {/* Match Results */}
      {matchResult && (
        <div className="results-container">
          <div className="results-header">
            <h2>Match Analysis Results</h2>
          </div>

          <div className="results-grid">
            {/* Match Meter */}
            <div className="result-card meter-card">
              <MatchMeter percentage={matchResult.match_percentage} />
              <p className="meter-interpretation">
                {matchResult.match_percentage >= 80
                  ? 'Excellent match!'
                  : matchResult.match_percentage >= 60
                  ? 'Good match'
                  : 'Moderate match'}
              </p>
            </div>

            {/* Match Breakdown */}
            <div className="result-card breakdown-card">
              <h3>Match Breakdown</h3>
              <div className="breakdown-item">
                <span>Required Skills</span>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${matchResult.match_breakdown?.required_match || 0}%`,
                      backgroundColor: getScoreColor(matchResult.match_breakdown?.required_match || 0)
                    }}
                  />
                </div>
                <span className="percentage">
                  {(matchResult.match_breakdown?.required_match || 0).toFixed(1)}%
                </span>
              </div>

              <div className="breakdown-item">
                <span>Nice-to-Have Skills</span>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${matchResult.match_breakdown?.nice_to_have_match || 0}%`,
                      backgroundColor: getScoreColor(matchResult.match_breakdown?.nice_to_have_match || 0)
                    }}
                  />
                </div>
                <span className="percentage">
                  {(matchResult.match_breakdown?.nice_to_have_match || 0).toFixed(1)}%
                </span>
              </div>

              <div className="breakdown-item">
                <span>Experience Level</span>
                <span className="badge">
                  {matchResult.required_experience_level || 'Mid-level'}
                </span>
              </div>
            </div>

            {/* Skills Analysis */}
            <div className="result-card skills-card">
              <h3>✅ Skills You Have</h3>
              <div className="skills-list matched-skills">
                {matchResult.matched_skills?.length > 0 ? (
                  matchResult.matched_skills.map((skill, idx) => (
                    <span key={idx} className="skill-tag matched">
                      {skill}
                    </span>
                  ))
                ) : (
                  <p className="no-skills">No skills matched</p>
                )}
              </div>
            </div>

            {/* Missing Skills */}
            <div className="result-card missing-card">
              <h3>❌ Skills You're Missing</h3>
              <div className="skills-list">
                {matchResult.missing_skills_required?.length > 0 ? (
                  <>
                    <h4>Required:</h4>
                    <div className="skills-list">
                      {matchResult.missing_skills_required.map((skill, idx) => (
                        <span key={idx} className="skill-tag missing required">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </>
                ) : null}

                {matchResult.missing_skills_nice?.length > 0 ? (
                  <>
                    <h4>Nice-to-Have:</h4>
                    <div className="skills-list">
                      {matchResult.missing_skills_nice.map((skill, idx) => (
                        <span key={idx} className="skill-tag missing nice">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </>
                ) : null}

                {!matchResult.missing_skills_required?.length &&
                  !matchResult.missing_skills_nice?.length && (
                    <p className="no-skills">All skills matched!</p>
                  )}
              </div>
            </div>

            {/* Experience Gap */}
            {matchResult.experience_gap !== undefined && (
              <div className="result-card experience-card">
                <h3>📊 Experience Analysis</h3>
                <div className="experience-detail">
                  <span>Your Experience:</span>
                  <strong>{matchResult.candidate_experience_years} years</strong>
                </div>
                <div className="experience-detail">
                  <span>Required Level:</span>
                  <strong>{matchResult.required_experience_level}</strong>
                </div>
                {matchResult.experience_gap > 0 ? (
                  <p className="positive">
                    ✓ You have {matchResult.experience_gap} extra years of experience!
                  </p>
                ) : matchResult.experience_gap < 0 ? (
                  <p className="warning">
                    ⚠ You need {Math.abs(matchResult.experience_gap)} more years of experience
                  </p>
                ) : (
                  <p className="neutral">✓ Your experience matches the requirement</p>
                )}
              </div>
            )}

            {/* Improvement Suggestions */}
            {matchResult.improvement_suggestions?.length > 0 && (
              <div className="result-card suggestions-card">
                <h3>💡 Improvement Suggestions</h3>
                <div className="suggestions-list">
                  {matchResult.improvement_suggestions.map((suggestion, idx) => (
                    <div key={idx} className="suggestion-item">
                      <div className="suggestion-header">
                        <strong>{suggestion.skill}</strong>
                        <span className={`importance ${suggestion.importance}`}>
                          {suggestion.importance}
                        </span>
                      </div>
                      <p>{suggestion.tips}</p>
                      {suggestion.learning_time_weeks && (
                        <p className="learning-time">
                          ⏱️ Learning time: ~{suggestion.learning_time_weeks} weeks
                        </p>
                      )}
                      {suggestion.resources?.length > 0 && (
                        <div className="resources">
                          <p>Resources:</p>
                          <ul>
                            {suggestion.resources.map((resource, i) => (
                              <li key={i}>{resource}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
