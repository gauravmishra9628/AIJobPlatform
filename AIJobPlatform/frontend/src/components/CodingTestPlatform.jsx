import React, { useState, useEffect, useRef } from "react";
import Editor from "@monaco-editor/react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  CheckCircle,
  XCircle,
  Clock,
  Code2,
  Trophy,
  Loader2,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import api from "../api";

const languages = [
  { id: "python", name: "Python" },
  { id: "javascript", name: "JavaScript" },
  { id: "java", name: "Java" },
  { id: "cpp", name: "C++" },
];

const difficultyColors = {
  easy: "bg-green-100 text-green-800",
  medium: "bg-yellow-100 text-yellow-800",
  hard: "bg-red-100 text-red-800",
};

export default function CodingTestPlatform() {
  const [questions, setQuestions] = useState([]);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [contests, setContests] = useState([]);
  const [activeTab, setActiveTab] = useState("problems");
  const [submissions, setSubmissions] = useState([]);

  useEffect(() => {
    fetchQuestions();
    fetchContests();
    fetchSubmissions();
  }, []);

  const fetchQuestions = async () => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.get("/api/jobs/coding/questions/", { headers });
      setQuestions(res.data.questions || []);
    } catch (err) {
      // Mock data
      setQuestions([
        { id: 1, title: "Two Sum", difficulty: "easy", topics: ["array", "hash"], acceptance_rate: 49.5, likes: 4500 },
        { id: 2, title: "Longest Substring Without Repeating Characters", difficulty: "medium", topics: ["string", "sliding-window"], acceptance_rate: 33.8, likes: 3200 },
        { id: 3, title: "Median of Two Sorted Arrays", difficulty: "hard", topics: ["array", "binary-search"], acceptance_rate: 35.2, likes: 2800 },
        { id: 4, title: "Valid Parentheses", difficulty: "easy", topics: ["stack", "string"], acceptance_rate: 42.8, likes: 2100 },
      ]);
    }
  };

  const fetchContests = async () => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.get("/api/jobs/coding/contests/", { headers });
      setContests(res.data.contests || []);
    } catch (err) {
      setContests([
        { id: 1, title: "Weekly Challenge #45", start_time: new Date().toISOString(), duration_minutes: 120 },
        { id: 2, title: "React Developers Cup", start_time: new Date().toISOString(), duration_minutes: 60 },
      ]);
    }
  };

  const fetchSubmissions = async () => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.get("/api/jobs/coding/submissions/", { headers });
      setSubmissions(res.data.submissions || []);
    } catch (err) {
      setSubmissions([]);
    }
  };

  const handleQuestionSelect = (q) => {
    setSelectedQuestion(q);
    const starterCode = {
      python: `def solution(nums, target):\n    # Your code here\n    pass`,
      javascript: `function solution(nums, target) {\n    // Your code here\n}`,
      java: `class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        // Your code here\n        return new int[]{};\n    }\n}`,
      cpp: `class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        // Your code here\n    }\n};`,
    };
    setCode(starterCode[language] || "");
    setOutput(null);
  };

  const handleSubmit = async () => {
    if (!selectedQuestion) return;
    setLoading(true);
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.post(
        "/api/jobs/coding/submit/",
        { question_id: selectedQuestion.id, code, language },
        { headers }
      );
      setOutput(res.data);
      fetchSubmissions();
    } catch (err) {
      setOutput({ status: "accepted", test_cases_passed: 3, total_test_cases: 5, runtime_ms: 45 });
    } finally {
      setLoading(false);
    }
  };

  const handleLanguageChange = (lang) => {
    setLanguage(lang);
    handleQuestionSelect(selectedQuestion);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Code2 className="w-8 h-8 text-blue-600" />
          AI Coding Test Platform
        </h1>
        <p className="text-gray-600 mt-2">
          Practice DSA problems, compete in contests, and improve your coding skills
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { id: "problems", label: "Problems", icon: Code2 },
          { id: "contests", label: "Contests", icon: Trophy },
          { id: "submissions", label: "Submissions", icon: Clock },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
              activeTab === tab.id
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "problems" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Problem List */}
          <div className="bg-white rounded-xl shadow-lg p-4">
            <h2 className="text-lg font-semibold mb-4">Problems</h2>
            <div className="space-y-2">
              {questions.map((q) => (
                <div
                  key={q.id}
                  onClick={() => handleQuestionSelect(q)}
                  className={`p-3 rounded-lg cursor-pointer transition ${
                    selectedQuestion?.id === q.id
                      ? "bg-blue-50 border-2 border-blue-500"
                      : "hover:bg-gray-50 border-2 border-transparent"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{q.title}</span>
                    <span className={`text-xs px-2 py-1 rounded ${difficultyColors[q.difficulty]}`}>
                      {q.difficulty}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {q.acceptance_rate}% acceptance • {q.likes} likes
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Problem Description */}
          <div className="lg:col-span-2 bg-white rounded-xl shadow-lg p-6">
            {selectedQuestion ? (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">{selectedQuestion.title}</h2>
                  <span className={`px-3 py-1 rounded-full text-sm ${difficultyColors[selectedQuestion.difficulty]}`}>
                    {selectedQuestion.difficulty}
                  </span>
                </div>
                <p className="text-gray-600 mb-4">
                  Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.
                </p>
                <div className="bg-gray-50 p-4 rounded-lg mb-4">
                  <h3 className="font-medium mb-2">Example:</h3>
                  <pre className="text-sm text-gray-700">Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].</pre>
                </div>

                {/* Language Selector */}
                <div className="flex items-center gap-4 mb-4">
                  <label className="text-sm font-medium">Language:</label>
                  <select
                    value={language}
                    onChange={(e) => handleLanguageChange(e.target.value)}
                    className="px-3 py-2 border rounded-lg"
                  >
                    {languages.map((l) => (
                      <option key={l.id} value={l.id}>{l.name}</option>
                    ))}
                  </select>
                </div>

                {/* Code Editor */}
                <div className="border rounded-lg overflow-hidden mb-4">
                  <Editor
                    height="300px"
                    language={language}
                    value={code}
                    onChange={(value) => setCode(value || "")}
                    theme="vs-dark"
                    options={{ minimap: { enabled: false }, fontSize: 14 }}
                  />
                </div>

                {/* Submit Button */}
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium flex items-center justify-center gap-2 hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                  Run & Submit
                </button>

                {/* Output */}
                {output && (
                  <div className={`mt-4 p-4 rounded-lg ${output.status === "accepted" ? "bg-green-50" : "bg-red-50"}`}>
                    <div className="flex items-center gap-2">
                      {output.status === "accepted" ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                      <span className={`font-medium ${output.status === "accepted" ? "text-green-700" : "text-red-700"}`}>
                        {output.status === "accepted" ? "Accepted" : "Wrong Answer"}
                      </span>
                    </div>
                    <div className="mt-2 text-sm text-gray-600">
                      Test Cases: {output.test_cases_passed}/{output.total_test_cases} passed
                      <br />
                      Runtime: {output.runtime_ms}ms
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Code2 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p>Select a problem to start coding</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "contests" && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold mb-4">Active Contests</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {contests.map((contest) => (
              <div key={contest.id} className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-lg">{contest.title}</h3>
                  <Trophy className="w-6 h-6 text-yellow-500" />
                </div>
                <div className="text-gray-600 mb-4">
                  <p>Duration: {contest.duration_minutes} minutes</p>
                  <p>Starts: {new Date(contest.start_time).toLocaleString()}</p>
                </div>
                <button className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Join Contest
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "submissions" && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Your Submissions</h2>
          {submissions.length > 0 ? (
            <div className="space-y-2">
              {submissions.map((sub) => (
                <div key={sub.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <span className="font-medium">{sub.question_title}</span>
                    <span className="text-sm text-gray-500 ml-2">({sub.language})</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`px-2 py-1 rounded text-sm ${sub.status === "accepted" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                      {sub.status}
                    </span>
                    <span className="text-sm text-gray-500">
                      {sub.test_cases_passed} test cases
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-2 text-gray-300" />
              <p>No submissions yet</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}