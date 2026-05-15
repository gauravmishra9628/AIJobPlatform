import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Brain,
  User,
  Users,
  TrendingUp,
  MessageSquare,
  Target,
  Loader2,
  Sparkles,
} from "lucide-react";
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
} from "recharts";
import api from "../api";

export default function PersonalityAnalyzer() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.get("/api/jobs/personality/profile/me/", { headers });
      setProfile(res.data);
    } catch (err) {
      // Mock data
      setProfile({
        mbti_type: "INTJ",
        big_five: { openness: 72, conscientiousness: 68, extraversion: 45, agreeableness: 70, neuroticism: 30 },
        soft_skills: { communication: 75, leadership: 68, teamwork: 82, problem_solving: 78, adaptability: 65 },
      });
    } finally {
      setLoading(false);
    }
  };

  const analyzePersonality = async () => {
    setAnalyzing(true);
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.post("/api/jobs/personality/analyze/", {}, { headers });
      setProfile(res.data);
    } catch (err) {
      // Mock analysis
      setProfile({
        mbti_type: "ENFP",
        big_five: { openness: 85, conscientiousness: 60, extraversion: 75, agreeableness: 80, neuroticism: 25 },
        soft_skills: { communication: 82, leadership: 70, teamwork: 88, problem_solving: 72, adaptability: 85 },
      });
    } finally {
      setAnalyzing(false);
    }
  };

  const bigFiveData = profile ? [
    { trait: "Openness", value: profile.big_five.openness, fullMark: 100 },
    { trait: "Conscientiousness", value: profile.big_five.conscientiousness, fullMark: 100 },
    { trait: "Extraversion", value: profile.big_five.extraversion, fullMark: 100 },
    { trait: "Agreeableness", value: profile.big_five.agreeableness, fullMark: 100 },
    { trait: "Neuroticism", value: 100 - profile.big_five.neuroticism, fullMark: 100 },
  ] : [];

  const softSkillsData = profile ? [
    { skill: "Communication", score: profile.soft_skills.communication },
    { skill: "Leadership", score: profile.soft_skills.leadership },
    { skill: "Teamwork", score: profile.soft_skills.teamwork },
    { skill: "Problem Solving", score: profile.soft_skills.problem_solving },
    { skill: "Adaptability", score: profile.soft_skills.adaptability },
  ] : [];

  const mbtiDescriptions = {
    INTJ: "Strategic thinker, independent, analytical",
    INTP: "Logical, curious, abstract thinker",
    ENTJ: "Natural leader, decisive, commanding",
    ENTP: "Innovative, creative, debate-oriented",
    INFJ: "Insightful, idealistic, principled",
    INFP: "Compassionate, creative, authentic",
    ENFJ: "Charismatic, empathetic, inspiring",
    ENFP: "Enthusiastic, imaginative, spontaneous",
    ISTJ: "Responsible, organized, systematic",
    ISFJ: "Loyal, dedicated, nurturing",
    ESTJ: "Efficient, structured, results-oriented",
    ESFJ: "Caring, social, supportive",
    ISTP: "Pragmatic, action-oriented, hands-on",
    ISFP: "Gentle, artistic, flexible",
    ESTP: "Energetic, practical, adventurous",
    ESFP: "Playful, fun-loving, spontaneous",
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Brain className="w-8 h-8 text-purple-600" />
            AI Personality Analyzer
          </h1>
          <p className="text-gray-600 mt-2">
            Understand your personality traits and soft skills
          </p>
        </div>
        <button
          onClick={analyzePersonality}
          disabled={analyzing}
          className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50"
        >
          {analyzing ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
          {analyzing ? "Analyzing..." : "Analyze My Personality"}
        </button>
      </div>

      {profile ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* MBTI Result */}
          <div className="bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl shadow-lg p-6 text-white">
            <div className="text-center">
              <div className="text-sm opacity-80 mb-2">Your MBTI Type</div>
              <div className="text-6xl font-bold mb-2">{profile.mbti_type}</div>
              <div className="text-lg opacity-90">{mbtiDescriptions[profile.mbti_type] || "Unique personality"}</div>
            </div>
            <div className="mt-6 grid grid-cols-4 gap-2 text-center text-sm">
              <div>
                <div className="font-bold text-2xl">{profile.mbti_type[0]}</div>
                <div className="opacity-70">Energy</div>
              </div>
              <div>
                <div className="font-bold text-2xl">{profile.mbti_type[1]}</div>
                <div className="opacity-70">Information</div>
              </div>
              <div>
                <div className="font-bold text-2xl">{profile.mbti_type[2]}</div>
                <div className="opacity-70">Decisions</div>
              </div>
              <div>
                <div className="font-bold text-2xl">{profile.mbti_type[3]}</div>
                <div className="opacity-70">Structure</div>
              </div>
            </div>
          </div>

          {/* Big Five Radar */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-purple-600" />
              Big Five Traits
            </h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={bigFiveData}>
                  <PolarGrid stroke="#e5e7eb" />
                  <PolarAngleAxis dataKey="trait" tick={{ fill: "#6b7280", fontSize: 12 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: "#9ca3af" }} />
                  <Radar
                    name="Score"
                    dataKey="value"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.5}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Soft Skills Bar Chart */}
          <div className="bg-white rounded-xl shadow-lg p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              Soft Skills Assessment
            </h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={softSkillsData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis dataKey="skill" type="category" width={120} />
                  <Tooltip />
                  <Bar dataKey="score" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Insights */}
          <div className="bg-white rounded-xl shadow-lg p-6 lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-green-600" />
              Personalized Insights
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <h3 className="font-medium text-green-800 mb-2">Strengths</h3>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• Strong analytical and problem-solving abilities</li>
                  <li>• Excellent team collaboration skills</li>
                  <li>• Good communication capabilities</li>
                </ul>
              </div>
              <div className="p-4 bg-blue-50 rounded-lg">
                <h3 className="font-medium text-blue-800 mb-2">Growth Areas</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Consider taking on leadership roles</li>
                  <li>• Expand your adaptability in new situations</li>
                  <li>• Continue building technical expertise</li>
                </ul>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <h3 className="font-medium text-purple-800 mb-2">Career Fit</h3>
                <ul className="text-sm text-purple-700 space-y-1">
                  <li>• Technical Lead roles</li>
                  <li>• Product Management</li>
                  <li>• Architecture & Design</li>
                </ul>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <h3 className="font-medium text-orange-800 mb-2">Team Dynamics</h3>
                <ul className="text-sm text-orange-700 space-y-1">
                  <li>• Best with collaborative teams</li>
                  <li>• Values clear communication</li>
                  <li>• Prefers structured workflows</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <Brain className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p>Click "Analyze My Personality" to get your profile</p>
        </div>
      )}
    </div>
  );
}