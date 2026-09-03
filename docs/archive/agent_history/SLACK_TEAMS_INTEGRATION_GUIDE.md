# 🔔 Slack/Teams Integration - Complete Guide

## ✅ Notification Integration Complete!

PsychSync now sends **real-time notifications** to Slack and Microsoft Teams for important email events.

---

## 🚀 Quick Start

### 1. Set Up Webhook URLs

#### For Slack:

1. Go to https://api.slack.com/apps
2. Create a new app → "From scratch"
3. Enable "Incoming Webhooks"
4. Create a new webhook
5. Copy the webhook URL

#### For Microsoft Teams:

1. Go to your Teams channel
2. Click "..." → "Connectors"
3. Search "Incoming Webhook"
4. Configure and copy the webhook URL

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Teams Webhook
TEAMS_WEBHOOK_URL=https://YOUR-ORG.webhook.office.com/webhookb2/YOUR/WEBHOOK/URL
```

### 3. Test Notification

```bash
curl "http://localhost:8000/api/v1/notification-integration/test?platform=slack" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📡 API Endpoints

### Send Custom Notification

**Endpoint:** `POST /api/v1/notification-integration/send`

**Request:**
```json
{
  "platform": "slack",
  "message": "Important update about your email activity",
  "title": "Email Alert",
  "priority": "high",
  "fields": {
    "Emails Today": "45",
    "Top Category": "Security"
  },
  "channel": "#alerts"
}
```

**Response:**
```json
{
  "success": true,
  "platform": "slack",
  "message": "Notification sent successfully"
}
```

### Send Email Alert

**Endpoint:** `POST /api/v1/notification-integration/email-alert`

**Request:**
```json
{
  "platform": "teams",
  "alert_type": "anomaly",
  "details": {
    "anomaly_type": "unusual_volume",
    "severity": "high",
    "message": "Email volume is 3x higher than normal"
  }
}
```

### Send Daily Summary

**Endpoint:** `POST /api/v1/notification-integration/daily-summary`

**Request:**
```json
{
  "platform": "slack",
  "summary_data": {
    "total_emails": 1250,
    "emails_today": 87,
    "top_category": "security",
    "overall_sentiment": "positive"
  }
}
```

### Send Team Digest

**Endpoint:** `POST /api/v1/notification-integration/team-digest`

**Request:**
```json
{
  "platform": "teams",
  "team_data": {
    "team_name": "Engineering",
    "productivity_score": 85,
    "avg_response_time": 32,
    "team_size": 8,
    "period_days": 30
  }
}
```

---

## 🎨 Notification Formats

### Slack Notification Example

```
┌─────────────────────────────────────────┐
│ 📧 Email Alert                          │
├─────────────────────────────────────────┤
│ Important update about your email       │
│ activity                                 │
│                                          │
│ Emails Today: 45                         │
│ Top Category: Security                   │
│                                          │
│ Timestamp: 2026-01-22 14:30:00           │
│ Alert Type: custom                       │
│                                          │
│ PsychSync Email Monitor                  │
└─────────────────────────────────────────┘
```

### Teams Notification Example

```
┌─────────────────────────────────────────┐
│ 📧 Email Alert                          │
├─────────────────────────────────────────┤
│ Important update about your email       │
│ activity                                 │
│                                          │
│ Emails Today: 45                         │
│ Top Category: Security                   │
│ Timestamp: 2026-01-22 14:30:00           │
│                                          │
│ [View Dashboard]                         │
└─────────────────────────────────────────┘
```

---

## 🎯 Priority Levels

| Priority | Color | Use Case |
|----------|-------|----------|
| **Low** | 🟢 Green | Daily summaries, updates |
| **Medium** | 🟠 Orange | Routine alerts, notifications |
| **High** | 🔴 Red | Anomalies, stress alerts |
| **Critical** | 🔴 Dark Red | Critical incidents, emergencies |

---

## 💡 Integration Examples

### Example 1: Anomaly Detection Alert

```python
# When email anomaly is detected
from app.services.notification_integration_service import notification_integration_service, PlatformType

await notification_integration_service.send_email_alert(
    platform=PlatformType.SLACK,
    alert_type="anomaly",
    details={
        "anomaly_type": "unusual_volume",
        "severity": "high",
        "message": "Email volume is 3x higher than normal",
        "current_volume": 150,
        "baseline_volume": 50
    }
)
```

### Example 2: Daily Summary Cron Job

```python
# Scheduled daily at 9 AM
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def send_daily_summary():
    summary = get_email_summary()  # Your function
    await notification_integration_service.send_daily_summary(
        platform=PlatformType.TEAMS,
        summary_data=summary
    )

scheduler.add_job(send_daily_summary, 'cron', hour=9, minute=0)
scheduler.start()
```

### Example 3: Team Weekly Digest

```python
# Every Monday morning
async def send_team_digest():
    team_analytics = get_team_metrics(team_id=1)
    await notification_integration_service.send_team_digest(
        platform=PlatformType.SLACK,
        team_data={
            "team_name": "Engineering",
            "productivity_score": team_analytics["average_productivity_score"],
            "avg_response_time": team_analytics["average_response_time_minutes"],
            "team_size": team_analytics["team_size"],
            "period_days": 7
        }
    )
```

