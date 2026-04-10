import React, { useState } from 'react';
import { Mail, Lock, Eye, EyeOff, User, Stethoscope } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import './Login.css';

const Login = ({ onLogin, onSwitchToRegister, onBack }) => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    userType: 'patient'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (field, value) => {
    setError('');
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const userData = await login(formData.email, formData.password);
      onLogin(userData);
    } catch (err) {
      if (!err.response) {
        setError('Cannot reach the server. Check your connection or try again shortly — the server may be waking up.');
      } else {
        const msg = err?.response?.data?.detail || 'Invalid email or password. Please try again.';
        setError(msg);
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
          <p>Sign in to your account</p>
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
                placeholder="Enter your password"
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

          <div className="form-options">
            <label className="checkbox-label">
              <input type="checkbox" />
              <span className="checkmark"></span>
              Remember me
            </label>
            <a href="#forgot" className="forgot-link">Forgot password?</a>
          </div>

          {error && (
            <div className="error-message" style={{ color: '#dc2626', marginBottom: '12px', fontSize: '14px' }}>
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            className="login-btn"
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <div className="login-footer">
          <p>
            Don't have an account?{' '}
            <button className="switch-link" onClick={onSwitchToRegister}>
              Sign up
            </button>
          </p>
        </div>

      </div>
    </div>
  );
};

export default Login;