import { useEffect, useState } from "react";
import { getRecruiterAnalytics, getHiringTrends } from "../api";

export default function RecruiterAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timeRange, setTimeRange] = useState(30);

  const fetchAnalytics = async () => {
    try {
      const [analyticsData, trendsData] = await Promise.all([
        getRecruiterAnalytics(),
        getHiringTrends(timeRange)
      ]);
      setAnalytics(analyticsData);
      setTrends(trendsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  if (loading) return <p>Loading analytics...</p>;
  if (error) return <p className="error">{error}</p>;
  if (!analytics) return <p>No analytics data available.</p>;

  return (
    <div className="recruiter-analytics card">
      <h2>Recruiter Analytics Dashboard</h2>

      <div className="time-range">
        <label>Time Range:</label>
        <select value={timeRange} onChange={(e) => setTimeRange(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      <div className="analytics-grid">
        <div className="stat-card">
          <h3>{analytics.total_jobs_posted}</h3>
          <p>Total Jobs Posted</p>
        </div>
        
        <div className="stat-card">
          <h3>{analytics.total_applications}</h3>
          <p>Total Applications</p>
        </div>
        
        <div className="stat-card">
          <h3>{analytics.total_hired}</h3>
          <p>Candidates Hired</p>
        </div>
        
        <div className="stat-card">
          <h3>{analytics.average_time_to_hire} days</h3>
          <p>Avg. Time to Hire</p>
        </div>
        
        <div className="stat-card">
          <h3>{analytics.engagement_rate.toFixed(1)}%</h3>
          <p>Engagement Rate</p>
        </div>
      </div>

      {analytics.top_performing_jobs && analytics.top_performing_jobs.length > 0 && (
        <div className="top-jobs-section">
          <h3>Top Performing Jobs</h3>
          <table className="jobs-table">
            <thead>
              <tr>
                <th>Job Title</th>
                <th>Applications</th>
              </tr>
            </thead>
            <tbody>
              {analytics.top_performing_jobs.map((job, idx) => (
                <tr key={idx}>
                  <td>{job.title}</td>
                  <td>{job.applications}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {trends && (
        <div className="trends-section">
          <h3>Application Trends</h3>
          <div className="status-distribution">
            {Object.entries(trends.status_distribution || {}).map(([status, count]) => (
              <div key={status} className="status-item">
                <span className="status-label">{status}</span>
                <span className="status-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="last-updated">
        Updated: {new Date(analytics.updated_at).toLocaleString()}
      </p>
    </div>
  );
}
