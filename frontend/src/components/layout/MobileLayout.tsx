import React, { useState } from 'react';
import {
  Menu,
  X,
  Bell,
  Home,
  Shield,
  FileText,
  MessageSquare,
  BookOpen,
  BarChart3,
  User,
  Settings,
  ChevronRight,
  LogOut,
  RefreshCw
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import Button from '../common/Button';
import { NotificationCenter } from '../common/NotificationCenter';
import Badge from '../common/Badge';
interface MobileLayoutProps {
  children: React.ReactNode;
  title?: string;
  showBackButton?: boolean;
  onBackClick?: () => void;
}
export const MobileLayout: React.FC<MobileLayoutProps> = ({
  children,
  title,
  showBackButton,
  onBackClick
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const menuItems = [
    { icon: <Home className="w-5 h-5" />, label: 'Dashboard', path: '/dashboard' },
    { icon: <Shield className="w-5 h-5" />, label: 'Compliance', path: '/compliance' },
    { icon: <FileText className="w-5 h-5" />, label: 'Training', path: '/compliance/training' },
    { icon: <MessageSquare className="w-5 h-5" />, label: 'Feedback', path: '/anonymous-feedback' },
    { icon: <BookOpen className="w-5 h-5" />, label: 'Employee Rights', path: '/compliance/rights' },
    { icon: <BarChart3 className="w-5 h-5" />, label: 'Analytics', path: '/analytics' },
    { icon: <Settings className="w-5 h-5" />, label: 'Settings', path: '/settings' }
  ];
  const isActive = (path: string) => location.pathname === path;
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Mobile Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center space-x-3">
            <Button
              variant="ghost"
              size="small"
              onClick={() => setSidebarOpen(true)}
              icon={<Menu className="w-5 h-5" />}
            />
            {showBackButton && (
              <Button
                variant="ghost"
                size="small"
                onClick={onBackClick || (() => window.history.back())}
                icon={<ChevronRight className="w-5 h-5 rotate-180" />}
              />
            )}
            <div>
              <h1 className="text-lg font-semibold text-gray-900">{title || 'PsychSync'}</h1>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <NotificationCenter />
            <div className="relative">
              <Button
                variant="ghost"
                size="small"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                icon={<User className="w-5 h-5" />}
              />
            </div>
          </div>
        </div>
      </header>
      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-4 max-w-lg mx-auto">
          {children}
        </div>
      </main>
      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="fixed left-0 top-0 h-full w-64 bg-white shadow-lg z-50 flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold">PsychSync</h2>
              <Button
                variant="ghost"
                size="small"
                onClick={() => setSidebarOpen(false)}
                icon={<X className="w-5 h-5" />}
              />
            </div>
            <nav className="flex-1 overflow-y-auto p-4">
              <ul className="space-y-2">
                {menuItems.map((item) => (
                  <li key={item.path}>
                    <button
                      onClick={() => {
                        navigate(item.path);
                        setSidebarOpen(false);
                      }}
                      className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                        isActive(item.path)
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <span className={isActive(item.path) ? 'text-blue-700' : 'text-gray-500'}>
                        {item.icon}
                      </span>
                      <span className="font-medium">{item.label}</span>
                      {item.label === 'Feedback' && (
                        <Badge color="red" size="sm">3</Badge>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
            <div className="p-4 border-t border-gray-200">
              <div className="space-y-2">
                <button className="w-full flex items-center space-x-3 px-4 py-3 text-gray-700 hover:bg-gray-100 rounded-lg">
                  <LogOut className="w-5 h-5 text-gray-500" />
                  <span className="font-medium">Log Out</span>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
      {/* User Dropdown */}
      {userMenuOpen && (
        <>
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={() => setUserMenuOpen(false)}
          />
          <div className="fixed right-4 top-16 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
            <div className="p-4 border-b border-gray-200">
              <p className="text-sm font-medium text-gray-900">John Doe</p>
              <p className="text-xs text-gray-500">john.doe@company.com</p>
            </div>
            <nav className="p-2">
              <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg">
                Profile Settings
              </button>
              <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg">
                Preferences
              </button>
              <button className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg">
                Log Out
              </button>
            </nav>
          </div>
        </>
      )}
    </div>
  );
};
// Mobile-specific components
export const MobileCard: React.FC<{
  title: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}> = ({ title, children, actions, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 mb-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-900">{title}</h3>
        {actions && <div className="flex space-x-2">{actions}</div>}
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  );
};
export const MobileStatsGrid: React.FC<{
  stats: Array<{
    label: string;
    value: string | number;
    icon: React.ReactNode;
    color: 'blue' | 'green' | 'yellow' | 'red';
  }>;
}> = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 gap-4 mb-6">
      {stats.map((stat, index) => (
        <div key={index} className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className={`p-2 rounded-lg ${
              stat.color === 'blue' ? 'bg-blue-100 text-blue-600' :
              stat.color === 'green' ? 'bg-green-100 text-green-600' :
              stat.color === 'yellow' ? 'bg-yellow-100 text-yellow-600' :
              'bg-red-100 text-red-600'
            }`}>
              {stat.icon}
            </div>
          </div>
          <p className="text-xs text-gray-600">{stat.label}</p>
          <p className="text-xl font-bold text-gray-900">{stat.value}</p>
        </div>
      ))}
    </div>
  );
};
export const MobileQuickActions: React.FC<{
  actions: Array<{
    label: string;
    icon: React.ReactNode;
    color: 'blue' | 'green' | 'red' | 'yellow';
    onPress: () => void;
  }>;
}> = ({ actions }) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
      <h3 className="text-base font-semibold text-gray-900 mb-4">Quick Actions</h3>
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action, index) => (
          <button
            key={index}
            onClick={action.onPress}
            className={`p-4 rounded-lg border ${
              action.color === 'blue' ? 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100' :
              action.color === 'green' ? 'bg-green-50 border-green-200 text-green-700 hover:bg-green-100' :
              action.color === 'red' ? 'bg-red-50 border-red-200 text-red-700 hover:bg-red-100' :
              'bg-yellow-50 border-yellow-200 text-yellow-700 hover:bg-yellow-100'
            }`}
          >
            <div className="flex flex-col items-center space-y-2">
              {action.icon}
              <span className="text-xs font-medium">{action.label}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
export const MobilePullToRefresh: React.FC<{
  onRefresh: () => Promise<void>;
  isRefreshing: boolean;
}> = ({ onRefresh, isRefreshing }) => {
  const [pullDistance, setPullDistance] = useState(0);
  const [startY, setStartY] = useState(0);
  const [pulling, setPulling] = useState(false);
  const handleTouchStart = (e: React.TouchEvent) => {
    setStartY(e.touches[0].clientY);
    setPulling(true);
  };
  const handleTouchMove = (e: React.TouchEvent) => {
    if (!pulling) return;
    const currentY = e.touches[0].clientY;
    const distance = currentY - startY;
    if (distance > 0 && distance < 120) {
      setPullDistance(distance);
    }
  };
  const handleTouchEnd = async () => {
    if (pulling && pullDistance > 80 && !isRefreshing) {
      await onRefresh();
    }
    setPullDistance(0);
    setPulling(false);
    setStartY(0);
  };
  return (
    <div
      className="relative -mt-4"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {pullDistance > 0 && (
        <div
          className="flex justify-center items-center transition-all duration-200"
          style={{
            height: `${Math.min(pullDistance, 80)}px`,
            opacity: pullDistance / 80
          }}
        >
          <div className="text-center">
            <div className={`inline-flex items-center px-4 py-2 bg-white rounded-full shadow-md border border-gray-200 ${
              isRefreshing ? 'animate-pulse' : ''
            }`}>
              {isRefreshing ? (
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-500 border-t-transparent" />
              ) : (
                <RefreshCw className="w-4 h-4 text-blue-500" />
              )}
              <span className="ml-2 text-sm text-gray-700">
                {isRefreshing ? 'Refreshing...' : 'Pull to refresh'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};