# Anonymous Feedback System - Deployment Guide

## Overview

The Anonymous Feedback System is a comprehensive psychological safety reporting platform that enables employees to submit completely anonymous feedback about workplace concerns. This system prioritizes anonymity, psychological safety, and toxic behavior detection.

## Features

### Core Functionality
- **100% Anonymous Submissions**: No IP tracking, no user accounts, cryptographically secure tracking IDs
- **Multiple Feedback Categories**: Toxic behavior, psychological safety, team dynamics, leadership concerns, discrimination
- **Severity-Based Routing**: Critical issues trigger immediate HR alerts
- **Status Tracking**: Anonymous status checking via tracking ID
- **HR Review Dashboard**: Secure interface for authorized personnel
- **Advanced Analytics**: Pattern detection and psychological safety metrics

### Privacy & Security Features
- **Double Hashing**: Target identifiers are double-hashed for security
- **Content Sanitization**: Automatic removal of identifying information
- **No Forensics**: No timing patterns or metadata that could identify users
- **Separate Systems**: HR cannot see tracking IDs; submitters don't see internal notes
- **Tamper-Proof Audit Logs**: Cryptographic integrity verification

## Architecture

### Backend Components
```
FastAPI Application (Port 8000)
├── Anonymous Feedback Service
├── Database Models (PostgreSQL)
├── Celery Tasks (Redis)
├── Email Notifications
└── API Endpoints
```

### Frontend Components
```
React SPA (Port 5173)
├── Anonymous Feedback Form
├── Status Checking Interface
├── HR Review Dashboard
└── Analytics Components
```

### Database Schema
- `anonymous_feedback`: Main feedback submissions table
- `anonymous_feedback_pattern`: Pattern analysis table
- `anonymous_feedback_template`: Template definitions

## Installation & Setup

### Prerequisites
- PostgreSQL 12+
- Redis 6+
- Node.js 18+
- Python 3.9+
- Docker (optional)

### Backend Setup

1. **Environment Configuration**
```bash
# Add to .env.dev
ANONYMOUS_FEEDBACK_ENABLED=true
CRITICAL_FEEDBACK_ALERTS=true
FEEDBACK_DIGEST_ENABLED=true
```

2. **Database Migration**
```bash
# Apply the anonymous feedback migration
alembic upgrade head

# Verify tables were created
psql -d psychsync -c "\dt anonymous_feedback*"
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Celery Worker Setup**
```bash
# Start Celery worker for background tasks
celery -A app.tasks.anonymous_feedback_tasks worker --loglevel=info

# Start Celery beat for scheduled tasks
celery -A app.tasks.anonymous_feedback_tasks beat --loglevel=info
```

### Frontend Setup

1. **Install Components**
```bash
# Copy components to frontend
cp app/components/AnonymousFeedback*.tsx frontend/src/components/
```

2. **Update Routes**
```typescript
// Add to frontend/src/App.tsx
import AnonymousFeedbackForm from '@/components/AnonymousFeedbackForm';
import AnonymousFeedbackStatus from '@/components/AnonymousFeedbackStatus';
import AnonymousFeedbackHRDashboard from '@/components/AnonymousFeedbackHRDashboard';

