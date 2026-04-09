import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Calendar, RefreshCw } from 'lucide-react';
import AppointmentScheduler from './AppointmentScheduler';
import { chatAPI } from '../services/api';
import './ChatInterface.css';

// Quick symptom chips shown at the start
const QUICK_SYMPTOMS = [
  { label: '🤕 Headache',        value: 'I have a headache' },
  { label: '🌡️ Fever',           value: 'I have a fever' },
  { label: '😮‍💨 Chest Pain',      value: 'I have chest pain and difficulty breathing' },
  { label: '🤢 Nausea',          value: 'I feel nauseous and have stomach pain' },
  { label: '😮 Sore Throat',     value: 'I have a sore throat and cough' },
  { label: '🩹 Injury',          value: 'I have an injury that needs assessment' },
  { label: '📅 Book Appointment', value: 'I would like to schedule an appointment' },
  { label: '💙 Mental Health',   value: 'I am struggling with anxiety and stress' },
];

// Severity → display config
const SEVERITY_CONFIG = {
  CRITICAL: { emoji: '🔴', color: '#dc2626', bg: '#fef2f2', border: '#fca5a5' },
  HIGH:     { emoji: '🟠', color: '#ea580c', bg: '#fff7ed', border: '#fdba74' },
  MEDIUM:   { emoji: '🟡', color: '#b45309', bg: '#fffbeb', border: '#fcd34d' },
  LOW:      { emoji: '🟢', color: '#15803d', bg: '#f0fdf4', border: '#86efac' },
};

// Render **bold** markdown and newlines as JSX
const RenderText = ({ text }) => (
  <div>
    {text.split('\n').map((line, i) => {
      const parts = line.split(/\*\*(.*?)\*\*/g);
      return (
        <p key={i} style={{ margin: line === '' ? '4px 0' : '2px 0', lineHeight: '1.6' }}>
          {parts.map((part, j) => j % 2 === 1 ? <strong key={j}>{part}</strong> : part)}
        </p>
      );
    })}
  </div>
);

const ChatInterface = () => {
  const [messages, setMessages] = useState([{
    id: 1,
    text: "Hello! I'm **VitalAI**, your medical triage assistant.\n\nDescribe your symptoms and I'll assess their severity and advise on the right next steps. Type freely or tap a quick option below to get started.",
    sender: 'bot',
    timestamp: new Date(),
    type: 'text',
    showQuickSymptoms: true,
  }]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showAppointmentScheduler, setShowAppointmentScheduler] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    const messageText = (text || inputText).trim();
    if (!messageText || isLoading) return;

    setMessages(prev => prev.map(m => ({ ...m, showQuickSymptoms: false })).concat({
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
      type: 'text',
    }));
    setInputText('');
    setIsLoading(true);

    try {
      const data = await chatAPI.sendMessage(messageText);
      const reply = data.reply || 'Sorry, I could not process that. Please try again.';
      const severityKey = (data.severity || '').toUpperCase();
      const severity = SEVERITY_CONFIG[severityKey]
        ? { level: severityKey, ...SEVERITY_CONFIG[severityKey] }
        : null;

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: reply,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text',
        severity,
        confidence: data.confidence || 0,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: '⚠️ Could not reach the VitalAI service. Please check your connection and try again.',
        sender: 'bot',
        timestamp: new Date(),
        type: 'text',
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAppointmentSchedule = (data) => {
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: `✅ Appointment requested — ${data.department} on ${data.date} at ${data.time}.\n\nYou will receive a confirmation from the clinic.`,
      sender: 'bot',
      timestamp: new Date(),
      type: 'appointment',
    }]);
    setShowAppointmentScheduler(false);
  };

  const handleReset = () => {
    setMessages([{
      id: Date.now(),
      text: "New session started. Tell me your symptoms and I'll help assess them.\n\nOr tap a quick option below.",
      sender: 'bot',
      timestamp: new Date(),
      type: 'text',
      showQuickSymptoms: true,
    }]);
    setInputText('');
  };

  return (
    <div className="vitalai-chat">

      {/* Header */}
      <div className="chat-header">
        <div className="header-left">
          <div className="bot-avatar"><Bot size={22} /></div>
          <div className="header-info">
            <h3>VitalAI</h3>
            <span className="status">● Online · Medical Triage Assistant</span>
          </div>
        </div>
        <button
          onClick={handleReset}
          title="Start new session"
          style={{
            background: 'none', border: '1px solid #e5e7eb', borderRadius: '6px',
            padding: '5px 10px', cursor: 'pointer', color: '#6b7280',
            display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px',
          }}
        >
          <RefreshCw size={13} /> New Session
        </button>
      </div>

      {/* Messages */}
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender}`}>
            <div className="message-avatar">
              {message.sender === 'bot' ? <Bot size={15} /> : <User size={15} />}
            </div>
            <div className="message-content">

              {/* Severity badge */}
              {message.severity && (
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: '6px',
                  background: message.severity.bg,
                  border: `1px solid ${message.severity.border}`,
                  color: message.severity.color,
                  borderRadius: '20px', padding: '4px 12px',
                  fontSize: '12px', fontWeight: 700, marginBottom: '10px',
                }}>
                  {message.severity.emoji} {message.severity.level}
                  {message.confidence > 0 && (
                    <span style={{ fontWeight: 400, opacity: 0.7 }}>
                      · {message.confidence}% confidence
                    </span>
                  )}
                </div>
              )}

              {/* Message body */}
              {message.type === 'appointment' ? (
                <div className="appointment-message">
                  <Calendar size={14} />
                  <RenderText text={message.text} />
                </div>
              ) : (
                <RenderText text={message.text} />
              )}

              {/* Quick symptom chips */}
              {message.showQuickSymptoms && (
                <div style={{ marginTop: '14px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {QUICK_SYMPTOMS.map((s) => (
                    <button
                      key={s.value}
                      onClick={() => sendMessage(s.value)}
                      style={{
                        background: '#f0f4ff', border: '1px solid #c7d2fe',
                        borderRadius: '20px', padding: '6px 14px',
                        fontSize: '13px', cursor: 'pointer', color: '#4338ca',
                        fontWeight: 500, transition: 'background 0.15s',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = '#e0e7ff'}
                      onMouseLeave={e => e.currentTarget.style.background = '#f0f4ff'}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              )}

              <span className="timestamp">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div className="message bot">
            <div className="message-avatar"><Bot size={15} /></div>
            <div className="message-content">
              <div className="typing-indicator"><span /><span /><span /></div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick action bar */}
      <div className="quick-actions">
        <button className="quick-action-btn" onClick={() => setShowAppointmentScheduler(true)}>
          <Calendar size={15} /> Schedule Appointment
        </button>
      </div>

      {/* Input */}
      <div className="input-area">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
          placeholder="Describe your symptoms…"
          disabled={isLoading}
        />
        <button
          onClick={() => sendMessage()}
          disabled={!inputText.trim() || isLoading}
          className="send-button"
        >
          <Send size={17} />
        </button>
      </div>

      {/* Appointment modal */}
      {showAppointmentScheduler && (
        <AppointmentScheduler
          onSchedule={handleAppointmentSchedule}
          onClose={() => setShowAppointmentScheduler(false)}
        />
      )}
    </div>
  );
};

export default ChatInterface;
