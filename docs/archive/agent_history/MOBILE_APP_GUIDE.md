# 📱 PsychSync Mobile Apps - Quick Start Guide

## ✅ Mobile Apps Implementation Complete!

Native iOS and Android applications have been successfully created using **React Native + Expo**.

---

## 🚀 Quick Start

### 1. Navigate to Mobile App Directory

```bash
cd mobile-app
```

### 2. Start the Development Server

```bash
npm start
```

### 3. Run on Your Preferred Platform

When the Expo CLI starts, press one of these keys:

- **i** - Open iOS Simulator (macOS only)
- **a** - Open Android Emulator
- **w** - Open in Web Browser
- **shift + i** - Open iOS on physical device (via Expo Go app)

---

## 📦 What's Included

### ✅ Fully Implemented Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Dashboard Screen** | ✅ Complete | Real-time email monitoring with stats, categories, insights |
| **Connections Screen** | ✅ Complete | Manage email accounts, sync connections |
| **Settings Screen** | ✅ Complete | Notifications, appearance, data management |
| **API Service** | ✅ Complete | Backend communication for FastAPI |
| **Push Notifications** | ✅ Complete | Local alerts + push notification setup |
| **Pull-to-Refresh** | ✅ Complete | Swipe down to refresh data |
| **Auto-Refresh** | ✅ Complete | Data updates every 30 seconds |
| **Mobile UI** | ✅ Complete | Touch-optimized, responsive design |
| **TypeScript** | ✅ Complete | Type-safe codebase |

---

## 📂 Project Structure

```
mobile-app/
├── App.tsx                    # Root component with navigation
├── package.json               # Dependencies
├── README.md                  # Detailed documentation
│
├── src/
│   ├── screens/              # Screen components
│   │   ├── DashboardScreen.tsx      # Main monitoring dashboard
│   │   ├── ConnectionsScreen.tsx    # Email connections management
│   │   └── SettingsScreen.tsx       # App settings
│   │
│   ├── services/             # Business logic
│   │   ├── api.ts                   # Backend API client
│   │   └── notifications.ts          # Push notification service
│   │
│   ├── navigation/           # Navigation structure
│   │   └── AppNavigator.tsx         # Bottom tab navigation
│   │
│   └── types/               # TypeScript definitions
│       └── index.ts                 # Shared types
```

---

## 🔌 Backend Integration

The mobile app connects to your FastAPI backend:

```typescript
// API Base URL (configured in src/services/api.ts)
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

### For Physical Devices/Emulators:

If testing on a physical device or emulator, update to your local IP:

```typescript
// Find your IP (macOS):
// ipconfig getifaddr en0

const API_BASE_URL = 'http://YOUR_LOCAL_IP:8000/api/v1';
```

---

## 📱 Screens Overview

### 1. Dashboard Screen
**Path:** `src/screens/DashboardScreen.tsx`

**Features:**
- 📊 Stats grid (total emails, last hour, 24h, 7 days)
- 📂 Category breakdown with visual bars
- 🧠 Behavioral insights (security, financial, professional, social)
- 🚨 Recent alerts display
- 💡 Actionable recommendations
- 🔄 Pull-to-refresh
- ⚡ Auto-refresh every 30 seconds

**Preview:**
```
┌─────────────────────────────┐
│  Email Monitoring        🔔3│
│  Last updated: 2:30 PM      │
├─────────────────────────────┤
│  Total     Last 24h  Last 7d│
│  62,377    289       987    │
│  Last Hour: 12              │
├─────────────────────────────┤
│  Email Categories           │
│  ████████ Security 81       │
│  ██████ Financial 29        │
├─────────────────────────────┤
│  Behavioral Insights        │
│  🔒 Security: HIGH          │
│  💰 Financial: HIGH         │
│  💼 Professional: MED       │
└─────────────────────────────┘
```

### 2. Connections Screen
**Path:** `src/screens/ConnectionsScreen.tsx`

**Features:**
- 📧 List all connected email accounts
- 🔄 Sync individual connections
- 🟢 Status badges (Active, Error, Inactive)
- 📅 Connection details and last sync time

### 3. Settings Screen
**Path:** `src/screens/SettingsScreen.tsx`

**Features:**
- 🔔 Push notification toggle
- 🔄 Auto-refresh control
- 🌙 Dark mode toggle (ready)
- 💾 Cache management
- 📲 Sync all accounts
- ℹ️ App version info
- 🚪 Sign out

---

## 🔔 Push Notifications

### Setup Complete

The app includes:
- ✅ Local notification system
- ✅ Permission request handling
- ✅ Notification scheduling
- ✅ Critical alert detection
- ✅ Expo Notifications integration

### How It Works:

1. **On App Launch:** Requests notification permissions
2. **Critical Alerts:** Automatically shows notification when critical alerts detected
3. **Settings Toggle:** Users can enable/disable in Settings
4. **Badge Count:** Shows unread alert count on dashboard

### Production Push Notifications:

To enable actual push notifications (remote):

1. **Create Expo account:** https://expo.dev
2. **Run:** `eas login`
3. **Configure push credentials** in `app.json`
4. **Build standalone app** with `eas build`

---

## 🛠️ Development Commands

```bash
# Start development server
npm start

