import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Paperclip, Calendar } from 'lucide-react';
import LanguageSelector from './LanguageSelector';
import FileUpload from './FileUpload';
import AppointmentScheduler from './AppointmentScheduler';
import './ChatInterface.css';


const API_BASE_URL =  "http://localhost:5000";


// Main chat interface component for VitalAI
const ChatInterface = () => {
  // State for chat messages
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm VitalAI. How can I help you today? You can describe your symptoms, request an appointment, or upload medical documents.",
      sender: 'bot',
      timestamp: new Date(),
      type: 'text'
    }
  ]);
  // State for user input text
  const [inputText, setInputText] = useState('');
  // State to indicate if bot is "typing"
  const [isLoading, setIsLoading] = useState(false);
  // State for selected language
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  // State to show/hide file upload modal
  const [showFileUpload, setShowFileUpload] = useState(false);
  // State to show/hide appointment scheduler modal
  const [showAppointmentScheduler, setShowAppointmentScheduler] = useState(false);
  // Ref to scroll to the bottom of messages
  const messagesEndRef = useRef(null);

  // Scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle sending a message
  const sendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    // Add user message to chat
    const userMessage = {
      id: Date.now(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
      type: 'text'
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    
    try {
  // Call FastAPI endpoint
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: inputText })
  });

  if (!response.ok) throw new Error("Failed to fetch AI response");

  const data = await response.json();

  let responseText = "";
const conf = data.confidence.toFixed(2);

switch (data.predicted_severity.toUpperCase()) {
  case "LOW":
    responseText = `Your condition appears to be *low severity*. It’s likely mild, but monitor your symptoms and rest. (Confidence: ${conf})`;
    break;
  case "MEDIUM":
    responseText = `This condition may be of *moderate concern*. You should monitor symptoms and consult a doctor if needed. (Confidence: ${conf})`;
    break;
  case "HIGH":
    responseText = `Your symptoms suggest a *high severity* condition. Please seek medical advice soon. (Confidence: ${conf})`;
    break;
  case "CRITICAL":
    responseText = `⚠️ *Critical severity detected.* Please seek *immediate medical attention*. (Confidence: ${conf})`;
    break;
  default:
    responseText = `I couldn’t determine severity confidently. (Confidence: ${conf})`;
}

  // Format bot message based on response
  const botMessage = {
    id: Date.now() + 1,
    text: responseText,
    sender: 'bot',
    timestamp: new Date(),
    type: 'text'
  };

  setMessages(prev => [...prev, botMessage]);
} catch (error) {
  console.error("Error fetching AI response:", error);

  const botMessage = {
    id: Date.now() + 1,
    text: "⚠️ Sorry, I couldn't process that right now. Please try again.",
    sender: 'bot',
    timestamp: new Date(),
    type: 'text'
  };
  setMessages(prev => [...prev, botMessage]);
} finally {
  setIsLoading(false);
}

  };

  // Handle file upload event
  const handleFileUpload = (file) => {
    const fileMessage = {
      id: Date.now(),
      text: `Uploaded file: ${file.name}`,
      sender: 'user',
      timestamp: new Date(),
      type: 'file',
      file: file
    };
    setMessages(prev => [...prev, fileMessage]);
    setShowFileUpload(false);
  };

  // Handle appointment scheduling event
  const handleAppointmentSchedule = (appointmentData) => {
    const appointmentMessage = {
      id: Date.now(),
      text: `Appointment scheduled for ${appointmentData.date} in ${appointmentData.department}`,
      sender: 'user',
      timestamp: new Date(),
      type: 'appointment',
      appointment: appointmentData
    };
    setMessages(prev => [...prev, appointmentMessage]);
    setShowAppointmentScheduler(false);
  };

  // Handle Enter key press for sending messages
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
            <span className="status">Online • Medical Assistant</span>
          </div>
        </div>
        {/* Language selection dropdown */}
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
              {/* Render different message types */}
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
                <p>{message.text}</p>
              )}
              {/* Message timestamp */}
              <span className="timestamp">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        
        {/* Loading/typing indicator for bot */}
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
        {/* Dummy div to scroll to bottom */}
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
        {/* Attachment button */}
        <button 
          className="attachment-btn"
          onClick={() => setShowFileUpload(true)}
        >
          <Paperclip size={18} />
        </button>
        
        {/* Text input for user messages */}
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe your symptoms or ask for help..."
          disabled={isLoading}
        />
        
        {/* Send button */}
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