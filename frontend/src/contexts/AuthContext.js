/**
 * AuthContext — Global authentication state
 *
 * Stores the JWT token in localStorage so it survives page refreshes.
 * On app load, restores session from localStorage if token exists.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session on app load
  useEffect(() => {
    const token = localStorage.getItem('vitalai_token');
    const storedUser = localStorage.getItem('vitalai_user');
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem('vitalai_token');
        localStorage.removeItem('vitalai_user');
      }
    }
    setLoading(false);
  }, []);

  /**
   * Login: calls the backend, stores JWT and user info.
   * Returns user object on success, throws on failure.
   */
  const login = async (email, password) => {
    const data = await authAPI.login(email, password);
    const token = data.access_token;

    // Decode user info from the token response
    const userData = {
      email,
      token,
      role: data.role || 'patient',
      name: email.split('@')[0],
      avatar: `https://ui-avatars.com/api/?name=${email.split('@')[0]}&background=667eea&color=fff`,
    };

    localStorage.setItem('vitalai_token', token);
    localStorage.setItem('vitalai_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  /**
   * Staff login: doctor selector + universal access code.
   * Returns user object on success, throws on failure.
   */
  const staffLogin = async (doctorEmail, accessCode) => {
    const data = await authAPI.staffLogin(doctorEmail, accessCode);
    const token = data.access_token;
    const userData = {
      email: doctorEmail,
      token,
      role: 'staff',
      name: data.name || doctorEmail.split('@')[0],
      department: data.department || null,
    };
    localStorage.setItem('vitalai_token', token);
    localStorage.setItem('vitalai_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  /**
   * Register: creates account, then auto-logs in.
   */
  const register = async (email, password, role = 'patient') => {
    await authAPI.register(email, password, role);
    return login(email, password);
  };

  /**
   * Logout: clears token and user state.
   */
  const logout = () => {
    localStorage.removeItem('vitalai_token');
    localStorage.removeItem('vitalai_user');
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    staffLogin,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
