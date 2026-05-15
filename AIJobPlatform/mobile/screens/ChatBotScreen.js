import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';

const API_URL = 'http://127.0.0.1:8000/api';

const suggestedQuestions = [
  'How do I prepare for a tech interview?',
  'What skills are in demand?',
  'How can I improve my resume?',
  'What career path should I take?',
];

export default function ChatBotScreen() {
  const [messages, setMessages] = useState([
    { id: '1', role: 'assistant', content: "Hi! I'm your AI Career Assistant. Ask me anything about jobs, career paths, or interview tips!" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const flatListRef = useRef();

  useEffect(() => {
    flatListRef.current?.scrollToEnd({ animated: true });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { id: Date.now().toString(), role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const token = await import('expo-secure-store').then(m => m.getItemAsync('authToken'));
      const response = await axios.post(`${API_URL}/jobs/career-coach/`,
        { message: userMessage.content },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response || response.data.answer || "I'm here to help! Try asking differently."
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm having trouble connecting. Please try again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessage = ({ item }) => (
    <View style={[styles.messageContainer, item.role === 'user' && styles.userMessageContainer]}>
      <View style={[styles.messageBubble, item.role === 'user' ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.messageText, item.role === 'user' && styles.userMessageText]}>
          {item.content}
        </Text>
      </View>
    </View>
  );

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.messageList}
        ListFooterComponent={loading ? <Text style={styles.typingText}>AI is typing...</Text> : null}
      />

      {messages.length === 1 && (
        <View style={styles.suggestionsContainer}>
          <Text style={styles.suggestionsTitle}>Try asking:</Text>
          {suggestedQuestions.map((q, i) => (
            <TouchableOpacity key={i} style={styles.suggestionButton} onPress={() => setInput(q)}>
              <Text style={styles.suggestionText}>{q}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="Ask about jobs, careers, interviews..."
          value={input}
          onChangeText={setInput}
          placeholderTextColor="#9CA3AF"
          multiline
        />
        <TouchableOpacity style={[styles.sendButton, !input.trim() && styles.sendButtonDisabled]} onPress={sendMessage} disabled={!input.trim()}>
          <Ionicons name="send" size={20} color="#fff" />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  messageList: { padding: 16 },
  messageContainer: { marginBottom: 12 },
  userMessageContainer: { alignItems: 'flex-end' },
  messageBubble: { maxWidth: '80%', padding: 14, borderRadius: 18 },
  userBubble: { backgroundColor: '#3B82F6', borderBottomRightRadius: 4 },
  assistantBubble: { backgroundColor: '#fff', borderBottomLeftRadius: 4 },
  messageText: { fontSize: 15, color: '#1F2937', lineHeight: 22 },
  userMessageText: { color: '#fff' },
  typingText: { fontSize: 12, color: '#9CA3AF', padding: 8 },
  suggestionsContainer: { padding: 16, borderTopWidth: 1, borderTopColor: '#E5E7EB', backgroundColor: '#fff' },
  suggestionsTitle: { fontSize: 12, color: '#6B7280', marginBottom: 8 },
  suggestionButton: { backgroundColor: '#EEF2FF', padding: 10, borderRadius: 8, marginBottom: 8 },
  suggestionText: { fontSize: 14, color: '#3B82F6' },
  inputContainer: { flexDirection: 'row', padding: 12, backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#E5E7EB', alignItems: 'flex-end' },
  input: { flex: 1, backgroundColor: '#F3F4F6', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, fontSize: 15, maxHeight: 100 },
  sendButton: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#3B82F6', alignItems: 'center', justifyContent: 'center', marginLeft: 8 },
  sendButtonDisabled: { backgroundColor: '#9CA3AF' },
});