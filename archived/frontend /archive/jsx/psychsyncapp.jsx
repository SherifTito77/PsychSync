// App.js - Main React Application
// import React, { useState, useEffect } from 'react';

import React, { useState, useEffect, createContext, useContext } from 'react';


import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
// import { TeamProvider } from './contexts/TeamContext';
import { NotificationProvider } from './contexts/NotificationContext';



// Import components
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import Dashboard from './components/Dashboard/Dashboard';
import TeamManagement from './components/Teams/TeamManagement';
import AssessmentCenter from './components/Assessments/AssessmentCenter';
import TeamOptimizer from './components/Optimizer/TeamOptimizer';
import Analytics from './components/Analytics/Analytics';
import Settings from './components/Settings/Settings';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import LoadingSpinner from './components/UI/LoadingSpinner';
import NotificationContainer from './components/UI/NotificationContainer';

// Import styles
import './App.css';
import './styles/tailwind.css';

function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <TeamProvider>
          <Router>
            <div className="app">
              <AppContent />
            </div>
          </Router>
        </TeamProvider>
      </NotificationProvider>
    </AuthProvider>
  );
}

function AppContent() {
  const { user, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className={`flex-1 flex flex-col transition-all duration-300 ${
        sidebarOpen ? 'ml-64' : 'ml-16'
      }`}>
        <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />
        
        <main className="flex-1 p-6 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/teams/*" element={<TeamManagement />} />
            <Route path="/assessments/*" element={<AssessmentCenter />} />
            <Route path="/optimizer" element={<TeamOptimizer />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
      
      <NotificationContainer />
    </div>
  );
}

export default App;

// contexts/AuthContext.js - Authentication Context
// import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext();

// export const useAuth = () => {
//   const context = useContext(AuthContext);
//   if (!context) {
//     throw new Error('useAuth must be used within an AuthProvider');
//   }
//   return context;
// };

// export const AuthProvider = ({ children }) => {
//   const [user, setUser] = useState(null);
//   const [isLoading, setIsLoading] = useState(true);

//   useEffect(() => {
//     checkAuthStatus();
//   }, []);

//   const checkAuthStatus = async () => {
//     try {
//       const token = localStorage.getItem('authToken');
//       if (token) {
//         const userData = await authAPI.verifyToken(token);
//         setUser(userData);
//       }
//     } catch (error) {
//       localStorage.removeItem('authToken');
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const login = async (email, password) => {
//     try {
//       const response = await authAPI.login(email, password);
//       const { access_token, user: userData } = response;
      
//       localStorage.setItem('authToken', access_token);
//       setUser(userData);
      
//       return { success: true };
//     } catch (error) {
//       return { 
//         success: false, 
//         error: error.message || 'Login failed' 
//       };
//     }
//   };

//   const register = async (userData) => {
//     try {
//       const response = await authAPI.register(userData);
//       return { success: true, data: response };
//     } catch (error) {
//       return { 
//         success: false, 
//         error: error.message || 'Registration failed' 
//       };
//     }
//   };

//   const logout = () => {
//     localStorage.removeItem('authToken');
//     setUser(null);
//   };

//   const value = {
//     user,
//     isLoading,
//     login,
//     register,
//     logout
//   };

//   return (
//     <AuthContext.Provider value={value}>
//       {children}
//     </AuthContext.Provider>
//   );
// };

// contexts/TeamContext.js - Team Management Context
// import React, { createContext, useContext, useState, useCallback } from 'react';
import { teamAPI } from '../services/api';
import { useNotification } from './NotificationContext';

const TeamContext = createContext();

export const useTeam = () => {
  const context = useContext(TeamContext);
  if (!context) {
    throw new Error('useTeam must be used within a TeamProvider');
  }
  return context;
};

// export const TeamProvider = ({ children }) => {
//   const [teams, setTeams] = useState([]);
//   const [currentTeam, setCurrentTeam] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const { showNotification } = useNotification();

//   const fetchTeams = useCallback(async () => {
//     setLoading(true);
//     try {
//       const teamsData = await teamAPI.getTeams();
//       setTeams(teamsData);
//     } catch (error) {
//       showNotification('Failed to fetch teams', 'error');
//     } finally {
//       setLoading(false);
//     }
//   }, [showNotification]);

//   const createTeam = async (teamData) => {
//     try {
//       const newTeam = await teamAPI.createTeam(teamData);
//       setTeams(prev => [...prev, newTeam]);
//       showNotification('Team created successfully', 'success');
//       return { success: true, team: newTeam };
//     } catch (error) {
//       showNotification('Failed to create team', 'error');
//       return { success: false, error: error.message };
//     }
//   };

//   const updateTeam = async (teamId, updateData) => {
//     try {
//       const updatedTeam = await teamAPI.updateTeam(teamId, updateData);
//       setTeams(prev => prev.map(team => 
//         team.id === teamId ? updatedTeam : team
//       ));
//       if (currentTeam && currentTeam.id === teamId) {
//         setCurrentTeam(updatedTeam);
//       }
//       showNotification('Team updated successfully', 'success');
//       return { success: true, team: updatedTeam };
//     } catch (error) {
//       showNotification('Failed to update team', 'error');
//       return { success: false, error: error.message };
//     }
//   };

//   const deleteTeam = async (teamId) => {
//     try {
//       await teamAPI.deleteTeam(teamId);
//       setTeams(prev => prev.filter(team => team.id !== teamId));
//       if (currentTeam && currentTeam.id === teamId) {
//         setCurrentTeam(null);
//       }
//       showNotification('Team deleted successfully', 'success');
//       return { success: true };
//     } catch (error) {
//       showNotification('Failed to delete team', 'error');
//       return { success: false, error: error.message };
//     }
//   };

//   const selectTeam = (team) => {
//     setCurrentTeam(team);
//   };

//   const value = {
//     teams,
//     currentTeam,
//     loading,
//     fetchTeams,
//     createTeam,
//     updateTeam,
//     deleteTeam,
//     selectTeam
//   };

//   return (
//     <TeamContext.Provider value={value}>
//       {children}
//     </TeamContext.Provider>
//   );
// };

// contexts/NotificationContext.js - Notification System
// import React, { createContext, useContext, useState } from 'react';

const NotificationContext = createContext();

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

// export const NotificationProvider = ({ children }) => {
//   const [notifications, setNotifications] = useState([]);

//   const showNotification = (message, type = 'info', duration = 5000) => {
//     const id = Date.now();
//     const notification = {
//       id,
//       message,
//       type, // 'success', 'error', 'warning', 'info'
//       duration
//     };

//     setNotifications(prev => [...prev, notification]);

//     if (duration > 0) {
//       setTimeout(() => {
//         removeNotification(id);
//       }, duration);
//     }
//   };

//   const removeNotification = (id) => {
//     setNotifications(prev => prev.filter(notif => notif.id !== id));
//   };

//   const value = {
//     notifications,
//     showNotification,
//     removeNotification
//   };

//   return (
//     <NotificationContext.Provider value={value}>
//       {children}
//     </NotificationContext.Provider>
//   );
// };

// components/Dashboard/Dashboard.js - Main Dashboard Component
// import React, { useState, useEffect } from 'react';
 import { useAuth } from '../../contexts/AuthContext';
import { useTeam } from '../../contexts/TeamContext';
import DashboardCard from './DashboardCard';
import TeamOverview from './TeamOverview';
import RecentInsights from './RecentInsights';
import PerformanceMetrics from './PerformanceMetrics';
import QuickActions from './QuickActions';
import { dashboardAPI } from '../../services/api';

const Dashboard = () => {
  const { user } = useAuth();
  const { teams, currentTeam } = useTeam();
  const [dashboardData, setDashboardData] = useState({
    totalTeams: 0,
    totalAssessments: 0,
    avgCompatibility: 0,
    predictedVelocity: 0,
    recentInsights: [],
    performanceMetrics: {}
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [currentTeam]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const data = await dashboardAPI.getDashboardData();
      setDashboardData(data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, {user?.name}!
            </h1>
            <p className="text-gray-600 mt-1">
              Here's what's happening with your teams today.
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">
              {new Date().toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Total Teams"
          value={dashboardData.totalTeams}
          icon="👥"
          trend="+12%"
          trendDirection="up"
        />
        <DashboardCard
          title="Completed Assessments"
          value={dashboardData.totalAssessments}
          icon="📊"
          trend="+8%"
          trendDirection="up"
        />
        <DashboardCard
          title="Avg Team Compatibility"
          value={`${Math.round(dashboardData.avgCompatibility * 100)}%`}
          icon="🤝"
          trend="+5%"
          trendDirection="up"
        />
        <DashboardCard
          title="Predicted Velocity"
          value={`${dashboardData.predictedVelocity} SP`}
          icon="⚡"
          trend="+15%"
          trendDirection="up"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Team Overview */}
        <div className="lg:col-span-2">
          <TeamOverview teams={teams} currentTeam={currentTeam} />
        </div>

        {/* Quick Actions */}
        <div>
          <QuickActions />
        </div>
      </div>

      {/* Secondary Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Insights */}
        <RecentInsights insights={dashboardData.recentInsights} />

        {/* Performance Metrics */}
        <PerformanceMetrics metrics={dashboardData.performanceMetrics} />
      </div>
    </div>
  );
};

export default Dashboard;

// components/Dashboard/DashboardCard.js - Dashboard Metric Card
// import React from 'react';

const DashboardCard = ({ title, value, icon, trend, trendDirection, onClick }) => {
  const trendColor = trendDirection === 'up' ? 'text-green-600' : 'text-red-600';
  const trendIcon = trendDirection === 'up' ? '↗' : '↘';

  return (
    <div 
      className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow ${
        onClick ? 'cursor-pointer' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-2">{value}</p>
          {trend && (
            <p className={`text-sm ${trendColor} mt-1 flex items-center`}>
              <span className="mr-1">{trendIcon}</span>
              {trend} from last month
            </p>
          )}
        </div>
        <div className="text-3xl ml-4">{icon}</div>
      </div>
    </div>
  );
};

export default DashboardCard;

// components/Teams/TeamManagement.js - Team Management Component
// import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { useTeam } from '../../contexts/TeamContext';
import TeamList from './TeamList';
import TeamDetail from './TeamDetail';
import CreateTeam from './CreateTeam';
import TeamOptimization from './TeamOptimization';
import Button from '../UI/Button';
import { PlusIcon } from '@heroicons/react/24/outline';

const TeamManagement = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { teams, fetchTeams, loading } = useTeam();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    fetchTeams();
  }, [fetchTeams]);

  const filteredTeams = teams.filter(team => {
    const matchesSearch = team.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         team.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || team.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const isListView = location.pathname === '/teams' || location.pathname === '/teams/';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Management</h1>
          <p className="text-gray-600 mt-1">
            Manage your teams and optimize their performance
          </p>
        </div>
        {isListView && (
          <Button
            onClick={() => navigate('/teams/create')}
            className="flex items-center space-x-2"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Create Team</span>
          </Button>
        )}
      </div>

      {/* Filters - Only show on list view */}
      {isListView && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="flex-1 max-w-md">
              <input
                type="text"
                placeholder="Search teams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex items-center space-x-4">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Teams</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Routes */}
      <Routes>
        <Route 
          path="/" 
          element={
            <TeamList 
              teams={filteredTeams} 
              loading={loading}
              searchTerm={searchTerm}
            />
          } 
        />
        <Route path="/create" element={<CreateTeam />} />
        <Route path="/:teamId" element={<TeamDetail />} />
        <Route path="/:teamId/optimization" element={<TeamOptimization />} />
      </Routes>
    </div>
  );
};

export default TeamManagement;

// components/Assessments/AssessmentCenter.js - Assessment Management
// import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import AssessmentList from './AssessmentList';
import TakeAssessment from './TakeAssessment';
import AssessmentResults from './AssessmentResults';
import AssessmentComparison from './AssessmentComparison';
import { assessmentAPI } from '../../services/api';
import Button from '../UI/Button';

const AssessmentCenter = () => {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState([]);
  const [availableFrameworks, setAvailableFrameworks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAssessments();
    fetchAvailableFrameworks();
  }, []);

  const fetchAssessments = async () => {
    try {
      const data = await assessmentAPI.getAssessments();
      setAssessments(data);
    } catch (error) {
      console.error('Failed to fetch assessments:', error);
    }
  };

  const fetchAvailableFrameworks = async () => {
    try {
      const frameworks = await assessmentAPI.getAvailableFrameworks();
      setAvailableFrameworks(frameworks);
    } finally {
      setLoading(false);
    }
  };

  const handleAssessmentComplete = (assessmentData) => {
    setAssessments(prev => [...prev, assessmentData]);
    navigate('/assessments/results/' + assessmentData.id);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Assessment Center</h1>
          <p className="text-gray-600 mt-1">
            Complete personality assessments and view your results
          </p>
        </div>
        <Button
          onClick={() => navigate('/assessments/take')}
          className="bg-blue-600 hover:bg-blue-700"
        >
          Take Assessment
        </Button>
      </div>

      {/* Available Frameworks Overview */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Available Assessment Frameworks
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {availableFrameworks.map((framework) => (
            <div key={framework.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-900">{framework.name}</h3>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  assessments.some(a => a.framework_type === framework.id)
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {assessments.some(a => a.framework_type === framework.id) 
                    ? 'Completed' 
                    : 'Available'
                  }
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3">{framework.description}</p>
              <div className="text-xs text-gray-500">
                <span>Duration: {framework.duration} minutes</span>
                <span className="ml-2">Questions: {framework.questionCount}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Routes */}
      <Routes>
        <Route 
          path="/" 
          element={
            <AssessmentList 
              assessments={assessments}
              availableFrameworks={availableFrameworks}
            />
          } 
        />
        <Route 
          path="/take" 
          element={
            <TakeAssessment 
              availableFrameworks={availableFrameworks}
              onComplete={handleAssessmentComplete}
            />
          } 
        />
        <Route path="/results/:assessmentId" element={<AssessmentResults />} />
        <Route path="/compare" element={<AssessmentComparison assessments={assessments} />} />
      </Routes>
    </div>
  );
};

export default AssessmentCenter;

// services/api.js - API Service Layer
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class APIService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    };
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.getAuthHeaders(),
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Auth API
  auth = {
    login: async (email, password) => {
      return this.request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
    },

    register: async (userData) => {
      return this.request('/auth/register', {
        method: 'POST',
        body: JSON.stringify(userData)
      });
    },

    verifyToken: async (token) => {
      return this.request('/auth/verify', {
        headers: { Authorization: `Bearer ${token}` }
      });
    }
  };

  // Team API
  team = {
    getTeams: async () => {
      return this.request('/teams');
    },

    getTeam: async (teamId) => {
      return this.request(`/teams/${teamId}`);
    },

    createTeam: async (teamData) => {
      return this.request('/teams', {
        method: 'POST',
        body: JSON.stringify(teamData)
      });
    },

    updateTeam: async (teamId, updateData) => {
      return this.request(`/teams/${teamId}`, {
        method: 'PUT',
        body: JSON.stringify(updateData)
      });
    },

    deleteTeam: async (teamId) => {
      return this.request(`/teams/${teamId}`, {
        method: 'DELETE'
      });
    },

    optimizeTeam: async (teamId, optimizationRequest) => {
      return this.request(`/teams/${teamId}/optimize`, {
        method: 'POST',
        body: JSON.stringify(optimizationRequest)
      });
    },

    getTeamInsights: async (teamId) => {
      return this.request(`/teams/${teamId}/insights`);
    },

    getTeamPredictions: async (teamId, predictionType = 'all') => {
      return this.request(`/teams/${teamId}/predictions?prediction_type=${predictionType}`);
    }
  };

  // Assessment API
  assessment = {
    getAssessments: async () => {
      return this.request('/assessments');
    },

    createAssessment: async (assessmentData) => {
      return this.request('/assessments', {
        method: 'POST',
        body: JSON.stringify(assessmentData)
      });
    },

    getAvailableFrameworks: async () => {
      return this.request('/assessments/frameworks');
    },

    getAssessmentQuestions: async (frameworkType) => {
      return this.request(`/assessments/frameworks/${frameworkType}/questions`);
    }
  };

  // Dashboard API
  dashboard = {
    getDashboardData: async () => {
      return this.request('/dashboard');
    },

    getMetrics: async (timeframe = '30d') => {
      return this.request(`/dashboard/metrics?timeframe=${timeframe}`);
    }
  };

  // Analytics API
  analytics = {
    getTeamAnalytics: async (teamId, timeframe = '30d') => {
      return this.request(`/analytics/teams/${teamId}?timeframe=${timeframe}`);
    },

    getOrganizationAnalytics: async (timeframe = '30d') => {
      return this.request(`/analytics/organization?timeframe=${timeframe}`);
    },

    getBehavioralTrends: async (timeframe = '30d') => {
      return this.request(`/analytics/behavioral-trends?timeframe=${timeframe}`);
    }
  };
}

// Create singleton instance
const apiService = new APIService();

// Export individual API modules
export const authAPI = apiService.auth;
export const teamAPI = apiService.team;
export const assessmentAPI = apiService.assessment;
export const dashboardAPI = apiService.dashboard;
export const analyticsAPI = apiService.analytics;

export default apiService;