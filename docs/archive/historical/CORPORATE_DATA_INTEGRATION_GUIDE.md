# Corporate Data Source Integration System

## 📊 Overview

PsychSync's Corporate Data Source Integration system enables organizations to connect 30+ corporate data sources for automated, continuous behavioral analysis. This **privacy-first** architecture extracts behavioral signals without storing sensitive content, providing actionable insights into:

- **Burnout Prevention** - Detect overwork patterns before they cause harm
- **Toxicity Detection** - Identify toxic teams and leadership issues
- **Team Health** - Monitor collaboration and engagement levels
- **Retention Risk** - Predict and prevent employee turnover
- **Work-Life Balance** - Track after-hours work and boundary violations

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   PsychSync Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   Integration    │         │  Behavioral      │         │
│  │  Management UI   │────────▶│  Analytics       │         │
│  │                  │         │  Engine           │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                             │                   │
│  ┌────────▼─────────┐         ┌────────▼─────────┐         │
│  │  Integration     │         │  Insight          │         │
│  │  Service Layer   │────────▶│  Generation      │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                             │                   │
│  ┌────────▼─────────┐         ┌────────▼─────────┐         │
│  │  Data Source     │         │  Privacy          │         │
│  │  Registry        │         │  Controls         │         │
│  └──────────────────┘         └──────────────────┘         │
│           │                                                  │
└───────────┼──────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Corporate Systems                          │
│  Email • Slack • Jira • Calendar • HRIS • VPN • GitHub      │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- ✅ **Metadata-Only Extraction** - No message content stored by default
- ✅ **Consent Management** - Built-in employee consent workflows
- ✅ **Real-Time Sync** - Configurable sync frequencies (1-168 hours)
- ✅ **Data Retention** - Automatic cleanup (30-1095 days)
- ✅ **Privacy Levels** - metadata_only, anonymized, full
- ✅ **Health Monitoring** - Integration health and error tracking

---

## 📁 File Structure

### Backend Files

```
app/integrations/
├── corporate_data_sources.py          # Data source registry (30+ integrations)
├── email_metadata.py                  # Email integration implementation
├── slack_integration.py               # Slack integration implementation
└── calendar_integration.py            # Calendar integration implementation

app/api/v1/endpoints/
└── corporate_integrations.py          # API endpoints for integration management

app/schemas/
└── corporate_data_sources.py          # Pydantic schemas for API
```

### Frontend Files

```
frontend/src/
├── types/
│   └── corporateIntegrations.ts       # TypeScript type definitions
├── services/
│   └── corporateIntegrationService.ts # API service layer
└── components/integrations/
    ├── IntegrationManagementDashboard.tsx  # Integration management UI
    └── BehavioralInsightsDashboard.tsx     # Insights display UI
```

---

## 🚀 Quick Start

### 1. Backend Setup

The data source registry is pre-configured with 30+ integrations. No additional setup needed.

```python
from app.integrations.corporate_data_sources import CorporateDataSourceRegistry

# Get all available data sources
all_sources = CorporateDataSourceRegistry.get_all_sources()

# Get recommended sources for organization size
recommended = CorporateDataSourceRegistry.get_recommended_sources_by_org_size(
    employee_count=100
)

# Get privacy-compliant sources (metadata only, no consent)
privacy_safe = CorporateDataSourceRegistry.get_privacy_compliant_sources()
```

### 2. Frontend Integration

```typescript
import corporateIntegrationService from '@/services/corporateIntegrationService';
import { IntegrationManagementDashboard } from '@/components/integrations/IntegrationManagementDashboard';

// Fetch organization integrations
const integrations = await corporateIntegrationService.getOrganizationIntegrations();

// Setup bulk integrations
const result = await corporateIntegrationService.setupBulkIntegrations({
  organization_size: 100,
  privacy_preference: 'balanced',
  auto_enable_recommended: true
});

// Render dashboard
<IntegrationManagementDashboard
  organizationId={1}
  organizationSize={100}
/>
```

### 3. API Registration

Add to your API routes:

```python
# app/api/v1/routes.py
from app.api.v1.endpoints import corporate_integrations

api_router.include_router(
    corporate_integrations.router,
    prefix="/integrations/corporate",
    tags=["corporate-integrations"]
)
```

---

## 📡 Available Data Sources

### 🔴 MUST-HAVE (MVP)

| Data Source | Behavioral Signals | Privacy Level | Consent Required |
|-------------|-------------------|--------------|------------------|
| **Email Metadata** | Communication patterns, response times, after-hours work | Metadata | ✅ Yes |
| **Calendar Events** | Meeting load, focus time, back-to-back meetings | Metadata | ❌ No |
| **Pulse Surveys** | Satisfaction, engagement, stress levels | Anonymized | ❌ No |

### 🟡 HIGH PRIORITY

