import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Github, Linkedin, Import, Check, X, Loader, User, Code, Briefcase, GraduationCap } from 'lucide-react';

const SKILL_CATEGORIES = {
  'JavaScript': ['React', 'Vue', 'Angular', 'Node.js', 'TypeScript'],
  'Python': ['Django', 'Flask', 'FastAPI', 'Pandas', 'TensorFlow'],
  'Java': ['Spring', 'Hibernate', 'Maven', 'JUnit'],
  'Go': ['Gin', 'Echo', 'Docker', 'Kubernetes'],
  'Rust': ['Tokio', 'Actix', 'Serde'],
};

export default function SocialImport() {
  const [activeTab, setActiveTab] = useState('github');
  const [githubUsername, setGithubUsername] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [linkedInData, setLinkedInData] = useState({
    name: '',
    headline: '',
    location: '',
    summary: '',
    skills: '',
  });

  const importGitHub = async () => {
    if (!githubUsername.trim()) return;

    setIsImporting(true);
    try {
      const response = await fetch('/api/jobs/import/github/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ username: githubUsername }),
      });

      const data = await response.json();
      setImportResult(data);
    } catch (error) {
      setImportResult({ error: 'Failed to import GitHub profile' });
    } finally {
      setIsImporting(false);
    }
  };

  const importLinkedIn = async () => {
    setIsImporting(true);
    try {
      const response = await fetch('/api/jobs/import/linkedin/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(linkedInData),
      });

      const data = await response.json();
      setImportResult(data);
    } catch (error) {
      setImportResult({ error: 'Failed to import LinkedIn data' });
    } finally {
      setIsImporting(false);
    }
  };

  const resetForm = () => {
    setGithubUsername('');
    setImportResult(null);
    setLinkedInData({
      name: '',
      headline: '',
      location: '',
      summary: '',
      skills: '',
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-3xl shadow-lg overflow-hidden"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-800 to-slate-900 p-6 text-white">
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <Import className="w-7 h-7" />
            Import from Social Platforms
          </h2>
          <p className="text-slate-300 mt-1">Connect your GitHub or LinkedIn to auto-fill your profile</p>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => { setActiveTab('github'); resetForm(); }}
            className={`flex-1 py-4 font-medium flex items-center justify-center gap-2 transition ${
              activeTab === 'github'
                ? 'border-b-2 border-slate-800 text-slate-800'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Github className="w-5 h-5" />
            GitHub
          </button>
          <button
            onClick={() => { setActiveTab('linkedin'); resetForm(); }}
            className={`flex-1 py-4 font-medium flex items-center justify-center gap-2 transition ${
              activeTab === 'linkedin'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Linkedin className="w-5 h-5" />
            LinkedIn
          </button>
        </div>

        <div className="p-6">
          <AnimatePresence mode="wait">
            {activeTab === 'github' ? (
              <motion.div
                key="github"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                {/* GitHub Import */}
                {!importResult?.success ? (
                  <div className="space-y-6">
                    <div className="bg-gray-50 rounded-xl p-6">
                      <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                        <Code className="w-5 h-5 text-slate-600" />
                        What we'll import from GitHub:
                      </h3>
                      <ul className="space-y-2 text-gray-600">
                        <li className="flex items-center gap-2">
                          <Check className="w-4 h-4 text-green-500" /> Your bio and profile info
                        </li>
                        <li className="flex items-center gap-2">
                          <Check className="w-4 h-4 text-green-500" /> Programming languages you use
                        </li>
                        <li className="flex items-center gap-2">
                          <Check className="w-4 h-4 text-green-500" /> Top repositories and projects
                        </li>
                        <li className="flex items-center gap-2">
                          <Check className="w-4 h-4 text-green-500" /> Skills from your code
                        </li>
                      </ul>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        GitHub Username
                      </label>
                      <div className="flex gap-3">
                        <div className="flex-1 relative">
                          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                            github.com/
                          </span>
                          <input
                            type="text"
                            value={githubUsername}
                            onChange={(e) => setGithubUsername(e.target.value)}
                            placeholder="your-username"
                            className="w-full pl-32 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-slate-500 focus:border-slate-500"
                          />
                        </div>
                        <button
                          onClick={importGitHub}
                          disabled={isImporting || !githubUsername.trim()}
                          className="px-6 bg-slate-800 text-white rounded-xl font-medium hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                          {isImporting ? (
                            <Loader className="w-5 h-5 animate-spin" />
                          ) : (
                            <Import className="w-5 h-5" />
                          )}
                          Import
                        </button>
                      </div>
                    </div>

                    {importResult?.error && (
                      <div className="p-4 bg-red-50 text-red-600 rounded-xl flex items-center gap-2">
                        <X className="w-5 h-5" />
                        {importResult.error}
                      </div>
                    )}
                  </div>
                ) : (
                  <ImportResult result={importResult} onReset={resetForm} platform="github" />
                )}
              </motion.div>
            ) : (
              <motion.div
                key="linkedin"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {/* LinkedIn Import */}
                {!importResult?.success ? (
                  <div className="space-y-6">
                    <div className="bg-blue-50 rounded-xl p-6">
                      <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                        <Briefcase className="w-5 h-5 text-blue-600" />
                        LinkedIn Import (Manual Entry)
                      </h3>
                      <p className="text-gray-600 text-sm">
                        Due to LinkedIn's restrictions, we use manual entry. Enter your details below and we'll parse them automatically.
                      </p>
                    </div>

                    <div className="grid gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Full Name
                        </label>
                        <input
                          type="text"
                          value={linkedInData.name}
                          onChange={(e) => setLinkedInData({ ...linkedInData, name: e.target.value })}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                          placeholder="John Doe"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Professional Headline
                        </label>
                        <input
                          type="text"
                          value={linkedInData.headline}
                          onChange={(e) => setLinkedInData({ ...linkedInData, headline: e.target.value })}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                          placeholder="Software Engineer at Google"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Location
                        </label>
                        <input
                          type="text"
                          value={linkedInData.location}
                          onChange={(e) => setLinkedInData({ ...linkedInData, location: e.target.value })}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                          placeholder="San Francisco, CA"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Summary
                        </label>
                        <textarea
                          value={linkedInData.summary}
                          onChange={(e) => setLinkedInData({ ...linkedInData, summary: e.target.value })}
                          rows={3}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                          placeholder="Brief professional summary..."
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Skills (comma-separated)
                        </label>
                        <input
                          type="text"
                          value={linkedInData.skills}
                          onChange={(e) => setLinkedInData({ ...linkedInData, skills: e.target.value })}
                          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
                          placeholder="Python, Django, React, SQL, AWS"
                        />
                      </div>

                      <button
                        onClick={importLinkedIn}
                        disabled={isImporting || !linkedInData.name || !linkedInData.headline}
                        className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        {isImporting ? (
                          <Loader className="w-5 h-5 animate-spin" />
                        ) : (
                          <Import className="w-5 h-5" />
                        )}
                        Import LinkedIn Data
                      </button>
                    </div>

                    {importResult?.error && (
                      <div className="p-4 bg-red-50 text-red-600 rounded-xl flex items-center gap-2">
                        <X className="w-5 h-5" />
                        {importResult.error}
                      </div>
                    )}
                  </div>
                ) : (
                  <ImportResult result={importResult} onReset={resetForm} platform="linkedin" />
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}

function ImportResult({ result, onReset, platform }) {
  const importedData = result.imported_data || {};

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="space-y-6"
    >
      <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
        <Check className="w-12 h-12 text-green-500 mx-auto mb-3" />
        <h3 className="text-xl font-bold text-green-800">Import Successful!</h3>
        <p className="text-green-600">{result.message}</p>
      </div>

      {/* Imported Data Summary */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* Skills */}
        {importedData.skills?.length > 0 && (
          <div className="bg-gray-50 rounded-xl p-5">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Code className="w-5 h-5 text-slate-600" />
              Skills Imported
            </h4>
            <div className="flex flex-wrap gap-2">
              {importedData.skills.slice(0, 10).map((skill, i) => (
                <span
                  key={i}
                  className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm"
                >
                  {skill}
                </span>
              ))}
              {importedData.skills.length > 10 && (
                <span className="px-3 py-1 bg-slate-100 text-slate-500 rounded-full text-sm">
                  +{importedData.skills.length - 10} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Profile Info */}
        {importedData.profile && (
          <div className="bg-gray-50 rounded-xl p-5">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <User className="w-5 h-5 text-slate-600" />
              Profile Info
            </h4>
            <div className="space-y-2 text-sm">
              {importedData.profile.name && (
                <p><span className="text-gray-500">Name:</span> {importedData.profile.name}</p>
              )}
              {importedData.profile.bio && (
                <p><span className="text-gray-500">Bio:</span> {importedData.profile.bio}</p>
              )}
              {importedData.profile.location && (
                <p><span className="text-gray-500">Location:</span> {importedData.profile.location}</p>
              )}
            </div>
          </div>
        )}

        {/* Repositories (GitHub) */}
        {importedData.repositories?.length > 0 && (
          <div className="bg-gray-50 rounded-xl p-5 md:col-span-2">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Code className="w-5 h-5 text-slate-600" />
              Top Repositories
            </h4>
            <div className="space-y-2">
              {importedData.repositories.slice(0, 5).map((repo, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-white rounded-lg border">
                  <div>
                    <p className="font-medium text-gray-800">{repo.name}</p>
                    <p className="text-sm text-gray-500">{repo.description}</p>
                  </div>
                  <div className="text-right text-sm">
                    <span className="text-yellow-500">★ {repo.stars}</span>
                    <span className="text-gray-400 ml-2">{repo.language}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <button
        onClick={onReset}
        className="w-full py-3 bg-slate-100 text-slate-700 rounded-xl font-medium hover:bg-slate-200"
      >
        Import Another Account
      </button>
    </motion.div>
  );
}