// Add routes
<Route path="/anonymous-feedback" element={<AnonymousFeedbackForm />} />
<Route path="/feedback-status" element={<AnonymousFeedbackStatus />} />
<Route path="/hr/anonymous-feedback" element={<AnonymousFeedbackHRDashboard />} />
```

3. **Update API Service**
```typescript
// Add to frontend/src/services/api.ts
export const anonymousFeedbackAPI = {
  submit: (data) => api.post('/anonymous-feedback/submit', data),
  checkStatus: (trackingId) => api.get(`/anonymous-feedback/status/${trackingId}`),
  getCategories: () => api.get('/anonymous-feedback/categories'),
  getReviewData: (filters) => api.get('/anonymous-feedback/review', { params: filters }),
  updateStatus: (id, data) => api.put(`/anonymous-feedback/${id}/status`, data),
  getStatistics: (orgId, days) => api.get(`/anonymous-feedback/statistics/${orgId}`, { params: { days } })
};
```

### API Configuration

1. **Update API Router**
```python
# The endpoints are automatically included in app/api/v1/api.py
# Available at:
# POST /api/v1/anonymous-feedback/submit
# GET /api/v1/anonymous-feedback/status/{tracking_id}
# GET /api/v1/anonymous-feedback/categories
# GET /api/v1/anonymous-feedback/review
# PUT /api/v1/anonymous-feedback/{id}/status
# GET /api/v1/anonymous-feedback/statistics/{org_id}
```

2. **Environment Variables**
```bash
# Email configuration for notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@company.com
SMTP_PASSWORD=your-app-password
```

## Configuration

### Feedback Categories Configuration

The system supports these default categories:

```python
FEEDBACK_CATEGORIES = {
    'toxic_behavior': {
        'subcategories': ['verbal_abuse', 'bullying', 'harassment', 'intimidation'],
        'severity_levels': ['low', 'medium', 'high', 'critical']
    },
    'psychological_safety': {
        'subcategories': ['fear_speaking_up', 'exclusion', 'micromanagement'],
        'severity_levels': ['low', 'medium', 'high', 'critical']
    },
    'discrimination_bias': {
        'subcategories': ['gender_bias', 'racial_bias', 'age_discrimination'],
        'severity_levels': ['medium', 'high', 'critical']
    }
}
```

### Notification Configuration

1. **Critical Alerts**
```python
# Immediate alerts for critical/high severity
CRITICAL_SEVERITY_LEVELS = ['critical', 'high']
ALERT_RECIPIENTS = ['hr@company.com', 'safety@company.com']
```

2. **Daily Digest**
```python
# Daily summary at 9 AM
DIGEST_SCHEDULE = '0 9 * * *'  # Cron format
```

### Privacy Settings

```python
# Content sanitization patterns
SANITIZATION_PATTERNS = {
    'names': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
    'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phones': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'dates': r'\b\d{1,2}\/\d{1,2}\/\d{4}\b'
}
```

## Security Considerations

### Data Protection
1. **Encryption**: All sensitive data encrypted at rest
2. **Hashing**: Double hashing for target identifiers
3. **No Logging**: No IP addresses or timestamps in logs
4. **Access Control**: Role-based permissions for HR access

### Anonymity Verification
1. **Regular Audits**: Verify no identifying data is stored
2. **Penetration Testing**: Test for data leakage
3. **Code Reviews**: Review all data handling code

### Legal Compliance
- **GDPR Compliant**: Data subject rights implementation
- **CCPA Ready**: California privacy compliance
- **Whistleblower Protection**: Legal safe harbor provisions

## Monitoring & Maintenance

### Health Monitoring

```bash
# System health check
curl http://localhost:8000/api/v1/anonymous-feedback/health

# Expected response:
{
  "status": "healthy",
  "system": "anonymous_feedback",
  "features": {
    "submission": "operational",
    "tracking": "operational",
    "review": "operational"
  }
}
```

### Performance Metrics

Monitor these key metrics:
- **Submission Success Rate**: > 99%
- **Response Time**: < 200ms for submissions
- **Database Performance**: < 50ms queries
- **Email Delivery**: > 98% success rate

### Regular Maintenance Tasks

1. **Daily**
   - Review critical feedback alerts
   - Monitor system performance
   - Check email delivery rates

2. **Weekly**
   - Review feedback patterns
   - Update HR permissions
   - Audit access logs

3. **Monthly**
   - Analyze psychological safety metrics
   - Review retention policies
   - Update security patches

## Testing

### Unit Tests
```bash
# Run service tests
pytest app/tests/test_anonymous_feedback.py -v

