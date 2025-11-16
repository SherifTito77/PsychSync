# PsychSync Email-Based Behavioral Analysis

A powerful privacy-first system that analyzes workplace email communication to provide insights into team dynamics, culture health, and personalized coaching recommendations.

## 🎯 Key Features

- **🔗 Email Integration**: OAuth support for Gmail, Outlook, IMAP
- **🧠 AI-Powered Analysis**: NLP sentiment, emotion, and behavioral pattern analysis
- **📊 Culture Health**: Real-time monitoring of team psychological safety and collaboration
- **🤖 Personalized Coaching**: AI-generated recommendations based on communication patterns
- **🔒 Privacy-First**: No email content storage, only metadata analysis
- **⚡ Real-Time Insights**: Continuous pattern monitoring and alerting

## 🏗️ Architecture Overview

```
Email Providers → Metadata Extraction → NLP Analysis → Pattern Aggregation → Insights & Coaching
     ↓                    ↓                    ↓              ↓              ↓
   Gmail/Outlook         EmailMetadata    CommunicationAnalysis  CommunicationPatterns  CoachingRecs
```

## 📋 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL database
- Redis cache
- Gmail/Microsoft OAuth applications

### Installation

1. **Clone and Setup**
   ```bash
   cd psychsync
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Database Setup**
   ```bash
   # Create database tables
   alembic upgrade head
   ```

5. **Start Services**
   ```bash
   # Start all services with Docker Compose
   docker-compose up --build

   # Or start manually:
   # PostgreSQL and Redis
   # Backend API: uvicorn app.main:app --reload
   # Celery Worker: celery -A app.core.celery worker --loglevel=info
   # Celery Beat: celery -A app.core.celery beat --loglevel=info
   ```

### OAuth Setup

**Google Gmail API:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:8000/api/v1/email-connections/callback`

