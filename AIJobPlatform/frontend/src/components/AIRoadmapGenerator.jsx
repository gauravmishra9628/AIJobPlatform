import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Calendar, BookOpen, Code, Youtube, Award, CheckCircle, ChevronRight, Sparkles, Clock, Target, Zap } from 'lucide-react';

const CAREER_OPTIONS = [
  { id: 'data_scientist', label: 'Data Scientist', icon: '📊', color: 'blue' },
  { id: 'software_engineer', label: 'Software Engineer', icon: '💻', color: 'indigo' },
  { id: 'frontend_developer', label: 'Frontend Developer', icon: '🎨', color: 'pink' },
  { id: 'backend_developer', label: 'Backend Developer', icon: '⚙️', color: 'green' },
  { id: 'ai_engineer', label: 'AI/ML Engineer', icon: '🤖', color: 'purple' },
  { id: 'devops', label: 'DevOps Engineer', icon: '🚀', color: 'orange' },
  { id: 'product_manager', label: 'Product Manager', icon: '📦', color: 'teal' },
  { id: 'custom', label: 'Custom Goal', icon: '✨', color: 'yellow' },
];

const TIMEFRAME_OPTIONS = [
  { id: '3_months', label: '3 Months', desc: 'Intensive' },
  { id: '6_months', label: '6 Months', desc: 'Balanced' },
  { id: '1_year', label: '12 Months', desc: 'Relaxed' },
];

