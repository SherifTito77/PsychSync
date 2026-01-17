/**
 * Biometric Authentication Settings Component
 *
 * Mobile-optimized interface for managing biometric authentication (Face ID, Touch ID, Fingerprint).
 * Allows users to register, authenticate, and manage biometric settings.
 *
 * Usage:
 * ```tsx
 * <BiometricAuthSettings onAuthenticationSuccess={(token) => console.log(token)} />
 * ```
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, Switch, ScrollView, Alert, Platform } from 'react-native';
import { useBiometricAuth } from '@/hooks/useBiometricAuth';

interface BiometricAuthSettingsProps {
  /**
   * Callback when authentication is successful
   */
  onAuthenticationSuccess?: (result: any) => void;

  /**
   * Callback when registration is successful
   */
  onRegistrationSuccess?: () => void;

  /**
   * Optional custom device ID
   */
  deviceId?: string;
}

export const BiometricAuthSettings: React.FC<BiometricAuthSettingsProps> = ({
  onAuthenticationSuccess,
  onRegistrationSuccess,
  deviceId,
}) => {
  const {
    isAvailable,
    isRegistered,
    isSupported,
    biometricType,
    isLoading,
    error,
    register,
    revoke,
    authenticate,
    checkStatus,
    refreshAvailability,
    deviceId: currentDeviceId,
    registeredDevices,
  } = useBiometricAuth({
    deviceId,
    checkAvailability: true,
    checkRegistration: true,
  });

  const [showTestAuth, setShowTestAuth] = useState(false);

  // Handle biometric registration
  const handleRegister = async () => {
    Alert.alert(
      'Enable Biometric Authentication',
      `Use ${getBiometricName()} to quickly and securely access your account. Your biometric data is stored securely on your device and never leaves it.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Enable',
          onPress: async () => {
            const success = await register();
            if (success) {
              Alert.alert(
                'Success',
                `${getBiometricName()} has been enabled for your account.`,
                [
                  {
                    text: 'OK',
                    onPress: () => onRegistrationSuccess?.(),
                  },
                ]
              );
            }
          },
        },
      ]
    );
  };

  // Handle biometric revocation
  const handleRevoke = async () => {
    Alert.alert(
      'Disable Biometric Authentication',
      'Are you sure you want to disable biometric authentication? You will need to use your password to sign in.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Disable',
          style: 'destructive',
          onPress: async () => {
            const success = await revoke();
            if (success) {
              Alert.alert('Disabled', 'Biometric authentication has been disabled.');
            }
          },
        },
      ]
    );
  };

  // Handle test authentication
  const handleTestAuth = async () => {
    const result = await authenticate();

    if (result.success && result.authenticated) {
      Alert.alert(
        'Authentication Successful',
        `${getBiometricName()} authentication worked perfectly!`,
        [
          {
            text: 'OK',
            onPress: () => onAuthenticationSuccess?.(result),
          },
        ]
      );
    }
  };

  // Get display name for biometric type
  const getBiometricName = () => {
    switch (biometricType) {
      case 'face_id':
        return 'Face ID';
      case 'touch_id':
        return 'Touch ID';
      case 'fingerprint':
        return 'Fingerprint';
      case 'iris':
        return 'Iris Scan';
      case 'face_unlock':
        return 'Face Unlock';
      default:
        return 'Biometric Authentication';
    }
  };

  // Get icon for biometric type
  const getBiometricIcon = () => {
    switch (biometricType) {
      case 'face_id':
      case 'face_unlock':
        return '👤';
      case 'touch_id':
      case 'fingerprint':
        return '👆';
      case 'iris':
        return '👁️';
      default:
        return '🔐';
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header Section */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Biometric Authentication</Text>
        <Text style={styles.headerSubtitle}>
          {isSupported
            ? `Use ${getBiometricName()} for secure, quick access`
            : 'Biometric authentication is not available on this device'}
        </Text>
      </View>

      {/* Availability Status */}
      {!isSupported && (
        <View style={styles.section}>
          <View style={styles.notSupportedBanner}>
            <Text style={styles.notSupportedIcon}>⚠️</Text>
            <Text style={styles.notSupportedTitle}>
              Biometric Authentication Not Available
            </Text>
            <Text style={styles.notSupportedText}>
              {Platform.OS === 'ios'
                ? 'Face ID or Touch ID is not available on this device. Biometric authentication requires an iPhone 5s or later with Touch ID, or iPhone X or later with Face ID.'
                : 'Fingerprint authentication is not available or not set up on this device. Please add a fingerprint in your device settings.'}
            </Text>
          </View>
        </View>
      )}

      {/* Main Settings Section */}
      {isSupported && (
        <View style={styles.section}>
          <View style={styles.enableRow}>
            <View style={styles.enableTextContainer}>
              <Text style={styles.enableLabel}>{getBiometricName()}</Text>
              <Text style={styles.enableDescription}>
                {isRegistered
                  ? 'Quickly authenticate with your biometric data'
                  : `Enable ${getBiometricName()} for faster, secure access`}
              </Text>
            </View>
            <Switch
              value={isRegistered}
              onValueChange={(value) => {
                if (value) {
                  handleRegister();
                } else {
                  handleRevoke();
                }
              }}
              disabled={isLoading || !isAvailable}
              trackColor={{ false: '#cbd5e1', true: '#6366F1' }}
              thumbColor="#ffffff"
            />
          </View>

          {/* Biometric Icon */}
          <View style={styles.iconContainer}>
            <Text style={styles.biometricIcon}>{getBiometricIcon()}</Text>
          </View>

          {/* Error Message */}
          {error && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <View style={styles.loadingBanner}>
              <Text style={styles.loadingText}>Processing...</Text>
            </View>
          )}
        </View>
      )}

      {/* Test Authentication Section */}
      {isRegistered && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Test Authentication</Text>
          <Text style={styles.testDescription}>
            Verify that {getBiometricName()} is working correctly by testing it now.
          </Text>
          <View style={styles.testButton}>
            <Text
              style={styles.testButtonText}
              onPress={handleTestAuth}
            >
              Test {getBiometricName()}
            </Text>
          </View>
        </View>
      )}

      {/* Registered Devices Section */}
      {registeredDevices.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Registered Devices</Text>
          {registeredDevices.map((device, index) => (
            <View key={index} style={styles.deviceCard}>
              <View style={styles.deviceInfo}>
                <Text style={styles.deviceName}>
                  {device.device_id === currentDeviceId ? 'This Device' : `Device ${index + 1}`}
                </Text>
                <Text style={styles.deviceDetails}>
                  {device.biometric_type} • Registered:{' '}
                  {new Date(device.registered_at).toLocaleDateString()}
                </Text>
              </View>
              {device.device_id === currentDeviceId && (
                <View style={styles.currentDeviceBadge}>
                  <Text style={styles.currentDeviceText}>Current</Text>
                </View>
              )}
            </View>
          ))}
        </View>
      )}

      {/* Security Information Section */}
      {isSupported && (
        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>🔒 Security Information</Text>
          <Text style={styles.infoText}>
            <Text style={styles.infoBold}>How it works:</Text> Your biometric data is
            encrypted and stored securely in the device's Secure Enclave (iOS) or
            TEE (Android). It never leaves your device.
          </Text>
          <Text style={styles.infoText}>
            <Text style={styles.infoBold}>Privacy:</Text> We do not store your actual
            biometric data (fingerprint, face scan) on our servers. Instead, we use
            cryptographic challenges to verify your identity.
          </Text>
          <Text style={styles.infoText}>
            <Text style={styles.infoBold}>Backup:</Text> You can always sign in with
            your password if {getBiometricName()} fails or is unavailable.
          </Text>
        </View>
      )}

      {/* Troubleshooting Section */}
      {isSupported && !isAvailable && (
        <View style={styles.troubleshootSection}>
          <Text style={styles.troubleshootTitle}>Troubleshooting</Text>
          <Text style={styles.troubleshootText}>
            If {getBiometricName()} is not working:
          </Text>
          <Text style={styles.troubleshootStep}>
            • Make sure {getBiometricName()} is set up in your device settings
          </Text>
          <Text style={styles.troubleshootStep}>
            • Ensure you have enrolled at least one {getBiometricName()} on your device
          </Text>
          <Text style={styles.troubleshootStep}>
            • Check that your device screen is clean and dry
          </Text>
          <Text style={styles.troubleshootStep}>
            • Try removing and re-adding your {getBiometricName()} in device settings
          </Text>
        </View>
      )}
    </ScrollView>
  );
};

// -----------------------------------------------------------------------------
// Styles
// -----------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 24,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#6b7280',
    lineHeight: 22,
  },
  section: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  enableRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  enableTextContainer: {
    flex: 1,
    marginRight: 12,
  },
  enableLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  enableDescription: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
  },
  iconContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  biometricIcon: {
    fontSize: 48,
  },
  errorBanner: {
    backgroundColor: '#FEE2E2',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  errorText: {
    fontSize: 14,
    color: '#991B1B',
    lineHeight: 20,
  },
  loadingBanner: {
    backgroundColor: '#EFF6FF',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 14,
    color: '#1E40AF',
  },
  notSupportedBanner: {
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    padding: 16,
  },
  notSupportedIcon: {
    fontSize: 32,
    textAlign: 'center',
    marginBottom: 8,
  },
  notSupportedTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#92400E',
    textAlign: 'center',
    marginBottom: 8,
  },
  notSupportedText: {
    fontSize: 14,
    color: '#92400E',
    lineHeight: 20,
    textAlign: 'center',
  },
  testDescription: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 12,
    lineHeight: 20,
  },
  testButton: {
    backgroundColor: '#6366F1',
    borderRadius: 8,
    padding: 14,
    alignItems: 'center',
  },
  testButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#ffffff',
  },
  deviceCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  deviceInfo: {
    flex: 1,
  },
  deviceName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 2,
  },
  deviceDetails: {
    fontSize: 13,
    color: '#6b7280',
  },
  currentDeviceBadge: {
    backgroundColor: '#10B981',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  currentDeviceText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  infoSection: {
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#6366F1',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E40AF',
    marginBottom: 12,
  },
  infoText: {
    fontSize: 14,
    color: '#1E40AF',
    lineHeight: 20,
    marginBottom: 12,
  },
  infoBold: {
    fontWeight: '600',
  },
  troubleshootSection: {
    backgroundColor: '#FFFBEB',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#F59E0B',
  },
  troubleshootTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#92400E',
    marginBottom: 8,
  },
  troubleshootText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#92400E',
    marginTop: 8,
    marginBottom: 4,
  },
  troubleshootStep: {
    fontSize: 14,
    color: '#92400E',
    lineHeight: 20,
    marginLeft: 8,
  },
});

export default BiometricAuthSettings;
