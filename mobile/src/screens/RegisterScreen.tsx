/**
 * Register Screen for PsychSync Mobile
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { apiService } from '../services/api';
import { MaterialIcons } from '@expo/vector-icons';

interface Props {
  onRegisterSuccess: () => void;
  onNavigateToLogin: () => void;
}

export const RegisterScreen: React.FC<Props> = ({
  onRegisterSuccess,
  onNavigateToLogin,
}) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<{
    full_name?: string;
    email?: string;
    password?: string;
    confirm_password?: string;
  }>({});
  const [acceptTerms, setAcceptTerms] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: {
      full_name?: string;
      email?: string;
      password?: string;
      confirm_password?: string;
    } = {};

    if (!fullName.trim()) {
      newErrors.full_name = 'Full name is required';
    } else if (fullName.trim().length < 2) {
      newErrors.full_name = 'Name must be at least 2 characters';
    }

    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
      newErrors.password =
        'Password must contain uppercase, lowercase, and number';
    }

    if (password !== confirmPassword) {
      newErrors.confirm_password = 'Passwords do not match';
    }

    if (!acceptTerms) {
      Alert.alert('Terms Required', 'Please accept the Terms of Service');
      return false;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleRegister = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.register({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
      });

      if (response.success) {
        Alert.alert(
          'Registration Successful',
          'Please check your email to verify your account.',
          [
            {
              text: 'OK',
              onPress: onNavigateToLogin,
            },
          ]
        );
      } else {
        Alert.alert('Registration Failed', response.error || 'Please try again');
      }
    } catch (error) {
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <View style={styles.content}>
          {/* Logo/Header */}
          <View style={styles.header}>
            <MaterialIcons name="psychology" size={64} color="#3b82f6" />
            <Text style={styles.title}>Create Account</Text>
            <Text style={styles.subtitle}>Start monitoring your emails today</Text>
          </View>

          {/* Register Form */}
          <View style={styles.form}>
            {/* Full Name Input */}
            <View style={styles.inputContainer}>
              <MaterialIcons name="person" size={20} color="#6b7280" style={styles.inputIcon} />
              <TextInput
                style={[styles.input, errors.full_name && styles.inputError]}
                placeholder="Full name"
                placeholderTextColor="#9ca3af"
                value={fullName}
                onChangeText={setFullName}
                autoCapitalize="words"
                autoComplete="name"
                editable={!loading}
              />
            </View>
            {errors.full_name && <Text style={styles.errorText}>{errors.full_name}</Text>}

            {/* Email Input */}
            <View style={styles.inputContainer}>
              <MaterialIcons name="email" size={20} color="#6b7280" style={styles.inputIcon} />
              <TextInput
                style={[styles.input, errors.email && styles.inputError]}
                placeholder="Email address"
                placeholderTextColor="#9ca3af"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                autoComplete="email"
                keyboardType="email-address"
                editable={!loading}
              />
            </View>
            {errors.email && <Text style={styles.errorText}>{errors.email}</Text>}

            {/* Password Input */}
            <View style={styles.inputContainer}>
              <MaterialIcons name="lock" size={20} color="#6b7280" style={styles.inputIcon} />
              <TextInput
                style={[styles.input, errors.password && styles.inputError]}
                placeholder="Password"
                placeholderTextColor="#9ca3af"
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPassword}
                autoComplete="password-new"
                editable={!loading}
              />
              <TouchableOpacity
                onPress={() => setShowPassword(!showPassword)}
                style={styles.eyeIcon}
              >
                <MaterialIcons
                  name={showPassword ? 'visibility' : 'visibility-off'}
                  size={20}
                  color="#6b7280"
                />
              </TouchableOpacity>
            </View>
            {errors.password && <Text style={styles.errorText}>{errors.password}</Text>}

            {/* Confirm Password Input */}
            <View style={styles.inputContainer}>
              <MaterialIcons name="lock-outline" size={20} color="#6b7280" style={styles.inputIcon} />
              <TextInput
                style={[styles.input, errors.confirm_password && styles.inputError]}
                placeholder="Confirm password"
                placeholderTextColor="#9ca3af"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry={!showConfirmPassword}
                autoComplete="password-new"
                editable={!loading}
              />
              <TouchableOpacity
                onPress={() => setShowConfirmPassword(!showConfirmPassword)}
                style={styles.eyeIcon}
              >
                <MaterialIcons
                  name={showConfirmPassword ? 'visibility' : 'visibility-off'}
                  size={20}
                  color="#6b7280"
                />
              </TouchableOpacity>
            </View>
            {errors.confirm_password && (
              <Text style={styles.errorText}>{errors.confirm_password}</Text>
            )}

            {/* Terms Checkbox */}
            <TouchableOpacity
              style={styles.termsContainer}
              onPress={() => setAcceptTerms(!acceptTerms)}
              disabled={loading}
            >
              <MaterialIcons
                name={acceptTerms ? 'check-box' : 'check-box-outline-blank'}
                size={24}
                color={acceptTerms ? '#3b82f6' : '#9ca3af'}
              />
              <View style={styles.termsTextContainer}>
                <Text style={styles.termsText}>
                  I accept the{' '}
                  <Text style={styles.termsLink}>Terms of Service</Text>
                  {' '}and{' '}
                  <Text style={styles.termsLink}>Privacy Policy</Text>
                </Text>
              </View>
            </TouchableOpacity>

            {/* Register Button */}
            <TouchableOpacity
              style={[styles.registerButton, loading && styles.registerButtonDisabled]}
              onPress={handleRegister}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <Text style={styles.registerButtonText}>Create Account</Text>
              )}
            </TouchableOpacity>

            {/* Login Link */}
            <View style={styles.loginContainer}>
              <Text style={styles.loginText}>Already have an account? </Text>
              <TouchableOpacity onPress={onNavigateToLogin} disabled={loading}>
                <Text style={styles.loginLink}>Sign In</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 16,
  },
  subtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  form: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    paddingVertical: 14,
    fontSize: 16,
    color: '#111827',
  },
  inputError: {
    borderColor: '#ef4444',
  },
  eyeIcon: {
    padding: 8,
  },
  errorText: {
    fontSize: 12,
    color: '#ef4444',
    marginBottom: 12,
    marginLeft: 4,
  },
  termsContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 12,
    marginBottom: 24,
  },
  termsTextContainer: {
    flex: 1,
    marginLeft: 12,
  },
  termsText: {
    fontSize: 13,
    color: '#6b7280',
    lineHeight: 18,
  },
  termsLink: {
    color: '#3b82f6',
    fontWeight: '500',
  },
  registerButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  registerButtonDisabled: {
    backgroundColor: '#9ca3af',
  },
  registerButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  loginContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginText: {
    fontSize: 14,
    color: '#6b7280',
  },
  loginLink: {
    fontSize: 14,
    color: '#3b82f6',
    fontWeight: '600',
  },
});
