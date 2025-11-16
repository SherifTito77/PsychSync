// // src/components/common/NotificationContainer    
// src/components/common/NotificationContainer.tsx - Clean Notification Container
import React from 'react';
import { useNotification } from '../../contexts/NotificationContext';
import { Notification } from '../../types';
const NotificationContainer: React.FC = () => {
  const { notifications, removeNotification } = useNotification();
  const getNotificationStyles = (type: Notification['type']): string => {
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
  if (notifications.length === 0) {
    return null;
  }
  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm space-y-2">
      {notifications.map((notification: Notification) => (
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
              className="ml-2 text-lg leading-none opacity-70 hover:opacity-100 transition-opacity"
              aria-label="Close notification"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
export default NotificationContainer;
