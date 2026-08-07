// // src/contexts/NotificationContext.tsx
// src/contexts/NotificationContext.tsx - Notification Management Context
//
// FIXED: Memory leaks from setTimeout cleanup - now tracks and cleans up timeouts

import React, { createContext, useContext, useState, useCallback, useMemo, useRef, ReactNode } from 'react';
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

  // Track timeout IDs for cleanup - FIXED: Prevents memory leaks
  const timeoutRefs = useRef<Map<number, NodeJS.Timeout>>(new Map());

  // Clean up all timeouts on unmount
  React.useEffect(() => {
    return () => {
      // Clear all pending timeouts when provider unmounts
      timeoutRefs.current.forEach((timeoutId) => clearTimeout(timeoutId));
      timeoutRefs.current.clear();
    };
  }, []);

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

    // Auto-dismiss after duration - FIXED: Now tracks timeout for cleanup
    if (duration > 0) {
      const timeoutId = setTimeout(() => {
        setNotifications((prev) => prev.filter((notif) => notif.id !== id));
        // Clean up timeout ref after execution
        timeoutRefs.current.delete(id);
      }, duration);

      // Store timeout ref for cleanup
      timeoutRefs.current.set(id, timeoutId);
    }
  }, []);

  const removeNotification = useCallback((id: number): void => {
    // Clear timeout if it exists for this notification
    const timeoutId = timeoutRefs.current.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutRefs.current.delete(id);
    }

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
