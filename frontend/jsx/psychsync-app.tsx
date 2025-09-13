import React, { useState, useEffect, createContext, useContext } from 'react';

// Context Implementations
const AuthContext = createContext();
const TeamContext = createContext();
const NotificationContext = createContext();

// API Service
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class APIService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  getAuthHeaders() {
    // Use in-memory storage instead of localStorage
    const token = window.authToken;
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    };
  }

  async request(endpoint, options = {}) {
    try {
      // Simulate API calls for demo purposes
      await new Promise(resolve => setTimeout(resolve, 500));
      
      if (endpoint === '/auth/login') {
        return { access_token: 'demo-token', user: { id: 1, name: 'Demo User', email: 'demo@example.com' }};
      }
      
      if (endpoint === '/teams') {
        return [
          { id: 1, name: 'Development Team', description: 'Core development team', status: 'active', members: 5 },
          { id: 2, name: 'Design Team', description: 'UI/UX design team', status: 'active', members: 3 }
        ];
      }
      
      if (endpoint === '/dashboard') {
        return {
          totalTeams: 2,
          totalAssessments: 15,
          avgCompatibility: 0.85,
          predictedVelocity: 42,
          recentInsights: [],
          performanceMetrics: {}
        };
      }
      
      return {};
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }
}

const apiService = new APIService();

// Context Providers
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = window.authToken;
      if (token) {
        // Simulate token verification
        setUser({ id: 1, name: 'Demo User', email: 'demo@example.com' });
      }
    } catch (error) {
      window.authToken = null;
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await apiService.request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
      const { access_token, user: userData } = response;
      
      window.authToken = access_token;
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Login failed' 
      };
    }
  };

  const logout = () => {
    window.authToken = null;
    setUser(null);
  };

  const value = {
    user,
    isLoading,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  const showNotification = (message, type = 'info', duration = 5000) => {
    const id = Date.now();
    const notification = { id, message, type, duration };

    setNotifications(prev => [...prev, notification]);

    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, duration);
    }
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const value = {
    notifications,
    showNotification,
    removeNotification
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useTeam = () => {
  const context = useContext(TeamContext);
  if (!context) {
    throw new Error('useTeam must be used within a TeamProvider');
  }
  return context;
};

export const TeamProvider = ({ children }) => {
  const [teams, setTeams] = useState([]);
  const [currentTeam, setCurrentTeam] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showNotification } = useNotification();

  const fetchTeams = async () => {
    setLoading(true);
    try {
      const teamsData = await apiService.request('/teams');
      setTeams(teamsData);
    } catch (error) {
      showNotification('Failed to fetch teams', 'error');
    } finally {
      setLoading(false);
    }
  };

  const createTeam = async (teamData) => {
    try {
      const newTeam = { ...teamData, id: Date.now(), status: 'active' };
      setTeams(prev => [...prev, newTeam]);
      showNotification('Team created successfully', 'success');
      return { success: true, team: newTeam };
    } catch (error) {
      showNotification('Failed to create team', 'error');
      return { success: false, error: error.message };
    }
  };

  const selectTeam = (team) => {
    setCurrentTeam(team);
  };

  const value = {
    teams,
    currentTeam,
    loading,
    fetchTeams,
    createTeam,
    selectTeam
  };

  return (
    <TeamContext.Provider value={value}>
      {children}
    </TeamContext.Provider>
  );
};

// UI Components
const LoadingSpinner = ({ size = 'medium' }) => {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8',
    large: 'h-12 w-12'
  };

  return (
    <div className={`animate-spin rounded-full border-2 border-blue-600 border-t-transparent ${sizeClasses[size]}`}></div>
  );
};

const Button = ({ children, onClick, className = '', variant = 'primary', disabled = false, type = 'button' }) => {
  const baseClasses = 'px-4 py-2 rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors';
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900 focus:ring-gray-500',
    danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500'
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variants[variant]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
    >
      {children}
    </button>
  );
};

