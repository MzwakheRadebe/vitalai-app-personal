import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Mock data for development
const mockResponses = {
  symptoms: {
    headache: "I understand you're experiencing a headache. How long have you had this pain?",
    fever: "For fever symptoms, please monitor your temperature. Have you taken any medication?",
    appointment: "I can help schedule an appointment. Which department do you need?",
    emergency: "This sounds serious. Please proceed to emergency care immediately."
  }
};

export const chatAPI = {
  sendMessage: async (message, language = 'en') => {
    try {
      // For now, use mock responses
      const mockResponse = getMockResponse(message);
      return { data: { reply: mockResponse, triage_level: 'MEDIUM', department: 'General Practice' } };
      
      // TODO: Uncomment when backend is ready
      // return await api.post('/chat', { message, language });
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  scheduleAppointment: async (appointmentData) => {
    // Mock appointment scheduling
    return { 
      data: { 
        success: true, 
        appointment_id: 'APT-' + Date.now(),
        date: appointmentData.date,
        department: appointmentData.department
      } 
    };
  }
};

const getMockResponse = (userInput) => {
  const input = userInput.toLowerCase();
  
  if (input.includes('headache') || input.includes('pain')) {
    return mockResponses.symptoms.headache;
  } else if (input.includes('fever') || input.includes('temperature')) {
    return mockResponses.symptoms.fever;
  } else if (input.includes('appointment') || input.includes('schedule')) {
    return mockResponses.symptoms.appointment;
  } else if (input.includes('emergency') || input.includes('urgent')) {
    return mockResponses.symptoms.emergency;
  } else {
    return "Thank you for sharing. Could you tell me more about your symptoms so I can better assist you?";
  }
};

export default api;