# Biometric Authentication System

Complete biometric authentication (Face ID, Touch ID, Fingerprint) for mobile apps with enterprise-grade security.

## 🎯 Overview

The biometric authentication system enables secure, passwordless authentication using device biometrics. It uses public-key cryptography to ensure that biometric data never leaves the device.

**Supported Biometrics:**
- **iOS**: Face ID, Touch ID
- **Android**: Fingerprint, Face Unlock, Iris Scan

**Security Features:**
- Private keys stored in Secure Enclave (iOS) or TEE (Android)
- Challenge-response authentication prevents replay attacks
- Zero biometric data stored on servers
- Automatic challenge expiration (60 seconds)
- Failed attempt lockout (5 attempts)

## 🏗️ Architecture

```
┌─────────────────┐                     ┌──────────────────┐
│  Mobile App     │                     │  Backend API     │
│                 │                     │  (FastAPI)       │
│  ┌───────────┐  │  1. Request Auth    │                  │
│  │ Biometric │  │ ──────────────────> │  Generate        │
│  │  Prompt   │  │                     │  Challenge       │
│  └───────────┘  │                     │                  │
│        │        │  2. Challenge        │                  │
│        │        │ <─────────────────── │                  │
│        │        │                     │                  │
│  ┌───────────┐  │  3. Sign Challenge   │                  │
│  │ Secure    │  │ <─────────────────── │                  │
│  │ Enclave   │  │  (Private Key)      │                  │
│  └───────────┘  │                     │                  │
│        │        │  4. Signature        │                  │
│        │        │ ──────────────────> │  Verify          │
│        │        │                     │  Signature       │
│        │        │                     │  ┌────────────┐ │
│        │        │                     │  │ Public Key  │ │
│        │        │                     │  └────────────┘ │
│        │        │  5. Auth Token       │                  │
│        │        │ <─────────────────── │                  │
└─────────────────┘                     └──────────────────┘
```

### Security Model

**Registration Flow:**
1. Device generates RSA/ECDSA key pair
2. Private key stored in Secure Enclave/Keystore (never exported)
3. Public key sent to server
4. Server associates public key with user + device

**Authentication Flow:**
1. Server generates random challenge
2. Device signs challenge with private key
3. Server verifies signature using stored public key
4. Auth token issued if signature valid

**Key Benefits:**
- ✅ Biometric data never leaves device
- ✅ Server can't impersonate user (no private key)
- ✅ Compromised server can't authenticate users
- ✅ Challenges are one-time use and expire quickly
- ✅ Private keys can't be extracted from Secure Enclave

## 🚀 Quick Start

### 1. Backend Setup

#### Environment Variables

No additional environment variables needed. The system uses the existing database configuration.

#### Database Migration

The biometric authentication system requires these tables (already in models):

```sql
-- Biometric key storage
CREATE TABLE biometric_keys (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    key_id VARCHAR(255) UNIQUE NOT NULL,
    public_key TEXT NOT NULL,
    biometric_type VARCHAR(50) NOT NULL,
    device_info JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP
);

-- Challenge storage
CREATE TABLE biometric_challenges (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    key_id VARCHAR(255) NOT NULL,
    challenge VARCHAR(255) NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Attempt logging
CREATE TABLE biometric_attempts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    success BOOLEAN NOT NULL,
    error_code VARCHAR(100),
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Mobile App Setup

#### iOS Setup

**Install Dependencies:**
```bash
npm install react-native-biometrics
cd ios && pod install
```

**Configure Info.plist:**
```xml
<key>NSFaceIDUsageDescription</key>
<string>Use Face ID to securely authenticate and access your account.</string>
```

**Usage Example:**
```typescript
import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';

const rnBiometrics = new ReactNativeBiometrics({ allowDeviceCredentials: true });

// Check availability
const { available, biometryType } = await rnBiometrics.isSensorAvailable();

if (available && biometryType === BiometryTypes.FaceID) {
  // Prompt user
  const { success } = await rnBiometrics.simplePrompt({
    promptMessage: 'Authenticate',
    cancelButtonText: 'Cancel',
  });

  if (success) {
    // Generate keys and sign challenge
    const { publicKey } = await rnBiometrics.createKeys();

    // Sign server challenge
    const { signature } = await rnBiometrics.createSignature({
      promptMessage: 'Sign authentication challenge',
      payload: challengeString,
    });

    // Send to server
    await completeRegistration({ publicKey, signature });
  }
}
```

#### Android Setup

**Configure AndroidManifest.xml:**
```xml
<uses-permission android:name="android.permission.USE_BIOMETRIC" />
```

**Usage (same as iOS):**
```typescript
import ReactNativeBiometrics from 'react-native-biometrics';

const rnBiometrics = new ReactNativeBiometrics({ allowDeviceCredentials: true });

// Same implementation as iOS
const { success } = await rnBiometrics.simplePrompt({
  promptMessage: 'Authenticate',
});
```

### 3. Frontend Integration

#### Using the Service

```typescript
import { biometricAuthService } from '@/services/biometricAuth';

