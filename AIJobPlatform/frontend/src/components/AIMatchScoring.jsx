import { useEffect, useState } from "react";
import { calculateAIMatch } from "../api";

export default function AIMatchScoring({ jobId, resumeId }) {
  const [match, setMatch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCalculate = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await calculateAIMatch(jobId, resumeId);
      setMatch(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (jobId && resumeId) {
      handleCalculate();
    }
  }, [jobId, resumeId]);

  if (!match) {
    return (
      <div className="match-scoring card">
        <h3>AI Match Scoring</h3>
        <button onClick={handleCalculate} disabled={loading}>
          {loading ? "Calculating..." : "Calculate Match"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="match-scoring card">
      <h2>AI Match Score</h2>

      <div className="match-main">
        <div className="match-percentage">
          <h1>{match.match_percentage}%</h1>
          <p>Overall Match</p>
        </div>
      </div>

      <div className="match-breakdown">
        <div className="match-item">
          <span>Skills Alignment</span>
          <div className="progress">
            <div style={{ width: `${match.skills_alignment}%` }}></div>
          </div>
          <span>{match.skills_alignment}%</span>
        </div>

        <div className="match-item">
          <span>Experience Match</span>
          <div className="progress">
            <div style={{ width: `${match.experience_alignment}%` }}></div>
          </div>
          <span>{match.experience_alignment}%</span>
        </div>

        <div className="match-item">
          <span>Culture Fit</span>
          <div className="progress">
            <div style={{ width: `${match.culture_fit}%` }}></div>
          </div>
          <span>{match.culture_fit}%</span>
        </div>

        <div className="match-item">
          <span>Growth Potential</span>
          <div className="progress">
            <div style={{ width: `${match.growth_potential}%` }}></div>
          </div>
          <span>{match.growth_potential}%</span>
        </div>
      </div>

      <div className="match-details">
        {match.matched_skills && match.matched_skills.length > 0 && (
          <div className="detail-section">
            <h4>✓ Matched Skills ({match.matched_skills.length})</h4>
            <div className="skills-list">
              {match.matched_skills.map((skill, idx) => (
                <span key={idx} className="skill-badge success">{skill}</span>
              ))}
            </div>
          </div>
        )}

        {match.missing_skills && match.missing_skills.length > 0 && (
          <div className="detail-section">
            <h4>⚠ Missing Skills ({match.missing_skills.length})</h4>
            <div className="skills-list">
              {match.missing_skills.map((skill, idx) => (
                <span key={idx} className="skill-badge warning">{skill}</span>
              ))}
            </div>
          </div>
        )}

        {match.bonus_skills && match.bonus_skills.length > 0 && (
          <div className="detail-section">
            <h4>⭐ Bonus Skills ({match.bonus_skills.length})</h4>
            <div className="skills-list">
              {match.bonus_skills.map((skill, idx) => (
                <span key={idx} className="skill-badge">{skill}</span>
              ))}
            </div>
          </div>
        )}

        {match.match_reasons && (
          <div className="detail-section">
            <h4>Why This Match</h4>
            <p>{match.match_reasons}</p>
          </div>
        )}
      </div>
    </div>
  );
}
