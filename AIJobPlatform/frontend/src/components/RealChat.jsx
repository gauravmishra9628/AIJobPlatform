import { useEffect, useMemo, useRef, useState } from "react";
import { getAuthenticatedUser, getChatList, getChatMessages, sendChatMessage } from "../api";

function buildChatRoomName(currentUserId, otherUserId) {
  const pair = [currentUserId, otherUserId].map(String).sort();
  return `chat_${pair[0]}_${pair[1]}`;
}

function toChatSocketUrl(roomName) {
  const configured = import.meta.env.VITE_CHAT_WS_URL;
  if (configured) {
    return configured.includes("{roomName}") ? configured.replace("{roomName}", roomName) : configured;
  }

  if (typeof window === "undefined") {
    return "";
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws/chat/${roomName}/`;
}

function formatTime(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function RealChat() {
  const currentUser = useMemo(() => getAuthenticatedUser(), []);
  const currentUserId = currentUser?.id;
  const [chatList, setChatList] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [error, setError] = useState("");
  const [connectionState, setConnectionState] = useState("syncing");
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);

  const selectedConversation = chatList.find((conversation) => String(conversation.id) === String(selectedUserId));
  const liveTyping = Boolean(newMessage.trim());

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchChatList = async () => {
    try {
      const data = await getChatList();
      setChatList(data.conversations || []);
      if (!selectedUserId && data.conversations?.length) {
        setSelectedUserId(String(data.conversations[0].id));
      }
      setError("");
    } catch (err) {
      setError(err.message || "Failed to load conversations");
    } finally {
      setLoadingConversations(false);
    }
  };

  const fetchMessages = async (userId = selectedUserId) => {
    if (!userId) {
      return;
    }

    setLoadingMessages(true);
    try {
      const data = await getChatMessages(userId);
      setMessages(data.messages || []);
      setError("");
      scrollToBottom();
    } catch (err) {
      setError(err.message || "Failed to load messages");
    } finally {
      setLoadingMessages(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    let refreshTimer = null;

    const loadConversations = async () => {
      if (!mounted) {
        return;
      }
      await fetchChatList();
    };

    loadConversations();
    refreshTimer = window.setInterval(loadConversations, 12000);

    return () => {
      mounted = false;
      if (refreshTimer) {
        window.clearInterval(refreshTimer);
      }
    };
  }, []);

  useEffect(() => {
    if (!selectedUserId) {
      return undefined;
    }

    fetchMessages(selectedUserId);

    const roomName = buildChatRoomName(currentUserId, selectedUserId);
    let socket = null;

    if (currentUserId && typeof window !== "undefined" && window.WebSocket) {
      try {
        socket = new WebSocket(toChatSocketUrl(roomName));
        socketRef.current = socket;
        socket.onopen = () => setConnectionState("live");
        socket.onerror = () => setConnectionState("syncing");
        socket.onclose = () => setConnectionState("syncing");
        socket.onmessage = () => {
          fetchMessages(selectedUserId);
          fetchChatList();
        };
      } catch {
        setConnectionState("syncing");
      }
    }

    const pollingTimer = window.setInterval(() => {
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        fetchMessages(selectedUserId);
      }
    }, 8000);

    return () => {
      if (pollingTimer) {
        window.clearInterval(pollingTimer);
      }
      if (socket) {
        socket.close();
      }
      socketRef.current = null;
    };
  }, [selectedUserId, currentUserId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (event) => {
    event.preventDefault();
    if (!newMessage.trim() || !selectedUserId) {
      return;
    }

    const payload = {
      sender_id: currentUserId,
      recipient_id: selectedUserId,
      message: newMessage.trim(),
    };

    setSending(true);
    setError("");

    try {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify(payload));
      } else {
        await sendChatMessage(selectedUserId, newMessage.trim());
      }

      setNewMessage("");
      await fetchMessages(selectedUserId);
      await fetchChatList();
    } catch (err) {
      setError(err.message || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  return (
    <section className="real-chat panel">
      <div className="sectionHeader inline">
        <div>
          <p className="eyebrow">Realtime communication</p>
          <h2>Recruiter and student chat</h2>
        </div>
        <span className={`syncPill ${connectionState === "live" ? "live" : "syncing"}`}>
          {connectionState === "live" ? "Live" : "Polling"}
        </span>
      </div>

      <div className="chatContainer">
        <aside className="chatListPanel">
          <div className="chatPanelHeader">
            <h3>Conversations</h3>
            <span className="chip">{chatList.length}</span>
          </div>

          {loadingConversations ? (
            <div className="chatSkeletonStack" aria-label="Loading conversations">
              <div className="chatSkeleton" />
              <div className="chatSkeleton short" />
              <div className="chatSkeleton" />
            </div>
          ) : chatList.length === 0 ? (
            <div className="emptyPanel subtle">
              <strong>No conversations yet</strong>
              <p>Once a recruiter and student exchange a message, the thread will appear here.</p>
            </div>
          ) : (
            <div className="conversationList">
              {chatList.map((conversation) => (
                <button
                  key={conversation.id}
                  type="button"
                  className={`conversationItem ${String(selectedUserId) === String(conversation.id) ? "active" : ""}`}
                  onClick={() => setSelectedUserId(String(conversation.id))}
                >
                  <div className="conversationAvatar">
                    {String(conversation.display_name || conversation.email || "AI").slice(0, 2).toUpperCase()}
                  </div>
                  <div className="conversationMeta">
                    <div className="conversationTitleRow">
                      <strong>{conversation.display_name || conversation.email}</strong>
                      <span className={`presenceDot ${conversation.is_online ? "online" : "offline"}`}>
                        {conversation.is_online ? "Online" : "Offline"}
                      </span>
                    </div>
                    <p>{conversation.last_message || "Start the conversation."}</p>
                    <small>{conversation.role || "member"}</small>
                  </div>
                  {conversation.unread_count > 0 ? <span className="badge">{conversation.unread_count}</span> : null}
                </button>
              ))}
            </div>
          )}
        </aside>

        <article className="chatWindowPanel">
          {!selectedConversation ? (
            <div className="emptyPanel subtle chatPrompt">
              <strong>Select a conversation</strong>
              <p>Open a recruiter-student thread to review messages, send a reply, and watch the unread badge update live.</p>
            </div>
          ) : (
            <>
              <div className="chatWindowHeader">
                <div>
                  <h3>{selectedConversation.display_name || selectedConversation.email}</h3>
                  <p>
                    {selectedConversation.role || "member"}
                    {selectedConversation.last_active_at ? ` · last active ${formatTime(selectedConversation.last_active_at)}` : " · ready to chat"}
                  </p>
                </div>
                <div className="chatHeaderActions">
                  <span className={`presenceDot ${selectedConversation.is_online ? "online" : "offline"}`}>
                    {selectedConversation.is_online ? "Online now" : "Away"}
                  </span>
                  <span className="syncPill">{loadingMessages ? "Syncing" : "Synced"}</span>
                </div>
              </div>

              <div className="chatMessages">
                {loadingMessages ? (
                  <div className="chatSkeletonStack">
                    <div className="chatMessageSkeleton" />
                    <div className="chatMessageSkeleton right" />
                    <div className="chatMessageSkeleton" />
                  </div>
                ) : messages.length === 0 ? (
                  <div className="emptyPanel subtle chatPrompt">
                    <strong>No messages yet</strong>
                    <p>Send the first note to start the interview or hiring conversation.</p>
                  </div>
                ) : (
                  messages.map((message) => {
                    const isOwnMessage = String(message.sender_id) === String(currentUserId);
                    return (
                      <article key={message.id} className={`messageBubble ${isOwnMessage ? "sent" : "received"}`}>
                        <p>{message.message}</p>
                        <small>
                          {message.sender_email || "You"} · {formatTime(message.created_at)} {isOwnMessage && message.is_read ? "· Read" : ""}
                        </small>
                      </article>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              <form onSubmit={handleSendMessage} className="chatComposer">
                {error ? <p className="status errorText">{error}</p> : null}
                {liveTyping ? <p className="typingIndicator">You are typing a reply...</p> : null}
                <div className="chatComposerRow">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(event) => setNewMessage(event.target.value)}
                    placeholder="Write a message to the candidate or recruiter..."
                    disabled={sending}
                  />
                  <button type="submit" disabled={sending || !newMessage.trim()}>
                    {sending ? "Sending" : "Send"}
                  </button>
                </div>
              </form>
            </>
          )}
        </article>
      </div>
    </section>
  );
}
