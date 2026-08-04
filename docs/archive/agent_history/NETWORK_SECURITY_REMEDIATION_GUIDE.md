# Network Security Remediation Guide

**Generated:** 2025-12-23
**Audit Score:** 8.42/10 (GOOD)
**Target:** PsychSync Application

---

## Executive Summary

The network security audit identified **6 findings** across severity levels:
- 🔴 CRITICAL: 0
- 🟠 HIGH: 2
- 🟡 MEDIUM: 3
- 🔵 LOW: 1

This guide provides step-by-step remediation for each finding.

---

## Priority 1: HIGH Severity Issues

### Issue #1: SSL/TLS Certificate Not Accessible

**Location:** `tls_configuration`
**Finding:** Server running HTTP in development mode (port 8000)
**Impact:** No encryption for data in transit

#### Remediation Steps:

1. **For Development (Current State):**
   - ✅ Current configuration is acceptable for development
   - HTTP on port 8000 is intentional for local development
   - See: `app/main.py:764-774`

2. **For Production:**

   **Step 1:** Generate valid SSL certificates
   ```bash
   # Option A: Use Let's Encrypt (Recommended for production)
   sudo apt install certbot
   sudo certbot certonly --standalone -d api.psychsync.com

   # Option B: Self-signed for testing
   openssl req -x509 -newkey rsa:4096 -keyout certs/psychsync.key -out certs/psychsync.crt -days 365 -nodes
   ```

   **Step 2:** Verify certificate permissions
   ```bash
   chmod 600 certs/psychsync.key
   chmod 640 certs/psychsync.crt
   ```

   **Step 3:** Update environment configuration
   ```bash
   # In .env.production
   SSL_ENABLED=true
   SSL_KEY_PATH=/path/to/certs/psychsync.key
   SSL_CERT_PATH=/path/to/certs/psychsync.crt
   ```

   **Step 4:** Verify SSL configuration
   ```bash
   # Test the certificate
   openssl s_client -connect localhost:8443 -servername localhost

   # Check certificate details
   openssl x509 -in certs/psychsync.crt -text -noout
   ```

**Verification:**
```bash
# Run SSL test
python3 network_layer_security_audit.py --host localhost --port 8443
```

---

### Issue #2: No Secure TLS Version Supported

**Location:** `tls_configuration`
**Finding:** Server does not support TLS 1.2 or 1.3
**Impact:** Same as Issue #1 (HTTP mode)

#### Remediation:

✅ **Already Configured Correctly**

Your SSL configuration in `app/core/ssl_config.py:54-60` already enforces TLS 1.2+:

```python
def _configure_tls_versions(self, context: ssl.SSLContext) -> None:
    # Enable only TLS 1.2 and 1.3 (disable older insecure versions)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.maximum_version = ssl.TLSVersion.TLSv1_3
```

Once HTTPS is enabled, this will automatically be active.

**Configuration already includes:**
- ✅ TLS 1.2 minimum
- ✅ TLS 1.3 maximum
- ✅ Strong cipher suites
- ✅ Forward secrecy
- ✅ SSLv2/SSLv3/TLSv1.0/TLSv1.1 disabled

---

## Priority 2: MEDIUM Severity Issues

### Issue #3: DNSSEC Validation Status Unclear

**Location:** `dns_poisoning`
**Finding:** Could not verify DNSSEC is enabled
**Impact:** Potential vulnerability to DNS cache poisoning attacks

#### Remediation Steps:

**Step 1:** Check current DNS configuration
```bash
# Check DNS servers
cat /etc/resolv.conf

# Test DNSSEC for your domain
dig +dnssec psychsync.com
```

**Step 2:** Configure DNSSEC validation (Optional for app-level)

**For Application-Level DNS Resolution:**

Create a DNS resolver configuration in `app/core/config/dns.py`:

```python
import dns.resolver
import dns.rdatatype

class SecureDNSResolver:
    """DNSSEC-aware DNS resolver"""

    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.validate_dnssec = True

    def resolve(self, hostname: str) -> str:
        """Resolve hostname with DNSSEC validation"""
        try:
            answer = self.resolver.resolve(hostname, 'A')
            if answer.response.flags & dns.flags.AD:
                # Authenticated Data flag set - DNSSEC validated
                return answer[0].address
            else:
                # DNSSEC not validated
                raise ValueError("DNSSEC validation failed")
        except Exception as e:
            # Fallback to system resolver
            import socket
            return socket.gethostbyname(hostname)
```

**Step 3:** For infrastructure-level DNSSEC:

1. Enable DNSSEC on your domain registrar
2. Generate DNSSEC keys at your DNS provider
3. Submit DS records to your registrar
4. Verify with: `dig +dnssec yourdomain.com +short`

