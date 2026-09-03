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
import { DESIGN_TOKENS } from '@/constants/designTokens';

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
    backgroundColor: DESIGN_TOKENS.colors.gray[50],
  },
  contentContainer: {
    padding: DESIGN_TOKENS.spacing.md,
    paddingBottom: DESIGN_TOKENS.spacing['2xl'],
  },
  header: {
    marginBottom: DESIGN_TOKENS.spacing.lg,
  },
  headerTitle: {
    fontSize: DESIGN_TOKENS.typography.size['3xl'],
    fontWeight: DESIGN_TOKENS.typography.weight.bold as any,
    color: DESIGN_TOKENS.colors.gray[900],
    marginBottom: DESIGN_TOKENS.spacing.xs,
  },
  headerSubtitle: {
    fontSize: DESIGN_TOKENS.typography.size.base,
    color: DESIGN_TOKENS.colors.gray[500],
    lineHeight: 22,
  },
  section: {
    backgroundColor: DESIGN_TOKENS.colors.gray[50],
    borderRadius: DESIGN_TOKENS.radius.lg,
    padding: DESIGN_TOKENS.spacing.md,
    marginBottom: DESIGN_TOKENS.spacing.md,
    ...DESIGN_TOKENS.shadow.sm,
  },
  sectionTitle: {
    fontSize: DESIGN_TOKENS.typography.size.lg,
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
    color: DESIGN_TOKENS.colors.gray[900],
    marginBottom: DESIGN_TOKENS.spacing.md,
  },
  enableRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: DESIGN_TOKENS.spacing.md,
  },
  enableTextContainer: {
    flex: 1,
    marginRight: DESIGN_TOKENS.spacing.md,
  },
  enableLabel: {
    fontSize: DESIGN_TOKENS.typography.size.base,
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
    color: DESIGN_TOKENS.colors.gray[900],
    marginBottom: DESIGN_TOKENS.spacing.xs,
  },
  enableDescription: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    color: DESIGN_TOKENS.colors.gray[500],
    lineHeight: 20,
  },
  iconContainer: {
    alignItems: 'center',
    paddingVertical: DESIGN_TOKENS.spacing.lg,
  },
  biometricIcon: {
    fontSize: 48,
  },
  errorBanner: {
    backgroundColor: '#FEE2E2',
    borderRadius: DESIGN_TOKENS.radius.md,
    padding: DESIGN_TOKENS.spacing.md,
    marginTop: DESIGN_TOKENS.spacing.md,
  },
  errorText: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    color: '#991B1B',
    lineHeight: 20,
  },
  loadingBanner: {
    backgroundColor: '#EFF6FF',
    borderRadius: DESIGN_TOKENS.radius.md,
    padding: DESIGN_TOKENS.spacing.md,
    marginTop: DESIGN_TOKENS.spacing.md,
    alignItems: 'center',
  },
  loadingText: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    color: DESIGN_TOKENS.colors.primary[800],
  },
  notSupportedBanner: {
    backgroundColor: '#FEF3C7',
    borderRadius: DESIGN_TOKENS.radius.md,
    padding: DESIGN_TOKENS.spacing.md,
  },
  notSupportedIcon: {
    fontSize: DESIGN_TOKENS.typography.size['3xl'],
    textAlign: 'center',
    marginBottom: DESIGN_TOKENS.spacing.sm,
  },
  notSupportedTitle: {
    fontSize: DESIGN_TOKENS.typography.size.base,
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
    color: '#92400E',
    textAlign: 'center',
    marginBottom: DESIGN_TOKENS.spacing.sm,
  },
  notSupportedText: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    color: '#92400E',
    lineHeight: 20,
    textAlign: 'center',
  },
  testDescription: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    color: DESIGN_TOKENS.colors.gray[500],
    marginBottom: DESIGN_TOKENS.spacing.md,
    lineHeight: 20,
  },
  testButton: {
    backgroundColor: '#6366F1',
    borderRadius: DESIGN_TOKENS.radius.md,
    padding: DESIGN_TOKENS.spacing.md,
    alignItems: 'center',
  },
  testButtonText: {
    fontSize: DESIGN_TOKENS.typography.size.base,
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
    color: DESIGN_TOKENS.colors.gray[50],
  },
  deviceCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: DESIGN_TOKENS.colors.gray[50],
    borderRadius: DESIGN_TOKENS.radius.md,
    padding: DESIGN_TOKENS.spacing.md,
    marginBottom: DESIGN_TOKENS.spacing.sm,
  },
  deviceInfo: {
    flex: 1,
  },
  deviceName: {
    fontSize: DESIGN_TOKENS.typography.size.base,
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
    color: DESIGN_TOKENS.colors.gray[900],
    marginBottom: DESIGN_TOKENS.spacing.xs,
  },
  deviceDetails: {
    fontSize: DESIGN_TOKENS.typography.size.xs,
    color: DESIGN_TOKENS.colors.gray[500],
  },
  currentDeviceBadge: {
    backgroundColor: DESIGN_TOKENS.colors.success,
    paddingHorizontal: DESIGN_TOKENS.spacing.sm,
    paddingVertical: DESIGN_TOKENS.spacing.xs,
    borderRadius: DESIGN_TOKENS.radius.lg,
  },
  currentDeviceText: {
    fontSize: DESIGN_TOKENS.typography.size.xs,
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
    color: DESIGN_TOKENS.colors.gray[50],
  },
  infoSection: {
    backgroundColor: '#EFF6FF',
    borderRadius: DESIGN_TOKENS.radius.lg,
    padding: DESIGN_TOKENS.spacing.md,
    borderLeftWidth: 4,
    borderLeftColor: '#6366F1',
  },
  infoTitle: {
    fontSize: DESIGN_TOKENS.typography.size.base,
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
    color: DESIGN_TOKENS.colors.primary[800],
    marginBottom: DESIGN_TOKENS.spacing.md,
  },
  infoText: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    color: DESIGN_TOKENS.colors.primary[800],
    lineHeight: 20,
    marginBottom: DESIGN_TOKENS.spacing.md,
  },
  infoBold: {
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
  },
  troubleshootSection: {
    backgroundColor: '#FFFBEB',
    borderRadius: DESIGN_TOKENS.radius.lg,
    padding: DESIGN_TOKENS.spacing.md,
    borderLeftWidth: 4,
    borderLeftColor: DESIGN_TOKENS.colors.warning,
  },
  troubleshootTitle: {
    fontSize: DESIGN_TOKENS.typography.size.base,
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
    color: '#92400E',
    marginBottom: DESIGN_TOKENS.spacing.sm,
  },
  troubleshootText: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    fontWeight: DESIGN_TOKENS.typography.weight.semibold as any,
    color: '#92400E',
    marginTop: DESIGN_TOKENS.spacing.sm,
    marginBottom: DESIGN_TOKENS.spacing.xs,
  },
  troubleshootStep: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    color: '#92400E',
    lineHeight: 20,
    marginLeft: DESIGN_TOKENS.spacing.sm,
  },
});

export default BiometricAuthSettings;
