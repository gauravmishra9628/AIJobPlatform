import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Play, Pause, Send, Brain, MessageSquare, Volume2, ChevronRight, Award, Target, Zap } from 'lucide-react';

const ROLES = [
  { id: 'software_engineer', label: 'Software Engineer', icon: '💻' },
  { id: 'data_scientist', label: 'Data Scientist', icon: '📊' },
  { id: 'frontend_developer', label: 'Frontend Developer', icon: '🎨' },
  { id: 'backend_developer', label: 'Backend Developer', icon: '⚙️' },
  { id: 'devops', label: 'DevOps Engineer', icon: '🚀' },
];

export default function AIInterviewPrep() {
  const [step, setStep] = useState(1); // 1: role, 2: interview, 3: results
  const [selectedRole, setSelectedRole] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answer, setAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [results, setResults] = useState([]);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const recognitionRef = useRef(null);
  const synthRef = useRef(null);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setTranscript(prev => prev + ' ' + finalTranscript);
          setAnswer(prev => prev + ' ' + finalTranscript);
        }
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };
    }

    // Initialize speech synthesis
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      synthRef.current = window.speechSynthesis;
    }
  }, []);

  const generateQuestions = () => {
    const mockQuestions = [
      {
        question: "Tell me about a challenging technical problem you faced and how you solved it.",
        type: "behavioral",
        tips: ["Use STAR method", "Focus on your specific contributions", "Quantify the impact"]
      },
      {
        question: "Explain the difference between REST and GraphQL APIs. When would you choose one over the other?",
        type: "technical",
        tips: ["Start with high-level comparison", "Give practical examples", "Mention trade-offs"]
      },
      {
        question: "How do you handle disagreements with team members on technical decisions?",
        type: "situational",
        tips: ["Show empathy", "Focus on data-driven decisions", "Mention collaboration"]
      },
      {
        question: "What is the time complexity of quicksort in average and worst case? How can you optimize it?",
        type: "technical",
        tips: ["Be precise with complexity", "Explain the difference", "Mention optimizations"]
      },
      {
        question: "Where do you see yourself in 5 years?",
        type: "behavioral",
        tips: ["Show ambition", "Align with company growth", "Be realistic"]
      },
    ];
    setQuestions(mockQuestions);
    setStep(2);
  };

  const startRecording = () => {
    if (recognitionRef.current && !isListening) {
      recognitionRef.current.start();
      setIsListening(true);
      setIsRecording(true);
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      setIsRecording(false);
    }
  };

  const speakQuestion = () => {
    if (synthRef.current && questions[currentQuestion]) {
      const utterance = new SpeechSynthesisUtterance(questions[currentQuestion].question);
      utterance.rate = 0.9;
      synthRef.current.speak(utterance);
      setIsPlaying(true);
    }
  };

  const analyzeAnswer = () => {
    // Mock analysis - in production this would call the AI API
    const mockFeedback = {
      overall_score: Math.floor(Math.random() * 30) + 70,
      length_score: Math.min(100, answer.split(' ').length * 3),
      clarity_score: Math.floor(Math.random() * 20) + 70,
      content_score: Math.floor(Math.random() * 20) + 70,
      confidence_score: isListening ? 60 : Math.floor(Math.random() * 20) + 75,
      strengths: [
        "Good use of specific examples",
        "Clear structure to your answer",
        answer.split(' ').length > 30 ? "Comprehensive answer" : "To the point response"
      ],
      improvements: [
        answer.split(' ').length < 20 ? "Try to provide more detail" : null,
        !transcript.includes('I') || !transcript.includes('we') ? "Use more first-person perspective" : null
      ].filter(Boolean),
      suggestions: [
        "Consider using the STAR method for behavioral questions",
        "Try to include quantifiable achievements"
      ]
    };

    setFeedback(mockFeedback);
    setShowFeedback(true);

    // Add to results
    setResults(prev => [...prev, {
      question: questions[currentQuestion].question,
      answer: answer,
      feedback: mockFeedback,
      type: questions[currentQuestion].type
    }]);
  };

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
      setAnswer('');
      setTranscript('');
      setShowFeedback(false);
      setFeedback(null);
    } else {
      setStep(3);
    }
  };

  // Step 1: Role Selection
  if (step === 1) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg p-8"
        >
          <div className="text-center mb-8">
            <div className="text-5xl mb-4">🎯</div>
            <h2 className="text-3xl font-bold text-gray-800">AI Mock Interview</h2>
            <p className="text-gray-600 mt-2">Practice with AI-generated questions and get real-time feedback</p>
          </div>

          <h3 className="text-lg font-semibold text-gray-700 mb-4">Select your target role:</h3>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
            {ROLES.map((role) => (
              <button
                key={role.id}
                onClick={() => setSelectedRole(role.id)}
                className={`p-6 rounded-xl border-2 transition-all ${
                  selectedRole === role.id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-indigo-300'
                }`}
              >
                <span className="text-3xl block mb-2">{role.icon}</span>
                <span className="font-medium text-gray-700">{role.label}</span>
              </button>
            ))}
          </div>

          <div className="bg-indigo-50 rounded-xl p-4 mb-6">
            <h4 className="font-semibold text-indigo-800 mb-2">What you'll get:</h4>
            <ul className="text-sm text-indigo-700 space-y-1">
              <li>✨ 5 personalized interview questions</li>
              <li>🎤 Voice recording & transcription</li>
              <li>📊 Real-time AI feedback</li>
              <li>💪 Confidence & communication analysis</li>
            </ul>
          </div>

          <button
            onClick={generateQuestions}
            disabled={!selectedRole}
            className={`w-full py-4 rounded-xl font-semibold text-lg transition ${
              selectedRole
                ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
            }`}
          >
            Start Interview Practice
          </button>
        </motion.div>
      </div>
    );
  }

  // Step 2: Interview
  if (step === 2) {
    const currentQ = questions[currentQuestion];

    return (
      <div className="max-w-3xl mx-auto p-6">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Question {currentQuestion + 1} of {questions.length}</span>
            <span>{Math.round(((currentQuestion) / questions.length) * 100)}% Complete</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full">
            <div
              className="h-2 bg-indigo-600 rounded-full transition-all"
              style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
            />
          </div>
        </div>

        <motion.div
          key={currentQuestion}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-2xl shadow-lg p-8"
        >
          {/* Question Header */}
          <div className="flex items-center justify-between mb-4">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              currentQ.type === 'technical' ? 'bg-blue-100 text-blue-700' :
              currentQ.type === 'behavioral' ? 'bg-purple-100 text-purple-700' :
              'bg-orange-100 text-orange-700'
            }`}>
              {currentQ.type.charAt(0).toUpperCase() + currentQ.type.slice(1)} Question
            </span>
            <button
              onClick={speakQuestion}
              className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg"
              title="Read aloud"
            >
              <Volume2 size={20} />
            </button>
          </div>

          {/* Question */}
          <h3 className="text-xl font-semibold text-gray-800 mb-6">{currentQ.question}</h3>

          {/* Tips */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-gray-700 mb-2">
              <Zap size={16} className="text-yellow-500" />
              <span className="font-medium">Tips:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {currentQ.tips.map((tip, i) => (
                <span key={i} className="text-sm text-gray-600 bg-white px-2 py-1 rounded">
                  {tip}
                </span>
              ))}
            </div>
          </div>

          {/* Answer Area */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Answer {isRecording && <span className="text-red-500">(Recording...)</span>}
            </label>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder={isRecording ? "Speak or type your answer..." : "Type your answer here or click the microphone to speak..."}
              className="w-full h-40 p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* Voice Controls */}
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
                isRecording
                  ? 'bg-red-100 text-red-700 hover:bg-red-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
              {isRecording ? 'Stop Recording' : 'Start Voice'}
            </button>

            {transcript && (
              <div className="flex-1 text-sm text-gray-500">
                Live transcript: {transcript.slice(-50)}...
              </div>
            )}
          </div>

          {/* Show Feedback or Actions */}
          <AnimatePresence>
            {showFeedback && feedback && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-indigo-50 rounded-xl p-6 mb-6"
              >
                <div className="flex items-center gap-2 mb-4">
                  <Brain className="text-indigo-600" />
                  <h4 className="font-semibold text-indigo-800">AI Feedback</h4>
                </div>

                {/* Scores */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  {[
                    { label: 'Overall', value: feedback.overall_score },
                    { label: 'Clarity', value: feedback.clarity_score },
                    { label: 'Content', value: feedback.content_score },
                    { label: 'Confidence', value: feedback.confidence_score },
                  ].map((item) => (
                    <div key={item.label} className="text-center p-3 bg-white rounded-lg">
                      <div className="text-2xl font-bold text-indigo-600">{item.value}</div>
                      <div className="text-xs text-gray-500">{item.label}</div>
                    </div>
                  ))}
                </div>

                {/* Strengths & Improvements */}
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h5 className="font-medium text-green-700 mb-2">✓ Strengths</h5>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {feedback.strengths.map((s, i) => <li key={i}>• {s}</li>)}
                    </ul>
                  </div>
                  {feedback.improvements.length > 0 && (
                    <div>
                      <h5 className="font-medium text-orange-700 mb-2">↑ Improvements</h5>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {feedback.improvements.map((i, idx) => <li key={idx}>• {i}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action Buttons */}
          <div className="flex gap-4">
            {!showFeedback ? (
              <button
                onClick={analyzeAnswer}
                disabled={!answer.trim()}
                className={`flex-1 py-3 rounded-xl font-medium transition ${
                  answer.trim()
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                <Send className="inline mr-2" size={18} />
                Get AI Feedback
              </button>
            ) : (
              <button
                onClick={nextQuestion}
                className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition flex items-center justify-center gap-2"
              >
                {currentQuestion < questions.length - 1 ? (
                  <>Next Question <ChevronRight /></>
                ) : (
                  <>View Results <Award /></>
                )}
              </button>
            )}
          </div>
        </motion.div>
      </div>
    );
  }

  // Step 3: Results
  if (step === 3) {
    const avgScore = Math.round(results.reduce((acc, r) => acc + r.feedback.overall_score, 0) / results.length);

    return (
      <div className="max-w-3xl mx-auto p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl shadow-lg p-8 text-center"
        >
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">Interview Complete!</h2>
          <p className="text-gray-600 mb-8">Here's how you performed</p>

          {/* Overall Score */}
          <div className="relative w-40 h-40 mx-auto mb-8">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="80" cy="80" r="70" fill="none" stroke="#e5e7eb" strokeWidth="12" />
              <circle
                cx="80" cy="80" r="70" fill="none"
                stroke={avgScore >= 70 ? '#6366f1' : '#f59e0b'}
                strokeWidth="12"
                strokeDasharray={`${(avgScore / 100) * 440} 440`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-bold text-gray-800">{avgScore}</span>
              <span className="text-sm text-gray-500">Average</span>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="p-4 bg-gray-50 rounded-xl">
              <div className="text-2xl font-bold text-indigo-600">{results.length}</div>
              <div className="text-sm text-gray-600">Questions</div>
            </div>
            <div className="p-4 bg-gray-50 rounded-xl">
              <div className="text-2xl font-bold text-green-600">
                {results.filter(r => r.feedback.overall_score >= 70).length}
              </div>
              <div className="text-sm text-gray-600">Good</div>
            </div>
            <div className="p-4 bg-gray-50 rounded-xl">
              <div className="text-2xl font-bold text-orange-600">
                {results.filter(r => r.feedback.overall_score < 70).length}
              </div>
              <div className="text-sm text-gray-600">Need Work</div>
            </div>
          </div>

          {/* Question Breakdown */}
          <div className="text-left mb-8">
            <h3 className="font-semibold text-gray-800 mb-4">Question Breakdown</h3>
            <div className="space-y-3">
              {results.map((result, i) => (
                <div key={i} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div className="flex-1 mr-4">
                    <p className="text-sm text-gray-700 line-clamp-1">{result.question}</p>
                    <span className="text-xs text-gray-500">{result.type}</span>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    result.feedback.overall_score >= 70 ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'
                  }`}>
                    {result.feedback.overall_score}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={() => { setStep(1); setResults([]); setCurrentQuestion(0); }}
              className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition"
            >
              Practice Again
            </button>
            <button className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition">
              View Full Report
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return null;
}