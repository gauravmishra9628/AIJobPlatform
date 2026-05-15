import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  MicOff,
  Volume2,
  MessageSquare,
  Brain,
  Briefcase,
  Target,
  Loader2,
  Send,
  Bot,
} from "lucide-react";
import api from "../api";

const sessionTypes = [
  { id: "advice", label: "Career Advice", icon: Brain },
  { id: "interview", label: "Interview Practice", icon: Briefcase },
  { id: "skill", label: "Skill Guidance", icon: Target },
];

export default function VoiceCareerCoach() {
  const [isListening, setIsListening] = useState(false);
  const [sessionType, setSessionType] = useState("advice");
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    startSession();
  }, [sessionType]);

  const startSession = async () => {
    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.post("/api/jobs/voice/session/start/", { session_type: sessionType }, { headers });
      setSessionId(res.data.session_id);
    } catch (err) {
      setSessionId(1);
    }
  };

  const handleVoiceInput = () => {
    setIsListening(!isListening);
    if (!isListening) {
      // Start voice recording simulation
      setTimeout(() => {
        setIsListening(false);
        setTranscript("I'm looking for advice on how to transition from a junior developer to a senior role.");
        processTranscript();
      }, 3000);
    }
  };

  const processTranscript = async () => {
    if (!transcript) return;
    setLoading(true);

    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };
      const res = await api.post(
        "/api/jobs/voice/transcript/process/",
        { session_id: sessionId, transcript },
        { headers }
      );
      setResponse(res.data.response);
      setHistory([...history, { transcript, response: res.data.response, mood: res.data.mood_detected }]);
    } catch (err) {
      // Mock response
      const mockResponse = sessionType === "interview"
        ? "Great answer! Try using the STAR method to structure your responses. Can you tell me about a time when you faced a challenging technical problem?"
        : sessionType === "advice"
        ? "That's a great career goal! To transition to senior, focus on 3 key areas: 1) Take ownership of projects, 2) Mentor junior developers, 3) Develop system design skills."
        : "To improve your React skills, I recommend building real-world projects, studying React internals, and contributing to open source. Start with a complex app like a dashboard.";

      setResponse(mockResponse);
      setHistory([...history, { transcript, response: mockResponse, mood: "confident" }]);
    } finally {
      setLoading(false);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!transcript.trim()) return;
    processTranscript();
  };

  const playAudio = (text) => {
    // In production, use Web Speech API or TTS service
    alert("Playing audio: " + text.substring(0, 50) + "...");
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <Mic className="w-8 h-8 text-red-500" />
          Voice Career Coach
        </h1>
        <p className="text-gray-600 mt-2">
          Get career advice, practice interviews, or get skill guidance via voice
        </p>
      </div>

      {/* Session Type Selector */}
      <div className="flex gap-2 mb-6">
        {sessionTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => setSessionType(type.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
              sessionType === type.id
                ? "bg-red-500 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <type.icon className="w-4 h-4" />
            {type.label}
          </button>
        ))}
      </div>

      {/* Main Interface */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        {/* Chat Area */}
        <div className="h-96 p-6 overflow-y-auto space-y-4">
          {history.length === 0 && !transcript && (
            <div className="text-center py-12 text-gray-500">
              <Bot className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>Start a conversation with your AI career coach</p>
            </div>
          )}

          <AnimatePresence>
            {history.map((item, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="flex justify-end">
                  <div className="bg-blue-500 text-white p-4 rounded-l-lg rounded-tr-lg max-w-md">
                    <div className="flex items-center gap-2 mb-1">
                      <Mic className="w-4 h-4" />
                      <span className="text-xs opacity-80">You</span>
                    </div>
                    {item.transcript}
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-800 p-4 rounded-r-lg rounded-tl-lg max-md">
                    <div className="flex items-center gap-2 mb-1">
                      <Bot className="w-4 h-4 text-purple-500" />
                      <span className="text-xs text-gray-500">AI Coach</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${item.mood === "confident" ? "bg-green-100 text-green-700" : "bg-gray-200"}`}>
                        {item.mood}
                      </span>
                    </div>
                    {item.response}
                    <button
                      onClick={() => playAudio(item.response)}
                      className="mt-2 flex items-center gap-1 text-sm text-purple-600 hover:text-purple-800"
                    >
                      <Volume2 className="w-4 h-4" /> Listen
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 p-4 rounded-lg">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin text-purple-500" />
                  <span className="text-gray-500">Thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t p-4">
          <form onSubmit={handleTextSubmit} className="flex gap-2">
            <input
              type="text"
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              placeholder="Type your question or use voice..."
              className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <button
              type="submit"
              disabled={loading || !transcript.trim()}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>

          {/* Voice Button */}
          <div className="flex justify-center mt-4">
            <button
              onClick={handleVoiceInput}
              className={`w-16 h-16 rounded-full flex items-center justify-center transition ${
                isListening
                  ? "bg-red-500 animate-pulse"
                  : "bg-gray-800 hover:bg-gray-900"
              }`}
            >
              {isListening ? (
                <MicOff className="w-8 h-8 text-white" />
              ) : (
                <Mic className="w-8 h-8 text-white" />
              )}
            </button>
          </div>
          <p className="text-center text-sm text-gray-500 mt-2">
            {isListening ? "Listening... Speak now" : "Click to use voice input"}
          </p>
        </div>
      </div>

      {/* Session History */}
      {history.length > 0 && (
        <div className="mt-6 bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Session History</h2>
          <div className="space-y-2">
            {history.map((item, idx) => (
              <div key={idx} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                <MessageSquare className="w-5 h-5 text-gray-400" />
                <span className="flex-1 truncate">{item.transcript}</span>
                <span className="text-sm text-gray-500">{item.mood}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}