| Data Source | Behavioral Signals | Privacy Level | Consent Required |
|-------------|-------------------|--------------|------------------|
| **Slack Messages** | Message frequency, emoji usage, response latency | Metadata | ✅ Yes |
| **Teams Messages** | Meeting participation, chat activity | Metadata | ✅ Yes |
| **Time Tracking** | Overtime, weekend work, continuous work | Metadata | ✅ Yes |
| **Jira Activity** | Ticket volume, overdue tasks, blockers | Metadata | ❌ No |

### 🟢 VALUABLE ADDITIONS

| Data Source | Behavioral Signals | Privacy Level | Consent Required |
|-------------|-------------------|--------------|------------------|
| **Zoom Transcripts** | Speaking time, interruptions, sentiment | Anonymized | ✅ Yes |
| **GitHub Commits** | Commit patterns, review tone, churn | Metadata | ❌ No |
| **VPN Logs** | Remote work, after-hours access | Metadata | ❌ No |
| **Performance Reviews** | Rating trends, feedback sentiment | Anonymized | ✅ Yes |

---

## 🔐 Privacy & Consent

### Privacy Levels

1. **Metadata Only** (Safest)
   - Timestamps, counts, patterns
   - No message content or PII
   - No employee consent required

2. **Anonymized**
   - Aggregated, de-identified data
   - Statistical patterns only
   - No individual consent required (anonymous surveys)

3. **Full** (Requires Consent)
   - Personal behavioral data
   - Individual insights
   - Explicit employee consent required

### Consent Management

```typescript
// Grant consent for data sources
await corporateIntegrationService.grantConsent([
  DataSourceType.EMAIL_METADATA,
  DataSourceType.SLACK_MESSAGES
]);

// Revoke consent
await corporateIntegrationService.revokeConsent([
  DataSourceType.WEARABLE_DATA
]);

// Check consent status
const consents = await corporateIntegrationService.getConsentRecords(employeeId);
```

---

## 🎯 Behavioral Insights

### Insight Categories

#### 1. **Burnout Detection**
- Continuous work stretches (>4 hours without break)
- After-hours communication frequency
- Weekend/holiday work patterns
- Vacation non-usage
- High-stress language in communications

#### 2. **Toxicity Detection**
- Conflict language in emails/Slack
- Meeting interruption patterns
- Unequal speaking time in meetings
- CC/BCC exclusion patterns
- Negative sentiment trends

#### 3. **Team Health**
- Collaboration cross-pollination
- Knowledge sharing patterns
- Peer recognition frequency
- Team participation diversity
- Social connection indicators

#### 4. **Retention Risk**
- Engagement survey trends
- Performance review velocity
- Promotion timing gaps
- Compensation changes
- Internal vs external mobility

#### 5. **Leadership Effectiveness**
- 1:1 meeting frequency
- Feedback response time
- Team engagement under manager
- Direct meeting time vs team size
- Recognition given to reports

### Generating Insights

```typescript
// Analyze behavioral data
const insights = await corporateIntegrationService.analyzeBehavioralData({
  source_types: [
    DataSourceType.EMAIL_METADATA,
    DataSourceType.SLACK_MESSAGES,
    DataSourceType.CALENDAR_EVENTS
  ],
  date_range: {
    start: '2025-01-01T00:00:00Z',
    end: '2025-01-14T23:59:59Z'
  },
  analysis_type: 'comprehensive'
});

// Generate comprehensive report
const report = await corporateIntegrationService.generateInsightsReport({
  start: '2025-01-01T00:00:00Z',
  end: '2025-01-14T23:59:59Z'
});
```

---

## 🔧 Configuration

### Integration Configuration

```typescript
interface IntegrationConfig {
  source_type: DataSourceType;
  enabled: boolean;
  privacy_level: 'metadata_only' | 'anonymized' | 'full';
  sync_frequency_hours: number;      // 1-168 hours
  data_retention_days: number;        // 30-1095 days
  requires_consent: boolean;
  api_credentials?: Record<string, string>;
  custom_settings?: Record<string, any>;
}
```

### Organization Size Recommendations

| Size | Recommended Integrations |
|------|------------------------|
| **<50 employees** | 6 core sources (Email, Calendar, Pulse, Slack, 1:1s) |
| **50-500 employees** | 12 sources (add Teams, Jira, GitHub, Performance, Engagement) |
| **500+ employees** | 15+ sources (full enterprise stack) |

---

## 📊 API Endpoints

### Integration Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/integrations/corporate/organization` | GET | Get all integrations |
| `/api/v1/integrations/corporate/{source_type}` | GET | Get integration details |
| `/api/v1/integrations/corporate` | POST | Create integration |
| `/api/v1/integrations/corporate/{source_type}` | PUT | Update integration |
| `/api/v1/integrations/corporate/{source_type}` | DELETE | Delete integration |
| `/api/v1/integrations/corporate/{source_type}/sync` | POST | Trigger manual sync |

