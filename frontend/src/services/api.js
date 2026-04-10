/**
 * VitalAI API Service
 *
 * All API calls to the FastAPI backend.
 * Set REACT_APP_API_URL in your .env file for local dev,
 * or as an environment variable in Vercel for production.
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to every request if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('vitalai_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('vitalai_token');
      localStorage.removeItem('vitalai_user');
    }
    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password });
    return response.data;
  },

  register: async (email, password, role = 'patient') => {
    const response = await api.post('/api/auth/register', { email, password, role });
    return response.data;
  },

  getMe: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

export const chatAPI = {
  sendMessage: async (message, language = 'en') => {
    const response = await api.post('/api/chat', {
      prompt: message,
      language,
    });
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Appointments
// ---------------------------------------------------------------------------

export const appointmentsAPI = {
  create: async (appointmentData) => {
    const response = await api.post('/api/appointments', appointmentData);
    return response.data;
  },

  list: async () => {
    const response = await api.get('/api/appointments');
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/api/appointments/${id}`);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/api/appointments/${id}`);
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Staff / Doctors
// ---------------------------------------------------------------------------

export const staffAPI = {
  getDoctors: async () => {
    const response = await api.get('/api/staff/doctors');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// FAQ
// ---------------------------------------------------------------------------

export const faqAPI = {
  list: async () => {
    const response = await api.get('/api/faq');
    return response.data;
  },
};

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

export const healthAPI = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