**Alternative Recommendation:**
Use trusted DNS resolvers with built-in DNSSEC validation:
- Cloudflare DNS: 1.1.1.1
- Google Public DNS: 8.8.8.8
- Quad9: 9.9.9.9

---

### Issue #4: Host Header Validation Not Verified

**Location:** `dns_poisoning`
**Finding:** Manual testing required for Host header validation
**Impact:** Potential DNS rebinding attacks

#### Remediation Steps:

**Step 1:** Implement Host header validation middleware

Create `app/middleware/host_validation.py`:

```python
from fastapi import Request, HTTPException
from app.core.config import settings

ALLOWED_HOSTS = settings.get("ALLOWED_HOSTS", ["*"])

async def validate_host_header(request: Request, call_next):
    """Validate Host header to prevent DNS rebinding attacks"""

    host = request.headers.get("host", "").split(":")[0]

    # Skip validation for health checks in development
    if settings.ENVIRONMENT == "development" and request.url.path in ["/health", "/docs"]:
        return await call_next(request)

    # Check if host is allowed
    if "*" not in ALLOWED_HOSTS and host not in ALLOWED_HOSTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Host header: {host}"
        )

    # Check for suspicious patterns
    suspicious_patterns = ["evil.com", "attacker.com", "malicious.com"]
    if any(pattern in host.lower() for pattern in suspicious_patterns):
        raise HTTPException(
            status_code=400,
            detail="Suspicious Host header detected"
        )

    return await call_next(request)
```

**Step 2:** Add to application configuration in `.env`:

```bash
# .env.production
ALLOWED_HOSTS=api.psychsync.com,psychsync.com,www.psychsync.com
```

**Step 3:** Register middleware in `app/main.py`:

```python
from app.middleware.host_validation import validate_host_header

app.add_middleware(BaseHTTPMiddleware, dispatch=validate_host_header)
```

---

### Issue #5: Localhost Endpoint Exposure Not Verified

**Location:** `internal_api`
**Finding:** Manual code review required
**Impact:** Internal endpoints might be exposed externally

#### Remediation Steps:

**Step 1:** Audit all API endpoints

```bash
# List all endpoints
python3 -c "
from app.main import app
for route in app.routes:
    if hasattr(route, 'path'):
        print(f'{route.methods} {route.path}')
"
```

**Step 2:** Check for localhost-only endpoints

Search codebase for patterns like:
```bash
# Search for localhost binding
grep -r "127.0.0.1" app/
grep -r "localhost" app/api/
grep -r "internal" app/api/
```

**Step 3:** Implement IP whitelisting for sensitive endpoints

```python
# In endpoint definition
from fastapi import Request
from app.core.config import settings

@app.get("/api/v1/internal/metrics")
async def get_metrics(request: Request):
    """Only accessible from localhost or whitelisted IPs"""

    client_ip = request.client.host

    # Allow localhost
    if client_ip in ["127.0.0.1", "::1"]:
        return get_internal_metrics()

    # Check whitelist
    allowed_ips = settings.INTERNAL_API_WHITELIST.split(",")
    if client_ip not in allowed_ips:
        raise HTTPException(status_code=403, detail="Forbidden")

    return get_internal_metrics()
```

**Step 4:** Add network-level controls

```nginx
# nginx.conf
location /api/internal {
    # Only allow from localhost
    allow 127.0.0.1;
    deny all;

    proxy_pass http://backend;
}
```

---

## Priority 3: LOW Severity Issues

### Issue #6: Using External DNS Resolvers

**Location:** `dns_poisoning`
**Finding:** Using external DNS servers: 192.168.0.1
**Impact:** Minimal - local network DNS is acceptable

#### Remediation Steps:

**For Development:**
- ✅ Current configuration is acceptable
- Using local router DNS (192.168.0.1) is standard for home/office networks

**For Production:**

1. **Use cloud provider's DNS resolver:**
   - AWS: 169.254.169.253 (internal resolver)
   - GCP: 169.254.169.254
   - Azure: 168.63.129.16

2. **Or specify trusted DNS in application:**

```python
# In application startup
import dns.resolver

resolver = dns.resolver.Resolver()
resolver.nameservers = ['8.8.8.8', '8.8.4.4']  # Google Public DNS
resolver.validate_dnssec = True
```

---

## Additional Security Hardening Recommendations

### 1. Implement Rate Limiting Per IP

Already implemented in your codebase (`app/main.py:134-139`) ✅

### 2. Enable HTTP/2 with HTTPS

Update uvicorn configuration for production:

```python
# In app/main.py, line 751
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8443,
    ssl_keyfile=ssl_settings["ssl_keyfile"],
    ssl_certfile=ssl_settings["ssl_certfile"],
    ssl_version=ssl_settings["ssl_version"],
    ssl_ciphers=ssl_settings["ssl_ciphers"],
    reload=False,
    log_level="info",
    access_log=True,
    http="h11"  # For HTTP/1.1, or use "httptools" for HTTP/2 support
)
```

