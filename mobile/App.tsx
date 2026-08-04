import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ThemeProvider } from './src/contexts/ThemeContext';
import { ErrorBoundary } from './src/components/ErrorBoundary';
import { AuthNavigator } from './src/components/AuthNavigator';
import { notificationService } from './src/services/notifications';

function AppContent() {
  useEffect(() => {
    // Register for push notifications on app start
    notificationService.registerForPushNotifications();
  }, []);

  return (
    <>
      <AuthNavigator />
      <StatusBar style="auto" />
    </>
  );
}

export default function App() {
  return (
    <SafeAreaProvider>
      <ErrorBoundary>
        <ThemeProvider>
          <AppContent />
        </ThemeProvider>
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}
