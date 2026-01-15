// frontend/src/components/layout/DashboardLayout.tsx
// Enhanced dashboard layout with httpOnly cookie-based authentication
import React, { useState, useEffect, useCallback, memo } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { SecurityUtils } from '../../utils/securityUtils';
// SECURITY: No longer using SecureTokenStorage - tokens in httpOnly cookies
import Sidebar from './Sidebar';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

interface SecurityMetrics {
  lastActivity: number;
  securityScore: number;
  sessionWarnings: number;
}
const DashboardLayout: React.FC<DashboardLayoutProps> = memo(({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth >= 768);
  const [securityMetrics, setSecurityMetrics] = useState<SecurityMetrics>({
    lastActivity: Date.now(),
    securityScore: 100,
    sessionWarnings: 0
  });
  const [showSecurityWarning, setShowSecurityWarning] = useState(false);

  // Auto-collapse sidebar on small screens
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768 && isSidebarOpen) {
        setIsSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isSidebarOpen]);

  // Security monitoring and session management
  useEffect(() => {
    // Track user activity for security
    const updateActivity = () => {
      setSecurityMetrics(prev => ({
        ...prev,
        lastActivity: Date.now()
      }));

      // SECURITY: Session maintained via httpOnly cookies
      // Backend handles token refresh automatically
    };

    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    activityEvents.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true });
    });

    // Check for session timeout
    const sessionCheck = setInterval(() => {
      const now = Date.now();
      const timeSinceActivity = now - securityMetrics.lastActivity;
      const sessionTimeout = parseInt(import.meta.env.VITE_SESSION_TIMEOUT || '1800000'); // 30 minutes

      if (timeSinceActivity > sessionTimeout) {
        setShowSecurityWarning(true);
        setSecurityMetrics(prev => ({
          ...prev,
          sessionWarnings: prev.sessionWarnings + 1
        }));
      }
    }, 60000); // Check every minute

    // Security score monitoring
    const securityCheck = setInterval(() => {
      const report = SecurityUtils.getSecurityReport();
      setSecurityMetrics(prev => ({
        ...prev,
        securityScore: report.securityScore
      }));
    }, 30000); // Check every 30 seconds

    return () => {
      activityEvents.forEach(event => {
        document.removeEventListener(event, updateActivity);
      });
      clearInterval(sessionCheck);
      clearInterval(securityCheck);
    };
  }, [securityMetrics.lastActivity]);

  // Enhanced logout with security cleanup
  const handleLogout = useCallback(async () => {
    try {
      // Clear security metrics
      setSecurityMetrics({
        lastActivity: Date.now(),
        securityScore: 100,
        sessionWarnings: 0
      });

      // Secure logout
      await logout();

      // Clear any remaining security data from sessionStorage
      Object.keys(sessionStorage).forEach(key => {
        if (key.includes('security') || key.includes('csrf')) {
          sessionStorage.removeItem(key);
        }
      });

      // SECURITY: Tokens cleared by backend via httpOnly cookies

      navigate('/login');
    } catch (error) {
      console.error('Secure logout failed:', error);
      // Force logout even if error occurs
      navigate('/login');
    }
  }, [logout, navigate]);

  // Secure menu toggles with click outside protection
  const toggleMobileMenu = useCallback(() => {
    setIsMobileMenuOpen(prev => !prev);
  }, []);

  const toggleUserMenu = useCallback(() => {
    setIsUserMenuOpen(prev => !prev);
  }, []);

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;

      if (isMobileMenuOpen && !target.closest('[data-mobile-menu]')) {
        setIsMobileMenuOpen(false);
      }

      if (isUserMenuOpen && !target.closest('[data-user-menu]')) {
        setIsUserMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isMobileMenuOpen, isUserMenuOpen]);

  const isActive = useCallback((path: string) => {
    return location.pathname === path;
  }, [location.pathname]);

  // Enhanced navigation with security considerations
  const createSecureLink = useCallback((path: string, className: string = '') => {
    const isExternal = path.startsWith('http');
    const sanitizedPath = isExternal ? SecurityUtils.sanitizeURL(path) : path;

    return {
      to: sanitizedPath,
      className: isActive(path) ? `${className} active` : className,
      ...(isExternal && { target: '_blank', rel: 'noopener noreferrer' })
    };
  }, [isActive]);

  const navLinkClass = useCallback((path: string) => {
    const baseClass = 'px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200';
    const activeClass = 'bg-indigo-700 text-white shadow-sm';
    const inactiveClass = 'text-indigo-100 hover:bg-indigo-600 hover:text-white';

    return `${baseClass} ${isActive(path) ? activeClass : inactiveClass}`;
  }, [isActive]);
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Security Warning Modal */}
      {showSecurityWarning && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <div className="flex items-center mb-4">
              <svg className="w-6 h-6 text-yellow-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <h3 className="text-lg font-semibold text-gray-900">Session Warning</h3>
            </div>
            <p className="text-gray-600 mb-4">
              You've been inactive for a while. For your security, please confirm you want to continue your session.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowSecurityWarning(false);
                  setSecurityMetrics(prev => ({
                    ...prev,
                    lastActivity: Date.now(),
                    sessionWarnings: 0
                  }));
                }}
                className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
              >
                Continue Session
              </button>
              <button
                onClick={handleLogout}
                className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Security Status Indicator */}
      <div className="fixed top-4 left-4 z-40 bg-white rounded-lg shadow-md p-2 hidden lg:block">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            securityMetrics.securityScore >= 80 ? 'bg-green-500' :
            securityMetrics.securityScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
          }`} />
          <span className="text-xs text-gray-600">
            Security: {securityMetrics.securityScore}%
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="bg-indigo-600 shadow-lg fixed top-0 left-0 right-0 z-50 pointer-events-auto" role="navigation" aria-label="Main navigation">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 min-w-0">
            {/* Logo and Primary Navigation */}
            <div className="flex min-w-0 flex-1" data-mobile-menu>
              {/* Logo */}
              <div className="flex-shrink-0 flex items-center">
                <Link
                  to="/dashboard"
                  className="flex items-center group focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-indigo-600 rounded-md p-1"
                  aria-label="PsychSync Dashboard"
                >
                  <svg
                    className="h-7 w-7 md:h-8 md:w-8 text-white flex-shrink-0 group-hover:scale-105 transition-transform"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                  <span className="ml-1 md:ml-2 text-lg md:text-xl font-bold text-white hidden sm:inline group-hover:text-indigo-100 transition-colors">
                    Psych<span className="hidden md:inline">Sync</span>
                  </span>
                </Link>
              </div>
              {/* Primary Navigation - Desktop */}
              <div className="hidden lg:ml-6 lg:flex lg:space-x-1">
                {/* Full navigation items on large screens */}
                <Link to="/dashboard" className={navLinkClass('/dashboard')}>
                  <svg className="inline-block w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  <span className="hidden xl:inline">Dashboard</span>
                </Link>
                <Link to="/teams" className={navLinkClass('/teams')}>
                  <svg className="inline-block w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                  <span className="hidden xl:inline">Teams</span>
                </Link>
                <Link to="/assessments" className={navLinkClass('/assessments')}>
                  <svg className="inline-block w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                  <span className="hidden xl:inline">Assessments</span>
                </Link>
                <Link to="/analytics" className={navLinkClass('/analytics')}>
                  <svg className="inline-block w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span className="hidden xl:inline">Analytics</span>
                </Link>
                <Link to="/templates" className={navLinkClass('/templates')}>
                  <svg className="inline-block w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                  </svg>
                  <span className="hidden xl:inline">Templates</span>
                </Link>
              </div>

              {/* Medium screen navigation with icons only */}
              <div className="hidden md:flex lg:hidden md:ml-3 md:space-x-1 overflow-x-auto min-w-0">
                <Link to="/dashboard" className="text-indigo-100 hover:bg-indigo-600 hover:text-white p-2 rounded-lg" title="Dashboard">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                </Link>
                <Link to="/teams" className="text-indigo-100 hover:bg-indigo-600 hover:text-white p-2 rounded-lg" title="Teams">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                </Link>
                <Link to="/assessments" className="text-indigo-100 hover:bg-indigo-600 hover:text-white p-2 rounded-lg" title="Assessments">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                </Link>
                <Link to="/analytics" className="text-indigo-100 hover:bg-indigo-600 hover:text-white p-2 rounded-lg" title="Analytics">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </Link>
                <Link to="/templates" className="text-indigo-100 hover:bg-indigo-600 hover:text-white p-2 rounded-lg" title="Templates">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                  </svg>
                </Link>
              </div>
            </div>
  
            {/* Right Side Actions - Desktop */}
            <div className="hidden md:flex md:items-center md:space-x-4 flex-shrink-0">
              {/* Sidebar Toggle for Desktop */}
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="p-2 rounded-lg text-indigo-200 hover:text-white hover:bg-indigo-700 transition-colors"
                aria-label="Toggle sidebar"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              {/* Notifications Button */}
              <button
                type="button"
                className="relative p-2 rounded-full text-indigo-200 hover:text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-indigo-600 transition-colors"
              >
                <span className="sr-only">View notifications</span>
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
              </button>
              {/* User Dropdown */}
              <div className="ml-3 relative">
                <div>
                  <button
                    onClick={toggleUserMenu}
                    className="flex items-center text-sm rounded-full text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-indigo-600"
                    id="user-menu-button"
                    aria-expanded={isUserMenuOpen}
                    aria-haspopup="true"
                  >
                    <span className="sr-only">Open user menu</span>
                    <div className="h-8 w-8 rounded-full bg-indigo-800 flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-medium">
                        {user?.full_name?.charAt(0).toUpperCase() || 'U'}
                      </span>
                    </div>
                    <span className="ml-2 md:ml-3 text-sm font-medium hidden md:inline">
                      {user?.full_name || 'User'}
                    </span>
                    <svg
                      className="ml-1 md:ml-2 h-4 w-4 md:h-5 md:w-5 flex-shrink-0"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </button>
                </div>
                {/* Dropdown menu */}
                {isUserMenuOpen && (
                  <>
                    {/* Backdrop for closing menu */}
                    <div
                      className="fixed inset-0 z-10"
                      onClick={toggleUserMenu}
                    ></div>
                    {/* Dropdown content */}
                    <div
                      className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-20"
                      role="menu"
                      aria-orientation="vertical"
                      aria-labelledby="user-menu-button"
                    >
                      <div className="px-4 py-2 border-b border-gray-200">
                        <p className="text-sm text-gray-900 font-medium">
                          {user?.full_name}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {user?.email}
                        </p>
                      </div>
                      <Link
                        to="/profile"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        role="menuitem"
                        onClick={() => setIsUserMenuOpen(false)}
                      >
                        <div className="flex items-center">
                          <svg
                            className="mr-3 h-5 w-5 text-gray-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                            />
                          </svg>
                          Profile Settings
                        </div>
                      </Link>
                      <Link
                        to="/settings"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        role="menuitem"
                        onClick={() => setIsUserMenuOpen(false)}
                      >
                        <div className="flex items-center">
                          <svg
                            className="mr-3 h-5 w-5 text-gray-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                          </svg>
                          Settings
                        </div>
                      </Link>
                      <Link
                        to="/help"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        role="menuitem"
                        onClick={() => setIsUserMenuOpen(false)}
                      >
                        <div className="flex items-center">
                          <svg
                            className="mr-3 h-5 w-5 text-gray-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          Help & Support
                        </div>
                      </Link>
                      <div className="border-t border-gray-200">
                        <button
                          onClick={handleLogout}
                          className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                          role="menuitem"
                        >
                          <div className="flex items-center">
                            <svg
                              className="mr-3 h-5 w-5 text-red-500"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                              />
                            </svg>
                            Sign out
                          </div>
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
            {/* Mobile menu button */}
            <div className="flex items-center md:hidden">
              {/* Sidebar Toggle for Mobile */}
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-indigo-200 hover:text-white hover:bg-indigo-700 mr-2"
                aria-label="Toggle sidebar"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <button
                onClick={toggleMobileMenu}
                type="button"
                className="inline-flex items-center justify-center p-3 rounded-md text-indigo-200 hover:text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white mobile-touch-target"
                aria-controls="mobile-menu"
                aria-expanded={isMobileMenuOpen}
              >
                <span className="sr-only">Open main menu</span>
                {!isMobileMenuOpen ? (
                  <svg
                    className="block h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 6h16M4 12h16M4 18h16"
                    />
                  </svg>
                ) : (
                  <svg
                    className="block h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden" id="mobile-menu">
            <div className="px-2 pt-2 pb-3 space-y-2">
              <Link
                to="/dashboard"
                className={
                  isActive('/dashboard')
                    ? 'bg-indigo-700 text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item active'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item'
                }
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Dashboard
              </Link>
              <Link
                to="/teams"
                className={
                  isActive('/teams')
                    ? 'bg-indigo-700 text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item active'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item'
                }
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Teams
              </Link>
              <Link
                to="/assessments"
                className={
                  isActive('/assessments')
                    ? 'bg-indigo-700 text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item active'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item'
                }
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Assessments
              </Link>
              <Link
                to="/analytics"
                className={
                  isActive('/analytics')
                    ? 'bg-indigo-700 text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item active'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item'
                }
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Analytics
              </Link>
              {/* Additional navigation items */}
              <div className="pt-2 mt-2 border-t border-indigo-600">
                <Link
                  to="/settings"
                  className={
                    isActive('/settings')
                      ? 'bg-indigo-700 text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item active'
                      : 'text-indigo-100 hover:bg-indigo-700 hover:text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item'
                  }
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Settings
                </Link>
                <Link
                  to="/my-responses"
                  className={
                    isActive('/my-responses')
                      ? 'bg-indigo-700 text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item active'
                      : 'text-indigo-100 hover:bg-indigo-700 hover:text-white block px-4 py-3 rounded-md text-base font-medium mobile-nav-item'
                  }
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  My Responses
                </Link>
              </div>
            </div>
            {/* Mobile user menu */}
            <div className="pt-4 pb-3 border-t border-indigo-700">
              <div className="flex items-center px-5">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-full bg-indigo-800 flex items-center justify-center">
                    <span className="text-lg font-medium text-white">
                      {user?.full_name?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                </div>
                <div className="ml-3">
                  <div className="text-base font-medium text-white">
                    {user?.full_name}
                  </div>
                  <div className="text-sm font-medium text-indigo-200">
                    {user?.email}
                  </div>
                </div>
              </div>
              <div className="mt-3 px-2 space-y-1">
                <Link
                  to="/profile"
                  className="block px-3 py-2 rounded-md text-base font-medium text-indigo-100 hover:text-white hover:bg-indigo-700"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Profile Settings
                </Link>
                <Link
                  to="/settings"
                  className="block px-3 py-2 rounded-md text-base font-medium text-indigo-100 hover:text-white hover:bg-indigo-700"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Settings
                </Link>
                <Link
                  to="/help"
                  className="block px-3 py-2 rounded-md text-base font-medium text-indigo-100 hover:text-white hover:bg-indigo-700"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Help & Support
                </Link>
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-red-300 hover:text-white hover:bg-red-600"
                >
                  Sign out
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>
      {/* Page Content with Sidebar */}
      <div className="flex pt-16 sm:pt-20 md:pt-20 lg:pt-20 pb-6">
        <Sidebar isOpen={isSidebarOpen} onToggle={() => setIsSidebarOpen(!isSidebarOpen)} />

        {/* Mobile backdrop */}
        {isSidebarOpen && window.innerWidth < 768 && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-30 md:hidden"
            onClick={() => setIsSidebarOpen(false)}
            aria-hidden="true"
          />
        )}

        <main className={`flex-1 transition-all duration-300 ${
          isSidebarOpen ? 'ml-48' : 'ml-14'
        } ${window.innerWidth < 768 && isSidebarOpen ? 'ml-0' : ''}`}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">
              © 2025 PsychSync. All rights reserved.
            </p>
            <div className="flex space-x-6">
              <Link
                to="/privacy"
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Privacy Policy
              </Link>
              <Link
                to="/terms"
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Terms of Service
              </Link>
              <Link
                to="/contact"
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Contact
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
});

DashboardLayout.displayName = 'DashboardLayout';
export default DashboardLayout;
