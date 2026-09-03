# 🚀 Production Deployment Security Checklist

**Purpose:** Ensure all security measures are in place before deploying PsychSync to production
**Last Updated:** 2025-12-24
**Version:** 1.0

---

## 📋 Pre-Deployment Checklist

Use this checklist to verify security configurations before production deployment. Each item must be completed and verified.

### ✅ Section 1: Code Security

- [ ] **No backup files in deployment**
  ```bash
  find . -name "*.backup" -o -name "*.bak" -o -name "*.old"
  # Expected: No files found
  ```

- [ ] **No sensitive files tracked in git**
  ```bash
  git ls-files | grep -E "\.env$|\.key$|\.pem$|secrets\.yaml"
  # Expected: No files found
  ```

- [ ] **All dependencies up to date**
  ```bash
  pip-audit  # Python
  npm audit  # Frontend
  # Expected: No high/critical vulnerabilities
  ```

- [ ] **Code scanned for security issues**
  ```bash
  bandit -r app/
  # Expected: No high/severity issues
  ```

- [ ] **Debug statements removed**
  ```bash
  grep -r "print(" app/ --include="*.py" | grep -v "# print"
  grep -r "console.log" frontend/src/ --include="*.ts" --include="*.tsx"
  # Expected: Only intentional logging
  ```

---

### ✅ Section 2: Authentication & Authorization

- [ ] **Rate limiting enabled on auth endpoints**
  - Login: Max 5 attempts per minute
  - Registration: Max 3 attempts per hour
  - Password reset: Max 3 attempts per hour

- [ ] **JWT tokens properly configured**
  ```python
  # Verify in app/core/config.py
  SECRET_KEY = os.getenv("SECRET_KEY")  # Must be set, not default
  ACCESS_TOKEN_EXPIRE_MINUTES = 30
  ALGORITHM = "HS256"
  ```

- [ ] **Refresh token rotation implemented**
  - Refresh tokens rotate on use
  - Old refresh tokens invalidated
  - Token revocation on logout

- [ ] **Password requirements enforced**
  - Minimum 8 characters
  - Requires uppercase, lowercase, number, special character
  - Password hashing with bcrypt/argon2

- [ ] **Multi-factor authentication available** (optional but recommended)
  - TOTP-based (Google Authenticator, Authy)
  - SMS backup codes
  - Recovery codes

---

### ✅ Section 3: Security Headers

- [ ] **All security headers configured**
  ```bash
  # Test with:
  curl -I https://your-domain.com/api/v1/health

  # Required headers:
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  Content-Security-Policy: default-src 'self'
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()
  ```

- [ ] **Server header removed**
  ```bash
  curl -I https://your-domain.com/api/v1/health | grep -i "^Server:"
  # Expected: No output (header removed)
  ```

- [ ] **X-Powered-By header removed** (if using Express/proxy)
  ```bash
  curl -I https://your-domain.com | grep -i "x-powered-by"
  # Expected: No output
  ```

---

### ✅ Section 4: API Security

- [ ] **CORS properly configured**
  ```python
  # In app/main.py
  ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS").split(",")
  # Only production domains, no wildcards
  ```

- [ ] **API documentation protected**
  ```python
  # /docs and /redoc disabled in production
  if settings.ENVIRONMENT == "production":
      app.remove_route("/docs")
      app.remove_route("/redoc")
  ```

- [ ] **Request size limits configured**
  ```python
  # In nginx or app config
  max_upload_size = 10MB
  max_request_body_size = 1MB
  ```

- [ ] **Input validation on all endpoints**
  - Pydantic schemas for request validation
  - SQL injection protection (parameterized queries)
  - XSS protection (output encoding)

- [ ] **Rate limiting on public APIs**
  ```python
  # Apply to all public endpoints
  @rate_limit(max_requests=100, window_seconds=60)
  ```

---

### ✅ Section 5: Database Security

- [ ] **Database credentials not in code**
  ```bash
  grep -r "postgresql://" app/ --include="*.py"
  # Expected: Only DATABASE_URL env var reference
  ```

- [ ] **Database connection uses SSL**
  ```python
  # In DATABASE_URL
  # postgresql://user:pass@host/db?sslmode=require
  ```

