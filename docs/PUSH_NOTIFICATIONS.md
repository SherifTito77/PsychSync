# Push Notifications System

Complete Firebase Cloud Messaging (FCM) integration for mobile apps (iOS and Android).

## 🎯 Overview

The push notification system enables PsychSync to send timely updates to users' mobile devices, including:
- **Assessment reminders** - Gently remind users to complete pending assessments
- **Appointment notifications** - Remind users about upcoming appointments
- **Clinical alerts** - Notify clinicians about high-risk patients or crisis situations
- **Message notifications** - Alert users to new messages from their care team
- **Wellness check-ins** - Daily reminders to check in on mental wellness

## 🏗️ Architecture

```
┌─────────────────┐      FCM Token      ┌──────────────────┐
│  Mobile App     │ ───────────────────> │  Backend API     │
│  (iOS/Android)  │ <─────────────────── │  (FastAPI)       │
└─────────────────┘   Push Notification  └──────────────────┘
        │                                      │
        │                                      │
        v                                      v
┌─────────────────┐                    ┌──────────────────┐
│   Firebase FCM  │                    │   PostgreSQL     │
│   (APNS + FCM)  │                    │   Token Storage  │
└─────────────────┘                    └──────────────────┘
```

### Components

1. **Backend Service** (`app/services/push_notification_service.py`)
   - Manages FCM token registration and lifecycle
   - Sends notifications to Firebase
   - Handles user preferences
   - Supports iOS and Android platforms

2. **API Endpoints** (`app/api/v1/endpoints/push_notifications.py`)
   - REST API for token management
   - Test notification endpoints
   - Status and preferences endpoints

3. **Frontend Service** (`frontend/src/services/pushNotifications.ts`)
   - API client for push notification operations
   - Platform detection
   - Device info collection

4. **React Hook** (`frontend/src/hooks/usePushNotifications.ts`)
   - State management for notifications
   - Permission handling
   - Easy integration into components

5. **Mobile UI Components**
   - `PushNotificationSettings.tsx` - Settings/preferences UI
   - `PushNotificationExample.tsx` - Integration example

## 🚀 Quick Start

### 1. Backend Setup

#### Environment Variables

Add to your `.env` file:

```bash
# Firebase Cloud Messaging
FCM_SERVER_KEY=your_fcm_server_key_here
FCM_API_URL=https://fcm.googleapis.com/fcm/send
```

**Getting your FCM Server Key:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create/select your project
3. Go to Project Settings → Cloud Messaging
4. Copy the Server Key

#### Database Migration

The push notification system uses the following tables (already created):

```sql
-- Push notification tokens
CREATE TABLE push_notification_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    token TEXT NOT NULL,
    platform VARCHAR(10) NOT NULL,
    device_info JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW(),
    deactivated_at TIMESTAMP
);

-- Notification preferences
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    assessment_reminders BOOLEAN DEFAULT TRUE,
    appointment_reminders BOOLEAN DEFAULT TRUE,
    message_notifications BOOLEAN DEFAULT TRUE,
    general_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Mobile App Setup

#### Install Dependencies

```bash
# For React Native
npm install @react-native-firebase/app @react-native-firebase/messaging

# For iOS
cd ios && pod install
```

#### Configure Firebase

**Android:**
1. Download `google-services.json` from Firebase Console
2. Place it in `android/app/`
3. Add to `android/app/build.gradle`:
```gradle
apply plugin: 'com.google.gms.google-services'
```

**iOS:**
1. Download `GoogleService-Info.plist` from Firebase Console
2. Add it to your Xcode project
3. Enable Push Notifications and Background Modes in capabilities
4. Add APNs key to Firebase Console

### 3. Initialize in Your App

```typescript
// App.tsx
import messaging from '@react-native-firebase/messaging';
import { PushNotificationSettings } from '@/components/mobile/PushNotificationSettings';

function App() {
  // Initialize Firebase and register for notifications
  useEffect(() => {
    async function initializeFirebase() {
      // Register device for remote messages
      await messaging().registerDeviceForRemoteMessages();

      // Get FCM token
      const token = await messaging().getToken();
      console.log('FCM Token:', token);

      // Foreground notification handler
      const unsubscribe = messaging().onMessage(async remoteMessage => {
        Alert.alert('New notification', remoteMessage.notification?.body);
      });

      return unsubscribe;
    }

    initializeFirebase();
  }, []);

  // FCM token provider
  const getFCMToken = async () => {
    return await messaging().getToken();
  };

  return (
    <PushNotificationSettings
      getFCMToken={getFCMToken}
      onSettingsChange={(enabled) => console.log('Notifications:', enabled)}
    />
  );
}
```

### 4. Background/Quit State Handling

```typescript
// Register background message handler
messaging().setBackgroundMessageHandler(async remoteMessage => {
  console.log('Background notification:', remoteMessage);
});

