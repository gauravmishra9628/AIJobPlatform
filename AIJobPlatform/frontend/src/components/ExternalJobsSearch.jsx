import React, { useState } from 'react';
import { FiSearch, FiMapPin, FiBriefcase } from 'react-icons/fi';
import api from '../api';
import toast from 'react-hot-toast';

export default function ExternalJobsSearch() {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [jobType, setJobType] = useState('');
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setLoading(true);
    try {
      const params = {
        q: query,
        location,
        type: jobType,
      };
      const response = await api.get('/jobs/external-jobs/', { params });
      setJobs(response.data.results || []);
      if (response.data.results.length === 0) {
        toast.error('No jobs found');
      }
    } catch (error) {
      toast.error(error.response?.data?.error || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">Find External Jobs</h1>
        <p className="text-gray-600 mb-8">Search from Google, LinkedIn, and remote job boards</p>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Job Title</label>
              <div className="flex items-center bg-gray-100 rounded-lg px-4 py-3">
                <FiSearch className="text-gray-400 mr-3" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g. React Developer"
                  className="bg-transparent flex-1 outline-none text-gray-800"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
              <div className="flex items-center bg-gray-100 rounded-lg px-4 py-3">
                <FiMapPin className="text-gray-400 mr-3" />
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. USA, Remote"
                  className="bg-transparent flex-1 outline-none text-gray-800"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Job Type</label>
              <select
                value={jobType}
                onChange={(e) => setJobType(e.target.value)}
                className="w-full bg-gray-100 rounded-lg px-4 py-3 text-gray-800 outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="internship">Internship</option>
                <option value="remote">Remote</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </form>

        {/* Jobs List */}
        <div className="grid gap-6">
          {jobs.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <FiBriefcase className="mx-auto text-4xl text-gray-300 mb-4" />
              <p className="text-gray-500">
                {loading ? 'Searching for jobs...' : 'Enter your search to find external jobs'}
              </p>
            </div>
          ) : (
            jobs.map((job, idx) => (
              <div key={idx} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-800">{job.title}</h3>
                    <p className="text-blue-600 font-semibold">{job.company}</p>
                  </div>
                  <span className="text-xs bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                    {job.source.toUpperCase()}
                  </span>
                </div>

                <div className="flex flex-wrap gap-4 mb-4 text-sm text-gray-600">
                  <span className="flex items-center">
                    <FiMapPin className="mr-2" /> {job.location}
                  </span>
                  <span className="flex items-center">
                    <FiBriefcase className="mr-2" /> {job.employment_type}
                  </span>
                  {job.is_remote && <span className="text-green-600 font-semibold">🌍 Remote</span>}
                </div>

                <p className="text-gray-700 mb-4 line-clamp-2">{job.description}</p>

                <a
                  href={job.job_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition"
                >
                  View Job →
                </a>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
