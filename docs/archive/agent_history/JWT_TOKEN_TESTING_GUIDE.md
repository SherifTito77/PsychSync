# 🔐 JWT Token Testing Comprehensive Guide

**Created:** December 2, 2025
**Version:** 1.0
**Coverage:** Complete JWT token security and behavior testing for PsychSync API

---

## 📋 Executive Summary

This guide provides comprehensive testing strategies for JWT token behavior, covering expiration, refresh mechanisms, invalid token handling, and security validation. The testing suite ensures robust token management and identifies potential security vulnerabilities.

### **Key Testing Areas**
- **Token Expiration:** Validates proper expiration handling and time-based security
- **Refresh Token Flow:** Tests secure token refresh and reuse prevention
- **Invalid Token Security:** Ensures proper rejection of malformed or tampered tokens
- **Concurrent Usage:** Validates system behavior under concurrent token requests
- **Security Features:** Tests blacklisting, leakage prevention, and rate limiting

---

## 🏗️ JWT Implementation Analysis

### **PsychSync JWT Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Login   │ -> │ Token Generation│ -> │ Token Storage   │
│                 │    │ • Access Token  │    │ • Client Side   │
│                 │    │ • Refresh Token │    │ • Server Cache  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐
                       │ Token Validation│
                       │ • Signature     │
                       │ • Expiration    │
                       │ • Blacklist     │
                       └─────────────────┘
```

### **Token Specifications**

#### **Access Token**
- **Algorithm:** HS256 (configurable)
- **Lifetime:** 30 minutes (1800 seconds)
- **Claims:** sub, exp, iat, type, jti, version
- **Security:** Device fingerprinting, IP tracking

#### **Refresh Token**
- **Algorithm:** HS256
- **Lifetime:** 7 days (604800 seconds)
- **Usage:** Single-use (blacklisted after use)
- **Claims:** sub, exp, iat, type

#### **Security Features**
- **Token Blacklisting:** Redis-based invalidation
- **Device Fingerprinting:** Session binding
- **Emergency Revocation:** Mass token invalidation
- **Rate Limiting:** Brute force protection
- **Audit Logging:** Comprehensive security events

---

## 🧪 Testing Framework Overview

### **Test Categories**

#### **1. Functional Testing**
```python
# Purpose: Validate JWT token behavior
# Tools: Python test suite, Postman collection
# Coverage: All token operations and edge cases
```

#### **2. Security Testing**
```python
# Purpose: Identify security vulnerabilities
# Tools: Custom attack scripts, malformed tokens
# Coverage: Token tampering, leakage, replay attacks
```

#### **3. Performance Testing**
```python
# Purpose: Measure token operation performance
# Tools: Load testing, concurrent requests
# Coverage: Response times, throughput, resource usage
```

#### **4. Compliance Testing**
```python
# Purpose: Ensure security standards compliance
# Tools: OWASP JWT guidelines, RFC 7519
# Coverage: Token structure, algorithm security, claim validation
```

---

## 🚀 Quick Start Guide

### **Prerequisites**
```bash
# Ensure API server is running
curl http://localhost:8000/api/v1/health

# Install test dependencies
pip install aiohttp requests jwt

# Verify test user exists
# Email: admin@example.com
# Password: Admin@12345
```

### **Run All Tests**
```bash
# Comprehensive JWT testing
python jwt_token_test_suite.py --all

# With custom output
python jwt_token_test_suite.py --all --output jwt_test_results.json
```

### **Postman Collection Testing**
```bash
# Run Postman collection programmatically
python postman_test_runner.py \
    --collection postman_jwt_token_collection.json \
    --suite "JWT Token Tests" \
    --report json
```

### **Specific Test Categories**
```bash
# Test only expiration scenarios
python jwt_token_test_suite.py --expiration

# Test refresh token functionality
python jwt_token_test_suite.py --refresh

# Test security scenarios
python jwt_token_test_suite.py --security

