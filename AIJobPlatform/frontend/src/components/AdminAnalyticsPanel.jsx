import React, { useState, useEffect } from 'react';
import { FiUsers, FiBriefcase, FiCheckCircle, FiTrendingUp, FiBarChart2 } from 'react-icons/fi';
import api from '../api';
import toast from 'react-hot-toast';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export default function AdminAnalyticsPanel() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await api.get('/jobs/admin/analytics/');
      setAnalytics(response.data);
    } catch (error) {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;
  if (!analytics) return <div className="text-center py-12">No data</div>;

  const { users, jobs, applications, recruiter_analytics } = analytics;

  const userChartData = [
    { name: 'Students', value: users.students },
    { name: 'Recruiters', value: users.recruiters },
  ];

  const COLORS = ['#3b82f6', '#10b981'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">Admin Analytics Panel</h1>
        <p className="text-gray-600 mb-8">Platform metrics and insights</p>

        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-2">Total Users</p>
                <p className="text-3xl font-bold text-blue-600">{users.total}</p>
              </div>
              <FiUsers className="text-5xl text-blue-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-2">Total Jobs</p>
                <p className="text-3xl font-bold text-green-600">{jobs.total}</p>
              </div>
              <FiBriefcase className="text-5xl text-green-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-2">Active Jobs</p>
                <p className="text-3xl font-bold text-purple-600">{jobs.active}</p>
              </div>
              <FiCheckCircle className="text-5xl text-purple-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-2">Applications</p>
                <p className="text-3xl font-bold text-orange-600">{applications.total}</p>
              </div>
              <FiTrendingUp className="text-5xl text-orange-500 opacity-20" />
            </div>
          </div>
        </div>

        {/* User Breakdown & Applications This Month */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">User Breakdown</h2>
            <div className="flex justify-center">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={userChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {COLORS.map((color, index) => (
                      <Cell key={`cell-${index}`} fill={color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 space-y-2">
              <p className="text-gray-600"><span className="font-bold text-blue-600">{users.students}</span> Students</p>
              <p className="text-gray-600"><span className="font-bold text-green-600">{users.recruiters}</span> Recruiters</p>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Application Trends</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-2 border-b">
                <span className="text-gray-700">Total Applications</span>
                <span className="text-2xl font-bold text-blue-600">{applications.total}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b">
                <span className="text-gray-700">This Month</span>
                <span className="text-2xl font-bold text-green-600">{applications.this_month}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Avg. Applications per Job</span>
                <span className="text-2xl font-bold text-purple-600">
                  {jobs.active > 0 ? (applications.total / jobs.active).toFixed(1) : 0}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Recruiter Analytics */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Recruiter Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <p className="text-gray-600 text-sm">Total Jobs Posted</p>
              <p className="text-2xl font-bold">{recruiter_analytics.total_jobs_posted || 0}</p>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <p className="text-gray-600 text-sm">Total Applications</p>
              <p className="text-2xl font-bold">{recruiter_analytics.total_applications_sum || 0}</p>
            </div>
            <div className="border-l-4 border-purple-500 pl-4">
              <p className="text-gray-600 text-sm">Total Hired</p>
              <p className="text-2xl font-bold">{recruiter_analytics.total_hired_sum || 0}</p>
            </div>
            <div className="border-l-4 border-orange-500 pl-4">
              <p className="text-gray-600 text-sm">Avg. Time to Hire</p>
              <p className="text-2xl font-bold">{recruiter_analytics.avg_time_to_hire || 0} days</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
