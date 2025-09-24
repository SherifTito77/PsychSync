// App.js - Main React Application
import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// ===== CONTEXTS =====

// AuthContext
const AuthContext = createContext();

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
      const token = localStorage.getItem('authToken');
      if (token) {
        // Simulate API call - replace with actual API
        const userData = { id: 1, name: 'Demo User', email: 'demo@example.com' };
        setUser(userData);
      }
    } catch (error) {
      localStorage.removeItem('authToken');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      // Simulate API call - replace with actual API
      const mockResponse = {
        access_token: 'mock-token-' + Date.now(),
        user: { id: 1, name: 'Demo User', email: email }
      };
      
      localStorage.setItem('authToken', mockResponse.access_token);
      setUser(mockResponse.user);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      // Simulate API call - replace with actual API
      const response = { id: Date.now(), ...userData };
      return { success: true, data: response };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
  };

  const value = {
    user,
    isLoading,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// NotificationContext
const NotificationContext = createContext();

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
    const notification = {
      id,
      message,
      type,
      duration
    };

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

// TeamContext
const TeamContext = createContext();

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
      // Mock data - replace with actual API call
      const mockTeams = [
        { id: 1, name: 'Frontend Team', status: 'active', description: 'Web development team' },
        { id: 2, name: 'app Team', status: 'active', description: 'API development team' },
        { id: 3, name: 'QA Team', status: 'inactive', description: 'Quality assurance team' }
      ];
      setTeams(mockTeams);
    } catch (error) {
      showNotification('Failed to fetch teams', 'error');
    } finally {
      setLoading(false);
    }
  };

  const createTeam = async (teamData) => {
    try {
      const newTeam = { id: Date.now(), ...teamData, status: 'active' };
      setTeams(prev => [...prev, newTeam]);
      showNotification('Team created successfully', 'success');
      return { success: true, team: newTeam };
    } catch (error) {
      showNotification('Failed to create team', 'error');
      return { success: false, error: error.message };
    }
  };

  const updateTeam = async (teamId, updateData) => {
    try {
      const updatedTeam = { ...updateData, id: teamId };
      setTeams(prev => prev.map(team => 
        team.id === teamId ? { ...team, ...updatedTeam } : team
      ));
      if (currentTeam && currentTeam.id === teamId) {
        setCurrentTeam({ ...currentTeam, ...updatedTeam });
      }
      showNotification('Team updated successfully', 'success');
      return { success: true, team: updatedTeam };
    } catch (error) {
      showNotification('Failed to update team', 'error');
      return { success: false, error: error.message };
    }
  };

  const deleteTeam = async (teamId) => {
    try {
      setTeams(prev => prev.filter(team => team.id !== teamId));
      if (currentTeam && currentTeam.id === teamId) {
        setCurrentTeam(null);
      }
      showNotification('Team deleted successfully', 'success');
      return { success: true };
    } catch (error) {
      showNotification('Failed to delete team', 'error');
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
    updateTeam,
    deleteTeam,
    selectTeam
  };

  return (
    <TeamContext.Provider value={value}>
      {children}
    </TeamContext.Provider>
  );
};

// ===== COMPONENTS =====

// LoadingSpinner Component
const LoadingSpinner = ({ size = 'medium' }) => {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8',
    large: 'h-12 w-12'
  };

  return (
    <div className={`animate-spin rounded-full border-b-2 border-blue-600 ${sizeClasses[size]}`} />
  );
};

// NotificationContainer Component
const NotificationContainer = () => {
  const { notifications, removeNotification } = useNotification();

  const getNotificationStyles = (type) => {
    const baseStyles = 'mb-4 p-4 rounded-md shadow-md';
    switch (type) {
      case 'success':
        return `${baseStyles} bg-green-100 border-green-500 text-green-700`;
      case 'error':
        return `${baseStyles} bg-red-100 border-red-500 text-red-700`;
      case 'warning':
        return `${baseStyles} bg-yellow-100 border-yellow-500 text-yellow-700`;
      default:
        return `${baseStyles} bg-blue-100 border-blue-500 text-blue-700`;
    }
  };

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={getNotificationStyles(notification.type)}
        >
          <div className="flex justify-between items-center">
            <span>{notification.message}</span>
            <button
              onClick={() => removeNotification(notification.id)}
              className="ml-2 text-lg leading-none"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

// Button Component
const Button = ({ children, onClick, className = '', disabled = false, ...props }) => {
  const baseStyles = 'px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  const defaultStyles = 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed';
  
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyles} ${defaultStyles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

// Header Component
const Header = ({ onMenuToggle }) => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={onMenuToggle}
            className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          >
            ☰
          </button>
          <h1 className="ml-4 text-xl font-semibold text-gray-900">PsychSync</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">Welcome, {user?.name}</span>
          <Button onClick={logout} className="bg-red-600 hover:bg-red-700">
            Logout
          </Button>
        </div>
      </div>
    </header>
  );
};