- [ ] **Database user has minimum required privileges**
  - No superuser access
  - SELECT, INSERT, UPDATE, DELETE only on needed tables
  - No DROP, CREATE, ALTER privileges

- [ ] **Database backups encrypted**
  ```bash
  # Test backup encryption
  ls -lh backups/*.enc
  # Expected: Encrypted backup files
  ```

- [ ] **Database not accessible from internet**
  ```bash
  # Firewall rules only allow application server IP
  # PostgreSQL port 5432 not exposed publicly
  ```

---

### ✅ Section 6: Environment Configuration

- [ ] **ENVIRONMENT variable set to production**
  ```bash
  echo $ENVIRONMENT
  # Expected: "production"
  ```

- [ ] **DEBUG mode disabled**
  ```bash
  echo $DEBUG
  # Expected: "False" or "0"
  ```

- [ ] **Secret keys randomly generated**
  ```bash
  # Length should be 32+ characters
  echo $SECRET_KEY | wc -c
  # Expected: 33+ (including newline)
  ```

- [ ] **All secrets in environment, not hardcoded**
  ```bash
  # Verify no secrets in code
  grep -r "sk_" app/ --include="*.py"  # Stripe keys
  grep -r "api_key" app/ --include="*.py"
  # Expected: Only env var references
  ```

- [ ] **Environment file not committed**
  ```bash
  git ls-files | grep "\.env$"
  # Expected: No files found
  ```

---

### ✅ Section 7: SSL/TLS Configuration

- [ ] **Valid SSL certificate installed**
  ```bash
  curl -I https://your-domain.com
  # Expected: No certificate errors
  ```

- [ ] **HTTP redirects to HTTPS**
  ```bash
  curl -I http://your-domain.com
  # Expected: 301/302 redirect to https://
  ```

- [ ] **Strong TLS configuration**
  ```nginx
  # In nginx config
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256...';
  ssl_prefer_server_ciphers on;
  ```

- [ ] **HSTS header with preload**
  ```bash
  curl -I https://your-domain.com | grep Strict-Transport-Security
  # Expected: max-age=31536000; includeSubDomains; preload
  ```

- [ ] **Certificate auto-renewal configured**
  ```bash
  # If using Let's Encrypt (certbot)
  certbot renew --dry-run
  # Expected: Renewal simulation successful
  ```

---

### ✅ Section 8: Monitoring & Logging

- [ ] **Security logging enabled**
  - Failed login attempts logged
  - Successful authentication logged
  - Permission denied events logged
  - Suspicious activity alerts configured

- [ ] **Log aggregation configured**
  - Centralized logging (e.g., Sentry, Datadog, ELK)
  - Log rotation configured
  - Log retention policy (90+ days)

- [ ] **Performance monitoring enabled**
  - Application performance monitoring (APM)
  - Database query performance tracking
  - API response time monitoring

- [ ] **Uptime monitoring configured**
  - External uptime monitor (e.g., Pingdom, UptimeRobot)
  - Health check endpoint: `/api/v1/health`
  - Alert on downtime (> 1 minute)

- [ ] **Security incident response plan documented**
  - Team contact list
  - Escalation procedures
  - Communication templates
  - Post-incident review process

---

### ✅ Section 9: Data Protection

- [ ] **PHI/PII encryption at rest**
  - Database encryption enabled
  - File storage encryption enabled
  - Backup encryption verified

- [ ] **PHI/PII encryption in transit**
  - TLS 1.2+ enforced
  - API calls over HTTPS only
  - No unauthenticated endpoints with sensitive data

- [ ] **Data retention policy defined**
  - Automatic data deletion after X years
  - User data export functionality (GDPR)
  - Right to be forgotten implementation

- [ ] **Access logging for sensitive data**
  - All access to PHI/PII logged
  - Who, what, when, where logged
  - Audit logs tamper-evident

- [ ] **Regular security backups configured**
  - Automated daily backups
  - Backup restoration tested
  - Off-site backup storage

---

### ✅ Section 10: Network Security

- [ ] **Web Application Firewall (WAF) enabled**
  ```bash
  # If using Cloudflare, AWS WAF, etc.
  # Verify WAF rules active
  ```

- [ ] **DDoS protection enabled**
  - Rate limiting per IP
  - Challenge platform for suspicious traffic
  - Auto-mitigation enabled

