# 🚀 Rate Limiting & Throttling Test Scenarios

**Created:** December 2, 2025
**Version:** 1.0
**Scope:** Comprehensive rate limiting testing for PsychSync API

---

## 📊 Rate Limiting Implementation Analysis

Based on code analysis, PsychSync implements a **multi-layered rate limiting system**:

### **🔧 Rate Limiting Components**

1. **Token Bucket Algorithm** (`app/middleware/rate_limiter.py`)
   - Smooth rate limiting with burst capacity
   - Redis backend for distributed systems
   - Configurable limits per endpoint
   - Rate limit headers in responses

2. **Tier-Based Limiting** (`app/services/rate_limiter_service.py`)
   - User tier limits (Anonymous, Basic, Premium, Enterprise, Admin)
   - Endpoint-specific restrictions
   - Burst protection
   - Sliding window implementation

3. **Auth-Specific Limiting** (`app/middleware/auth_rate_limiter.py`)
   - Progressive rate limiting for auth endpoints
   - Failed attempt penalties
   - IP-based and user-based tracking
   - Brute force protection

4. **Redis-Based Storage** (`app/core/rate_limiting.py`)
   - Sliding window algorithm
   - Distributed support
   - Progressive penalties
   - Automatic cleanup

### **📋 Current Rate Limits**

#### **User Tiers**
- **Anonymous:** 50/min, 200/hour, 1000/day (20 burst)
- **Basic:** 200/min, 1000/hour, 10000/day (100 burst)
- **Premium:** 500/min, 2500/hour, 50000/day (500 burst)
- **Enterprise:** 1000/min, 10000/hour, 100000/day (1000 burst)
- **Admin:** 2000/min, 20000/hour, 200000/day (2000 burst)

#### **Auth Endpoints**
- **Login:** 20/hour, progressive penalties on failures
- **Register:** 5/hour
- **Password Reset:** 3/hour
- **Token Refresh:** 100/hour
- **2FA:** 10/hour

---

## 🧪 Comprehensive Test Scenarios

### **Category 1: Basic Rate Limiting Validation**

#### **1.1 Anonymous User Rate Limits**
```bash
# Test: Anonymous user basic API access
# Expected: 50 requests/minute limit
# Endpoint: GET /api/v1/health (public endpoint)
```

**Test Plan:**
- ✅ Send 50 requests within 1 minute → Should all succeed (200)
- 🚫 Send 51st request → Should be rate limited (429)
- 🕒 Wait 60 seconds → 52nd request should succeed

#### **1.2 Authenticated User Rate Limits**
```bash
# Test: Basic tier user API access
# Expected: 200 requests/minute limit
# Prerequisites: Valid authentication token
```

**Test Plan:**
- ✅ Send 200 requests within 1 minute → Should all succeed
- 🚫 Send 201st request → Should be rate limited (429)
- 🔄 Test with different endpoint types (GET, POST, PUT, DELETE)

#### **1.3 Premium Tier Rate Limits**
```bash
# Test: Premium tier user API access
# Expected: 500 requests/minute limit
# Prerequisites: Premium user token
```

**Test Plan:**
- ✅ Send 500 requests within 1 minute → Should all succeed
- 🚫 Send 501st request → Should be rate limited (429)

---

### **Category 2: Authentication-Specific Rate Limiting**

#### **2.1 Login Rate Limiting**
```bash
# Test: Login endpoint rate limiting
# Expected: 20 attempts/hour (per IP)
# Progressive penalties on failures
```

**Test Plan:**
- ✅ Send 20 login attempts with valid credentials → Should succeed (2 per user max)
- 🚫 Send 21st login attempt → Should be rate limited (429)
- 🔄 Test failed login penalties:
  - 5 failed attempts → Limit should reduce progressively
  - Successful login after failures → May have increased penalty

#### **2.2 Registration Rate Limiting**
```bash
# Test: Registration endpoint rate limiting
# Expected: 5 attempts/hour (per IP)
```

**Test Plan:**
- ✅ Send 5 registration attempts with unique emails → Should succeed
- 🚫 Send 6th registration attempt → Should be rate limited (429)
- 🕒 Wait 1 hour → 6th attempt should succeed

#### **2.3 Password Reset Rate Limiting**
```bash
# Test: Password reset endpoint rate limiting
# Expected: 3 attempts/hour (per email)
```

**Test Plan:**
- ✅ Send 3 password reset requests → Should succeed
- 🚫 Send 4th password reset request → Should be rate limited (429)
- 🔄 Test with different emails vs same email

#### **2.4 Token Refresh Rate Limiting**
```bash
# Test: Token refresh endpoint rate limiting
# Expected: 100 attempts/hour (per user)
```