// Sidebar Component
const Sidebar = ({ isOpen, onToggle }) => {
  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'Teams', path: '/teams', icon: '👥' },
    { name: 'Assessments', path: '/assessments', icon: '📋' },
    { name: 'Optimizer', path: '/optimizer', icon: '⚡' },
    { name: 'Analytics', path: '/analytics', icon: '📈' },
    { name: 'Settings', path: '/settings', icon: '⚙️' }
  ];

  return (
    <div className={`fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 z-40 ${
      isOpen ? 'w-64' : 'w-16'
    }`}>
      <div className="p-4">
        <div className={`flex items-center ${isOpen ? 'justify-between' : 'justify-center'}`}>
          {isOpen && <span className="text-lg font-semibold">PsychSync</span>}
        </div>
      </div>
      
      <nav className="mt-8">
        {menuItems.map((item) => (
          <a
            key={item.path}
            href={item.path}
            className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
          >
            <span className="text-xl">{item.icon}</span>
            {isOpen && <span className="ml-3">{item.name}</span>}
          </a>
        ))}
      </nav>
    </div>
  );
};

// Login Component
const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { showNotification } = useNotification();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await login(email, password);
    
    if (!result.success) {
      showNotification(result.error, 'error');
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold text-center mb-6">Login to PsychSync</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <Button
            type="submit"
            disabled={loading}
            className="w-full"
          >
            {loading ? <LoadingSpinner size="small" /> : 'Login'}
          </Button>
        </form>
        
        <p className="mt-4 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <a href="/register" className="text-blue-600 hover:text-blue-500">
            Register here
          </a>
        </p>
      </div>
    </div>
  );
};

// Register Component
const Register = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const { showNotification } = useNotification();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      showNotification('Passwords do not match', 'error');
      return;
    }

    setLoading(true);
    const result = await register(formData);
    
    if (result.success) {
      showNotification('Registration successful! Please login.', 'success');
    } else {
      showNotification(result.error, 'error');
    }
    
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold text-center mb-6">Register for PsychSync</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <Button
            type="submit"
            disabled={loading}
            className="w-full"
          >
            {loading ? <LoadingSpinner size="small" /> : 'Register'}
          </Button>
        </form>
        
        <p className="mt-4 text-center text-sm text-gray-600">
          Already have an account?{' '}
          <a href="/login" className="text-blue-600 hover:text-blue-500">
            Login here
          </a>
        </p>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user } = useAuth();
  const { teams } = useTeam();
  const [dashboardData, setDashboardData] = useState({
    totalTeams: 0,
    totalAssessments: 0,
    avgCompatibility: 0.85,
    predictedVelocity: 42
  });

  useEffect(() => {
    // Mock dashboard data
    setDashboardData({
      totalTeams: teams.length,
      totalAssessments: 12,
      avgCompatibility: 0.85,
      predictedVelocity: 42
    });
  }, [teams]);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.name}!
        </h1>
        <p className="text-gray-600 mt-1">
          Here's what's happening with your teams today.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Teams</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardData.totalTeams}</p>
            </div>
            <div className="text-3xl">👥</div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Assessments</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardData.totalAssessments}</p>
            </div>
            <div className="text-3xl">📊</div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Compatibility</p>
              <p className="text-2xl font-bold text-gray-900">{Math.round(dashboardData.avgCompatibility * 100)}%</p>
            </div>
            <div className="text-3xl">🤝</div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Predicted Velocity</p>
              <p className="text-2xl font-bold text-gray-900">{dashboardData.predictedVelocity} SP</p>
            </div>
            <div className="text-3xl">⚡</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Placeholder Components
const TeamManagement = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <h2 className="text-2xl font-bold text-gray-900 mb-4">Team Management</h2>
    <p className="text-gray-600">Team management functionality coming soon...</p>
  </div>
);

const AssessmentCenter = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <h2 className="text-2xl font-bold text-gray-900 mb-4">Assessment Center</h2>
    <p className="text-gray-600">Assessment center functionality coming soon...</p>
  </div>
);

const TeamOptimizer = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <h2 className="text-2xl font-bold text-gray-900 mb-4">Team Optimizer</h2>
    <p className="text-gray-600">Team optimizer functionality coming soon...</p>
  </div>
);

const Analytics = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <h2 className="text-2xl font-bold text-gray-900 mb-4">Analytics</h2>
    <p className="text-gray-600">Analytics functionality coming soon...</p>
  </div>
);

const Settings = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <h2 className="text-2xl font-bold text-gray-900 mb-4">Settings</h2>
    <p className="text-gray-600">Settings functionality coming soon...</p>
  </div>
);

// ===== MAIN APP =====

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

export default App;