import React, { useState } from 'react';
import { 
  BarChart3, Users, Calendar, FileText, MessageCircle, 
  Settings, LogOut, Bell, Search, Filter,
  TrendingUp, Clock, AlertTriangle, Download,
  Eye, Edit, Trash2, MoreVertical
} from 'lucide-react';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Mock data for dashboard
  const stats = [
    { label: 'Total Patients', value: '2,847', change: '+12%', trend: 'up', icon: Users },
    { label: 'Appointments Today', value: '156', change: '+8%', trend: 'up', icon: Calendar },
    { label: 'Chat Sessions', value: '423', change: '+15%', trend: 'up', icon: MessageCircle },
    { label: 'Pending Tasks', value: '23', change: '-5%', trend: 'down', icon: FileText }
  ];

  const recentActivities = [
    { id: 1, type: 'appointment', user: 'John Doe', action: 'scheduled appointment', time: '2 min ago', priority: 'low' },
    { id: 2, type: 'chat', user: 'Sarah Wilson', action: 'started emergency chat', time: '5 min ago', priority: 'high' },
    { id: 3, type: 'upload', user: 'Mike Johnson', action: 'uploaded medical document', time: '15 min ago', priority: 'medium' },
    { id: 4, type: 'system', user: 'System', action: 'AI model updated', time: '1 hour ago', priority: 'low' }
  ];

  const appointments = [
    { id: 1, patient: 'John Doe', department: 'Cardiology', time: '09:30 AM', status: 'confirmed', type: 'Follow-up' },
    { id: 2, patient: 'Sarah Wilson', department: 'Pediatrics', time: '10:15 AM', status: 'pending', type: 'New Patient' },
    { id: 3, patient: 'Mike Johnson', department: 'General Practice', time: '11:00 AM', status: 'confirmed', type: 'Consultation' },
    { id: 4, patient: 'Emily Brown', department: 'Dermatology', time: '02:30 PM', status: 'cancelled', type: 'Follow-up' }
  ];

  const systemMetrics = [
    { label: 'AI Accuracy', value: '94.2%', trend: '+2.1%' },
    { label: 'Response Time', value: '1.2s', trend: '-0.3s' },
    { label: 'Uptime', value: '99.8%', trend: '+0.2%' },
    { label: 'User Satisfaction', value: '4.7/5', trend: '+0.2' }
  ];

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return '#6B7280';
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
    <div className="admin-dashboard">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="logo">
            <BarChart3 size={24} />
            <span>VitalAI Admin</span>
          </div>
          <button className="close-sidebar" onClick={() => setSidebarOpen(false)}>
            ×
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
            className={`nav-item ${activeTab === 'chats' ? 'active' : ''}`}
            onClick={() => setActiveTab('chats')}
          >
            <MessageCircle size={20} />
            Chat Sessions
          </button>
          <button 
            className={`nav-item ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            <FileText size={20} />
            Reports
          </button>
          <button 
            className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings size={20} />
            Settings
          </button>
        </nav>

        <div className="sidebar-footer">
          <button className="nav-item logout">
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
            <button className="menu-btn" onClick={() => setSidebarOpen(true)}>
              ☰
            </button>
            <h1>Dashboard Overview</h1>
          </div>

          <div className="top-bar-right">
            <div className="search-bar">
              <Search size={18} />
              <input type="text" placeholder="Search..." />
            </div>
            <button className="notification-btn">
              <Bell size={20} />
              <span className="notification-badge">3</span>
            </button>
            <div className="user-profile">
              <div className="user-avatar">AD</div>
              <div className="user-info">
                <span className="user-name">Admin User</span>
                <span className="user-role">Administrator</span>
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="dashboard-content">
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
                <button className="view-all">View All</button>
              </div>
              <div className="activities-list">
                {recentActivities.map(activity => (
                  <div key={activity.id} className="activity-item">
                    <div 
                      className="priority-indicator"
                      style={{ backgroundColor: getPriorityColor(activity.priority) }}
                    ></div>
                    <div className="activity-content">
                      <div className="activity-main">
                        <span className="user">{activity.user}</span>
                        <span className="action">{activity.action}</span>
                      </div>
                      <span className="activity-time">{activity.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Today's Appointments */}
            <div className="content-card">
              <div className="card-header">
                <h3>Today's Appointments</h3>
                <Filter size={18} />
              </div>
              <div className="appointments-list">
                {appointments.map(appointment => (
                  <div key={appointment.id} className="appointment-item">
                    <div className="appointment-info">
                      <h4>{appointment.patient}</h4>
                      <p>{appointment.department} • {appointment.type}</p>
                      <span className="appointment-time">{appointment.time}</span>
                    </div>
                    <div className="appointment-actions">
                      <span 
                        className="appointment-status"
                        style={{ color: getStatusColor(appointment.status) }}
                      >
                        {appointment.status}
                      </span>
                      <button className="action-btn">
                        <MoreVertical size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* System Metrics */}
            <div className="content-card">
              <div className="card-header">
                <h3>System Performance</h3>
                <Download size={18} />
              </div>
              <div className="metrics-list">
                {systemMetrics.map((metric, index) => (
                  <div key={index} className="metric-item">
                    <div className="metric-info">
                      <span className="metric-label">{metric.label}</span>
                      <span className="metric-value">{metric.value}</span>
                    </div>
                    <span className={`metric-trend ${metric.trend.startsWith('+') ? 'positive' : 'negative'}`}>
                      {metric.trend}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="content-card">
              <div className="card-header">
                <h3>Quick Actions</h3>
              </div>
              <div className="quick-actions-grid">
                <button className="quick-action">
                  <Users size={20} />
                  <span>Manage Patients</span>
                </button>
                <button className="quick-action">
                  <Calendar size={20} />
                  <span>Schedule Appointment</span>
                </button>
                <button className="quick-action">
                  <MessageCircle size={20} />
                  <span>View Chats</span>
                </button>
                <button className="quick-action">
                  <FileText size={20} />
                  <span>Generate Report</span>
                </button>
                <button className="quick-action">
                  <Settings size={20} />
                  <span>System Settings</span>
                </button>
                <button className="quick-action">
                  <BarChart3 size={20} />
                  <span>Analytics</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)}></div>
      )}
    </div>
  );
};

export default AdminDashboard;