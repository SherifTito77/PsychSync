# PsychSync Security Features Guide

This guide provides comprehensive documentation for the enhanced security features implemented in the PsychSync application.

## 🔐 Overview

The PsychSync security implementation provides enterprise-grade protection through multiple layers of defense:

1. **Enhanced Authentication** - JWT token rotation, strong password validation, device fingerprinting
2. **Real-time Threat Detection** - Anomaly detection for suspicious behavior patterns
3. **Account Protection** - Progressive lockout mechanisms and session management
4. **Security Monitoring** - Continuous behavioral analysis and automated alerting
5. **CSRF Protection** - Token-based validation to prevent cross-site attacks

## ⚙️ Security Configuration

All security features are configurable through environment variables in `.env.dev` or `.env.production`:

### Authentication Security
```bash
# JWT Configuration (Required for production)
SECRET_KEY=your-64-character-cryptographically-secure-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Security
PASSWORD_MIN_LENGTH=8
PASSWORD_MAX_LENGTH=128
```

### Account Security
```bash
# Account Lockout Settings
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
PROGRESSIVE_LOCKOUT_ENABLED=true
```

### Session Management
```bash
# Device and Session Tracking
DEVICE_FINGERPRINTING_ENABLED=true
MAX_CONCURRENT_SESSIONS=3
SESSION_DURATION_HOURS=24
DEVICE_TRUST_DURATION_DAYS=30
```

### Security Monitoring
```bash
# Anomaly Detection
SECURITY_MONITORING_ENABLED=true
ANOMALY_DETECTION_THRESHOLD=0.7
IMPOSSIBLE_TRAVEL_SPEED_KMH=800
BRUTE_FORCE_THRESHOLD=5
UNUSUAL_LOCATION_THRESHOLD=0.8

# Alert Retention
SECURITY_ALERT_RETENTION_DAYS=90
BEHAVIOR_PROFILE_RETENTION_DAYS=30
```

## 🛡️ Enhanced Security Features

### 1. Advanced Authentication

#### JWT Token Rotation
- **Access tokens**: 30-minute expiration
- **Refresh tokens**: 7-day expiration with rotation
- **Token blacklisting**: Prevents replay attacks
- **Secure storage**: Automatic refresh via axios interceptors

#### Password Validation
- **Strength scoring**: 0-100 scale based on multiple factors
- **Character requirements**: Uppercase, lowercase, digits, special characters
- **Pattern detection**: Prevents common passwords and sequential characters
- **Real-time feedback**: Detailed validation messages

### 2. Account Security

#### Progressive Lockout
- **Initial lockout**: 15 minutes after 5 failed attempts
- **Progressive scaling**: Duration increases with repeated failures
- **Security events**: Detailed logging of all lockout events
- **Automatic recovery**: Lockouts expire automatically

#### Device Fingerprinting
- **Browser detection**: User agent, screen resolution, timezone
- **Hardware profiling**: Canvas fingerprint, WebGL information
- **Trust management**: Remember trusted devices for 30 days
- **Anomaly detection**: Alert on new/unknown devices

### 3. Session Management

#### Concurrent Session Limits
- **Maximum sessions**: 3 concurrent sessions per user
- **Session tracking**: Detailed session information and activity
- **Device management**: View and revoke active sessions
- **Trust devices**: Mark devices as trusted for convenience

#### Session Security
- **Automatic cleanup**: Expired sessions removed immediately
- **Activity monitoring**: Track session usage patterns
- **Geographic tracking**: IP-based location analysis
- **Suspicious activity detection**: Unusual access patterns

### 4. Security Monitoring & Anomaly Detection

#### Real-time Threat Detection
- **Impossible travel**: Detects geographically impossible logins
- **Brute force attacks**: Identifies credential stuffing attempts
- **Concurrent sessions**: Alerts on suspicious multi-device access
- **Unusual locations**: Detects access from new geographic areas
- **API abuse**: Identifies suspicious usage patterns

