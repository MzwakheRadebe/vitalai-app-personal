import React, { useState } from 'react';
import { X, Calendar, Clock, User } from 'lucide-react';
import './AppointmentScheduler.css';

// List of available departments for appointment selection
const DEPARTMENTS = [
  'General Practice',
  'Pediatrics',
  'Emergency',
  'Cardiology',
  'Dermatology',
  'Orthopedics',
  'Dental'
];

// List of available time slots for appointments
const TIME_SLOTS = [
  '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
  '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
];

// AppointmentScheduler component for scheduling a new appointment
const AppointmentScheduler = ({ onSchedule, onClose }) => {
  // State to hold form data for the appointment
  const [formData, setFormData] = useState({
    department: '',
    date: '',
    time: '',
    patientName: '',
    reason: ''
  });

  // Handle changes to form fields and update state
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Handle form submission: validate and send appointment data
  const handleSubmit = (e) => {
    e.preventDefault();
    // Ensure required fields are filled
    if (formData.department && formData.date && formData.time && formData.patientName) {
      const appointmentData = {
        ...formData,
        id: 'APT-' + Date.now(), // Generate a unique appointment ID
        timestamp: new Date().toISOString() // Record creation timestamp
      };
      onSchedule(appointmentData); // Pass data to parent handler
    } else {
      alert('Please fill in all required fields');
    }
  };

  // Get tomorrow's date in YYYY-MM-DD format for date input min value
  const getTomorrowDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  return (
    <div className="modal-overlay">
      <div className="appointment-modal">
        {/* Modal header with title and close button */}
        <div className="modal-header">
          <h3>Schedule Appointment</h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Appointment form */}
        <form onSubmit={handleSubmit} className="appointment-form">
          {/* Patient Name input */}
          <div className="form-group">
            <label>
              <User size={16} />
              Patient Name *
            </label>
            <input
              type="text"
              value={formData.patientName}
              onChange={(e) => handleInputChange('patientName', e.target.value)}
              placeholder="Enter patient name"
              required
            />
          </div>

          {/* Department selection */}
          <div className="form-group">
            <label>
              <Calendar size={16} />
              Department *
            </label>
            <select
              value={formData.department}
              onChange={(e) => handleInputChange('department', e.target.value)}
              required
            >
              <option value="">Select Department</option>
              {DEPARTMENTS.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>

          {/* Date and Time selection */}
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
              <label>
                <Clock size={16} />
                Time *
              </label>
              <select
                value={formData.time}
                onChange={(e) => handleInputChange('time', e.target.value)}
                required
              >
                <option value="">Select Time</option>
                {TIME_SLOTS.map(time => (
                  <option key={time} value={time}>{time}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Reason for visit textarea */}
          <div className="form-group">
            <label>Reason for Visit</label>
            <textarea
              value={formData.reason}
              onChange={(e) => handleInputChange('reason', e.target.value)}
              placeholder="Briefly describe the reason for your visit..."
              rows="3"
            />
          </div>

          {/* Appointment summary section */}
          <div className="appointment-summary">
            <h4>Appointment Summary</h4>
            <div className="summary-details">
              <div className="summary-item">
                <span>Patient:</span>
                <span>{formData.patientName || 'Not specified'}</span>
              </div>
              <div className="summary-item">
                <span>Department:</span>
                <span>{formData.department || 'Not selected'}</span>
              </div>
              <div className="summary-item">
                <span>Date & Time:</span>
                <span>
                  {formData.date && formData.time 
                    ? `${formData.date} at ${formData.time}`
                    : 'Not selected'
                  }
                </span>
              </div>
            </div>
          </div>

          {/* Modal action buttons */}
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Schedule Appointment
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AppointmentScheduler;