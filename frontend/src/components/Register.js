import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, User, Stethoscope } from 'lucide-react';
import './Login.css';
import { authAPI } from '../services/api';

const Register = ({ onSwitchToLogin, onBack }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    userType: 'patient'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleInputChange = (field, value) => {
    setError('');
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      await authAPI.register(formData.email, formData.password, formData.userType);
      setSuccess(true);
      // Auto-redirect to login after 1.5 seconds
      setTimeout(() => onSwitchToLogin?.(), 1500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      // Pydantic returns detail as array or string
      if (Array.isArray(detail)) {
        setError(detail.map(d => d.msg).join(' · '));
      } else if (typeof detail === 'string') {
        setError(detail);
      } else if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else if (err.response?.status === 409) {
        setError('An account with this email already exists. Please sign in.');
      } else {
        setError('Sign up failed. Please check your details and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {onBack && (
          <button
            onClick={onBack}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: 'none', border: 'none', cursor: 'pointer',
              color: '#6b7280', fontSize: '13px', marginBottom: '12px', padding: 0,
            }}
          >
            ← Back to Home
          </button>
        )}
        <div className="login-header">
          <div className="logo">
            <Stethoscope size={32} />
            <h1>VitalAI</h1>
          </div>
          <p>Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>User Type</label>
            <div className="user-type-selector">
              <button
                type="button"
                className={`user-type-btn ${formData.userType === 'patient' ? 'active' : ''}`}
                onClick={() => handleInputChange('userType', 'patient')}
              >
                <User size={16} />
                Patient
              </button>
              <button
                type="button"
                className={`user-type-btn ${formData.userType === 'staff' ? 'active' : ''}`}
                onClick={() => handleInputChange('userType', 'staff')}
              >
                <Stethoscope size={16} />
                Staff
              </button>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <div className="input-wrapper">
              <Mail size={18} className="input-icon" />
              <input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                placeholder="Enter your email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <Lock size={18} className="input-icon" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                placeholder="Min. 8 characters"
                minLength={8}
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <div className="input-wrapper">
              <Lock size={18} className="input-icon" />
              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                placeholder="Confirm your password"
                required
              />
            </div>
          </div>

          {/* Success message */}
          {success && (
            <div style={{
              background: '#f0fdf4', border: '1px solid #86efac', borderRadius: '8px',
              padding: '12px 14px', marginBottom: '12px', color: '#15803d', fontSize: '14px',
            }}>
              ✅ Account created! Redirecting to sign in…
            </div>
          )}

          {/* Error message */}
          {error && (
            <div style={{
              background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '8px',
              padding: '12px 14px', marginBottom: '12px', color: '#dc2626', fontSize: '14px',
            }}>
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            className="login-btn"
            disabled={isLoading || success}
          >
            {isLoading ? 'Creating account…' : 'Sign up'}
          </button>
        </form>

        <div className="login-footer">
          <p>
            Already have an account?{' '}
            <button className="switch-link" onClick={onSwitchToLogin}>
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
