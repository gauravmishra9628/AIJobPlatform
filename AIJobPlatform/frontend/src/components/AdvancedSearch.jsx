import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  MapPin,
  DollarSign,
  Briefcase,
  Building2,
  Loader2,
  X,
} from "lucide-react";
import api from "../api";

const skillsList = [
  "Python", "JavaScript", "React", "Django", "SQL", "AWS", "Docker", "Machine Learning",
  "TypeScript", "Node.js", "MongoDB", "PostgreSQL", "Kubernetes", "Java", "Go", "Rust"
];

const workTypes = ["Remote", "Hybrid", "On-site"];

export default function AdvancedSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [filters, setFilters] = useState({
    skills: [],
    min_salary: "",
    max_salary: "",
    experience_min: "",
    experience_max: "",
    work_type: [],
  });
  const [showFilters, setShowFilters] = useState(false);
  const [totalResults, setTotalResults] = useState(0);

  useEffect(() => {
    if (query.length >= 2) {
      fetchSuggestions();
    }
  }, [query]);

  const fetchSuggestions = async () => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.get("/api/jobs/search/suggestions/", { headers, params: { prefix: query } });
      setSuggestions(res.data.suggestions || []);
    } catch (err) {
      setSuggestions(["React Developer", "Python Developer", "Full Stack Developer", "Data Scientist"]);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const params = { q: query, ...filters };
      // Remove empty values
      Object.keys(params).forEach(key => {
        if (!params[key]) delete params[key];
      });
      const res = await api.get("/api/jobs/search/", { headers, params });
      setResults(res.data.jobs || []);
      setTotalResults(res.data.total || 0);
    } catch (err) {
      // Mock results
      setResults([
        { id: 1, title: "Senior React Developer", company: "TechCorp", location: "Bangalore", salary_range: "20-30 L", skills_required: "React, TypeScript, Redux", employment_type: "full-time" },
        { id: 2, title: "Python Backend Engineer", company: "StartupXYZ", location: "Remote", salary_range: "15-25 L", skills_required: "Python, Django, PostgreSQL", employment_type: "full-time" },
        { id: 3, title: "Full Stack Developer", company: "InnovateLabs", location: "Hyderabad", salary_range: "18-28 L", skills_required: "React, Node, MongoDB", employment_type: "hybrid" },
      ]);
      setTotalResults(3);
    } finally {
      setLoading(false);
    }
  };

  const toggleSkill = (skill) => {
    setFilters(prev => ({
      ...prev,
      skills: prev.skills.includes(skill)
        ? prev.skills.filter(s => s !== skill)
        : [...prev.skills, skill]
    }));
  };

  const toggleWorkType = (type) => {
    setFilters(prev => ({
      ...prev,
      work_type: prev.work_type.includes(type)
        ? prev.work_type.filter(t => t !== type)
        : [...prev.work_type, type]
    }));
  };

  const clearFilters = () => {
    setFilters({
      skills: [],
      min_salary: "",
      max_salary: "",
      experience_min: "",
      experience_max: "",
      work_type: [],
    });
  };

  const hasActiveFilters = filters.skills.length > 0 || filters.min_salary || filters.max_salary || filters.work_type.length > 0;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Search className="w-8 h-8 text-blue-600" />
          Advanced Job Search
        </h1>
        <p className="text-gray-600 mt-2">
          Find your perfect job with advanced filtering
        </p>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search jobs, companies, or skills..."
              className="w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            {suggestions.length > 0 && query && (
              <div className="absolute top-full left-0 right-0 bg-white border rounded-lg mt-1 shadow-lg z-10">
                {suggestions.map((s, idx) => (
                  <div
                    key={idx}
                    onClick={() => { setQuery(s); setSuggestions([]); }}
                    className="px-4 py-2 hover:bg-gray-50 cursor-pointer"
                  >
                    {s}
                  </div>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 ${showFilters || hasActiveFilters ? "bg-blue-600 text-white" : "border hover:bg-gray-50"}`}
          >
            <Filter className="w-5 h-5" />
            Filters
            {hasActiveFilters && (
              <span className="bg-white text-blue-600 px-2 py-0.5 rounded-full text-xs">
                {filters.skills.length + filters.work_type.length + (filters.min_salary ? 1 : 0)}
              </span>
            )}
          </button>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Search"}
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            className="mt-4 pt-4 border-t"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Skills */}
              <div>
                <h3 className="font-medium mb-2">Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {skillsList.map((skill) => (
                    <button
                      key={skill}
                      onClick={() => toggleSkill(skill)}
                      className={`px-3 py-1 rounded-full text-sm ${
                        filters.skills.includes(skill)
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {skill}
                    </button>
                  ))}
                </div>
              </div>

              {/* Salary */}
              <div>
                <h3 className="font-medium mb-2">Salary Range (LPA)</h3>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={filters.min_salary}
                    onChange={(e) => setFilters({ ...filters, min_salary: e.target.value })}
                    placeholder="Min"
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                  <input
                    type="number"
                    value={filters.max_salary}
                    onChange={(e) => setFilters({ ...filters, max_salary: e.target.value })}
                    placeholder="Max"
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>

              {/* Work Type */}
              <div>
                <h3 className="font-medium mb-2">Work Type</h3>
                <div className="flex gap-2">
                  {workTypes.map((type) => (
                    <button
                      key={type}
                      onClick={() => toggleWorkType(type)}
                      className={`px-4 py-2 rounded-lg ${
                        filters.work_type.includes(type)
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {hasActiveFilters && (
              <div className="mt-4 flex items-center justify-between">
                <span className="text-sm text-gray-500">Active filters applied</span>
                <button onClick={clearFilters} className="text-sm text-red-600 hover:underline">
                  Clear all filters
                </button>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Results */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-gray-600">
          {totalResults} jobs found
        </span>
      </div>

      <div className="space-y-4">
        {results.map((job) => (
          <motion.div
            key={job.id}
            whileHover={{ scale: 1.01 }}
            className="bg-white rounded-xl shadow-lg p-6 cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                <div className="flex items-center gap-4 mt-2 text-gray-600">
                  <span className="flex items-center gap-1">
                    <Building2 className="w-4 h-4" />
                    {job.company}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-4 h-4" />
                    {job.location}
                  </span>
                  <span className="flex items-center gap-1">
                    <DollarSign className="w-4 h-4" />
                    {job.salary_range}
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {job.skills_required?.split(",").map((skill, idx) => (
                    <span key={idx} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-sm">
                      {skill.trim()}
                    </span>
                  ))}
                </div>
              </div>
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                {job.employment_type}
              </span>
            </div>
          </motion.div>
        ))}

        {results.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-500">
            <Search className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>No jobs found. Try adjusting your filters or search query.</p>
          </div>
        )}
      </div>
    </div>
  );
}