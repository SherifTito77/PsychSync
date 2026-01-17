/**
 * Push Notification Integration Example
 *
 * This demonstrates how to integrate push notifications into your mobile app.
 * It shows the complete flow from getting the FCM token to displaying settings.
 *
 * Before using this example, make sure you have:
 * 1. Installed Firebase in your mobile app (@react-native-firebase/app, @react-native-firebase/messaging)
 * 2. Configured Firebase with your FCM server key in backend .env
 * 3. Set up the mobile app bridge to communicate with React Native
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import PushNotificationSettings from './PushNotificationSettings';

/**
 * Example implementation of getting FCM token from React Native Firebase
 *
 * In your actual mobile app, this would be implemented in native code
 * and exposed to React Native via a bridge or module.
 */
async function getFCMTokenFromMobile(): Promise<string | null> {
  try {
    // Example using @react-native-firebase/messaging:
    //
    // import messaging from '@react-native-firebase/messaging';
    //
    // // Request permission
    // const authStatus = await messaging().requestPermission();
    // const enabled =
    //   authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    //   authStatus === messaging.AuthorizationStatus.PROVISIONAL;
    //
    // if (!enabled) {
    //   console.log('Failed to get push notification permission');
    //   return null;
    // }
    //
    // // Get the token
    // const token = await messaging().getToken();
    // console.log('FCM Token:', token);
    // return token;

    // For web testing, return a mock token
    if (typeof window !== 'undefined' && 'Notification' in window) {
      // In a real app, this would come from Firebase
      return 'mock_fcm_token_for_testing_' + Math.random().toString(36).substring(7);
    }

    return null;
  } catch (error) {
    console.error('Error getting FCM token:', error);
    return null;
  }
}

/**
 * Complete example component showing push notification integration
 */
export const PushNotificationExample: React.FC = () => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [setupComplete, setSetupComplete] = React.useState(false);

  React.useEffect(() => {
    // Simulate initialization
    const timer = setTimeout(() => {
      setIsLoading(false);
      setSetupComplete(true);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const handleSettingsChange = (enabled: boolean) => {
    console.log('Notifications', enabled ? 'enabled' : 'disabled');
    // You could update UI, send analytics, etc.
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366F1" />
        <Text style={styles.loadingText}>Setting up notifications...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Notification Settings</Text>
        <Text style={styles.headerSubtitle}>
          Manage how you receive updates from PsychSync
        </Text>
      </View>

      {/* Main Settings Component */}
      <PushNotificationSettings
        getFCMToken={getFCMTokenFromMobile}
        onSettingsChange={handleSettingsChange}
      />

      {/* Integration Guide */}
      <View style={styles.guideSection}>
        <Text style={styles.guideTitle}>📱 Integration Guide</Text>

        <View style={styles.guideStep}>
          <Text style={styles.guideStepTitle}>1. Install Dependencies</Text>
          <Text style={styles.guideCode}>
            npm install @react-native-firebase/app @react-native-firebase/messaging
          </Text>
        </View>

        <View style={styles.guideStep}>
          <Text style={styles.guideStepTitle}>2. Configure Firebase</Text>
          <Text style={styles.guideText}>
            - Add google-services.json (Android) or GoogleService-Info.plist (iOS)
          </Text>
          <Text style={styles.guideText}>
            - Set FCM_SERVER_KEY in backend .env file
          </Text>
        </View>

        <View style={styles.guideStep}>
          <Text style={styles.guideStepTitle}>3. Initialize in App.tsx</Text>
          <Text style={styles.guideCode}>
            {`// Initialize Firebase
import messaging from '@react-native-firebase/messaging';

// Register for remote notifications
messaging().registerDeviceForRemoteMessages();
const token = await messaging().getToken();

// Listen for notifications
messaging().onMessage(async remoteMessage => {
  Alert.alert('New notification', remoteMessage.notification.body);
});

// Background notification handler
messaging().setBackgroundMessageHandler(async remoteMessage => {
  console.log('Background notification:', remoteMessage);
});`}
          </Text>
        </View>

        <View style={styles.guideStep}>
          <Text style={styles.guideStepTitle}>4. Use in Components</Text>
          <Text style={styles.guideCode}>
            {`import { usePushNotifications } from '@/hooks/usePushNotifications';

function MyComponent() {
  const { status, register, sendTest } = usePushNotifications({
    getFCMToken: () => messaging().getToken(),
    autoInit: false
  });

  return (
    <Button onPress={register} title="Enable Notifications" />
  );
}`}
          </Text>
        </View>
      </View>

      {/* Testing Instructions */}
      <View style={styles.testingSection}>
        <Text style={styles.testingTitle}>🧪 Testing Your Setup</Text>
        <Text style={styles.testingText}>
          1. Enable notifications using the toggle above
        </Text>
        <Text style={styles.testingText}>
          2. Click "Send Test Notification" button
        </Text>
        <Text style={styles.testingText}>
          3. Check that notification appears on your device
        </Text>
        <Text style={styles.testingText}>
          4. Try toggling different notification types
        </Text>
        <Text style={styles.testingText}>
          5. Verify tokens are registered in backend API
        </Text>
      </View>

      {/* API Reference */}
      <View style={styles.apiSection}>
        <Text style={styles.apiTitle}>🔌 API Reference</Text>

        <Text style={styles.apiEndpoint}>POST /api/v1/push-notifications/register-token</Text>
        <Text style={styles.apiDescription}>
          Register a device token for push notifications
        </Text>

        <Text style={styles.apiEndpoint}>GET /api/v1/push-notifications/my-tokens</Text>
        <Text style={styles.apiDescription}>
          Get all active tokens for current user
        </Text>

        <Text style={styles.apiEndpoint}>GET /api/v1/push-notifications/test-send</Text>
        <Text style={styles.apiDescription}>
          Send a test notification to current user
        </Text>

        <Text style={styles.apiEndpoint}>POST /api/v1/push-notifications/send</Text>
        <Text style={styles.apiDescription}>
          Send notification to specific user (clinician/admin only)
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
    padding: 20,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6b7280',
  },
  header: {
    backgroundColor: '#6366F1',
    padding: 20,
    paddingTop: 60,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#E0E7FF',
  },
  guideSection: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    margin: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  guideTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 16,
  },
  guideStep: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  guideStepTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  guideCode: {
    backgroundColor: '#1f2937',
    color: '#f9fafb',
    padding: 12,
    borderRadius: 8,
    fontFamily: 'monospace',
    fontSize: 12,
    lineHeight: 18,
  },
  guideText: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 20,
    marginBottom: 4,
  },
  testingSection: {
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    padding: 16,
    margin: 16,
    marginBottom: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#6366F1',
  },
  testingTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1E40AF',
    marginBottom: 12,
  },
  testingText: {
    fontSize: 14,
    color: '#1E40AF',
    lineHeight: 20,
    marginBottom: 6,
  },
  apiSection: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    margin: 16,
    marginTop: 8,
    marginBottom: 32,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  apiTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 16,
  },
  apiEndpoint: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6366F1',
    fontFamily: 'monospace',
    marginTop: 12,
    marginBottom: 4,
  },
  apiDescription: {
    fontSize: 14,
    color: '#6b7280',
    lineHeight: 18,
  },
});

export default PushNotificationExample;