// Handle notification tap when app is in quit state
messaging().getInitialNotification().then(remoteMessage => {
  if (remoteMessage) {
    console.log('App opened from quit state:', remoteMessage);
    // Navigate to appropriate screen
  }
});
```

## 📋 API Reference

### POST /api/v1/push-notifications/register-token

Register an FCM device token.

**Request:**
```json
{
  "token": "FCM device token string (min 100 chars)",
  "platform": "ios",
  "device_id": "unique-device-id",
  "device_model": "iPhone 14",
  "os_version": "iOS 16.0",
  "app_version": "1.0.0"
}
```

**Response:**
```json
{
  "id": "uuid",
  "token": "first_20_chars...",
  "platform": "ios",
  "is_active": true,
  "created_at": "2024-01-17T10:00:00Z",
  "last_used_at": "2024-01-17T10:00:00Z"
}
```

### GET /api/v1/push-notifications/my-tokens

Get all active tokens for current user.

**Response:**
```json
[
  {
    "id": "uuid",
    "token": "first_20_chars...",
    "platform": "ios",
    "is_active": true,
    "created_at": "2024-01-17T10:00:00Z",
    "last_used_at": "2024-01-17T10:00:00Z"
  }
]
```

### POST /api/v1/push-notifications/unregister-token

Unregister a device token.

**Request:**
```json
{
  "token": "FCM device token string"
}
```

### POST /api/v1/push-notifications/send

Send notification to a specific user (clinician/admin only).

**Request:**
```json
{
  "user_id": "target-user-uuid",
  "notification_type": "appointment_reminder",
  "data": {
    "clinician_name": "Dr. Smith",
    "minutes_until": 15,
    "click_action": "OPEN_APPOINTMENT"
  }
}
```

### POST /api/v1/push-notifications/send-bulk

Send notification to multiple users (admin only).

**Request:**
```json
{
  "user_ids": ["uuid1", "uuid2", "uuid3"],
  "notification_type": "system_announcement",
  "data": {
    "title": "Scheduled Maintenance",
    "message": "System will be down for maintenance..."
  }
}
```

### GET /api/v1/push-notifications/test-send

Send a test notification to current user.

### GET /api/v1/push-notifications/types

List all available notification types and templates.

### GET /api/v1/push-notifications/status

Get notification status for current user.

**Response:**
```json
{
  "user_id": "uuid",
  "active_devices": 2,
  "ios_devices": 1,
  "android_devices": 1,
  "last_used": "2024-01-17T10:00:00Z",
  "push_enabled": true
}
```

## 🔔 Notification Types

### Assessment Notifications
- `assessment_reminder` - Reminder to complete pending assessment
- `assessment_due` - Assessment due soon
- `assessment_overdue` - Assessment is overdue

### Appointment Notifications
- `appointment_scheduled` - New appointment scheduled
- `appointment_reminder` - Reminder before appointment
- `appointment_canceled` - Appointment canceled
- `appointment_rescheduled` - Appointment rescheduled

### Clinical Alerts (for clinicians)
- `clinical_alert` - General clinical alert
- `crisis_alert` - 🚨 Crisis situation (high priority)
- `high_risk_alert` - Patient flagged as high risk

### Messages
- `new_message` - New message from another user
- `clinician_message` - Message from clinician
- `system_announcement` - System-wide announcement

### Wellness
- `daily_check_in` - Daily wellness check-in reminder
- `wellness_reminder` - General wellness reminder
- `progress_update` - Progress milestone update

### Account
- `account_update` - Account changes
- `privacy_update` - Privacy policy updates
- `security_alert` - Security-related alerts

## 🎨 Notification Templates

Each notification type has a template with customizable content:

```python
NotificationType.CRISIS_ALERT: {
    "title": "🚨 CRISIS ALERT",
    "body": "{patient_name} has triggered crisis indicators. Immediate action required.",
    "icon": "alert-octagon",
    "color": "#EF4444",
    "priority": "high"
}
```

Templates support **variable substitution** using `{variable_name}` syntax.

### Customizing Templates

Edit `app/services/push_notification_service.py`:

```python
NOTIFICATION_TEMPLATES = {
    NotificationType.ASSESSMENT_REMINDER: {
        "title": "Assessment Reminder",
        "body": "You have a pending {assessment_name} to complete.",
        "icon": "assessment",
        "color": "#6366F1",
        "priority": "normal"
    },
}
```

## 👤 User Preferences

Users can control which notifications they receive:

- **Assessment reminders** - Toggle assessment-related notifications
- **Appointment reminders** - Toggle appointment notifications
- **Clinical alerts** - Toggle general clinical alerts
- **Crisis alerts** - Always enabled (cannot be disabled for safety)
- **Messages** - Toggle message notifications
- **Wellness** - Toggle wellness check-ins

Preferences are stored in the `notification_preferences` table and checked before sending notifications.

## 🔧 Frontend Usage

### Using the React Hook

```typescript
import { usePushNotifications } from '@/hooks/usePushNotifications';

function MyComponent() {
  const {
    status,           // 'default' | 'granted' | 'denied'
    isInitialized,
    isLoading,
    error,
    hasActiveTokens,
    tokenCount,
    requestPermission,
    register,
    sendTest,
    checkStatus
  } = usePushNotifications({
    getFCMToken: async () => {
      const token = await messaging().getToken();
      return token;
    },
    autoInit: false  // Don't auto-initialize on mount
  });

  return (
    <View>
      <Text>Status: {status}</Text>
      <Button onPress={register} title="Enable Notifications" />
      <Button onPress={sendTest} title="Send Test" />
    </View>
  );
}
```

### Using the Settings Component

```typescript
import PushNotificationSettings from '@/components/mobile/PushNotificationSettings';