# Run on iOS Simulator
npm run ios

# Run on Android Emulator
npm run android

# Run in web browser
npm run web

# Start with tunnel (for physical devices)
npm start -- --tunnel

# Clear cache and restart
npm start -- --clear

# Install dependencies
npm install

# Check for updates
npm update
```

---

## 📱 Installing on Physical Devices

### iOS

1. **Install Expo Go** from App Store
2. **Start app:** `npm start -- --tunnel`
3. **Scan QR code** with Expo Go camera
4. **App launches** automatically

### Android

1. **Install Expo Go** from Play Store
2. **Start app:** `npm start -- --tunnel`
3. **Scan QR code** with Expo Go
4. **App launches** automatically

---

## 🎨 UI/UX Features

### Mobile-First Design
- **Touch Targets:** Minimum 44x44 pixels
- **Responsive:** Works on all screen sizes
- **Safe Areas:** Adapts to notches and home indicators
- **Dark Mode:** Ready (toggle in Settings)

### Accessibility
- **High Contrast:** WCAG AA compliant
- **Text Scaling:** Respects system font size
- **Color Blindness:** Icons + colors for indicators

### Performance
- **Lazy Loading:** Screens load on demand
- **Auto-Refresh:** Intelligent 30-second intervals
- **Pull-to-Refresh:** On-demand updates
- **Optimized Re-renders:** React.memo and useCallback

---

## 🔧 Configuration

### API Configuration

Edit `src/services/api.ts`:

```typescript
const API_BASE_URL = 'http://YOUR_IP:8000/api/v1';
```

### Notification Configuration

Edit `src/services/notifications.ts`:

```typescript
// Add notification channels (Android)
await Notifications.setNotificationChannelAsync('email-alerts', {
  name: 'Email Alerts',
  importance: Notifications.AndroidImportance.HIGH,
});
```

---

## 🐛 Troubleshooting

### "Metro bundler issues"
```bash
npm start -- --clear
```

### "Cannot connect to backend"
1. Check backend is running: `curl http://localhost:8000/api/v1/health`
2. Update API_BASE_URL to use your local IP (not localhost)
3. Ensure backend CORS allows mobile requests

### "Push notifications not working"
1. Check notification permissions in Settings
2. For physical devices, must use Expo Go or standalone build
3. Web version has limited notification support

### "Navigation not working"
```bash
npm install @react-navigation/native @react-navigation/bottom-tabs
npm install react-native-safe-area-context react-native-screens
```

---

## 📦 Building for Production

### Using EAS Build (Recommended)

```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Configure project
eas build:configure

# Build for iOS
eas build --platform ios

# Build for Android
eas build --platform android

# Build locally
eas build --platform android --local
```

### Standalone Apps

EAS Build generates:
- **iOS:** .ipa file for TestFlight/App Store
- **Android:** .apk (direct install) or .aab (Play Store)

---

## 🎯 Next Steps

### Phase 2: Enhanced Features (Ready to Implement)

1. **Authentication Flow**
   - Login/signup screens
   - JWT token management
   - Secure token storage (Expo SecureStore)

2. **Real-Time Alerts**
   - WebSocket connection for live updates
   - Background sync

3. **Charts and Graphs**
   - Victory Native or react-native-chart-kit
   - Timeline charts
   - Category pie charts

4. **Offline Mode**
   - AsyncStorage for caching
   - Sync when connection restored

---

## 📚 Resources

- **Expo Documentation:** https://docs.expo.dev
- **React Navigation:** https://reactnavigation.org
- **React Native:** https://reactnative.dev

---

## ✨ Summary

**Status:** ✅ **COMPLETE & FUNCTIONAL**

The mobile app provides:
- ✅ Full email monitoring dashboard
- ✅ Connection management
- ✅ Push notifications (local + setup for remote)
- ✅ Mobile-optimized UI
- ✅ TypeScript for type safety
- ✅ Ready for iOS and Android deployment

**Ready to run:** `cd mobile-app && npm start`

---

*Generated: 2026-01-22*
*PsychSync Email Monitoring System v1.0*
*Status: ✅ Mobile Apps Operational*
