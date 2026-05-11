import React, { useState, useEffect } from 'react';
import { FiBook, FiCheckCircle, FiAlertCircle, FiDownload } from 'react-icons/fi';
import api from '../api';
import toast from 'react-hot-toast';

export default function StudentDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await api.get('/jobs/student/dashboard/');
      setDashboard(response.data);
    } catch (error) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center py-12">Loading...</div>;
  if (!dashboard) return <div className="text-center py-12">No data</div>;

  const { applications, bookmarks, resumes, profile_completion, profile } = dashboard;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-8">Student Dashboard</h1>

        {/* Profile Completion */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-800">Profile Completion</h2>
            <span className="text-3xl font-bold text-blue-600">{profile_completion}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all"
              style={{ width: `${profile_completion}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2">Complete your profile to increase visibility</p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Applications</p>
                <p className="text-3xl font-bold text-gray-800">{applications.total}</p>
              </div>
              <FiBook className="text-4xl text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Shortlisted</p>
                <p className="text-3xl font-bold text-green-600">{applications.shortlisted}</p>
              </div>
              <FiCheckCircle className="text-4xl text-green-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Bookmarked</p>
                <p className="text-3xl font-bold text-purple-600">{bookmarks}</p>
              </div>
              <FiBook className="text-4xl text-purple-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Resumes</p>
                <p className="text-3xl font-bold text-orange-600">{resumes}</p>
              </div>
              <FiDownload className="text-4xl text-orange-500" />
            </div>
          </div>
        </div>

        {/* Application Status Breakdown */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Application Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="border-l-4 border-blue-500 pl-4">
              <p className="text-gray-600">Applied</p>
              <p className="text-2xl font-bold text-gray-800">{applications.applied}</p>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <p className="text-gray-600">Shortlisted</p>
              <p className="text-2xl font-bold text-gray-800">{applications.shortlisted}</p>
            </div>
            <div className="border-l-4 border-red-500 pl-4">
              <p className="text-gray-600">Rejected</p>
              <p className="text-2xl font-bold text-gray-800">{applications.rejected}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
