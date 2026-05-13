import React, { useState } from 'react';
import { FiBriefcase, FiExternalLink, FiMapPin, FiSearch } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { fetchExternalJobs } from '../api';

const sourceOptions = [
  { value: 'all', label: 'All sources' },
  { value: 'google', label: 'Google Jobs' },
  { value: 'linkedin', label: 'LinkedIn-style' },
  { value: 'remote', label: 'Remote boards' },
  { value: 'internships', label: 'Internships' },
];

const jobTypeOptions = [
  { value: '', label: 'All types' },
  { value: 'full-time', label: 'Full-time' },
  { value: 'part-time', label: 'Part-time' },
  { value: 'internship', label: 'Internship' },
  { value: 'remote', label: 'Remote' },
];

function sourceLabel(source) {
  const labels = {
    google_jobs: 'Google Jobs',
    linkedin: 'LinkedIn-style',
    jsearch: 'JSearch',
    adzuna: 'Adzuna',
    remotive: 'Remotive',
  };
  return labels[source] || source || 'External';
}

export default function ExternalJobsSearch() {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [jobType, setJobType] = useState('');
  const [source, setSource] = useState('all');
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
      const data = await fetchExternalJobs(query, location, jobType, source);
      setJobs(data.results || []);

      if (!data.results?.length) {
        toast.error('No jobs found');
      } else if (data.errors?.length) {
        toast.error('Some job sources could not be reached');
      }
    } catch (error) {
      toast.error(error.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Live Company Jobs</h1>
          <p className="mt-2 text-slate-600">
            Search Google Jobs, LinkedIn-style listings, remote boards, and internship sources.
          </p>
        </div>

        <form onSubmit={handleSearch} className="mb-8 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Job title</span>
              <span className="flex items-center rounded-lg bg-slate-100 px-4 py-3">
                <FiSearch className="mr-3 text-slate-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="React Developer"
                  className="min-w-0 flex-1 bg-transparent text-slate-900 outline-none"
                />
              </span>
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Location</span>
              <span className="flex items-center rounded-lg bg-slate-100 px-4 py-3">
                <FiMapPin className="mr-3 text-slate-400" />
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="USA or Remote"
                  className="min-w-0 flex-1 bg-transparent text-slate-900 outline-none"
                />
              </span>
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Source</span>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="w-full rounded-lg bg-slate-100 px-4 py-3 text-slate-900 outline-none focus:ring-2 focus:ring-blue-500"
              >
                {sourceOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">Job type</span>
              <select
                value={jobType}
                onChange={(e) => setJobType(e.target.value)}
                className="w-full rounded-lg bg-slate-100 px-4 py-3 text-slate-900 outline-none focus:ring-2 focus:ring-blue-500"
              >
                {jobTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </form>

        <div className="grid gap-5">
          {jobs.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-300 bg-white py-12 text-center">
              <FiBriefcase className="mx-auto mb-4 text-4xl text-slate-300" />
              <p className="text-slate-500">
                {loading ? 'Searching live job sources...' : 'Enter a role to find live company jobs'}
              </p>
            </div>
          ) : (
            jobs.map((job, idx) => (
              <article key={`${job.source}-${job.external_id || idx}`} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
                <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-slate-900">{job.title}</h3>
                    <p className="font-semibold text-blue-700">{job.company}</p>
                  </div>
                  <span className="w-fit rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                    {sourceLabel(job.source)}
                  </span>
                </div>

                <div className="mb-4 flex flex-wrap gap-3 text-sm text-slate-600">
                  <span className="flex items-center">
                    <FiMapPin className="mr-2" /> {job.location || 'Not specified'}
                  </span>
                  <span className="flex items-center">
                    <FiBriefcase className="mr-2" /> {job.employment_type || 'Role'}
                  </span>
                  {job.is_remote && <span className="font-semibold text-emerald-700">Remote</span>}
                  {job.is_internship && <span className="font-semibold text-violet-700">Internship</span>}
                </div>

                <p className="mb-4 line-clamp-2 text-slate-700">{job.description}</p>

                <a
                  href={job.job_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center rounded-lg bg-blue-600 px-5 py-2 font-semibold text-white transition hover:bg-blue-700"
                >
                  View job <FiExternalLink className="ml-2" />
                </a>
              </article>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