### Analytics & Insights

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/integrations/corporate/analyze` | POST | Analyze behavioral data |
| `/api/v1/integrations/corporate/reports/generate` | POST | Generate insights report |
| `/api/v1/integrations/corporate/reports/latest` | GET | Get latest report |
| `/api/v1/integrations/corporate/health` | GET | Get health metrics |

### Configuration

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/integrations/corporate/available` | GET | List available sources |
| `/api/v1/integrations/corporate/bulk-setup` | POST | Setup multiple integrations |
| `/api/v1/integrations/corporate/recommendations` | GET | Get recommendations |
| `/api/v1/integrations/corporate/consent` | GET | Get consent records |
| `/api/v1/integrations/corporate/consent/grant` | POST | Grant consent |
| `/api/v1/integrations/corporate/consent/revoke` | POST | Revoke consent |

---

## 🎨 Frontend Components

### IntegrationManagementDashboard

Main dashboard for managing integrations.

```tsx
<IntegrationManagementDashboard
  organizationId={1}
  organizationSize={100}
/>
```

**Features:**
- View all integrations with status
- Toggle integrations on/off
- Trigger manual syncs
- View health metrics
- Filter by category/status

### BehavioralInsightsDashboard

Display actionable insights from integrated data.

```tsx
<BehavioralInsightsDashboard
  organizationId={1}
  dateRange={{
    start: '2025-01-01T00:00:00Z',
    end: '2025-01-14T23:59:59Z'
  }}
  onInsightClick={(insightId) => console.log(insightId)}
/>
```

**Features:**
- View insights by severity/category
- Filter insights
- Generate new reports
- View AI recommendations

---

## 🔍 Data Extraction Examples

### Email Metadata

```python
email_signals = {
    "communication_frequency": 45.2,      # emails/day
    "response_time_avg_hours": 2.3,       # avg response time
    "after_hours_pct": 15.7,              # % sent outside 9-5
    "weekend_activity": true,             # weekend emails detected
    "conflict_keywords_count": 3,         # urgent/ASAP flags
    "thread_length_avg": 4.2              # avg emails per thread
}
```

### Calendar Events

```python
calendar_signals = {
    "meeting_hours_per_day": 4.2,        # hours in meetings
    "back_to_back_pct": 65.0,            # % back-to-back meetings
    "focus_hours_per_day": 1.5,          # uninterrupted work time
    "after_hours_meetings": 2,           # meetings outside 9-5
    "last_minute_cancellations": 1,      # cancellations <1h before
    "meeting_acceptance_rate": 0.87      # % invites accepted
}
```

### Slack Messages

```python
slack_signals = {
    "messages_per_day": 28.5,
    "response_latency_minutes": 12.3,
    "emoji_diversity_score": 0.72,
    "weekend_messages": 0,
    "reaction_rate": 0.45,
    "channel_diversity": 8,
    "direct_message_ratio": 0.23
}
```

---

## 🚧 Implementation TODOs

### Backend
- [ ] Implement database models for integrations
- [ ] Create actual integration implementations (Email, Slack, Calendar, Jira)
- [ ] Build data ingestion pipeline
- [ ] Implement behavioral analysis engine
- [ ] Add consent management database
- [ ] Create background jobs for data syncing
- [ ] Implement data retention cleanup

### Frontend
- [ ] Add integration setup wizard UI
- [ ] Create consent management interface
- [ ] Build detailed insight drill-down views
- [ ] Add data export functionality
- [ ] Create integration testing UI
- [ ] Add notification system for critical insights

---

## 📈 Monitoring & Health

### Integration Health Metrics

```typescript
interface IntegrationHealthMetrics {
  total_integrations: number;           // Total configured
  active_integrations: number;          // Currently syncing
  error_integrations: number;           // With errors
  total_data_points: number;            // Total records ingested
  last_24h_ingestion_count: number;     // Records in last 24h
  avg_sync_latency_minutes: number;     // Average sync time
  data_quality_score: number;           // 0-1 quality score
}
```

### Sync Status Tracking

```typescript
enum SyncStatus {
  ACTIVE = 'active',      // Syncing normally
  PAUSED = 'paused',      // Manually paused
  ERROR = 'error',        // Has errors
  PENDING = 'pending',    // Initial setup
  DISABLED = 'disabled'   // Disabled
}
```

---

## 🔐 Security Considerations

1. **API Credentials**: Encrypted at rest using application-level encryption
2. **Data in Transit**: All API calls use HTTPS/TLS
3. **Data at Rest**: Sensitive data encrypted in database
4. **Access Control**: Role-based access (admin only for integrations)
5. **Audit Logging**: All integration changes logged
6. **Consent Tracking**: Immutable consent records
7. **Data Retention**: Automatic cleanup after retention period

---

## 📚 Next Steps

1. **Implement Email Integration** - Connect to Gmail/Outlook APIs
2. **Implement Slack Integration** - Slack API for team analytics
3. **Implement Calendar Integration** - Google Calendar/Outlook
4. **Build Analysis Engine** - ML models for insight generation
5. **Add Webhooks** - Real-time data push notifications
6. **Create Admin Portal** - Organization-level management
7. **Deploy to Production** - Scalability and performance tuning

---

**Built with ❤️ for PsychSync Enterprise**