# Test concurrent usage
python jwt_token_test_suite.py --concurrent
```

---

## 📱 Test Scenarios Detailed

### **Category 1: Token Expiration Testing**

#### **1.1 Fresh Token Validation**
```python
# Test: Newly issued token should work
# Expected: 200 OK
# Validation: Token structure, claims, expiration time
```

**Test Plan:**
- ✅ Generate fresh access token
- ✅ Verify token structure (3 parts, valid base64)
- ✅ Decode and validate claims (sub, exp, iat, type)
- ✅ Confirm expiration time (~30 minutes)
- ✅ Test token works with protected endpoint

#### **1.2 Token Near Expiration**
```python
# Test: Token close to expiration
# Expected: Should work until exact expiration
# Edge Case: Millisecond precision expiration
```

**Test Plan:**
- ✅ Monitor token as it approaches expiration
- ✅ Test requests in final seconds
- ✅ Verify exact expiration behavior
- ✅ Confirm proper 401 response after expiration

#### **1.3 Expired Token Rejection**
```python
# Test: Explicitly expired token
# Expected: 401 Unauthorized
# Security: No partial access after expiration
```

**Test Plan:**
- ✅ Create token with past expiration
- ✅ Attempt protected resource access
- ✅ Verify 401 response with appropriate error
- ✅ Ensure no data leakage in error response

### **Category 2: Refresh Token Testing**

#### **2.1 Refresh Token Structure**
```python
# Test: Refresh token format and claims
# Expected: Valid JWT with refresh type
# Lifetime: ~7 days from issuance
```

**Test Plan:**
- ✅ Verify refresh token structure
- ✅ Decode and validate claims
- ✅ Confirm longer lifetime than access token
- ✅ Validate token type: "refresh"

#### **2.2 Token Refresh Flow**
```python
# Test: Use refresh token to get new access token
# Expected: 200 OK with new access token
# Security: New token should be different
```

**Test Plan:**
- ✅ Send refresh token to refresh endpoint
- ✅ Verify new access token returned
- ✅ Confirm new token is different
- ✅ Validate new token works for authentication

#### **2.3 Refresh Token Reuse Prevention**
```python
# Test: Prevent refresh token reuse
# Expected: 401 Unauthorized on second use
# Security: Single-use refresh tokens
```

**Test Plan:**
- ✅ Successfully refresh token once
- ✅ Attempt to reuse same refresh token
- ✅ Verify second attempt is rejected
- ✅ Confirm token is blacklisted after use

#### **2.4 Invalid Refresh Token**
```python
# Test: Reject malformed/invalid refresh tokens
# Expected: 401/403 Unauthorized
# Security: No token leakage in errors
```

**Test Plan:**
- ✅ Test with malformed tokens
- ✅ Test with wrong signatures
- ✅ Test with expired refresh tokens
- ✅ Verify proper error handling

### **Category 3: Invalid Token Security**

#### **3.1 Missing Authorization**
```python
# Test: Request without Authorization header
# Expected: 401 Unauthorized
# Security: WWW-Authenticate header present
```

**Test Plan:**
- ✅ Make request without auth header
- ✅ Verify 401 response
- ✅ Check WWW-Authenticate header
- ✅ Confirm no protected data access

#### **3.2 Invalid Token Format**
```python
# Test: Malformed JWT tokens
# Expected: 401 Unauthorized
# Security: Reject all malformed formats
```

**Test Plan:**
- ✅ Test invalid formats (not 3 parts)
- ✅ Test non-base64 encoded parts
- ✅ Test missing claims
- ✅ Verify consistent rejection

#### **3.3 Wrong Token Signature**
```python
# Test: Token with incorrect signature
# Expected: 401 Unauthorized
# Security: Cryptographic validation
```

**Test Plan:**
- ✅ Create token with valid payload, wrong signature
- ✅ Verify signature validation failure
- ✅ Ensure no partial access granted
- ✅ Test timing attack resistance

#### **3.4 Token Tampering Detection**
```python
# Test: Modified token payload
# Expected: 401 Unauthorized
# Security: Integrity verification
```

**Test Plan:**
- ✅ Modify valid token payload
- ✅ Verify tampering detection
- ✅ Test boundary conditions
- ✅ Ensure security logging

### **Category 4: Token Security Features**

#### **4.1 Token Blacklisting**
```python
# Test: Token invalidation after logout
# Expected: 401 Unauthorized after logout
# Security: Immediate token revocation
```

**Test Plan:**
- ✅ Login and get access token
- ✅ Use token successfully
- ✅ Logout to blacklist token
- ✅ Verify token is rejected after logout

#### **4.2 Token Leakage Prevention**
```python
# Test: No token leakage in error responses
# Expected: No sensitive data in errors
# Security: Information disclosure prevention
```

**Test Plan:**
- ✅ Trigger authentication errors
- ✅ Check error responses for token data
- ✅ Verify no JWT secrets leaked
- ✅ Test security headers presence

#### **4.3 Concurrent Token Usage**
```python
# Test: Multiple requests with same token
# Expected: Proper handling of concurrent access
# Performance: No race conditions
```

**Test Plan:**
- ✅ Send 10+ concurrent requests with same token
- ✅ Verify all succeed or properly rate-limited
- ✅ Test refresh token under concurrency
- ✅ Monitor system stability

#### **4.4 Rate Limiting Integration**
```python
# Test: Token validation respects rate limits
# Expected: 429 Too Many Requests when exceeded
# Security: Brute force protection
```

**Test Plan:**
- ✅ Rapid authentication attempts
- ✅ Token validation rate limits
- ✅ Verify rate limiting headers
- ✅ Test exponential backoff

---

## 📊 Test Results Analysis

### **Success Criteria**

#### **Functional Requirements**
- ✅ Fresh tokens work for authentication
- ✅ Expired tokens are properly rejected
- ✅ Refresh token flow works correctly
- ✅ Invalid tokens are consistently rejected

#### **Security Requirements**
- ✅ Token tampering is detected and blocked
- ✅ Token blacklisting works immediately
- ✅ No token leakage in any responses
- ✅ Rate limiting prevents brute force attacks

#### **Performance Requirements**
- ✅ Token validation under 100ms average
- ✅ Concurrent requests handled properly
- ✅ System scales with multiple users
- ✅ Memory usage remains reasonable

### **Security Analysis Checklist**

#### **Token Structure**
- [ ] Proper JWT format with 3 parts
- [ ] Secure algorithm (HS256/RS256)
- [ ] Required claims present (sub, exp, iat, type)
- [ ] No sensitive data in payload

#### **Token Lifecycle**
- [ ] Appropriate expiration times
- [ ] Secure refresh token mechanism
- [ ] Proper token invalidation
- [ ] No token reuse vulnerabilities

#### **Validation Security**
- [ ] Signature verification enabled
- [ ] Expiration strictly enforced
- [ ] Invalid formats rejected
- [ ] Tampering attempts blocked

#### **Error Handling**
- [ ] No token information leaked
- [ ] Consistent error responses
- [ ] Proper HTTP status codes
- [ ] Security headers present

---

## 🔧 Configuration Guide

### **Test Environment Setup**
```bash
# Environment variables
export JWT_TEST_BASE_URL="http://localhost:8000"
export JWT_TEST_USER="admin@example.com"
export JWT_TEST_PASSWORD="Admin@12345"

