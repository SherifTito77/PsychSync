# Network Error Fix - Login Issues

**Date**: January 21, 2026
**Issue**: Network error when trying to login
**Status**: 🔍 **INVESTIGATING**

---

## 🚨 Problem Description

**User Report**: "still showing network error"

### Root Cause Analysis

**Issue 1: CSRF Protection Blocking Login**
The backend has CSRF protection enabled, but the frontend isn't getting a CSRF token before attempting login.

**Test Result**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@psychsync.test","password":"TestPassword123!"}'

# Response: {"detail":"CSRF token missing. Please reload the page."}
# HTTP Status: 403 Forbidden
```

**Issue 2: Preview Server Doesn't Have Proxy**
The user ran `npm run build && npm run preview` which:
- Starts preview server on port 4173
- Doesn't have proxy configuration to `/api` endpoints
- Tries to connect to IPv6 localhost (`::1:8000`) instead of IPv4
- Results in `ECONNREFUSED` errors

---

## 🔧 Solutions

### Solution 1: Use Development Server (RECOMMENDED)

**Why**: Dev server has proxy configuration that handles API requests correctly

**Steps**:
```bash
# Stop any running servers
pkill -f "vite"
pkill -f "npm.*preview"

# Start dev server
cd /Users/sheriftito/Downloads/psychsync
./dev.sh

# Or manually:
cd frontend
npm run dev
```

**Access**: http://localhost:5173

---

### Solution 2: Disable CSRF for Development (QUICK FIX)

**File**: `app/main.py:712`

**Change**:
```python
unified_security_config = SecurityConfig(
    # Feature toggles
    security_headers_enabled=True,
    csrf_protection_enabled=False,  # ❌ Disabled for development
    # ...
)
```

**Then restart backend**:
```bash
pkill -f uvicorn
./dev.sh
```

---

### Solution 3: Fix CSRF Implementation (PROPER FIX)

The frontend needs to:
1. Fetch CSRF token on page load
2. Include it in login request
3. Handle token refresh

**Frontend Changes Required**:

**File**: `frontend/src/services/api.ts`

**Add function to fetch CSRF token**:
```typescript
export async function getCsrfToken(): Promise<string> {
  try {
    const response = await axios.get('/api/v1/auth/csrf/token');
    return response.data.csrf_token;
  } catch (error) {
    console.error('Failed to get CSRF token:', error);
    return '';
  }
}
```

**Update login flow**:
```typescript
// In login component
const csrfToken = await getCsrfToken();
const response = await api.post('/auth/login', {
  email,
  password,
  _csrf_token: csrfToken  // Include CSRF token
});
```

**Backend Changes Required**:

**Register CSRF endpoint**:
```python
# File: app/api/v1/api.py
from app.api.v1.endpoints import csrf

api_router.include_router(
    csrf.router,
    prefix="/auth/csrf",
    tags=["csrf"]
)
```

**Update CSRF middleware** to accept token from:
- Header: `X-CSRF-Token`
- Form field: `csrf_token`
- Request body: `_csrf_token`

---

## 📊 Current Status

**Servers Running**:
- ✅ Backend: http://localhost:8000 (healthy)
- ✅ Frontend Dev: http://localhost:5173 (with proxy)
- ❌ Frontend Preview: http://localhost:4173 (no proxy - causes errors)

**API Test Results**:
- ✅ Backend health: `200 OK`
- ❌ Login without CSRF: `403 Forbidden`
- ❌ Proxy through preview: `500 Internal Server Error`

**Admin User**:
- ✅ Exists in database
- ✅ Email: admin@psychsync.test
- ✅ Password: TestPassword123!

---

## 🎯 Recommended Next Steps

### Immediate (Quick Fix):

1. **Disable CSRF protection temporarily**:
   ```bash
   # Edit app/main.py line 712
   csrf_protection_enabled=False

   # Restart backend
   pkill -f uvicorn && ./dev.sh
   ```

2. **Use development server** (not preview):
   ```
   URL: http://localhost:5173/login
   ```

3. **Test login**:
   - Email: admin@psychsync.test
   - Password: TestPassword123!

### Long-term (Proper Fix):

1. Implement proper CSRF token flow
2. Add CSRF endpoint to API router
3. Update frontend to fetch and use CSRF tokens
4. Re-enable CSRF protection

---

## 📞 Quick Verification

**After applying fix**, test:

```bash
# Test login endpoint directly
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@psychsync.test","password":"TestPassword123!"}' \
  -w "\nHTTP Status: %{http_code}\n"

# Expected: 200 OK with access_token
```

---

**Last Updated**: January 21, 2026
**Status**: 🔍 **AWAITING FIX**
**Priority**: 🔴 **HIGH** - Blocking user login
