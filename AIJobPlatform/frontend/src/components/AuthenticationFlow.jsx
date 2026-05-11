import React, { useState } from 'react';
import { FiMail, FiLock, FiCheckCircle } from 'react-icons/fi';
import api from '../api';
import toast from 'react-hot-toast';

export default function AuthenticationFlow() {
  const [step, setStep] = useState('login'); // login, otp, register, forgot-password, reset-password
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('student');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendOTP = async (e) => {
    e.preventDefault();
    if (!email) {
      toast.error('Please enter email');
      return;
    }
    
    setLoading(true);
    try {
      await api.post('/jobs/auth/send-otp/', { email });
      toast.success('OTP sent to your email');
      setStep('otp');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (!otp || !password) {
      toast.error('Please enter OTP and password');
      return;
    }
    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/jobs/auth/verify-otp/', {
        email,
        otp,
        password,
        role,
      });
      toast.success('Registration successful!');
      localStorage.setItem('user_id', response.data.user_id);
      setStep('login');
    } catch (error) {
      toast.error(error.response?.data?.error || 'OTP verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!email) {
      toast.error('Please enter email');
      return;
    }

    setLoading(true);
    try {
      await api.post('/jobs/auth/forgot-password/', { email });
      toast.success('Password reset link sent to email');
      setStep('reset-password');
    } catch (error) {
      toast.error('Failed to send reset link');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!resetToken || !newPassword) {
      toast.error('Please enter token and new password');
      return;
    }

    setLoading(true);
    try {
      await api.post('/jobs/auth/reset-password/', {
        token: resetToken,
        new_password: newPassword,
      });
      toast.success('Password reset successful!');
      setStep('login');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Password reset failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Register with OTP */}
        {step === 'login' && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-8 text-center">AI Job Portal</h1>
            
            <div className="space-y-4 mb-6">
              <button
                onClick={() => setStep('otp')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition"
              >
                Sign Up with Email OTP
              </button>
              <button
                onClick={() => setStep('forgot-password')}
                className="w-full bg-gray-600 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-lg transition"
              >
                Forgot Password?
              </button>
            </div>

            <p className="text-center text-gray-600 text-sm">
              Login to your existing account using the web form
            </p>
          </div>
        )}

        {/* OTP Registration */}
        {step === 'otp' && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Sign Up with Email</h2>
            
            <form onSubmit={handleSendOTP} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <div className="flex items-center bg-gray-100 rounded-lg px-4 py-3">
                  <FiMail className="text-gray-400 mr-3" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="bg-transparent flex-1 outline-none text-gray-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-gray-100 rounded-lg px-4 py-3 text-gray-800 outline-none"
                >
                  <option value="student">Student</option>
                  <option value="recruiter">Recruiter</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
              >
                {loading ? 'Sending OTP...' : 'Send OTP'}
              </button>
            </form>

            <button
              onClick={() => setStep('login')}
              className="w-full mt-4 text-blue-600 hover:text-blue-700 font-semibold"
            >
              Back to Login
            </button>
          </div>
        )}

        {/* OTP Verification */}
        {step === 'otp' && email && (
          <div className="bg-white rounded-lg shadow-xl p-8 mt-4">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Verify OTP</h2>
            
            <form onSubmit={handleVerifyOTP} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">OTP (6 digits)</label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.slice(0, 6))}
                  placeholder="000000"
                  maxLength="6"
                  className="w-full bg-gray-100 rounded-lg px-4 py-3 text-center text-2xl tracking-widest outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full bg-gray-100 rounded-lg px-4 py-3 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm password"
                  className="w-full bg-gray-100 rounded-lg px-4 py-3 outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
              >
                {loading ? 'Registering...' : 'Complete Registration'}
              </button>
            </form>
          </div>
        )}

        {/* Forgot Password */}
        {step === 'forgot-password' && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Reset Password</h2>
            
            <form onSubmit={handleForgotPassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <div className="flex items-center bg-gray-100 rounded-lg px-4 py-3">
                  <FiMail className="text-gray-400 mr-3" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="bg-transparent flex-1 outline-none text-gray-800"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </form>

            <button
              onClick={() => setStep('login')}
              className="w-full mt-4 text-blue-600 hover:text-blue-700 font-semibold"
            >
              Back to Login
            </button>
          </div>
        )}

        {/* Reset Password with Token */}
        {step === 'reset-password' && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Enter Reset Token</h2>
            
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Reset Token</label>
                <input
                  type="text"
                  value={resetToken}
                  onChange={(e) => setResetToken(e.target.value)}
                  placeholder="Token from email"
                  className="w-full bg-gray-100 rounded-lg px-4 py-3 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">New Password</label>
                <div className="flex items-center bg-gray-100 rounded-lg px-4 py-3">
                  <FiLock className="text-gray-400 mr-3" />
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="New password"
                    className="bg-transparent flex-1 outline-none text-gray-800"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>

            <button
              onClick={() => setStep('login')}
              className="w-full mt-4 text-blue-600 hover:text-blue-700 font-semibold"
            >
              Back to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
