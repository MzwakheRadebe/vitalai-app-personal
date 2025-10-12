import React, { useState } from 'react';
import { 
  BarChart3, Users, Calendar, FileText, 
  Bell, Settings, LogOut, Menu, X,
  TrendingUp, Clock, AlertTriangle
} from 'lucide-react';
import './Dashboard.css';

const Dashboard = ({ user, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Mock data
  const stats = [
    { label: 'Total Patients', value: '1,247', icon: Users, change: '+12%', trend: 'up' },
    { label: 'Appointments Today', value: '34', icon: Calendar, change: '+5%', trend: 'up' },
    { label: 'Pending Tasks', value: '8', icon: FileText, change: '-2%', trend: 'down' },
    { label: 'AI Accuracy', value: '94%', icon: BarChart3, change: '+3%', trend: 'up' }
  ];

  const recentActivities = [
    { id: 1, type: 'appointment', message: 'New appointment scheduled with Dr. Smith', time: '2 min ago' },
    { id: 2, type: 'chat', message: 'Patient consultation completed via chat', time: '15 min ago' },
    { id: 3, type: 'upload', message: 'Medical document uploaded by patient', time: '1 hour ago' },
    { id: 4, type: 'emergency', message: 'Emergency triage case handled', time: '2 hours ago' }
  ];

  const upcomingAppointments = [
    { id: 1, patient: 'John Doe', time: '09:30 AM', department: 'General Practice', status: 'confirmed' },
    { id: 2, patient: 'Sarah Wilson', time: '10:15 AM', department: 'Pediatrics', status: 'confirmed' },
    { id: 3, patient: 'Mike Johnson', time: '11:00 AM', department: 'Cardiology', status: 'pending' }
  ];

  const getActivityIcon = (type) => {
    switch (type) {
      case 'appointment': return Calendar;
      case 'chat': return Users;
      case 'upload': return FileText;
      case 'emergency': return AlertTriangle;
      default: return Bell;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed': return '#10B981';
      case 'pending': return '#F59E0B';
      case 'cancelled': return '#EF4444';
      default: return '#6B7280';
    }
  };

  return (
    <div className="dashboard">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <BarChart3 size={24} />
            <span>VitalAI Dashboard</span>
          </div>
          <button className="close-sidebar" onClick={() => setSidebarOpen(false)}>
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <BarChart3 size={20} />
            Overview
          </button>
          <button 
            className={`nav-item ${activeTab === 'patients' ? 'active' : ''}`}
            onClick={() => setActiveTab('patients')}
          >
            <Users size={20} />
            Patients
          </button>
          <button 
            className={`nav-item ${activeTab === 'appointments' ? 'active' : ''}`}
            onClick={() => setActiveTab('appointments')}
          >
            <Calendar size={20} />
            Appointments
          </button>
          <button 
            className={`nav-item ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            <FileText size={20} />
            Reports
          </button>
        </nav>

        <div className="sidebar-footer">
          <button className="nav-item">
            <Settings size={20} />
            Settings
          </button>
          <button className="nav-item logout" onClick={onLogout}>
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Top Bar */}
        <div className="top-bar">
          <button className="menu-btn" onClick={() => setSidebarOpen(true)}>
            <Menu size={20} />
          </button>

          <div className="top-bar-right">
            <button className="notification-btn">
              <Bell size={20} />
              <span className="notification-badge">3</span>
            </button>

            <div className="user-profile">
              <img src={user.avatar} alt={user.name} className="user-avatar" />
              <div className="user-info">
                <span className="user-name">{user.name}</span>
                <span className="user-role">{user.userType}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="dashboard-content">
          <div className="content-header">
            <h1>Dashboard Overview</h1>
            <p>Welcome back, {user.name}. Here's what's happening today.</p>
          </div>

          {/* Stats Grid */}
          <div className="stats-grid">
            {stats.map((stat, index) => (
              <div key={index} className="stat-card">
                <div className="stat-header">
                  <stat.icon size={24} className="stat-icon" />
                  <span className={`trend ${stat.trend}`}>
                    <TrendingUp size={14} />
                    {stat.change}
                  </span>
                </div>
                <div className="stat-content">
                  <h3>{stat.value}</h3>
                  <p>{stat.label}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Content Grid */}
          <div className="content-grid">
            {/* Recent Activities */}
            <div className="content-card">
              <div className="card-header">
                <h3>Recent Activities</h3>
                <Clock size={18} />
              </div>
              <div className="activities-list">
                {recentActivities.map(activity => {
                  const Icon = getActivityIcon(activity.type);
                  return (
                    <div key={activity.id} className="activity-item">
                      <div className="activity-icon">
                        <Icon size={16} />
                      </div>
                      <div className="activity-content">
                        <p>{activity.message}</p>
                        <span>{activity.time}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Upcoming Appointments */}
            <div className="content-card">
              <div className="card-header">
                <h3>Upcoming Appointments</h3>
                <Calendar size={18} />
              </div>
              <div className="appointments-list">
                {upcomingAppointments.map(appointment => (
                  <div key={appointment.id} className="appointment-item">
                    <div className="appointment-info">
                      <h4>{appointment.patient}</h4>
                      <p>{appointment.department} • {appointment.time}</p>
                    </div>
                    <span 
                      className="appointment-status"
                      style={{ color: getStatusColor(appointment.status) }}
                    >
                      {appointment.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Overlay */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)}></div>
      )}
    </div>
  );
};

export default Dashboard;