import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { getRecruiterDashboard } from '../api';

const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6'];

export default function RecruiterAnalytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    async function fetchData() {
      setLoading(true);
      setError('');
      try {
        const resp = await getRecruiterDashboard();
        if (!mounted) return;
        setData(resp);
      } catch (err) {
        if (!mounted) return;
        setError(err?.message || 'Failed to load analytics');
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchData();
    return () => { mounted = false; };
  }, []);

  if (loading) return <div className="analytics-card">Loading analytics...</div>;
  if (error) return <div className="analytics-card error">{error}</div>;

  const analytics = data?.analytics || data || {};
  const mostViewedJobs = data?.most_viewed_jobs || [];
  const candidateRanking = data?.candidate_ranking || [];

  const pieData = [
    { name: 'Shortlisted', value: analytics.shortlisted || 0 },
    { name: 'Hired', value: analytics.hired || 0 },
    { name: 'Others', value: Math.max((analytics.total_applications || 0) - ((analytics.shortlisted||0)+(analytics.hired||0)), 0) }
  ];

  const barData = (analytics.applications_by_stage || []).map((s) => ({ stage: s.status || s.stage || 'stage', value: s.total || s.count || 0 }));

  return (
    <section className="analytics-card panel">
      <div className="sectionHeader inline">
        <div>
          <p className="eyebrow">Analytics</p>
          <h3>Hiring insights</h3>
        </div>
      </div>

      <div className="stat-cards small">
        <div className="stat-card">
          <h4>Posted Jobs</h4>
          <div className="stat-value">{analytics.total_jobs ?? 0}</div>
        </div>
        <div className="stat-card">
          <h4>Total Applicants</h4>
          <div className="stat-value">{analytics.total_applications ?? 0}</div>
        </div>
        <div className="stat-card">
          <h4>Job Views</h4>
          <div className="stat-value">{analytics.total_views ?? 0}</div>
        </div>
        <div className="stat-card">
          <h4>Shortlisted</h4>
          <div className="stat-value">{analytics.shortlisted ?? 0}</div>
        </div>
      </div>

      <div className="analytics-charts">
        <div className="chart half">
          <h4>Applications by Stage</h4>
          {barData.length ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={barData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <XAxis dataKey="stage" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="muted">No pipeline data</p>
          )}
        </div>

        <div className="chart half">
          <h4>Status Breakdown</h4>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend verticalAlign="bottom" height={36} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {mostViewedJobs.length > 0 && (
        <div className="insightList">
          <h4>Most viewed jobs</h4>
          {mostViewedJobs.map((job) => (
            <p key={job.id}>{job.title} - {job.views_count} views, {job.applications_count} applications</p>
          ))}
        </div>
      )}

      {candidateRanking.length > 0 && (
        <div className="insightList">
          <h4>Candidate ranking</h4>
          {candidateRanking.map((candidate, index) => (
            <p key={candidate.application_id}>
              {index + 1}. {candidate.candidate_name} - {candidate.job_title} ({candidate.match_score}%)
            </p>
          ))}
        </div>
      )}
    </section>
  );
}