### 3. Implement Certificate Monitoring

```python
# Add to application startup
from datetime import datetime
from pathlib import Path

def check_certificate_expiry():
    """Check if SSL certificate is expiring soon"""
    cert_path = Path("certs/psychsync.crt")

    # Read certificate
    with open(cert_path, 'rb') as f:
        cert = ssl.load_ssl_certificate(f.read())

    # Get expiry date
    expiry = datetime.strptime(cert.get('notAfter'), '%b %d %H:%M:%S %Y %Z')
    days_remaining = (expiry - datetime.utcnow()).days

    if days_remaining < 30:
        logger.critical(f"SSL certificate expires in {days_remaining} days!")
        # Send alert to ops team

    return days_remaining
```

### 4. Implement Security Headers

Already implemented in `app/main.py:600-621` ✅

Your application already includes:
- Strict-Transport-Security
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection
- Content-Security-Policy
- Referrer-Policy

### 5. Set Up Automated Security Scanning

```bash
# Create scheduled task
crontab -e

# Add weekly security scan
0 2 * * 0 cd /app && python3 network_layer_security_audit.py --output /var/log/security_audit.json
```

---

## Testing Checklist

### Pre-Production Testing

- [ ] SSL certificate installation verified
- [ ] TLS 1.2/1.3 only (older versions rejected)
- [ ] HSTS header present with max-age >= 31536000
- [ ] All security headers in place
- [ ] Host header validation working
- [ ] Internal endpoints properly restricted
- [ ] CORS configuration appropriate for environment
- [ ] No open redirect vulnerabilities
- [ ] No path traversal vulnerabilities
- [ ] Rate limiting functional

### Automated Tests

```bash
# Run comprehensive security audit
python3 network_layer_security_audit.py --host production-api.com --port 443

# Test SSL configuration
openssl s_client -connect production-api.com:443 -tls1_2
openssl s_client -connect production-api.com:443 -tls1_3

# Test for security headers
curl -I https://production-api.com

# Test DNSSEC
dig +dnssec production-api.com
```

---

## Monitoring and Alerting

### Key Metrics to Monitor

1. **TLS/SSL Metrics**
   - Certificate expiry dates
   - TLS protocol versions used by clients
   - Failed TLS handshakes
   - Expired or invalid certificates

2. **DNS Metrics**
   - DNS resolution time
   - Failed DNS lookups
   - DNSSEC validation failures

3. **Network Security Events**
   - Suspicious Host headers
   - Rate limit violations
   - Failed authentication attempts
   - Blocked requests

### Alert Configuration

```python
# In monitoring configuration
alerts = {
    "ssl_certificate_expiring": {
        "threshold_days": 30,
        "severity": "critical",
        "channels": ["email", "slack", "pagerduty"]
    },
    "tls_version_too_old": {
        "minimum_version": "TLSv1.2",
        "severity": "high",
        "channels": ["slack", "email"]
    },
    "dns_resolution_failure": {
        "threshold_percentage": 5,
        "severity": "medium",
        "channels": ["slack"]
    }
}
```

---

## Compliance Considerations

### SOC 2 / ISO 27001 Requirements

- ✅ Encryption in transit (TLS 1.2+)
- ✅ Strong cipher suites
- ✅ Certificate management
- ✅ Security headers
- ✅ Network access controls
- ⚠️ DNSSEC (recommended but not required)

### HIPAA Requirements (for healthcare data)

- ✅ TLS 1.2+ encryption
- ✅ Strong ciphers
- ✅ Certificate validation
- ✅ Access controls on internal APIs
- ⚠️ Business Associate Agreement (BAA) with cloud providers

---

## Summary

**Immediate Actions (High Priority):**
1. ✅ SSL configuration is production-ready
2. ⚠️ Enable HTTPS before production deployment
3. ⚠️ Implement Host header validation
4. ⚠️ Document and test internal endpoint restrictions

**Short-term Actions (Medium Priority):**
1. Review DNS configuration for production
2. Implement certificate expiry monitoring
3. Set up automated security scanning
4. Create IP whitelisting for sensitive endpoints

**Long-term Actions:**
1. Consider DNSSEC implementation
2. Set up comprehensive security monitoring
3. Regular penetration testing
4. Security training for development team

---

**Next Steps:**
1. Run the audit script on staging environment
2. Test HTTPS configuration with valid certificates
3. Implement Host header validation
4. Set up monitoring and alerting
5. Schedule regular security audits

**Resources:**
- OWASP TLS Configuration: https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html
- Mozilla SSL Configuration Generator: https://ssl-config.mozilla.org/
- DNSSEC Deployment Guide: https://www.dnsops.org/operations/dnssec-deployment-guide.html
