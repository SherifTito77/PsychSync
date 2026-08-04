/**
 * Add Email Connection Modal
 * Allows users to add a new email connection
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import { apiService } from '../services/api';

interface Props {
  visible: boolean;
  onClose: () => void;
  onConnectionAdded: () => void;
}

const EMAIL_PROVIDERS = [
  { id: 'gmail', name: 'Gmail', icon: '📧', server: 'imap.gmail.com', port: 993 },
  { id: 'outlook', name: 'Outlook', icon: '🔷', server: 'outlook.office365.com', port: 993 },
  { id: 'yahoo', name: 'Yahoo', icon: '📬', server: 'imap.mail.yahoo.com', port: 993 },
  { id: 'icloud', name: 'iCloud', icon: '☁️', server: 'imap.mail.me.com', port: 993 },
  { id: 'custom', name: 'Custom IMAP', icon: '⚙️', server: '', port: 993 },
];

export const AddEmailConnectionModal: React.FC<Props> = ({
  visible,
  onClose,
  onConnectionAdded,
}) => {
  const [step, setStep] = useState<'provider' | 'credentials' | 'testing'>('provider');
  const [selectedProvider, setSelectedProvider] = useState<typeof EMAIL_PROVIDERS[0] | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [server, setServer] = useState('');
  const [port, setPort] = useState('993');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const resetForm = () => {
    setStep('provider');
    setSelectedProvider(null);
    setEmail('');
    setPassword('');
    setServer('');
    setPort('993');
    setShowPassword(false);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleProviderSelect = (provider: typeof EMAIL_PROVIDERS[0]) => {
    setSelectedProvider(provider);
    if (provider.id === 'custom') {
      setServer('');
      setPort('993');
    } else {
      setServer(provider.server);
      setPort(provider.port.toString());
    }
    setStep('credentials');
  };

  const handleTestConnection = async () => {
    if (!email.trim() || !password) {
      Alert.alert('Validation Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);
    setStep('testing');

    try {
      const response = await apiService.testEmailConnection({
        email_provider: selectedProvider?.id || 'custom',
        email_address: email.trim(),
        password,
        server: server.trim(),
        port: parseInt(port, 10),
      });

      if (response.success) {
        // Connection successful, now set it up
        const setupResponse = await apiService.setupEmailConnection({
          email_provider: selectedProvider?.id || 'custom',
          email_address: email.trim(),
          password,
          server: server.trim(),
          port: parseInt(port, 10),
        });

        if (setupResponse.success) {
          Alert.alert('Success', 'Email connection added successfully!', [
            {
              text: 'OK',
              onPress: () => {
                onConnectionAdded();
                handleClose();
              },
            },
          ]);
        } else {
          Alert.alert('Setup Failed', setupResponse.error || 'Failed to save connection');
          setStep('credentials');
        }
      } else {
        Alert.alert('Connection Failed', response.error || 'Could not connect to email server');
        setStep('credentials');
      }
    } catch (error) {
      Alert.alert('Error', 'Network error. Please try again.');
      setStep('credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
            <MaterialIcons name="close" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>
            {step === 'provider'
              ? 'Select Provider'
              : step === 'credentials'
              ? 'Enter Credentials'
              : 'Testing Connection'}
          </Text>
          <View style={styles.placeholder} />
        </View>

        <ScrollView style={styles.content}>
          {/* Step 1: Provider Selection */}
          {step === 'provider' && (
            <View style={styles.stepContent}>
              <Text style={styles.stepDescription}>
                Choose your email provider to get started
              </Text>
              {EMAIL_PROVIDERS.map((provider) => (
                <TouchableOpacity
                  key={provider.id}
                  style={styles.providerCard}
                  onPress={() => handleProviderSelect(provider)}
                >
                  <Text style={styles.providerIcon}>{provider.icon}</Text>
                  <View style={styles.providerInfo}>
                    <Text style={styles.providerName}>{provider.name}</Text>
                    {provider.id !== 'custom' && (
                      <Text style={styles.providerServer}>{provider.server}</Text>
                    )}
                  </View>
                  <MaterialIcons name="chevron-right" size={24} color="#9ca3af" />
                </TouchableOpacity>
              ))}
            </View>
          )}

          {/* Step 2: Credentials */}
          {step === 'credentials' && (
            <View style={styles.stepContent}>
              <TouchableOpacity
                onPress={() => setStep('provider')}
                style={styles.backButton}
              >
                <MaterialIcons name="arrow-back" size={20} color="#3b82f6" />
                <Text style={styles.backButtonText}>Change provider</Text>
              </TouchableOpacity>

              <View style={styles.selectedProviderCard}>
                <Text style={styles.providerIcon}>{selectedProvider?.icon}</Text>
                <Text style={styles.selectedProviderName}>
                  {selectedProvider?.name}
                </Text>
              </View>

              <Text style={styles.inputLabel}>Email Address</Text>
              <View style={styles.inputContainer}>
                <MaterialIcons name="email" size={20} color="#6b7280" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="your@email.com"
                  placeholderTextColor="#9ca3af"
                  value={email}
                  onChangeText={setEmail}
                  autoCapitalize="none"
                  autoComplete="email"
                  keyboardType="email-address"
                  editable={!loading}
                />
              </View>

              <Text style={styles.inputLabel}>Password / App Password</Text>
              <View style={styles.inputContainer}>
                <MaterialIcons name="lock" size={20} color="#6b7280" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Enter password"
                  placeholderTextColor="#9ca3af"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                  autoComplete="password"
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

              {selectedProvider?.id === 'custom' && (
                <>
                  <Text style={styles.inputLabel}>IMAP Server</Text>
                  <View style={styles.inputContainer}>
                    <MaterialIcons name="dns" size={20} color="#6b7280" style={styles.inputIcon} />
                    <TextInput
                      style={styles.input}
                      placeholder="imap.example.com"
                      placeholderTextColor="#9ca3af"
                      value={server}
                      onChangeText={setServer}
                      autoCapitalize="none"
                      editable={!loading}
                    />
                  </View>

                  <Text style={styles.inputLabel}>Port</Text>
                  <View style={styles.inputContainer}>
                    <MaterialIcons name="settings" size={20} color="#6b7280" style={styles.inputIcon} />
                    <TextInput
                      style={styles.input}
                      placeholder="993"
                      placeholderTextColor="#9ca3af"
                      value={port}
                      onChangeText={setPort}
                      keyboardType="number-pad"
                      editable={!loading}
                    />
                  </View>
                </>
              )}

              <Text style={styles.helpText}>
                💡 Tip: For Gmail, use an App Password instead of your regular password
              </Text>

              <TouchableOpacity
                style={styles.connectButton}
                onPress={handleTestConnection}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#ffffff" />
                ) : (
                  <Text style={styles.connectButtonText}>Connect Account</Text>
                )}
              </TouchableOpacity>
            </View>
          )}

          {/* Step 3: Testing */}
          {step === 'testing' && (
            <View style={[styles.stepContent, styles.testingContent]}>
              <ActivityIndicator size="large" color="#3b82f6" />
              <Text style={styles.testingTitle}>Testing Connection...</Text>
              <Text style={styles.testingSubtitle}>
                We're verifying your email credentials. This may take a moment.
              </Text>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  closeButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  placeholder: {
    width: 40,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  stepContent: {
    paddingVertical: 16,
  },
  stepDescription: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 24,
    textAlign: 'center',
  },
  providerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  providerIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  providerInfo: {
    flex: 1,
  },
  providerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  providerServer: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  backButtonText: {
    fontSize: 14,
    color: '#3b82f6',
    marginLeft: 4,
    fontWeight: '500',
  },
  selectedProviderCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#eff6ff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  selectedProviderName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#3b82f6',
    marginLeft: 12,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
    marginTop: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 16,
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
  eyeIcon: {
    padding: 8,
  },
  helpText: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 16,
    marginBottom: 24,
    textAlign: 'center',
    lineHeight: 16,
  },
  connectButton: {
    backgroundColor: '#3b82f6',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  connectButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  testingContent: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  testingTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginTop: 24,
  },
  testingSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 8,
    textAlign: 'center',
  },
});