# Redis for token blacklisting (if used)
export REDIS_URL="redis://localhost:6379/0"

# JWT Configuration (verify these match your setup)
export JWT_ALGORITHM="HS256"
export ACCESS_TOKEN_LIFETIME=1800  # 30 minutes
export REFRESH_TOKEN_LIFETIME=604800  # 7 days
```

### **Performance Benchmarks**
```python
# Expected performance metrics
JWT_VALIDATION_TIME_MAX = 100  # ms
TOKEN_GENERATION_TIME_MAX = 200  # ms
REFRESH_TOKEN_TIME_MAX = 300  # ms
CONCURRENT_REQUESTS_MAX = 50  # simultaneous
```

### **Security Validation Checklist**
```python
# Security requirements to validate
TOKEN_ENTROPY_MIN = 128  # bits
SIGNATURE_ALGORITHM_SECURE = True
BLACKLIST_IMPLEMENTED = True
RATE_LIMITING_ENABLED = True
AUDIT_LOGGING_ENABLED = True
```

---

## 🚨 Common Issues & Solutions

### **Test Failures**

#### **Authentication Issues**
```python
# Problem: Tests can't authenticate
# Solution: Verify test user exists and credentials are correct

# Check user exists
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@example.com" \
  -d "password=Admin@12345"

# Create test user if needed
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin@12345"}'
```

#### **Token Parsing Errors**
```python
# Problem: JWT token structure doesn't match expectations
# Solution: Check your JWT configuration and token format

