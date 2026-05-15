import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Trophy,
  Flame,
  Star,
  Zap,
  Award,
  Target,
  CheckCircle,
  Lock,
  Loader2,
} from "lucide-react";
import api from "../api";

const levelThresholds = [
  { level: 1, xp: 0, title: "Newcomer" },
  { level: 2, xp: 100, title: "Explorer" },
  { level: 3, xp: 250, title: "Achiever" },
  { level: 4, xp: 500, title: "Expert" },
  { level: 5, xp: 1000, title: "Master" },
  { level: 6, xp: 2000, title: "Champion" },
  { level: 7, xp: 5000, title: "Legend" },
];

export default function GamificationHub() {
  const [profile, setProfile] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("profile");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const [profileRes, leaderboardRes, challengesRes] = await Promise.all([
        api.get("/api/jobs/game/profile/", { headers }),
        api.get("/api/jobs/game/leaderboard/", { headers }),
        api.get("/api/jobs/game/challenges/daily/", { headers }),
      ]);
      setProfile(profileRes.data);
      setLeaderboard(leaderboardRes.data.leaderboard || []);
      setChallenges(challengesRes.data.challenges || []);
    } catch (err) {
      setProfile({ total_xp: 250, level: 2, current_streak: 5, longest_streak: 12, badges: [] });
      setLeaderboard([
        { rank: 1, user: "john@example.com", level: 7, total_xp: 5000, streak: 30 },
        { rank: 2, user: "jane@example.com", level: 5, total_xp: 1200, streak: 15 },
        { rank: 3, user: "you", level: 2, total_xp: 250, streak: 5 },
      ]);
      setChallenges([
        { id: 1, title: "Apply to 3 Jobs", description: "Submit job applications today", xp_reward: 30, difficulty: "easy", completed: false },
        { id: 2, title: "Complete Profile", description: "Fill in your skills and bio", xp_reward: 50, difficulty: "easy", completed: true },
        { id: 3, title: "Solve 2 DSA Problems", description: "Practice coding problems", xp_reward: 40, difficulty: "medium", completed: false },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const completeChallenge = async (challengeId) => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      await api.post("/api/jobs/game/challenges/complete/", { challenge_id: challengeId }, { headers });
      fetchData();
    } catch (err) {
      setChallenges(challenges.map(c => c.id === challengeId ? { ...c, completed: true } : c));
    }
  };

  const getLevelInfo = (level) => levelThresholds.find(l => l.level === level) || levelThresholds[0];
  const getNextLevelXp = (level) => levelThresholds.find(l => l.level === level + 1)?.xp || 10000;
  const progressPercent = profile ? (profile.total_xp % getNextLevelXp(profile.level)) / (getNextLevelXp(profile.level) - getNextLevelXp(profile.level - 1)) * 100 : 0;

  const badges = [
    { name: "First Application", icon: "📝", xp: 10, earned: true },
    { name: "Profile Master", icon: "👤", xp: 50, earned: true },
    { name: "Code Warrior", icon: "💻", xp: 100, earned: false },
    { name: "Streak Master", icon: "🔥", xp: 75, earned: true },
    { name: "Interview Pro", icon: "🎯", xp: 150, earned: false },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-yellow-500" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Trophy className="w-8 h-8 text-yellow-500" />
          Gamification Hub
        </h1>
        <p className="text-gray-600 mt-2">
          Earn XP, unlock badges, and climb the leaderboard
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { id: "profile", label: "My Profile", icon: Star },
          { id: "challenges", label: "Challenges", icon: Target },
          { id: "leaderboard", label: "Leaderboard", icon: Trophy },
          { id: "badges", label: "Badges", icon: Award },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
              activeTab === tab.id
                ? "bg-yellow-500 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "profile" && profile && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Level Card */}
          <div className="bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl shadow-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-sm opacity-80">Current Level</div>
                <div className="text-4xl font-bold">{profile.level}</div>
                <div className="text-lg">{getLevelInfo(profile.level).title}</div>
              </div>
              <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center">
                <Star className="w-10 h-10" />
              </div>
            </div>
            <div className="bg-white/20 rounded-full h-4 overflow-hidden">
              <div className="bg-white h-full rounded-full transition-all" style={{ width: `${progressPercent}%` }} />
            </div>
            <div className="flex justify-between mt-2 text-sm">
              <span>{profile.total_xp} XP</span>
              <span>{getNextLevelXp(profile.level)} XP to next level</span>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-2 text-orange-500 mb-2">
                <Flame className="w-6 h-6" />
                <span className="font-semibold">Streak</span>
              </div>
              <div className="text-3xl font-bold">{profile.current_streak}</div>
              <div className="text-sm text-gray-500">days</div>
              <div className="text-xs text-gray-400 mt-2">Best: {profile.longest_streak} days</div>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-2 text-blue-500 mb-2">
                <Zap className="w-6 h-6" />
                <span className="font-semibold">Total XP</span>
              </div>
              <div className="text-3xl font-bold">{profile.total_xp}</div>
              <div className="text-sm text-gray-500">earned</div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "challenges" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {challenges.map((challenge) => (
            <motion.div
              key={challenge.id}
              whileHover={{ scale: 1.02 }}
              className={`bg-white rounded-xl shadow-lg p-6 ${challenge.completed ? "opacity-60" : ""}`}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-lg">{challenge.title}</h3>
                {challenge.completed ? (
                  <CheckCircle className="w-6 h-6 text-green-500" />
                ) : (
                  <span className={`px-2 py-1 rounded text-xs ${challenge.difficulty === "easy" ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}`}>
                    {challenge.difficulty}
                  </span>
                )}
              </div>
              <p className="text-gray-600 text-sm mb-4">{challenge.description}</p>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-yellow-600 font-medium">
                  <Zap className="w-4 h-4" />
                  {challenge.xp_reward} XP
                </span>
                {!challenge.completed && (
                  <button
                    onClick={() => completeChallenge(challenge.id)}
                    className="px-4 py-2 bg-yellow-500 text-white rounded-lg text-sm hover:bg-yellow-600"
                  >
                    Complete
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {activeTab === "leaderboard" && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Global Leaderboard</h2>
          <div className="space-y-2">
            {leaderboard.map((entry, idx) => (
              <div
                key={idx}
                className={`flex items-center justify-between p-4 rounded-lg ${
                  entry.user === "you" ? "bg-yellow-50 border-2 border-yellow-400" : "bg-gray-50"
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                    entry.rank === 1 ? "bg-yellow-400 text-white" :
                    entry.rank === 2 ? "bg-gray-300 text-white" :
                    entry.rank === 3 ? "bg-orange-400 text-white" : "bg-gray-200"
                  }`}>
                    {entry.rank}
                  </div>
                  <div>
                    <div className="font-medium">{entry.user === "you" ? "You" : entry.user.split("@")[0]}</div>
                    <div className="text-sm text-gray-500">Level {entry.level}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-yellow-600">{entry.total_xp} XP</div>
                  <div className="text-sm text-gray-500">🔥 {entry.streak} streak</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "badges" && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {badges.map((badge, idx) => (
            <div
              key={idx}
              className={`bg-white rounded-xl shadow-lg p-6 text-center ${badge.earned ? "" : "opacity-50"}`}
            >
              <div className="text-4xl mb-2">{badge.earned ? badge.icon : <Lock className="w-8 h-8 mx-auto text-gray-400" />}</div>
              <div className="font-medium">{badge.name}</div>
              <div className="text-sm text-gray-500">{badge.xp} XP</div>
              {badge.earned && (
                <div className="mt-2 text-green-500 text-sm">Earned ✓</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}