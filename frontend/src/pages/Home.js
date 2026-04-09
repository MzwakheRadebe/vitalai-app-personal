import React, { useState } from 'react';
import { Stethoscope, MessageCircle, Calendar, Upload, Users, Shield, ArrowLeft, LogOut } from 'lucide-react';
import ChatInterface from '../components/ChatInterface';
import Login from '../components/Login';
import Register from '../components/Register';
import './Home.css';

const Home = () => {
  const [currentView, setCurrentView] = useState('welcome');
  const [user, setUser] = useState(null);

  const handleLogin = (userData) => {
    setUser(userData);
    setCurrentView('chat');
  };

  const handleLogout = () => {
    setUser(null);
    setCurrentView('welcome');
  };

  // ── Chat view with navigation bar ──────────────────────────────────────────
  if (currentView === 'chat') {
    const userType = user ? user.userType : 'patient';
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
        {/* Top nav bar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 20px',
          background: '#ffffff',
          borderBottom: '1px solid #e5e7eb',
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
          flexShrink: 0,
        }}>
          <button
            onClick={() => setCurrentView('welcome')}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: 'none', border: 'none', cursor: 'pointer',
              color: '#6b7280', fontSize: '14px', padding: '6px 10px',
              borderRadius: '6px', transition: 'background 0.2s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#f3f4f6'}
            onMouseLeave={e => e.currentTarget.style.background = 'none'}
          >
            <ArrowLeft size={16} /> Back to Home
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, color: '#1f2937' }}>
            <Stethoscope size={20} color="#667eea" />
            VitalAI
          </div>

          {user ? (
            <button
              onClick={handleLogout}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                background: 'none', border: '1px solid #e5e7eb', cursor: 'pointer',
                color: '#6b7280', fontSize: '14px', padding: '6px 12px',
                borderRadius: '6px', transition: 'background 0.2s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = '#f3f4f6'}
              onMouseLeave={e => e.currentTarget.style.background = 'none'}
            >
              <LogOut size={14} /> Sign out
            </button>
          ) : (
            <button
              onClick={() => setCurrentView('login')}
              style={{
                background: '#667eea', color: '#fff', border: 'none',
                padding: '6px 14px', borderRadius: '6px', cursor: 'pointer',
                fontSize: '14px', fontWeight: 500,
              }}
            >
              Sign in
            </button>
          )}
        </div>

        {/* Chat takes the rest of the height */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <ChatInterface userType={userType} />
        </div>
      </div>
    );
  }

  // ── Login view ─────────────────────────────────────────────────────────────
  if (currentView === 'login') {
    return (
      <Login
        onLogin={handleLogin}
        onSwitchToRegister={() => setCurrentView('register')}
        onBack={() => setCurrentView('welcome')}
      />
    );
  }

  // ── Register view ──────────────────────────────────────────────────────────
  if (currentView === 'register') {
    return (
      <Register
        onSwitchToLogin={() => setCurrentView('login')}
        onBack={() => setCurrentView('welcome')}
      />
    );
  }

  // ── Welcome / Landing page ─────────────────────────────────────────────────
  return (
    <div className="home-container">
      {/* Header */}
      <header className="home-header">
        <div className="header-content">
          <div className="logo">
            <Stethoscope size={32} />
            <h1>VitalAI</h1>
          </div>
          <nav className="nav-links">
            <button onClick={() => setCurrentView('login')} className="nav-link">Sign In</button>
            <button onClick={() => setCurrentView('register')} className="nav-link">Sign Up</button>
            <button onClick={() => setCurrentView('chat')} className="nav-link primary">Get Started</button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-text">
            <h1>AI-Powered Healthcare Assistance</h1>
            <p className="hero-subtitle">
              Reducing patient backlogs in South African hospitals through intelligent automation
            </p>
            <p className="hero-description">
              VitalAI helps you schedule appointments, get medical advice, and manage your healthcare
              needs through an intelligent chatbot available 24/7 in multiple languages.
            </p>
            <div className="hero-actions">
              <button onClick={() => setCurrentView('chat')} className="cta-button primary">
                Start Chat with VitalAI
              </button>
              <button onClick={() => setCurrentView('login')} className="cta-button secondary">
                Healthcare Staff Login
              </button>
            </div>
          </div>
          <div className="hero-visual">
            <div className="chat-preview">
              <div className="chat-message bot">
                <div className="message-avatar">V</div>
                <div className="message-content">Hello! I'm VitalAI. How can I help you today?</div>
              </div>
              <div className="chat-message user">
                <div className="message-content">I have a severe headache and fever</div>
                <div className="message-avatar">U</div>
              </div>
              <div className="chat-message bot">
                <div className="message-avatar">V</div>
                <div className="message-content">🟡 MEDIUM severity — please consult a doctor soon.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="container">
          <h2>How VitalAI Helps You</h2>
          <div className="features-grid">
            <div className="feature-card">
              <MessageCircle className="feature-icon" />
              <h3>24/7 Medical Assistance</h3>
              <p>Get instant responses to medical questions anytime, anywhere</p>
            </div>
            <div className="feature-card">
              <Calendar className="feature-icon" />
              <h3>Easy Appointment Scheduling</h3>
              <p>Book hospital appointments quickly without phone calls</p>
            </div>
            <div className="feature-card">
              <Upload className="feature-icon" />
              <h3>Document Management</h3>
              <p>Upload and manage medical documents securely</p>
            </div>
            <div className="feature-card">
              <Users className="feature-icon" />
              <h3>Multilingual Support</h3>
              <p>Available in English, Zulu, Xhosa, Afrikaans, and Sotho</p>
            </div>
            <div className="feature-card">
              <Shield className="feature-icon" />
              <h3>Secure & Private</h3>
              <p>Your medical information is protected and confidential</p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats-section">
        <div className="container">
          <div className="stats-grid">
            <div className="stat"><h3>50%</h3><p>Reduction in Admin Time</p></div>
            <div className="stat"><h3>24/7</h3><p>Availability</p></div>
            <div className="stat"><h3>10+</h3><p>Languages Supported</p></div>
            <div className="stat"><h3>1000+</h3><p>Patients Served</p></div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <h2>Ready to Get Started?</h2>
          <p>Join thousands of patients using VitalAI for better healthcare access</p>
          <button onClick={() => setCurrentView('chat')} className="cta-button large">
            Start Chatting with VitalAI
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="home-footer">
        <div className="container">
          <p>&copy; 2025 VitalAI. AI-powered healthcare assistance for South Africa.</p>
        </div>
      </footer>
    </div>
  );
};

export default Home;
