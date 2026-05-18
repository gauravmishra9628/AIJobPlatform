import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getAuthenticatedUser, listNotifications } from "../api";

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

export default function NotificationBadge() {
  const currentUser = useMemo(() => getAuthenticatedUser(), []);
  const userId = currentUser?.id;
  const [unreadCount, setUnreadCount] = useState(0);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!userId) {
      return undefined;
    }

    let mounted = true;
    let refreshTimer = null;
    let socket = null;

    const refresh = async () => {
      try {
        const data = await listNotifications(true);
        if (mounted) {
          setUnreadCount(data.unread_count || 0);
        }
      } catch {
        if (mounted) {
          setConnected(false);
        }
      }
    };

    refresh();
    refreshTimer = window.setInterval(refresh, 45000);

    if (typeof window !== "undefined" && window.WebSocket) {
      try {
        socket = new WebSocket(buildNotificationSocketUrl(userId));
        socket.onopen = () => mounted && setConnected(true);
        socket.onclose = () => mounted && setConnected(false);
        socket.onerror = () => mounted && setConnected(false);
        socket.onmessage = () => {
          if (mounted) {
            refresh();
          }
        };
      } catch {
        setConnected(false);
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
  }, [userId]);

  if (!userId) {
    return null;
  }

  return (
    <Link className={`notificationBadge ${connected ? "live" : "syncing"}`} to="/dashboard" title="Open activity feed">
      <span className="notificationBadgeIcon">Bell</span>
      <span className="notificationBadgeText">Inbox</span>
      <span className="notificationBadgeCount">{unreadCount}</span>
    </Link>
  );
}