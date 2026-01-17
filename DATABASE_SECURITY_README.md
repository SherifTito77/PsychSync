# Database Security Testing Suite

A comprehensive database security testing framework that tests for NoSQL injection, credential rotation, backup encryption, privilege escalation, and log security vulnerabilities.

## 🚀 Quick Start

### Prerequisites

```bash
# Install required Python packages
pip install asyncio aiohttp motor asyncpg redis pymongo boto3 botocore

# For database connections, set environment variables:
export MONGO_USERNAME="your_mongo_user"
export MONGO_PASSWORD="your_mongo_password"
export DB_USER="your_postgres_user"
export DB_PASSWORD="your_postgres_password"
export REDIS_PASSWORD="your_redis_password"
```

### Run All Tests

```bash
# Run comprehensive security assessment
python database_security_master.py

# Run specific tests
python database_security_master.py --tests injection backup privilege

# Test production environment
python database_security_master.py --env production --api-url https://your-api.com

# Enable verbose logging
python database_security_master.py --verbose
```

## 📊 Test Coverage

### 1. NoSQL Injection Testing
- ✅ Authentication bypass attacks
- ✅ Operator injection (`$ne`, `$gt`, `$regex`, etc.)
- ✅ JavaScript injection (`$where`)
- ✅ Array-based injection
- ✅ Blind injection (time-based)
- ✅ Denial of Service attacks
- ✅ MongoDB, PostgreSQL, and other NoSQL databases

### 2. Credential Rotation Testing
- ✅ Default credential detection
- ✅ Hardcoded credential scanning
- ✅ Credential age verification
- ✅ Password strength analysis
- ✅ Rotation mechanism verification
- ✅ Environment variable checks

### 3. Backup Encryption Testing
- ✅ Backup file encryption detection
- ✅ AES-256 encryption verification
- ✅ Cloud backup security (AWS S3, Azure, GCS)
- ✅ Backup file permissions checking
- ✅ Retention policy validation
- ✅ Backup integrity verification

### 4. Privilege Escalation Testing
- ✅ PostgreSQL privilege abuse
- ✅ MongoDB role escalation
- ✅ Redis command abuse
- ✅ Function-based escalation
- ✅ Extension abuse
- ✅ Cross-database escalation

### 5. Log Security Testing
- ✅ Sensitive data exposure (PII, credentials, tokens)
- ✅ Log injection vulnerabilities
- ✅ File permission analysis
- ✅ Log retention compliance
- ✅ Integrity verification
- ✅ Monitoring assessment

## 🔧 Configuration

### Environment Variables
```bash
# Database connections
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USERNAME=admin
MONGO_PASSWORD=secret
MONGO_AUTH_DB=admin

DB_HOST=localhost
DB_PORT=5432
DB_NAME=psychsync
DB_USER=postgres
DB_PASSWORD=secret

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=secret

# API testing
API_BASE_URL=http://localhost:8000
```

### Custom Configuration
Create `security_config.json`:
```json
{
  "api_base_url": "https://your-api.com",
  "backup_directories": ["./backups", "/var/backups"],
  "log_directories": ["./logs", "/var/log"],
  "max_file_size": 52428800,
  "environment": "production"
}
```

## 📋 Report Structure

### Executive Summary
- Total findings by severity
- Risk score (0-100)
- Risk level assessment
- Overall security status

### Detailed Findings
- NoSQL injection vulnerabilities
- Credential management issues
- Backup security gaps
- Privilege escalation paths
- Log exposure incidents

### Risk Assessment
- Top security risks
- Threat vectors identified
- Asset impact analysis
- Affected systems inventory

### Remediation Roadmap
- Immediate actions (critical)
- Urgent actions (high priority)
- Planned improvements (medium/low)
- Time estimates for completion

### Compliance Status
- SOC 2 compliance
- PCI DSS requirements
- HIPAA regulations
- GDPR compliance

## 🎯 Individual Test Modules

### NoSQL Injection Tester
```bash
python nosql_injection_tester.py
```

Tests for:
- Authentication bypasses
- Query manipulation
- JavaScript code execution
- Time-based blind injection
- Aggregation pipeline abuse

### Backup Security Tester
```bash
python backup_security_tester.py
```

Tests for:
- File encryption verification
- Cloud storage security
- Access control issues
- Retention compliance
- Integrity validation

### Privilege Escalation Tester
```bash
python privilege_escalation_tester.py
```

Tests for:
- Role abuse opportunities
- Function exploitation
- Configuration weaknesses
- Extension abuse
- Cross-system escalation

### Log Security Tester
```bash
python log_security_tester.py
```

Tests for:
- PII exposure
- Credential leakage
- Injection vulnerabilities
- Permission issues
- Monitoring gaps

## 🚨 Severity Levels

- **CRITICAL**: Immediate security risk requiring immediate action
- **HIGH**: Significant security risk requiring urgent attention (24-48 hours)
- **MEDIUM**: Moderate security risk requiring planned remediation (1-2 weeks)
- **LOW**: Minor security issue for future improvement

## 🛡️ Security Best Practices

### Database Security
1. **Principle of Least Privilege**: Grant minimum required permissions
2. **Regular Credential Rotation**: Change passwords every 90 days
3. **Encrypt All Backups**: Use AES-256 encryption for database dumps
4. **Monitor Privileged Access**: Log and review administrative actions
5. **Network Segmentation**: Isolate database servers from public networks

### Application Security
1. **Input Validation**: Sanitize all user inputs
2. **Parameterized Queries**: Use prepared statements
3. **Error Handling**: Don't expose sensitive information in errors
4. **Rate Limiting**: Prevent brute force attacks
5. **Security Headers**: Implement proper HTTP security headers

### Logging and Monitoring
1. **Log Sanitization**: Remove sensitive data from logs
2. **Secure Log Storage**: Restrict log file permissions
3. **Log Rotation**: Implement proper log rotation policies
4. **Real-time Monitoring**: Set up security event alerting
5. **Audit Trails**: Maintain comprehensive audit logs

## 🔍 Customization

### Adding New Tests
1. Create new test class in appropriate module
2. Implement required methods
3. Add to master test runner
4. Update reporting templates

### Custom Patterns
Add new security patterns to relevant modules:
```python
# In log_security_tester.py
sensitive_patterns = {
    SensitiveDataType.CUSTOM: [
        r'custom_pattern_here',
        r'another_pattern'
    ]
}
```

## 📊 Integration

### CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Database Security Scan
  run: |
    python database_security_master.py --env production --tests all
```

### Monitoring Integration
```python
# Export results to monitoring system
import requests

def send_alerts_to_slack(finding):
    webhook_url = "your_slack_webhook"
    payload = {"text": f"🚨 {finding['description']}"}
    requests.post(webhook_url, json=payload)
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request
5. Ensure all tests pass

## 📝 License

This security testing suite is provided for authorized security testing only. Users must have explicit permission to test target systems.

## ⚠️ Disclaimer

This tool is designed for authorized security testing only. Users must obtain proper authorization before scanning any systems. The authors are not responsible for misuse of this software.