const NotificationContainer = () => {
  const { notifications, removeNotification } = useNotification();

  const getNotificationStyles = (type) => {
    const styles = {
      success: 'bg-green-50 border-green-200 text-green-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border-blue-200 text-blue-800'
    };
    return styles[type] || styles.info;
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`p-4 rounded-md border shadow-sm max-w-sm ${getNotificationStyles(notification.type)}`}
        >
          <div className="flex justify-between items-start">
            <p className="text-sm font-medium">{notification.message}</p>
            <button
              onClick={() => removeNotification(notification.id)}
              className="ml-2 text-lg leading-none hover:opacity-70"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

// Auth Components
const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('password');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const result = await login(email, password);
    
    if (!result.success) {
      setError(result.error);
    } else {
      onLogin();
    }
    
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to PsychSync
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Optimize your team dynamics with AI-powered insights
          </p>
        </div>
        <div className="mt-8 space-y-6">
          <div className="rounded-md shadow-sm space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email address</label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Email address"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Password"
              />
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">{error}</div>
          )}

          <div>
            <Button
              onClick={handleSubmit}
              disabled={isLoading}
              className="group relative w-full flex justify-center"
            >
              {isLoading ? <LoadingSpinner size="small" /> : 'Sign in'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Dashboard Components
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

const QuickActions = ({ onNavigate }) => {
  const actions = [
    { title: 'Create New Team', description: 'Set up a new team for assessment', action: () => onNavigate('/teams/create'), icon: '👥' },
    { title: 'Take Assessment', description: 'Complete a personality assessment', action: () => onNavigate('/assessments/take'), icon: '📊' },
    { title: 'View Analytics', description: 'Analyze team performance data', action: () => onNavigate('/analytics'), icon: '📈' },
    { title: 'Team Optimizer', description: 'Optimize existing team composition', action: () => onNavigate('/optimizer'), icon: '⚡' }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
      <div className="space-y-3">
        {actions.map((action, index) => (
          <button
            key={index}
            onClick={action.action}
            className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">{action.icon}</span>
              <div>
                <p className="font-medium text-gray-900">{action.title}</p>
                <p className="text-sm text-gray-600">{action.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

const TeamOverview = ({ teams, currentTeam, onNavigate }) => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Team Overview</h3>
      {teams.length > 0 ? (
        <div className="space-y-4">
          {teams.slice(0, 3).map((team) => (
            <div key={team.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h4 className="font-medium text-gray-900">{team.name}</h4>
                <p className="text-sm text-gray-600">{team.description}</p>
                <p className="text-xs text-gray-500 mt-1">{team.members} members</p>
              </div>
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                team.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {team.status}
              </div>
            </div>
          ))}
          {teams.length > 3 && (
            <p className="text-center text-sm text-gray-500 mt-4">
              +{teams.length - 3} more teams
            </p>
          )}
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-gray-500">No teams created yet</p>
          <Button className="mt-4" onClick={() => onNavigate('/teams/create')}>
            Create Your First Team
          </Button>
        </div>
      )}
    </div>
  );
};

const Dashboard = ({ onNavigate }) => {
  const { user } = useAuth();
  const { teams, currentTeam, fetchTeams } = useTeam();
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
    fetchTeams();
  }, [currentTeam]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const data = await apiService.request('/dashboard');
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
        <LoadingSpinner size="large" />
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
        <div className="lg:col-span-2">
          <TeamOverview teams={teams} currentTeam={currentTeam} onNavigate={onNavigate} />
        </div>
        <div>
          <QuickActions onNavigate={onNavigate} />
        </div>
      </div>
    </div>
  );
};

// Header and Sidebar Components
const Header = ({ onMenuToggle }) => {
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={onMenuToggle}
            className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100"
          >
            ☰
          </button>
          <h2 className="ml-4 text-xl font-semibold text-gray-900">PsychSync</h2>
        </div>

        <div className="flex items-center space-x-4">
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 p-2 rounded-md text-gray-700 hover:bg-gray-100"
            >
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm">
                {user?.name?.charAt(0) || 'U'}
              </div>
              <span className="hidden sm:block">{user?.name}</span>
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1">
                <button
                  onClick={() => {
                    logout();
                    setShowUserMenu(false);
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

const Sidebar = ({ isOpen, onToggle, currentPath, onNavigate }) => {
  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '🏠' },
    { path: '/teams', label: 'Teams', icon: '👥' },
    { path: '/assessments', label: 'Assessments', icon: '📊' },
    { path: '/optimizer', label: 'Optimizer', icon: '⚡' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/settings', label: 'Settings', icon: '⚙️' }
  ];

  return (
    <div className={`fixed inset-y-0 left-0 z-50 transform ${isOpen ? 'translate-x-0' : '-translate-x-full'} 
      transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
      <div className={`flex flex-col h-full bg-gray-900 text-white ${isOpen ? 'w-64' : 'w-16'} transition-all duration-300`}>
        <div className="flex items-center justify-center h-16 bg-gray-800">
          <span className="text-xl font-bold">{isOpen ? 'PsychSync' : 'PS'}</span>
        </div>

        <nav className="flex-1 px-2 py-4 space-y-2">
          {menuItems.map((item) => {
            const isActive = currentPath.startsWith(item.path);
            return (
              <button
                key={item.path}
                onClick={() => onNavigate(item.path)}
                className={`w-full flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                {isOpen && <span className="ml-3">{item.label}</span>}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};

// Page components for other routes
const TeamManagement = ({ onNavigate }) => {
  const { teams, createTeam, fetchTeams, loading } = useTeam();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');

  useEffect(() => {
    fetchTeams();
  }, []);

  const handleCreateTeam = async () => {
    if (!newTeamName.trim()) return;
    
    const result = await createTeam({
      name: newTeamName,
      description: newTeamDescription
    });
    
    if (result.success) {
      setNewTeamName('');
      setNewTeamDescription('');
      setShowCreateForm(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Team Management</h1>
          <p className="text-gray-600 mt-1">Manage your teams and optimize their performance</p>
        </div>
        <Button onClick={() => setShowCreateForm(true)}>
          + Create Team
        </Button>
      </div>

      {showCreateForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Team</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Team Name</label>
              <input
                type="text"
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter team name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={newTeamDescription}
                onChange={(e) => setNewTeamDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="3"
                placeholder="Enter team description"
              />
            </div>
            <div className="flex space-x-3">
              <Button onClick={handleCreateTeam}>Create Team</Button>
              <Button variant="secondary" onClick={() => setShowCreateForm(false)}>Cancel</Button>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Teams</h3>
        {loading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : teams.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {teams.map((team) => (
              <div key={team.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <h4 className="font-semibold text-gray-900">{team.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{team.description}</p>
                <div className="flex justify-between items-center mt-3">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    team.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {team.status}
                  </span>
                  <span className="text-xs text-gray-500">{team.members} members</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">No teams created yet</p>
          </div>
        )}
      </div>
    </div>
  );
};

const AssessmentCenter = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Assessment Center</h1>
      <p className="text-gray-600 mb-6">Complete personality assessments and view your results</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {['Big Five', 'MBTI', 'DISC', 'Enneagram'].map((assessment) => (
          <div key={assessment} className="border border-gray-200 rounded-lg p-4">
            <h3 className="font-medium text-gray-900">{assessment}</h3>
            <p className="text-sm text-gray-600 mt-2">Complete the {assessment} personality assessment</p>
            <Button className="mt-4 w-full">Take Assessment</Button>
          </div>
        ))}
      </div>
    </div>
  );
};

const TeamOptimizer = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Team Optimizer</h1>
      <p className="text-gray-600 mb-6">Optimize your team composition using AI-powered insights</p>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Optimization Goals</h3>
            <div className="space-y-3">
              {['Maximize Creativity', 'Improve Communication', 'Enhance Productivity', 'Balance Skills'].map((goal) => (
                <label key={goal} className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-blue-600" />
                  <span className="ml-2 text-gray-700">{goal}</span>
                </label>
              ))}
            </div>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Team Size</h3>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
              <option>3-5 members</option>
              <option>6-8 members</option>
              <option>9-12 me