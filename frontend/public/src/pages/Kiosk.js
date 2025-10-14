import React, { useState } from 'react';
import { Users, Stethoscope, Clock, Calendar, MessageCircle, UserPlus } from 'lucide-react';
import PatientPortal from './PatientPortal';
import StaffDashboard from './StaffDashboard';
import './Kiosk.css';

const Kiosk = () => {
  const [userType, setUserType] = useState(null); // null, 'patient', or 'staff'
  const [quickAction, setQuickAction] = useState(null);

  // Quick actions for patients
  const patientQuickActions = [
    { 
      id: 'checkin', 
      label: 'Quick Check-in', 
      description: 'Check in for your appointment',
      icon: UserPlus,
      color: '#10B981'
    },
    { 
      id: 'appointment', 
      label: 'Schedule Appointment', 
      description: 'Book a new appointment',
      icon: Calendar,
      color: '#3B82F6'
    },
    { 
      id: 'chat', 
      label: 'Medical Assistance', 
      description: 'Chat with VitalAI for help',
      icon: MessageCircle,
      color: '#8B5CF6'
    },
    { 
      id: 'info', 
      label: 'Clinic Information', 
      description: 'View services and wait times',
      icon: Clock,
      color: '#F59E0B'
    }
  ];

  // Quick actions for staff
  const staffQuickActions = [
    { 
      id: 'patients', 
      label: 'Patient Queue', 
      description: 'View current patients',
      icon: Users,
      color: '#EF4444'
    },
    { 
      id: 'schedule', 
      label: 'Today\'s Schedule', 
      description: 'View appointments',
      icon: Calendar,
      color: '#3B82F6'
    },
    { 
      id: 'records', 
      label: 'Medical Records', 
      description: 'Access patient files',
      icon: Stethoscope,
      color: '#10B981'
    },
    { 
      id: 'analytics', 
      label: 'Clinic Analytics', 
      description: 'View performance metrics',
      icon: Clock,
      color: '#8B5CF6'
    }
  ];

  // If user has selected a specific mode, show that interface
  if (userType === 'patient' && quickAction) {
    return <PatientPortal quickAction={quickAction} onBack={() => setQuickAction(null)} />;
  }

  if (userType === 'staff' && quickAction) {
    return <StaffDashboard quickAction={quickAction} onBack={() => setQuickAction(null)} />;
  }

  // If user has selected a type but no specific action, show quick actions
  if (userType) {
    const actions = userType === 'patient' ? patientQuickActions : staffQuickActions;
    
    return (
      <div className="clinic-interface">
        {/* Header */}
        <div className="clinic-header">
          <button 
            className="back-button"
            onClick={() => setUserType(null)}
          >
            ← Back
          </button>
          <h1>
            {userType === 'patient' ? 'Patient Services' : 'Staff Portal'}
          </h1>
          <div className="clinic-info">
            <span>Clinic Kiosk</span>
          </div>
        </div>

        {/* Quick Actions Grid */}
        <div className="quick-actions-section">
          <h2>What would you like to do?</h2>
          <div className="quick-actions-grid">
            {actions.map((action) => (
              <button
                key={action.id}
                className="quick-action-card large"
                onClick={() => setQuickAction(action.id)}
                style={{ '--action-color': action.color }}
              >
                <div className="action-icon-container">
                  <action.icon size={32} />
                </div>
                <div className="action-content">
                  <h3>{action.label}</h3>
                  <p>{action.description}</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Full Access Option */}
        <div className="full-access-section">
          <button 
            className="full-access-btn"
            onClick={() => setQuickAction('full')}
          >
            Access Full {userType === 'patient' ? 'Patient' : 'Staff'} Portal
          </button>
        </div>
      </div>
    );
  }

  // Main selection screen (initial view)
  return (
    <div className="clinic-interface initial">
      {/* Header */}
      <div className="clinic-header">
        <div className="clinic-logo">
          <Stethoscope size={40} />
          <h1>VitalAI Clinic Center</h1>
        </div>
        <div className="clinic-status">
          <div className="status-indicator open">● Clinic Open</div>
          <span>Current Wait Time: 15-20 mins</span>
        </div>
      </div>

      {/* Main Selection */}
      <div className="user-selection">
        <h2>Welcome to Our Clinic</h2>
        <p className="selection-subtitle">Please select how you would like to use this kiosk:</p>
        
        <div className="selection-grid">
          {/* Patient Option */}
          <button 
            className="selection-card patient"
            onClick={() => setUserType('patient')}
          >
            <div className="selection-icon">
              <Users size={48} />
            </div>
            <div className="selection-content">
              <h3>I'm a Patient</h3>
              <p>Check in, schedule appointments, get medical assistance, or view clinic information</p>
              <ul className="feature-list">
                <li>✓ Quick check-in</li>
                <li>✓ Schedule appointments</li>
                <li>✓ Medical assistance</li>
                <li>✓ Clinic information</li>
              </ul>
            </div>
            <div className="selection-arrow">→</div>
          </button>

          {/* Staff Option */}
          <button 
            className="selection-card staff"
            onClick={() => setUserType('staff')}
          >
            <div className="selection-icon">
              <Stethoscope size={48} />
            </div>
            <div className="selection-content">
              <h3>I'm Clinic Staff</h3>
              <p>Access patient queue, medical records, schedule, and clinic analytics</p>
              <ul className="feature-list">
                <li>✓ Patient queue management</li>
                <li>✓ Medical records access</li>
                <li>✓ Appointment schedule</li>
                <li>✓ Clinic analytics</li>
              </ul>
            </div>
            <div className="selection-arrow">→</div>
          </button>
        </div>
      </div>

      {/* Emergency & Help Section */}
      <div className="help-section">
        <div className="emergency-alert">
          <div className="emergency-info">
            <strong>Emergency?</strong> Please proceed directly to reception
          </div>
          <div className="help-info">
            <strong>Need help?</strong> Ask our staff for assistance
          </div>
        </div>
        
        <div className="language-selector">
          <span>Language: </span>
          <select>
            <option>English</option>
            <option>isiZulu</option>
            <option>isiXhosa</option>
            <option>Afrikaans</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default Kiosk;