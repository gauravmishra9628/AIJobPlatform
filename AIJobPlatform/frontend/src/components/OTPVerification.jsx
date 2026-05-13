import React, { useState, useRef, useEffect } from 'react';
import { useThemedStyles } from '../contexts/ThemeContext';
import api from '../api';

const OTPVerification = ({ email, onSuccess, onError }) => {
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes
  const inputRefs = useRef([]);
  const styles = useThemedStyles();

  // Countdown timer
  useEffect(() => {
    if (timeLeft <= 0) return;
    
    const timer = setInterval(() => {
      setTimeLeft(prev => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  const handleInputChange = (index, value) => {
    if (!/^[0-9]?$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Move to next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleVerify = async () => {
    const otpValue = otp.join('');
    
    if (otpValue.length !== 6) {
      if (onError) {
        onError('Please enter all 6 digits');
      }
      return;
    }

    try {
      setLoading(true);
      const response = await api.post('/api/auth/otp/verify/', {
        otp: otpValue,
        email: email
      });

      if (onSuccess) {
        onSuccess(response.data);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'OTP verification failed';
      if (onError) {
        onError(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    try {
      setResending(true);
      await api.post('/api/auth/otp/send/', {
        email: email
      });
      
      setOtp(['', '', '', '', '', '']);
      setTimeLeft(300);
      inputRefs.current[0]?.focus();
      
      if (onSuccess) {
        onSuccess({ detail: 'OTP resent successfully' });
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to resend OTP';
      if (onError) {
        onError(errorMsg);
      }
    } finally {
      setResending(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`rounded-lg ${styles.card} border ${styles.border} p-8 max-w-md mx-auto`}>
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold mb-2">Verify Your Email</h2>
        <p className={`text-sm ${styles.isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Enter the 6-digit code sent to <br />
          <span className="font-semibold">{email}</span>
        </p>
      </div>

      {/* OTP Inputs */}
      <div className="flex justify-center gap-2 mb-8">
        {otp.map((digit, index) => (
          <input
            key={index}
            ref={(ref) => (inputRefs.current[index] = ref)}
            type="text"
            maxLength="1"
            value={digit}
            onChange={(e) => handleInputChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            className={`w-12 h-12 text-center text-2xl font-bold rounded-lg border-2 transition
              ${digit ? 'border-blue-600' : `${styles.border}`}
              ${styles.isDark ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'}
              focus:outline-none focus:border-blue-600
            `}
            disabled={loading}
          />
        ))}
      </div>

      {/* Timer */}
      <div className="text-center mb-6">
        {timeLeft > 0 ? (
          <p className={`text-sm ${timeLeft < 60 ? 'text-red-600 font-bold' : ''}`}>
            Code expires in: <span className="font-mono">{formatTime(timeLeft)}</span>
          </p>
        ) : (
          <p className="text-sm text-red-600 font-bold">Code has expired</p>
        )}
      </div>

      {/* Verify Button */}
      <button
        onClick={handleVerify}
        disabled={loading || otp.join('').length !== 6}
        className={`w-full py-3 rounded-lg font-semibold transition mb-4
          ${loading || otp.join('').length !== 6
            ? 'opacity-50 cursor-not-allowed'
            : 'hover:shadow-lg'
          }
          ${styles.isDark
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-blue-600 text-white hover:bg-blue-700'
          }
        `}
      >
        {loading ? 'Verifying...' : 'Verify Code'}
      </button>

      {/* Resend Button */}
      <button
        onClick={handleResend}
        disabled={resending || timeLeft > 0}
        className={`w-full py-2 rounded-lg font-semibold transition border
          ${resending || timeLeft > 0
            ? 'opacity-50 cursor-not-allowed'
            : ''
          }
          ${styles.isDark
            ? 'border-blue-600 text-blue-600 hover:bg-blue-600/10'
            : 'border-blue-600 text-blue-600 hover:bg-blue-50'
          }
        `}
      >
        {resending ? 'Sending...' : timeLeft > 0 ? 'Resend Code' : 'Resend Now'}
      </button>

      {/* Info Text */}
      <p className={`text-xs text-center mt-4 ${styles.isDark ? 'text-gray-500' : 'text-gray-600'}`}>
        Didn't receive the code? Check your spam folder or request a new code.
      </p>
    </div>
  );
};

export default OTPVerification;
