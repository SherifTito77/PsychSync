# Real-Time Stress & Burnout Monitoring System - Frontend Integration Guide

This guide provides comprehensive information for integrating and using the Real-Time Stress & Burnout Monitoring System and Automated Intervention & Alert System in the frontend.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Services](#services)
5. [Type Definitions](#type-definitions)
6. [Usage Examples](#usage-examples)
7. [Real-Time Monitoring](#real-time-monitoring)
8. [Manager Dashboard](#manager-dashboard)
9. [Route Configuration](#route-configuration)
10. [Best Practices](#best-practices)

---

## Overview

The health monitoring system provides:

- **Personal Health Dashboard**: Individual health risk analysis, stress monitoring, and biometric tracking
- **Automated Interventions**: Intelligent intervention generation based on health risks
- **Manager Dashboard**: Anonymized team health analytics for managers and HR
- **Real-Time Monitoring**: Live health updates via WebSocket with polling fallback
- **Alert System**: Context-aware health alerts with severity levels

---

## Architecture

### Service Layer

```
HealthMonitoringService
  ├─ analyzeHealthRisks()
  ├─ getHealthReport()
  ├─ submitBiometricData()
  └─ updateConsentPreferences()

InterventionService
  ├─ createInterventionPlan()
  ├─ createProgram()
  ├─ analyzeEffectiveness()
  └─ getEffectivenessResults()

ManagerDashboardService
  ├─ getTeamDashboard()
  ├─ getOrganizationOverview()
  └─ getTeamOverview()
```

### Component Layer

```
EnhancedHealthDashboard (Personal)
  ├─ Health Risk Scores
  ├─ Risk Factors & Warning Signs
  ├─ Active Interventions
  └─ Biometric Data Submission

ManagerDashboard (Team Analytics)
  ├─ Team Stress Distribution
  ├─ Cardiovascular Risk Distribution
  ├─ Weekly Stress Trends
  └─ Organizational Risk Factors

HealthAlertBanner (Notifications)
  ├─ Severity-Based Styling
  ├─ Action Buttons
  └─ Resource Links
```

---

## Components

### 1. EnhancedHealthDashboard

Personal health dashboard with real-time monitoring.

**Location**: `frontend/src/components/health/EnhancedHealthDashboard.tsx`

**Features**:
- Real-time health risk display
- Cardiovascular and mental health risk gauges
- Stress level indicators
- Active intervention management
- Tabbed interface for different views
- Live updates via WebSocket

**Usage**:
```tsx
import { EnhancedHealthDashboard } from '@/components/health/EnhancedHealthDashboard';

function HealthPage() {
  return <EnhancedHealthDashboard />;
}
```

### 2. ManagerDashboard

Privacy-focused team health analytics for managers and HR.

**Location**: `frontend/src/components/health/ManagerDashboard.tsx`

**Features**:
- Anonymized team health metrics
- Stress level distribution
- Cardiovascular risk trends
- Weekly stress trend analysis
- High-risk member counts (no identities)
- Organizational risk factors

**Usage**:
```tsx
import { ManagerDashboard } from '@/components/health/ManagerDashboard';

function TeamHealthPage() {
  return <ManagerDashboard />;
}
```

### 3. HealthAlertBanner

Display health intervention alerts with severity-based styling.

**Location**: `frontend/src/components/health/HealthAlertBanner.tsx`

**Features**:
- Animated alert banner
- Severity-based styling (critical, high, medium, low)
- Action buttons for quick responses
- Resource links
- Dismissible alerts

**Usage**:
```tsx
import { HealthAlertContainer } from '@/components/health/HealthAlertBanner';

function AlertsPage() {
  const interventions = [
    // Your intervention data
  ];

  return (
    <HealthAlertContainer
      interventions={interventions}
      onDismiss={(id) => console.log('Dismissed:', id)}
      onAcknowledge={(id) => console.log('Acknowledged:', id)}
    />
  );
}
```

---

## Services

### HealthMonitoringService

Service for personal health monitoring and biometric data.

**Location**: `frontend/src/services/healthMonitoringService.ts`

**Key Methods**:

```typescript
// Quick health check (7 days)
const healthData = await HealthMonitoringService.quickHealthCheck();

// Comprehensive analysis (90 days)
const fullAnalysis = await HealthMonitoringService.comprehensiveHealthAnalysis(biometricData);

// Custom time window
const analysis = await HealthMonitoringService.analyzeHealthRisks({
  time_window_days: 30,
  include_biometric: true,
  biometric_data: myBiometricData
});

// Get health report
const report = await HealthMonitoringService.getHealthReport(30);

// Submit biometric data
const result = await HealthMonitoringService.submitBiometricData(biometricData);

// Consent management
const consent = await HealthMonitoringService.getConsentStatus();
await HealthMonitoringService.updateConsentPreferences({
  biometric_collection: true,
  biometric_processing: true,
  biometric_sharing: false,
  data_retention_days: 365
});
```

### InterventionService

Service for managing health interventions and programs.

**Location**: `frontend/src/services/interventionService.ts`

**Key Methods**:

```typescript
// Create intervention plan
const interventions = await InterventionService.createInterventionPlan({
  health_risks: healthRiskData,
  work_patterns: workPatternData
});

// Create intervention program
const program = await InterventionService.createProgram({
  title: 'Stress Management Workshop',
  category: 'stress_management',
  start_date: '2025-01-20',
  participants_target: 25,
  priority: 'high'
});

// List programs
const activePrograms = await InterventionService.listPrograms({
  status: 'active',
  limit: 50
});

// Analyze effectiveness
const analysis = await InterventionService.analyzeEffectiveness({
  intervention_id: 'abc-123',
  metrics: ['stress_level', 'sleep_quality'],
  significance_level: 0.05
});

// Get effectiveness results
const results = await InterventionService.getEffectivenessResults('abc-123');
```

### ManagerDashboardService

Service for team health analytics (managers/HR only).

**Location**: `frontend/src/services/managerDashboardService.ts`

**Key Methods**:

```typescript
// Get organization overview
const orgOverview = await ManagerDashboardService.getOrganizationOverview(30);

// Get specific team data
const teamData = await ManagerDashboardService.getTeamOverview('team-123', 30);

// Get weekly trends
const trends = await ManagerDashboardService.getWeeklyTrends('team-123');

// Get quarterly report
const quarterly = await ManagerDashboardService.getQuarterlyReport();

// Check access permissions
const hasAccess = await ManagerDashboardService.checkManagerAccess();
```

---

## Type Definitions

All health monitoring types are centralized in:

**Location**: `frontend/src/types/healthMonitoring.ts`

**Key Types**:

```typescript
// Health risk data
interface HealthRiskData {
  stress_level: StressLevel;  // 'normal' | 'elevated' | 'high' | 'critical'
  burnout_stage: BurnoutStage;
  cardiovascular_risk_score: number;
  mental_health_risk: number;
  work_life_imbalance: number;
  sleep_disruption_score: number;
  // ... more fields
}

// Biometric data
interface BiometricData {
  data_source: string;
  measurement_date: string;
  resting_heart_rate?: number;
  heart_rate_variability?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  sleep_hours?: number;
  steps_count?: number;
  // ... more fields
}

// Intervention
interface Intervention {
  intervention_id: string;
  intervention_type: InterventionType;
  urgency: InterventionUrgency;
  title: string;
  message: string;
  actions_required: string[];
  resources: InterventionResource[];
  // ... more fields
}

// Manager dashboard data
interface ManagerDashboardData {
  team_id: string;
  team_name: string;
  stress_distribution: StressDistribution;
  cardiovascular_risk_distribution: CardiovascularRiskDistribution;
  weekly_stress_trend: WeeklyStressTrend[];
  // ... more fields
}
```

---

## Usage Examples

### Example 1: Personal Health Dashboard

```tsx
import React from 'react';
import { EnhancedHealthDashboard } from '@/components/health/EnhancedHealthDashboard';

export default function HealthPage() {
  return (
    <div className="container mx-auto py-6">
      <EnhancedHealthDashboard />
    </div>
  );
}
```

### Example 2: Manager Dashboard with Access Control

```tsx
import React, { useEffect, useState } from 'react';
import { ManagerDashboard } from '@/components/health/ManagerDashboard';
import ManagerDashboardService from '@/services/managerDashboardService';

export default function TeamHealthPage() {
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAccess = async () => {
      try {
        const access = await ManagerDashboardService.checkManagerAccess();
        setHasAccess(access);
      } catch (error) {
        console.error('Failed to check access:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAccess();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!hasAccess) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold mb-2">Access Denied</h2>
        <p>You don't have permission to view team health analytics.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <ManagerDashboard />
    </div>
  );
}
```

### Example 3: Custom Health Analysis

```tsx
import React, { useState } from 'react';
import HealthMonitoringService from '@/services/healthMonitoringService';
import type { HealthRiskData } from '@/types/healthMonitoring';

export default function CustomHealthAnalysis() {
  const [healthData, setHealthData] = useState<HealthRiskData | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const runAnalysis = async (days: number) => {
    setAnalyzing(true);
    try {
      const data = await HealthMonitoringService.analyzeHealthRisks({
        time_window_days: days,
      });
      setHealthData(data);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div>
      <button onClick={() => runAnalysis(7)}>Last 7 days</button>
      <button onClick={() => runAnalysis(30)}>Last 30 days</button>
      <button onClick={() => runAnalysis(90)}>Last 90 days</button>

      {healthData && (
        <div>
          <h3>Stress Level: {healthData.stress_level}</h3>
          <p>Risk Score: {(healthData.cardiovascular_risk_score * 100).toFixed(0)}%</p>
        </div>
      )}
    </div>
  );
}
```

---

## Real-Time Monitoring

### WebSocket Integration

The system uses WebSocket for real-time health updates with automatic polling fallback.

**Hook**: `useRealTimeHealthMonitoring`

**Location**: `frontend/src/hooks/useRealTimeHealthMonitoring.ts`

**Usage**:

```tsx
import { useRealTimeHealthMonitoring } from '@/hooks/useRealTimeHealthMonitoring';

function MyComponent() {
  const {
    isConnected,           // WebSocket connection status
    currentStressLevel,    // Current stress level
    latestUpdate,          // Latest health update
    alerts,                // Array of health alerts
    acknowledgeAlert,      // Function to acknowledge alert
    clearAlerts,           // Function to clear all alerts
  } = useRealTimeHealthMonitoring({
    enabled: true,
    onHealthAlert: (alert) => {
      console.log('New health alert:', alert);
      // Custom alert handling
    },
    onHealthUpdate: (update) => {
      console.log('Health updated:', update);
      // Custom update handling
    },
    updateInterval: 60000, // 1 minute polling fallback
  });

  return (
    <div>
      <p>Connection: {isConnected ? 'Connected' : 'Connecting...'}</p>
      <p>Current Stress: {currentStressLevel}</p>
      <p>Active Alerts: {alerts.length}</p>
    </div>
  );
}
```

---

## Route Configuration

Add these routes to your React Router configuration:

```tsx
// App.tsx or routes configuration file
import { EnhancedHealthDashboard } from '@/components/health/EnhancedHealthDashboard';
import { ManagerDashboard } from '@/components/health/ManagerDashboard';
import { MentalHealthWellness } from '@/pages/MentalHealthWellness';

const routes = [
  // Personal health monitoring
  {
    path: '/health',
    element: <EnhancedHealthDashboard />,
    meta: { requiresAuth: true, title: 'Health Dashboard' }
  },

  // Manager dashboard (requires manager/HR role)
  {
    path: '/team-health',
    element: <ManagerDashboard />,
    meta: { requiresAuth: true, requiresRole: ['manager', 'hr', 'admin'], title: 'Team Health' }
  },

  // Mental health & wellness hub
  {
    path: '/mental-health',
    element: <MentalHealthWellness />,
    meta: { requiresAuth: true, title: 'Mental Health & Wellness' }
  },
];
```

---

## Best Practices

### 1. Error Handling

Always wrap service calls in try-catch blocks:

```tsx
const analyzeHealth = async () => {
  try {
    const data = await HealthMonitoringService.analyzeHealthRisks();
    setHealthData(data);
  } catch (error) {
    console.error('Health analysis failed:', error);
    // Show user-friendly error message
    toast({
      title: 'Analysis Failed',
      description: 'Unable to analyze health data. Please try again.',
      variant: 'destructive',
    });
  }
};
```

### 2. Loading States

Provide loading indicators for better UX:

```tsx
const [loading, setLoading] = useState(false);

const handleRefresh = async () => {
  setLoading(true);
  try {
    await analyzeHealth();
  } finally {
    setLoading(false);
  }
};

return (
  <Button onClick={handleRefresh} disabled={loading}>
    {loading ? <RefreshCw className="animate-spin" /> : 'Refresh'}
  </Button>
);
```

### 3. Permission Checks

For manager-only features, always check permissions:

```tsx
useEffect(() => {
  const checkAccess = async () => {
    const hasAccess = await ManagerDashboardService.checkManagerAccess();
    if (!hasAccess) {
      navigate('/unauthorized');
    }
  };
  checkAccess();
}, []);
```

### 4. Real-Time Updates Cleanup

Ensure WebSocket connections are properly cleaned up:

```tsx
useEffect(() => {
  // Connection is automatically managed by the hook
  // Component cleanup is handled internally

  return () => {
    // Cleanup is automatic
  };
}, []);
```

### 5. Data Privacy

Never expose individual user data in the manager dashboard:

```tsx
// ✅ Correct - aggregate metrics only
<div>High Risk Members: {count}</div>

// ❌ Wrong - exposes identities
<div>{users.map(u => u.name)}</div>
```

---

## Testing

### Service Testing

```typescript
import { HealthMonitoringService } from '@/services/healthMonitoringService';

describe('HealthMonitoringService', () => {
  it('should analyze health risks', async () => {
    const data = await HealthMonitoringService.quickHealthCheck();
    expect(data).toHaveProperty('stress_level');
    expect(data).toHaveProperty('cardiovascular_risk_score');
  });
});
```

### Component Testing

```typescript
import { render, screen } from '@testing-library/react';
import { EnhancedHealthDashboard } from '@/components/health/EnhancedHealthDashboard';

describe('EnhancedHealthDashboard', () => {
  it('renders health dashboard', () => {
    render(<EnhancedHealthDashboard />);
    expect(screen.getByText('Your Health Dashboard')).toBeInTheDocument();
  });
});
```

---

## Troubleshooting

### WebSocket Connection Issues

If WebSocket connection fails, the system automatically falls back to polling. Check:

1. Backend WebSocket endpoint is running
2. Firewall/proxy settings allow WebSocket connections
3. Environment variable `VITE_WS_URL` is correctly set

### Manager Access Denied

If manager dashboard shows access denied:

1. Verify user has manager/HR/admin role
2. Check role-based access control in backend
3. Ensure organization/team associations are correct

### Health Data Not Loading

If health data fails to load:

1. Check API endpoint connectivity
2. Verify authentication token is valid
3. Ensure user has completed assessments
4. Check data source integrations (email, wearables)

---

## Additional Resources

- **Backend API Docs**: `http://localhost:8000/docs`
- **Type Definitions**: `frontend/src/types/healthMonitoring.ts`
- **Component Examples**: `frontend/src/components/health/`
- **Service Examples**: `frontend/src/services/*health*.ts`

---

## Support

For issues or questions:
1. Check this guide first
2. Review component documentation
3. Check backend API documentation
4. Contact development team

---

**Last Updated**: 2025-01-14
**Version**: 1.0.0
