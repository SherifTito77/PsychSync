// frontend/src/components/mobile/MobileLayout.tsx
import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  HomeIcon,
  UserIcon,
  ChartBarIcon,
  CogIcon,
  MenuIcon,
  XIcon,
  ChevronLeftIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '@/contexts/AuthContext';

interface MobileLayoutProps {
  children?: React.ReactNode;
}

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ElementType;
  href: string;
  badge?: number;
}

export const MobileLayout: React.FC<MobileLayoutProps> = ({ children }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  const location = useLocation();
  const { user } = useAuth();
  const shouldReduceMotion = useReducedMotion();

  // Animation configs based on motion preference
  const springConfig = shouldReduceMotion
    ? { type: 'spring', damping: 50, stiffness: 400 } // Stiffer, less bounce
    : { type: 'spring', damping: 40, stiffness: 300 }; // Improved from 30/300

  // Navigation items
  const navigationItems: NavigationItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: HomeIcon, href: '/dashboard' },
    { id: 'assessments', label: 'Assessments', icon: ChartBarIcon, href: '/assessments' },
    { id: 'teams', label: 'Teams', icon: UserIcon, href: '/teams' },
    { id: 'settings', label: 'Settings', icon: CogIcon, href: '/settings' },
  ];

  // Handle back button functionality
  const handleBack = () => {
    window.history.back();
  };

  // Close menus when route changes
  useEffect(() => {
    setIsMenuOpen(false);
    setIsSheetOpen(false);
  }, [location.pathname]);

  // Close sheet when clicking outside
  useEffect(() => {
    const handleSheetClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest('.mobile-sheet') || target.closest('.sheet-trigger')) {
        return;
      }
      setIsSheetOpen(false);
    };

    if (isSheetOpen) {
      document.addEventListener('click', handleSheetClick);
    }

    return () => {
      if (isSheetOpen) {
        document.removeEventListener('click', handleSheetClick);
      }
    };
  }, [isSheetOpen]);

  // Handle pull-to-refresh
  const [isPulling, setIsPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handlePullStart = (e: React.TouchEvent) => {
    if (window.scrollY === 0) {
      setIsPulling(true);
      setPullDistance(0);
    }
  };

  const handlePullMove = (e: React.TouchEvent) => {
    if (isPulling && window.scrollY === 0) {
      const touch = e.touches[0];
      const distance = touch.clientY - 0;
      setPullDistance(Math.max(0, Math.min(distance, 100)));
    }
  };

  const handlePullEnd = () => {
    if (isPulling) {
      if (pullDistance > 60) {
        handleRefresh();
      }
      setIsPulling(false);
      setPullDistance(0);
    }
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Trigger refresh logic here
    setTimeout(() => {
      setIsRefreshing(false);
    }, 2000);
  };

  return (
    <div className="mobile-layout min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="mobile-header bg-white border-b border-gray-200 sticky top-0 z-40 mobile-safe-area">
        <div className="mobile-container flex items-center justify-between py-4">
          {/* Back button or menu */}
          <div className="flex items-center">
            {location.pathname !== '/' ? (
              <button
                onClick={handleBack}
                className="mobile-button p-2 rounded-full hover:bg-gray-100"
                aria-label="Go back"
              >
                <ChevronLeftIcon className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="mobile-button p-2 rounded-full hover:bg-gray-100"
                aria-label="Toggle menu"
              >
                {isMenuOpen ? <XIcon className="w-5 h-5" /> : <MenuIcon className="w-5 h-5" />}
              </button>
            )}
          </div>

          {/* Title */}
          <div className="flex-1 text-center">
            <h1 className="mobile-h1 text-lg font-semibold text-gray-900 truncate">
              PsychSync
            </h1>
          </div>

          {/* User avatar */}
          <div className="flex items-center">
            <button
              onClick={() => setIsSheetOpen(true)}
              className="sheet-trigger mobile-avatar small"
              aria-label="User menu"
            >
              {user?.profile_image ? (
                <img
                  src={user.profile_image}
                  alt={user.full_name}
                  className="w-8 h-8 rounded-full object-cover"
                />
              ) : (
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                  </span>
                </div>
              )}
            </button>
          </div>
        </div>

        {/* Pull-to-refresh indicator */}
        <AnimatePresence>
          {(isPulling || isRefreshing) && (
            <motion.div
              layout
              initial={{ height: 0 }}
              animate={{ height: isPulling ? pullDistance : 60 }}
              exit={{ height: 0 }}
              transition={shouldReduceMotion ? { duration: 0 } : undefined}
              className="mobile-pull-refresh"
              onTouchStart={handlePullStart}
              onTouchMove={handlePullMove}
              onTouchEnd={handlePullEnd}
            >
              {isRefreshing ? (
                <div className="flex items-center justify-center">
                  <div className="mobile-spinner w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <span className="ml-2 text-sm">Refreshing...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <div className="mobile-icon w-5 h-5">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </div>
                  <span className="ml-2 text-sm">Pull to refresh</span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Side Menu */}
      <AnimatePresence mode="wait">
        {isMenuOpen && (
          <>
            <motion.div
              layout
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={shouldReduceMotion ? { duration: 0.1 } : undefined}
              className="fixed inset-0 bg-black bg-opacity-50 z-50"
              onClick={() => setIsMenuOpen(false)}
            />
            <motion.nav
              layout
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={shouldReduceMotion ? { duration: 0.2 } : springConfig as any}
              className="fixed top-0 left-0 bottom-0 w-64 bg-white shadow-lg z-50 mobile-safe-area"
            >
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="mobile-h2 text-lg font-semibold">Menu</h2>
                  <button
                    onClick={() => setIsMenuOpen(false)}
                    className="mobile-button p-2 rounded-full hover:bg-gray-100"
                    aria-label="Close menu"
                  >
                    <XIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <nav className="p-4">
                <ul className="space-y-2">
                  {navigationItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.href;

                    return (
                      <li key={item.id}>
                        <a
                          href={item.href}
                          className={`mobile-flex mobile-flex-row items-center p-3 rounded-lg transition-colors ${
                            isActive
                              ? 'bg-blue-50 text-blue-600'
                              : 'hover:bg-gray-100 text-gray-700'
                          }`}
                        >
                          <Icon className="w-5 h-5 mr-3" />
                          <span className="font-medium">{item.label}</span>
                          {item.badge && item.badge > 0 && (
                            <span className="ml-auto mobile-badge bg-red-500 text-white">
                              {item.badge}
                            </span>
                          )}
                        </a>
                      </li>
                    );
                  })}
                </ul>
              </nav>

              {/* User section */}
              <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
                <div className="mobile-flex mobile-flex-row items-center">
                  <div className="mobile-avatar">
                    {user?.profile_image ? (
                      <img
                        src={user.profile_image}
                        alt={user.full_name}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-sm font-medium">
                          {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="ml-3 flex-1">
                    <p className="mobile-body font-medium text-gray-900 truncate">
                      {user?.full_name || 'User'}
                    </p>
                    <p className="mobile-caption text-gray-500 truncate">
                      {user?.email || 'user@example.com'}
                    </p>
                  </div>
                </div>
              </div>
            </motion.nav>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <main className="flex-1 mobile-overflow-scroll">
        <div className="mobile-container py-4">
          {children || <Outlet />}
        </div>
      </main>

      {/* Bottom Navigation */}
      <nav className="mobile-nav bg-white border-t border-gray-200">
        <div className="mobile-nav-items">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;

            return (
              <a
                key={item.id}
                href={item.href}
                className={`mobile-nav-item ${isActive ? 'active' : ''}`}
              >
                <Icon className="mobile-nav-icon" />
                <span className="mobile-nav-label">{item.label}</span>
                {item.badge && item.badge > 0 && (
                  <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
                )}
              </a>
            );
          })}
        </div>
      </nav>

      {/* Bottom Sheet */}
      <AnimatePresence mode="wait">
        {isSheetOpen && (
          <motion.div
            layout
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={shouldReduceMotion ? { duration: 0.1 } : undefined}
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={() => setIsSheetOpen(false)}
          />
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {isSheetOpen && (
          <motion.div
            layout
            initial={{ y: 400 }}
            animate={{ y: 0 }}
            exit={{ y: 400 }}
            transition={shouldReduceMotion ? { duration: 0.2 } : (springConfig as any)}
            className="mobile-sheet open"
          >
            <div className="mobile-sheet-handle" />
            <div className="p-6">
              <h2 className="mobile-h2 text-lg font-semibold mb-4">Account</h2>

              <div className="space-y-4">
                {/* Profile section */}
                <div className="mobile-flex mobile-flex-row items-center p-4 bg-gray-50 rounded-lg">
                  <div className="mobile-avatar large">
                    {user?.profile_image ? (
                      <img
                        src={user.profile_image}
                        alt={user.full_name}
                        className="w-14 h-14 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-14 h-14 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-lg font-medium">
                          {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="ml-4 flex-1">
                    <h3 className="mobile-body font-medium text-gray-900">
                      {user?.full_name || 'User'}
                    </h3>
                    <p className="mobile-caption text-gray-500">
                      {user?.email || 'user@example.com'}
                    </p>
                    <p className="mobile-caption text-blue-600">
                      {user?.role || 'User'}
                    </p>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="space-y-2">
                  <button className="mobile-button w-full bg-blue-600 text-white hover:bg-blue-700">
                    View Profile
                  </button>
                  <button className="mobile-button w-full bg-gray-200 text-gray-700 hover:bg-gray-300">
                    Settings
                  </button>
                  <button className="mobile-button w-full bg-red-100 text-red-600 hover:bg-red-200">
                    Sign Out
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MobileLayout;
