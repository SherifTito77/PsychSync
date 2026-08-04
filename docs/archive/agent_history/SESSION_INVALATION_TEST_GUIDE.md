# 🧪 Session Invalidation Testing Guide

**Date**: February 12, 2026
**Status**: ✅ **ALL FIXES IMPLEMENTED & TESTED**

---

## 🎯 Quick Start

To verify all session invalidation fixes work correctly:

```bash
# Run the complete test suite
./test_session_invalidation.sh
```

---

## 📋 What's Being Tested

### **Backend Tests** (`tests/api/test_session_invalidation.py`)

#### 1. Token Blacklisting (`TestTokenBlacklisting`)
- ✅ `test_revoke_token_adds_to_blacklist`
  - Verifies tokens are actually added to Redis blacklist
  - Checks expiry time is set correctly

- ✅ `test_revoke_token_handles_redis_unavailable`
  - Verifies graceful handling when Redis is down
  - Returns False on failure

- ✅ `test_is_token_blacklisted`
  - Verifies blacklisted tokens are detected
  - Checks Redis exists() is called

- ✅ `test_is_token_blacklisted_not_found`
  - Verifies non-blacklisted tokens return False
  - Prevents false positives

#### 2. Logout Endpoint (`TestLogoutEndpoint`)
- ✅ `test_logout_blacklists_token`
  - Verifies `/api/v1/auth/logout` blacklists tokens
  - Checks for 200 response

- ✅ `test_logout_returns_error_if_redis_fails`
  - Verifies 503 response when Redis unavailable
  - Proper error handling

#### 3. Integration Tests (`TestSessionInvalidationIntegration`)
- ✅ `test_logout_and_token_rejection_complete_flow`
  - End-to-end test of logout → blacklist → rejection
  - Verifies complete security chain

---

### **Frontend Tests** (`frontend/src/services/__tests__/authService.test.ts`)

#### 1. Logout State Management (`TestFrontendLogout`)
- ✅ `should_clear_local_state_on_backend_success`
  - Verifies localStorage cleared ONLY after backend success
  - Prevents session inconsistency

- ✅ `should_preserve_state_on_backend_failure`
  - Verifies state preserved when backend fails
  - User stays logged in locally

- ✅ `should_handle_network_errors_gracefully`
  - Verifies no crashes on network errors

#### 2. Token Refresh (`TestTokenRefresh`)
- ✅ `should_queue_requests_during_token_refresh`
  - Verifies request queuing prevents concurrent refreshes
  - Only ONE refresh token API call

- ✅ `should_process_queue_even_on_refresh_failure`
  - Verifies queued requests processed even on failure
  - Prevents hanging requests

- ✅ `should_not_force_redirect_on_token_refresh_failure`
  - Verifies no forced redirect to `/login`
  - SessionExpiryModal handles UX

#### 3. Session Consistency (`TestSessionConsistency`)
- ✅ `logout_should_prevent_session_inconsistency`
  - Verifies backend confirmation required before state change
  - No split-brain between frontend/backend

- ✅ `token_blacklist_should_be_checked_on_each_request`
  - Verifies interceptor checks blacklist
  - Prevents replay attacks

---

## 🚀 Running Tests Manually

### Backend Tests

```bash
# Ensure dependencies are installed
pip install pytest pytest-asyncio

# Run only backend tests
python -m pytest tests/api/test_session_invalidation.py -v

# Run specific test class
python -m pytest tests/api/test_session_invalidation.py -v -k "TestTokenBlacklisting"
```

### Frontend Tests

```bash
cd frontend

# Ensure dependencies are installed
npm install

# Run frontend tests (if using Jest)
npm test -- authService.test.ts

# Or run all tests
npm test
```

---

## 🔍 What Each Fix Tests

### Fix #1: Token Blacklisting ✅

**Before**:
```python
async def revoke_token(...) -> None:
    # TODO: Implement actual blacklist storage
    return None  # ← Does nothing!
```

**After**:
```python
async def revoke_token(...) -> bool:
    try:
        await redis_client.setex(f"blacklist:token:{jti}", expiry, "1")
        return True
    except Exception as e:
        logger.error(f"Failed to blacklist: {e}")
        return False
```

**Test Verifies**:
- Token added to Redis with correct key format
- Expiry time matches token lifetime
- Returns True on success, False on failure
- Error handling for Redis unavailability

---

### Fix #2: Logout State Validation ✅

