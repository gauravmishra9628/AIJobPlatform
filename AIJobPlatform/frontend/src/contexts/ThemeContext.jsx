import React, { createContext, useContext, useEffect, useState } from 'react';
import api from '../api';

// Create Theme Context
const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

// Theme Provider Component
export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState('light');
  const [loading, setLoading] = useState(true);

  // Load theme preference from backend on mount
  useEffect(() => {
    const loadThemePreference = async () => {
      try {
        const response = await api.get('/api/auth/theme/');
        setTheme(response.data.theme_preference || 'light');
      } catch (error) {
        // Fallback to localStorage if API fails
        const savedTheme = localStorage.getItem('theme_preference') || 'light';
        setTheme(savedTheme);
      } finally {
        setLoading(false);
      }
    };

    loadThemePreference();
  }, []);

  // Apply theme to document
  useEffect(() => {
    const htmlElement = document.documentElement;
    
    if (theme === 'dark') {
      htmlElement.classList.add('dark');
      document.body.style.backgroundColor = '#1a1a1a';
      document.body.style.color = '#ffffff';
    } else {
      htmlElement.classList.remove('dark');
      document.body.style.backgroundColor = '#ffffff';
      document.body.style.color = '#1f2937';
    }
    
    localStorage.setItem('theme_preference', theme);
  }, [theme]);

  const toggleTheme = async () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    
    try {
      // Update on backend
      await api.put('/api/auth/theme/', {
        theme_preference: newTheme
      });
      setTheme(newTheme);
    } catch (error) {
      console.error('Failed to update theme:', error);
      // Still update locally if API fails
      setTheme(newTheme);
    }
  };

  const setSystemTheme = async () => {
    try {
      await api.put('/api/auth/theme/', {
        theme_preference: 'system'
      });
      setTheme('system');
    } catch (error) {
      console.error('Failed to set system theme:', error);
    }
  };

  const value = {
    theme,
    setTheme,
    toggleTheme,
    setSystemTheme,
    isDark: theme === 'dark',
    loading
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Custom hook for themed styles
export const useThemedStyles = () => {
  const { isDark } = useTheme();
  
  return {
    background: isDark ? 'bg-gray-900' : 'bg-white',
    text: isDark ? 'text-white' : 'text-gray-900',
    border: isDark ? 'border-gray-700' : 'border-gray-300',
    input: isDark ? 'bg-gray-800 text-white border-gray-700' : 'bg-white text-gray-900 border-gray-300',
    card: isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200',
    hover: isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100',
    shadow: isDark ? 'shadow-lg shadow-black/50' : 'shadow-lg',
  };
};
