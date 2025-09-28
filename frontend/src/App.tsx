// // App.tsx - Complete PsychSync SaaS Application

// App.tsx - Complete PsychSync SaaS Application with Modular Structure
import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Context Providers
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { TeamProvider } from './contexts/TeamContext';

// Hooks
import { useAuth } from './contexts/AuthContext';
import { useNotification } from './contexts/NotificationContext';

// Pages
import Login from '/Users/sheriftito/Downloads/psychsync/frontend/src/pages/Login';
import Register from '/Users/sheriftito/Downloads/psychsync/frontend/src/pages/Register';
import Dashboard from './pages/Dashboard';

// Components
import LoadingSpinner from './components/LoadingSpinner';
import Button from './components/Button';

// Types
import { HeaderProps, SidebarProps, MenuItem } from './types/components';

// ===== LAYOUT COMPONENTS =====

// NotificationContainer Component
const NotificationContainer: React.FC = () => {
  const { notifications, removeNotification } = useNotification();

  const getNotificationStyles = (type: string): string => {
    const baseStyles = 'mb-4 p-4 rounded-lg shadow-lg transition-all duration-300 transform';
    switch (type) {
      case 'success':
        return `${baseStyles} bg-green-50 border-l-4 border-green-400 text-green-800`;
      case 'error':
        return `${baseStyles} bg-red-50 border-l-4 border-red-400 text-red-800`;
      case 'warning':
        return `${baseStyles} bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800`;
      default:
        return `${baseStyles} bg-blue-50 border-l-4 border-blue-400 text-blue-800`;
    }
  };

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm space-y-2">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={getNotificationStyles(notification.type)}
        >
          <div className="flex justify-between items-start">
            <span className="flex-1 text-sm font-medium">
              {notification.message}
            </span>
            <button
              onClick={() => removeNotification(notification.id)}
              className="ml-2 text-lg leading-none opacity-70 hover:opacity-100"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

// Header Component
const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={onMenuToggle}
              className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            >
              ☰
            </button>
            <h1 className="ml-4 text-xl font-semibold text-gray-900">PsychSync</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">Welcome, {user?.name}</span>
            <Button onClick={logout} variant="danger">
              Logout
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

// Sidebar Component
const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
  const menuItems: MenuItem[] = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'Teams', path: '/teams', icon: '👥' },
    { name: 'Assessments', path: '/assessments', icon: '📋' },
    { name: 'Optimizer', path: '/optimizer', icon: '⚡' },
    { name: 'Analytics', path: '/analytics', icon: '📈' },
    { name: 'Settings', path: '/settings', icon: '⚙️' }
  ];

  return (
    <aside className={`fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 z-40 ${
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
    </aside>
  );
};

// ===== PLACEHOLDER PAGES =====

const TeamManagement: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
    <div className="max-w-md mx-auto">
      <div className="text-4xl mb-4">👥</div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Team Management</h2>
      <p className="text-gray-600 mb-6">
        Comprehensive team management features are coming soon. You'll be able
        to create, edit, and organize your teams here.
      </p>
      <Button>Get Notified When Ready</Button>
    </div>
  </div>
);

const AssessmentCenter: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
    <div className="max-w-md mx-auto">
      <div className="text-4xl mb-4">📋</div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Assessment Center</h2>
      <p className="text-gray-600 mb-6">
        Psychological assessments including MBTI, Big Five, and DISC are being
        integrated. Stay tuned for comprehensive personality profiling.
      </p>
      <Button>Get Notified When Ready</Button>
    </div>
  </div>
);

const TeamOptimizer: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
    <div className="max-w-md mx-auto">
      <div className="text-4xl mb-4">⚡</div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">AI Team Optimizer</h2>
      <p className="text-gray-600 mb-6">
        Advanced AI algorithms will analyze team dynamics and provide
        optimization recommendations. Machine learning models are in development.
      </p>
      <Button>Get Notified When Ready</Button>
    </div>
  </div>
);

const Analytics: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
    <div className="max-w-md mx-auto">
      <div className="text-4xl mb-4">📈</div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Advanced Analytics</h2>
      <p className="text-gray-600 mb-6">
        Detailed analytics dashboards with behavioral trends, performance
        metrics, and predictive insights are being developed.
      </p>
      <Button>Get Notified When Ready</Button>
    </div>
  </div>
);

const Settings: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
    <div className="max-w-md mx-auto">
      <div className="text-4xl mb-4">⚙️</div>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Settings</h2>
      <p className="text-gray-600 mb-6">
        User preferences, account settings, and system configurations will be
        available here.
      </p>
      <Button>Get Notified When Ready</Button>
    </div>
  </div>
);

// ===== MAIN APP COMPONENTS =====

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600">Loading PsychSync...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
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
};

// ===== MAIN APP =====

const App: React.FC = () => {
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
};

export default App;


// import React, { useState, useEffect, createContext, useContext } from "react";
// import {
//   BrowserRouter as Router,
//   Routes,
//   Route,
//   Navigate,
// } from "react-router-dom";

// // Types
// import {
//   User,
//   Team,
//   Notification,
//   ApiResponse,
//   RegisterFormData,
//   DashboardData,
// } from "./types";

// import {
//   AuthContextType,
//   NotificationContextType,
//   TeamContextType,
// } from "./types/contexts";

// import { HeaderProps, SidebarProps, MenuItem } from "./types/components";

// // Components
// // import  LoadingSpinner  from "./components/LoadingSpinner";
// // import Button from "./components/Button";

// import LoadingSpinner from "./components/LoadingSpinner";
// import Button from "./components/Button";

// // ===== CONTEXTS =====

// // AuthContext
// const AuthContext = createContext<AuthContextType | undefined>(undefined);

// export const useAuth = (): AuthContextType => {
//   const context = useContext(AuthContext);
//   if (!context) {
//     throw new Error("useAuth must be used within an AuthProvider");
//   }
//   return context;
// };

// export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
//   children,
// }) => {
//   const [user, setUser] = useState<User | null>(null);
//   const [isLoading, setIsLoading] = useState<boolean>(true);

//   useEffect(() => {
//     checkAuthStatus();
//   }, []);

//   const checkAuthStatus = async (): Promise<void> => {
//     try {
//       const token = localStorage.getItem("authToken");
//       if (token) {
//         // Simulate API call - replace with actual API
//         const userData: User = {
//           id: 1,
//           name: "Demo User",
//           email: "demo@example.com",
//         };
//         setUser(userData);
//       }
//     } catch (error) {
//       localStorage.removeItem("authToken");
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const login = async (
//     email: string,
//     password: string,
//   ): Promise<ApiResponse> => {
//     try {
//       setIsLoading(true);
//       // Simulate API call - replace with actual API
//       const mockResponse = {
//         access_token: "mock-token-" + Date.now(),
//         user: { id: 1, name: "Demo User", email: email },
//       };

//       localStorage.setItem("authToken", mockResponse.access_token);
//       setUser(mockResponse.user);

//       return { success: true };
//     } catch (error) {
//       return {
//         success: false,
//         error: error instanceof Error ? error.message : "Login failed",
//       };
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const register = async (userData: RegisterFormData): Promise<ApiResponse> => {
//     try {
//       setIsLoading(true);
//       // Simulate API call - replace with actual API
//       const response = { id: Date.now(), ...userData };
//       return { success: true, data: response };
//     } catch (error) {
//       return {
//         success: false,
//         error: error instanceof Error ? error.message : "Registration failed",
//       };
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const logout = (): void => {
//     localStorage.removeItem("authToken");
//     setUser(null);
//   };

//   const value: AuthContextType = {
//     user,
//     isLoading,
//     login,
//     register,
//     logout,
//   };

//   return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
// };

// // NotificationContext
// const NotificationContext = createContext<NotificationContextType | undefined>(
//   undefined,
// );

// export const useNotification = (): NotificationContextType => {
//   const context = useContext(NotificationContext);
//   if (!context) {
//     throw new Error(
//       "useNotification must be used within a NotificationProvider",
//     );
//   }
//   return context;
// };

// export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({
//   children,
// }) => {
//   const [notifications, setNotifications] = useState<Notification[]>([]);

//   const showNotification = (
//     message: string,
//     type: Notification["type"] = "info",
//     duration: number = 5000,
//   ): void => {
//     const id = Date.now();
//     const notification: Notification = {
//       id,
//       message,
//       type,
//       duration,
//     };

//     setNotifications((prev) => [...prev, notification]);

//     if (duration > 0) {
//       setTimeout(() => {
//         removeNotification(id);
//       }, duration);
//     }
//   };

//   const removeNotification = (id: number): void => {
//     setNotifications((prev) => prev.filter((notif) => notif.id !== id));
//   };

//   const value: NotificationContextType = {
//     notifications,
//     showNotification,
//     removeNotification,
//   };

//   return (
//     <NotificationContext.Provider value={value}>
//       {children}
//     </NotificationContext.Provider>
//   );
// };

// // TeamContext
// const TeamContext = createContext<TeamContextType | undefined>(undefined);

// export const useTeam = (): TeamContextType => {
//   const context = useContext(TeamContext);
//   if (!context) {
//     throw new Error("useTeam must be used within a TeamProvider");
//   }
//   return context;
// };

// export const TeamProvider: React.FC<{ children: React.ReactNode }> = ({
//   children,
// }) => {
//   const [teams, setTeams] = useState<Team[]>([]);
//   const [currentTeam, setCurrentTeam] = useState<Team | null>(null);
//   const [loading, setLoading] = useState<boolean>(false);
//   const { showNotification } = useNotification();

//   const fetchTeams = async (): Promise<void> => {
//     setLoading(true);
//     try {
//       // Mock data - replace with actual API call
//       const mockTeams: Team[] = [
//         {
//           id: 1,
//           name: "Frontend Team",
//           status: "active",
//           description: "Web development team",
//         },
//         {
//           id: 2,
//           name: "Backend Team",
//           status: "active",
//           description: "API development team",
//         },
//         {
//           id: 3,
//           name: "QA Team",
//           status: "inactive",
//           description: "Quality assurance team",
//         },
//       ];
//       setTeams(mockTeams);
//     } catch (error) {
//       showNotification("Failed to fetch teams", "error");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const createTeam = async (
//     teamData: Omit<Team, "id">,
//   ): Promise<ApiResponse<Team>> => {
//     try {
//       const newTeam: Team = {
//         id: Date.now(),
//         ...teamData,
//         status: "active",
//       };
//       setTeams((prev) => [...prev, newTeam]);
//       showNotification("Team created successfully", "success");
//       return { success: true, data: newTeam };
//     } catch (error) {
//       const errorMessage =
//         error instanceof Error ? error.message : "Failed to create team";
//       showNotification(errorMessage, "error");
//       return { success: false, error: errorMessage };
//     }
//   };

//   const updateTeam = async (
//     teamId: number,
//     updateData: Partial<Team>,
//   ): Promise<ApiResponse<Team>> => {
//     try {
//       const updatedTeam: Team = { ...updateData, id: teamId } as Team;
//       setTeams((prev) =>
//         prev.map((team) =>
//           team.id === teamId ? { ...team, ...updatedTeam } : team,
//         ),
//       );
//       if (currentTeam && currentTeam.id === teamId) {
//         setCurrentTeam({ ...currentTeam, ...updatedTeam });
//       }
//       showNotification("Team updated successfully", "success");
//       return { success: true, data: updatedTeam };
//     } catch (error) {
//       const errorMessage =
//         error instanceof Error ? error.message : "Failed to update team";
//       showNotification(errorMessage, "error");
//       return { success: false, error: errorMessage };
//     }
//   };

//   const deleteTeam = async (teamId: number): Promise<ApiResponse> => {
//     try {
//       setTeams((prev) => prev.filter((team) => team.id !== teamId));
//       if (currentTeam && currentTeam.id === teamId) {
//         setCurrentTeam(null);
//       }
//       showNotification("Team deleted successfully", "success");
//       return { success: true };
//     } catch (error) {
//       const errorMessage =
//         error instanceof Error ? error.message : "Failed to delete team";
//       showNotification(errorMessage, "error");
//       return { success: false, error: errorMessage };
//     }
//   };

//   const selectTeam = (team: Team): void => {
//     setCurrentTeam(team);
//   };

//   const value: TeamContextType = {
//     teams,
//     currentTeam,
//     loading,
//     fetchTeams,
//     createTeam,
//     updateTeam, // ensure teamId is number
//     deleteTeam, // ensure teamId is number
//     selectTeam,
//   };

//   return <TeamContext.Provider value={value}>{children}</TeamContext.Provider>;
// };

// // ===== COMPONENTS =====

// // NotificationContainer Component
// const NotificationContainer: React.FC = () => {
//   const { notifications, removeNotification } = useNotification();

//   const getNotificationStyles = (type: Notification["type"]): string => {
//     const baseStyles =
//       "mb-4 p-4 rounded-lg shadow-lg transition-all duration-300 transform";
//     switch (type) {
//       case "success":
//         return `${baseStyles} bg-green-50 border-l-4 border-green-400 text-green-800`;
//       case "error":
//         return `${baseStyles} bg-red-50 border-l-4 border-red-400 text-red-800`;
//       case "warning":
//         return `${baseStyles} bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800`;
//       default:
//         return `${baseStyles} bg-blue-50 border-l-4 border-blue-400 text-blue-800`;
//     }
//   };

//   if (notifications.length === 0) return null;

//   return (
//     <div className="fixed top-4 right-4 z-50 max-w-sm space-y-2">
//       {notifications.map((notification: Notification) => (
//         <div
//           key={notification.id}
//           className={getNotificationStyles(notification.type)}
//         >
//           <div className="flex justify-between items-start">
//             <span className="flex-1 text-sm font-medium">
//               {notification.message}
//             </span>
//             <button
//               onClick={() => removeNotification(notification.id)}
//               className="ml-2 text-lg leading-none opacity-70 hover:opacity-100"
//             >
//               ×
//             </button>
//           </div>
//         </div>
//       ))}
//     </div>
//   );
// };

// // Header Component
// const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
//   const { user, logout } = useAuth();

//   return (
//     <header className="bg-white shadow-sm border-b border-gray-200">
//       <div className="px-6 py-4">
//         <div className="flex items-center justify-between">
//           <div className="flex items-center">
//             <button
//               onClick={onMenuToggle}
//               className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
//             >
//               ☰
//             </button>
//             <h1 className="ml-4 text-xl font-semibold text-gray-900">
//               PsychSync
//             </h1>
//           </div>

//           <div className="flex items-center space-x-4">
//             <span className="text-sm text-gray-600">Welcome, {user?.name}</span>
//             <Button onClick={logout} variant="danger">
//               Logout
//             </Button>
//           </div>
//         </div>
//       </div>
//     </header>
//   );
// };

// // Sidebar Component
// const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
//   const menuItems: MenuItem[] = [
//     { name: "Dashboard", path: "/dashboard", icon: "📊" },
//     { name: "Teams", path: "/teams", icon: "👥" },
//     { name: "Assessments", path: "/assessments", icon: "📋" },
//     { name: "Optimizer", path: "/optimizer", icon: "⚡" },
//     { name: "Analytics", path: "/analytics", icon: "📈" },
//     { name: "Settings", path: "/settings", icon: "⚙️" },
//   ];

//   return (
//     <aside
//       className={`fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 z-40 ${
//         isOpen ? "w-64" : "w-16"
//       }`}
//     >
//       <div className="p-4">
//         <div
//           className={`flex items-center ${isOpen ? "justify-between" : "justify-center"}`}
//         >
//           {isOpen && <span className="text-lg font-semibold">PsychSync</span>}
//         </div>
//       </div>

//       <nav className="mt-8">
//         {menuItems.map((item) => (
//           <a
//             key={item.path}
//             href={item.path}
//             className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
//           >
//             <span className="text-xl">{item.icon}</span>
//             {isOpen && <span className="ml-3">{item.name}</span>}
//           </a>
//         ))}
//       </nav>
//     </aside>
//   );
// };

// // Login Component
// const Login: React.FC = () => {
//   const [email, setEmail] = useState<string>("");
//   const [password, setPassword] = useState<string>("");
//   const [loading, setLoading] = useState<boolean>(false);
//   const { login } = useAuth();
//   const { showNotification } = useNotification();

//   const handleSubmit = async (
//     e: React.FormEvent<HTMLFormElement>,
//   ): Promise<void> => {
//     e.preventDefault();
//     setLoading(true);

//     const result = await login(email, password);

//     if (!result.success) {
//       showNotification(result.error || "Login failed", "error");
//     }

//     setLoading(false);
//   };

//   return (
//     <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
//       <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
//         <div className="text-center mb-8">
//           <h2 className="text-3xl font-bold text-gray-900">PsychSync</h2>
//           <p className="text-gray-600 mt-2">Sign in to your account</p>
//         </div>

//         <form onSubmit={handleSubmit} className="space-y-6">
//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-2">
//               Email Address
//             </label>
//             <input
//               type="email"
//               value={email}
//               onChange={(e) => setEmail(e.target.value)}
//               className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
//               placeholder="your@email.com"
//               required
//             />
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-2">
//               Password
//             </label>
//             <input
//               type="password"
//               value={password}
//               onChange={(e) => setPassword(e.target.value)}
//               className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
//               placeholder="••••••••"
//               required
//             />
//           </div>

//           <Button type="submit" disabled={loading} className="w-full">
//             {loading ? <LoadingSpinner size="small" /> : "Sign In"}
//           </Button>
//         </form>

//         <p className="mt-6 text-center text-sm text-gray-600">
//           Don't have an account?{" "}
//           <a
//             href="/register"
//             className="text-blue-600 hover:text-blue-500 font-medium"
//           >
//             Create one here
//           </a>
//         </p>
//       </div>
//     </div>
//   );
// };

// // Register Component
// const Register: React.FC = () => {
//   const [formData, setFormData] = useState<RegisterFormData>({
//     name: "",
//     email: "",
//     password: "",
//     confirmPassword: "",
//   });
//   const [loading, setLoading] = useState<boolean>(false);
//   const { register } = useAuth();
//   const { showNotification } = useNotification();

//   const handleSubmit = async (
//     e: React.FormEvent<HTMLFormElement>,
//   ): Promise<void> => {
//     e.preventDefault();

//     if (formData.password !== formData.confirmPassword) {
//       showNotification("Passwords do not match", "error");
//       return;
//     }

//     if (formData.password.length < 8) {
//       showNotification("Password must be at least 8 characters long", "error");
//       return;
//     }

//     setLoading(true);
//     const result = await register(formData);

//     if (result.success) {
//       showNotification("Registration successful! Please login.", "success");
//       // Reset form
//       setFormData({ name: "", email: "", password: "", confirmPassword: "" });
//     } else {
//       showNotification(result.error || "Registration failed", "error");
//     }

//     setLoading(false);
//   };

//   const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
//     setFormData((prev) => ({
//       ...prev,
//       [e.target.name]: e.target.value,
//     }));
//   };

//   return (
//     <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
//       <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
//         <div className="text-center mb-8">
//           <h2 className="text-3xl font-bold text-gray-900">Join PsychSync</h2>
//           <p className="text-gray-600 mt-2">Create your account</p>
//         </div>

//         <form onSubmit={handleSubmit} className="space-y-6">
//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-2">
//               Full Name
//             </label>
//             <input
//               type="text"
//               name="name"
//               value={formData.name}
//               onChange={handleChange}
//               className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
//               placeholder="John Doe"
//               required
//             />
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-2">
//               Email Address
//             </label>
//             <input
//               type="email"
//               name="email"
//               value={formData.email}
//               onChange={handleChange}
//               className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
//               placeholder="your@email.com"
//               required
//             />
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-2">
//               Password
//             </label>
//             <input
//               type="password"
//               name="password"
//               value={formData.password}
//               onChange={handleChange}
//               className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
//               placeholder="••••••••"
//               required
//             />
//           </div>

//           <div>
//             <label className="block text-sm font-medium text-gray-700 mb-2">
//               Confirm Password
//             </label>
//             <input
//               type="password"
//               name="confirmPassword"
//               value={formData.confirmPassword}
//               onChange={handleChange}
//               className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
//               placeholder="••••••••"
//               required
//             />
//           </div>

//           <Button type="submit" disabled={loading} className="w-full">
//             {loading ? <LoadingSpinner size="small" /> : "Create Account"}
//           </Button>
//         </form>

//         <p className="mt-6 text-center text-sm text-gray-600">
//           Already have an account?{" "}
//           <a
//             href="/login"
//             className="text-blue-600 hover:text-blue-500 font-medium"
//           >
//             Sign in here
//           </a>
//         </p>
//       </div>
//     </div>
//   );
// };

// // Dashboard Component
// const Dashboard: React.FC = () => {
//   const { user } = useAuth();
//   const { teams, fetchTeams } = useTeam();
//   const [dashboardData, setDashboardData] = useState<DashboardData>({
//     totalTeams: 0,
//     totalAssessments: 0,
//     avgCompatibility: 0.85,
//     predictedVelocity: 42,
//   });

//   useEffect(() => {
//     fetchTeams();
//   }, []);

//   useEffect(() => {
//     // Mock dashboard data
//     setDashboardData({
//       totalTeams: teams.length,
//       totalAssessments: 12,
//       avgCompatibility: 0.85,
//       predictedVelocity: 42,
//     });
//   }, [teams]);

//   const statCards = [
//     {
//       title: "Total Teams",
//       value: dashboardData.totalTeams,
//       icon: "👥",
//       color: "bg-blue-500",
//     },
//     {
//       title: "Assessments",
//       value: dashboardData.totalAssessments,
//       icon: "📊",
//       color: "bg-green-500",
//     },
//     {
//       title: "Avg Compatibility",
//       value: `${Math.round(dashboardData.avgCompatibility * 100)}%`,
//       icon: "🤝",
//       color: "bg-purple-500",
//     },
//     {
//       title: "Predicted Velocity",
//       value: `${dashboardData.predictedVelocity} SP`,
//       icon: "⚡",
//       color: "bg-yellow-500",
//     },
//   ];

//   return (
//     <div className="space-y-8">
//       {/* Welcome Section */}
//       <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
//         <h1 className="text-3xl font-bold text-gray-900">
//           Welcome back, {user?.name}!
//         </h1>
//         <p className="text-gray-600 mt-2">
//           Here's an overview of your team optimization platform.
//         </p>
//       </div>

//       {/* Stats Grid */}
//       <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
//         {statCards.map((card, index) => (
//           <div
//             key={index}
//             className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
//           >
//             <div className="flex items-center justify-between">
//               <div>
//                 <p className="text-sm font-medium text-gray-600">
//                   {card.title}
//                 </p>
//                 <p className="text-2xl font-bold text-gray-900 mt-1">
//                   {card.value}
//                 </p>
//               </div>
//               <div className={`p-3 rounded-lg ${card.color} bg-opacity-10`}>
//                 <span className="text-2xl">{card.icon}</span>
//               </div>
//             </div>
//           </div>
//         ))}
//       </div>

//       {/* Quick Actions */}
//       <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
//         <h2 className="text-xl font-semibold text-gray-900 mb-4">
//           Quick Actions
//         </h2>
//         <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
//           <Button className="justify-center">Create New Team</Button>
//           <Button className="justify-center" variant="secondary">
//             Run Assessment
//           </Button>
//           <Button className="justify-center" variant="secondary">
//             Optimize Teams
//           </Button>
//         </div>
//       </div>

//       {/* Recent Activity */}
//       <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
//         <h2 className="text-xl font-semibold text-gray-900 mb-4">
//           Recent Activity
//         </h2>
//         <div className="space-y-3">
//           <div className="flex items-center text-sm text-gray-600">
//             <span className="w-2 h-2 bg-green-400 rounded-full mr-3"></span>
//             Team "Frontend Squad" completed MBTI assessment
//           </div>
//           <div className="flex items-center text-sm text-gray-600">
//             <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
//             New optimization suggestion for "Backend Team"
//           </div>
//           <div className="flex items-center text-sm text-gray-600">
//             <span className="w-2 h-2 bg-purple-400 rounded-full mr-3"></span>
//             Analytics report generated for Q4 2024
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// // Placeholder Components for future development
// const TeamManagement: React.FC = () => (
//   <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
//     <div className="max-w-md mx-auto">
//       <div className="text-4xl mb-4">👥</div>
//       <h2 className="text-2xl font-bold text-gray-900 mb-4">Team Management</h2>
//       <p className="text-gray-600 mb-6">
//         Comprehensive team management features are coming soon. You'll be able
//         to create, edit, and organize your teams here.
//       </p>
//       <Button>Get Notified When Ready</Button>
//     </div>
//   </div>
// );

// const AssessmentCenter: React.FC = () => (
//   <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
//     <div className="max-w-md mx-auto">
//       <div className="text-4xl mb-4">📋</div>
//       <h2 className="text-2xl font-bold text-gray-900 mb-4">
//         Assessment Center
//       </h2>
//       <p className="text-gray-600 mb-6">
//         Psychological assessments including MBTI, Big Five, and DISC are being
//         integrated. Stay tuned for comprehensive personality profiling.
//       </p>
//       <Button>Get Notified When Ready</Button>
//     </div>
//   </div>
// );

// const TeamOptimizer: React.FC = () => (
//   <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
//     <div className="max-w-md mx-auto">
//       <div className="text-4xl mb-4">⚡</div>
//       <h2 className="text-2xl font-bold text-gray-900 mb-4">
//         AI Team Optimizer
//       </h2>
//       <p className="text-gray-600 mb-6">
//         Advanced AI algorithms will analyze team dynamics and provide
//         optimization recommendations. Machine learning models are in
//         development.
//       </p>
//       <Button>Get Notified When Ready</Button>
//     </div>
//   </div>
// );

// const Analytics: React.FC = () => (
//   <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
//     <div className="max-w-md mx-auto">
//       <div className="text-4xl mb-4">📈</div>
//       <h2 className="text-2xl font-bold text-gray-900 mb-4">
//         Advanced Analytics
//       </h2>
//       <p className="text-gray-600 mb-6">
//         Detailed analytics dashboards with behavioral trends, performance
//         metrics, and predictive insights are being developed.
//       </p>
//       <Button>Get Notified When Ready</Button>
//     </div>
//   </div>
// );

// const Settings: React.FC = () => (
//   <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
//     <div className="max-w-md mx-auto">
//       <div className="text-4xl mb-4">⚙️</div>
//       <h2 className="text-2xl font-bold text-gray-900 mb-4">Settings</h2>
//       <p className="text-gray-600 mb-6">
//         User preferences, account settings, and system configurations will be
//         available here.
//       </p>
//       <Button>Get Notified When Ready</Button>
//     </div>
//   </div>
// );

// // ===== MAIN APP COMPONENTS =====

// const AppContent: React.FC = () => {
//   const { user, isLoading } = useAuth();
//   const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

//   if (isLoading) {
//     return (
//       <div className="flex items-center justify-center min-h-screen bg-gray-50">
//         <div className="text-center">
//           <LoadingSpinner size="large" />
//           <p className="mt-4 text-gray-600">Loading PsychSync...</p>
//         </div>
//       </div>
//     );
//   }

//   if (!user) {
//     return (
//       <Routes>
//         <Route path="/login" element={<Login />} />
//         <Route path="/register" element={<Register />} />
//         <Route path="*" element={<Navigate to="/login" replace />} />
//       </Routes>
//     );
//   }

//   return (
//     <div className="flex min-h-screen bg-gray-50">
//       <Sidebar
//         isOpen={sidebarOpen}
//         onToggle={() => setSidebarOpen(!sidebarOpen)}
//       />

//       <div
//         className={`flex-1 flex flex-col transition-all duration-300 ${
//           sidebarOpen ? "ml-64" : "ml-16"
//         }`}
//       >
//         <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

//         <main className="flex-1 p-6 overflow-auto">
//           <Routes>
//             <Route path="/" element={<Dashboard />} />
//             <Route path="/dashboard" element={<Dashboard />} />
//             <Route path="/teams/*" element={<TeamManagement />} />
//             <Route path="/assessments/*" element={<AssessmentCenter />} />
//             <Route path="/optimizer" element={<TeamOptimizer />} />
//             <Route path="/analytics" element={<Analytics />} />
//             <Route path="/settings" element={<Settings />} />
//             <Route path="*" element={<Navigate to="/dashboard" replace />} />
//           </Routes>
//         </main>
//       </div>

//       <NotificationContainer />
//     </div>
//   );
// };

// // ===== MAIN APP =====

// const App: React.FC = () => {
//   return (
//     <AuthProvider>
//       <NotificationProvider>
//         <TeamProvider>
//           <Router>
//             <div className="app">
//               <AppContent />
//             </div>
//           </Router>
//         </TeamProvider>
//       </NotificationProvider>
//     </AuthProvider>
//   );
// };

// export default App;
