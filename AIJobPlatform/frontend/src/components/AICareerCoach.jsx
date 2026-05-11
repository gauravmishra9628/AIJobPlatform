import { useEffect, useState } from "react";
import { generateCareerPlan, getCareerCoach } from "../api";

export default function AICareerCoach() {
  const [coach, setCoach] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [currentLevel, setCurrentLevel] = useState("junior");

  const levels = ["junior", "mid", "senior", "lead"];
  const roles = [
    "Junior Developer",
    "Senior Developer",
    "Data Scientist",
    "Product Manager",
    "DevOps Engineer",
  ];

  const fetchCoach = async () => {
    try {
      const data = await getCareerCoach();
      setCoach(data);
    } catch (err) {
      // No plan yet
    }
  };

  useEffect(() => {
    fetchCoach();
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await generateCareerPlan(targetRole, currentLevel);
      setCoach(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="career-coach card">
      <h2>🎯 AI Career Coach</h2>

      <form onSubmit={handleGenerate}>
        <div className="form-row">
          <div className="form-group">
            <label>Current Level:</label>
            <select
              value={currentLevel}
              onChange={(e) => setCurrentLevel(e.target.value)}
            >
              {levels.map((level) => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Target Role:</label>
            <select
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              required
            >
              <option value="">Select a role...</option>
              {roles.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Generating Plan..." : "Generate Career Plan"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {coach && (
        <div className="coach-results">
          <div className="journey-section">
            <h3>
              {coach.current_level} → {coach.target_level}
            </h3>
            <p>{coach.personalized_advice}</p>
          </div>

          {coach.recommended_roles && coach.recommended_roles.length > 0 && (
            <div className="roles-section">
              <h4>Recommended Career Paths</h4>
              <div className="roles-list">
                {coach.recommended_roles.map((role, idx) => (
                  <div key={idx} className="role-badge">
                    {role}
                  </div>
                ))}
              </div>
            </div>
          )}

          {coach.skill_development_plan &&
            coach.skill_development_plan.length > 0 && (
              <div className="skills-plan">
                <h4>Skill Development Plan</h4>
                <div className="plan-timeline">
                  {coach.skill_development_plan.map((item, idx) => (
                    <div key={idx} className="plan-item">
                      <div className="plan-header">
                        <h5>{item.skill}</h5>
                        <span className="timeline">{item.timeline}</span>
                      </div>
                      <p>{item.resources.join(" • ")}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

          {coach.career_milestones && coach.career_milestones.length > 0 && (
            <div className="milestones">
              <h4>Career Milestones</h4>
              <div className="milestone-list">
                {coach.career_milestones.map((milestone, idx) => (
                  <div key={idx} className="milestone">
                    <div className="milestone-title">{milestone.milestone}</div>
                    <div className="milestone-details">
                      <span>{milestone.timeline}</span>
                      <span className={`status ${milestone.status}`}>
                        {milestone.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {coach.salary_insights && Object.keys(coach.salary_insights).length > 0 && (
            <div className="salary-section">
              <h4>💰 Salary Insights</h4>
              <div className="salary-ranges">
                {Object.entries(coach.salary_insights).map(([role, range]) => (
                  <div key={role} className="salary-item">
                    <span className="role">{role}</span>
                    <span className="range">{range}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