#### Risk Assessment
- **Dynamic scoring**: Real-time risk level calculation
- **Behavioral analysis**: User profile tracking and comparison
- **Trend analysis**: Historical pattern recognition
- **Context-aware responses**: Security actions based on risk level

### 5. CSRF Protection

#### Token Validation
- **Session binding**: CSRF tokens bound to user sessions
- **Constant-time comparison**: Prevents timing attacks
- **Automatic token refresh**: Seamless user experience
- **Path exclusion**: Configurable endpoint exclusions

## 🔧 Security API Endpoints

### Authentication Endpoints
```bash
# Enhanced login with security monitoring
POST /api/v1/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=secure_password

# Refresh token rotation
POST /api/v1/refresh
Authorization: Bearer <refresh_token>

# Secure logout
POST /api/v1/logout
Authorization: Bearer <access_token>

# Logout from all devices
POST /api/v1/logout-all
Authorization: Bearer <access_token>
```

### Security Monitoring Endpoints

#### View Security Alerts
```bash
# Get user's security alerts
GET /api/v1/security-alerts
Authorization: Bearer <access_token>

# Get alerts with filters
GET /api/v1/security-alerts?severity=high&hours=24&include_resolved=false
Authorization: Bearer <access_token>

# Admin: Get all security alerts
GET /api/v1/security-alerts
Authorization: Bearer <admin_access_token>
```

#### Manage Security Alerts
```bash
# Resolve a security alert
POST /api/v1/resolve-alert/{alert_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "resolution_note": "Investigated and confirmed as false positive"
}
```

#### Risk Assessment
```bash
# Get current user's risk assessment
GET /api/v1/risk-assessment
Authorization: Bearer <access_token>

# Admin: Get risk assessment for specific user
GET /api/v1/risk-assessment?target_user_id=user_id
Authorization: Bearer <admin_access_token>
```

### Session Management Endpoints
```bash
# Get active sessions
GET /api/v1/sessions
Authorization: Bearer <access_token>

# Revoke specific session
DELETE /api/v1/sessions/{session_id}
Authorization: Bearer <access_token>

# Trust a device
POST /api/v1/trust-device
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "device_id": "device_fingerprint_hash"
}
```

## 📊 Security Response Examples

