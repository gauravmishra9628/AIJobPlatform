import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  Legend,
} from "recharts";
import {
  Target,
  TrendingUp,
  BookOpen,
  Clock,
  Award,
  ChevronRight,
  Zap,
  Brain,
  Loader2,
  Plus,
  CheckCircle,
} from "lucide-react";
import api from "../api";

const skillCategories = [
  "Backend",
  "Frontend",
  "ML",
  "Data",
  "DevOps",
  "Database",
  "Mobile",
  "Design",
];

export default function CareerGraph() {
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState(null);
  const [careerPaths, setCareerPaths] = useState([]);
  const [selectedPath, setSelectedPath] = useState(null);
  const [pathProgress, setPathProgress] = useState(null);
  const [activeTab, setActiveTab] = useState("radar");

  useEffect(() => {
    fetchCareerGraph();
    fetchCareerPaths();
  }, []);

  const fetchCareerGraph = async () => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.get("/api/jobs/career/graph/", { headers });
      setGraphData(res.data);
    } catch (err) {
      console.error("Error fetching career graph:", err);
      // Use mock data for demo
      setGraphData({
        radarChart: [
          { category: "Backend", level: 2.5 },
          { category: "Frontend", level: 2 },
          { category: "ML", level: 1.5 },
          { category: "DevOps", level: 1 },
        ],
        nodes: [
          { id: 1, name: "Python", category: "Backend", current_level: 3, target_level: 3, progress: 90 },
          { id: 2, name: "React", category: "Frontend", current_level: 2, target_level: 3, progress: 70 },
          { id: 3, name: "SQL", category: "Database", current_level: 2, target_level: 3, progress: 65 },
          { id: 4, name: "Docker", category: "DevOps", current_level: 1, target_level: 2, progress: 40 },
        ],
        total_skills: 4,
        avg_progress: 66,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchCareerPaths = async () => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.get("/api/jobs/career/paths/", { headers });
      setCareerPaths(res.data.paths || []);
    } catch (err) {
      // Use mock data
      setCareerPaths([
        { id: 1, name: "Senior React Developer", description: "Build expert-level React applications", skills_count: 8, experience_years: 4, salary_range: "15-25", market_demand: 1.8 },
        { id: 2, name: "ML Engineer", description: "Master machine learning", skills_count: 10, experience_years: 3, salary_range: "18-30", market_demand: 2.0 },
        { id: 3, name: "Full Stack Developer", description: "Full stack web development", skills_count: 12, experience_years: 3, salary_range: "12-20", market_demand: 1.9 },
      ]);
    }
  };

  const generatePath = async (pathId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const path = careerPaths.find((p) => p.id === pathId);
      const res = await api.post(
        "/api/jobs/career/path/generate/",
        { target_role: path?.name || "Senior Developer" },
        { headers }
      );
      setPathProgress(res.data);
    } catch (err) {
      // Mock response
      setPathProgress({
        career_path: "Senior React Developer",
        missing_skills: ["TypeScript", "GraphQL", "System Design"],
        learning_path: [
          { skill: "TypeScript", category: "Frontend", weeks_needed: 4, difficulty: 2, resources: [] },
          { skill: "GraphQL", category: "Backend", weeks_needed: 3, difficulty: 2, resources: [] },
          { skill: "System Design", category: "Architecture", weeks_needed: 6, difficulty: 3, resources: [] },
        ],
        total_weeks: 13,
        hiring_probability_timeline: [
          { weeks: 0, probability: 20, milestone: "Current" },
          { weeks: 4, probability: 35, milestone: "Month 1" },
          { weeks: 8, probability: 55, milestone: "Month 2" },
          { weeks: 12, probability: 75, milestone: "Month 3" },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading && !graphData) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Brain className="w-8 h-8 text-purple-600" />
          Smart Career Graph
        </h1>
        <p className="text-gray-600 mt-2">
          Visualize your skills, track progress, and plan your career path
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { id: "radar", label: "Skill Radar", icon: Target },
          { id: "paths", label: "Career Paths", icon: TrendingUp },
          { id: "progress", label: "Learning Timeline", icon: Clock },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
              activeTab === tab.id
                ? "bg-purple-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "radar" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Radar Chart */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Skill Proficiency</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={graphData?.radarChart || []}>
                  <PolarGrid stroke="#e5e7eb" />
                  <PolarAngleAxis dataKey="category" tick={{ fill: "#6b7280" }} />
                  <PolarRadiusAxis angle={30} domain={[0, 3]} tick={{ fill: "#9ca3af" }} />
                  <Radar
                    name="Current Level"
                    dataKey="level"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.5}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Skills List */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Your Skills</h2>
            <div className="space-y-4">
              {(graphData?.nodes || []).map((skill) => (
                <div key={skill.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <h3 className="font-medium text-gray-900">{skill.name}</h3>
                    <span className="text-sm text-gray-500">{skill.category}</span>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-purple-600 rounded-full"
                          style={{ width: `${skill.progress}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{skill.progress}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="bg-purple-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-600">{graphData?.total_skills || 0}</div>
                <div className="text-sm text-purple-700">Total Skills</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600">{graphData?.avg_progress || 0}%</div>
                <div className="text-sm text-green-700">Avg Progress</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "paths" && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold mb-4">Available Career Paths</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {careerPaths.map((path) => (
              <motion.div
                key={path.id}
                whileHover={{ scale: 1.02 }}
                className="bg-white rounded-xl shadow-lg p-6 cursor-pointer border-2 border-transparent hover:border-purple-500"
                onClick={() => {
                  setSelectedPath(path);
                  generatePath(path.id);
                }}
              >
                <h3 className="font-semibold text-lg text-gray-900">{path.name}</h3>
                <p className="text-gray-600 text-sm mt-2">{path.description}</p>
                <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                  <span className="flex items-center gap-1">
                    <BookOpen className="w-4 h-4" />
                    {path.skills_count} skills
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {path.experience_years} yrs
                  </span>
                </div>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-green-600 font-medium">₹{path.salary_range}L</span>
                  <span className="flex items-center gap-1 text-purple-600">
                    <Zap className="w-4 h-4" />
                    {path.market_demand} demand
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "progress" && pathProgress && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">
              Learning Path: {pathProgress.career_path}
            </h2>

            {/* Timeline Chart */}
            <div className="h-64 mb-6">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={pathProgress.hiring_probability_timeline}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="milestone" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="probability"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={{ fill: "#8b5cf6" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Learning Path Steps */}
            <h3 className="font-semibold mb-3">Learning Roadmap</h3>
            <div className="space-y-3">
              {pathProgress.learning_path.map((item, idx) => (
                <div key={idx} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">{item.skill}</h4>
                      <span className="text-purple-600 font-medium">{item.weeks_needed} weeks</span>
                    </div>
                    <span className="text-sm text-gray-500">{item.category}</span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-purple-50 rounded-lg flex items-center justify-between">
              <div>
                <div className="text-sm text-purple-700">Total Time Required</div>
                <div className="text-2xl font-bold text-purple-900">{pathProgress.total_weeks} weeks</div>
              </div>
              <Award className="w-12 h-12 text-purple-600" />
            </div>
          </div>
        </div>
      )}

      {activeTab === "progress" && !pathProgress && (
        <div className="text-center py-12 text-gray-500">
          <TrendingUp className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p>Select a career path to see your personalized learning timeline</p>
        </div>
      )}
    </div>
  );
}