function SettingsScreen() {
  return (
    <PushNotificationSettings
      getFCMToken={async () => {
        return await messaging().getToken();
      }}
      onSettingsChange={(enabled) => {
        console.log('Notifications', enabled ? 'enabled' : 'disabled');
      }}
    />
  );
}
```

## 🧪 Testing

### 1. Unit Testing

```python
import pytest
from app.services.push_notification_service import push_notification_service

@pytest.mark.asyncio
async def test_register_device_token(db_session, test_user):
    token = await push_notification_service.register_device_token(
        db=db_session,
        user_id=test_user.id,
        token="test_fcm_token_12345",
        device_info={"platform": "ios", "device_model": "iPhone 14"}
    )

    assert token is not None
    assert token.platform == "ios"
    assert token.is_active == True
```

### 2. Integration Testing

```bash
# Send test notification via API
curl -X GET "http://localhost:8000/api/v1/push-notifications/test-send" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Manual Testing

1. Enable notifications in the app settings
2. Click "Send Test Notification" button
3. Verify notification appears on device
4. Test with app in foreground, background, and quit states
5. Verify notification tap opens the app

## 🔒 Security Considerations

### Token Security
- FCM tokens are treated as sensitive data
- Tokens are truncated in API responses (first 20 chars only)
- Never log full tokens in production
- Tokens are transmitted over HTTPS

### Authorization
- Only authenticated users can register tokens
- Only clinicians and admins can send notifications to others
- Only admins can send bulk notifications
- Users can only view and manage their own tokens

### Rate Limiting
Consider implementing rate limiting for:
- Token registration (prevent spam)
- Bulk notification sends (prevent abuse)

## 📊 Analytics & Monitoring

The system logs all notification delivery attempts:

```
Notification delivery report:
user=123e4567-e89b-12d3-a456-426614174000,
type=appointment_reminder,
sent=2,
successful=2,
failed=0
```

Consider tracking:
- Delivery success rate
- Platform breakdown (iOS vs Android)
- User engagement (notification open rate)
- Failed token cleanup

## 🐛 Troubleshooting

### Notifications Not Arriving

1. **Check permission status:**
   ```typescript
   const status = await Notifications.getPermissionsAsync();
   console.log('Permission:', status);
   ```

2. **Verify token registration:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/push-notifications/my-tokens" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **Test FCM directly:**
   - Use Firebase Console → Cloud Messaging → Send test message

4. **Check FCM server key:**
   - Verify `FCM_SERVER_KEY` in backend `.env`
   - Ensure key is valid and not expired

### iOS-Specific Issues

1. **APNs Certificate:**
   - Verify APNs key is uploaded to Firebase Console
   - Check certificate expiration
   - Ensure Key ID and Team ID are correct

2. **Provisioning Profile:**
   - Push Notifications capability must be enabled
   - App ID must match bundle identifier

3. **Test vs Production:**
   - Use separate APNs keys for development and production
   - Development tokens don't work in production

### Android-Specific Issues

1. **FCM Configuration:**
   - Verify `google-services.json` is correct
   - Check package name matches Firebase project

2. **Battery Optimization:**
   - Some devices kill background services
   - Guide users to exempt app from battery optimization

## 📚 Additional Resources

- [Firebase Cloud Messaging Documentation](https://firebase.google.com/docs/cloud-messaging)
- [React Native Firebase](https://rnfirebase.io/)
- [Apple Push Notification Service](https://developer.apple.com/documentation/usernotifications)
- [Android Notification Guide](https://developer.android.com/guide/topics/ui/notifiers/notifications)

## 🎯 Best Practices

1. **Always respect user preferences** - Don't send if user disabled
2. **Use appropriate priority** - High priority for urgent alerts only
3. **Localize content** - Send notifications in user's preferred language
4. **Handle token refresh** - FCM tokens can change, update backend
5. **Clean up old tokens** - Remove inactive tokens periodically
6. **Test thoroughly** - Test on both iOS and Android devices
7. **Monitor delivery rates** - Track success/failure rates
8. **Respect time zones** - Consider user's local time when scheduling

## 🔄 Next Steps

1. ✅ Backend service and API endpoints
2. ✅ Frontend service and React hook
3. ✅ Mobile UI components
4. ⏳ **TODO:** Implement notification preferences API endpoint
5. ⏳ **TODO:** Add notification scheduling (cron-based)
6. ⏳ **TODO:** Build notification history/logs view
7. ⏳ **TODO:** Add rich notification support (images, actions)
8. ⏳ **TODO:** Implement notification categories/channels (Android)
9. ⏳ **TODO:** A/B test notification content
10. ⏳ **TODO:** Add analytics dashboard for notification metrics

---

**Status:** ✅ Core implementation complete

**Last Updated:** January 17, 2026

**Maintainer:** PsychSync Engineering Team
