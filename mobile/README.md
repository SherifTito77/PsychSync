# PsychSync Mobile App

Native iOS and Android application for email monitoring on the go.

## 🚀 Features

- ✅ Real-time email monitoring dashboard
- ✅ Multi-account support (Gmail, IMAP, Outlook)
- ✅ Push notifications for critical alerts
- ✅ Email category breakdown
- ✅ Behavioral insights
- ✅ Connection management
- ✅ Auto-refresh every 30 seconds
- ✅ Pull-to-refresh
- ✅ Mobile-optimized UI

## 📱 Prerequisites

1. **Node.js** v18+ (current: v18.20.8)
2. **Expo CLI** - Installed automatically
3. **iOS Simulator** (for iOS development)
   - Xcode Command Line Tools: `xcode-select --install`
4. **Android Studio** (for Android development)
   - Android SDK installed
   - Android emulator configured

## 🔧 Installation

```bash
cd mobile-app

# Install dependencies
npm install

# Start development server
npm start
```

## 🏃 Running the App

### Development Mode

```bash
# Start Expo development server
npm start

# Or with specific platform
npm run ios     # iOS Simulator
npm run android # Android Emulator
npm run web     # Web browser
```

### Press keys in the terminal:
- **i** - Open iOS Simulator
- **a** - Open Android Emulator
- **w** - Open in Web Browser
- **r** - Reload app
- **shift + r** - Clear cache and reload

## 📂 Project Structure

```
mobile-app/
├── src/
│   ├── screens/           # Screen components
│   │   ├── DashboardScreen.tsx        # Main monitoring dashboard
│   │   └── ConnectionsScreen.tsx      # Email connections management
│   ├── services/          # API and business logic
│   │   ├── api.ts                  # Backend API client
│   │   └── notifications.ts         # Push notification service
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts                # Shared types
│   ├── navigation/       # Navigation structure
│   │   └── AppNavigator.tsx         # Bottom tab navigation
│   ├── components/       # Reusable UI components
│   └── utils/            # Helper functions
├── assets/               # Images, fonts, etc.
├── App.tsx              # Root component
└── package.json         # Dependencies
```

## 🔌 API Configuration

The mobile app connects to your local FastAPI backend:

```typescript
// src/services/api.ts
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

### For Production/Physical Devices:

1. **Find your local IP address:**
   ```bash
   # macOS
   ipconfig getifaddr en0

   # Linux
   hostname -I
   ```

2. **Update API_BASE_URL** in `src/services/api.ts`:
   ```typescript
   const API_BASE_URL = 'http://YOUR_LOCAL_IP:8000/api/v1';
   ```

3. **Ensure your backend allows network requests:**
   ```python
   # In app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

## 🔑 Authentication

Currently, the app expects an auth token. In production:

```typescript
import SecureStore from 'expo-secure-store';

// Store token
await SecureStore.setItemAsync('auth_token', token);

// Retrieve token
const token = await SecureStore.getItemAsync('auth_token');
```

## 🔔 Push Notifications

Push notifications are handled by Expo Notifications service:

### Setup (Production):

1. **Create Expo account:** https://expo.dev
2. **Configure push credentials** in `app.json`:
   ```json
   {
     "expo": {
       "plugins": [
         [
           "expo-notifications",
           {
             "icon": "./assets/notification-icon.png",
             "color": "#ffffff",
             "sounds": ["./assets/notification.wav"]
           }
         ]
       ]
     }
   }
   ```

3. **Generate standalone app** with EAS Build

### Current Implementation:
- ✅ Local notifications working
- ✅ Permission requests
- ✅ Notification scheduling
- ⏳ Push token registration (TODO)

## 📊 Screens

### Dashboard Screen
- **Stats Grid**: Total emails, last hour, 24h, 7 days
- **Categories**: Visual breakdown with progress bars
- **Behavioral Insights**: Security, financial, professional, social levels
- **Alerts**: Recent critical alerts
- **Recommendations**: Actionable insights

### Connections Screen
- **List** all connected email accounts
- **Sync** individual connections
- **Status badges** (Active, Error, Inactive)
- **Connection details** (date, last sync)

## 🎨 UI Components

Uses React Native built-in components:
- `View`, `Text`, `ScrollView`, `TouchableOpacity`
- `SafeAreaView` for notched devices
- `RefreshControl` for pull-to-refresh
- Custom styling with `StyleSheet`

## 🔧 Development Tips

### Hot Reloading
- Changes reflect instantly without restart
- Press `r` in terminal if not working

### Debugging
```bash
# Start with debug menu
npm start -- --tunnel

# Access debug menu by shaking device/emulator
# Cmd+D (iOS) or Cmd+M (Android)
```

### Clear Cache
```bash
# Clear Metro bundler cache
npm start -- --clear

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📱 Building for Production

### iOS
```bash
# Requires Apple Developer account
eas build --platform ios
```

### Android
```bash
# Generate APK
eas build --platform android

# Or run locally
eas build --platform android --local
```

### Web
```bash
# Build web version
npm run web
```

## 🚀 Deployment

### Using Expo (Recommended)
1. Create account at https://expo.dev
2. Login: `eas login`
3. Configure project: `eas build:configure`
4. Build: `eas build --platform all`

### Standalone Apps
EAS Build generates:
- **iOS**: .ipa file (TestFlight/App Store)
- **Android**: .apk or .aab (Play Store)

## 📚 Key Dependencies

```json
{
  "expo": "~54.0.32",
  "expo-notifications": "~0.29.14",
  "@react-navigation/native": "^7.0.14",
  "@react-navigation/bottom-tabs": "^7.2.1",
  "react-native-safe-area-context": "4.14.0",
  "react-native-screens": "~4.5.0"
}
```

## 🔗 Integration with Backend

The mobile app communicates with FastAPI backend via REST:

```typescript
// GET /api/v1/email-monitoring/stats
apiService.getMonitoringStats()

// GET /api/v1/email-connector/connections
apiService.getEmailConnections()

// POST /api/v1/email-connector/sync
apiService.syncEmailConnection(connectionId)
```

## 🎯 Roadmap

### Phase 1: Core (Current)
- ✅ Dashboard with stats
- ✅ Connection management
- ✅ Local notifications
- ✅ Pull-to-refresh

### Phase 2: Enhanced
- ⏳ Authentication flow
- ⏳ Real-time alerts via WebSocket
- ⏳ Charts and graphs
- ⏳ Settings screen
- ⏳ Dark mode

### Phase 3: Advanced
- ⏳ Email actions (reply, forward)
- ⏳ Sentiment analysis
- ⏳ Team dashboards
- ⏳ Offline mode

## 🐛 Troubleshooting

### "Unable to resolve module"
```bash
npm install
```

### Metro bundler issues
```bash
npm start -- --clear
```

### iOS build errors
```bash
cd ios && pod install && cd ..
```

### Network requests failing
- Check backend is running: `curl http://localhost:8000/api/v1/health`
- Verify API_BASE_URL in `src/services/api.ts`
- For physical devices, use local IP instead of localhost

## 📞 Support

For issues or questions:
1. Check backend logs: `/tmp/backend.log`
2. Check mobile console (Cmd+D → Debug)
3. Review Expo docs: https://docs.expo.dev

---

*Generated: 2026-01-22*
*PsychSync Email Monitoring System v1.0*
