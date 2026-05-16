import React, { useState, useEffect, useRef, useCallback } from "react";
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
  BarChart3,
  Zap,
  AlertCircle,
  Settings,
  Cloud,
  Radio,
} from "lucide-react";
import api from "../api";

const sessionTypes = [
  { id: "advice", label: "Career Advice", icon: Brain },
  { id: "interview", label: "Interview Practice", icon: Briefcase },
  { id: "skill", label: "Skill Guidance", icon: Target },
];

const FILLER_WORDS = [
  "um", "uh", "like", "you know", "basically", "actually", "literally",
  "so", "well", "I mean", "sort of", "kind of", "yeah", "okay", "right",
];

export default function VoiceCareerCoach() {
  const [isListening, setIsListening] = useState(false);
  const [sessionType, setSessionType] = useState("advice");
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [history, setHistory] = useState([]);
  const [useWhisper, setUseWhisper] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [interimTranscript, setInterimTranscript] = useState("");
  const [audioLevel, setAudioLevel] = useState(0);
  const [useWebSpeech, setUseWebSpeech] = useState(true);

  // Speech analysis state
  const [speechMetrics, setSpeechMetrics] = useState({
    confidence: 0,
    speakingSpeed: 0,
    fillerWords: [],
    fillerWordCount: 0,
    wordsPerMinute: 0,
    totalWords: 0,
  });

  const recognitionRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);
  const wordsRef = useRef([]);
  const startTimeRef = useRef(null);

  // Check for Web Speech API support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
    }
    startSession();
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Initialize audio visualization
  const initAudioVisualization = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      const updateLevel = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(Math.min(100, (average / 128) * 100));
        if (isListening) {
          requestAnimationFrame(updateLevel);
        }
      };
      updateLevel();
    } catch (err) {
      console.log("Audio visualization not available");
    }
  };

  const analyzeSpeech = useCallback((text) => {
    if (!text.trim()) return;

    const words = text.toLowerCase().split(/\s+/).filter(w => w.length > 0);
    const foundFillers = [];
    const wordCount = words.length;

    // Detect filler words
    for (const filler of FILLER_WORDS) {
      const regex = new RegExp(`\\b${filler}\\b`, 'gi');
      const matches = text.toLowerCase().match(regex);
      if (matches) {
        foundFillers.push({ word: filler, count: matches.length });
      }
    }

    // Calculate speaking speed if we have timing info
    let wordsPerMinute = 0;
    if (startTimeRef.current && wordCount > 0) {
      const elapsedSeconds = (Date.now() - startTimeRef.current) / 1000;
      wordsPerMinute = Math.round((wordCount / elapsedSeconds) * 60);
    }

    // Estimate confidence based on sentence structure and fillers
    let confidence = 85;
    if (foundFillers.length > 0) {
      confidence -= Math.min(20, foundFillers.reduce((a, b) => a + b.count, 0) * 3);
    }
    if (text.endsWith("...") || text.includes("?")) {
      confidence -= 5;
    }
    if (wordCount > 10 && wordsPerMinute > 0 && wordsPerMinute < 200) {
      confidence += 5;
    }
    confidence = Math.max(50, Math.min(100, confidence));

    setSpeechMetrics({
      confidence,
      speakingSpeed: wordsPerMinute > 150 ? "fast" : wordsPerMinute < 100 ? "slow" : "normal",
      fillerWords: foundFillers,
      fillerWordCount: foundFillers.reduce((a, b) => a + b.count, 0),
      wordsPerMinute,
      totalWords: wordCount,
    });
  }, []);

  const startListening = async () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = "en-US";

    recognitionRef.current.onstart = () => {
      setIsListening(true);
      startTimeRef.current = Date.now();
      wordsRef.current = [];
      initAudioVisualization();
    };

    recognitionRef.current.onresult = (event) => {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      setInterimTranscript(interim);
      if (final) {
        setTranscript(prev => prev + " " + final);
        wordsRef.current = [...wordsRef.current, ...final.split(/\s+/)];
        analyzeSpeech(transcript);
      }
    };

    recognitionRef.current.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      if (event.error !== "no-speech") {
        setIsListening(false);
      }
    };

    recognitionRef.current.onend = () => {
      setIsListening(false);
      setAudioLevel(0);
      if (transcript.trim()) {
        processTranscript();
      }
    };

    try {
      recognitionRef.current.start();
    } catch (err) {
      console.error("Failed to start recognition:", err);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
    setAudioLevel(0);
    if (transcript.trim()) {
      processTranscript();
    }
  };

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

  const processTranscript = async () => {
    if (!transcript.trim()) return;
    setLoading(true);

    try {
      const token = localStorage.getItem("aijob_tokens");
      const headers = { Authorization: `Bearer ${JSON.parse(token).access}` };

      const payload = {
        session_id: sessionId,
        transcript: transcript.trim(),
        speech_analysis: speechMetrics,
      };

      const res = await api.post(
        "/api/jobs/voice/transcript/process/",
        payload,
        { headers }
      );

      setResponse(res.data.response);
      setHistory([...history, {
        transcript: transcript.trim(),
        response: res.data.response,
        mood: res.data.mood_detected,
        metrics: { ...speechMetrics },
      }]);
    } catch (err) {
      // Mock response with follow-up questions
      let mockResponse = "";
      let followUpQuestions = [];

      if (sessionType === "interview") {
        mockResponse = "That's a solid answer! I'd like to dig deeper. ";
        followUpQuestions = [
          "Can you tell me about a specific time you faced a difficult technical challenge?",
          "How do you handle disagreements with team members?",
        ];
      } else if (sessionType === "advice") {
        mockResponse = "Great question! Here are some actionable steps: ";
        followUpQuestions = [
          "What's your current role and how many years of experience do you have?",
          "Are you more interested in technical leadership or management?",
        ];
      } else {
        mockResponse = "Let me help you with that skill. ";
        followUpQuestions = [
          "What's your current proficiency level in this skill?",
          "How much time can you dedicate to learning per week?",
        ];
      }

      setResponse(mockResponse);
      setHistory([...history, {
        transcript: transcript.trim(),
        response: mockResponse,
        mood: speechMetrics.confidence > 70 ? "confident" : "uncertain",
        metrics: { ...speechMetrics },
        followUpQuestions,
      }]);
    } finally {
      setLoading(false);
      setTranscript("");
      setInterimTranscript("");
      setSpeechMetrics({
        confidence: 0,
        speakingSpeed: 0,
        fillerWords: [],
        fillerWordCount: 0,
        wordsPerMinute: 0,
        totalWords: 0,
      });
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!transcript.trim()) return;
    analyzeSpeech(transcript);
    processTranscript();
  };

  const playAudio = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1;
      utterance.pitch = 1;
      speechSynthesis.speak(utterance);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return "text-green-500";
    if (confidence >= 60) return "text-yellow-500";
    return "text-red-500";
  };

  const getSpeedLabel = (wpm) => {
    if (wpm === 0) return "N/A";
    if (wpm < 100) return "Slow";
    if (wpm > 160) return "Fast";
    return "Optimal";
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

      {/* Settings */}
      <div className="flex items-center gap-4 mb-6 p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center gap-2">
          <Radio className={`w-4 h-4 ${useWebSpeech ? "text-blue-500" : "text-gray-400"}`} />
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              checked={useWebSpeech}
              onChange={() => setUseWebSpeech(true)}
              className="w-4 h-4"
            />
            <span className="text-sm">Web Speech API</span>
          </label>
        </div>
        <div className="flex items-center gap-2">
          <Cloud className={`w-4 h-4 ${useWhisper ? "text-purple-500" : "text-gray-400"}`} />
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={useWhisper}
              onChange={(e) => setUseWhisper(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm">Use Whisper (Higher Quality)</span>
          </label>
        </div>
        {!speechSupported && (
          <div className="flex items-center gap-2 text-red-500 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>Speech recognition not supported</span>
          </div>
        )}
      </div>

      {/* Session Type Selector */}
      <div className="flex gap-2 mb-6">
        {sessionTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => { setSessionType(type.id); startSession(); }}
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
        {/* Speech Metrics Display */}
        {(isListening || speechMetrics.totalWords > 0) && (
          <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 border-b">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-6">
                {/* Confidence Score */}
                <div className="flex items-center gap-2">
                  <BarChart3 className={`w-5 h-5 ${getConfidenceColor(speechMetrics.confidence)}`} />
                  <span className="text-sm font-medium">Confidence:</span>
                  <span className={`font-bold ${getConfidenceColor(speechMetrics.confidence)}`}>
                    {speechMetrics.confidence}%
                  </span>
                </div>

                {/* Speaking Speed */}
                <div className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-500" />
                  <span className="text-sm font-medium">Speed:</span>
                  <span className="font-bold">{getSpeedLabel(speechMetrics.wordsPerMinute)}</span>
                  {speechMetrics.wordsPerMinute > 0 && (
                    <span className="text-xs text-gray-500">({speechMetrics.wordsPerMinute} WPM)</span>
                  )}
                </div>

                {/* Filler Words */}
                {speechMetrics.fillerWordCount > 0 && (
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-orange-500" />
                    <span className="text-sm font-medium">Fillers:</span>
                    <span className="font-bold text-orange-600">{speechMetrics.fillerWordCount}</span>
                  </div>
                )}
              </div>

              {/* Audio Level */}
              {isListening && (
                <div className="flex items-center gap-2">
                  <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 transition-all duration-100"
                      style={{ width: `${audioLevel}%` }}
                    />
                  </div>
                  <Mic className="w-4 h-4 text-red-500 animate-pulse" />
                </div>
              )}
            </div>

            {/* Filler Words Details */}
            {speechMetrics.fillerWords.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {speechMetrics.fillerWords.map((f, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full"
                  >
                    "{f.word}" ({f.count})
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Chat Area */}
        <div className="h-96 p-6 overflow-y-auto space-y-4">
          {history.length === 0 && !transcript && !interimTranscript && (
            <div className="text-center py-12 text-gray-500">
              <Bot className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>Start a conversation with your AI career coach</p>
              <p className="text-sm mt-2">Click the microphone or type to begin</p>
            </div>
          )}

          {/* Interim Transcript */}
          {interimTranscript && (
            <div className="bg-gray-100 p-3 rounded-lg italic text-gray-500">
              {interimTranscript}...
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
                {/* User Message with Metrics */}
                <div className="flex justify-end">
                  <div className="bg-blue-500 text-white p-4 rounded-l-lg rounded-tr-lg max-w-md">
                    <div className="flex items-center gap-2 mb-1">
                      <Mic className="w-4 h-4" />
                      <span className="text-xs opacity-80">You</span>
                      {item.metrics?.totalWords > 0 && (
                        <span className="text-xs opacity-60 ml-auto">
                          {item.metrics.totalWords} words | {item.metrics.wordsPerMinute} WPM
                        </span>
                      )}
                    </div>
                    {item.transcript}
                    {item.metrics?.confidence > 0 && (
                      <div className="mt-2 pt-2 border-t border-blue-400 text-xs opacity-80">
                        Confidence: {item.metrics.confidence}% | Fillers: {item.metrics.fillerWordCount}
                      </div>
                    )}
                  </div>
                </div>

                {/* AI Response */}
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-800 p-4 rounded-r-lg rounded-tl-lg max-w-md">
                    <div className="flex items-center gap-2 mb-1">
                      <Bot className="w-4 h-4 text-purple-500" />
                      <span className="text-xs text-gray-500">AI Coach</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        item.mood === "confident" ? "bg-green-100 text-green-700" :
                        item.mood === "uncertain" ? "bg-yellow-100 text-yellow-700" :
                        "bg-gray-200"
                      }`}>
                        {item.mood || "neutral"}
                      </span>
                    </div>
                    {item.response}

                    {/* Follow-up Questions */}
                    {item.followUpQuestions && item.followUpQuestions.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs font-medium text-purple-600 mb-2">Follow-up Questions:</p>
                        {item.followUpQuestions.map((q, qidx) => (
                          <button
                            key={qidx}
                            onClick={() => { setTranscript(q); }}
                            className="block w-full text-left text-sm text-blue-600 hover:text-blue-800 py-1"
                          >
                            • {q}
                          </button>
                        ))}
                      </div>
                    )}

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
              onClick={isListening ? stopListening : startListening}
              disabled={!speechSupported}
              className={`w-16 h-16 rounded-full flex items-center justify-center transition ${
                isListening
                  ? "bg-red-500 animate-pulse"
                  : "bg-gray-800 hover:bg-gray-900 disabled:bg-gray-400"
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
            {isListening ? "Listening... Speak now (click to stop)" : "Click to use voice input"}
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
                <div className="flex items-center gap-2">
                  {item.metrics?.confidence > 0 && (
                    <span className={`text-xs px-2 py-1 rounded ${getConfidenceColor(item.metrics.confidence).replace('text-', 'bg-').replace('500', '100')}`}>
                      {item.metrics.confidence}%
                    </span>
                  )}
                  <span className="text-sm text-gray-500">{item.mood}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}