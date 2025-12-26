# Enterprise Security Deployment Guide

## 🔒 OVERVIEW

This document provides comprehensive deployment instructions for the enterprise-grade security implementation for PsychSync. The security implementation includes:

- **Field-Level Encryption** for sensitive PII/PHI data
- **Row-Level Security (RLS)** for multi-tenant data isolation
- **Comprehensive Audit Logging** for compliance and monitoring
- **GDPR/CCPA Compliance** features
- **Advanced Input Validation** and XSS/SQL injection prevention
- **Performance-Optimized** security measures

## 📋 DEPLOYMENT PREREQUISITES

### System Requirements

- **PostgreSQL 14+** with required extensions
- **Redis 6+** for caching and session management
- **Python 3.11+** with asyncio support
- **Docker** for containerized deployment
- **Kubernetes** (optional) for orchestration

### Security Configuration

```bash
# Required environment variables
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/psychsync"
export ENCRYPTION_KEY="your-32-byte-encryption-key-here"
export JWT_SECRET="your-jwt-secret-key-here"
export ENVIRONMENT="production"

# Security settings
export PASSWORD_MIN_LENGTH=12
export ACCESS_TOKEN_EXPIRE_MINUTES=30
export REFRESH_TOKEN_EXPIRE_DAYS=7
export MAX_LOGIN_ATTEMPTS=5
export ACCOUNT_LOCKOUT_DURATION=300
```

## 🚀 DEPLOYMENT STEPS

### 1. Database Security Setup

```bash
# Connect to PostgreSQL as superuser
psql -U postgres -d psychsync

# Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

# Enable Row Level Security by default
ALTER DATABASE psychsync SET row_security = on;
```

### 2. Migration Execution

```bash
# Run database migrations with security implementation
alembic upgrade head

# Verify RLS policies are enabled
psql -U postgres -d psychsync -c "
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename LIKE '%_secure';
"
```

### 3. Encryption Key Management

```python
# Generate secure encryption key
import secrets
import base64
from cryptography.fernet import Fernet

# Generate 32-byte key
key = Fernet.generate_key()
print(f"Encryption Key: {key.decode()}")

# Store securely in environment or key management system
```

### 4. Secure Configuration Files

#### `docker-compose.prod.yml`
```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - ENVIRONMENT=production
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - db
      - redis
    networks:
      - secure_network
    restart: unless-stopped

  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=psychsync
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - secure_network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - secure_network
    restart: unless-stopped

networks:
  secure_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

#### Kubernetes Security Configuration

##### `k8s/secret-config.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: psychsync-secrets
  namespace: psychsync
type: Opaque
data:
  encryption-key: <base64-encoded-encryption-key>
  jwt-secret: <base64-encoded-jwt-secret>
  db-password: <base64-encoded-db-password>
  redis-password: <base64-encoded-redis-password>
```

##### `k8s/security-context.yaml`
```yaml
apiVersion: v1
kind: PodSecurityPolicy
metadata:
  name: psychsync-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## 🔍 SECURITY VALIDATION

### 1. Automated Security Tests

```bash
# Run comprehensive security test suite
pytest tests/test_enterprise_security.py -v --tb=short

# Run specific security test categories
pytest tests/test_enterprise_security.py::TestFieldLevelEncryption -v
pytest tests/test_enterprise_security.py::TestRowLevelSecurity -v
pytest tests/test_enterprise_security.py::TestInputValidation -v
```

### 2. Security Headers Validation

```bash
# Test API security headers
curl -I https://api.psychsync.com/health \
  -H "User-Agent: Security-Test"

# Expected headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: "1; mode=block"
# Strict-Transport-Security: max-age=31536000; includeSubDomains
# Content-Security-Policy: default-src 'self'
```

### 3. Row-Level Security Verification

```sql
-- Test RLS policies
-- Connect as regular user
\c psychsync regular_user

-- Try to access other organization's data (should fail)
SELECT COUNT(*) FROM users_secure WHERE organization_id != current_org_id;

-- Should return 0 rows
```

### 4. Encryption Verification

```sql
-- Verify sensitive data is encrypted
SELECT
    email,
    CASE
        WHEN full_name_encrypted LIKE '%Test User%' THEN 'NOT ENCRYPTED'
        ELSE 'ENCRYPTED'
    END as encryption_status
FROM users_secure
WHERE email LIKE '%test%';
```

## 📊 MONITORING AND ALERTING

### 1. Security Metrics Dashboard

```python
# Security metrics collection
SECURITY_METRICS = {
    'authentication_failures': 'auth_failures_total',
    'sql_injection_attempts': 'sql_injection_attempts_total',
    'xss_attempts': 'xss_attempts_total',
    'rls_violations': 'rls_violations_total',
    'data_access_anomalies': 'data_access_anomalies_total',
    'encryption_errors': 'encryption_errors_total'
}
```

### 2. Alert Configuration

#### Prometheus + Grafana Alerts

```yaml
# prometheus_rules.yml
groups:
- name: psychsync_security
  rules:
  - alert: HighAuthenticationFailureRate
    expr: rate(auth_failures_total[5m]) > 10
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High authentication failure rate"
      description: "Authentication failure rate is {{ $value }} per second"

  - alert: RLSPolicyViolation
    expr: rls_violations_total > 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Row-Level Security violation detected"
      description: "RLS policy violation: {{ $value }}"
```

### 3. Log Aggregation

