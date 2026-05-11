import { useEffect, useState } from "react";
import { bookmarkJob, listBookmarks } from "../api";

export default function JobBookmarks() {
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchBookmarks = async () => {
    try {
      const data = await listBookmarks();
      setBookmarks(data.bookmarks || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookmarks();
  }, []);

  const handleRemoveBookmark = async (jobId) => {
    try {
      await bookmarkJob(jobId, "remove");
      setBookmarks(bookmarks.filter(b => b.job.id !== jobId));
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p>Loading bookmarks...</p>;
  if (error) return <p className="error">{error}</p>;

  return (
    <div className="job-bookmarks card">
      <h2>Saved Jobs ({bookmarks.length})</h2>
      
      {bookmarks.length === 0 ? (
        <p>No bookmarked jobs yet. Start saving jobs you're interested in!</p>
      ) : (
        <div className="bookmarks-list">
          {bookmarks.map((bookmark) => (
            <div key={bookmark.id} className="bookmark-item">
              <div className="job-info">
                <h3>{bookmark.job.title}</h3>
                <p className="company">{bookmark.job.company}</p>
                <p className="location">{bookmark.job.location}</p>
                <p className="type">{bookmark.job.employment_type}</p>
                {bookmark.notes && (
                  <p className="notes"><strong>Notes:</strong> {bookmark.notes}</p>
                )}
              </div>
              <button 
                onClick={() => handleRemoveBookmark(bookmark.job.id)}
                className="btn-secondary"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
