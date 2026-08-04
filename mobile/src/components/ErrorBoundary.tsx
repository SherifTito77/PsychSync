/**
 * Error Boundary Component
 * Catches JavaScript errors anywhere in the child component tree
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Platform } from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log the error to console and potentially to an error reporting service
    console.error('Error caught by ErrorBoundary:', error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });

    // TODO: Send error to error reporting service (e.g., Sentry)
    // Sentry.captureException(error, { contexts: { react: errorInfo } });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    this.handleReset();
    // In a real app, you might want to reload the app or navigate to a safe screen
    // For now, just reset the error state
  };

  render() {
    if (this.state.hasError) {
      const isDev = __DEV__;

      return (
        <View style={styles.container}>
          <ScrollView contentContainerStyle={styles.content}>
            <View style={styles.iconContainer}>
              <MaterialIcons name="error-outline" size={64} color="#ef4444" />
            </View>

            <Text style={styles.title}>Oops! Something went wrong</Text>
            <Text style={styles.message}>
              {isDev
                ? 'An error occurred. Check the details below.'
                : 'We encountered an unexpected error. Please try again.'}
            </Text>

            {isDev && this.state.error && (
              <View style={styles.errorDetails}>
                <Text style={styles.errorTitle}>Error Details:</Text>
                <Text style={styles.errorText}>
                  {this.state.error.toString()}
                  {'\n\n'}
                  {this.state.errorInfo?.componentStack}
                </Text>
              </View>
            )}

            <TouchableOpacity style={styles.button} onPress={this.handleReload}>
              <Text style={styles.buttonText}>Try Again</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              onPress={this.handleReset}
            >
              <Text style={[styles.buttonText, styles.secondaryButtonText]}>
                Dismiss
              </Text>
            </TouchableOpacity>

            {!isDev && (
              <Text style={styles.supportText}>
                If this problem persists, please contact support
              </Text>
            )}
          </ScrollView>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  content: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  iconContainer: {
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    textAlign: 'center',
    marginBottom: 12,
  },
  message: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 32,
    paddingHorizontal: 16,
  },
  errorDetails: {
    backgroundColor: '#fee2e2',
    borderRadius: 8,
    padding: 16,
    marginBottom: 24,
    width: '100%',
    maxWidth: 600,
  },
  errorTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#991b1b',
    marginBottom: 8,
  },
  errorText: {
    fontSize: 12,
    color: '#7f1d1d',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  button: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
    marginBottom: 12,
    minWidth: 200,
    alignItems: 'center',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  secondaryButtonText: {
    color: '#374151',
  },
  supportText: {
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'center',
    marginTop: 24,
  },
});
