import React, { useState } from 'react';
import { useThemedStyles } from '../contexts/ThemeContext';
import api from '../api';

const GoogleOAuthButton = ({ onSuccess, onError, role = 'student' }) => {
  const [loading, setLoading] = useState(false);
  const styles = useThemedStyles();

  const handleGoogleLogin = async (credentialResponse) => {
    try {
      setLoading(true);
      
      // Send token to backend
      const response = await api.post('/api/auth/oauth/google/', {
        id_token: credentialResponse.credential,
        role: role
      });

      // Store tokens
      const { tokens, user } = response.data;
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      localStorage.setItem('user', JSON.stringify(user));

      // Call success callback
      if (onSuccess) {
        onSuccess(response.data);
      }

    } catch (error) {
      console.error('Google OAuth error:', error);
      const errorMsg = error.response?.data?.detail || 'Google authentication failed';
      if (onError) {
        onError(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      {/* Note: This requires Google Sign-In SDK to be loaded in index.html */}
      {/* Add this to public/index.html: <script src="https://accounts.google.com/gsi/client" async defer></script> */}
      
      <div 
        id="g_id_onload"
        data-client_id={process.env.REACT_APP_GOOGLE_CLIENT_ID}
        data-callback="handleCredentialResponse"
      ></div>
      <div id="g_id_signin" data-type="standard"></div>

      {/* Alternative button if SDK not loaded */}
      <button
        onClick={() => alert('Google Sign-In SDK not configured. Please check setup.')}
        disabled={loading}
        className={`w-full px-4 py-2 rounded-lg font-semibold transition flex items-center justify-center gap-2
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
          ${styles.isDark ? 'bg-white text-gray-900 hover:bg-gray-100' : 'bg-white text-gray-900 hover:bg-gray-50 border border-gray-300'}
        `}
      >
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Sign up with Google
      </button>
    </div>
  );
};

export default GoogleOAuthButton;
