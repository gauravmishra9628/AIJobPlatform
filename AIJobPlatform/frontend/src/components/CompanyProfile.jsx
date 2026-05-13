import React, { useState, useEffect } from 'react';
import { useThemedStyles } from '../contexts/ThemeContext';
import api, { submitCompanyReview } from '../api';

const CompanyProfile = ({ companyId }) => {
  const [company, setCompany] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewForm, setReviewForm] = useState({ rating: 5, title: '', body: '', is_anonymous: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submittingReview, setSubmittingReview] = useState(false);
  const styles = useThemedStyles();

  useEffect(() => {
    fetchCompanyProfile();
  }, [companyId]);

  const fetchCompanyProfile = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/companies/${companyId}/`);
      setCompany(response.data.company || null);
      setReviews(response.data.reviews || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load company profile');
      console.error('Company profile error:', err);
    } finally {
      setLoading(false);
    }
  };

  const submitReview = async (event) => {
    event.preventDefault();
    try {
      setSubmittingReview(true);
      const response = await submitCompanyReview(companyId, reviewForm);
      setCompany(response.company || company);
      setReviews((currentReviews) => [response.review, ...currentReviews].filter(Boolean));
      setReviewForm({ rating: 5, title: '', body: '', is_anonymous: false });
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit review');
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return (
      <div className={`p-6 rounded-lg ${styles.card} border ${styles.border}`}>
        <div className="animate-pulse space-y-4">
          <div className={`h-32 ${styles.background} rounded`}></div>
          <div className={`h-4 ${styles.background} rounded w-3/4`}></div>
          <div className={`h-4 ${styles.background} rounded w-1/2`}></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-4 rounded-lg border border-red-500 bg-red-50 text-red-700`}>
        <p className="font-semibold">Error</p>
        <p>{error}</p>
      </div>
    );
  }

  if (!company) {
    return null;
  }

  return (
    <div className={`rounded-lg ${styles.card} border ${styles.border} overflow-hidden`}>
      {/* Header with Logo */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-32 relative">
        {company.logo && (
          <img
            src={company.logo}
            alt={company.name}
            className="absolute -bottom-8 left-6 w-24 h-24 rounded-full border-4 border-white"
          />
        )}
      </div>

      {/* Content */}
      <div className="pt-12 px-6 pb-6">
        {/* Company Name */}
        <h1 className="text-3xl font-bold mb-2">{company.name}</h1>

        {/* Basic Info */}
        <div className="grid grid-cols-2 gap-4 mb-6 pb-6 border-b border-gray-200">
          <div>
            <p className="text-sm text-gray-500">Industry</p>
            <p className="font-semibold">{company.industry || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Employee Count</p>
            <p className="font-semibold">{company.employee_count || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Founded</p>
            <p className="font-semibold">{company.founded_year || 'N/A'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Headquarters</p>
            <p className="font-semibold">{company.location || 'N/A'}</p>
          </div>
        </div>

        {/* Description */}
        {company.description && (
          <div className="mb-6">
            <h3 className="font-semibold text-lg mb-2">About</h3>
            <p className="text-gray-600 leading-relaxed">{company.description}</p>
          </div>
        )}

        {/* Hiring Status */}
        <div className="mb-6">
          <h3 className="font-semibold text-lg mb-3">Hiring Status</h3>
          <div className="flex gap-4">
            <div className="flex-1">
              <p className="text-sm text-gray-500">Active Positions</p>
              <p className="text-2xl font-bold text-green-600">
                {company.active_positions || 0}
              </p>
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-500">Hiring Urgency</p>
              <p className={`text-lg font-semibold ${
                company.hiring_urgency === 'high' ? 'text-red-600' :
                company.hiring_urgency === 'medium' ? 'text-yellow-600' :
                'text-green-600'
              }`}>
                {company.hiring_urgency ? company.hiring_urgency.toUpperCase() : 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Reputation */}
        <div className="mb-6">
          <h3 className="font-semibold text-lg mb-2">Company Rating</h3>
          <div className="flex items-center gap-3">
            <span className="text-3xl font-bold text-amber-600">{Number(company.average_rating || 0).toFixed(1)}</span>
            <span className="text-sm text-gray-500">from {company.review_count || reviews.length || 0} reviews</span>
            {company.badge_label && (
              <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-800 text-xs font-semibold">
                {company.badge_label}
              </span>
            )}
          </div>
          {company.verified_recruiter && (
            <p className="mt-2 text-sm text-green-700 font-medium">
              Verified recruiter: {company.verified_recruiter_name || company.verified_recruiter_email || company.recruiter}
            </p>
          )}
        </div>

        {/* Reviews */}
        <div className="mb-6">
          <h3 className="font-semibold text-lg mb-3">Recent Reviews</h3>
          <div className="space-y-3">
            {reviews.length === 0 ? (
              <p className="text-sm text-gray-500">No reviews yet. Be the first to review this company.</p>
            ) : (
              reviews.slice(0, 5).map((review) => (
                <div key={review.id} className={`p-4 rounded-lg ${styles.background} border ${styles.border}`}>
                  <div className="flex items-center justify-between gap-4 mb-2">
                    <strong>{review.title}</strong>
                    <span className="text-sm text-amber-600">{review.rating}/5</span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{review.body}</p>
                  <p className="text-xs text-gray-500">{review.reviewer} · {review.is_verified_employee ? 'Verified employee' : 'Public review'}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Review form */}
        <form onSubmit={submitReview} className={`mb-6 p-4 rounded-lg ${styles.background} border ${styles.border}`}>
          <h3 className="font-semibold text-lg mb-3">Write a Review</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <label className="field">
              <span>Rating</span>
              <select value={reviewForm.rating} onChange={(event) => setReviewForm({ ...reviewForm, rating: Number(event.target.value) })}>
                {[5, 4, 3, 2, 1].map((score) => <option key={score} value={score}>{score}</option>)}
              </select>
            </label>
            <label className="field">
              <span>Title</span>
              <input value={reviewForm.title} onChange={(event) => setReviewForm({ ...reviewForm, title: event.target.value })} placeholder="Short summary" />
            </label>
          </div>
          <label className="field mb-4">
            <span>Review</span>
            <textarea value={reviewForm.body} onChange={(event) => setReviewForm({ ...reviewForm, body: event.target.value })} placeholder="Share your experience with hiring, growth, and work culture." />
          </label>
          <label className="inline-flex items-center gap-2 mb-4 text-sm text-gray-600">
            <input type="checkbox" checked={reviewForm.is_anonymous} onChange={(event) => setReviewForm({ ...reviewForm, is_anonymous: event.target.checked })} />
            Post anonymously
          </label>
          <button type="submit" disabled={submittingReview} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            {submittingReview ? 'Submitting...' : 'Submit review'}
          </button>
        </form>

        {/* Links */}
        <div className="flex gap-4 flex-wrap">
          {company.website && (
            <a
              href={company.website}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Visit Website
            </a>
          )}
          {company.linkedin_url && (
            <a
              href={company.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-800 text-white rounded-lg hover:bg-blue-900 transition"
            >
              LinkedIn
            </a>
          )}
          {company.twitter_url && (
            <a
              href={company.twitter_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition"
            >
              Twitter
            </a>
          )}
        </div>

        {/* Recruiter Info */}
        {company.recruiter && (
          <div className={`mt-6 p-4 rounded-lg ${styles.background} border ${styles.border}`}>
            <h4 className="font-semibold mb-2">Primary Recruiter</h4>
            <p className="text-sm">{company.recruiter}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompanyProfile;
