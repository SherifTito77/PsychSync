# Wearable Device Integration Guide

This guide shows how to integrate popular wearable devices with the PsychSync Health Monitoring System.

## Table of Contents
1. [Overview](#overview)
2. [Supported Devices](#supported-devices)
3. [Integration Methods](#integration-methods)
4. [Device-Specific Guides](#device-specific-guides)
5. [API Usage](#api-usage)
6. [Data Mapping](#data-mapping)
7. [Privacy & Security](#privacy--security)
8. [Testing](#testing)

## Overview

The health monitoring system accepts biometric data from any source through the REST API. The system validates, stores, and analyzes this data alongside work patterns and communication metrics to provide comprehensive health risk assessments.

**Key Benefits:**
- Real-time health risk detection
- Objective physiological validation
- Continuous monitoring without user effort
- Early warning of cardiovascular issues

## Supported Devices

| Device | Data Types | Integration Method | Difficulty |
|--------|-----------|-------------------|------------|
| **Apple Health** | HR, HRV, Sleep, Steps, BP | HealthKit API | Medium |
| **Google Fit** | HR, Sleep, Steps, Activity | Google Fit REST API | Medium |
| **Fitbit** | HR, Sleep, Steps, Activity | Fitbit Web API | Easy |
| **Garmin** | HR, HRV, Sleep, Steps, Stress | Health API | Medium |
| **Whoop** | HR, HRV, Sleep, Recovery, Strain | Whoop API | Easy |
| **Oura Ring** | HR, HRV, Sleep, Activity | Oura API v2 | Medium |

## Integration Methods

### Method 1: Direct API Integration (Recommended)

Create a backend service that:
1. Authenticates with the device's API
2. Fetches data periodically (hourly/daily)
3. Submits to PsychSync health monitoring API

**Pros:**
- Real-time data sync
- No user action required after setup
- Can run on server

**Cons:**
- Requires OAuth setup
- Need to handle rate limits
- More complex implementation

### Method 2: User-Submitted Export

User exports data from device app and uploads:
1. User downloads CSV/JSON from device app
2. User uploads to PsychSync
3. System parses and stores data

**Pros:**
- Simple to implement
- No OAuth complexity
- User controls when data is shared

**Cons:**
- Manual process
- Not real-time
- User burden

### Method 3: Mobile App Integration

Create a mobile app that:
1. Connects to device using native SDKs
2. Syncs data in background
3. Submits to PsychSync API

**Pros:**
- Best user experience
- Background sync
- Native device features

**Cons:**
- Need to develop mobile apps
- Platform-specific (iOS/Android)

## Device-Specific Guides

### 1. Apple Health (HealthKit)

**Setup:**
```bash
npm install react-native-health
```

**Code Example:**
```typescript
import AppleHealthKit from 'react-native-health';

// Init
const healthKit = new AppleHealthKit();
await healthKit.initHealthKit();

// Request permissions
const permissions = {
  permissions: {
    read: ['HeartRate', 'HeartRateVariability', 'SleepAnalysis', 'Steps', 'BloodPressure'],
    write: []
  }
};
await healthKit.requestAuthorization(permissions);

// Fetch heart rate data
const heartRate = await healthKit.getHeartRateSamples({
  startDate: new Date(2025, 0, 1),
  endDate: new Date(),
  limit: 100
});

// Submit to PsychSync
fetch('/api/v1/health-monitoring/biometric', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    data_source: 'apple_health',
    measurement_date: new Date().toISOString().split('T')[0],
    resting_heart_rate: heartRate.avg,
    heart_rate_variability: hrvData.avg,
    sleep_hours: sleepData.totalSleepTime / 3600,
    steps_count: stepsData.value
  })
});
```

**Required iOS Permissions:**
```xml
<!-- Info.plist -->
<key>NSHealthShareUsageDescription</key>
<string>We need access to your health data to monitor stress and prevent burnout.</string>
<key>NSHealthUpdateUsageDescription</key>
<string>We need to save health data to track your wellness over time.</string>
```

### 2. Google Fit

**Setup:**
```bash
npm install react-native-google-fit
```

**Code Example:**
```typescript
import GoogleFit from 'react-native-google-fit';

// Init
GoogleFit.init();

// Authorize
const options = {
  scopes: [
    Scopes.FITNESS_HEART_RATE_READ,
    Scopes.FITNESS_SLEEP_READ,
    Scopes.FITNESS_ACTIVITY_READ
  ]
};
await GoogleFit.authorize(options);

// Fetch daily heart rate
const heartRate = await GoogleFit.getHeartRateSamples({
  startDate: new Date(2025, 0, 1).toISOString(),
  endDate: new Date().toISOString()
});

// Submit to PsychSync
fetch('/api/v1/health-monitoring/biometric', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    data_source: 'google_fit',
    measurement_date: new Date().toISOString().split('T')[0],
    avg_heart_rate: heartRate.raw.reduce((a, b) => a + b.value, 0) / heartRate.raw.length,
    steps_count: stepsData.steps
  })
});
```

### 3. Fitbit

**Setup:**
1. Create Fitbit app: https://dev.fitbit.com/
2. Get OAuth credentials
3. Use Fitbit Web API

**Code Example:**
```python
import requests
from datetime import datetime

# OAuth flow (simplified)
AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"

# After getting access token...
access_token = "your_access_token"

# Fetch heart rate data
url = f"https://api.fitbit.com/1/user/-/activities/heart/date/today/1d.json"
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(url, headers=headers)
data = response.json()

# Get resting heart rate
resting_hr = data['activities-heart'][0]['restingHeartRate']

# Submit to PsychSync
psychsync_url = "http://localhost:8000/api/v1/health-monitoring/biometric"
headers = {
    "Authorization": f"Bearer {psychsync_token}",
    "Content-Type": "application/json"
}
biometric_data = {
    "data_source": "fitbit",
    "measurement_date": datetime.now().strftime('%Y-%m-%d'),
    "resting_heart_rate": resting_hr,
    "steps_count": data['activities-heart'][0]['heartRateZones'][0]['minutes']
}
requests.post(psychsync_url, json=biometric_data, headers=headers)
```

### 4. Whoop

**Setup:**
1. Create Whoop account: https://www.whoop.com/
2. Get API access
3. Use Whoop API

**API Endpoint:**
```
GET https://api.prod.whoop.com/developer/v1/users/{user_id}/cycle/{cycle_id}
```

**Code Example:**
```python
import requests

WHOOP_API = "https://api.prod.whoop.com/developer/v1"
api_key = "your_api_key"

# Get today's cycle
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(
    f"{WHOOP_API}/cycle/{cycle_id}",
    headers=headers
)
data = response.json()

# Extract metrics
hrv = data['cycle']['hrv']
resting_hr = data['cycle']['resting_heart_rate']
sleep = data['cycle']['sleep']['duration'] / 3600  # Convert to hours
recovery = data['cycle']['recovery_score']

# Submit to PsychSync
# ... (same as above)
```

### 5. Garmin Health API

**Setup:**
1. Register app: https://developer.garmin.com/
2. Use Health API

**Code Example:**
```python
from garmin_connect import Garmin

# Connect
client = Garmin("email", "password")
client.login()

# Get today's data
activities = client.get_activities(1)  # Last day
hr_data = client.get_heart_rates(1)  # Last day
sleep_data = client.get_sleep_data(1)

# Extract metrics
avg_hr = sum([d['heartRate'] for d in hr_data]) / len(hr_data)
steps = activities[0]['steps']
sleep = sleep_data[0]['totalSleepSeconds'] / 3600

# Submit to PsychSync
# ... (same as above)
```

## API Usage

### Endpoint
```
POST /api/v1/health-monitoring/biometric
```

### Request Body
```json
{
  "data_source": "whoop",
  "measurement_date": "2025-01-14",
  "resting_heart_rate": 75,
  "heart_rate_variability": 65,
  "avg_heart_rate": 72,
  "blood_pressure_systolic": 118,
  "blood_pressure_diastolic": 78,
  "oxygen_saturation": 98,
  "sleep_hours": 7.5,
  "sleep_quality_score": 0.85,
  "deep_sleep_hours": 1.8,
  "rem_sleep_hours": 2.1,
  "light_sleep_hours": 3.2,
  "steps_count": 10500,
  "activity_minutes": 75,
  "moderate_activity_minutes": 45,
  "vigorous_activity_minutes": 30
}
```

### Response
```json
{
  "success": true,
  "data_id": "uuid-1234",
  "risk_indicators": {
    "risks_detected": false,
    "risk_count": 0,
    "max_severity": "none",
    "risks": []
  }
}
```

## Data Mapping

### Apple Health → PsychSync

| Apple Health | PsychSync Field | Type |
|-------------|-----------------|------|
| HKQuantityTypeIdentifierHeartRateVariabilitySDNN | heart_rate_variability | Float (ms) |
| HKQuantityTypeIdentifierRestingHeartRate | resting_heart_rate | Float (bpm) |
| HKCategoryTypeIdentifierSleepAnalysis | sleep_hours | Float (hours) |
| HKQuantityTypeIdentifierStepCount | steps_count | Integer |
| HKQuantityTypeIdentifierBloodPressureSystolic | blood_pressure_systolic | Integer |

### Whoop → PsychSync

| Whoop | PsychSync Field | Type |
|-------|-----------------|------|
| cycle.hrv | heart_rate_variability | Float (ms) |
| cycle.resting_heart_rate | resting_heart_rate | Float (bpm) |
| cycle.sleep.duration | sleep_hours | Float (hours) |
| cycle.recovery_score | recovery_score | Float (0-100) |
| cycle.strain | stress_score | Float (0-21) |

### Fitbit → PsychSync

| Fitbit | PsychSync Field | Type |
|--------|-----------------|------|
| restingHeartRate | resting_heart_rate | Integer |
| minutesSedentary | sedentary_minutes | Integer |
| steps | steps_count | Integer |
| minutesAsleep | sleep_hours | Float (hours) |
| efficiency | sleep_efficiency | Float (%) |

## Privacy & Security

### 1. User Consent

Before collecting biometric data, users must give explicit consent:

```bash
# Check consent status
GET /api/v1/health-monitoring/consent

# Update consent
POST /api/v1/health-monitoring/consent
{
  "biometric_collection": true,
  "biometric_processing": true,
  "biometric_sharing": false,
  "data_sources": ["whoop", "apple_health"],
  "data_retention_days": 365
}
```

### 2. Data Encryption

- Store access tokens encrypted at rest
- Use HTTPS for all API calls
- Encrypt biometric data in database (optional)

### 3. Data Retention

Users control how long data is kept:
- Default: 365 days
- User can set any retention period
- Automatic deletion after period expires

### 4. Access Control

- Users can delete their data anytime
- Only user can see their individual data
- Managers see anonymized aggregates only

## Testing

### Test Biometric Submission

```bash
# Test with sample data
curl -X POST "http://localhost:8000/api/v1/health-monitoring/biometric" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data_source": "test",
    "measurement_date": "2025-01-14",
    "resting_heart_rate": 85,
    "heart_rate_variability": 42,
    "blood_pressure_systolic": 145,
    "blood_pressure_diastolic": 95,
    "sleep_hours": 5.2,
    "steps_count": 3500
  }'
```

### Expected Response for High Risk:

```json
{
  "success": true,
  "data_id": "uuid",
  "risk_indicators": {
    "risks_detected": true,
    "risk_count": 4,
    "max_severity": "high",
    "risks": [
      {
        "indicator": "elevated_rhr",
        "severity": "high",
        "value": 85,
        "message": "Elevated resting heart rate: 85 bpm"
      },
      {
        "indicator": "low_hrv",
        "severity": "high",
        "value": 42,
        "message": "Low heart rate variability: 42 ms (indicates stress)"
      },
      {
        "indicator": "high_bp_systolic",
        "severity": "critical",
        "value": 145,
        "message": "High systolic blood pressure: 145 mmHg"
      },
      {
        "indicator": "sleep_deprivation",
        "severity": "high",
        "value": 5.2,
        "message": "Insufficient sleep: 5.2 hours"
      }
    ]
  }
}
```

## Best Practices

### 1. Error Handling
```typescript
try {
  await submitBiometric(data);
} catch (error) {
  if (error.response?.status === 400) {
    // Invalid data format
    console.error('Invalid biometric data');
  } else if (error.response?.status === 403) {
    // User hasn't given consent
    console.error('User consent required');
  }
}
```

### 2. Rate Limiting
- Don't submit data more than once per hour per user
- Batch data when possible
- Handle 429 Too Many Requests responses

### 3. Data Validation
```typescript
// Validate before submitting
if (data.resting_heart_rate < 30 || data.resting_heart_rate > 220) {
  throw new Error('Invalid heart rate');
}
if (data.sleep_hours < 0 || data.sleep_hours > 24) {
  throw new Error('Invalid sleep duration');
}
```

### 4. Background Sync
```typescript
// Sync every hour
setInterval(async () => {
  const data = await fetchFromWearable();
  await submitToPsychSync(data);
}, 60 * 60 * 1000);
```

## Complete Integration Example

```typescript
import { useState, useEffect } from 'react';

export const WearableConnector: React.FC = () => {
  const [connectedDevice, setConnectedDevice] = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<Date | null>(null);
  const [syncing, setSyncing] = useState(false);

  // Connect to device
  const connectDevice = async (deviceType: 'apple' | 'fitbit' | 'whoop') => {
    try {
      if (deviceType === 'apple') {
        await connectAppleHealth();
      } else if (deviceType === 'fitbit') {
        await connectFitbit();
      } else if (deviceType === 'whoop') {
        await connectWhoop();
      }
      setConnectedDevice(deviceType);
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  };

  // Sync data
  const syncData = async () => {
    if (!connectedDevice) return;

    setSyncing(true);
    try {
      let biometricData;

      if (connectedDevice === 'apple') {
        biometricData = await fetchFromAppleHealth();
      } else if (connectedDevice === 'fitbit') {
        biometricData = await fetchFromFitbit();
      } else if (connectedDevice === 'whoop') {
        biometricData = await fetchFromWhoop();
      }

      // Submit to PsychSync
      await submitToPsychSync(biometricData);
      setLastSync(new Date());
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="wearable-connector">
      <h3>Connect Your Wearable</h3>
      <div className="device-buttons">
        <button onClick={() => connectDevice('apple')}>
          Connect Apple Health
        </button>
        <button onClick={() => connectDevice('fitbit')}>
          Connect Fitbit
        </button>
        <button onClick={() => connectDevice('whoop')}>
          Connect Whoop
        </button>
      </div>
      {connectedDevice && (
        <div className="sync-controls">
          <p>Connected to: {connectedDevice}</p>
          <button onClick={syncData} disabled={syncing}>
            {syncing ? 'Syncing...' : 'Sync Now'}
          </button>
          {lastSync && (
            <p>Last synced: {lastSync.toLocaleString()}</p>
          )}
        </div>
      )}
    </div>
  );
};
```

## Troubleshooting

### Issue: "User consent required"

**Solution:** User must first give consent through the consent endpoint.

### Issue: "Invalid biometric data"

**Solution:** Check data ranges (see validation rules in API docs).

### Issue: "Data source not supported"

**Solution:** Ensure `data_source` matches one of: `apple_health`, `google_fit`, `fitbit`, `garmin`, `whoop`, `oura_ring`, or `manual_entry`.

### Issue: Rate limit exceeded

**Solution:** Reduce sync frequency or implement exponential backoff.

## Support

For integration help:
- API docs: `http://localhost:8000/docs`
- Tests: `tests/api/test_health_monitoring.py`
- Demo: `python demo_health_monitoring.py`

---

**Remember:** Biometric data is sensitive health information. Always:
1. Get explicit user consent
2. Encrypt data at rest and in transit
3. Follow GDPR/HIPAA guidelines
4. Allow users to delete their data
5. Be transparent about data usage
