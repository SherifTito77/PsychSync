# PsychSync Mobile App

React Native mobile application for the PsychSync mental health platform.

## Features

### Clinical Assessments
- **LSAS** (Social Anxiety) - 24-item dual-rating assessment
- **EAT-26** (Eating Disorders) - Behavioral risk assessment
- **Y-BOCS** (OCD) - Obsession and compulsion severity
- **PHQ-9** (Depression) - Standard depression screening
- **GAD-7** (Anxiety) - Generalized anxiety disorder assessment

### Telehealth Video Consultations
- Schedule video sessions with clinicians
- HIPAA-compliant video calls via Twilio
- Real-time video with adaptive quality
- Calendar integration with reminders

### AI Chatbot Support
- Immediate mental health support
- Crisis detection and escalation
- Context-aware conversations
- Available 24/7

### Offline Capability
- Complete assessments without internet
- Automatic sync when connection restored
- Local caching of assessment history

## Tech Stack

- **Framework**: React Native 0.73
- **Language**: TypeScript
- **Navigation**: React Navigation 6
- **State Management**: React Context + Hooks
- **UI Components**: React Native Paper
- **Video**: Twilio Video React Native
- **Push Notifications**: Firebase Cloud Messaging
- **Charts**: Victory Native
- **Networking**: Axios with interceptors

## Project Structure

```
mobile/psychsync_native/
├── src/
│   ├── components/       # Reusable UI components
│   ├── screens/          # Screen components
│   │   ├── auth/        # Authentication screens
│   │   ├── assessments/ # Assessment screens
│   │   └── telehealth/  # Video consultation screens
│   ├── services/         # API services
│   ├── contexts/         # React Context providers
│   ├── hooks/           # Custom React hooks
│   ├── utils/           # Helper functions
│   ├── types/           # TypeScript type definitions
│   ├── constants/       # App constants (theme, config)
│   ├── navigation/      # Navigation configuration
│   └── App.tsx          # Root component
├── android/             # Android native code
├── ios/                 # iOS native code
└── package.json
```

## Getting Started

### Prerequisites

- Node.js >= 18
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)

### Installation

1. Install dependencies:
```bash
cd mobile/psychsync_native
npm install
```

2. Install iOS dependencies (macOS only):
```bash
cd ios && pod install && cd ..
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and backend URL
```

4. Run on iOS:
```bash
npm run ios
```

5. Run on Android:
```bash
npm run android
```

## Development

### Running Tests

```bash
npm test
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Backend API
API_BASE_URL=http://localhost:8000/api/v1

# Twilio Video
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_API_KEY=your_api_key
TWILIO_API_SECRET=your_api_secret

# Firebase (for push notifications)
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_PROJECT_ID=your_project_id

# Feature Flags
ENABLE_OFFLINE_MODE=true
ENABLE_CRISIS_DETECTION=true
```

## Key Components

### Assessment Screens

Each assessment (LSAS, EAT-26, Y-BOCS) has its own screen component:
- Dual-rating inputs for LSAS (fear + avoidance)
- Behavioral questions for EAT-26
- Progress tracking
- Real-time validation
- Offline mode support

Example:
```typescript
import LSASScreen from '@screens/assessments/LSASScreen';

// In navigation
<Stack.Screen
  name="LSAS"
  component={LSASScreen}
  options={{ title: 'Social Anxiety Assessment' }}
/>
```

### Video Consultations

Telehealth features using Twilio Video:
```typescript
import VideoConsultationScreen from '@screens/telehealth/VideoConsultationScreen';

// Schedule session
await api.scheduleSession({
  session_type: 'initial',
  consultation_reason: 'Initial consultation',
  scheduled_time: '2024-01-20T14:00:00Z',
  duration_minutes: 50,
});

// Join video call
await api.joinSession(sessionId);
```

### AI Chatbot

Crisis-aware chatbot integration:
```typescript
import ChatbotScreen from '@screens/ChatbotScreen';

// Send message
const response = await api.sendChatMessage(message, sessionId);

// Automatic crisis detection
if (response.data.crisis_detected) {
  // Show crisis resources
  displayCrisisBanner(response.data.crisis_resources);
}
```

## Security Considerations

### HIPAA Compliance

1. **Data at Rest**: All sensitive data encrypted in AsyncStorage
2. **Data in Transit**: TLS 1.3 for all API communication
3. **Authentication**: JWT tokens with automatic refresh
4. **Video**: End-to-end encryption via Twilio Video
5. **Audit Logging**: All clinical interactions logged

### Crisis Detection

The app includes 3-tier crisis detection:
- **Critical**: Immediate life threat → Call emergency services
- **High**: Significant risk → Alert clinicians immediately
- **Moderate**: Concerning → Offer resources

## Deployment

### iOS App Store

1. Update version in `package.json`
2. Build for production:
```bash
cd ios && xcodebuild -workspace PsychSync.xcworkspace \
  -scheme PsychSync \
  -configuration Release \
  -archivePath PsychSync.xcarchive archive
```

3. Upload to App Store Connect

### Google Play Store

1. Update version in `package.json`
2. Build APK/AAB:
```bash
cd android
./gradlew assembleRelease
# or
./gradlew bundleRelease
```

3. Upload to Google Play Console

## Performance Optimization

### Rendering Optimization
- Use `React.memo` for expensive components
- Implement `FlatList` for long lists
- Lazy load assessment screens

### Network Optimization
- Request debouncing
- Response caching
- Offline-first architecture

### Bundle Size
- Code splitting by feature
- Tree shaking unused dependencies
- Proguard/R8 for Android releases

## Troubleshooting

### iOS Build Issues

**Problem**: CocoaPods dependencies not linking
```bash
cd ios && pod deintegrate && pod install
```

**Problem**: Simulator won't launch
```bash
xcrun simctl erase all
npm run ios
```

### Android Build Issues

**Problem**: Gradle build fails
```bash
cd android
./gradlew clean
cd ..
npm run android
```

**Problem**: APK too large
- Enable Proguard in `android/app/build.gradle`
- Split APK by ABI

## Contributing

1. Follow TypeScript strict mode
2. Write tests for new features
3. Update documentation
4. Follow React Native performance best practices

## Support

For technical questions:
- Open an issue on GitHub
- Contact: mobile@psychsync.com

For clinical questions:
- Consult implementation guide: `ADVANCED_CLINICAL_FEATURES_IMPLEMENTATION.md`
- Review scoring algorithms: `app/services/clinical/scoring_algorithms.py`

## License

Proprietary - PsychSync © 2024