**Test Plan:**
- ✅ Send 100 token refresh requests → Should succeed
- 🚫 Send 101st token refresh request → Should be rate limited (429)
- 🔄 Test with invalid vs valid refresh tokens

---

### **Category 3: Burst Capacity Testing**

#### **3.1 Anonymous User Burst**
```bash
# Test: Anonymous user burst capacity
# Expected: 20 burst requests (from anonymous tier)
# Endpoint: Any public endpoint
```

**Test Plan:**
- ✅ Send 20 requests in 1 second → Should all succeed (burst capacity)
- 🚫 Send 21st request immediately → Should be rate limited
- 🕒 Wait for tokens to refill → Requests should succeed again

#### **3.2 Premium User Burst**
```bash
# Test: Premium user burst capacity
# Expected: 500 burst requests (from premium tier)
```

**Test Plan:**
- ✅ Send 500 requests in 1 second → Should all succeed (burst capacity)
- 🚫 Send 501st request → Should be rate limited
- ⚡ Measure response time under burst conditions

---

### **Category 4: Progressive Penalties Testing**

#### **4.1 Failed Login Penalties**
```bash
# Test: Progressive penalties on failed auth
# Expected: Rate limit decreases after failures
# Recovery: Gradual limit restoration
```

**Test Plan:**
- ❌ Send 10 failed login attempts → Rate limit should decrease
- 🔄 Attempt successful login → May face additional restrictions
- ⏰ Wait penalty duration → Limits should gradually restore
- 📈 Measure penalty decay over time

#### **4.2 IP-Based Penalties**
```bash
# Test: IP-based progressive penalties
# Expected: IP address gets blacklisted after repeated violations
```

**Test Plan:**
- ❌ Trigger rate limit violations from multiple user accounts
- 🚫 Observe increasing penalties for the IP
- 🔄 Test if other users from same IP are affected
- 🕒 Test IP recovery after penalty period

---

### **Category 5: Distributed Rate Limiting**

#### **5.1 Multi-Instance Consistency**
```bash
# Test: Rate limiting across multiple API instances
# Expected: Consistent limits across distributed system
# Prerequisites: Multiple API instances behind load balancer
```

**Test Plan:**
- 🌐 Send requests to different API instances
- 📊 Verify rate limits are synchronized
- 🔄 Test failover scenarios
- ⚡ Measure consistency latency

#### **5.2 Redis Backend Resilience**
```bash
# Test: Rate limiting behavior during Redis issues
# Expected: Graceful degradation or fail-open
```

**Test Plan:**
- 🔥 Test with Redis unavailable → System behavior
- ⚡ Test Redis connection drops during active limiting
- 🔄 Test Redis replication scenarios
- 📈 Measure fallback behavior

---

### **Category 6: Endpoint-Specific Rate Limits**

#### **6.1 Assessment Creation Rate Limits**
```bash
# Test: Assessment endpoint specific limits
# Expected: Lower limits for resource-intensive operations
# Endpoint: POST /api/v1/assessments
```

**Test Plan:**
- 📊 Test assessment creation limits (different from general API)
- 💾 Test large assessment payload rate limits
- 🔄 Test concurrent assessment creation
- ⚡ Measure performance under limit

#### **6.2 Data Export Rate Limits**
```bash
# Test: Data export endpoint specific limits
# Expected: Stricter limits for expensive operations
# Endpoint: GET /api/v1/export
```

**Test Plan:**
- 📊 Test data export limits (stricter than general API)
- 💾 Test large dataset export rate limits
- ⏱️ Test export timeout interactions
- 🔄 Test concurrent export requests

#### **6.3 Email Sending Rate Limits**
```bash
# Test: Email endpoint specific limits
# Expected: Limits to prevent email spam
# Endpoint: POST /api/v1/send-email
```

**Test Plan:**
- 📧 Test email sending rate limits
- 🔄 Test email template limits
- 📊 Test bulk email sending limits
- ⚡ Measure email service integration under limits

---

### **Category 7: Edge Cases & Boundary Testing**

#### **7.1 Rapid Succession Requests**
```bash
# Test: Extremely rapid request succession
# Expected: Rate limiting should still work
# Test: Send requests with minimal delay (< 1ms)
```

**Test Plan:**
- ⚡ Send requests with < 1ms delay between requests
- 📊 Measure exact rate limit enforcement
- 🔄 Test system behavior under extreme load
- ⏱️ Test recovery after rapid burst

#### **7.2 Mixed Endpoint Requests**
```bash
# Test: Rate limiting across different endpoints
# Expected: Separate limits per endpoint type
# Test: Mix public, auth, and premium endpoints
```

**Test Plan:**
- 🔄 Mix requests across different endpoints
- 📊 Verify separate rate limiting per endpoint type
- 🧪 Test endpoint-specific rate limit isolation
- ⚡ Measure overall system capacity

