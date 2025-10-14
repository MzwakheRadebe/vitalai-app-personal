import React, { useState, useEffect } from 'react';
import { 
  User, Calendar, FileText, MessageCircle, History, Settings, LogOut, 
  Bell, Plus, Download, Clock, MapPin, Stethoscope, AlertCircle,
  Heart, Pill, Activity, Shield
} from 'lucide-react';
import ChatInterface from '../components/ChatInterface';
import AppointmentScheduler from '../components/AppointmentScheduler';
import FileUpload from '../components/FileUpload';
import LanguageSelector from '../components/LanguageSelector';
import { useAuth } from '../contexts/AuthContext';
import './PatientPortal.css';

const PatientPortal = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showAppointmentModal, setShowAppointmentModal] = useState(false);
  const [showFileUploadModal, setShowFileUploadModal] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en');

  // Mock patient data
  const patientInfo = {
    name: user?.name || 'John Doe',
    id: 'PT-001234',
    age: 35,
    bloodType: 'O+',
    lastVisit: '2024-01-15',
    primaryDoctor: 'Dr. Sarah Smith',
    phone: '+27 12 345 6789',
    email: 'john.doe@example.com',
    address: '123 Main St, Johannesburg, 2000'
  };

  const upcomingAppointments = [
    { 
      id: 1, 
      doctor: 'Dr. Sarah Smith', 
      department: 'Cardiology', 
      date: '2024-02-15', 
      time: '10:30 AM', 
      status: 'confirmed',
      type: 'Follow-up',
      location: 'Room 201'
    },
    { 
      id: 2, 
      doctor: 'Dr. Mike Johnson', 
      department: 'General Practice', 
      date: '2024-02-20', 
      time: '02:15 PM', 
      status: 'confirmed',
      type: 'Consultation',
      location: 'Room 105'
    }
  ];

  const medicalHistory = [
    { 
      id: 1, 
      date: '2024-01-15', 
      doctor: 'Dr. Sarah Smith', 
      diagnosis: 'Routine Checkup', 
      notes: 'All vitals normal. Blood pressure 120/80. Weight stable.',
      department: 'General Practice'
    },
    { 
      id: 2, 
      date: '2023-12-10', 
      doctor: 'Dr. Mike Johnson', 
      diagnosis: 'Influenza', 
      notes: 'Prescribed antiviral medication. Rest recommended.',
      department: 'General Practice'
    },
    { 
      id: 3, 
      date: '2023-11-05', 
      doctor: 'Dr. Emily Brown', 
      diagnosis: 'Annual Physical', 
      notes: 'Good overall health. Recommended exercise routine.',
      department: 'General Practice'
    }
  ];

  const prescriptions = [
    { 
      id: 1, 
      medication: 'Amoxicillin', 
      dosage: '500mg', 
      frequency: '3 times daily', 
      endDate: '2024-02-20',
      prescribedBy: 'Dr. Mike Johnson',
      instructions: 'Take with food. Complete full course.'
    },
    { 
      id: 2, 
      medication: 'Vitamin D', 
      dosage: '1000 IU', 
      frequency: 'Once daily', 
      endDate: 'Ongoing',
      prescribedBy: 'Dr. Sarah Smith',
      instructions: 'Take with breakfast.'
    }
  ];

  const vitalSigns = {
    bloodPressure: '120/80',
    heartRate: '72 bpm',
    temperature: '36.8°C',
    weight: '75 kg',
    height: '175 cm',
    lastUpdated: '2024-01-15'
  };

  const quickActions = [
    { 
      icon: MessageCircle, 
      label: 'Chat with VitalAI', 
      description: 'Get instant medical assistance',
      action: () => setActiveTab('chat'),
      color: '#667eea'
    },
    { 
      icon: Calendar, 
      label: 'Book Appointment', 
      description: 'Schedule a new appointment',
      action: () => setShowAppointmentModal(true),
      color: '#10B981'
    },
    { 
      icon: FileText, 
      label: 'Upload Documents', 
      description: 'Share medical records',
      action: () => setShowFileUploadModal(true),
      color: '#F59E0B'
    },
    { 
      icon: History, 
      label: 'View History', 
      description: 'Check medical history',
      action: () => setActiveTab('medical-history'),
      color: '#8B5CF6'
    }
  ];

  const handleFileUpload = (file) => {
    console.log('File uploaded:', file);
    // Here you would typically upload to your backend
    setShowFileUploadModal(false);
  };

  const handleAppointmentSchedule = (appointmentData) => {
    console.log('Appointment scheduled:', appointmentData);
    // Here you would typically send to your backend
    setShowAppointmentModal(false);
  };

  const handleEmergencyContact = () => {
    alert('In case of emergency, please call:\n\nEmergency Services: 911\nClinic Emergency: +27 11 123 4567');
  };

  // Auto-close sidebar on mobile when clicking a nav item
  useEffect(() => {
    if (window.innerWidth <= 768) {
      setSidebarOpen(false);
    }
  }, [activeTab]);

  // Render different content based on active tab
  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatInterface userType="patient" />;
      
      case 'appointments':
        return (
          <div className="tab-content">
            <div className="content-header">
              <h2>My Appointments</h2>
              <button 
                className="btn-primary"
                onClick={() => setShowAppointmentModal(true)}
              >
                <Plus size={16} />
                Book New Appointment
              </button>
            </div>
            <div className="appointments-section">
              {upcomingAppointments.map(appointment => (
                <div key={appointment.id} className="appointment-card detailed">
                  <div className="appointment-main">
                    <div className="appointment-header">
                      <h3>{appointment.doctor}</h3>
                      <span className={`appointment-status ${appointment.status}`}>
                        {appointment.status}
                      </span>
                    </div>
                    <p className="appointment-department">{appointment.department}</p>
                    <div className="appointment-details">
                      <div className="detail">
                        <Calendar size={16} />
                        <span>{appointment.date}</span>
                      </div>
                      <div className="detail">
                        <Clock size={16} />
                        <span>{appointment.time}</span>
                      </div>
                      <div className="detail">
                        <MapPin size={16} />
                        <span>{appointment.location}</span>
                      </div>
                    </div>
                    <p className="appointment-type">Type: {appointment.type}</p>
                  </div>
                  <div className="appointment-actions">
                    <button className="btn-secondary">Reschedule</button>
                    <button className="btn-text">Cancel</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'medical-history':
        return (
          <div className="tab-content">
            <div className="content-header">
              <h2>Medical History</h2>
              <button className="btn-text">
                <Download size={16} />
                Export Records
              </button>
            </div>
            <div className="medical-history-section">
              {medicalHistory.map(record => (
                <div key={record.id} className="medical-record">
                  <div className="record-header">
                    <div className="record-date">{record.date}</div>
                    <div className="record-department">{record.department}</div>
                  </div>
                  <div className="record-content">
                    <h4>Dr. {record.doctor}</h4>
                    <p className="record-diagnosis">{record.diagnosis}</p>
                    <p className="record-notes">{record.notes}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'prescriptions':
        return (
          <div className="tab-content">
            <div className="content-header">
              <h2>Current Prescriptions</h2>
              <button className="btn-text">
                <Download size={16} />
                Export List
              </button>
            </div>
            <div className="prescriptions-section">
              {prescriptions.map(prescription => (
                <div key={prescription.id} className="prescription-card">
                  <div className="prescription-header">
                    <h3>{prescription.medication}</h3>
                    <span className="prescription-status active">Active</span>
                  </div>
                  <div className="prescription-details">
                    <div className="detail">
                      <strong>Dosage:</strong> {prescription.dosage}
                    </div>
                    <div className="detail">
                      <strong>Frequency:</strong> {prescription.frequency}
                    </div>
                    <div className="detail">
                      <strong>Prescribed by:</strong> {prescription.prescribedBy}
                    </div>
                    <div className="detail">
                      <strong>Valid until:</strong> {prescription.endDate}
                    </div>
                  </div>
                  <div className="prescription-instructions">
                    <strong>Instructions:</strong> {prescription.instructions}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      
      default: // dashboard
        return (
          <div className="tab-content">
            {/* Welcome Section */}
            <div className="welcome-section">
              <h2>Welcome back, {patientInfo.name}!</h2>
              <p>Here's your healthcare overview for today.</p>
            </div>

            {/* Quick Actions */}
            <div className="quick-actions-section">
              <h3>Quick Actions</h3>
              <div className="quick-actions-grid">
                {quickActions.map((action, index) => (
                  <button
                    key={index}
                    className="quick-action-card"
                    onClick={action.action}
                    style={{ '--action-color': action.color }}
                  >
                    <div className="action-icon">
                      <action.icon size={24} />
                    </div>
                    <div className="action-content">
                      <h4>{action.label}</h4>
                      <p>{action.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Content Grid */}
            <div className="content-grid">
              {/* Upcoming Appointments */}
              <div className="content-card">
                <div className="card-header">
                  <h3>Upcoming Appointments</h3>
                  <button 
                    className="btn-text"
                    onClick={() => setActiveTab('appointments')}
                  >
                    View All
                  </button>
                </div>
                <div className="appointments-list">
                  {upcomingAppointments.slice(0, 2).map(appointment => (
                    <div key={appointment.id} className="appointment-item">
                      <div className="appointment-info">
                        <h4>{appointment.doctor}</h4>
                        <p>{appointment.department}</p>
                        <div className="appointment-meta">
                          <span>{appointment.date}</span>
                          <span>{appointment.time}</span>
                        </div>
                      </div>
                      <span className={`appointment-status ${appointment.status}`}>
                        {appointment.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Vital Signs */}
              <div className="content-card">
                <div className="card-header">
                  <h3>Vital Signs</h3>
                  <span className="last-updated">Last: {vitalSigns.lastUpdated}</span>
                </div>
                <div className="vital-signs-grid">
                  <div className="vital-item">
                    <Activity className="vital-icon" />
                    <div className="vital-info">
                      <span className="vital-label">Blood Pressure</span>
                      <span className="vital-value">{vitalSigns.bloodPressure}</span>
                    </div>
                  </div>
                  <div className="vital-item">
                    <Heart className="vital-icon" />
                    <div className="vital-info">
                      <span className="vital-label">Heart Rate</span>
                      <span className="vital-value">{vitalSigns.heartRate}</span>
                    </div>
                  </div>
                  <div className="vital-item">
                    <Stethoscope className="vital-icon" />
                    <div className="vital-info">
                      <span className="vital-label">Temperature</span>
                      <span className="vital-value">{vitalSigns.temperature}</span>
                    </div>
                  </div>
                  <div className="vital-item">
                    <User className="vital-icon" />
                    <div className="vital-info">
                      <span className="vital-label">Weight</span>
                      <span className="vital-value">{vitalSigns.weight}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Current Prescriptions */}
              <div className="content-card">
                <div className="card-header">
                  <h3>Current Prescriptions</h3>
                  <button 
                    className="btn-text"
                    onClick={() => setActiveTab('prescriptions')}
                  >
                    View All
                  </button>
                </div>
                <div className="prescriptions-list">
                  {prescriptions.slice(0, 2).map(prescription => (
                    <div key={prescription.id} className="prescription-item">
                      <Pill size={16} className="prescription-icon" />
                      <div className="prescription-info">
                        <h4>{prescription.medication}</h4>
                        <p>{prescription.dosage} • {prescription.frequency}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Patient Summary */}
              <div className="content-card">
                <div className="card-header">
                  <h3>Patient Summary</h3>
                </div>
                <div className="patient-summary">
                  <div className="summary-item">
                    <span className="label">Patient ID:</span>
                    <span className="value">{patientInfo.id}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Age:</span>
                    <span className="value">{patientInfo.age} years</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Blood Type:</span>
                    <span className="value">{patientInfo.bloodType}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Primary Doctor:</span>
                    <span className="value">{patientInfo.primaryDoctor}</span>
                  </div>
                  <div className="summary-item">
                    <span className="label">Last Visit:</span>
                    <span className="value">{patientInfo.lastVisit}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Emergency Contact */}
            <div className="emergency-section">
              <div className="emergency-alert">
                <AlertCircle size={20} />
                <div className="emergency-content">
                  <h4>Emergency Contact</h4>
                  <p>In case of emergency, contact your healthcare provider immediately</p>
                  <button className="emergency-btn" onClick={handleEmergencyContact}>
                    View Emergency Contacts
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="patient-portal">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <Stethoscope size={24} />
            <span>VitalAI Patient</span>
          </div>
          <button 
            className="close-sidebar"
            onClick={() => setSidebarOpen(false)}
          >
            ×
          </button>
        </div>

        <div className="patient-profile">
          <div className="patient-avatar">
            <User size={32} />
          </div>
          <div className="patient-info">
            <h3>{patientInfo.name}</h3>
            <p>Patient ID: {patientInfo.id}</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <User size={20} />
            Dashboard
          </button>
          <button 
            className={`nav-item ${activeTab === 'appointments' ? 'active' : ''}`}
            onClick={() => setActiveTab('appointments')}
          >
            <Calendar size={20} />
            Appointments
          </button>
          <button 
            className={`nav-item ${activeTab === 'medical-history' ? 'active' : ''}`}
            onClick={() => setActiveTab('medical-history')}
          >
            <History size={20} />
            Medical History
          </button>
          <button 
            className={`nav-item ${activeTab === 'prescriptions' ? 'active' : ''}`}
            onClick={() => setActiveTab('prescriptions')}
          >
            <Pill size={20} />
            Prescriptions
          </button>
          <button 
            className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageCircle size={20} />
            Chat with VitalAI
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="language-section">
            <LanguageSelector
              selectedLanguage={selectedLanguage}
              onLanguageChange={setSelectedLanguage}
            />
          </div>
          <button className="nav-item">
            <Settings size={20} />
            Settings
          </button>
          <button className="nav-item logout" onClick={logout}>
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Top Bar */}
        <div className="top-bar">
          <div className="top-bar-left">
            <button 
              className="menu-btn"
              onClick={() => setSidebarOpen(true)}
            >
              ☰
            </button>
            <h1>
              {activeTab === 'dashboard' && 'Patient Dashboard'}
              {activeTab === 'appointments' && 'My Appointments'}
              {activeTab === 'medical-history' && 'Medical History'}
              {activeTab === 'prescriptions' && 'Prescriptions'}
              {activeTab === 'chat' && 'Chat with VitalAI'}
            </h1>
          </div>

          <div className="top-bar-right">
            <button className="notification-btn">
              <Bell size={20} />
              <span className="notification-badge">2</span>
            </button>
            <div className="user-profile">
              <div className="user-avatar">
                <User size={20} />
              </div>
              <div className="user-info">
                <span className="user-name">{patientInfo.name}</span>
                <span className="user-role">Patient</span>
              </div>
            </div>
          </div>
        </div>

        {/* Page Content */}
        <div className="page-content">
          {renderContent()}
        </div>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div 
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Modals */}
      {showAppointmentModal && (
        <AppointmentScheduler
          onSchedule={handleAppointmentSchedule}
          onClose={() => setShowAppointmentModal(false)}
        />
      )}

      {showFileUploadModal && (
        <FileUpload
          onFileUpload={handleFileUpload}
          onClose={() => setShowFileUploadModal(false)}
        />
      )}
    </div>
  );
};

export default PatientPortal;