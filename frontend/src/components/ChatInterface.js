import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Paperclip, Calendar, RefreshCw } from 'lucide-react';
import LanguageSelector from './LanguageSelector';
import FileUpload from './FileUpload';
import AppointmentScheduler from './AppointmentScheduler';
import { chatAPI } from '../services/api';
import './ChatInterface.css';

// Quick symptom chips shown at the start
const QUICK_SYMPTOMS = [
  { label: '🤕 Headache', value: 'I have a headache' },
  { label: '🌡️ Fever', value: 'I have a fever' },
  { label: '😮‍💨 Chest Pain', value: 'I have chest pain and difficulty breathing' },
  { label: '🤢 Nausea', value: 'I feel nauseous and have stomach pain' },
  { label: '😮 Sore Throat', value: 'I have a sore throat and cough' },
  { label: '🩹 Injury', value: 'I have an injury that needs assessment' },
  { label: '📅 Book Appointment', value: 'I would like to schedule an appointment' },
  { label: '💙 Mental Health', value: 'I am struggling with anxiety and stress' },
];

// Map severity string → display config
const SEVERITY_CONFIG = {
  CRITICAL: { emoji: '🔴', color: '#dc2626', bg: '#fef2f2', border: '#fca5a5' },
  HIGH:     { emoji: '🟠', color: '#ea580c', bg: '#fff7ed', border: '#fdba74' },
  MEDIUM:   { emoji: '🟡', color: '#b45309', bg: '#fffbeb', border: '#fcd34d' },
  LOW:      { emoji: '🟢', color: '#15803d', bg: '#f0fdf4', border: '#86efac' },
};

// Render message text — convert **bold** and newlines to JSX
const RenderText = ({ text }) => {
  const lines = text.split('\n');
  return (
    <div>
      {lines.map((line, i) => {
        // Bold **text**
        const parts = line.split(/\*\*(.*?)\*\*/g);
        const rendered = parts.map((part, j) =>
          j % 2 === 1 ? <strong key={j}>{part}</strong> : part
        );
        return (
          <p key={i} style={{ margin: line === '' ? '4px 0' : '2px 0', lineHeight: '1.55' }}>
            {rendered}
          </p>
        );
      })}
    </div>
  );
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm **VitalAI**, your medical triage assistant.\n\nDescribe your symptoms below and I'll assess their severity and advise on next steps. You can type freely or tap one of the quick options to get started.",
      sender: 'bot',
      timestamp: new Date(),
      type: 'text',
      showQuickSymptoms: true,
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [showAppointmentScheduler, setShowAppointmentScheduler] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (text) => {
    const messageText = text || inputText;
    if (!messageText.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
      type: 'text',
    };

    setMessages(prev => prev.map(m => ({ ...m, showQuickSymptoms: false })).concat(userMessage));
    setInputText('');
    setIsLoading(true);

    try {
      const data = await chatAPI.sendMessage(messageText, selectedLanguage);
      const reply = data.reply || 'Sorry, I could not process that. Please try again.';
      const severityKey = (data.severity || '').toUpperCase();
      const severity = SEVERITY_CONFIG[severityKey] ? { level: severityKey, ...SEVERITY_CONFIG[severityKey] } : null;

      const botMessage = {
        id: Date.now() + 1,
        text: reply,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text',
        severity,
        confidence: data.confidence || 0,
      };
      setMessages(prev => [...prev, botMessage]);
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

  const handleFileUpload = (file) => {
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: `Uploaded: ${file.name}`,
      sender: 'user',
      timestamp: new Date(),
      type: 'file',
    }]);
    setShowFileUpload(false);
  };

  const handleAppointmentSchedule = (data) => {
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: `✅ Appointment booked — ${data.department} on ${data.date} at ${data.time}`,
      sender: 'bot',
      timestamp: new Date(),
      type: 'appointment',
    }]);
    setShowAppointmentScheduler(false);
  };

  const handleReset = () => {
    setMessages([{
      id: Date.now(),
      text: "Hello again! Tell me your symptoms and I'll help assess them.\n\nOr tap one of the quick options below.",
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <LanguageSelector selectedLanguage={selectedLanguage} onLanguageChange={setSelectedLanguage} />
          <button
            onClick={handleReset}
            title="Start new session"
            style={{ background: 'none', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '5px 8px', cursor: 'pointer', color: '#6b7280', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}
          >
            <RefreshCw size={13} /> New
          </button>
        </div>
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
                  borderRadius: '20px',
                  padding: '4px 12px',
                  fontSize: '12px',
                  fontWeight: 700,
                  marginBottom: '10px',
                }}>
                  {message.severity.emoji} {message.severity.level}
                  {message.confidence > 0 && (
                    <span style={{ fontWeight: 400, opacity: 0.75 }}>· {message.confidence}% confidence</span>
                  )}
                </div>
              )}

              {/* Message body */}
              {message.type === 'file' ? (
                <div className="file-message"><Paperclip size={14} /> <span>{message.text}</span></div>
              ) : message.type === 'appointment' ? (
                <div className="appointment-message"><Calendar size={14} /> <span>{message.text}</span></div>
              ) : (
                <RenderText text={message.text} />
              )}

              {/* Quick symptom chips on welcome message */}
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
                        fontWeight: 500, transition: 'all 0.15s',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = '#e0e7ff'; }}
                      onMouseLeave={e => { e.currentTarget.style.background = '#f0f4ff'; }}
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
        <button className="quick-action-btn" onClick={() => setShowFileUpload(true)}>
          <Paperclip size={15} /> Upload Document
        </button>
      </div>

      {/* Input */}
      <div className="input-area">
        <button className="attachment-btn" onClick={() => setShowFileUpload(true)} title="Upload document">
          <Paperclip size={17} />
        </button>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
          placeholder="Describe your symptoms…"
          disabled={isLoading}
        />
        <button onClick={() => sendMessage()} disabled={!inputText.trim() || isLoading} className="send-button">
          <Send size={17} />
        </button>
      </div>

      {/* Modals */}
      {showFileUpload && <FileUpload onFileUpload={handleFileUpload} onClose={() => setShowFileUpload(false)} />}
      {showAppointmentScheduler && <AppointmentScheduler onSchedule={handleAppointmentSchedule} onClose={() => setShowAppointmentScheduler(false)} />}
    </div>
  );
};

export default ChatInterface;
