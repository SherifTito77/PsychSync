// src/components/OnboardingNavigation.tsx
// Simple navigation to switch between onboarding flows
import React, { useState, useRef, useEffect } from 'react';

// TODO(human): Define the alert types and notification structure
interface CriticalAlert {
  id: string;
  type: 'security' | 'system' | 'deadline' | 'error';
  message: string;
  timestamp: Date;
  link?: string;
}

const OnboardingNavigation: React.FC = () => {
  const [isMinimized, setIsMinimized] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 80 }); // Initial position
  const dragOffset = useRef({ x: 0, y: 0 });
  const menuRef = useRef<HTMLDivElement>(null);

  // Notification state
  const [criticalAlerts, setCriticalAlerts] = useState<CriticalAlert[]>([]);

  // Alert management functions
  const addAlert = (alert: Omit<CriticalAlert, 'id'>) => {
    const newAlert: CriticalAlert = {
      ...alert,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
    };

    setCriticalAlerts(prev => {
      const updated = [...prev, newAlert];
      // Keep only the 5 most recent alerts
      return updated.slice(-5);
    });
  };

  const dismissAlert = (id: string) => {
    setCriticalAlerts(prev => prev.filter(alert => alert.id !== id));
  };

  const dismissAllAlerts = () => {
    setCriticalAlerts([]);
  };

  const formatTimestamp = (date: Date): string => {
    const now = Date.now();
    const timestamp = new Date(date).getTime();
    const diff = now - timestamp;

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} min${minutes > 1 ? 's' : ''} ago`;
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`;
    return new Date(date).toLocaleDateString();
  };

  // Load test alerts on mount
  useEffect(() => {
    // Add sample alerts for demonstration
    setTimeout(() => {
      addAlert({
        type: 'security',
        message: 'Session expires in 5 minutes',
        timestamp: new Date(Date.now() - 2 * 60000), // 2 minutes ago
      });
    }, 1000);

    setTimeout(() => {
      addAlert({
        type: 'deadline',
        message: 'Assessment deadline approaching',
        timestamp: new Date(Date.now() - 15 * 60000), // 15 minutes ago
      });
    }, 2000);

    setTimeout(() => {
      addAlert({
        type: 'error',
        message: 'Connection unstable - changes may not save',
        link: '/settings',
        timestamp: new Date(Date.now() - 30 * 60000), // 30 minutes ago
      });
    }, 3000);
  }, []);

  // TODO(human): Implement the drag handlers below
  // You need to:
  // 1. In handleMouseDown: Calculate the offset between mouse position and element position
  // 2. In handleMouseMove: Update the position state based on mouse movement minus offset
  // 3. Add window bounds checking to prevent dragging off-screen
  // 4. Make sure to attach/remove event listeners on the window for mouseup and mousemove

  const handleMouseDown = (e: React.MouseEvent) => {
    // Your code here
  };

  const handleMouseMove = (e: MouseEvent) => {
    // Your code here
  };

  const handleMouseUp = () => {
    // Your code here
  };

  useEffect(() => {
    // Cleanup event listeners when component unmounts
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  return (
    <div
      ref={menuRef}
      className={`fixed z-[100] bg-white rounded-lg shadow-xl border border-gray-200 transition-shadow duration-300 ${isMinimized ? 'p-2' : 'p-4'} ${isDragging ? 'shadow-2xl cursor-grabbing' : 'cursor-grab'}`}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        right: 'auto', // Override the default right positioning
      }}
      onMouseDown={handleMouseDown}
    >
      {/* Toggle Button */}
      <button
        onClick={(e) => {
          e.stopPropagation(); // Prevent drag when clicking toggle
          setIsMinimized(!isMinimized);
        }}
        className="w-full flex items-center justify-between text-gray-700 hover:text-gray-900"
        title={isMinimized ? 'Expand navigation' : 'Minimize'}
      >
        <div className="flex items-center gap-2">
          <span className={`font-semibold ${isMinimized ? 'text-xs' : 'text-sm'}`}>
            {isMinimized ? '📋 Menu' : 'Quick Navigation'}
          </span>
          {/* TODO(human): Implement the notification badge display */}
          {/* Badge should show when criticalAlerts.length > 0 */}
          {/* Consider: different colors for different alert types, animations, positioning */}
          {criticalAlerts.length > 0 && (
            <span className="relative flex h-5 w-5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-5 w-5 items-center justify-center text-xs font-bold text-white bg-red-500">
                {criticalAlerts.length}
              </span>
            </span>
          )}
        </div>
        <span className="text-lg ml-2">
          {isMinimized ? '▶' : '▼'}
        </span>
      </button>

      {/* Content - Hidden when minimized */}
      {!isMinimized && (
        <div className="mt-3 space-y-2">
          {/* Critical Alerts Section */}
          {criticalAlerts.length > 0 && (
            <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-red-800">⚠️ Critical Alerts</h4>
                <button
                  onClick={dismissAllAlerts}
                  className="text-xs text-red-600 hover:text-red-800 underline"
                  title="Dismiss all alerts"
                >
                  Dismiss All
                </button>
              </div>
              <div className="space-y-1">
                {criticalAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="relative text-xs text-red-700 p-2 bg-white rounded hover:bg-red-100 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-1 flex-1">
                        <span className="font-semibold flex-shrink-0">
                          {alert.type === 'security' && '🔒'}
                          {alert.type === 'system' && '⚙️'}
                          {alert.type === 'deadline' && '⏰'}
                          {alert.type === 'error' && '❌'}
                        </span>
                        <div className="flex-1">
                          <span className="block">{alert.message}</span>
                          <span className="text-xs text-red-500 mt-1 block">
                            {formatTimestamp(alert.timestamp)}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => dismissAlert(alert.id)}
                        className="text-red-400 hover:text-red-600 font-bold text-sm leading-none"
                        title="Dismiss this alert"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <a
            href="/"
            className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
          >
            🚀 New Value-First Onboarding
          </a>
          <a
            href="/login"
            className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
          >
            🔐 Traditional Login
          </a>
          <a
            href="/register"
            className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
          >
            📝 Register New Account
          </a>
          <a
            href="/preview"
            className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
          >
            👁️ Quick Assessment Preview
          </a>
          <a
            href="/assessments"
            className="block text-sm text-indigo-600 hover:text-indigo-700 hover:underline"
          >
            📊 All Assessments (requires login)
          </a>

          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Test Credentials:<br />
              📧 test@example.com<br />
              🔑 test123
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default OnboardingNavigation;
