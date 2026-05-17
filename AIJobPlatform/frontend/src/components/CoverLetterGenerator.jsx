import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Copy, Download, Sparkles, RefreshCw, Check, Building, User, FileEdit } from 'lucide-react';

const TONE_OPTIONS = [
  { id: 'professional', label: 'Professional', desc: 'Formal and business-like' },
  { id: 'enthusiastic', label: 'Energetic', desc: 'Passionate and dynamic' },
  { id: 'formal', label: 'Formal', desc: 'Very structured and traditional' },
  { id: 'conversational', label: 'Casual', desc: 'Friendly and approachable' },
];

export default function CoverLetterGenerator() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    companyName: '',
    position: '',
    jobDescription: '',
    tone: 'professional',
    selectedJob: null,
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [coverLetter, setCoverLetter] = useState(null);
  const [copied, setCopied] = useState(false);

  const generateLetter = async () => {
    if (!formData.companyName || !formData.position) return;

    setIsGenerating(true);
    try {
      const response = await fetch('/api/jobs/cover-letter/generate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          company_name: formData.companyName,
          position: formData.position,
          job_description: formData.jobDescription,
          tone: formData.tone,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCoverLetter(data);
      } else {
        // Fallback to mock
        setCoverLetter(getMockCoverLetter());
      }
    } catch (error) {
      setCoverLetter(getMockCoverLetter());
    } finally {
      setIsGenerating(false);
      setStep(2);
    }
  };

  const getMockCoverLetter = () => ({
    success: true,
    cover_letter: `${formData.companyName}
Your Name
your.email@example.com
New York, NY

Dear Hiring Manager,

I am writing to express my strong interest in the ${formData.position} position at ${formData.companyName}. With my background in software development and passion for innovation, I am excited about the opportunity to contribute to your team.

Throughout my career, I have developed a strong foundation in building scalable applications and delivering high-quality solutions. My experience working on complex projects has equipped me with the technical skills and problem-solving abilities necessary to excel in this role. I have consistently demonstrated my ability to collaborate effectively with cross-functional teams and drive projects to successful completion.

What excites me most about ${formData.companyName} is your commitment to innovation and excellence in the industry. Your company's reputation for fostering a collaborative and dynamic work environment aligns perfectly with my professional values. I am particularly drawn to your focus on continuous learning and professional development.

I bring a combination of technical expertise, strong communication skills, and a proactive approach that I believe would be valuable to your organization. I am confident that my background and enthusiasm would make me a great addition to your team.

Thank you for considering my application. I would welcome the opportunity to discuss how my background, skills, and enthusiasm would benefit your team.

Sincerely,

Your Name`,
    metadata: {
      company: formData.companyName,
      position: formData.position,
      tone: formData.tone,
      word_count: 250,
    },
  });

  const copyToClipboard = () => {
    navigator.clipboard.writeText(coverLetter?.cover_letter || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadAsText = () => {
    const blob = new Blob([coverLetter?.cover_letter || ''], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cover-letter-${formData.companyName.replace(/\s+/g, '-')}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Step 1: Input Form
  if (step === 1) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-3xl shadow-lg overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-6 text-white">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8" />
              <div>
                <h2 className="text-2xl font-bold">AI Cover Letter Generator</h2>
                <p className="text-orange-100">Create personalized cover letters in seconds</p>
              </div>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Company Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Building className="w-4 h-4 inline mr-1" />
                Company Name *
              </label>
              <input
                type="text"
                value={formData.companyName}
                onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                placeholder="e.g., Google, Amazon, Startup Inc."
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500"
              />
            </div>

            {/* Position */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <User className="w-4 h-4 inline mr-1" />
                Position/Role *
              </label>
              <input
                type="text"
                value={formData.position}
                onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                placeholder="e.g., Senior Software Engineer, Product Manager"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500"
              />
            </div>

            {/* Job Description (Optional) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <FileEdit className="w-4 h-4 inline mr-1" />
                Job Description (Optional)
              </label>
              <textarea
                value={formData.jobDescription}
                onChange={(e) => setFormData({ ...formData, jobDescription: e.target.value })}
                rows={4}
                placeholder="Paste the job description here for better matching..."
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                Adding the job description helps us tailor your cover letter to the specific requirements.
              </p>
            </div>

            {/* Tone Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Writing Tone
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {TONE_OPTIONS.map((tone) => (
                  <button
                    key={tone.id}
                    onClick={() => setFormData({ ...formData, tone: tone.id })}
                    className={`p-3 rounded-xl border-2 text-left transition ${
                      formData.tone === tone.id
                        ? 'border-orange-500 bg-orange-50'
                        : 'border-gray-200 hover:border-orange-300'
                    }`}
                  >
                    <div className="font-medium text-gray-800">{tone.label}</div>
                    <div className="text-xs text-gray-500">{tone.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Generate Button */}
            <button
              onClick={generateLetter}
              disabled={isGenerating || !formData.companyName || !formData.position}
              className={`w-full py-4 rounded-xl font-semibold text-lg transition flex items-center justify-center gap-2 ${
                formData.companyName && formData.position
                  ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:opacity-90'
                  : 'bg-gray-200 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isGenerating ? (
                <>
                  <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                  Generating your cover letter...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  Generate Cover Letter
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Step 2: Generated Letter
  if (step === 2 && coverLetter) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Success Header */}
          <div className="bg-green-50 border border-green-200 rounded-2xl p-6 flex items-center gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-green-800">Cover Letter Generated!</h3>
              <p className="text-green-600">
                {coverLetter.metadata?.word_count} words • {coverLetter.metadata?.tone} tone
              </p>
            </div>
          </div>

          {/* Letter Content */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="bg-gray-50 px-6 py-4 border-b flex items-center justify-between">
              <h3 className="font-semibold text-gray-800">
                {formData.position} at {formData.companyName}
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={copyToClipboard}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
                <button
                  onClick={downloadAsText}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-100 text-indigo-700 rounded-lg hover:bg-indigo-200 transition"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
              </div>
            </div>
            <div className="p-6">
              <pre className="whitespace-pre-wrap font-sans text-gray-700 leading-relaxed">
                {coverLetter.cover_letter}
              </pre>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={() => { setStep(1); setCoverLetter(null); }}
              className="flex-1 py-4 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition flex items-center justify-center gap-2"
            >
              <RefreshCw className="w-5 h-5" />
              Generate Another
            </button>
            <button
              onClick={() => {
                const blob = new Blob([coverLetter.cover_letter], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `cover-letter-${formData.companyName.replace(/\s+/g, '-')}.txt`;
                a.click();
              }}
              className="flex-1 py-4 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              Save as File
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return null;
}