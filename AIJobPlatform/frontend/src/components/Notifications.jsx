import { useEffect, useState } from "react";
import { listNotifications, markNotificationRead } from "../api";

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAll, setShowAll] = useState(false);

  const fetchNotifications = async () => {
    try {
      const data = await listNotifications(false);
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const handleMarkRead = async (notificationId) => {
    try {
      await markNotificationRead(notificationId);
      setNotifications(notifications.map(n =>
        n.id === notificationId ? { ...n, is_read: true } : n
      ));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p>Loading notifications...</p>;
  if (error) return <p className="error">{error}</p>;

  const displayNotifications = showAll ? notifications : notifications.slice(0, 5);

  return (
    <div className="notifications card">
      <div className="notifications-header">
        <h2>Notifications {unreadCount > 0 && <span className="badge">{unreadCount}</span>}</h2>
      </div>

      {notifications.length === 0 ? (
        <p>No notifications yet.</p>
      ) : (
        <>
          <div className="notifications-list">
            {displayNotifications.map((notif) => (
              <div 
                key={notif.id} 
                className={`notification-item ${notif.is_read ? "read" : "unread"}`}
              >
                <div className="notification-content">
                  <h4>{notif.title}</h4>
                  <p>{notif.message}</p>
                  <small>{new Date(notif.created_at).toLocaleString()}</small>
                </div>
                {!notif.is_read && (
                  <button 
                    onClick={() => handleMarkRead(notif.id)}
                    className="btn-small"
                  >
                    Mark as Read
                  </button>
                )}
              </div>
            ))}
          </div>

          {!showAll && notifications.length > 5 && (
            <button 
              onClick={() => setShowAll(true)}
              className="btn-secondary"
            >
              Show All ({notifications.length})
            </button>
          )}
        </>
      )}
    </div>
  );
}
