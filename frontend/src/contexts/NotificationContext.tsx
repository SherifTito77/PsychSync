// src/contexts/NotificationContext.tsx
import React, { createContext, useContext, useState } from 'react';
import { NotificationContextType } from '../types/contexts';
import { Notification } from '../types';

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const showNotification = (
    message: string,
    type: Notification['type'] = 'info',
    duration: number = 5000
  ): void => {
    const id = Date.now();
    const notification: Notification = {
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

  const removeNotification = (id: number): void => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const value: NotificationContextType = {
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