# Decode a sample token
import jwt
import base64

token = "your.jwt.token"
parts = token.split('.')
payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
print(payload)
```

#### **Rate Limiting Interference**
```python
# Problem: Tests being rate limited
# Solution: Adjust rate limits or use different test users

# Check current rate limits
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/users/me
```

#### **Redis Connection Issues**
```python
# Problem: Token blacklisting not working
# Solution: Verify Redis is running and accessible

# Check Redis connection
redis-cli ping
```

### **Performance Issues**

#### **Slow Token Validation**
```python
# Problem: Token validation taking too long
# Causes: Complex signatures, database lookups, network latency

# Monitor token validation time
import time
start = time.time()
# validate token
end = time.time()
print(f"Validation took: {end - start:.3f}s")
```

#### **Memory Leaks**
```python
# Problem: Memory usage increasing during tests
# Cause: Token caching not properly managed

# Monitor memory usage during tests
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

### **Security Issues**

#### **Token Leakage**
```python
# Problem: Tokens appearing in error messages
# Solution: Review error handling and logging

# Check for token leakage
grep -r "access_token\|refresh_token\|jwt" error_logs/
```

#### **Weak Algorithms**
```python
# Problem: Using weak JWT algorithms
# Solution: Configure secure algorithms

# Check token algorithm
decoded = jwt.decode(token, options={"verify_signature": False})
print(f"Algorithm: {decoded.get('alg')}")
```

---

## 📈 Advanced Testing Scenarios

### **1. Stress Testing**
```python
# High-volume token generation and validation
async def stress_test_tokens(concurrent_users=100, requests_per_user=50):
    """Stress test JWT token system under load"""
    tasks = []
    for user_id in range(concurrent_users):
        for request_id in range(requests_per_user):
            task = test_user_token_flow(user_id, request_id)
            tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return analyze_results(results)
```

### **2. Security Penetration Testing**
```python
# Attempt to bypass token security
async def security_penetration_test():
    """Test for JWT security vulnerabilities"""

    # Test common JWT attacks
    await test_none_algorithm()
    await test_algorithm_confusion()
    await test_key_confusion()
    await test_timing_attacks()
    await test_token_replay_attacks()
```

### **3. Compliance Validation**
```python
# Validate against security standards
def validate_jwt_compliance():
    """Check JWT implementation against security standards"""

    # OWASP JWT Security Checklist
    # RFC 7519 Compliance
    # NIST Guidelines
    # Industry Best Practices
    pass
```

### **4. Race Condition Testing**
```python
# Test for race conditions in token handling
async def race_condition_test():
    """Test concurrent token operations for race conditions"""

    # Simultaneous token refresh
    # Concurrent logout operations
    # Race conditions in blacklisting
    pass
```

---

## 📝 Test Report Template

### **Executive Summary**
```markdown
## JWT Token Security Assessment Report

**Date:** [Test Date]
**Tester:** [Tester Name]
**Target:** [API URL]

### Overall Security Posture
- **Risk Level:** [Low/Medium/High/Critical]
- **Compliance Score:** [X/100]
- **Critical Issues:** [Number]
- **Recommendations:** [Number]
```

### **Technical Findings**
```markdown
### Token Configuration Analysis
- **Algorithm:** [HS256/RS256/Other]
- **Token Lifetime:** [Access/Refresh durations]
- **Security Features:** [Blacklisting, Rate limiting, etc.]

### Vulnerability Assessment
1. **[Vulnerability Name]**
   - **Severity:** [Critical/High/Medium/Low]
   - **Description:** [Detailed description]
   - **Impact:** [Business/Technical impact]
   - **Remediation:** [Fix recommendations]
```

### **Performance Metrics**
```markdown
### Token Operation Performance
- **Validation Time:** [Average] ms
- **Generation Time:** [Average] ms
- **Refresh Time:** [Average] ms
- **Concurrent Users:** [Maximum tested]
- **Throughput:** [Requests/second]
```

---

**🎉 JWT Token Testing Complete!**

This comprehensive testing suite ensures your PsychSync JWT implementation is secure, performant, and compliant with industry best practices. Regular testing helps maintain security posture and identifies potential vulnerabilities before they can be exploited.

**Happy Testing!** 🚀
