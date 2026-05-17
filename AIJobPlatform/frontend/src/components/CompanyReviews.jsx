import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Star, Building, ThumbsUp, Search, Plus, Check } from 'lucide-react';

export default function CompanyReviews() {
  const [view, setView] = useState('list');
  const [searchQuery, setSearchQuery] = useState('');
  const [companyData, setCompanyData] = useState(null);
  const [loading, setLoading] = useState(false);

  const searchCompany = async () => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const response = await fetch(`/api/jobs/reviews/company/?company=${encodeURIComponent(searchQuery)}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (response.ok) {
        const data = await response.json();
        setCompanyData(data);
      }
    } catch (error) {
      console.error('Failed to fetch reviews:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderStars = (rating, size = 'md') => {
    const sizeClass = size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4';
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star key={star} className={`${sizeClass} ${star <= rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`} />
        ))}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-3xl shadow-lg overflow-hidden">
        <div className="bg-gradient-to-r from-emerald-600 to-teal-600 p-6 text-white">
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <Building className="w-7 h-7" />
            Company Reviews
          </h2>
          <p className="text-emerald-100 mt-1">Read and write reviews about companies</p>
        </div>

        <div className="p-6 space-y-6">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchCompany()}
                placeholder="Search for a company..."
                className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <button onClick={searchCompany} disabled={loading} className="px-6 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 disabled:opacity-50">
              Search
            </button>
          </div>

          {companyData && (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-800">{companyData.summary.company_name}</h3>
                    <p className="text-gray-500">{companyData.summary.total_reviews} reviews</p>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl font-bold text-emerald-600">{companyData.summary.average_rating}</div>
                    {renderStars(Math.round(companyData.summary.average_rating))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}