import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Stethoscope, MessageCircle, Calendar, Upload, Users, Shield, ArrowLeft, LogOut, X, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';
import ChatInterface from '../components/ChatInterface';
import Login from '../components/Login';
import Register from '../components/Register';
import { useAuth } from '../contexts/AuthContext';
import { faqAPI } from '../services/api';
import './Home.css';

/* ── FAQ Modal ─────────────────────────────────────────────────────────────── */
const FAQModal = ({ onClose }) => {
  const [faqs, setFaqs] = useState([]);
  const [open, setOpen] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    faqAPI.list()
      .then(data => setFaqs(data))
      .catch(() => setFaqs([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 9999, padding: '20px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#fff', borderRadius: '16px', width: '100%', maxWidth: '600px',
          maxHeight: '80vh', display: 'flex', flexDirection: 'column',
          boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '20px 24px 16px', borderBottom: '1px solid #e5e7eb',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <HelpCircle size={22} color="#667eea" />
            <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#1f2937' }}>
              Frequently Asked Questions
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: '#9ca3af', padding: '4px', borderRadius: '6px',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ overflowY: 'auto', padding: '16px 24px 24px' }}>
          {loading ? (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '24px 0' }}>Loading…</p>
          ) : faqs.length === 0 ? (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '24px 0' }}>No FAQs available yet.</p>
          ) : (
            faqs.map((faq, i) => (
              <div
                key={faq.id || i}
                style={{
                  borderBottom: '1px solid #f3f4f6', paddingBottom: '4px', marginBottom: '4px',
                }}
              >
                <button
                  onClick={() => setOpen(open === i ? null : i)}
                  style={{
                    width: '100%', display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', padding: '14px 0', background: 'none',
                    border: 'none', cursor: 'pointer', textAlign: 'left',
                    color: '#1f2937', fontWeight: open === i ? 600 : 500, fontSize: '15px',
                  }}
                >
                  {faq.question}
                  {open === i
                    ? <ChevronUp size={18} color="#667eea" />
                    : <ChevronDown size={18} color="#9ca3af" />}
                </button>
                {open === i && (
                  <p style={{
                    margin: '0 0 14px', color: '#4b5563', fontSize: '14px',
                    lineHeight: 1.65, paddingLeft: '2px',
                  }}>
                    {faq.answer}
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const Home = () => {
  const [currentView, setCurrentView] = useState('welcome');
  const [showFaq, setShowFaq] = useState(false);
  const navigate = useNavigate();
  const { user: authUser, logout: authLogout } = useAuth();

  // Use authUser (from AuthContext/localStorage) as the source of truth
  const user = authUser;

  const handleLogin = (userData) => {
    // After login, redirect to the right portal based on role
    const role = userData?.role || 'patient';
    if (role === 'admin') {
      navigate('/admin');
    } else if (role === 'staff') {
      navigate('/staff');
    } else {
      // Patient — show chat inline on home
      setCurrentView('chat');
    }
  };

  const handleLogout = () => {
    authLogout();
    setCurrentView('welcome');
  };

  // ── Chat view with navigation bar ──────────────────────────────────────────
  if (currentView === 'chat') {
    const userType = user ? (user.role || user.userType || 'patient') : 'patient';
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
        <div className="footer-main">
          <div className="footer-grid">

            {/* Brand column */}
            <div className="footer-col">
              <div className="footer-logo">
                <Stethoscope size={24} />
                <span>VitalAI</span>
              </div>
              <p className="footer-tagline">
                AI-powered healthcare assistance for South Africa — reducing patient backlogs
                and improving access to care, 24/7.
              </p>
            </div>

            {/* Quick links */}
            <div className="footer-col">
              <h4>Quick Links</h4>
              <ul className="footer-links">
                <li><button onClick={() => setCurrentView('chat')} className="footer-link-btn">Start Chat</button></li>
                <li><button onClick={() => setCurrentView('register')} className="footer-link-btn">Create Account</button></li>
                <li><button onClick={() => setCurrentView('login')} className="footer-link-btn">Staff Login</button></li>
                <li><button onClick={() => setShowFaq(true)} className="footer-link-btn">FAQ</button></li>
              </ul>
            </div>

            {/* Support */}
            <div className="footer-col">
              <h4>Support</h4>
              <ul className="footer-links">
                <li><a href="https://www.health.gov.za" target="_blank" rel="noreferrer" className="footer-link-btn">Dept. of Health SA</a></li>
                <li><a href="https://www.who.int" target="_blank" rel="noreferrer" className="footer-link-btn">World Health Organisation</a></li>
                <li><a href="https://github.com/MzwakheRadebe/vitalai-app-personal" target="_blank" rel="noreferrer" className="footer-link-btn">GitHub Repo</a></li>
              </ul>
            </div>

            {/* Emergency contacts */}
            <div className="footer-col">
              <h4>Emergency Contacts</h4>
              <ul className="footer-links">
                <li><span className="footer-link-btn">🚑 Ambulance: <strong>10177</strong></span></li>
                <li><span className="footer-link-btn">🚔 Police: <strong>10111</strong></span></li>
                <li><span className="footer-link-btn">📞 Emergency: <strong>112</strong></span></li>
              </ul>
            </div>

          </div>
        </div>

        {/* Disclaimer / Terms bar */}
        <div className="footer-disclaimer">
          <div className="container">
            <p className="disclaimer-text">
              ⚠️ <strong>Medical Disclaimer:</strong> VitalAI is an AI-powered triage assistant
              and is <strong>not a substitute for professional medical advice, diagnosis, or treatment.</strong>
              Always consult a qualified healthcare provider for medical concerns.
              In an emergency, call <strong>10177</strong> or <strong>112</strong> immediately.
            </p>
            <div className="footer-legal">
              <span>&copy; {new Date().getFullYear()} VitalAI. All rights reserved.</span>
              <span className="footer-divider">|</span>
              <button className="footer-legal-link" onClick={() => alert('Terms & Conditions: VitalAI provides AI-assisted health guidance for informational purposes only. By using this service you agree that responses do not constitute medical advice and that you will seek professional healthcare when needed.')}>
                Terms &amp; Conditions
              </button>
              <span className="footer-divider">|</span>
              <button className="footer-legal-link" onClick={() => alert('Privacy Policy: VitalAI collects only the information necessary to provide triage guidance. Your health data is not stored or shared with third parties. Compliant with POPIA (Protection of Personal Information Act, South Africa).')}>
                Privacy Policy
              </button>
              <span className="footer-divider">|</span>
              <a href="https://github.com/MzwakheRadebe/vitalai-app-personal" target="_blank" rel="noreferrer" className="footer-legal-link">
                Open Source
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* FAQ Modal — rendered on top of everything */}
      {showFaq && <FAQModal onClose={() => setShowFaq(false)} />}
    </div>
  );
};

export default Home;
