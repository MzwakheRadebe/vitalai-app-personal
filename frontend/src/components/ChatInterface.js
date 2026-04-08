import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Paperclip, Calendar } from 'lucide-react';
import LanguageSelector from './LanguageSelector';
import FileUpload from './FileUpload';
import AppointmentScheduler from './AppointmentScheduler';
import { chatAPI } from '../services/api';
import './ChatInterface.css';


// Severity level helper — parses the AI reply for a severity keyword
const getSeverityLabel = (reply) => {
  const upper = reply.toUpperCase();
  if (upper.includes('CRITICAL')) return { level: 'CRITICAL', emoji: '🔴', color: '#dc2626' };
  if (upper.includes('HIGH'))     return { level: 'HIGH',     emoji: '🟠', color: '#ea580c' };
  if (upper.includes('MEDIUM'))   return { level: 'MEDIUM',   emoji: '🟡', color: '#ca8a04' };
  if (upper.includes('LOW'))      return { level: 'LOW',      emoji: '🟢', color: '#16a34a' };
  return null;
};


// Main chat interface component for VitalAI
const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm VitalAI, your medical triage assistant. Describe your symptoms and I'll assess their severity and advise on next steps. You can also schedule an appointment or upload medical documents.",
      sender: 'bot',
      timestamp: new Date(),
      type: 'text',
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

  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
      type: 'text',
    };

    setMessages(prev => [...prev, userMessage]);
    const sentText = inputText;
    setInputText('');
    setIsLoading(true);

    try {
      // Call the real FastAPI backend at /api/chat
      const data = await chatAPI.sendMessage(sentText, selectedLanguage);
      const reply = data.reply || 'Sorry, I did not receive a response. Please try again.';

      const botMessage = {
        id: Date.now() + 1,
        text: reply,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text',
        severity: getSeverityLabel(reply),
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat API error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: '⚠️ Unable to connect to the VitalAI service. Please check your connection and try again.',
        sender: 'bot',
        timestamp: new Date(),
        type: 'text',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = (file) => {
    const fileMessage = {
      id: Date.now(),
      text: `Uploaded file: ${file.name}`,
      sender: 'user',
      timestamp: new Date(),
      type: 'file',
      file,
    };
    setMessages(prev => [...prev, fileMessage]);
    setShowFileUpload(false);
  };

  const handleAppointmentSchedule = (appointmentData) => {
    const appointmentMessage = {
      id: Date.now(),
      text: `Appointment scheduled for ${appointmentData.date} at ${appointmentData.time} — ${appointmentData.department}`,
      sender: 'user',
      timestamp: new Date(),
      type: 'appointment',
      appointment: appointmentData,
    };
    setMessages(prev => [...prev, appointmentMessage]);
    setShowAppointmentScheduler(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="vitalai-chat">
      {/* Header */}
      <div className="chat-header">
        <div className="header-left">
          <div className="bot-avatar">
            <Bot size={24} />
          </div>
          <div className="header-info">
            <h3>VitalAI</h3>
            <span className="status">Online • Medical Triage Assistant</span>
          </div>
        </div>
        <LanguageSelector
          selectedLanguage={selectedLanguage}
          onLanguageChange={setSelectedLanguage}
        />
      </div>

      {/* Messages Container */}
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.sender}`}>
            <div className="message-avatar">
              {message.sender === 'bot' ? <Bot size={16} /> : <User size={16} />}
            </div>
            <div className="message-content">
              {message.type === 'file' ? (
                <div className="file-message">
                  <Paperclip size={16} />
                  <span>{message.text}</span>
                </div>
              ) : message.type === 'appointment' ? (
                <div className="appointment-message">
                  <Calendar size={16} />
                  <span>{message.text}</span>
                </div>
              ) : (
                <>
                  {/* Severity badge for bot messages that contain a triage level */}
                  {message.sender === 'bot' && message.severity && (
                    <div
                      className="severity-badge"
                      style={{ color: message.severity.color }}
                    >
                      {message.severity.emoji} Severity: <strong>{message.severity.level}</strong>
                    </div>
                  )}
                  <p>{message.text}</p>
                </>
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
            <div className="message-avatar">
              <Bot size={16} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <button className="quick-action-btn" onClick={() => setShowAppointmentScheduler(true)}>
          <Calendar size={16} />
          Schedule Appointment
        </button>
        <button className="quick-action-btn" onClick={() => setShowFileUpload(true)}>
          <Paperclip size={16} />
          Upload Document
        </button>
      </div>

      {/* Input Area */}
      <div className="input-area">
        <button className="attachment-btn" onClick={() => setShowFileUpload(true)}>
          <Paperclip size={18} />
        </button>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe your symptoms or ask for help..."
          disabled={isLoading}
        />
        <button
          onClick={sendMessage}
          disabled={!inputText.trim() || isLoading}
          className="send-button"
        >
          <Send size={18} />
        </button>
      </div>

      {/* Modals */}
      {showFileUpload && (
        <FileUpload
          onFileUpload={handleFileUpload}
          onClose={() => setShowFileUpload(false)}
        />
      )}
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
