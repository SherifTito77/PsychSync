# 404 Error Troubleshooting - Complete Guide

## The Problem

You're getting **404 Page Not Found** errors when trying to access pages.

## Root Cause

Your application has **authentication-protected routes**. When you try to access protected pages without being logged in, React Router redirects you to `/login`. If that doesn't work, you see a 404.

## The Solution

### Step 1: Go to the Login Page
```
http://localhost:5173/login
```
This page **requires NO authentication** and should definitely work.

### Step 2: Login with Your Test Account
```
Email: testfix789@test.com
Password: (your password)
```

Don't remember the password? Reset it:
```
http://localhost:5173/forgot-password
```

Or create a new account:
```
http://localhost:5173/register
```

### Step 3: Access Protected Pages
After login, you can access:
- `/dashboard` - Main dashboard
- `/analytics` - Analytics pages
- All other authenticated routes

## What URLs Should Work

### ✅ Public Pages (No Login Needed)
```
http://localhost:5173/                  (Landing page)
http://localhost:5173/login             (Login)
http://localhost:5173/register          (Register)
http://localhost:5173/forgot-password   (Reset password)
```

### 🔒 Protected Pages (Require Login)
```
http://localhost:5173/dashboard         (Main dashboard)
http://localhost:5173/analytics         (Analytics)
http://localhost:5173/analytics/dashboard
http://localhost:5173/analytics/kpi
```

### ❌ Routes That Don't Exist (Will 404)
```
/product-operations                      (Component exists, no route)
```

## Quick Diagnostic

### If `/login` gives 404:
```
1. Check frontend is running:
   → Terminal in frontend/ folder
   → Should see: Vite server running on port 5173

2. If not running, start it:
   cd frontend
   npm run dev
```

### If `/dashboard` gives 404:
```
1. You're probably not logged in
2. Go to /login first
3. Login, then try /dashboard again
```

## Browser Console Debugging

Press F12 and check:

1. **Network Tab**: See what URLs are being requested
2. **Console Tab**: Look for React Router errors
3. **Application Tab**: Check if you have an auth token

## Still Stuck?

1. **Clear browser cache**
   ```
   Ctrl+Shift+Delete (Windows/Linux)
   Cmd+Shift+Delete (Mac)
   ```

2. **Try in incognito/private mode**
   - This eliminates cache/cookie issues

3. **Check both terminals**
   - Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
   - Frontend: Vite on port 5173

4. **Verify database connection**
   ```bash
   psql -h localhost -U psychsync_user -d psychsync_db -c "SELECT COUNT(*) FROM users;"
   ```

## Expected Flow

```
1. You open: http://localhost:5173/login
   ✅ Should see login form

2. You enter credentials and click Login
   ✅ Should redirect to /dashboard

3. You see: http://localhost:5173/dashboard
   ✅ Should see your dashboard

4. You navigate to analytics
   ✅ Should see analytics data
```

## Summary

| Issue | Solution |
|-------|----------|
| 404 on all pages | Go to `/login` first |
| 404 on `/login` | Frontend not running - check terminal |
| 404 after login | Browser cache - clear or use incognito |
| 404 on specific routes | Route doesn't exist - check App.tsx |

`★ Insight ─────────────────────────────────────`
**Route Protection Flow**: Your app uses a multi-layer authentication check: (1) `SecureRoute` checks for user data, (2) `RequireAuth` validates auth state, (3) If not authenticated, React Router redirects to login. This is good security, but means 404s often indicate "not logged in" rather than "page doesn't exist."
`─────────────────────────────────────────────────`

---

**Start Here**: `http://localhost:5173/login` - This page WILL work!
