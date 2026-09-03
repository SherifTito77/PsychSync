/**
 * PsychSync Mobile - Main App Component
 *
 * Provides:
 * - Authentication context
 * - Navigation structure
 * - Global state management
 * - Offline capability
 */

import React from 'react';
import { StatusBar, SafeAreaView, View, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';
import { AuthProvider } from './contexts/AuthContext';
import { AssessmentProvider } from './contexts/AssessmentContext';
import AppNavigator from './navigation/AppNavigator';
import { theme } from './constants/theme';

const App: React.FC = () => {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <PaperProvider theme={theme}>
        <AuthProvider>
          <AssessmentProvider>
            <NavigationContainer>
              <AppNavigator />
            </NavigationContainer>
          </AssessmentProvider>
        </AuthProvider>
      </PaperProvider>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
});

export default App;
