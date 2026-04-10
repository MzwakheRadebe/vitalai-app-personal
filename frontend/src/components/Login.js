import React, { useState, useEffect } from 'react';
import { Mail, Lock, Eye, EyeOff, User, Stethoscope, ChevronDown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { staffAPI } from '../services/api';
import './Login.css';

const Login = ({ onLogin, onSwitchToRegister, onBack }) => {
  const { login, staffLogin } = useAuth();
  const [userType, setUserType] = useState('patient');

  // Patient form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Staff form state
  const [doctors, setDoctors] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState('');
  const [accessCode, setAccessCode] = useState('');
  const [showCode, setShowCode] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load doctor list when staff tab is selected
  useEffect(() => {
    if (userType === 'staff' && doctors.length === 0) {
      staffAPI.getDoctors()
        .then(setDoctors)
        .catch(() => setDoctors([]));
    }
  }, [userType, doctors.length]);

  const handleTabChange = (type) => {
    setError('');
    setUserType(type);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (userType === 'staff') {
        if (!selectedDoctor) {
          setError('Please select your name from the list.');
          setIsLoading(false);
          return;
        }
        const userData = await staffLogin(selectedDoctor, accessCode);
        onLogin(userData);
      } else {
        const userData = await login(email, password);
        onLogin(userData);
      }
    } catch (err) {
      if (!err.response) {
        setError('Cannot reach the server. Check your connection or try again shortly — the server may be waking up.');
      } else {
        const detail = err?.response?.data?.detail;
        setError(typeof detail === 'string' ? detail : 'Sign in failed. Please check your details.');
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

          {/* User type tab selector */}
          <div className="form-group">
            <label>User Type</label>
            <div className="user-type-selector">
              <button
                type="button"
                className={`user-type-btn ${userType === 'patient' ? 'active' : ''}`}
                onClick={() => handleTabChange('patient')}
              >
                <User size={16} /> Patient
              </button>
              <button
                type="button"
                className={`user-type-btn ${userType === 'staff' ? 'active' : ''}`}
                onClick={() => handleTabChange('staff')}
              >
                <Stethoscope size={16} /> Staff
              </button>
            </div>
          </div>

          {/* ── Patient fields ── */}
          {userType === 'patient' && (
            <>
              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <div className="input-wrapper">
                  <Mail size={18} className="input-icon" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={e => { setError(''); setEmail(e.target.value); }}
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
                    value={password}
                    onChange={e => { setError(''); setPassword(e.target.value); }}
                    placeholder="Enter your password"
                    required
                  />
                  <button type="button" className="password-toggle" onClick={() => setShowPassword(v => !v)}>
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
            </>
          )}

          {/* ── Staff fields ── */}
          {userType === 'staff' && (
            <>
              <div className="form-group">
                <label htmlFor="doctor-select">Select Your Name</label>
                <div className="input-wrapper" style={{ position: 'relative' }}>
                  <Stethoscope size={18} className="input-icon" />
                  <select
                    id="doctor-select"
                    value={selectedDoctor}
                    onChange={e => { setError(''); setSelectedDoctor(e.target.value); }}
                    required
                    style={{
                      width: '100%',
                      padding: '0.75rem 2.5rem 0.75rem 2.75rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '0.75rem',
                      fontSize: '0.875rem',
                      background: 'white',
                      appearance: 'none',
                      cursor: 'pointer',
                      minHeight: '44px',
                    }}
                  >
                    <option value="">— Select doctor —</option>
                    {doctors.map(d => (
                      <option key={d.email} value={d.email}>
                        {d.name} · {d.department}
                      </option>
                    ))}
                  </select>
                  <ChevronDown
                    size={16}
                    style={{ position: 'absolute', right: '1rem', color: '#9ca3af', pointerEvents: 'none' }}
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="access-code">Staff Access Code</label>
                <div className="input-wrapper">
                  <Lock size={18} className="input-icon" />
                  <input
                    id="access-code"
                    type={showCode ? 'text' : 'password'}
                    value={accessCode}
                    onChange={e => { setError(''); setAccessCode(e.target.value); }}
                    placeholder="Enter staff access code"
                    required
                  />
                  <button type="button" className="password-toggle" onClick={() => setShowCode(v => !v)}>
                    {showCode ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                <p style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
                  Provided by your admin. &nbsp;
                  <span style={{ color: '#d1d5db' }}>Demo:&nbsp;</span>
                  <code style={{
                    background: '#f3f4f6', padding: '1px 6px', borderRadius: '4px',
                    fontSize: '11px', color: '#6b7280', letterSpacing: '0.05em',
                  }}>
                    STAFF-VITALAI-2024
                  </code>
                </p>
              </div>
            </>
          )}

          {/* Error */}
          {error && (
            <div style={{
              background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '8px',
              padding: '10px 14px', color: '#dc2626', fontSize: '14px',
            }}>
              ⚠️ {error}
            </div>
          )}

          <button type="submit" className="login-btn" disabled={isLoading}>
            {isLoading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <div className="login-footer">
          <p>
            Don't have an account?{' '}
            <button className="switch-link" onClick={onSwitchToRegister}>Sign up</button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