#### **7.3 Concurrent User Testing**
```bash
# Test: Multiple users from same IP
# Expected: Per-user rate limiting (not per-IP)
# Test: 100 users from same IP address
```

**Test Plan:**
- 👥 Simulate 100 different users from same IP
- 📊 Verify per-user rate limiting works correctly
- 🚫 Test if one user's violations affect others
- 🔄 Test mixed anonymous/authenticated users

---

### **Category 8: Performance Under Load**

#### **8.1 Rate Limit Performance Impact**
```bash
# Test: Rate limiting performance under load
# Expected: Minimal performance impact when not rate limited
# Test: Measure response times with and without rate limiting
```

**Test Plan:**
- ⚡ Measure response times with rate limiting enabled
- ⚡ Measure response times with rate limiting disabled
- 📊 Compare performance impact
- 🔄 Test rate limiting overhead under load

#### **8.2 Memory Usage Testing**
```bash
# Test: Memory usage during rate limiting
# Expected: Efficient memory usage for rate limiting data
# Test: Monitor Redis memory usage
```

**Test Plan:**
- 💾 Monitor Redis memory usage during tests
- 📊 Track rate limiting key storage
- 🧪 Test automatic key expiration
- 🔄 Test memory cleanup efficiency

#### **8.3 CPU Usage Testing**
```bash
# Test: CPU usage during rate limiting
# Expected: Efficient CPU usage for rate limiting calculations
# Test: Monitor CPU usage during burst traffic
```

**Test Plan:**
- 💻 Monitor CPU usage during burst requests
- 📊 Track rate limiting algorithm efficiency
- 🧪 Test sliding window calculation overhead
- 🔄 Compare different algorithm performance

---

## 🧪 Test Execution Plan

### **Phase 1: Basic Validation (1 hour)**
1. Anonymous user rate limits
2. Authenticated user rate limits
3. Premium tier rate limits
4. Basic auth endpoint limits

### **Phase 2: Advanced Scenarios (2 hours)**
1. Burst capacity testing
2. Progressive penalty testing
3. Mixed endpoint testing
4. Concurrent user testing

### **Phase 3: Edge Cases (1 hour)**
1. Rapid succession requests
2. Distributed consistency
3. Redis resilience testing
4. Performance impact analysis

### **Phase 4: Load Testing (2 hours)**
1. High-volume rate limit testing
2. Performance under load
3. Memory and CPU usage
4. System resilience testing

---

## 📊 Success Criteria

### **Functional Requirements**
- ✅ Rate limits enforced accurately
- ✅ Different tiers have appropriate limits
- ✅ Progressive penalties work correctly
- ✅ Rate limit headers included in responses

### **Performance Requirements**
- ✅ < 5ms overhead for rate limiting checks
- ✅ < 100MB Redis memory usage for 1000 active users
- ✅ < 10% CPU overhead under normal load
- ✅ Graceful degradation under Redis failures

### **Security Requirements**
- ✅ Brute force protection effective
- ✅ DDoS mitigation at application layer
- ✅ IP-based tracking works
- ✅ User-based isolation maintained

### **Reliability Requirements**
- ✅ Distributed consistency across instances
- ✅ Automatic key expiration and cleanup
- ✅ Graceful handling of Redis failures
- ✅ Monitoring and alerting capabilities

---

## 🔧 Test Implementation

### **Test Environment Setup**
```bash
# Redis configuration for testing
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### **Test Data Preparation**
```bash
# Create test users with different tiers
# Anonymous: No token required
# Basic: Standard user token
# Premium: Premium user token
# Enterprise: Enterprise user token
# Admin: Admin user token
```

### **Monitoring Setup**
```bash
# Monitor rate limiting metrics
- Redis key count and memory usage
- API response times
- Rate limit hit/miss ratios
- Error rates (429 responses)
```

---

## 📈 Expected Outcomes

### **Positive Results**
- Rate limiting protects against abuse
- Legitimate users have reasonable limits
- System remains responsive under load
- Fair resource allocation among users

### **Negative Results**
- Rate limiting too restrictive → User experience issues
- Rate limiting too lenient → Abuse potential
- Performance impact → System slowdown
- Inconsistent enforcement → Security gaps

### **Optimization Opportunities**
- Adjust rate limits based on testing results
- Implement adaptive rate limiting
- Optimize Redis usage and performance
- Enhance monitoring and alerting

---

**🎯 Ready for Implementation!**

This comprehensive test suite covers all aspects of the PsychSync rate limiting system. Execute the tests systematically to validate that your rate limiting implementation protects against abuse while maintaining good user experience.

**Happy Testing!** 🚀