**Microsoft Outlook:**
1. Go to [Azure Portal](https://portal.azure.com/)
2. Create App Registration
3. Add Microsoft Graph permissions (Mail.Read, User.Read)
4. Create client secret
5. Add redirect URI: `http://localhost:8000/api/v1/email-connections/callback`

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://psychsync_user:password@localhost:5432/psychsync_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Email Integration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret

# Email Encryption (generate with Python)
EMAIL_ENCRYPTION_KEY=your_fernet_key_here

# Feature Flags
ENABLE_EMAIL_ANALYSIS=true
ENABLE_CULTURE_METRICS=true
ENABLE_AI_COACHING=true
```

### Encryption Key Generation

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

## 📊 Usage Examples

### 1. Connect Email Account

```python
import requests

# Initiate OAuth flow
response = requests.post(
    "http://localhost:8000/api/v1/email-connections/initiate",
    json={
        "provider": "gmail",
        "redirect_uri": "http://localhost:8000/email-callback"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

# User authorizes and gets redirected with code
callback_response = requests.get(
    f"http://localhost:8000/api/v1/email-connections/callback?code={code}&state={state}&provider=gmail"
)
```

### 2. Get Communication Insights

```python
# Get personal insights
insights = requests.get(
    "http://localhost:8000/api/v1/communication-insights/me",
    params={"period_days": 30},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
).json()

print(f"Sentiment Score: {insights['metrics']['sentiment']['average_score']}")
print(f"Collaboration Score: {insights['metrics']['behavioral']['collaboration_score']}")
```

### 3. Get Coaching Recommendations

```python
# Get personalized recommendations
recommendations = requests.get(
    "http://localhost:8000/api/v1/coaching/recommendations",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
).json()

for rec in recommendations['recommendations']:
    print(f"Title: {rec['title']}")
    print(f"Priority: {rec['priority']}")
    print(f"Steps: {rec['actionable_steps']}")
```

### 4. Analyze Team Culture

```python
# Get team culture health
culture = requests.get(
    "http://localhost:8000/api/v1/culture-health/team/{team_id}",
    params={"period_days": 30},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
).json()

print(f"Psychological Safety: {culture['metrics']['psychological_safety']}")
print(f"Overall Health Score: {culture['health_score']}")
```

## 🗄️ Database Schema

### Core Tables

**EmailMetadata** - Privacy-focused email information
- message_id, sender, recipients, timestamps
- Subject hash (for analysis, no content storage)
- Folder labels, thread information

**CommunicationAnalysis** - NLP analysis results
- Sentiment scores, emotion analysis, tone detection
- Behavioral indicators, conflict probability
- Stress and urgency assessment

**CommunicationPatterns** - Aggregated metrics
- Response time distributions, collaboration scores
- Email volume patterns, leadership indicators
- Burnout and disengagement risk factors

**CultureMetrics** - Team/organization health
- Psychological safety, inclusivity scores
- Conflict levels, morale measurements
- Trend analysis and benchmarks

**CoachingRecommendation** - AI-generated insights
- Personalized development recommendations
- Evidence-based suggestions
- Progress tracking and completion

## 🔒 Privacy & Security

### Data Protection
- **No Content Storage**: Only email metadata is stored, never content
- **PII Redaction**: Automatic detection and redaction of personal information
- **Encryption**: Tokens and sensitive data encrypted at rest
- **User Control**: Users can delete data and connections anytime

### GDPR Compliance
- **Right to be Forgotten**: Complete data deletion capability
- **Data Portability**: Export user data in machine-readable format
- **Consent Management**: Explicit consent for email analysis
- **Purpose Limitation**: Data used only for stated purposes

## 📈 Key Metrics

### Individual Metrics
- **Sentiment Trends**: Track emotional patterns over time
- **Response Times**: Communication efficiency and responsiveness
- **Stress Indicators**: Linguistic patterns indicating burnout risk
- **Collaboration Score**: Network analysis of communication patterns
- **Work-Life Balance**: After-hours communication patterns

### Team Metrics
- **Psychological Safety**: Team comfort level with risk-taking
- **Inclusivity**: Balanced participation across team members
- **Conflict Resolution**: Early detection and intervention
- **Communication Health**: Overall team communication effectiveness

### Organization Metrics
- **Culture Health**: Organization-wide psychological safety trends
- **Leadership Effectiveness**: Management communication patterns
- **Cross-Team Collaboration**: Interdepartmental communication analysis
- **Risk Hotspots**: Early warning for organizational issues

## 🤖 AI Features

### Sentiment Analysis
- **Multi-Model Approach**: Combines VADER, transformer-based models
- **Context-Aware**: Understands workplace communication nuances
- **Trend Analysis**: Identifies patterns over time

### Behavioral Detection
- **Stress Indicators**: Linguistic markers of workplace stress
- **Burnout Risk**: Combination of timing, volume, and sentiment factors
- **Conflict Probability**: Early detection of potential escalations

### Coaching Engine
- **Personalized**: Tailored to individual communication patterns
- **Evidence-Based**: Recommendations backed by data analysis
- **Actionable**: Specific, measurable steps for improvement

## 🔄 Celery Tasks

### Automated Processing
- **Email Sync**: `sync_user_emails_task` - Fetch new emails
- **Pattern Analysis**: `aggregate_patterns_task` - Generate insights
- **Coaching**: `generate_coaching_recommendations_task` - Create recommendations
- **Culture Analysis**: `generate_culture_metrics_task` - Team/organization metrics

### Scheduling
```python
# celeryconfig.py
CELERY_BEAT_SCHEDULE = {
    'sync-emails-every-15-min': {
        'task': 'sync_user_emails_task',
        'schedule': crontab(minute='*/15'),
    },
    'aggregate-patterns-daily': {
        'task': 'aggregate_patterns_task',
        'schedule': crontab(hour=2, minute=0),
    },
    'generate-coaching-weekly': {
        'task': 'generate_coaching_recommendations_task',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),
    },
}
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest tests/

# Run email analysis tests
pytest tests/test_email_analysis.py

# Run with coverage
pytest --cov=app tests/
```

### Integration Tests
```bash
# Test email connector
pytest tests/test_email_connector.py

# Test NLP analysis
pytest tests/test_nlp_analysis.py

# Test culture metrics
pytest tests/test_culture_analyzer.py
```

## 📱 Frontend Integration

### React Service Example
```typescript
import EmailAnalysisService from './services/emailAnalysisService';

// Connect email account
await emailAnalysisService.initiateConnection('gmail');

// Get insights
const insights = await emailAnalysisService.getMyInsights(30);

// Get recommendations
const recommendations = await emailAnalysisService.getCoachingRecommendations();
```

### Available Endpoints
- `POST /api/v1/email-connections/initiate` - Start OAuth flow
- `GET /api/v1/communication-insights/me` - Personal insights
- `GET /api/v1/coaching/recommendations` - AI recommendations
- `GET /api/v1/culture-health/team/{id}` - Team culture metrics
- `GET /api/v1/alerts/active` - Active communication alerts

## 🚀 Production Deployment

### Environment Setup
```bash
# Production environment
export ENVIRONMENT=production
export DEBUG=false
export LOG_LEVEL=WARNING

# Scaling
export WORKERS=4
export REDIS_POOL_SIZE=20
export DB_POOL_SIZE=20
```

### Docker Production
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml scale celery-worker=4
```

### Monitoring
- **Grafana**: Culture health dashboards
- **Prometheus**: System and application metrics
- **Sentry**: Error tracking and performance
- **Health Checks**: `/api/v1/health` endpoint

## 🔍 Troubleshooting

### Common Issues

**OAuth Callbacks**
```bash
# Check callback URL configuration
# Verify client secret matches
# Check redirect URI in OAuth app settings
```

**NLP Model Loading**
```bash
# Check GPU availability
nvidia-smi

# Reduce model size if memory issues
pip install transformers==4.30.0
```

**Database Performance**
```sql
-- Check analysis table indexes
SELECT * FROM pg_indexes WHERE tablename = 'communication_analysis';

-- Add composite indexes if needed
CREATE INDEX idx_analysis_user_period ON communication_analysis(user_id, analyzed_at);
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('app.services.email')

# Test individual components
from app.services.email.email_analysis_service import EmailAnalysisService
```

## 📚 API Documentation

### Authentication
All endpoints require JWT authentication:
```bash
Authorization: Bearer <access_token>
```

### Rate Limiting
- **Authenticated users**: 100 requests/minute
- **Email analysis**: 10 requests/minute
- **Culture metrics**: 20 requests/minute

### Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

Error responses:
```json
{
  "success": false,
  "error": "Error description",
  "code": 400
}
```

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd psychsync

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Pre-commit hooks
pre-commit install
```

### Code Style
- Black for formatting
- Flake8 for linting
- MyPy for type checking
- pytest for testing

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Documentation**: Check this README and API docs
- **Issues**: Create GitHub issue with detailed description
- **Email**: support@psychsync.ai
- **Discord**: Join our community channel

## 🗺️ Roadmap

### Version 2.0 (Q2 2024)
- Multi-language support (Spanish, French, German)
- Advanced predictive analytics
- Integration marketplace
- Mobile apps (iOS/Android)

### Version 2.1 (Q3 2024)
- Video call analysis (Zoom, Teams)
- Slack/Teams integration
- Advanced team formation recommendations
- Real-time collaboration coaching

### Version 3.0 (Q4 2024)
- Enterprise-grade compliance (SOC2, HIPAA)
- Custom model fine-tuning
- Advanced network analysis
- Predictive team performance modeling

---

## 🎉 Conclusion

PsychSync's Email-Based Behavioral Analysis provides unprecedented insights into workplace communication while maintaining strict privacy standards. The system helps organizations:

- **Prevent conflicts** before they escalate
- **Identify burnout risk** early and intervene
- **Improve team collaboration** through data-driven insights
- **Enhance culture health** with measurable metrics
- **Personalize employee development** with AI coaching

By analyzing communication patterns rather than content, we provide valuable insights while respecting employee privacy. The system is designed to scale with organizations of all sizes, from small teams to large enterprises.

Ready to transform your team communication insights? Start connecting email accounts today! 🚀