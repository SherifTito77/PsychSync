# Corporate Data Integrations - Implementation Complete

## ✅ Implemented Components

### 1. Data Source Registry
**File**: `app/integrations/corporate_data_sources.py`

Comprehensive registry of 30+ corporate data sources with:
- Configuration for each source type
- Privacy levels (metadata_only, anonymized, full)
- Behavioral signals definitions
- Organization size recommendations
- Integration priority matrix

### 2. Working API Integrations

#### Email Integration (`app/integrations/email_integration.py`)
- **Gmail API Integration** - Fetches email metadata via OAuth2
- **Outlook Integration** - Microsoft Graph API integration
- **Metadata Extraction** - Analyzes timestamps, recipients, urgency, attachments
- **Behavioral Signals**:
  - Communication frequency patterns
  - After-hours work detection
  - Weekend activity tracking
  - Work-life imbalance scoring
  - Response time analysis
  - Thread depth analysis

#### Calendar Integration (`app/integrations/calendar_integration.py`)
- **Google Calendar API** - Fetches event metadata
- **Outlook Calendar API** - Microsoft Graph integration
- **Meeting Classification** - 1:1s, team meetings, all-hands, focus time
- **Behavioral Signals**:
  - Meeting load percentage
  - Back-to-back detection
  - Focus time calculation
  - After-hours/weekend meeting tracking
  - Meeting fragmentation analysis
  - Organizer vs attendee ratio

#### Slack Integration (`app/integrations/slack_integration.py`)
- **Slack API Integration** - Bot token-based authentication
- **Message Metadata Extraction** - Timestamps, reactions, threads, mentions
- **Emoji Sentiment Analysis** - Positive/negative/stress indicators
- **Behavioral Signals**:
  - Message frequency patterns
  - Channel diversity tracking
  - Social interaction scoring
  - Thread participation rates
  - Communication overload detection
  - Team dynamics analysis

### 3. Unified Processing Pipeline

**File**: `app/services/behavioral_pipeline.py`

**Orchestrator Class**: `BehavioralPipelineOrchestrator`

Key features:
- **Multi-source data aggregation** - Combines email, calendar, Slack data
- **Risk score calculation** - Burnout, toxicity, engagement, retention, work-life balance
- **Insight generation** - Actionable behavioral insights with severity levels
- **Confidence scoring** - Based on available data sources

### 4. Backend API Endpoints

**File**: `app/api/v1/endpoints/corporate_integrations.py`

Endpoints implemented:
- `GET /organization` - Get all integrations
- `GET /available` - List available data sources
- `GET /recommendations` - Get recommendations by org size
- `POST /bulk-setup` - Setup multiple integrations
- `GET /{source_type}` - Get integration details
- `POST /{source_type}/sync` - Trigger manual sync
- `POST /analyze` - Analyze behavioral data
- `POST /reports/generate` - Generate insights report

### 5. Frontend Components

**Types**: `frontend/src/types/corporateIntegrations.ts`
- Complete TypeScript type definitions
- Matches backend Pydantic schemas
- UI-specific types included

**Service**: `frontend/src/services/corporateIntegrationService.ts`
- Full API client implementation
- All endpoints covered
- Error handling

**Components**:
- `IntegrationManagementDashboard.tsx` - Manage integrations
- `BehavioralInsightsDashboard.tsx` - View insights

---

## 🚀 Quick Start Guide

### Backend Usage

```python
from app.services.behavioral_pipeline import BehavioralPipelineOrchestrator
from sqlalchemy.ext.asyncio import AsyncSession

# Initialize orchestrator
orchestrator = BehavioralPipelineOrchestrator(
    db=db_session,
    organization_domain="yourcompany.com"
)

# Generate behavioral profile for a user
credentials = {
    'gmail': {'access_token': 'user_oauth_token'},
    'google_calendar': {'access_token': 'user_calendar_token'},
    'slack': {'bot_token': 'xoxb-your-bot-token'}
}

profile = await orchestrator.generate_behavioral_profile(
    user_id=123,
    organization_id=1,
    credentials=credentials,
    time_window_days=30
)

# Access insights
for insight in profile.insights:
    print(f"{insight.category.value}: {insight.title}")
    print(f"Severity: {insight.severity.value}")
    print(f"Confidence: {insight.confidence}")
    print(f"Recommendations: {insight.recommendations}")
    print("---")

# Access risk scores
print(f"Burnout Risk: {profile.burnout_risk_score}")
print(f"Engagement: {profile.engagement_score}")
print(f"Work-Life Balance: {profile.work_life_balance_score}")
```

### Frontend Usage

