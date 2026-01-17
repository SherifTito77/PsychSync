/**
 * Push Notification Settings Component
 *
 * Mobile-optimized interface for managing push notification preferences.
 * Allows users to enable/disable notifications, choose notification types,
 * view active devices, and test notification delivery.
 *
 * Usage:
 * ```tsx
 * <PushNotificationSettings getFCMToken={() => getFCMTokenFromMobile()} />
 * ```
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Switch, ScrollView, Alert, Platform } from 'react-native';
import { usePushNotifications } from '@/hooks/usePushNotifications';

interface PushNotificationSettingsProps {
  /**
   * Function to get FCM token from the mobile app
   * This should be provided by the mobile app bridge
   */
  getFCMToken: () => Promise<string | null>;

  /**
   * Optional callback when notifications are enabled/disabled
   */
  onSettingsChange?: (enabled: boolean) => void;
}

interface NotificationPreference {
  key: string;
  label: string;
  description: string;
  enabled: boolean;
  category: 'assessments' | 'appointments' | 'alerts' | 'messages' | 'wellness';
}

interface DeviceInfo {
  id: string;
  token: string;
  platform: string;
  device_model?: string;
  is_active: boolean;
  last_used_at: string;
}

export const PushNotificationSettings: React.FC<PushNotificationSettingsProps> = ({
  getFCMToken,
  onSettingsChange,
}) => {
  const {
    status,
    isInitialized,
    isLoading,
    error,
    hasActiveTokens,
    tokenCount,
    requestPermission,
    register,
    sendTest,
    checkStatus,
  } = usePushNotifications({
    getFCMToken,
    autoInit: false,
  });

  const [preferences, setPreferences] = useState<NotificationPreference[]>([
    {
      key: 'assessment_reminders',
      label: 'Assessment Reminders',
      description: 'Get reminded about pending assessments',
      enabled: true,
      category: 'assessments',
    },
    {
      key: 'appointment_reminders',
      label: 'Appointment Reminders',
      description: 'Reminders before scheduled appointments',
      enabled: true,
      category: 'appointments',
    },
    {
      key: 'clinical_alerts',
      label: 'Clinical Alerts',
      description: 'Important updates from your care team',
      enabled: true,
      category: 'alerts',
    },
    {
      key: 'crisis_alerts',
      label: 'Crisis Alerts',
      description: 'Immediate notifications for crisis situations',
      enabled: true,
      category: 'alerts',
    },
    {
      key: 'messages',
      label: 'Messages',
      description: 'New messages from your care team',
      enabled: true,
      category: 'messages',
    },
    {
      key: 'daily_check_in',
      label: 'Daily Check-In',
      description: 'Gentle reminders to check in on your wellness',
      enabled: true,
      category: 'wellness',
    },
    {
      key: 'progress_updates',
      label: 'Progress Updates',
      description: 'Updates on your wellness journey',
      enabled: true,
      category: 'wellness',
    },
  ]);

  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const [showDevices, setShowDevices] = useState(false);

  // Load initial status
  useEffect(() => {
    checkStatus();
  }, []);

  // Handle permission request and registration
  const handleEnableNotifications = async () => {
    if (status === 'default') {
      const granted = await requestPermission();
      if (granted) {
        const success = await register();
        if (success) {
          Alert.alert('Success', 'Push notifications enabled!');
          onSettingsChange?.(true);
        } else {
          Alert.alert('Error', error || 'Failed to enable notifications');
        }
      } else {
        Alert.alert(
          'Permission Denied',
          'Please enable notifications in your device settings to receive updates.'
        );
      }
    } else if (status === 'denied') {
      Alert.alert(
        'Notifications Disabled',
        'Push notifications are currently disabled. To enable them:\n\n' +
          (Platform.OS === 'ios'
            ? '1. Open iOS Settings\n2. Tap Notifications\n3. Find PsychSync\n4. Enable notifications'
            : '1. Open Android Settings\n2. Tap Apps & notifications\n3. Find PsychSync\n4. Tap Notifications\n5. Enable notifications'),
        [{ text: 'OK', style: 'default' }]
      );
    }
  };

  // Handle disabling notifications
  const handleDisableNotifications = async () => {
    Alert.alert(
      'Disable Notifications',
      'Are you sure you want to disable push notifications? You will miss important updates.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Disable',
          style: 'destructive',
          onPress: () => {
            onSettingsChange?.(false);
            Alert.alert('Disabled', 'Push notifications have been disabled');
          },
        },
      ]
    );
  };

  // Handle preference toggle
  const handleTogglePreference = async (key: string) => {
    // Update local state immediately for responsiveness
    setPreferences((prev) =>
      prev.map((pref) =>
        pref.key === key ? { ...pref, enabled: !pref.enabled } : pref
      )
    );

    // TODO: Send preference update to backend
    // await updateNotificationPreferences({ [key]: !enabled });
  };

  // Handle test notification
  const handleSendTest = async () => {
    await sendTest();
    Alert.alert(
      'Test Notification Sent',
      'You should receive a test notification shortly. If you don\'t see it, check your device settings.',
      [{ text: 'OK' }]
    );
  };

  // Handle viewing devices
  const handleViewDevices = async () => {
    if (showDevices) {
      setShowDevices(false);
    } else {
      // TODO: Fetch devices from backend
      // const userTokens = await pushNotificationService.getMyTokens();
      // setDevices(userTokens);
      setShowDevices(true);
    }
  };

  // Group preferences by category
  const preferencesByCategory = preferences.reduce((acc, pref) => {
    if (!acc[pref.category]) {
      acc[pref.category] = [];
    }
    acc[pref.category].push(pref);
    return acc;
  }, {} as Record<string, NotificationPreference[]>);

  const categoryTitles: Record<string, string> = {
    assessments: 'Assessments',
    appointments: 'Appointments',
    alerts: 'Alerts & Notifications',
    messages: 'Messages',
    wellness: 'Wellness',
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
      {/* Header Section */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Push Notifications</Text>
        <Text style={styles.headerSubtitle}>
          {status === 'granted' && isInitialized
            ? 'Notifications are enabled'
            : 'Enable notifications to stay updated'}
        </Text>
      </View>

      {/* Enable/Disable Section */}
      <View style={styles.section}>
        <View style={styles.enableRow}>
          <View style={styles.enableTextContainer}>
            <Text style={styles.enableLabel}>Enable Push Notifications</Text>
            <Text style={styles.enableDescription}>
              {status === 'granted' && isInitialized
                ? 'Receive important updates on your device'
                : 'Stay informed with timely notifications'}
            </Text>
          </View>
          <Switch
            value={status === 'granted' && isInitialized}
            onValueChange={(value) => {
              if (value) {
                handleEnableNotifications();
              } else {
                handleDisableNotifications();
              }
            }}
            disabled={isLoading}
            trackColor={{ false: '#cbd5e1', true: '#6366F1' }}
            thumbColor="#ffffff"
          />
        </View>

        {/* Permission Status */}
        {status !== 'granted' && (
          <View style={styles.statusBanner}>
            <Text style={styles.statusBannerText}>
              {status === 'denied'
                ? '⚠️ Notifications are blocked in device settings'
                : '🔔 Enable notifications to receive updates'}
            </Text>
          </View>
        )}

        {/* Error Message */}
        {error && (
          <View style={styles.errorBanner}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
      </View>

      {/* Active Devices Section */}
      {hasActiveTokens && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Active Devices</Text>
          <View style={styles.deviceCard}>
            <Text style={styles.deviceCount}>
              {tokenCount} {tokenCount === 1 ? 'device' : 'devices'} registered
            </Text>
            <Text
              style={styles.viewDevicesLink}
              onPress={handleViewDevices}
            >
              {showDevices ? 'Hide' : 'View'}
            </Text>
          </View>

          {/* Device List */}
          {showDevices && (
            <View style={styles.deviceList}>
              {devices.map((device) => (
                <View key={device.id} style={styles.deviceItem}>
                  <View>
                    <Text style={styles.deviceName}>
                      {device.device_model || device.platform}
                    </Text>
                    <Text style={styles.deviceDetails}>
                      {device.platform} • Last used:{' '}
                      {new Date(device.last_used_at).toLocaleDateString()}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.deviceStatus,
                      { backgroundColor: device.is_active ? '#10B981' : '#cbd5e1' },
                    ]}
                  >
                    <Text style={styles.deviceStatusText}>
                      {device.is_active ? 'Active' : 'Inactive'}
                    </Text>
                  </View>
                </View>
              ))}
              {devices.length === 0 && (
                <Text style={styles.noDevicesText}>No devices found</Text>
              )}
            </View>
          )}
        </View>
      )}

      {/* Notification Preferences Section */}
      {isInitialized && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notification Preferences</Text>

          {Object.entries(preferencesByCategory).map(([category, prefs]) => (
            <View key={category} style={styles.category}>
              <Text style={styles.categoryTitle}>
                {categoryTitles[category]}
              </Text>
              {prefs.map((pref) => (
                <View key={pref.key} style={styles.preferenceItem}>
                  <View style={styles.preferenceTextContainer}>
                    <Text style={styles.preferenceLabel}>{pref.label}</Text>
                    <Text style={styles.preferenceDescription}>
                      {pref.description}
                    </Text>
                  </View>
                  <Switch
                    value={pref.enabled}
                    onValueChange={() => handleTogglePreference(pref.key)}
                    trackColor={{ false: '#cbd5e1', true: '#6366F1' }}
                    thumbColor="#ffffff"
                  />
                </View>
              ))}
            </View>
          ))}
        </View>
      )}

      {/* Test Notification Section */}
      {isInitialized && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Test Notifications</Text>
          <Text style={styles.testDescription}>
            Send a test notification to verify everything is working correctly.
          </Text>
          <View style={styles.testButton}>
            <Text
              style={styles.testButtonText}
              onPress={handleSendTest}
            >
              Send Test Notification
            </Text>
          </View>
        </View>
      )}

      {/* Info Section */}
      <View style={styles.infoSection}>
        <Text style={styles.infoTitle}>About Push Notifications</Text>
        <Text style={styles.infoText}>
          Push notifications allow us to send you important updates even when the
          app is not open. You can control which types of notifications you
          receive and disable them at any time.
        </Text>
        <Text style={styles.infoText}>
          Crisis alerts will always be delivered regardless of your preferences
          to ensure your safety.
        </Text>
      </View>
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
  statusBanner: {
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  statusBannerText: {
    fontSize: 14,
    color: '#92400E',
    lineHeight: 20,
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
  deviceCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
  },
  deviceCount: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  viewDevicesLink: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6366F1',
  },
  deviceList: {
    marginTop: 12,
  },
  deviceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
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
  deviceStatus: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  deviceStatusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  noDevicesText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    padding: 16,
  },
  category: {
    marginBottom: 16,
  },
  categoryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  preferenceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  preferenceTextContainer: {
    flex: 1,
    marginRight: 12,
  },
  preferenceLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: '#111827',
    marginBottom: 2,
  },
  preferenceDescription: {
    fontSize: 13,
    color: '#6b7280',
    lineHeight: 18,
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
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#1E40AF',
    lineHeight: 20,
    marginBottom: 8,
  },
});

export default PushNotificationSettings;
