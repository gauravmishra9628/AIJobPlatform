import React, { useState, useEffect } from 'react';
import { useThemedStyles } from '../contexts/ThemeContext';
import api from '../api';

const SkillVerificationBadges = ({ userId }) => {
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newBadge, setNewBadge] = useState(null);
  const [error, setError] = useState(null);
  const styles = useThemedStyles();

  useEffect(() => {
    fetchBadges();
  }, [userId]);

  const fetchBadges = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/users/${userId}/badges/`);
      setBadges(response.data.badges || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch badges:', err);
      setError('Failed to load badges');
    } finally {
      setLoading(false);
    }
  };

  const uploadCertificate = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('certificate', file);
      formData.append('skill_name', newBadge.skillName);

      const response = await api.post('/api/badges/upload/', formData);
      setNewBadge(null);
      fetchBadges();
    } catch (err) {
      setError('Failed to upload certificate');
      console.error('Upload error:', err);
    }
  };

  const connectGitHub = async () => {
    try {
      const response = await api.post('/api/badges/connect-github/');
      // Redirect to GitHub OAuth or handle the response
      window.location.href = response.data.auth_url;
    } catch (err) {
      setError('Failed to connect GitHub');
      console.error('GitHub connection error:', err);
    }
  };

  const getBadgeIcon = (badgeType) => {
    const icons = {
      verified: '✓',
      certificate: '📜',
      github: '🐙',
      achievement: '🏆',
      endorsement: '👍',
    };
    return icons[badgeType] || '⭐';
  };

  return (
    <div className={`rounded-lg ${styles.card} border ${styles.border} p-6`}>
      <h2 className="text-2xl font-bold mb-6">Skill Verification Badges</h2>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Badges Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {loading ? (
          // Loading skeleton
          Array(3)
            .fill(0)
            .map((_, i) => (
              <div key={i} className={`p-4 rounded-lg ${styles.background} animate-pulse`}>
                <div className="h-12 w-12 rounded-full bg-gray-300 mb-2"></div>
                <div className="h-4 bg-gray-300 rounded mb-2 w-2/3"></div>
                <div className="h-3 bg-gray-300 rounded w-1/2"></div>
              </div>
            ))
        ) : badges.length === 0 ? (
          <p className="col-span-full text-gray-500 text-center py-8">
            No badges yet. Start building your verified skills!
          </p>
        ) : (
          badges.map((badge) => (
            <div
              key={badge.id}
              className={`p-4 rounded-lg ${styles.background} border-2 border-yellow-400 hover:border-yellow-500 transition`}
            >
              <div className="text-4xl mb-2">{getBadgeIcon(badge.type)}</div>
              <h3 className="font-bold text-lg">{badge.skill_name}</h3>
              <p className="text-sm text-gray-600 mb-2">{badge.type}</p>
              <p className="text-xs text-gray-500">Verified {badge.verified_date || 'recently'}</p>
              
              {badge.certificate_url && (
                <a
                  href={badge.certificate_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-block px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                >
                  View Certificate
                </a>
              )}
            </div>
          ))
        )}
      </div>

      {/* Add Badge Section */}
      <div className={`border-t ${styles.border} pt-6`}>
        <h3 className="font-bold text-lg mb-4">Add Skill Verification</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Certificate Upload */}
          <div className={`p-4 rounded-lg border-2 border-dashed ${styles.border}`}>
            <h4 className="font-semibold mb-2">📜 Upload Certificate</h4>
            <p className="text-sm text-gray-600 mb-3">
              Upload a certificate to verify your skills
            </p>
            <label className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition">
              Choose File
              <input
                type="file"
                accept=".pdf,.jpg,.png"
                onChange={uploadCertificate}
                className="hidden"
              />
            </label>
          </div>

          {/* GitHub Connection */}
          <div className={`p-4 rounded-lg border-2 border-dashed ${styles.border}`}>
            <h4 className="font-semibold mb-2">🐙 Connect GitHub</h4>
            <p className="text-sm text-gray-600 mb-3">
              Link your GitHub to showcase projects
            </p>
            <button
              onClick={connectGitHub}
              className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition"
            >
              Connect Account
            </button>
          </div>

          {/* Endorsement Badge */}
          <div className={`p-4 rounded-lg border-2 border-dashed ${styles.border}`}>
            <h4 className="font-semibold mb-2">👍 Endorsements</h4>
            <p className="text-sm text-gray-600 mb-3">
              Get endorsed by recruiters and peers
            </p>
            <button
              disabled
              className="px-4 py-2 bg-gray-400 text-white rounded-lg cursor-not-allowed opacity-50"
            >
              Coming Soon
            </button>
          </div>

          {/* Achievement Badge */}
          <div className={`p-4 rounded-lg border-2 border-dashed ${styles.border}`}>
            <h4 className="font-semibold mb-2">🏆 Achievements</h4>
            <p className="text-sm text-gray-600 mb-3">
              Earn badges for platform milestones
            </p>
            <button
              disabled
              className="px-4 py-2 bg-gray-400 text-white rounded-lg cursor-not-allowed opacity-50"
            >
              Coming Soon
            </button>
          </div>
        </div>
      </div>

      {/* Badge Statistics */}
      {badges.length > 0 && (
        <div className={`mt-6 p-4 rounded-lg ${styles.background} border ${styles.border}`}>
          <h4 className="font-semibold mb-3">Your Badge Statistics</h4>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{badges.length}</div>
              <p className="text-sm text-gray-600">Total Badges</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {badges.filter(b => b.type === 'verified').length}
              </div>
              <p className="text-sm text-gray-600">Verified</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {badges.filter(b => b.type === 'certificate').length}
              </div>
              <p className="text-sm text-gray-600">Certificates</p>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {badges.filter(b => b.type === 'github').length}
              </div>
              <p className="text-sm text-gray-600">GitHub</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillVerificationBadges;
