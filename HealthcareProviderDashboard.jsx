import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users, Activity, Heart, AlertTriangle, Calendar, FileText,
  TrendingUp, TrendingDown, Clock, MessageSquare, Phone,
  Video, Shield, Settings, Search, Filter, Download,
  UserCheck, AlertCircle, CheckCircle, BarChart3,
  Brain, Pill, Stethoscope, Hospital, ChevronRight,
  Bell, Email, Smartphone, Plus, Edit, Eye
} from 'lucide-react';

const HealthcareProviderDashboard = ({ providerInfo, patients = [] }) => {
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [notifications, setNotifications] = useState([]);
  const [appointments, setAppointments] = useState([]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'patients', label: 'Patients', icon: Users },
    { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'messages', label: 'Messages', icon: MessageSquare }
  ];

  useEffect(() => {
    loadPatientData();
    loadNotifications();
    loadAppointments();
  }, []);

  const loadPatientData = async () => {
    // Load patient data from API
  };

  const loadNotifications = async () => {
    // Mock notifications for demo
    setNotifications([
      {
        id: 1,
        type: 'urgent',
        patient: 'John Doe',
        message: 'Critical stress level detected',
        time: '2 hours ago',
        read: false
      },
      {
        id: 2,
        type: 'warning',
        patient: 'Jane Smith',
        message: 'Missed medication adherence check',
        time: '5 hours ago',
        read: false
      },
      {
        id: 3,
        type: 'info',
        patient: 'System',
        message: 'Weekly patient report ready',
        time: '1 day ago',
        read: true
      }
    ]);
  };

  const loadAppointments = async () => {
    // Mock appointments for demo
    const today = new Date();
    setAppointments([
      {
        id: 1,
        patient: 'John Doe',
        time: '9:00 AM',
        type: 'video',
        duration: '30 min',
        status: 'confirmed'
      },
      {
        id: 2,
        patient: 'Jane Smith',
        time: '10:30 AM',
        type: 'in-person',
        duration: '45 min',
        status: 'confirmed'
      },
      {
        id: 3,
        patient: 'Robert Johnson',
        time: '2:00 PM',
        type: 'phone',
        duration: '20 min',
        status: 'pending'
      }
    ]);
  };

  const getFilteredPatients = () => {
    return patients.filter(patient => {
      const matchesSearch = patient.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           patient.email.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesFilter = filterStatus === 'all' || patient.status === filterStatus;
      return matchesSearch && matchesFilter;
    });
  };

  const getPatientRiskLevel = (patient) => {
    const score = patient.wellnessScore || 0;
    if (score < 40) return { level: 'high', color: 'red', label: 'High Risk' };
    if (score < 60) return { level: 'medium', color: 'yellow', label: 'Medium Risk' };
    return { level: 'low', color: 'green', label: 'Low Risk' };
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Total Patients', value: patients.length, icon: Users, color: '#3b82f6', trend: '+2 this week' },
          { label: 'High Risk', value: patients.filter(p => getPatientRiskLevel(p).level === 'high').length, icon: AlertTriangle, color: '#ef4444', trend: '-1 this week' },
          { label: 'Appointments Today', value: appointments.filter(a => a.status === 'confirmed').length, icon: Calendar, color: '#10b981', trend: '4 scheduled' },
          { label: 'Pending Reviews', value: notifications.filter(n => !n.read).length, icon: MessageSquare, color: '#f59e0b', trend: 'Need attention' }
        ].map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + index * 0.1 }}
            className="bg-white rounded-xl shadow-sm p-6 border border-gray-100"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 rounded-lg" style={{ backgroundColor: `${metric.color}20` }}>
                <metric.icon className="h-5 w-5" style={{ color: metric.color }} />
              </div>
              <span className="text-sm text-green-600 font-medium">{metric.trend}</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{metric.value}</div>
            <div className="text-sm text-gray-600 mt-1">{metric.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Recent Alerts */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="bg-white rounded-xl shadow-sm p-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Alerts</h3>
        <div className="space-y-3">
          {notifications.slice(0, 3).map(notification => (
            <div key={notification.id} className="flex items-start space-x-3 p-3 rounded-lg border border-gray-200">
              <div className={`p-2 rounded-lg ${
                notification.type === 'urgent' ? 'bg-red-100' :
                notification.type === 'warning' ? 'bg-yellow-100' : 'bg-blue-100'
              }`}>
                {notification.type === 'urgent' ? (
                  <AlertCircle className="h-4 w-4 text-red-600" />
                ) : notification.type === 'warning' ? (
                  <AlertTriangle className="h-4 w-4 text-yellow-600" />
                ) : (
                  <Bell className="h-4 w-4 text-blue-600" />
                )}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{notification.message}</p>
                <p className="text-xs text-gray-500 mt-1">{notification.patient} • {notification.time}</p>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Today's Schedule */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="bg-white rounded-xl shadow-sm p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Today's Schedule</h3>
          <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">View All</button>
        </div>
        <div className="space-y-3">
          {appointments.map(appointment => (
            <div key={appointment.id} className="flex items-center justify-between p-3 rounded-lg border border-gray-200">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${
                  appointment.type === 'video' ? 'bg-blue-100' :
                  appointment.type === 'phone' ? 'bg-green-100' : 'bg-purple-100'
                }`}>
                  {appointment.type === 'video' ? (
                    <Video className="h-4 w-4 text-blue-600" />
                  ) : appointment.type === 'phone' ? (
                    <Phone className="h-4 w-4 text-green-600" />
                  ) : (
                    <Stethoscope className="h-4 w-4 text-purple-600" />
                  )}
                </div>
                <div>
                  <p className="font-medium text-gray-900">{appointment.patient}</p>
                  <p className="text-sm text-gray-500">{appointment.time} • {appointment.duration}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  appointment.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                  appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {appointment.status}
                </span>
                <button className="p-1 hover:bg-gray-100 rounded">
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );

  const renderPatientsTab = () => {
    const filteredPatients = getFilteredPatients();

    return (
      <div className="space-y-6">
        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search patients..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="high-risk">High Risk</option>
          </select>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Add Patient</span>
          </button>
        </div>

        {/* Patients Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPatients.map((patient, index) => {
            const risk = getPatientRiskLevel(patient);

            return (
              <motion.div
                key={patient.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + index * 0.1 }}
                className="bg-white rounded-xl shadow-sm p-6 border border-gray-100 cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setSelectedPatient(patient)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
                      <UserCheck className="h-6 w-6 text-gray-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{patient.name}</h3>
                      <p className="text-sm text-gray-600">{patient.age} years • {patient.condition}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    risk.level === 'high' ? 'bg-red-100 text-red-800' :
                    risk.level === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                  }`}>
                    {risk.label}
                  </span>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Wellness Score</span>
                    <span className="font-semibold text-gray-900">{patient.wellnessScore || 0}/100</span>
                  </div>

                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all duration-500"
                      style={{
                        width: `${patient.wellnessScore || 0}%`,
                        backgroundColor: risk.level === 'high' ? '#ef4444' :
                                       risk.level === 'medium' ? '#f59e0b' : '#10b981'
                      }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Last check-in</span>
                    <span className="text-gray-900">{patient.lastCheckIn || '2 days ago'}</span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Medication Adherence</span>
                    <span className={`font-medium ${
                      (patient.medicationAdherence || 0) >= 80 ? 'text-green-600' :
                      (patient.medicationAdherence || 0) >= 60 ? 'text-yellow-600' : 'text-red-600'
                    }`}>
                      {patient.medicationAdherence || 0}%
                    </span>
                  </div>
                </div>

                <div className="mt-4 flex items-center space-x-2">
                  <button className="flex-1 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 flex items-center justify-center space-x-1">
                    <Eye className="h-4 w-4" />
                    <span>View Details</span>
                  </button>
                  <button className="p-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
                    <MessageSquare className="h-4 w-4" />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderPatientDetailModal = () => {
    if (!selectedPatient) return null;

    const risk = getPatientRiskLevel(selectedPatient);

    return (
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedPatient(null)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center">
                    <UserCheck className="h-8 w-8 text-gray-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{selectedPatient.name}</h2>
                    <p className="text-gray-600">{selectedPatient.age} years • {selectedPatient.condition}</p>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mt-1 ${
                      risk.level === 'high' ? 'bg-red-100 text-red-800' :
                      risk.level === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {risk.label}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedPatient(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Health Metrics */}
                <div className="lg:col-span-2 space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Health Metrics</h3>
                    <div className="grid grid-cols-2 gap-4">
                      {[
                        { label: 'Blood Pressure', value: '120/80', unit: 'mmHg', icon: Heart },
                        { label: 'Heart Rate', value: '72', unit: 'bpm', icon: Activity },
                        { label: 'Blood Sugar', value: '95', unit: 'mg/dL', icon: Activity },
                        { label: 'Weight', value: '165', unit: 'lbs', icon: Activity }
                      ].map((metric) => (
                        <div key={metric.label} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center space-x-2 mb-2">
                            <metric.icon className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">{metric.label}</span>
                          </div>
                          <div className="text-2xl font-bold text-gray-900">
                            {metric.value}
                            <span className="text-sm font-normal text-gray-500 ml-1">{metric.unit}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h3>
                    <div className="space-y-3">
                      {[
                        { date: 'Today', activity: 'Morning medication taken', status: 'completed' },
                        { date: 'Yesterday', activity: 'Evening walk - 30 minutes', status: 'completed' },
                        { date: '2 days ago', activity: 'Missed blood pressure check', status: 'missed' },
                        { date: '3 days ago', activity: 'Telehealth appointment', status: 'completed' }
                      ].map((activity, index) => (
                        <div key={index} className="flex items-center space-x-3 p-3 rounded-lg border border-gray-200">
                          <div className={`w-2 h-2 rounded-full ${
                            activity.status === 'completed' ? 'bg-green-500' : 'bg-red-500'
                          }`} />
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">{activity.activity}</p>
                            <p className="text-xs text-gray-500">{activity.date}</p>
                          </div>
                          {activity.status === 'completed' ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <XCircle className="h-4 w-4 text-red-600" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>

                  <button className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center space-x-2">
                    <MessageSquare className="h-4 w-4" />
                    <span>Send Message</span>
                  </button>

                  <button className="w-full py-3 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center space-x-2">
                    <Video className="h-4 w-4" />
                    <span>Schedule Video Call</span>
                  </button>

                  <button className="w-full py-3 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center space-x-2">
                    <Pill className="h-4 w-4" />
                    <span>Update Medications</span>
                  </button>

                  <button className="w-full py-3 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center space-x-2">
                    <FileText className="h-4 w-4" />
                    <span>View Full Report</span>
                  </button>

                  <button className="w-full py-3 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center space-x-2">
                    <Download className="h-4 w-4" />
                    <span>Export Data</span>
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </AnimatePresence>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                <Stethoscope className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Healthcare Dashboard</h1>
                <p className="text-gray-600">
                  Dr. {providerInfo?.name || 'Smith'} • {providerInfo?.specialty || 'General Practice'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Bell className="h-5 w-5 text-gray-600 cursor-pointer" />
                {notifications.filter(n => !n.read).length > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {notifications.filter(n => !n.read).length}
                  </span>
                )}
              </div>
              <button className="p-2 hover:bg-gray-100 rounded-lg">
                <Settings className="h-5 w-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'patients' && renderPatientsTab()}
        {activeTab === 'alerts' && (
          <div className="text-center py-12">
            <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Alerts Management</h3>
            <p className="text-gray-600">Comprehensive alert system coming soon</p>
          </div>
        )}
        {activeTab === 'schedule' && (
          <div className="text-center py-12">
            <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Schedule Management</h3>
            <p className="text-gray-600">Advanced scheduling features coming soon</p>
          </div>
        )}
        {activeTab === 'analytics' && (
          <div className="text-center py-12">
            <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Analytics Dashboard</h3>
            <p className="text-gray-600">Population health analytics coming soon</p>
          </div>
        )}
        {activeTab === 'messages' && (
          <div className="text-center py-12">
            <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Patient Messages</h3>
            <p className="text-gray-600">Secure messaging platform coming soon</p>
          </div>
        )}
      </div>

      {renderPatientDetailModal()}
    </div>
  );
};

export default HealthcareProviderDashboard;
