import { useEffect, useState } from "react";
import { analyzeResumeAts } from "../api";

export default function ATSScoring({ resumeId, jobId }) {
  const [score, setScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await analyzeResumeAts(resumeId, jobId);
      setScore(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resumeId && jobId) {
      handleAnalyze();
    }
  }, [resumeId, jobId]);

  if (!score) {
    return (
      <div className="ats-scoring card">
        <h3>Resume ATS Scoring</h3>
        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Resume"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="ats-scoring card">
      <h3>ATS Compatibility Score</h3>
      
      <div className="score-display">
        <div className="main-score">
          <h2>{score.overall_score}%</h2>
          <p>Overall Score</p>
        </div>
      </div>

      <div className="score-breakdown">
        <div className="score-item">
          <span>Keywords Match:</span>
          <div className="progress-bar">
            <div style={{ width: `${score.keyword_match_score}%` }}></div>
          </div>
          <span className="percentage">{score.keyword_match_score}%</span>
        </div>
        
        <div className="score-item">
          <span>Skills Match:</span>
          <div className="progress-bar">
            <div style={{ width: `${score.skills_match_score}%` }}></div>
          </div>
          <span className="percentage">{score.skills_match_score}%</span>
        </div>
        
        <div className="score-item">
          <span>Experience:</span>
          <div className="progress-bar">
            <div style={{ width: `${score.experience_score}%` }}></div>
          </div>
          <span className="percentage">{score.experience_score}%</span>
        </div>
        
        <div className="score-item">
          <span>Format:</span>
          <div className="progress-bar">
            <div style={{ width: `${score.format_score}%` }}></div>
          </div>
          <span className="percentage">{score.format_score}%</span>
        </div>
      </div>

      {score.missing_skills && score.missing_skills.length > 0 && (
        <div className="missing-section">
          <h4>Missing Skills:</h4>
          <div className="skills-list">
            {score.missing_skills.map((skill, idx) => (
              <span key={idx} className="skill-badge">{skill}</span>
            ))}
          </div>
        </div>
      )}

      {score.improvement_suggestions && score.improvement_suggestions.length > 0 && (
        <div className="suggestions-section">
          <h4>Improvement Suggestions:</h4>
          <ul>
            {score.improvement_suggestions.map((suggestion, idx) => (
              <li key={idx}>{suggestion}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
