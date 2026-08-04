/**
 * Authentication Navigator - Handles login/register flow
 */

import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { LoginScreen } from '../screens/LoginScreen';
import { RegisterScreen } from '../screens/RegisterScreen';
import { AppNavigator } from '../navigation/AppNavigator';
import { apiService } from '../services/api';

type AuthState = 'loading' | 'authenticated' | 'login' | 'register';

export const AuthNavigator: React.FC = () => {
  const [authState, setAuthState] = useState<AuthState>('loading');

  useEffect(() => {
    // On web, SecureStore doesn't work, so default to login immediately
    if (Platform.OS === 'web') {
      setAuthState('login');
      return;
    }

    // Small delay to ensure token loading completes on native
    const timer = setTimeout(() => {
      checkAuthStatus();
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  const checkAuthStatus = async () => {
    // Check if user has a valid token
    if (apiService.isAuthenticated()) {
      setAuthState('authenticated');
    } else {
      setAuthState('login');
    }
  };

  const handleLoginSuccess = () => {
    setAuthState('authenticated');
  };

  const handleRegisterSuccess = () => {
    // After registration, navigate to login
    setAuthState('login');
  };

  const handleLogout = () => {
    setAuthState('login');
  };

  if (authState === 'loading') {
    return <View style={styles.loadingContainer} />;
  }

  if (authState === 'authenticated') {
    return <AppNavigator onLogout={handleLogout} />;
  }

  if (authState === 'register') {
    return (
      <RegisterScreen
        onRegisterSuccess={handleRegisterSuccess}
        onNavigateToLogin={() => setAuthState('login')}
      />
    );
  }

  // Default to login
  return (
    <LoginScreen
      onLoginSuccess={handleLoginSuccess}
      onNavigateToRegister={() => setAuthState('register')}
    />
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
});