- [ ] **Firewall rules configured**
  - Only necessary ports open (80, 443)
  - Database not publicly accessible
  - SSH restricted to specific IPs

- [ ] **Intrusion detection/prevention (IDS/IPS)**
  - Network monitoring enabled
  - Anomaly detection configured
  - Automated blocking of threats

- [ ] **Private network for services**
  - Database in private subnet
  - Redis in private subnet
  - Inter-service communication over private network

---

### ✅ Section 11: Third-Party Integrations

- [ ] **API keys stored securely**
  - Environment variables only
  - No API keys in frontend code
  - Regular key rotation

- [ ] **OAuth security**
  - PKCE enabled for mobile apps
  - State parameter validation
  - Secure redirect URIs

- [ ] **Webhook security**
  - Webhook signature verification
  - HTTPS only for webhook endpoints
  - Replay attack prevention

- [ ] **Third-party dependency audit**
  ```bash
  pip-audit
  npm audit
  # Expected: No known vulnerabilities
  ```

- [ ] **API rate limits respected**
  - Don't exceed provider limits
  - Implement exponential backoff
  - Cache responses when possible

---

### ✅ Section 12: Compliance & Documentation

- [ ] **HIPAA compliance** (if handling PHI)
  - Risk assessment completed
  - Business Associate Agreements (BAAs) in place
  - Policies and procedures documented
  - Employee training completed

- [ ] **GDPR compliance** (if handling EU data)
  - Privacy policy published
  - Cookie consent implemented
  - Data processing agreements
  - Data protection impact assessment

- [ ] **Security documentation**
  - Architecture diagrams updated
  - Security policies documented
  - Incident response plan written
  - Employee security handbook

- [ ] **Disaster recovery plan**
  - Recovery time objective (RTO) defined
  - Recovery point objective (RPO) defined
  - Backup restoration tested
  - Failover procedures documented

- [ ] ** penetration testing scheduled**
  - Annual third-party pen test
  - Bug bounty program (optional)
  - Continuous security scanning

---

## 🚨 Post-Deployment Verification

Run these commands immediately after deployment:

### 1. Security Headers Check
```bash
curl -I https://your-domain.com/api/v1/health
```
Verify all headers present.

### 2. TLS Configuration Check
```bash
nmap --script ssl-enum-ciphers -p 443 your-domain.com
```
Verify strong TLS 1.2+ only.

### 3. Rate Limiting Check
```bash
for i in {1..10}; do
  curl -X POST https://your-domain.com/api/v1/auth/token \
    -H "Content-Type: application/json" \
    -d '{"username":"test@test.com","password":"wrong"}'
done
```
Should receive 429 after 5 attempts.

### 4. API Authentication Check
```bash
curl https://your-domain.com/api/v1/users
```
Should receive 401 Unauthorized.

### 5. Hidden Routes Check
```bash
curl https://your-domain.com/admin
curl https://your-domain.com/debug
```
Should receive 404 Not Found.

### 6. SSL Certificate Check
```bash
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```
Verify valid certificate and chain.

### 7. DNS Security Check
```bash
dig your-domain.com ANY
```
Verify no unexpected records.

---

## 📊 Deployment Sign-Off

Before deploying to production, ensure the following:

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Developer** | | | |
| **Security Lead** | | | |
| **DevOps Engineer** | | | |
| **Product Owner** | | | |
| **CTO / VP Engineering** | | | |

---

## 🔧 Rolling Back If Issues Found

If any security issues are discovered post-deployment:

1. **Immediate rollback** if critical vulnerability found
2. **Hotfix deployment** for non-critical issues
3. **Incident report** documenting the issue
4. **Post-mortem** to prevent recurrence

### Rollback Commands:
```bash
# Kubernetes
kubectl rollout undo deployment/psychsync-backend

# Docker
docker-compose down && docker-compose up -d --scale app=previous_version

# Manual
git revert <commit-hash>
# redeploy
```

---

## 📞 Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| **Security Lead** | | | |
| **DevOps On-Call** | | | |
| **CTO** | | | |
| **Incident Response** | | | |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-24
**Next Review:** 2026-01-24

---

*This checklist should be completed before EVERY production deployment. Security is an ongoing process, not a one-time event.*
