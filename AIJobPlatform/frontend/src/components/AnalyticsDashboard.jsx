import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Briefcase, Code, FileText, Target, Award, Clock, Users, Star, ArrowUp, ArrowDown } from 'lucide-react';

const COLORS = {
  primary: '#6366f1',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
};

export default function AnalyticsDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('/api/jobs/analytics/dashboard/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  const overview = data?.overview || {};
  const applications = data?.applications || {};
  const skills = data?.skills || {};
  const interviews = data?.interviews || {};
  const resume = data?.resume || {};

  return (
    <div className="max-w-7xl mx-auto p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-800">Analytics Dashboard</h2>
          <p className="text-gray-500 mt-1">Track your job search progress and performance</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {['overview', 'applications', 'skills', 'interviews', 'resume'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                activeTab === tab
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                icon={<Briefcase className="w-6 h-6" />}
                label="Total Applications"
                value={overview.total_applications || 0}
                color="indigo"
              />
              <StatCard
                icon={<Clock className="w-6 h-6" />}
                label="Pending"
                value={overview.pending_applications || 0}
                color="yellow"
              />
              <StatCard
                icon={<Users className="w-6 h-6" />}
                label="Interviews"
                value={overview.interview_invites || 0}
                color="blue"
              />
              <StatCard
                icon={<Award className="w-6 h-6" />}
                label="Offers"
                value={overview.job_offers || 0}
                color="green"
              />
            </div>

            {/* Application Trend Chart */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Application Trend (12 Weeks)</h3>
              <SimpleBarChart data={applications.weekly_applications || []} />
            </div>

            {/* Status Breakdown */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Application Status</h3>
                <div className="space-y-3">
                  {Object.entries(applications.status_breakdown || {}).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <span className="capitalize text-gray-600">{status}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${(count / Math.max(applications.total_applications, 1)) * 100}%`,
                              backgroundColor: status === 'offer' ? '#10b981' : status === 'interview' ? '#3b82f6' : status === 'rejected' ? '#ef4444' : '#f59e0b',
                            }}
                          />
                        </div>
                        <span className="font-medium text-gray-800">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Profile Completion</h3>
                <div className="flex items-center justify-center">
                  <div className="relative w-32 h-32">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle cx="64" cy="64" r="56" stroke="#e5e7eb" strokeWidth="12" fill="none" />
                      <circle
                        cx="64" cy="64" r="56"
                        stroke="#6366f1"
                        strokeWidth="12"
                        fill="none"
                        strokeDasharray={`${(overview.profile_completion || 0) * 3.52} 352`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-2xl font-bold text-gray-800">{overview.profile_completion || 0}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Applications Tab */}
        {activeTab === 'applications' && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-3 gap-4">
              <MetricCard
                label="Response Rate"
                value={`${applications.response_rate || 0}%`}
                icon={<TrendingUp className="w-5 h-5 text-green-500" />}
              />
              <MetricCard
                label="Interview Rate"
                value={`${applications.interview_rate || 0}%`}
                icon={<TrendingUp className="w-5 h-5 text-blue-500" />}
              />
              <MetricCard
                label="Total Applied"
                value={applications.total_applications || 0}
                icon={<Briefcase className="w-5 h-5 text-indigo-500" />}
              />
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Weekly Applications</h3>
              <SimpleBarChart data={applications.weekly_applications || []} />
            </div>
          </div>
        )}

        {/* Skills Tab */}
        {activeTab === 'skills' && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-4">
              <MetricCard
                label="Total Skills"
                value={skills.total_skills || 0}
                icon={<Code className="w-5 h-5 text-indigo-500" />}
              />
              <MetricCard
                label="Avg Progress"
                value={`${Math.round(skills.average_progress || 0)}%`}
                icon={<Target className="w-5 h-5 text-green-500" />}
              />
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Skill Progress</h3>
              <div className="space-y-4">
                {(skills.skills || []).map((skill, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <div className="w-32 truncate font-medium text-gray-700">{skill.skill}</div>
                    <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${skill.progress}%`,
                          backgroundColor: skill.status === 'mastered' ? '#10b981' : skill.status === 'practicing' ? '#3b82f6' : '#f59e0b',
                        }}
                      />
                    </div>
                    <div className="w-16 text-right">
                      <span className={`text-sm font-medium ${
                        skill.status === 'mastered' ? 'text-green-600' : skill.status === 'practicing' ? 'text-blue-600' : 'text-yellow-600'
                      }`}>
                        {skill.progress}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Interviews Tab */}
        {activeTab === 'interviews' && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-3 gap-4">
              <MetricCard
                label="Total Sessions"
                value={interviews.total_sessions || 0}
                icon={<Users className="w-5 h-5 text-indigo-500" />}
              />
              <MetricCard
                label="Average Score"
                value={Math.round(interviews.average_score || 0)}
                icon={<Star className="w-5 h-5 text-yellow-500" />}
              />
              <MetricCard
                label="Trend"
                value={interviews.trend === 'improving' ? 'Improving' : interviews.trend === 'declining' ? 'Declining' : 'N/A'}
                icon={interviews.trend === 'improving' ? <ArrowUp className="w-5 h-5 text-green-500" /> : <ArrowDown className="w-5 h-5 text-red-500" />}
              />
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Interview Sessions</h3>
              <div className="space-y-4">
                {(interviews.sessions || []).map((session, i) => (
                  <div key={i} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                    <div>
                      <p className="font-medium text-gray-800">{session.role}</p>
                      <p className="text-sm text-gray-500">{session.date}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-indigo-600">{session.score}</div>
                      <p className="text-xs text-gray-500">Score</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {interviews.top_strengths?.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Top Strengths</h3>
                <div className="flex flex-wrap gap-2">
                  {interviews.top_strengths.map((strength, i) => (
                    <span key={i} className="px-4 py-2 bg-green-100 text-green-700 rounded-full font-medium">
                      {strength}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Resume Tab */}
        {activeTab === 'resume' && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-4">
              <MetricCard
                label="Average ATS Score"
                value={Math.round(resume.average_ats_score || 0)}
                icon={<FileText className="w-5 h-5 text-indigo-500" />}
              />
              <MetricCard
                label="Resumes"
                value={resume.resumes?.length || 0}
                icon={<FileText className="w-5 h-5 text-blue-500" />}
              />
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Resume Scores</h3>
              <div className="space-y-4">
                {(resume.resumes || []).map((r, i) => (
                  <div key={i} className="p-4 bg-gray-50 rounded-xl">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-medium text-gray-800">{r.name}</span>
                      <span className="text-sm text-gray-500">{r.uploaded_at}</span>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-xl font-bold text-indigo-600">{r.ats_score}</div>
                        <div className="text-xs text-gray-500">ATS Score</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-green-600">{r.keyword_match}%</div>
                        <div className="text-xs text-gray-500">Keywords</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-blue-600">{r.skills_found}</div>
                        <div className="text-xs text-gray-500">Skills</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Recommendations</h3>
              <ul className="space-y-2">
                {(resume.recommendations || []).map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-600">
                    <span className="text-indigo-500">•</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  const colorClasses = {
    indigo: 'bg-indigo-50 text-indigo-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-5">
      <div className={`w-12 h-12 rounded-xl ${colorClasses[color]} flex items-center justify-center mb-3`}>
        {icon}
      </div>
      <div className="text-3xl font-bold text-gray-800">{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </div>
  );
}

function MetricCard({ label, value, icon }) {
  return (
    <div className="bg-white rounded-xl shadow p-4 flex items-center gap-4">
      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
        {icon}
      </div>
      <div>
        <div className="text-2xl font-bold text-gray-800">{value}</div>
        <div className="text-sm text-gray-500">{label}</div>
      </div>
    </div>
  );
}

function SimpleBarChart({ data }) {
  const maxValue = Math.max(...data.map(d => d.applications), 1);

  return (
    <div className="flex items-end gap-2 h-40">
      {data.map((item, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1">
          <div
            className="w-full bg-indigo-500 rounded-t transition-all hover:bg-indigo-600"
            style={{ height: `${(item.applications / maxValue) * 100}%` }}
          />
          <span className="text-xs text-gray-400 truncate w-full text-center">
            {item.week?.slice(5) || ''}
          </span>
        </div>
      ))}
    </div>
  );
}