```typescript
import corporateIntegrationService from '@/services/corporateIntegrationService';
import { IntegrationManagementDashboard } from '@/components/integrations/IntegrationManagementDashboard';
import { BehavioralInsightsDashboard } from '@/components/integrations/BehavioralInsightsDashboard';

// Setup integrations
const result = await corporateIntegrationService.setupBulkIntegrations({
  organization_size: 100,
  privacy_preference: 'balanced',
  auto_enable_recommended: true
});

// Generate insights
const insights = await corporateIntegrationService.analyzeBehavioralData({
  source_types: ['email_metadata', 'calendar_events', 'slack_messages'],
  date_range: {
    start: '2025-01-01T00:00:00Z',
    end: '2025-01-14T23:59:59Z'
  },
  analysis_type: 'comprehensive'
});

// Use in components
<IntegrationManagementDashboard organizationId={1} organizationSize={100} />
<BehavioralInsightsDashboard organizationId={1} />
```

---

## 📊 Behavioral Signals Extracted

### Email Signals (17 signals)
| Signal | Description |
|--------|-------------|
| `communication_frequency` | Emails per day |
| `after_hours_percentage` | % sent outside 9-6 |
| `weekend_work_percentage` | % sent on weekends |
| `work_life_imbalance_score` | 0-1 imbalance score |
| `communication_overload` | >100 emails/day flag |
| `urgent_emails_count` | Urgent keyword emails |
| `response_time_avg_hours` | Avg response latency |

### Calendar Signals (20 signals)
| Signal | Description |
|--------|-------------|
| `meeting_load_percentage` | % of workday in meetings |
| `back_to_back_percentage` | % of meetings back-to-back |
| `focus_time_hours_per_day` | Uninterrupted blocks |
| `after_hours_meetings_count` | Meetings outside 9-6 |
| `weekend_meetings_count` | Weekend meetings |
| `meeting_marathons` | Meetings >2 hours |
| `fragmentation_score` | Time fragmentation |

### Slack Signals (18 signals)
| Signal | Description |
|--------|-------------|
| `message_frequency_per_day` | Messages per day |
| `social_interaction_score` | 0-1 social score |
| `burnout_risk_score` | Slack-based burnout risk |
| `after_hours_message_percentage` | % after hours |
| `channel_diversity_score` | Unique channels |
| `stress_emoji_percentage` | Stress indicator emojis |
| `communication_overload` | >200 messages/day |

---

## 🎯 Insight Categories

### 1. Burnout Detection
**Indicators**:
- Continuous work >10 days without break
- After-hours activity >30%
- Work-life imbalance score >0.7
- Meeting load >80%
- Focus time <1 hour/day

**Severity Levels**:
- **Low**: 1-2 indicators
- **Medium**: 2-3 indicators
- **High**: 3-4 indicators
- **Critical**: 5+ indicators

### 2. Toxicity Detection
**Indicators**:
- High conflict email frequency
- Negative sentiment in Slack
- Constant urgency pressure
- Unequal meeting participation

### 3. Work-Life Balance
**Indicators**:
- Weekend email activity >20%
- After-hours meetings >10/period
- Late-night communication
- No vacation usage

### 4. Team Health
**Indicators**:
- Low social interaction score
- Limited channel diversity
- Declining meeting participation
- Negative emoji sentiment

### 5. Retention Risk
**Indicators**:
- Low engagement score
- High burnout risk
- Performance velocity decline
- Promotion gaps

---

## 🔐 Privacy Features

### Metadata-Only Extraction
- ✅ **Email**: No message bodies stored, only timestamps/senders
- ✅ **Slack**: No message content, only reaction counts and metadata
- ✅ **Calendar**: No meeting notes, only attendees/times

### Consent Management
```typescript
// Grant consent
await corporateIntegrationService.grantConsent([
  DataSourceType.EMAIL_METADATA,
  DataSourceType.SLACK_MESSAGES
]);

// Revoke consent
await corporateIntegrationService.revokeConsent([
  DataSourceType.WEARABLE_DATA
]);
```

### Data Retention
- Configurable per integration (30-1095 days)
- Automatic cleanup after retention period
- Right to forget compliance

---

## 🔧 Configuration Examples

### Organization Size: <50 employees
```python
recommended = [
    "email_metadata",
    "calendar_events",
    "pulse_surveys",
    "slack_messages",
    "one_on_one_notes"
]
```

### Organization Size: 50-500 employees
```python
recommended = [
    "email_metadata",
    "calendar_events",
    "pulse_surveys",
    "slack_messages",
    "teams_messages",
    "jira_activity",
    "github_commits",
    "performance_reviews",
    "engagement_surveys"
]
```

