import { useEffect, useState } from "react";
import { analyzeSkillGap, getSkillGap } from "../api";

export default function SkillGapAnalysis() {
  const [gap, setGap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [targetRole, setTargetRole] = useState("");
  const [error, setError] = useState("");

  const rolesOptions = [
    "Junior Developer",
    "Senior Developer",
    "Data Scientist",
    "Product Manager",
    "DevOps Engineer",
    "QA Engineer",
  ];

  const fetchGap = async () => {
    try {
      const data = await getSkillGap();
      setGap(data);
    } catch (err) {
      // No gap analysis yet
    }
  };

  useEffect(() => {
    fetchGap();
  }, []);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await analyzeSkillGap(targetRole);
      setGap(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="skill-gap card">
      <h2>Skill Gap Analysis</h2>

      <form onSubmit={handleAnalyze}>
        <label>
          Target Role:
          <select 
            value={targetRole} 
            onChange={(e) => setTargetRole(e.target.value)}
            required
          >
            <option value="">Select a role...</option>
            {rolesOptions.map(role => (
              <option key={role} value={role}>{role}</option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Skills"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {gap && (
        <div className="gap-results">
          <h3>{gap.target_role}</h3>

          <div className="skills-section">
            <h4>Current Skills ({gap.current_skills.length})</h4>
            <div className="skills-list">
              {gap.current_skills.map((skill, idx) => (
                <span key={idx} className="skill-badge success">{skill}</span>
              ))}
            </div>
          </div>

          {gap.missing_skills && gap.missing_skills.length > 0 && (
            <div className="skills-section">
              <h4>Skills to Learn ({gap.missing_skills.length})</h4>
              <div className="skills-list">
                {gap.missing_skills.map((skill, idx) => (
                  <span key={idx} className="skill-badge warning">{skill}</span>
                ))}
              </div>
            </div>
          )}

          {gap.learning_paths && gap.learning_paths.length > 0 && (
            <div className="learning-section">
              <h4>Recommended Learning Paths</h4>
              <ul>
                {gap.learning_paths.map((path, idx) => (
                  <li key={idx}>
                    <strong>{path.skill}</strong>
                    {path.resource && (
                      <a href={path.resource} target="_blank" rel="noopener noreferrer">
                        Learn →
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
