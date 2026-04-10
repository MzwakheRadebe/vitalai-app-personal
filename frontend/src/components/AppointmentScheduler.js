import React, { useState, useEffect } from 'react';
import { X, Calendar, Clock, User, Stethoscope } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { appointmentsAPI, staffAPI } from '../services/api';
import './AppointmentScheduler.css';

const TIME_SLOTS = [
  '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
  '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
];

const AppointmentScheduler = ({ onSchedule, onClose, onSignInRequired }) => {
  const { user } = useAuth();
  const [doctors, setDoctors] = useState([]);
  const [formData, setFormData] = useState({
    doctorEmail: '',
    date: '',
    time: '',
    patientName: user?.name || user?.email?.split('@')[0] || '',
    reason: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    staffAPI.getDoctors()
      .then(setDoctors)
      .catch(() => setDoctors([]));
  }, []);

  const handleInputChange = (field, value) => {
    setError('');
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const selectedDoctor = doctors.find(d => d.email === formData.doctorEmail) || null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!user) {
      if (onSignInRequired) onSignInRequired();
      else onClose();
      return;
    }

    if (!formData.doctorEmail || !formData.date || !formData.time || !formData.patientName) {
      setError('Please fill in all required fields.');
      return;
    }

    setIsLoading(true);
    try {
      const startsAt = `${formData.date}T${formData.time}:00`;
      const startDate = new Date(startsAt);
      const endDate = new Date(startDate.getTime() + 30 * 60 * 1000);
      const endsAt = endDate.toISOString().slice(0, 19);

      const payload = {
        patient_name: formData.patientName,
        clinician: selectedDoctor.name,
        department: selectedDoctor.department,
        reason: formData.reason || null,
        starts_at: startsAt,
        ends_at: endsAt,
      };

      const result = await appointmentsAPI.create(payload);
      onSchedule({
        ...formData,
        department: selectedDoctor.department,
        clinician: selectedDoctor.name,
        id: result.id,
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map(d => d.msg).join(' · '));
      } else if (err.response?.status === 409) {
        setError('That time slot is already booked. Please choose another time.');
      } else {
        setError('Booking failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getTomorrowDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  // Not signed in — show gate
  if (!user) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="appointment-modal" onClick={e => e.stopPropagation()}>
          <div className="modal-header">
            <h3>Book an Appointment</h3>
            <button className="close-btn" onClick={onClose}><X size={20} /></button>
          </div>
          <div style={{ padding: '32px 24px', textAlign: 'center' }}>
            <Calendar size={48} color="#667eea" style={{ marginBottom: '16px' }} />
            <h4 style={{ margin: '0 0 8px', color: '#1f2937', fontSize: '18px' }}>Sign in required</h4>
            <p style={{ color: '#6b7280', fontSize: '14px', lineHeight: 1.6, marginBottom: '24px' }}>
              You need an account to book appointments so we can send you confirmation and reminders.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <button
                onClick={() => { onClose(); if (onSignInRequired) onSignInRequired(); }}
                style={{
                  background: '#667eea', color: '#fff', border: 'none',
                  padding: '10px 24px', borderRadius: '8px', cursor: 'pointer',
                  fontSize: '14px', fontWeight: 600,
                }}
              >
                Sign In / Register
              </button>
              <button
                onClick={onClose}
                style={{
                  background: 'none', color: '#6b7280', border: '1px solid #d1d5db',
                  padding: '10px 24px', borderRadius: '8px', cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="appointment-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Schedule Appointment</h3>
          <button className="close-btn" onClick={onClose}><X size={20} /></button>
        </div>

        <form onSubmit={handleSubmit} className="appointment-form">

          {/* Patient name */}
          <div className="form-group">
            <label><User size={16} /> Patient Name *</label>
            <input
              type="text"
              value={formData.patientName}
              onChange={(e) => handleInputChange('patientName', e.target.value)}
              placeholder="Enter your full name"
              required
            />
          </div>

          {/* Doctor selection */}
          <div className="form-group">
            <label><Stethoscope size={16} /> Choose a Doctor *</label>
            <div className="doctor-grid">
              {doctors.map(doc => (
                <button
                  key={doc.email}
                  type="button"
                  className={`doctor-card ${formData.doctorEmail === doc.email ? 'selected' : ''}`}
                  onClick={() => handleInputChange('doctorEmail', doc.email)}
                >
                  <div className="doctor-avatar">{doc.name.split(' ').slice(-1)[0][0]}</div>
                  <div className="doctor-info">
                    <div className="doctor-name">{doc.name}</div>
                    <div className="doctor-dept">{doc.department}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Date and Time */}
          <div className="form-row">
            <div className="form-group">
              <label>Date *</label>
              <input
                type="date"
                value={formData.date}
                onChange={(e) => handleInputChange('date', e.target.value)}
                min={getTomorrowDate()}
                required
              />
            </div>
            <div className="form-group">
              <label><Clock size={16} /> Time *</label>
              <select
                value={formData.time}
                onChange={(e) => handleInputChange('time', e.target.value)}
                required
              >
                <option value="">Select Time</option>
                {TIME_SLOTS.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Reason */}
          <div className="form-group">
            <label>Reason for Visit</label>
            <textarea
              value={formData.reason}
              onChange={(e) => handleInputChange('reason', e.target.value)}
              placeholder="Briefly describe the reason for your visit…"
              rows="2"
            />
          </div>

          {/* Summary */}
          {selectedDoctor && formData.date && formData.time && (
            <div className="appointment-summary">
              <h4>Booking Summary</h4>
              <div className="summary-details">
                <div className="summary-item"><span>Patient:</span><span>{formData.patientName || '—'}</span></div>
                <div className="summary-item"><span>Doctor:</span><span>{selectedDoctor.name}</span></div>
                <div className="summary-item"><span>Department:</span><span>{selectedDoctor.department}</span></div>
                <div className="summary-item"><span>Date & Time:</span><span>{formData.date} at {formData.time}</span></div>
              </div>
            </div>
          )}

          {error && (
            <div style={{
              background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '8px',
              padding: '10px 14px', marginBottom: '4px', color: '#dc2626', fontSize: '13px',
            }}>
              {error}
            </div>
          )}

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={isLoading}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={isLoading}>
              {isLoading ? 'Booking…' : 'Confirm Appointment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AppointmentScheduler;