export default function AIRoadmapGenerator() {
  const [step, setStep] = useState(1);
  const [careerGoal, setCareerGoal] = useState('');
  const [selectedCareer, setSelectedCareer] = useState(null);
  const [timeframe, setTimeframe] = useState('6_months');
  const [currentSkills, setCurrentSkills] = useState([]);
  const [skillInput, setSkillInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [roadmap, setRoadmap] = useState(null);

  const generateRoadmap = async () => {
    setIsGenerating(true);
    try {
      // Call API (or use mock data)
      const response = await fetch('/api/jobs/career/internship-roadmap/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          career_goal: selectedCareer || careerGoal,
          current_skills: currentSkills,
          timeframe: timeframe,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setRoadmap(data);
      } else {
        setRoadmap(getMockRoadmap());
      }
    } catch (error) {
      setRoadmap(getMockRoadmap());
    } finally {
      setIsGenerating(false);
      setStep(2);
    }
  };

  const getMockRoadmap = () => ({
    career_path: CAREER_OPTIONS.find(c => c.id === selectedCareer)?.label || 'Data Scientist',
    total_duration: timeframe === '3_months' ? 3 : timeframe === '6_months' ? 6 : 12,
    milestones: [
      { week: 1, skill: 'Python Fundamentals', duration_weeks: 2, priority: 'high', deliverable: 'Build 5 Python scripts' },
      { week: 3, skill: 'Data Structures & Arrays', duration_weeks: 2, priority: 'high', deliverable: 'Solve 50 array problems' },
      { week: 5, skill: 'Statistics & Probability', duration_weeks: 3, priority: 'high', deliverable: 'Statistical analysis project' },
      { week: 8, skill: 'Pandas & NumPy', duration_weeks: 2, priority: 'high', deliverable: 'EDA on real dataset' },
      { week: 10, skill: 'Machine Learning Basics', duration_weeks: 4, priority: 'high', deliverable: 'Predictive model' },
      { week: 14, skill: 'Scikit-Learn', duration_weeks: 3, priority: 'medium', deliverable: 'Classification project' },
      { week: 17, skill: 'Deep Learning Intro', duration_weeks: 3, priority: 'medium', deliverable: 'Neural network project' },
      { week: 20, skill: 'MLOps Basics', duration_weeks: 2, priority: 'medium', deploy: 'ML model to cloud' },
      { week: 22, skill: 'Capstone Project', duration_weeks: 4, priority: 'high', deliverable: 'Complete ML portfolio project' },
    ],
    skills_to_learn: [
      { name: 'Python', weeks: 2, priority: 'high' },
      { name: 'Statistics', weeks: 3, priority: 'high' },
      { name: 'SQL', weeks: 2, priority: 'high' },
      { name: 'Pandas', weeks: 2, priority: 'high' },
      { name: 'Machine Learning', weeks: 4, priority: 'high' },
      { name: 'Scikit-Learn', weeks: 3, priority: 'medium' },
      { name: 'Deep Learning', weeks: 3, priority: 'medium' },
    ],
    projects: ['Exploratory Data Analysis', 'Predictive Model', 'Customer Segmentation', 'Recommendation System', 'End-to-End ML Pipeline'],
    certifications: ['IBM Data Science Certificate', 'Google Data Analytics', 'AWS ML Specialty'],
    resources: {
      youtube_channels: [
        { name: 'Kaggle', url: '#', subs: '500K+' },
        { name: 'StatQuest', url: '#', subs: '1M+' },
        { name: '3Blue1Brown', url: '#', subs: '5M+' },
        { name: 'TechTFQ', url: '#', subs: '200K+' },
      ],
      courses: [
        { name: 'freeCodeCamp', type: 'Free' },
        { name: 'Kaggle Learn', type: 'Free' },
        { name: 'DataCamp', type: 'Paid' },
      ],
      practice: ['LeetCode', 'Kaggle', 'GitHub'],
    },
    summary: 'Become a Data Scientist in 6 months by mastering Python, Statistics, and Machine Learning',
  });

  const addSkill = () => {
    if (skillInput.trim() && !currentSkills.includes(skillInput.trim())) {
      setCurrentSkills([...currentSkills, skillInput.trim()]);
      setSkillInput('');
    }
  };

  const removeSkill = (skill) => {
    setCurrentSkills(currentSkills.filter(s => s !== skill));
  };

  // Step 1: Select Career
  if (step === 1) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-3xl shadow-lg overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-8 text-white">
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="w-8 h-8" />
              <h2 className="text-3xl font-bold">AI Career Roadmap Generator</h2>
            </div>
            <p className="text-indigo-100 text-lg">Tell us your dream career and we'll create a personalized learning path</p>
          </div>

          <div className="p-8">
            {/* Step 1: Career Selection */}
            <div className="mb-8">
              <label className="block text-lg font-semibold text-gray-800 mb-4">
                🎯 What career do you want to pursue?
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {CAREER_OPTIONS.map((career) => (
                  <button
                    key={career.id}
                    onClick={() => { setSelectedCareer(career.id); setCareerGoal(career.label); }}
                    className={`p-4 rounded-xl border-2 transition-all text-left ${
                      selectedCareer === career.id
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-indigo-300'
                    }`}
                  >
                    <span className="text-2xl block mb-1">{career.icon}</span>
                    <span className="text-sm font-medium text-gray-700">{career.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Goal Input */}
            <div className="mb-8">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Or type your custom goal:
              </label>
              <input
                type="text"
                value={careerGoal}
                onChange={(e) => { setCareerGoal(e.target.value); setSelectedCareer('custom'); }}
                placeholder="e.g., Blockchain Developer, UX Designer..."
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {/* Step 2: Current Skills */}
            <div className="mb-8">
              <label className="block text-lg font-semibold text-gray-800 mb-4">
                🛠️ What skills do you already have?
              </label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addSkill()}
                  placeholder="Add a skill (e.g., Python)"
                  className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={addSkill}
                  className="px-6 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {currentSkills.map((skill) => (
                  <span
                    key={skill}
                    className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium flex items-center gap-1"
                  >
                    {skill}
                    <button onClick={() => removeSkill(skill)} className="hover:text-indigo-900">×</button>
                  </span>
                ))}
                {currentSkills.length === 0 && (
                  <span className="text-gray-400 text-sm">No skills added yet</span>
                )}
              </div>
            </div>

            {/* Step 3: Timeframe */}
            <div className="mb-8">
              <label className="block text-lg font-semibold text-gray-800 mb-4">
                ⏱️ How quickly do you want to achieve this?
              </label>
              <div className="grid grid-cols-3 gap-4">
                {TIMEFRAME_OPTIONS.map((option) => (
                  <button
                    key={option.id}
                    onClick={() => setTimeframe(option.id)}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      timeframe === option.id
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-indigo-300'
                    }`}
                  >
                    <div className="text-xl font-bold text-gray-800">{option.label}</div>
                    <div className="text-sm text-gray-500">{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Button */}
            <button
              onClick={generateRoadmap}
              disabled={isGenerating || (!selectedCareer && !careerGoal)}
              className={`w-full py-4 rounded-xl font-semibold text-lg transition flex items-center justify-center gap-2 ${
                selectedCareer || careerGoal
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:opacity-90'
                  : 'bg-gray-200 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                  Generating your personalized roadmap...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Generate My Roadmap
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Step 2: Roadmap Results
  if (step === 2 && roadmap) {
    return (
      <div className="max-w-5xl mx-auto p-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-3xl p-8 text-white mb-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold mb-2">🎉 Your Personalized Roadmap</h2>
              <p className="text-indigo-100 text-lg">{roadmap.summary}</p>
            </div>
            <div className="text-center bg-white/20 rounded-2xl p-4">
              <div className="text-4xl font-bold">{roadmap.total_duration}</div>
              <div className="text-sm">Months</div>
            </div>
          </div>
        </motion.div>

        {/* Timeline */}
        <div className="bg-white rounded-3xl shadow-lg p-8 mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            <MapPin className="text-indigo-600" />
            Your Learning Journey
          </h3>

          <div className="space-y-4">
            {roadmap.milestones.map((milestone, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex gap-4"
              >
                {/* Timeline dot */}
                <div className="flex flex-col items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                    milestone.priority === 'high' ? 'bg-red-100 text-red-600' :
                    milestone.priority === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-green-100 text-green-600'
                  }`}>
                    {milestone.week}
                  </div>
                  {index < roadmap.milestones.length - 1 && (
                    <div className="w-0.5 h-16 bg-gray-200 my-2" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 bg-gray-50 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-800">{milestone.skill}</h4>
                    <span className="text-sm text-gray-500">{milestone.duration_weeks} weeks</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{milestone.description}</p>
                  <div className="flex items-center gap-2 text-xs text-indigo-600">
                    <CheckCircle size={14} />
                    {milestone.deliverable}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Resources Grid */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* YouTube Channels */}
          <div className="bg-white rounded-3xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Youtube className="text-red-500" />
              Recommended YouTube Channels
            </h3>
            <div className="space-y-3">
              {roadmap.resources?.youtube_channels?.map((channel, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-800">{channel.name}</div>
                    <div className="text-xs text-gray-500">{channel.subs} subscribers</div>
                  </div>
                  <a href={channel.url} target="_blank" rel="noopener" className="text-indigo-600 hover:underline text-sm">
                    Visit →
                  </a>
                </div>
              ))}
            </div>
          </div>

          {/* Practice Platforms */}
          <div className="bg-white rounded-3xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Code className="text-green-500" />
              Practice Platforms
            </h3>
            <div className="flex flex-wrap gap-2">
              {roadmap.resources?.practice?.map((platform, i) => (
                <span key={i} className="px-4 py-2 bg-green-50 text-green-700 rounded-full font-medium">
                  {platform}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Projects & Certifications */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Projects */}
          <div className="bg-white rounded-3xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Target className="text-purple-500" />
              Projects to Build
            </h3>
            <ol className="space-y-2">
              {roadmap.projects?.map((project, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-6 h-6 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                    {i + 1}
                  </span>
                  <span className="text-gray-700">{project}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* Certifications */}
          <div className="bg-white rounded-3xl shadow-lg p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Award className="text-yellow-500" />
              Recommended Certifications
            </h3>
            <div className="space-y-2">
              {roadmap.certifications?.map((cert, i) => (
                <div key={i} className="flex items-center gap-2 p-3 bg-yellow-50 rounded-lg">
                  <Award className="text-yellow-600" size={18} />
                  <span className="text-gray-700 font-medium">{cert}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={() => setStep(1)}
            className="flex-1 py-4 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition"
          >
            ← Create Another Roadmap
          </button>
          <button className="flex-1 py-4 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition flex items-center justify-center gap-2">
            Download PDF 📥
          </button>
        </div>
      </div>
    );
  }

  return null;
}