### Example 4: High Stress Alert

```python
# When high stress detected in email
if stress_analysis["stress_level"] == "very high":
    await notification_integration_service.send_email_alert(
        platform=PlatformType.SLACK,
        alert_type="stress",
        details={
            "stress_level": "very high",
            "indicator_count": 5,
            "user": "john@example.com"
        }
    )
```

---

## 🔄 Integration with Email Monitoring

### Automatic Notifications

Trigger notifications based on email monitoring events:

```python
# In app/api/v1/endpoints/email_monitoring.py

async def check_and_alert_stats(stats: Dict):
    """Send notifications based on stats"""

    # High email volume alert
    if stats['emails_last_hour'] > 100:
        await notification_integration_service.send_notification(
            platform=PlatformType.SLACK,
            message=f"Unusual email volume detected: {stats['emails_last_hour']} emails in last hour",
            title="📧 High Volume Alert",
            priority=NotificationPriority.HIGH,
            fields={
                "Current Volume": str(stats['emails_last_hour']),
                "Baseline": "50-60",
                "Action": "Investigate immediately"
            }
        )

    # Critical sentiment alert
    if stats['negative_sentiment_ratio'] > 0.7:
        await notification_integration_service.send_email_alert(
            platform=PlatformType.TEAMS,
            alert_type="critical",
            details={
                "alert": "High negative sentiment detected",
                "negative_ratio": f"{stats['negative_sentiment_ratio']*100:.1f}%",
                "action_required": "Review team morale"
            }
        )
```

---

## 🔧 Configuration

### Environment Setup

```bash
# .env file
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/xxx
```

### Webhook Validation

Test webhooks are working:

```bash
# Test Slack
curl "http://localhost:8000/api/v1/notification-integration/test?platform=slack" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test Teams
curl "http://localhost:8000/api/v1/notification-integration/test?platform=teams" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 Use Cases

### 1. IT Operations

Get notified about:
- Email service issues
- Unusual patterns
- Security alerts

### 2. Team Management

Receive:
- Daily team summaries
- Performance digests
- Workload alerts

### 3. Executive Updates

Get:
- Organization-wide summaries
- Trend reports
- Critical incidents

### 4. Personal Notifications

Receive:
- Anomaly alerts for your inbox
- Sentiment warnings
- Daily summaries

---

## 📱 Platform-Specific Features

### Slack Features

- ✅ Custom channels (`#alerts`, `#email-updates`)
- ✅ Rich formatting (colors, emojis)
- ✅ Threaded messages
- ✅ Interactive buttons (future)
- ✅ Channel tagging

### Teams Features

- ✅ Action buttons ("View Dashboard")
- ✅ Rich cards (Adaptive Cards)
- ✅ Markdown support
- ✅ Multiple teams
- ✅ Channel targeting

---

## 🚧 Advanced Features

### Scheduled Notifications (Planned)

```python
# Future: Schedule notifications for specific times
await notification_integration_service.send_notification(
    platform=PlatformType.SLACK,
    message="Daily report ready",
    schedule="2026-01-22T09:00:00Z"
)
```

### Notification Templates (Planned)

```python
# Future: Pre-defined templates
await notification_integration_service.send_from_template(
    platform=PlatformType.TEAMS,
    template="daily_report",
    data={"stats": {...}}
)
```

### Filter Rules (Planned)

```python
# Future: Configure when to notify
notification_rules = {
    "only_critical": True,
    "working_hours_only": True,
    "cooldown_minutes": 30
}
```

---

## 🐛 Troubleshooting

### "Webhook URL not configured"

**Solution:**
1. Set environment variables in `.env`
2. Restart backend server
3. Verify URLs are correct

### "Slack API error: 404"

**Solution:**
1. Verify webhook URL is complete
2. Check webhook is active in Slack app settings
3. Regenerate webhook if needed

### "Teams notification not appearing"

**Solution:**
1. Check Teams webhook URL format
2. Verify connector is enabled in Teams
3. Check team/channel permissions

---

## ✨ Summary

**Status:** ✅ **COMPLETE & FUNCTIONAL**

Slack/Teams Integration provides:
- ✅ Real-time notifications to Slack
- ✅ Real-time notifications to Microsoft Teams
- ✅ Priority levels (low, medium, high, critical)
- ✅ Custom messages with fields
- ✅ Email alerts (anomaly, stress, critical)
- ✅ Daily summaries
- ✅ Team digests
- ✅ Webhook configuration
- ✅ Test endpoint for verification
- ✅ Ready for automation/integration

**Ready to notify:** Set up webhooks and start sending notifications!

---

## 📚 Next Steps

1. **Set up webhooks** (Slack and/or Teams)
2. **Configure environment variables**
3. **Test with** `/test` endpoint
4. **Integrate** with email monitoring for automatic alerts
5. **Schedule** regular summaries (daily/weekly)

---

*Generated: 2026-01-22*
*PsychSync Email Monitoring System v1.0*
*Status: ✅ Slack/Teams Integration Operational*