// Check availability
const available = await biometricAuthService.isBiometricAvailable();

// Register
const initResponse = await biometricAuthService.initiateRegistration('face_id');
// Prompt user for biometric
const confirmed = await biometricAuthService.promptBiometric('Register Face ID');
if (confirmed) {
  // Generate keys and sign challenge (native code)
  await completeRegistration({ publicKey, signature });
}

// Authenticate
const challenge = await biometricAuthService.initiateAuthentication();
// Prompt user
const confirmed = await biometricAuthService.promptBiometric('Authenticate');
if (confirmed) {
  // Sign challenge (native code)
  const result = await verifyAuthentication({ signature });
}
```

#### Using the React Hook

```typescript
import { useBiometricAuth } from '@/hooks/useBiometricAuth';

function BiometricLogin() {
  const {
    isAvailable,
    isRegistered,
    register,
    authenticate,
  } = useBiometricAuth();

  const handleAuth = async () => {
    const result = await authenticate();
    if (result.success) {
      console.log('Authenticated!', result.auth_token);
    }
  };

  return (
    <View>
      {isAvailable && !isRegistered && (
        <Button onPress={register} title="Enable Face ID" />
      )}
      {isRegistered && (
        <Button onPress={handleAuth} title="Sign in with Face ID" />
      )}
    </View>
  );
}
```

#### Using the UI Component

```typescript
import BiometricAuthSettings from '@/components/mobile/BiometricAuthSettings';

function SettingsScreen() {
  return (
    <BiometricAuthSettings
      onAuthenticationSuccess={(result) => {
        console.log('Auth successful:', result.auth_token);
        // Navigate to authenticated screen
      }}
      onRegistrationSuccess={() => {
        console.log('Registration successful');
      }}
    />
  );
}
```

## 📋 API Reference

### POST /api/v1/biometric-auth/register/initiate

Initiate biometric registration.

**Request:**
```json
{
  "device_id": "unique-device-id",
  "biometric_type": "face_id",
  "device_info": {
    "platform": "ios",
    "model": "iPhone 14"
  }
}
```

**Response:**
```json
{
  "registration_challenge": "random-challenge-string",
  "challenge_expires_in": 300,
  "biometric_type": "face_id",
  "device_info": {}
}
```

### POST /api/v1/biometric-auth/register/complete

Complete biometric registration.

**Request:**
```json
{
  "device_id": "unique-device-id",
  "public_key": "PEM-encoded-public-key",
  "challenge_signature": "base64-signature",
  "key_id": "optional-key-id"
}
```

**Response:**
```json
{
  "success": true,
  "key_id": "key-identifier",
  "registered_at": "2024-01-17T10:00:00Z",
  "message": "Biometric authentication registered successfully"
}
```

### POST /api/v1/biometric-auth/authenticate/initiate

Initiate biometric authentication.

**Request:**
```json
{
  "device_id": "unique-device-id"
}
```

**Response:**
```json
{
  "challenge": "random-challenge-string",
  "challenge_id": "challenge-uuid",
  "expires_in": 60,
  "key_id": "key-identifier"
}
```

### POST /api/v1/biometric-auth/authenticate/verify

Verify biometric authentication.

**Request:**
```json
{
  "device_id": "unique-device-id",
  "challenge_id": "challenge-uuid",
  "signature": "base64-signature"
}
```

**Response:**
```json
{
  "success": true,
  "authenticated": true,
  "auth_token": "jwt-token",
  "token_type": "Bearer",
  "expires_in": 3600,
  "message": "Biometric authentication successful"
}
```

### POST /api/v1/biometric-auth/revoke

Revoke biometric authentication.

**Request:**
```json
{
  "device_id": "unique-device-id"
}
```

### GET /api/v1/biometric-auth/devices

Get all registered devices.

**Response:**
```json
{
  "devices": [
    {
      "device_id": "unique-device-id",
      "key_id": "key-identifier",
      "biometric_type": "face_id",
      "registered_at": "2024-01-17T10:00:00Z",
      "last_used_at": "2024-01-17T12:00:00Z"
    }
  ],
  "total": 1
}
```

### GET /api/v1/biometric-auth/status?device_id={id}

Get biometric status for device.

**Response:**
```json
{
  "enabled": true,
  "biometric_type": "face_id",
  "registered_at": "2024-01-17T10:00:00Z",
  "last_used_at": "2024-01-17T12:00:00Z"
}
```

### GET /api/v1/biometric-auth/types

List supported biometric types.

**Response:**
```json
{
  "biometric_types": [
    {
      "type": "face_id",
      "name": "Face ID",
      "platform": "ios",
      "description": "3D facial recognition",
      "min_version": "iOS 11.0"
    }
  ],
  "total_types": 5
}
```

## 🔒 Security Best Practices

### 1. Private Key Protection
- ✅ Private keys stored in Secure Enclave (iOS) or TEE (Android)
- ✅ Keys never exported from secure hardware
- ✅ Key operations performed in hardware only

### 2. Challenge Management
- ✅ Challenges are cryptographically random (32 bytes)
- ✅ Challenges expire after 60 seconds
- ✅ Each challenge can only be used once
- ✅ Challenges tied to specific user + device

### 3. Rate Limiting
- ✅ 5 failed attempts triggers lockout
- ✅ Lockout duration: 15 minutes
- ✅ Attempts tracked per device

### 4. Data Protection
- ✅ No biometric data stored on servers
- ✅ Only public keys stored (not secret)
- ✅ All communication over HTTPS
- ✅ Signature verification prevents tampering

## 🧪 Testing

### Unit Tests

```python
import pytest
from app.services.biometric_auth_service import biometric_auth_service

