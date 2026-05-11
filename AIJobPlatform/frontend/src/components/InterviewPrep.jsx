import { useEffect, useState } from "react";
import { generateInterviewPrep, getInterviewPrep } from "../api";

export default function InterviewPrep({ applicationId }) {
  const [prep, setPrep] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("questions");

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await generateInterviewPrep(applicationId);
      setPrep(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (applicationId) {
      handleGenerate();
    }
  }, [applicationId]);

  if (!prep) {
    return (
      <div className="interview-prep card">
        <h3>Interview Preparation</h3>
        <button onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate Interview Materials"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="interview-prep card">
      <h2>Interview Preparation for {prep.role}</h2>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === "questions" ? "active" : ""}`}
          onClick={() => setActiveTab("questions")}
        >
          Interview Questions
        </button>
        {prep.coding_problems && prep.coding_problems.length > 0 && (
          <button 
            className={`tab ${activeTab === "coding" ? "active" : ""}`}
            onClick={() => setActiveTab("coding")}
          >
            Coding Problems
          </button>
        )}
        <button 
          className={`tab ${activeTab === "tips" ? "active" : ""}`}
          onClick={() => setActiveTab("tips")}
        >
          Tips & Tricks
        </button>
        <button 
          className={`tab ${activeTab === "resources" ? "active" : ""}`}
          onClick={() => setActiveTab("resources")}
        >
          Resources
        </button>
      </div>

      <div className="tab-content">
        {activeTab === "questions" && (
          <div className="questions-section">
            <h3>Commonly Asked Questions</h3>
            <ul>
              {prep.generated_questions.map((q, idx) => (
                <li key={idx}>{q}</li>
              ))}
            </ul>
          </div>
        )}

        {activeTab === "coding" && prep.coding_problems.length > 0 && (
          <div className="coding-section">
            <h3>Practice Problems</h3>
            <ul>
              {prep.coding_problems.map((p, idx) => (
                <li key={idx}>{p}</li>
              ))}
            </ul>
          </div>
        )}

        {activeTab === "tips" && (
          <div className="tips-section">
            <h3>Interview Tips</h3>
            <ul>
              {prep.tips_and_tricks.map((tip, idx) => (
                <li key={idx}>{tip}</li>
              ))}
            </ul>
          </div>
        )}

        {activeTab === "resources" && (
          <div className="resources-section">
            <h3>Learning Resources</h3>
            <ul>
              {prep.preparation_resources.map((res, idx) => (
                <li key={idx}>
                  <a href={res.url} target="_blank" rel="noopener noreferrer">
                    {res.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
