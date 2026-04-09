import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';

import Home from './pages/Home';
import ClinicKiosk from './pages/Kiosk';
import PatientPortal from './pages/PatientPortal';
import StaffDashboard from './pages/StaffDashboard';
import AdminDashboard from './pages/AdminDashboard';

import './App.css';

/**
 * ProtectedRoute — wraps routes that require authentication and/or a specific role.
 * Redirects to home if not logged in, or if the user's role doesn't match.
 */
const ProtectedRoute = ({ element, requiredRole }) => {
  const { user, loading } = useAuth();

  // Wait for session restore before deciding to redirect
  if (loading) return null;

  if (!user) return <Navigate to="/" replace />;

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return element;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Public */}
            <Route path="/" element={<Home />} />
            <Route path="/clinic" element={<ClinicKiosk />} />
            <Route path="/kiosk" element={<ClinicKiosk />} />

            {/* Authenticated — any logged-in user */}
            <Route
              path="/patient"
              element={<ProtectedRoute element={<PatientPortal />} />}
            />

            {/* Role-restricted */}
            <Route
              path="/staff"
              element={<ProtectedRoute element={<StaffDashboard />} requiredRole="staff" />}
            />
            <Route
              path="/admin"
              element={<ProtectedRoute element={<AdminDashboard />} requiredRole="admin" />}
            />

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster position="top-right" />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