@pytest.mark.asyncio
async def test_initiate_registration(db_session, test_user):
    result = await biometric_auth_service.initiate_registration(
        db=db_session,
        user_id=test_user.id,
        device_id="test-device",
        biometric_type="face_id"
    )

    assert "registration_challenge" in result
    assert result["challenge_expires_in"] == 300

@pytest.mark.asyncio
async def test_generate_challenge(db_session, test_user, registered_biometric):
    result = await biometric_auth_service.generate_challenge(
        db=db_session,
        user_id=test_user.id,
        device_id="test-device"
    )

    assert "challenge" in result
    assert result["expires_in"] == 60
```

### Integration Tests

```typescript
import { biometricAuthService } from '@/services/biometricAuth';

test('biometric registration flow', async () => {
  // Check availability
  const available = await biometricAuthService.isBiometricAvailable();
  expect(available).toBe(true);

  // Initiate registration
  const initResponse = await biometricAuthService.initiateRegistration('face_id');
  expect(initResponse).toHaveProperty('registration_challenge');

  // Complete registration
  const completeResponse = await biometricAuthService.completeRegistration({
    device_id: 'test-device',
    public_key: 'mock-public-key',
    challenge_signature: 'mock-signature',
  });
  expect(completeResponse.success).toBe(true);
});
```

## 🐛 Troubleshooting

### iOS Issues

**Face ID not available:**
- Ensure device supports Face ID (iPhone X or later)
- Check Face ID is enrolled in Settings → Face ID & Passcode
- Verify NSFaceIDUsageDescription in Info.plist
- Test on physical device (simulator doesn't support Face ID)

**Key generation fails:**
- Ensure Secure Enclave is available
- Check app has proper entitlements
- Verify keychain access is configured

**Signature verification fails:**
- Ensure challenge hasn't expired (60 second window)
- Check signature is base64-encoded
- Verify correct public key is registered

### Android Issues

**Fingerprint not available:**
- Ensure device has fingerprint sensor
- Check fingerprint is enrolled in Settings → Security
- Verify USE_BIOMETRIC permission in manifest
- Test on physical device with fingerprint enrolled

**BiometricPrompt errors:**
- Ensure you're using BiometricPrompt (not deprecated FingerprintManager)
- Check minSdkVersion is 28 (Android 9.0) or higher
- Verify biometric is enrolled before calling authenticate

### Common Issues

**Challenge expired:**
- Complete authentication within 60 seconds
- Don't reuse challenges

**Device not registered:**
- Call register/initiate first
- Check device ID matches registration

**Too many failed attempts:**
- Wait 15 minutes for lockout to expire
- Use password as fallback

## 📊 Monitoring & Analytics

Track these metrics for security and UX:

- **Registration Rate** - Users enabling biometric / Total users
- **Authentication Success Rate** - Successful / Total attempts
- **Failure Reasons** - Challenge expired, signature invalid, etc.
- **Platform Breakdown** - iOS vs Android usage
- **Biometric Type** - Face ID vs Touch ID vs Fingerprint
- **Attempt Frequency** - Average attempts per user per day
- **Security Events** - Failed attempt patterns, lockouts

## 🎯 Best Practices

1. **Always provide fallback** - Password should always work
2. **Explain the benefits** - Speed, security, convenience
3. **Respect user choice** - Don't force biometric registration
4. **Handle errors gracefully** - Clear error messages, recovery options
5. **Test on physical devices** - Simulators don't support biometrics
6. **Monitor success rates** - Track and optimize the flow
7. **Educate users** - Explain how biometrics work and security

## 🔄 Next Steps

1. ✅ Backend service and database models
2. ✅ API endpoints for registration and authentication
3. ✅ Frontend service and React hook
4. ✅ Mobile UI components
5. ⏳ **TODO:** Implement failed attempt tracking with Redis
6. ⏳ **TODO:** Add biometric auth to login screen
7. ⏳ **TODO:** Implement biometric-based transaction signing
8. ⏳ **TODO:** Add analytics dashboard for biometric usage
9. ⏳ **TODO:** Support multiple biometrics per device
10. ⏳ **TODO:** WebAuthn support for desktop browsers

---

**Status:** ✅ Core implementation complete

**Last Updated:** January 17, 2026

**Maintainer:** PsychSync Engineering Team
