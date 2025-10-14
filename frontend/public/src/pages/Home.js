import React, { useState } from 'react';
import { Stethoscope, MessageCircle, Calendar, Upload, Users, Shield } from 'lucide-react';
import ChatInterface from '../components/ChatInterface';
import Login from '../components/Login';
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

  // Render different views based on state
  if (currentView === 'chat') {
    // Fix: Check if user exists before accessing userType
    const userType = user ? user.userType : 'patient';
    return <ChatInterface userType={userType} />;
  }

  if (currentView === 'login') {
    return <Login onLogin={handleLogin} onSwitchToRegister={() => setCurrentView('welcome')} />;
  }

  // Welcome/Landing Page
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
            <button onClick={() => setCurrentView('login')} className="nav-link">Staff Login</button>
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
              <button 
                onClick={() => setCurrentView('chat')}
                className="cta-button primary"
              >
                Start Chat with VitalAI
              </button>
              <button 
                onClick={() => setCurrentView('login')}
                className="cta-button secondary"
              >
                Healthcare Staff Login
              </button>
            </div>
          </div>
          <div className="hero-visual">
            <div className="chat-preview">
              <div className="chat-message bot">
                <div className="message-avatar">V</div>
                <div className="message-content">
                  Hello! I'm VitalAI. How can I help you today?
                </div>
              </div>
              <div className="chat-message user">
                <div className="message-content">
                  I need to schedule an appointment
                </div>
                <div className="message-avatar">U</div>
              </div>
              <div className="chat-message bot">
                <div className="message-avatar">V</div>
                <div className="message-content">
                  I can help with that! Which department do you need?
                </div>
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
            <div className="stat">
              <h3>50%</h3>
              <p>Reduction in Admin Time</p>
            </div>
            <div className="stat">
              <h3>24/7</h3>
              <p>Availability</p>
            </div>
            <div className="stat">
              <h3>5</h3>
              <p>Languages Supported</p>
            </div>
            <div className="stat">
              <h3>1000+</h3>
              <p>Patients Served</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <h2>Ready to Get Started?</h2>
          <p>Join thousands of patients using VitalAI for better healthcare access</p>
          <button 
            onClick={() => setCurrentView('chat')}
            className="cta-button large"
          >
            Start Chatting with VitalAI
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="home-footer">
        <div className="container">
          <p>&copy; 2024 VitalAI. AI-powered healthcare assistance for South Africa.</p>
        </div>
      </footer>
    </div>
  );
};

export default Home;