# Debugging Guide: /admin/performance Routing Issue

## Problem
When you navigate to `http://localhost:5173/admin/performance`, it redirects to the dashboard instead of showing the Performance Monitoring page.

## Debugging Steps

### Step 1: Restart the Frontend Dev Server

The most likely cause is that the dev server hasn't picked up the new routes.

```bash
# Stop the dev server (Ctrl+C)
# Then restart it:
cd frontend
npm run dev
```

### Step 2: Test with the Simple Test Page

I've created a simple test page that doesn't have any complex dependencies:

**Navigate to**: `http://localhost:5173/admin/performance-test`

If you see a green page with "✅ Performance Monitoring Test Page", then routing works! The issue is with the component itself.

### Step 3: Check Browser Console

1. Open browser DevTools (F12 or right-click → Inspect)
2. Go to the **Console** tab
3. Navigate to `/admin/performance`
4. Look for any red errors

**Common errors to look for:**
- `Failed to fetch` → API endpoint issue
- `Module not found` → Import issue
- `Unexpected token` → Syntax error
- `RequireAuth` → Authentication issue

### Step 4: Check the Network Tab

1. Open browser DevTools (F12)
2. Go to the **Network** tab
3. Navigate to `/admin/performance`
4. Check if there are any **failed requests** (red status codes)

**Look for:**
- Failed to load `/api/v1/monitoring/health` → Backend not running or wrong port
- 403 Forbidden → Not authorized as admin
- 404 Not Found → Route not configured

### Step 5: Verify Backend is Running

The dashboard needs the backend API to fetch metrics:

```bash
# Check if backend is running
curl http://localhost:8000/health

# You should see JSON response like:
# {"status":"healthy","version":"...","timestamp":"..."}
```

If this fails, start the backend:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 6: Check Your User Role

The monitoring endpoints require **admin role**:

```bash
# Connect to database and check your role
psql -U postgres psychsync

SELECT email, role FROM users WHERE email = 'your@email.com';

# If not admin, update:
UPDATE users SET role = 'ADMIN' WHERE email = 'your@email.com';
```

### Step 7: Temporary Workaround - Bypass API Check

If you just want to see the UI, you can modify the dashboard to not require the API:

Edit `frontend/src/components/admin/PerformanceMonitoringDashboard.tsx`:

```typescript
// Around line 51, temporarily skip the API call:
const fetchMetrics = async () => {
  try {
    setError(null);

    // TEMPORARY: Use mock data instead of API
    setHealth({
      status: 'healthy',
      alerts: [],
      metrics: {
        query_metrics: {},
        slow_queries: [],
        pool_metrics: { total_connections: 60, checked_out: 12 },
        system_metrics: { memory_usage_mb: 245, cpu_usage_percent: 12.3 },
        response_times: { p50: 0.145, p95: 0.167, p99: 0.234 },
        issues_detected: { n_plus_1_queries: 0, unbounded_queries: 0, slow_queries: 0 }
      }
    });
    setLoading(false);
    return;

    // Original code below (commented out):
    // const response = await fetch('/api/v1/monitoring/health');
    // ...
  }
}
```

## Expected Behavior

### What Should Happen:
1. Navigate to `/admin/performance`
2. See a loading spinner briefly
3. Dashboard appears with:
   - System status badge (Healthy/Degraded)
   - 4 metric cards (Response Time, Memory, Pool, Issues)
   - Auto-refresh toggle
   - Performance metrics data

### URL Structure:
- **Admin home**: `/admin` (if it exists)
- **Performance monitoring**: `/admin/performance` ← This should work!
- **Performance test**: `/admin/performance-test` ← Test page

## Common Issues & Fixes

### Issue 1: "Cannot find module '@/components/ui/Card'"
**Fix**: The Card component exists at `@/components/common/card.tsx`. The import should work, but if not:
```typescript
// Change import in PerformanceMonitoringDashboard.tsx from:
import { Card } from '@/components/ui/Card';
// To:
import { Card } from '@/components/common/card';
```

### Issue 2: Route goes to dashboard instead
**Possible causes**:
1. Dev server not restarted → **Restart it!**
2. Browser cache → Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
3. Route conflict → Check if there's a `/admin/*` route matching first

### Issue 3: 403 Forbidden when loading metrics
**Fix**: You need admin role. See Step 6 above.

### Issue 4: API returns 404
**Fix**: Backend monitoring endpoints not registered. Check `app/main.py` has:
```python
from app.api.v1.endpoints.performance_monitoring import router as performance_router
app.include_router(performance_router, prefix="/api/v1/monitoring", tags=["monitoring"])
```

## Quick Test Command

```bash
# Test the backend API directly (get your admin token first):
TOKEN="your_admin_jwt_token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/monitoring/health

# Expected: JSON with performance metrics
```

## Next Steps After Fix

Once routing works:
1. Remove the test route (`/admin/performance-test`) from App.tsx
2. Remove the test page file (`PerformanceMonitoring.test.tsx`)
3. Customize the dashboard for your needs
4. Set up alerts and notifications

## Still Not Working?

Provide this information:
1. Browser console errors (screenshot or copy-paste)
2. Network tab errors (screenshot or copy-paste)
3. What URL you're accessing
4. What you see instead of the dashboard
5. Backend server logs (if any)