# Test coverage
pytest app/tests/test_anonymous_feedback.py --cov=app/services/anonymous_feedback_service
```

### Integration Tests
```bash
# Test API endpoints
pytest tests/api/test_anonymous_feedback.py -v

# Test database operations
pytest tests/db/test_anonymous_feedback_models.py -v
```

### Frontend Tests
```bash
# Test React components
npm test src/components/AnonymousFeedbackForm.test.tsx
npm test src/components/AnonymousFeedbackStatus.test.tsx
npm test src/components/AnonymousFeedbackHRDashboard.test.tsx
```

### Load Testing
```bash
# Test submission handling
ab -n 1000 -c 10 http://localhost:8000/api/v1/anonymous-feedback/submit

# Test status checking
ab -n 1000 -c 20 http://localhost:8000/api/v1/anonymous-feedback/status/test-tracking-id
```

## Troubleshooting

### Common Issues

1. **Migration Fails**
```bash
# Check database connection
psql -d psychsync -c "SELECT version();"

# Check existing tables
psql -d psychsync -c "\dt"

# Rollback migration if needed
alembic downgrade -1
```

2. **Celery Tasks Not Running**
```bash
# Check Redis connection
redis-cli ping

# Check Celery worker status
celery -A app.tasks.anonymous_feedback_tasks inspect active

# Restart Celery services
docker-compose restart celery-worker celery-beat
```

3. **Email Notifications Not Sending**
```bash
# Test email configuration
python -c "from app.services.email_service import email_service; print(email_service.test_connection())"

# Check Celery task logs
docker-compose logs celery-worker | grep "anonymous_feedback"
```

4. **Frontend Integration Issues**
```bash
# Check API endpoint access
curl http://localhost:8000/api/v1/anonymous-feedback/categories

# Verify CORS configuration
curl -H "Origin: http://localhost:5173" http://localhost:8000/api/v1/anonymous-feedback/categories
```

### Log Locations
- **Application Logs**: `logs/app.log`
- **Celery Logs**: `logs/celery.log`
- **Database Logs**: PostgreSQL logs directory
- **Web Server Logs**: Nginx access/error logs

## Rollback Procedures

### Database Rollback
```bash
# Rollback to previous migration
alembic downgrade 98e4cbc0aebf

# Verify tables are removed
psql -d psychsync -c "\dt anonymous_feedback*"
```

### Code Rollback
```bash
# Git rollback
git checkout HEAD~1 -- app/services/anonymous_feedback_service.py
git checkout HEAD~1 -- app/api/v1/endpoints/anonymous_feedback.py

# Restart services
docker-compose restart backend celery-worker
```

### Frontend Rollback
```bash
# Remove components
rm frontend/src/components/AnonymousFeedback*.tsx

# Revert route changes
git checkout HEAD~1 -- frontend/src/App.tsx
```

## Support & Documentation

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Additional Resources
- **Psychological Safety Guide**: `/docs/psychological_safety.md`
- **Toxicity Detection Guide**: `/docs/toxicity_detection.md`
- **Employee Privacy Guide**: `/docs/employee_privacy.md`

### Emergency Contacts
- **System Administrator**: admin@company.com
- **Privacy Officer**: privacy@company.com
- **HR Support**: hr@company.com

---

## Deployment Checklist

- [ ] Database migration applied successfully
- [ ] Backend API endpoints responding
- [ ] Celery workers running and processing tasks
- [ ] Email notifications configured and tested
- [ ] Frontend components integrated
- [ ] API routes configured
- [ ] CORS settings updated
- [ ] Security audit completed
- [ ] Performance testing passed
- [ ] Documentation updated
- [ ] Monitoring configured
- [ ] Backup procedures verified

---

This system represents a significant advancement in workplace psychological safety and should be treated with the utmost care for privacy and security. Regular maintenance and monitoring are essential to ensure continued effectiveness and employee trust.