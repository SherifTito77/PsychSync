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
    <div
      className="fixed top-4 right-4 z-50 max-w-sm space-y-2"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
    >
      {notifications.map((notification: Notification) => (
        <div
          key={notification.id}
          role="alert"
          aria-live={notification.type === 'error' ? 'assertive' : 'polite'}
          className={getNotificationStyles(notification.type)}
        >
          <div className="flex justify-between items-start">
            <span className="flex-1 text-sm font-medium">
              {notification.message}
            </span>
            <button
              onClick={() => removeNotification(notification.id)}
              className="ml-2 text-lg leading-none opacity-70 hover:opacity-100 transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-current rounded-md p-1"
              aria-label={`Close ${notification.type} notification`}
            >
              <span className="sr-only">Close</span>
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
export default NotificationContainer;
