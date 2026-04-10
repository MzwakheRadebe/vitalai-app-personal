/**
 * Staff Dashboard
 *
 * Purpose: Healthcare staff (nurses, receptionists, clinicians) use this to:
 *  - Monitor and respond to patient chat sessions / triage severity
 *  - View and manage all booked appointments
 *  - See real patient data from the live database
 *
 * Staff accounts exist so that qualified healthcare workers can:
 *  - Review AI triage decisions before escalating urgent cases
 *  - Manage the appointment schedule
 *  - Access the chat interface to assist patients directly
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar, MessageCircle, LogOut, RefreshCw,
  User, Clock, Stethoscope, AlertTriangle, CheckCircle, ArrowLeft
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import ChatInterface from '../components/ChatInterface';
import { appointmentsAPI } from '../services/api';
import './StaffDashboard.css';

const SEVERITY_COLOR = {
  CRITICAL: { bg: '#fef2f2', text: '#dc2626', border: '#fca5a5' },
  HIGH:     { bg: '#fff7ed', text: '#ea580c', border: '#fdba74' },
  MEDIUM:   { bg: '#fffbeb', text: '#d97706', border: '#fcd34d' },
  LOW:      { bg: '#f0fdf4', text: '#16a34a', border: '#86efac' },
};

const StaffDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('appointments');
  const [appointments, setAppointments] = useState([]);
  const [loadingAppts, setLoadingAppts] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const loadAppointments = async () => {
    setLoadingAppts(true);
    try {
      const data = await appointmentsAPI.list();
      setAppointments(data);
    } catch {
      setAppointments([]);
    } finally {
      setLoadingAppts(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'appointments') loadAppointments();
  }, [activeTab]);

  const name = user?.name || user?.email?.split('@')[0] || 'Staff';

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', display: 'flex', flexDirection: 'column' }}>

      {/* Top bar */}
      <div style={{
        background: '#fff', borderBottom: '1px solid #e5e7eb',
        padding: '12px 20px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => navigate('/')}
            style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              background: 'none', border: 'none', cursor: 'pointer',
              color: '#6b7280', fontSize: '13px', padding: '4px 8px', borderRadius: '6px',
            }}
          >
            <ArrowLeft size={14} /> Home
          </button>
          <span style={{ color: '#d1d5db' }}>|</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Stethoscope size={20} color="#667eea" />
            <span style={{ fontWeight: 700, color: '#1f2937', fontSize: '16px' }}>Staff Portal</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '50%',
              background: '#667eea', display: 'flex', alignItems: 'center',
              justifyContent: 'center', color: '#fff', fontSize: '14px', fontWeight: 600,
            }}>
              {name[0].toUpperCase()}
            </div>
            <div style={{ lineHeight: 1.3 }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#1f2937' }}>{name}</div>
              <div style={{ fontSize: '11px', color: '#667eea', fontWeight: 500 }}>Staff</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: 'none', border: '1px solid #e5e7eb', cursor: 'pointer',
              color: '#6b7280', fontSize: '13px', padding: '6px 12px', borderRadius: '6px',
            }}
          >
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{
        background: '#fff', borderBottom: '1px solid #e5e7eb',
        display: 'flex', gap: '0', padding: '0 20px',
      }}>
        {[
          { id: 'appointments', label: 'Appointments', icon: Calendar },
          { id: 'chat', label: 'Patient Chat Monitor', icon: MessageCircle },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '14px 20px', background: 'none', border: 'none',
              cursor: 'pointer', fontSize: '14px', fontWeight: activeTab === id ? 600 : 400,
              color: activeTab === id ? '#667eea' : '#6b7280',
              borderBottom: activeTab === id ? '2px solid #667eea' : '2px solid transparent',
              transition: 'all 0.15s',
            }}
          >
            <Icon size={16} /> {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'hidden' }}>

        {/* ── Appointments tab ── */}
        {activeTab === 'appointments' && (
          <div style={{ padding: '24px 20px', maxWidth: '900px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: '#1f2937' }}>
                All Appointments
              </h2>
              <button
                onClick={loadAppointments}
                style={{
                  display: 'flex', alignItems: 'center', gap: '6px',
                  background: '#667eea', color: '#fff', border: 'none',
                  padding: '8px 14px', borderRadius: '8px', cursor: 'pointer',
                  fontSize: '13px', fontWeight: 500,
                }}
              >
                <RefreshCw size={14} /> Refresh
              </button>
            </div>

            {loadingAppts ? (
              <div style={{ textAlign: 'center', color: '#9ca3af', padding: '48px 0' }}>Loading appointments…</div>
            ) : appointments.length === 0 ? (
              <div style={{
                textAlign: 'center', padding: '48px 24px',
                background: '#fff', borderRadius: '12px', border: '1px solid #e5e7eb',
              }}>
                <Calendar size={40} color="#d1d5db" style={{ marginBottom: '12px' }} />
                <p style={{ color: '#6b7280', margin: 0 }}>No appointments booked yet.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {appointments.map(appt => (
                  <div key={appt.id} style={{
                    background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px',
                    padding: '16px 20px', display: 'flex', alignItems: 'center',
                    justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <div style={{
                        width: '40px', height: '40px', borderRadius: '50%',
                        background: '#f0f0ff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        <User size={18} color="#667eea" />
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, color: '#1f2937', fontSize: '15px' }}>
                          {appt.patient_name}
                        </div>
                        <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '2px' }}>
                          {appt.department || 'General'} · {appt.clinician}
                        </div>
                        {appt.reason && (
                          <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '2px', fontStyle: 'italic' }}>
                            Reason: {appt.reason}
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#4b5563', fontSize: '13px', fontWeight: 500 }}>
                        <Clock size={13} />
                        {new Date(appt.starts_at).toLocaleDateString('en-ZA', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </div>
                      <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '3px' }}>
                        {new Date(appt.starts_at).toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit' })} –{' '}
                        {new Date(appt.ends_at).toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                      <div style={{
                        display: 'inline-flex', alignItems: 'center', gap: '4px',
                        marginTop: '6px', padding: '3px 8px', borderRadius: '20px',
                        background: '#f0fdf4', color: '#16a34a', fontSize: '11px', fontWeight: 600,
                      }}>
                        <CheckCircle size={11} /> Booked
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Chat monitor tab ── */}
        {activeTab === 'chat' && (
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{
              padding: '12px 20px', background: '#fffbeb',
              borderBottom: '1px solid #fde68a', display: 'flex', alignItems: 'center', gap: '8px',
            }}>
              <AlertTriangle size={16} color="#d97706" />
              <span style={{ fontSize: '13px', color: '#92400e' }}>
                <strong>Staff view:</strong> Use this to assist patients directly or test triage responses. All conversations use the live AI system.
              </span>
            </div>
            <div style={{ flex: 1, overflow: 'hidden' }}>
              <ChatInterface userType="staff" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StaffDashboard;
