# Corporate Integrations API Examples

Complete API usage examples with curl commands for testing.

---

## 🔑 Authentication

All API calls require a JWT token. Get your token from login:

```bash
# Login to get token
curl -X POST http://localhost:8000/api/v1/simple-login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "your_password"
  }'

# Save the access_token from response
export TOKEN="your_jwt_token_here"
```

---

## 📋 Get Available Data Sources

List all 30+ available integrations:

```bash
curl http://localhost:8000/api/v1/integrations/corporate/available \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
[
  {
    "type": "email_metadata",
    "name": "Email Metadata",
    "category": "communication",
    "priority": "must_have",
    "requires_consent": true,
    "behavioral_signals": [
      "Communication frequency and patterns",
      "Response time trends",
      "After-hours work indicators"
    ]
  }
]
```

---

## 🏢 Get Organization Integrations

View all configured integrations for your organization:

```bash
curl http://localhost:8000/api/v1/integrations/corporate/organization \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "organization_id": 1,
  "integrations": [
    {
      "config": {
        "source_type": "email_metadata",
        "enabled": true,
        "privacy_level": "metadata_only",
        "sync_frequency_hours": 24
      },
      "status": {
        "source_type": "email_metadata",
        "status": "active",
        "last_sync": "2025-01-14T10:30:00Z",
        "records_processed": 1523,
        "health_score": 0.95
      }
    }
  ],
  "summary": {
    "total_integrations": 3,
    "active_integrations": 2,
    "total_data_points": 5234
  }
}
```

---

## ➕ Create New Integration

Create a new data source integration:

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "email_metadata",
    "privacy_level": "metadata_only",
    "sync_frequency_hours": 24,
    "data_retention_days": 90,
    "api_credentials": {
      "access_token": "your_oauth_token"
    }
  }'
```

**Parameters:**
- `source_type`: One of 30+ types (email_metadata, calendar_events, slack_messages, etc.)
- `privacy_level`: "metadata_only" | "anonymized" | "full"
- `sync_frequency_hours`: 1-168 (how often to sync)
- `data_retention_days`: 30-1095 (how long to keep data)

---

## ✏️ Update Integration

Update an existing integration:

```bash
curl -X PUT http://localhost:8000/api/v1/integrations/corporate/email_metadata \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "sync_frequency_hours": 12,
    "data_retention_days": 180
  }'
```

---

## 🔄 Trigger Manual Sync

Manually trigger a data sync for an integration:

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/email_metadata/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "force_full_sync": false
  }'
```

**Response:**
```json
{
  "message": "Sync initiated for email_metadata",
  "sync_id": "sync_email_metadata_1705251600"
}
```

**With Date Range:**
```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/email_metadata/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "force_full_sync": true,
    "date_range": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2025-01-14T23:59:59Z"
    }
  }'
```

---

## 📊 Analyze Behavioral Data

Generate behavioral insights from integrated data:

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_types": ["email_metadata", "calendar_events", "slack_messages"],
    "date_range": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2025-01-14T23:59:59Z"
    },
    "analysis_type": "comprehensive"
  }'
```

**Response:**
```json
[
  {
    "category": "burnout",
    "severity": "high",
    "title": "High Burnout Risk Detected",
    "description": "Analysis reveals multiple burnout risk factors...",
    "affected_employees": [1, 2, 3, 4, 5],
    "confidence": 0.85,
    "indicators": [
      "Meeting load exceeds 80% of workday",
      "Work-life imbalance score elevated (0.75)"
    ],
    "recommendations": [
      "Block 2-hour focus time blocks daily",
      "Set communication hours boundaries"
    ],
    "data_sources": ["email_metadata", "calendar_events"]
  }
]
```

**Analysis Types:**
- `comprehensive` - All categories
- `toxicity` - Toxic behavior detection
- `burnout` - Burnout risk assessment
- `team_health` - Team dynamics
- `engagement` - Employee engagement

---

## 📈 Generate Insights Report

Generate a comprehensive insights report:

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_range": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2025-01-14T23:59:59Z"
    }
  }'
```

**Response:**
```json
{
  "report_id": "report_1705251600",
  "generated_at": "2025-01-14T15:00:00Z",
  "insights": [...],
  "health_metrics": {
    "total_integrations": 3,
    "active_integrations": 2,
    "data_quality_score": 0.92
  },
  "summary": {
    "total_insights": 15,
    "critical_insights": 2,
    "high_insights": 5
  },
  "recommendations": [
    "Address burnout risk in engineering team",
    "Investigate communication patterns in marketing"
  ]
}
```

---

## 📊 Get Health Metrics

Check the health of all integrations:

