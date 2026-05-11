import { useEffect, useState } from "react";
import { analyzeResumeAI, getResumeAnalysis } from "../api";

export default function AIResumeAnalyzer({ resumeId }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await analyzeResumeAI(resumeId);
      setAnalysis(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resumeId) {
      handleAnalyze();
    }
  }, [resumeId]);

  if (!analysis) {
    return (
      <div className="ai-analyzer card">
        <h3>AI Resume Analyzer</h3>
        <button onClick={handleAnalyze} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze with AI"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="ai-analyzer card">
      <h2>AI Resume Analysis</h2>

      <div className="rating-display">
        <div className="overall-rating">
          <h1>{analysis.overall_rating}/100</h1>
          <p>Overall Rating</p>
        </div>
        <div className="score-metrics">
          <div className="metric">
            <span>Readability</span>
            <div className="small-progress">
              <div style={{ width: `${analysis.readability_score}%` }}></div>
            </div>
            <span className="value">{analysis.readability_score}%</span>
          </div>
          <div className="metric">
            <span>Impact</span>
            <div className="small-progress">
              <div style={{ width: `${analysis.impact_score}%` }}></div>
            </div>
            <span className="value">{analysis.impact_score}%</span>
          </div>
        </div>
      </div>

      {analysis.strengths && analysis.strengths.length > 0 && (
        <div className="section strengths">
          <h4>✓ Strengths</h4>
          <ul>
            {analysis.strengths.map((strength, idx) => (
              <li key={idx}>{strength}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.weaknesses && analysis.weaknesses.length > 0 && (
        <div className="section weaknesses">
          <h4>⚠ Areas for Improvement</h4>
          <ul>
            {analysis.weaknesses.map((weakness, idx) => (
              <li key={idx}>{weakness}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.recommendations && analysis.recommendations.length > 0 && (
        <div className="section recommendations">
          <h4>💡 Recommendations</h4>
          <ul>
            {analysis.recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.detailed_feedback && (
        <div className="feedback-box">
          <h4>Detailed Feedback</h4>
          <p>{analysis.detailed_feedback}</p>
        </div>
      )}
    </div>
  );
}
