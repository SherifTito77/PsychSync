// // src/contexts/NotificationContext.tsx
// src/contexts/NotificationContext.tsx - Notification Management Context
import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react';
import { Notification } from '../types';
interface NotificationContextType {
  notifications: Notification[];
  showNotification: (message: string, type?: Notification['type'], duration?: number) => void;
  removeNotification: (id: number) => void;
}
const NotificationContext = createContext<NotificationContextType | undefined>(undefined);
export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};
interface NotificationProviderProps {
  children: ReactNode;
}
export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // ✅ MEMOIZED: Functions with useCallback
  const showNotification = useCallback((
    message: string,
    type: Notification['type'] = 'info',
    duration: number = 5000
  ): void => {
    const id = Date.now();
    const notification: Notification = {
      id,
      message,
      type,
      duration,
    };
    setNotifications((prev) => [...prev, notification]);
    if (duration > 0) {
      setTimeout(() => {
        setNotifications((prev) => prev.filter((notif) => notif.id !== id));
      }, duration);
    }
  }, []);

  const removeNotification = useCallback((id: number): void => {
    setNotifications((prev) => prev.filter((notif) => notif.id !== id));
  }, []);

  // ✅ MEMOIZED: Context value only changes when dependencies change
  const value: NotificationContextType = useMemo(() => ({
    notifications,
    showNotification,
    removeNotification,
  }), [notifications, showNotification, removeNotification]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};