```bash
curl http://localhost:8000/api/v1/integrations/corporate/health \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "total_integrations": 5,
  "active_integrations": 4,
  "error_integrations": 0,
  "total_data_points": 15234,
  "last_24h_ingestion_count": 1234,
  "avg_sync_latency_minutes": 8.5,
  "data_quality_score": 0.94
}
```

---

## 🎯 Get Recommendations

Get recommended integrations based on organization size:

```bash
curl "http://localhost:8000/api/v1/integrations/corporate/recommendations?organization_size=100" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "recommended": [
    "email_metadata",
    "calendar_events",
    "slack_messages",
    "pulse_surveys"
  ],
  "reasons": {
    "email_metadata": "Essential for communication pattern analysis",
    "calendar_events": "Tracks meeting load and focus time",
    "slack_messages": "Real-time team dynamics monitoring"
  }
}
```

---

## 🚀 Bulk Setup Integrations

Setup multiple integrations at once:

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/bulk-setup \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_size": 100,
    "privacy_preference": "balanced",
    "auto_enable_recommended": true
  }'
```

**Organization Sizes:**
- `<50`: 6 core integrations
- `50-500`: 12 integrations
- `500+`: 15+ integrations

**Privacy Preferences:**
- `minimal`: Privacy-compliant only
- `balanced`: Mix of metadata and anonymized
- `comprehensive`: All available sources

---

## 👤 Consent Management

### Grant Consent

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/consent/grant \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_types": ["email_metadata", "slack_messages"]
  }'
```

### Revoke Consent

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/consent/revoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_types": ["wearable_data"]
  }'
```

### Check Consent Status

```bash
curl "http://localhost:8000/api/v1/integrations/corporate/consent?employee_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🗑️ Delete Integration

Remove an integration and all its data:

```bash
curl -X DELETE http://localhost:8000/api/v1/integrations/corporate/email_metadata \
  -H "Authorization: Bearer $TOKEN"
```

**Warning:** This will delete all metadata from this integration.

---

## 📦 Export Data

Export integrated data in various formats:

### CSV Export

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_types": ["email_metadata"],
    "date_range": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2025-01-14T23:59:59Z"
    },
    "format": "csv"
  }' \
  --output exported_data.csv
```

### JSON Export

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_types": ["email_metadata", "calendar_events"],
    "format": "json"
  }' \
  --output exported_data.json
```

---

## 🧪 Test Connection

Test if API credentials work before creating integration:

```bash
curl -X POST http://localhost:8000/api/v1/integrations/corporate/email_metadata/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "api_credentials": {
      "access_token": "your_test_token"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Connection successful"
}
```

---

## 📊 Get Ingestion Statistics

View data ingestion statistics:

```bash
curl "http://localhost:8000/api/v1/integrations/corporate/stats/ingestion?days=30" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "total_records": 15234,
  "by_source": {
    "email_metadata": 5234,
    "calendar_events": 6000,
    "slack_messages": 4000
  },
  "by_day": [
    {"date": "2025-01-14", "count": 234},
    {"date": "2025-01-13", "count": 189}
  ],
  "error_rate": 0.02
}
```

---

## 🔍 Search and Filter

### Get Latest Report

```bash
curl http://localhost:8000/api/v1/integrations/corporate/reports/latest \
  -H "Authorization: Bearer $TOKEN"
```

### Get Specific Integration

```bash
curl http://localhost:8000/api/v1/integrations/corporate/email_metadata \
  -H "Authorization: Bearer $TOKEN"
```

---

## ⚡ Performance Tips

1. **Use date ranges** - Limit analysis to specific time periods
2. **Filter data sources** - Only analyze relevant sources
3. **Cache reports** - Store generated reports locally
4. **Async operations** - Use background workers for large datasets

---

## 🚨 Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

**Common Errors:**
- `401 Unauthorized` - Invalid or expired token
- `404 Not Found` - Integration doesn't exist
- `400 Bad Request` - Invalid parameters
- `500 Server Error` - Contact support

---

## 📚 Complete API Documentation

Interactive API docs available at:
```
http://localhost:8000/docs
http://localhost:8000/redoc
```

---

`★ Insight ─────────────────────────────────────`
**RESTful API Design**: All endpoints follow **REST principles** with proper HTTP methods (GET, POST, PUT, DELETE), resource-based URLs (`/integrations/corporate/{type}`), and standard status codes. This makes the API **predictable and easy to consume** from any programming language.

**Pagination Support**: Large datasets use **cursor-based pagination** for efficient traversal. Example: `?page=2&pageSize=50` returns the second page with 50 items per request.

**Rate Limiting**: API implements **token-bucket rate limiting** to prevent abuse while allowing legitimate burst traffic. This protects system resources while ensuring responsiveness.
`─────────────────────────────────────────────────`

---

**Ready to integrate! 🚀**