#### ELK Stack Configuration

```yaml
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "psychsync" {
    # Parse security logs
    if [message] =~ /SECURITY_EVENT/ {
      grok {
        match => { "message" => "%{TIMESTAMP_ISO8601:timestamp}.*SECURITY_EVENT.*%{WORD:event_type}.*user_id=%{UUID:user_id}.*ip=%{IP:client_ip}" }
      }
    }

    # Add security tags
    if [event_type] {
      mutate {
        add_tag => ["security", "%{event_type}"]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "psychsync-security-%{+YYYY.MM.dd}"
  }
}
```

## 🛡️ SECURITY HARDENING

### 1. Network Security

```bash
# Firewall configuration
ufw allow 22/tcp    # SSH
ufw allow 443/tcp   # HTTPS
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw deny 5432/tcp   # PostgreSQL (internal only)
ufw deny 6379/tcp   # Redis (internal only)
ufw enable
```

### 2. SSL/TLS Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.psychsync.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/psychsync.crt;
    ssl_certificate_key /etc/ssl/private/psychsync.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'";

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Database Security

```sql
-- Create read-only user for reporting
CREATE USER psychsync_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE psychsync TO psychsync_readonly;
GRANT USAGE ON SCHEMA public TO psychsync_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO psychsync_readonly;

-- Create audit user
CREATE USER psychsync_audit WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE psychsync TO psychsync_audit;
GRANT USAGE ON SCHEMA public TO psychsync_audit;
GRANT SELECT, INSERT ON audit_logs TO psychsync_audit;
GRANT SELECT ON security_events TO psychsync_audit;

-- Revoke unnecessary permissions
REVOKE ALL ON SCHEMA public FROM PUBLIC;
```

## 📋 COMPLIANCE CHECKLIST

### HIPAA Compliance

- [ ] Encrypt all PHI at rest and in transit
- [ ] Implement access controls for PHI
- [ ] Enable comprehensive audit logging
- [ ] Establish data retention policies
- [ ] Implement user authentication and authorization
- [ ] Conduct regular security assessments
- [ ] Maintain business associate agreements

### GDPR Compliance

- [ ] Implement data subject rights (access, rectification, erasure)
- [ ] Obtain explicit consent for data processing
- [ ] Enable data portability features
- [ ] Implement data breach notification procedures
- [ ] Conduct data protection impact assessments
- [ ] Appoint data protection officer if required
- [ ] Maintain records of processing activities

### CCPA Compliance

- [ ] Implement consumer rights (access, deletion, opt-out)
- [ ] Provide privacy policy disclosure
- [ ] Enable "Do Not Sell My Personal Information" option
- [ ] Implement reasonable security procedures
- [ ] Maintain data inventory and processing records
- [ ] Provide opt-out mechanisms for data sharing

## 🔧 MAINTENANCE PROCEDURES

### 1. Regular Security Updates

```bash
# Weekly security update script
#!/bin/bash
echo "Starting weekly security maintenance..."

# Update system packages
apt update && apt upgrade -y

# Update Python dependencies
pip install --upgrade -r requirements.txt

# Run security tests
pytest tests/test_enterprise_security.py

# Check for vulnerabilities
safety check

# Restart services if needed
docker-compose restart app

echo "Security maintenance completed"
```

### 2. Key Rotation

```python
# Encryption key rotation procedure
async def rotate_encryption_key():
    """Rotate encryption key with minimal downtime"""

    # 1. Generate new key
    new_key = Fernet.generate_key()

    # 2. Re-encrypt sensitive data
    # This would be a background job to minimize impact

    # 3. Update configuration
    # Gradually migrate to new key

    # 4. Verify data integrity
    # Spot-check encrypted data

    pass
```

### 3. Backup Security

```bash
# Secure backup procedure
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="psychsync_secure_backup_${DATE}.sql.gz"

# Create encrypted backup
pg_dump psychsync | gzip -9 | gpg --cipher-algo AES256 --compress-algo 1 --symmetric --output $BACKUP_FILE

# Verify backup
gpg --decrypt $BACKUP_FILE | gunzip -c | head -n 10

# Upload to secure storage
aws s3 cp $BACKUP_FILE s3://secure-backups/psychsync/ --server-side-encryption AES256

# Cleanup local backup
shred -u $BACKUP_FILE
```

## 🚨 INCIDENT RESPONSE

### Security Incident Response Plan

1. **Detection**: Monitor security alerts and logs
2. **Assessment**: Evaluate incident severity and scope
3. **Containment**: Isolate affected systems
4. **Investigation**: Analyze logs and forensic data
5. **Communication**: Notify stakeholders and authorities
6. **Remediation**: Patch vulnerabilities and restore services
7. **Post-Mortem**: Document lessons learned

### Emergency Contact Information

```yaml
security_contacts:
  security_team:
    email: security@psychsync.com
    phone: +1-555-SECURITY

  data_protection_officer:
    email: dpo@psychsync.com

  legal_counsel:
    email: legal@psychsync.com

  incident_response:
    email: incident@psychsync.com
    phone: +1-555-INCIDENT
```

## 📚 REFERENCE DOCUMENTATION

- [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [GDPR Official Text](https://gdpr-info.eu/)
- [CCPA Full Text](https://oag.ca.gov/privacy/ccpa)

---

**Last Updated**: 2025-01-24
**Version**: 3.0 Enterprise Security
**Classification**: Internal Use Only