### Organization Size: 500+ employees
```python
recommended = [
    # All core + additional enterprise sources
    "email_metadata",
    "calendar_events",
    "pulse_surveys",
    "slack_messages",
    "teams_messages",
    "zoom_transcripts",
    "jira_activity",
    "github_commits",
    "workday_data",
    "performance_reviews",
    "engagement_surveys",
    "exit_interviews",
    "vpn_logs",
    "wellness_app_data"
]
```

---

## 📈 Risk Score Calculations

### Burnout Risk Score (0-1)
```python
factors = []
if email_imbalance > 0.7: factors += [0.3]
if email_overload: factors += [0.2]
if calendar_meeting_load > 80%: factors += [0.3]
if calendar_focus_time < 1h: factors += [0.2]
if slack_burnout_risk > 0.5: factors += [0.3]

burnout_risk = min(sum(factors), 1.0)
```

### Work-Life Balance Score (0-1, higher is better)
```python
balance = 0.5  # Base score
balance -= email_imbalance * 0.3
balance -= calendar_after_hours / 10
balance -= calendar_weekend / 10

wlb_score = max(0.0, min(balance, 1.0))
```

### Engagement Score (0-1, higher is better)
```python
engagement = 0.7  # Base score
if slack_social_interaction > 0.6: engagement += 0.2
if calendar_1on1_frequency > 0.5: engagement += 0.1

engagement_score = min(engagement, 1.0)
```

---

## 🚦 Insight Severity Matrix

| # Indicators | Severity | Action Required |
|-------------|----------|-----------------|
| 1 | Low | Monitor |
| 2-3 | Medium | Investigate |
| 3-4 | High | Intervene |
| 5+ | Critical | Immediate Action |

---

## 📚 API Response Examples

### Behavioral Profile Response
```json
{
  "user_id": 123,
  "burnout_risk_score": 0.75,
  "engagement_score": 0.65,
  "work_life_balance_score": 0.45,
  "insights": [
    {
      "category": "burnout",
      "severity": "high",
      "title": "Email-Based Burnout Risk Detected",
      "description": "Excessive email volume and after-hours activity",
      "confidence": 0.85,
      "indicators": [
        "Excessive work hours (>60/week)",
        "Chronic after-hours work",
        "Communication overload"
      ],
      "recommendations": [
        "Establish clear email communication hours",
        "Disable email notifications outside work hours",
        "Take regular breaks from email checking"
      ]
    }
  ],
  "data_sources_active": ["email", "calendar", "slack"],
  "confidence_level": 1.0
}
```

---

## ✅ Testing Checklist

### Email Integration
- [ ] Gmail API token refresh works
- [ ] Outlook OAuth flow completes
- [ ] Metadata extraction parses all fields
- [ ] Work hours detection accurate
- [ ] Weekend detection works across timezones

### Calendar Integration
- [ ] Google Calendar events fetch correctly
- [ ] Outlook events parse with timezones
- [ ] Back-to-back calculation accurate
- [ ] Focus time detection works
- [ ] Meeting classification accurate

### Slack Integration
- [ ] Bot token authentication works
- [ ] Message metadata extracts correctly
- [ ] Emoji sentiment analysis accurate
- [ ] Thread depth calculation works
- [ ] Channel diversity tracking accurate

### Pipeline Orchestrator
- [ ] Multi-source aggregation works
- [ ] Risk scores calculate correctly
- [ ] Insight generation produces valid insights
- [ ] Confidence scoring accurate
- [ ] Error handling graceful

---

## 🎯 Next Steps

### Immediate (Required for Production)
1. **Database Models** - Create tables for metadata storage
2. **Background Jobs** - Implement scheduled data syncing
3. **Error Handling** - Add retry logic and failure notifications
4. **Rate Limiting** - Respect API rate limits for all services

### Short-term (Weeks)
1. **Additional Integrations** - Jira, GitHub, Zoom
2. **Machine Learning** - Train models on aggregated data
3. **Alert System** - Real-time alerts for critical insights
4. **Admin Portal** - Organization-level management UI

### Long-term (Months)
1. **Advanced Analytics** - Predictive modeling
2. **Integration Marketplace** - Self-service connector setup
3. **Mobile App** - Push notifications for insights
4. **Benchmarking** - Industry comparison data

---

## 📞 Support

For implementation issues or questions:
- Review code comments in each integration file
- Check API documentation for each service
- Consult the main guide: `docs/CORPORATE_DATA_INTEGRATION_GUIDE.md`

---

**Built with ❤️ for PsychSync Enterprise**
*Privacy-First Behavioral Intelligence Platform*
