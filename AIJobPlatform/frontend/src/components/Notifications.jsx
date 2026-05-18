import { useEffect, useMemo, useState } from "react";
import { getAuthenticatedUser, listNotifications, markNotificationRead } from "../api";

const NOTIFICATION_LABELS = {
  application: "Application",
  interview: "Interview",
  message: "Message",
  job_match: "Job match",
  profile_update: "Profile update",
  skill_rec: "Skill gap",
};

function buildNotificationSocketUrl(userId) {
  const configured = import.meta.env.VITE_NOTIFICATION_WS_URL;
  if (configured) {
    return configured.includes("{userId}") ? configured.replace("{userId}", String(userId)) : configured;
  }

  if (typeof window === "undefined") {
    return "";
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws/notifications/${userId}/`;
}

function formatDateTime(value) {
  if (!value) {
    return "Just now";
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Just now" : date.toLocaleString();
}

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [connectionState, setConnectionState] = useState("syncing");
  const currentUser = useMemo(() => getAuthenticatedUser(), []);
  const userId = currentUser?.id;

  useEffect(() => {
    let mounted = true;
    let refreshTimer = null;
    let socket = null;

    const fetchNotifications = async () => {
      try {
        const data = await listNotifications(showUnreadOnly);
        if (!mounted) {
          return;
        }
        setNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
        setError("");
      } catch (err) {
        if (mounted) {
          setError(err.message || "Failed to load notifications");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchNotifications();
    refreshTimer = window.setInterval(fetchNotifications, 30000);

    if (userId && typeof window !== "undefined" && window.WebSocket) {
      try {
        socket = new WebSocket(buildNotificationSocketUrl(userId));
        socket.onopen = () => mounted && setConnectionState("live");
        socket.onclose = () => mounted && setConnectionState("syncing");
        socket.onerror = () => mounted && setConnectionState("syncing");
        socket.onmessage = () => {
          if (mounted) {
            fetchNotifications();
          }
        };
      } catch {
        setConnectionState("syncing");
      }
    }

    return () => {
      mounted = false;
      if (refreshTimer) {
        window.clearInterval(refreshTimer);
      }
      if (socket) {
        socket.close();
      }
    };
  }, [showUnreadOnly, userId]);

  const handleMarkRead = async (notificationId) => {
    const previousUnread = unreadCount;
    setNotifications((current) => current.map((notification) => (
      notification.id === notificationId ? { ...notification, is_read: true } : notification
    )));
    setUnreadCount((current) => Math.max(0, current - 1));

    try {
      await markNotificationRead(notificationId);
    } catch (err) {
      setError(err.message || "Failed to mark notification as read");
      setUnreadCount(previousUnread);
      setNotifications((current) => current.map((notification) => (
        notification.id === notificationId ? { ...notification, is_read: false } : notification
      )));
    }
  };

  const handleMarkAllRead = async () => {
    const unreadItems = notifications.filter((notification) => !notification.is_read);
    if (!unreadItems.length) {
      return;
    }

    await Promise.all(unreadItems.map((notification) => markNotificationRead(notification.id)));
    setNotifications((current) => current.map((notification) => ({ ...notification, is_read: true })));
    setUnreadCount(0);
  };

  const displayNotifications = showUnreadOnly ? notifications.filter((notification) => !notification.is_read) : notifications;

  return (
    <section className="notificationPanel panel">
      <div className="sectionHeader inline">
        <div>
          <p className="eyebrow">Realtime activity</p>
          <h2>
            Notifications
            {unreadCount > 0 ? <span className="badge">{unreadCount}</span> : null}
          </h2>
        </div>
        <div className="notificationActions">
          <span className={`syncPill ${connectionState === "live" ? "live" : "syncing"}`}>
            {connectionState === "live" ? "Live" : "Syncing"}
          </span>
          <button className="ghostButton fitButton" type="button" onClick={() => setShowUnreadOnly((value) => !value)}>
            {showUnreadOnly ? "Show all" : "Unread only"}
          </button>
          <button className="ghostButton fitButton" type="button" onClick={handleMarkAllRead} disabled={!unreadCount}>
            Mark all read
          </button>
        </div>
      </div>

      {loading ? (
        <div className="notificationSkeletonStack" aria-label="Loading notifications">
          <div className="notificationSkeleton" />
          <div className="notificationSkeleton short" />
          <div className="notificationSkeleton" />
        </div>
      ) : error ? (
        <p className="status errorText">{error}</p>
      ) : displayNotifications.length === 0 ? (
        <div className="emptyPanel subtle">
          <strong>No notifications yet</strong>
          <p>When a recruiter shortlists, schedules, or messages you, updates will appear here instantly.</p>
        </div>
      ) : (
        <div className="notificationsList">
          {displayNotifications.slice(0, 6).map((notification) => (
            <article key={notification.id} className={`notificationItem ${notification.is_read ? "read" : "unread"}`}>
              <div className="notificationCopy">
                <span className="notificationTag">{NOTIFICATION_LABELS[notification.type] || notification.type}</span>
                <h3>{notification.title}</h3>
                <p>{notification.message}</p>
                <small>{formatDateTime(notification.created_at)}</small>
              </div>
              {!notification.is_read ? (
                <button className="ghostButton fitButton" type="button" onClick={() => handleMarkRead(notification.id)}>
                  Mark read
                </button>
              ) : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
