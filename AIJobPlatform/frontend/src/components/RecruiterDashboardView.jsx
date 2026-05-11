import React, { useState, useEffect } from 'react';
import { FiBriefcase, FiUsers, FiTrendingUp, FiCheckCircle } from 'react-icons/fi';
import api from '../api';
import toast from 'react-hot-toast';

export default function RecruiterDashboardEnhancedView() {
  const [dashboard, setDashboard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await api.get('/jobs/recruiter/dashboard/');
      setDashboard(response.data.dashboard);
      setAnalytics(response.data.analytics);
    } catch (error) {
      toast.error('Failed to load recruiter dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;
  if (!dashboard) return <div className="text-center py-12">No data</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-8">Recruiter Dashboard</h1>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-2">Total Jobs Posted</p>
                <p className="text-3xl font-bold text-blue-600">{analytics?.total_jobs || 0}</p>
              </div>
              <FiBriefcase className="text-5xl text-blue-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-2">Applications</p>
                <p className="text-3xl font-bold text-purple-600">{analytics?.total_applications || 0}</p>
              </div>
              <FiUsers className="text-5xl text-purple-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-2">Shortlisted</p>
                <p className="text-3xl font-bold text-green-600">{analytics?.shortlisted || 0}</p>
              </div>
              <FiCheckCircle className="text-5xl text-green-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm mb-2">Hired</p>
                <p className="text-3xl font-bold text-orange-600">{analytics?.hired || 0}</p>
              </div>
              <FiTrendingUp className="text-5xl text-orange-500 opacity-20" />
            </div>
          </div>
        </div>

        {/* Pipeline & Goals */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Pipeline Status</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-gray-700">Applied</span>
                  <span className="font-bold">{analytics?.pending}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '60%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-gray-700">Shortlisted</span>
                  <span className="font-bold">{analytics?.shortlisted}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '35%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-gray-700">Hired</span>
                  <span className="font-bold">{analytics?.hired}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-orange-500 h-2 rounded-full" style={{ width: '15%' }} />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Hiring Goals</h2>
            <div className="space-y-4">
              {dashboard.hiring_goals ? (
                Object.entries(dashboard.hiring_goals).map(([role, goal]) => (
                  <div key={role} className="border-l-4 border-blue-500 pl-4">
                    <p className="text-gray-600 capitalize">{role}</p>
                    <p className="text-lg font-bold text-gray-800">{goal.target} Target</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500">No hiring goals set</p>
              )}
            </div>
          </div>
        </div>

        {/* Favorite Jobs */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition">
              Post New Job
            </button>
            <button className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition">
              View Applicants
            </button>
            <button className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition">
              Schedule Interview
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
