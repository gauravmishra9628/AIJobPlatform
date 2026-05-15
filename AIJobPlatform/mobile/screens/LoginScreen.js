import React, { useState, useContext } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Alert
} from 'react-native';
import { AuthContext } from '../App';
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useContext(AuthContext);

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(`${API_URL}/auth/login/`, {
        email: email.toLowerCase(),
        password,
      });

      if (response.data.tokens) {
        login(response.data.tokens.access, response.data.user);
      }
    } catch (error) {
      Alert.alert('Login Failed', error.response?.data?.detail || 'Invalid credentials');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.logo}>AI Job</Text>
          <Text style={styles.tagline}>Platform</Text>
        </View>

        <View style={styles.form}>
          <Text style={styles.title}>Welcome Back</Text>
          <Text style={styles.subtitle}>Sign in to continue</Text>

          <TextInput
            style={styles.input}
            placeholder="Email"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            placeholderTextColor="#9CA3AF"
          />

          <TextInput
            style={styles.input}
            placeholder="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            placeholderTextColor="#9CA3AF"
          />

          <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={isLoading}>
            <Text style={styles.buttonText}>{isLoading ? 'Signing in...' : 'Sign In'}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.linkButton}>
            <Text style={styles.linkText}>Forgot Password?</Text>
          </TouchableOpacity>

          <View style={styles.signupContainer}>
            <Text style={styles.signupText}>Don't have an account? </Text>
            <TouchableOpacity>
              <Text style={styles.signupLink}>Sign Up</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  scrollContent: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  header: { alignItems: 'center', marginBottom: 40 },
  logo: { fontSize: 36, fontWeight: 'bold', color: '#3B82F6' },
  tagline: { fontSize: 24, color: '#6B7280' },
  form: { width: '100%' },
  title: { fontSize: 28, fontWeight: 'bold', color: '#1F2937', marginBottom: 8 },
  subtitle: { fontSize: 16, color: '#6B7280', marginBottom: 24 },
  input: {
    backgroundColor: '#F9FAFB', borderRadius: 12, padding: 16, marginBottom: 16,
    fontSize: 16, borderWidth: 1, borderColor: '#E5E7EB'
  },
  button: {
    backgroundColor: '#3B82F6', borderRadius: 12, padding: 16, alignItems: 'center',
    marginTop: 8
  },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  linkButton: { alignItems: 'center', marginTop: 16 },
  linkText: { color: '#3B82F6', fontSize: 14 },
  signupContainer: { flexDirection: 'row', justifyContent: 'center', marginTop: 24 },
  signupText: { color: '#6B7280', fontSize: 14 },
  signupLink: { color: '#3B82F6', fontSize: 14, fontWeight: '600' },
});