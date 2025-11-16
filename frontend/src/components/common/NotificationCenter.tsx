import React, { useState, useEffect } from 'react';
import {
  Bell,
  X,
  Check,
  Clock,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { websocketService, NotificationMessage } from '../../services/websocketService';
import Button from './Button';
import Badge from './Badge';
import { cn } from '../../utils/cn';
interface NotificationCenterProps {
  className?: string;
}
export const NotificationCenter: React.FC<NotificationCenterProps> = ({ className }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      websocketService.connect(token);
      websocketService.on('connected', () => setIsConnected(true));
      websocketService.on('disconnected', () => setIsConnected(false));
      websocketService.on('notification', handleNewNotification);
      // Request browser notification permission
      if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }
      return () => {
        websocketService.off('notification', handleNewNotification);
      };
    }
  }, []);
  const handleNewNotification = (notification: NotificationMessage) => {
    setNotifications(prev => [notification, ...prev]);
    setUnreadCount(prev => prev + 1);
    // Show browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        tag: notification.id,
      });
    }
  };
  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id
          ? { ...notification, read: true }
          : notification
      )
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
    websocketService.sendNotificationRead(id);
  };
  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(notification => ({ ...notification, read: true }))
    );
    setUnreadCount(0);
  };
  const clearNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
  };
  const getNotificationIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };
  return (
    <div className={cn('relative', className)}>
      {/* Notification Bell */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <Badge
            color="red"
            className="absolute -top-1 -right-1 min-w-[20px] h-5 flex items-center justify-center text-xs"
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </Badge>
        )}
        {isConnected && (
          <div className="absolute bottom-1 right-1 w-2 h-2 bg-green-500 rounded-full" />
        )}
      </button>
      {/* Notification Dropdown */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-[500px] overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-gray-900">Notifications</h3>
                <div className={cn(
                  'w-2 h-2 rounded-full',
                  isConnected ? 'bg-green-500' : 'bg-gray-300'
                )} />
                <span className="text-xs text-gray-500">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {unreadCount > 0 && (
                  <Button
                    variant="outline"
                    size="small"
                    onClick={markAllAsRead}
                    icon={<Check className="w-4 h-4" />}
                  >
                    Mark all read
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="small"
                  onClick={clearNotifications}
                  icon={<X className="w-4 h-4" />}
                >
                  Clear
                </Button>
              </div>
            </div>
            {/* Notifications List */}
            <div className="overflow-y-auto max-h-[400px]">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <Bell className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>No notifications</p>
                </div>
              ) : (
                notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={cn(
                      'p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors',
                      !notification.read && 'bg-blue-50'
                    )}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <div className="flex items-start space-x-3">
                      {getNotificationIcon(notification.severity)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-sm font-semibold text-gray-900 truncate">
                            {notification.title}
                          </h4>
                          <span className="text-xs text-gray-500">
                            {formatTime(notification.timestamp)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{notification.message}</p>
                        {notification.type && (
                          <Badge
                            color="gray"
                            size="sm"
                            className="mt-2 inline-block"
                          >
                            {notification.type}
                          </Badge>
                        )}
                      </div>
                      {!notification.read && (
                        <div className="w-2 h-2 bg-blue-600 rounded-full mt-1" />
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
            {/* Footer */}
            <div className="p-3 border-t border-gray-200 bg-gray-50">
              <div className="text-center">
                <a
                  href="/settings/notifications"
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Notification Settings
                </a>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
// Floating Notification Container for temporary notifications
interface FloatingNotificationProps {
  notification: NotificationMessage;
  onClose: () => void;
}
const FloatingNotification: React.FC<FloatingNotificationProps> = ({
  notification,
  onClose
}) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);
  const getNotificationStyles = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'bg-red-500 text-white';
      case 'warning':
        return 'bg-yellow-500 text-white';
      case 'success':
        return 'bg-green-500 text-white';
      default:
        return 'bg-blue-500 text-white';
    }
  };
  return (
    <div
      className={cn(
        'fixed top-4 right-4 z-50 max-w-sm p-4 rounded-lg shadow-lg transform transition-all duration-300',
        getNotificationStyles(notification.severity)
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-semibold">{notification.title}</h4>
          <p className="text-sm opacity-90">{notification.message}</p>
        </div>
        <button
          onClick={onClose}
          className="ml-4 opacity-70 hover:opacity-100"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
export const NotificationContainer: React.FC = () => {
  const [floatingNotifications, setFloatingNotifications] = useState<NotificationMessage[]>([]);
  const addFloatingNotification = (notification: Omit<NotificationMessage, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: NotificationMessage = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      read: false,
    };
    setFloatingNotifications(prev => [...prev, newNotification]);
  };
  const removeFloatingNotification = (id: string) => {
    setFloatingNotifications(prev => prev.filter(n => n.id !== id));
  };
  // Expose the addFloatingNotification function globally
  useEffect(() => {
    (window as any).showNotification = addFloatingNotification;
    return () => {
      delete (window as any).showNotification;
    };
  }, []);
  return (
    <>
      {floatingNotifications.map((notification) => (
        <FloatingNotification
          key={notification.id}
          notification={notification}
          onClose={() => removeFloatingNotification(notification.id)}
        />
      ))}
    </>
  );
};