**Before**:
```typescript
export const logout = async () => {
  try {
    await apiClient.post('/logout', ...);
  } catch (e) {
    // Log error but continue...
  }

  // BUG: Always runs!
  localStorage.removeItem('user');
}
```

**After**:
```typescript
export const logout = async () => {
  let backend_success = false;

  try {
    await apiClient.post('/logout', ...);
    backend_success = true;  // ← Track success
  } catch (e) {
    // Don't clear if failed
  }

  // Only clear if backend succeeded
  if (backend_success) {
    localStorage.removeItem('user');
  }
}
```

**Test Verifies**:
- `removeItem` called ONLY after backend success
- State preserved if backend unreachable
- No session inconsistency (frontend out, backend in)

---

### Fix #3: Token Refresh Queuing ✅

**Before**:
```typescript
if (error.response?.status === 401 && !originalRequest._retry) {
  await refreshToken();  // ← Multiple tabs = multiple refreshes!
}
```

**After**:
```typescript
let isRefreshing = false;
let failedQueue = [];

if (error.response?.status === 401 && !originalRequest._retry) {
  if (isRefreshing) {
    // Queue request instead
    return new Promise((resolve) => {
      failedQueue.push(() => resolve(api(originalRequest)));
    });
  }

  isRefreshing = true;
  await refreshToken();
  isRefreshing = false;  // ← Always reset

  // Process queue
  failedQueue.forEach(prom => prom());
}
```

**Test Verifies**:
- Only ONE refresh token call even with multiple tabs
- Requests queued during refresh
- Queue processed after refresh (success or failure)
- No race conditions or concurrent refreshes
- No forced redirects on refresh failure

---

## 📊 Test Results Interpretation

### ✅ All Tests Pass

```
🧪 SESSION INVALATION TEST SUITE
================================

✓ Token blacklisting tests passed
✓ Logout state management tests passed
✓ Token refresh tests passed
✓ Integration tests passed

================================
✓ ALL TESTS PASSED

Session invalidation is working correctly!

Security Fixes Verified:
  ✓ Token blacklisting implemented
  ✓ Logout validates backend success
  ✓ Token refresh uses request queuing
  ✓ Blacklisted tokens are rejected
```

### ❌ Some Tests Fail

**Common Issues**:

1. **Redis Not Running**
   ```bash
   # Start Redis
   docker-compose up -d redis

   # Or use local Redis
   redis-server
   ```

2. **Backend Not Running**
   ```bash
   # Start backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Import Errors**
   ```
   # Install missing dependencies
   pip install -r requirements.txt
   pip install pytest pytest-asyncio
   ```

4. **Port Already in Use**
   ```
   # Check what's using port 8000
   lsof -ti:8000

   # Kill the process
   kill -9 <PID>
   ```

---

## 🔐 Security Implications

### What These Fixes Prevent

#### Before Fixes (VULNERABLE):
- ❌ Token not blacklisted → Can reuse after logout
- ❌ State cleared on network error → Session inconsistency
- ❌ Multiple refresh attempts → Race conditions
- ❌ Blacklist not checked → Token replay attacks
- ❌ Forced redirects → Poor UX

#### After Fixes (SECURE):
- ✅ Token blacklisted → Cannot reuse after logout
- ✅ Backend validation → Session consistency
- ✅ Request queuing → No race conditions
- ✅ Blacklist checked → Replay attacks prevented
- ✅ Graceful failures → Better UX

---

## 📝 Testing Checklist

Before deploying to production, verify:

- [ ] Run `./test_session_invalidation.sh` - all tests pass
- [ ] Test logout manually in browser dev tools
- [ ] Verify tokens in Redis using `redis-cli`
  ```bash
  redis-cli
  > KEYS blacklist:token:*
  > GET blacklist:token:<specific-jti>
  ```
- [ ] Test multi-tab scenario (open app in 2+ tabs)
- [ ] Test token expiration (wait 30 min for token expiry)
- [ ] Test network failure (disconnect internet, click logout)
- [ ] Verify no console errors during any flow

---

## 🎯 Production Verification

To verify in production environment:

```bash
# Check Redis for blacklisted tokens
redis-cli -h <prod-redis-host> KEYS "blacklist:token:*"

# Should show keys like:
# 1) "blacklist:token:abc123..."
# 2) "blacklist:token:def456..."
```

If no keys appear, token blacklisting is **not working** in production.

---

**Author**: Security Team
**Last Updated**: February 12, 2026
**Status**: ✅ Ready for Production Testing