### Successful Login Response
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "user_id",
      "email": "user@example.com",
      "role": "user"
    },
    "security_info": {
      "attempts_remaining": 5,
      "security_score": 100
    },
    "session_info": {
      "session_id": "session_12345",
      "device_id": "device_abc123",
      "device_type": "desktop",
      "is_trusted_device": false,
      "concurrent_sessions": 1,
      "max_concurrent_sessions": 3
    }
  },
  "message": "Login successful"
}
```

### Security Alert Response
```json
{
  "status": "success",
  "data": {
    "alerts": [
      {
        "id": "alert_123456",
        "anomaly_type": "impossible_travel",
        "severity": "high",
        "user_id": "user_id",
        "description": "Impossible travel detected: 2500km in 0.5 hours",
        "timestamp": "2024-01-15T10:30:00Z",
        "risk_score": 80.0,
        "action_taken": "Security team notified and enhanced monitoring enabled",
        "resolved": false,
        "details": {
          "from_ip": "192.168.1.1",
          "to_ip": "203.0.113.1",
          "distance_km": 2500,
          "time_diff_hours": 0.5,
          "max_speed_kmh": 800
        }
      }
    ],
    "count": 1,
    "filters": {
      "severity": null,
      "hours": 24,
      "include_resolved": false,
      "user_id": "user_id"
    }
  },
  "message": "Retrieved 1 security alerts"
}
```

### Risk Assessment Response
```json
{
  "status": "success",
  "data": {
    "user_id": "user_id",
    "risk_level": "medium",
    "risk_factors": {
      "failed_login_rate": 0.1,
      "unusual_locations": 2,
      "total_logins": 50,
      "success_rate": 0.9,
      "recent_alerts": 1,
      "risk_score": 35.0
    },
    "risk_score": 35.0,
    "assessment_timestamp": "2024-01-15T10:30:00Z"
  },
  "message": "Risk assessment completed for user user_id"
}
```

## 🚀 Deployment Security Checklist

### Production Security Requirements

#### 1. Environment Variables
- [ ] Generate secure 64+ character SECRET_KEY
- [ ] Set production database credentials
- [ ] Configure Redis for caching and sessions
- [ ] Enable all security monitoring features
- [ ] Set appropriate lockout thresholds

#### 2. Database Security
- [ ] Enable SSL/TLS connections
- [ ] Use database-specific user accounts
- [ ] Implement connection pooling
- [ ] Enable query logging for audit

#### 3. Network Security
- [ ] Configure firewall rules
- [ ] Enable HTTPS with valid certificates
- [ ] Set up reverse proxy (nginx/traefik)
- [ ] Configure rate limiting at network level

#### 4. Monitoring & Logging
- [ ] Enable structured logging
- [ ] Configure log aggregation
- [ ] Set up security alert notifications
- [ ] Implement backup and recovery procedures

### Security Validation Commands

#### Test Configuration Loading
```bash
python -c "
from app.core.config import settings
print(f'✅ SECRET_KEY length: {len(settings.SECRET_KEY)}')
print(f'✅ SECURITY_MONITORING_ENABLED: {settings.SECURITY_MONITORING_ENABLED}')
print(f'✅ MAX_LOGIN_ATTEMPTS: {settings.MAX_LOGIN_ATTEMPTS}')
"
```

#### Test Security Modules
```bash
python -c "
from app.main import app
from app.core.security_monitoring import security_monitor
from app.core.account_security import account_security_manager
from app.core.session_management import session_manager
print('✅ All security modules loaded successfully')
"
```

#### Run Security Tests
```bash
# Run authentication tests
pytest tests/api/test_auth.py -v

# Run security validation tests
pytest tests/test_security_audit.py -v

# Run comprehensive test suite
pytest tests/ -k "security" -v
```

## 📈 Security Monitoring Best Practices

### 1. Regular Security Reviews
- Review security alerts daily
- Analyze failed login patterns weekly
- Update threat detection rules monthly
- Conduct quarterly security assessments

### 2. User Security Education
- Enable users to view their security status
- Provide alerts for suspicious activity
- Offer security tips and best practices
- Encourage strong password usage

### 3. Incident Response
- Establish security incident procedures
- Define escalation paths for different threat levels
- Maintain contact information for security team
- Document all security incidents

### 4. Continuous Improvement
- Monitor emerging security threats
- Update security configurations regularly
- Implement new security features as needed
- Regular penetration testing

## 🆘 Security Incident Response

### Immediate Actions
1. **Identify the threat level** based on security alerts
2. **Isolate affected accounts** if account takeover suspected
3. **Review recent login activity** for unauthorized access
4. **Force password resets** for compromised accounts

### Investigation Steps
1. **Analyze security alerts** for attack patterns
2. **Review session logs** for suspicious activity
3. **Check IP geolocation** for impossible travel
4. **Examine user behavior** for anomalies

### Recovery Actions
1. **Resolve security alerts** with detailed notes
2. **Update security configurations** if needed
3. **Notify affected users** of security incidents
4. **Document lessons learned** for future prevention

## 📞 Security Support

For security-related questions or incident reporting:
- **Security Team**: security@psychsync.com
- **Documentation**: This guide and inline code comments
- **Monitoring**: Real-time security dashboard (coming soon)
- **Alerts**: Email notifications for critical security events

---

**⚠️ Important**: This security implementation provides multiple layers of protection but requires proper configuration and ongoing monitoring. Always follow security best practices and keep systems updated.