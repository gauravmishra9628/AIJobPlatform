import { useEffect, useState } from "react";
import { sendChatMessage, getChatMessages, getChatList } from "../api";

export default function RealChat() {
  const [chatList, setChatList] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [error, setError] = useState("");

  // Fetch chat list on mount
  useEffect(() => {
    fetchChatList();
    const interval = setInterval(fetchChatList, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchChatList = async () => {
    try {
      const data = await getChatList();
      setChatList(data.conversations || []);
    } catch (err) {
      console.error("Failed to fetch chat list:", err);
    }
  };

  // Fetch messages when user is selected
  useEffect(() => {
    if (selectedUserId) {
      fetchMessages();
      const interval = setInterval(fetchMessages, 3000);
      return () => clearInterval(interval);
    }
  }, [selectedUserId]);

  const fetchMessages = async () => {
    if (!selectedUserId) return;
    setLoadingMessages(true);
    try {
      const data = await getChatMessages(selectedUserId);
      setMessages(data.messages || []);
    } catch (err) {
      console.error("Failed to fetch messages:", err);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedUserId) return;

    setLoading(true);
    setError("");
    try {
      await sendChatMessage(selectedUserId, newMessage);
      setNewMessage("");
      await fetchMessages();
      await fetchChatList();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="real-chat card">
      <h2>💬 Real Chat</h2>

      <div className="chat-container">
        {/* Chat List */}
        <div className="chat-list">
          <h3>Conversations</h3>
          {chatList.length === 0 ? (
            <p className="empty-state">No conversations yet</p>
          ) : (
            <div className="conversations">
              {chatList.map((chat) => (
                <div
                  key={chat.user_id}
                  className={`conversation ${
                    selectedUserId === chat.user_id ? "active" : ""
                  }`}
                  onClick={() => setSelectedUserId(chat.user_id)}
                >
                  <div className="conv-header">
                    <span className="name">{chat.user_name}</span>
                    {chat.unread_count > 0 && (
                      <span className="badge">{chat.unread_count}</span>
                    )}
                  </div>
                  <p className="last-message">{chat.last_message}</p>
                  <span className="timestamp">{chat.timestamp}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="chat-window">
          {!selectedUserId ? (
            <div className="empty-state">
              <p>Select a conversation to start chatting</p>
            </div>
          ) : (
            <>
              <div className="chat-messages">
                {loadingMessages ? (
                  <p>Loading messages...</p>
                ) : messages.length === 0 ? (
                  <p className="empty-state">No messages yet</p>
                ) : (
                  messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`message ${
                        msg.is_sender ? "sent" : "received"
                      }`}
                    >
                      <div className="message-content">{msg.message}</div>
                      <div className="message-footer">
                        <span className="timestamp">{msg.timestamp}</span>
                        {msg.is_sender && msg.read && (
                          <span className="read-status">✓✓</span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>

              <form onSubmit={handleSendMessage} className="chat-input-form">
                {error && <p className="error">{error}</p>}
                <div className="input-group">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type a message..."
                    disabled={loading}
                  />
                  <button type="submit" disabled={loading || !newMessage.trim()}>
                    {loading ? "..." : "Send"}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
