import React from 'react';
import { useTheme, useThemedStyles } from '../contexts/ThemeContext';

const EnhancedThemeToggle = () => {
  const { theme, toggleTheme, setSystemTheme, isDark } = useTheme();
  const styles = useThemedStyles();

  return (
    <div className={`flex items-center gap-2 p-3 rounded-lg ${styles.card} border ${styles.border}`}>
      {/* Sun Icon */}
      <button
        onClick={() => setSystemTheme()}
        className={`p-2 rounded-lg transition-colors ${
          theme !== 'dark' 
            ? `bg-yellow-400 text-white` 
            : `${styles.hover} text-gray-400`
        }`}
        title="Light Mode"
      >
        ☀️
      </button>

      {/* Toggle Switch */}
      <button
        onClick={toggleTheme}
        className={`relative w-14 h-8 rounded-full transition-colors ${
          isDark ? 'bg-blue-600' : 'bg-gray-300'
        }`}
      >
        <span
          className={`absolute top-1 left-1 w-6 h-6 bg-white rounded-full transition-transform ${
            isDark ? 'translate-x-6' : 'translate-x-0'
          }`}
        />
      </button>

      {/* Moon Icon */}
      <button
        onClick={() => setSystemTheme()}
        className={`p-2 rounded-lg transition-colors ${
          theme === 'dark'
            ? `bg-indigo-600 text-white`
            : `${styles.hover} text-gray-400`
        }`}
        title="Dark Mode"
      >
        🌙
      </button>

      {/* Current Theme Label */}
      <span className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
        {theme.charAt(0).toUpperCase() + theme.slice(1)} Mode
      </span>
    </div>
  );
};

export default EnhancedThemeToggle;
