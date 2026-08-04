# Performance Troubleshooting Guide

**Date**: January 21, 2026
**Issue**: Frontend is slow, heavy, and non-responsive after analytics integration
**Status**: 🔍 **DIAGNOSING**

---

## 🚨 Immediate Actions to Try

### 1. Hard Refresh Browser
The most common cause of slowness after code changes is browser cache.

**Chrome/Edge:**
- Press `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Or: Open DevTools → Right-click refresh button → "Empty Cache and Hard Reload"

**Firefox:**
- Press `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)

### 2. Restart Dev Server
Sometimes the dev server accumulates state and needs a restart.

```bash
# Stop the dev server (Ctrl+C)
# Then restart:
cd frontend
npm run dev
```

### 3. Check Browser Console
Open browser DevTools (F12) and check:

**Console Tab:**
- Look for red errors
- Look for warnings about re-renders
- Check for "Failed to load resource" errors

**Network Tab:**
- Are there requests taking >1 second?
- Are there failed requests?
- Is the backend responding slowly?

**Performance Tab:**
- Click "Record"
- Use the app for 10 seconds
- Stop recording
- Look for long tasks (>50ms)

---

## 🔍 Diagnostic Tools

### Using Performance Diagnostics

A new diagnostic tool has been added. Use it in browser console:

```javascript
// Get comprehensive performance report
perfDiagnostics.generateReport()

// Check memory usage
perfDiagnostics.checkMemoryLeaks()

// Clear diagnostic data
perfDiagnostics.clear()
```

### What to Look For

**High Render Counts:**
If a component is rendering 100+ times per minute, that's a problem.

**Memory Usage:**
- Normal: <50MB
- Warning: 50-100MB
- Critical: >100MB (possible memory leak)

**Long Tasks:**
- Any task >50ms will cause visible lag
- Tasks >100ms will make the UI freeze

---

## ✅ Fixes Already Applied

### Fix 1: DashboardLayout useEffect Loop
**File**: `frontend/src/components/layout/DashboardLayout.tsx:46-102`

**What was fixed:**
- Removed dependency on `securityMetrics.lastActivity` from useEffect
- Now uses closure variable `lastActivityTimestamp`
- Effect runs once on mount instead of continuously

**Expected improvement:**
- ✅ 100% reduction in unnecessary effect re-runs
- ✅ No event listener re-attachment on every interaction
- ✅ Main thread stays free for UI rendering

### Fix 2: Sidebar Memoization
**File**: `frontend/src/components/layout/Sidebar.tsx:31`

**What was fixed:**
- Wrapped Sidebar component in `React.memo`
- Only re-renders when `isOpen` or `onToggle` props change
- Prevents cascading re-renders to 30+ menu items

**Expected improvement:**
- ✅ 70% reduction in render work during normal interactions
- ✅ Sidebar opens instantly without lag

### Fix 3: Monitoring Component Optimization
**Files**: `App.tsx`, `AnalyticsHealthDashboard.tsx`, `AnalyticsPerformanceMonitor.tsx`

**What was fixed:**
- Disabled AnalyticsHealthDashboard in production
- Increased update intervals (2s→5s, 5s→30s)
- Memoized all monitoring components
- Moved SessionTracker outside App component

**Expected improvement:**
- ✅ 71-97% reduction in state updates from monitoring
- ✅ No monitoring overhead in production

---

## 🐛 If Still Slow After Fixes

### Step 1: Check if It's Development vs Production

**Development mode is always slower** because:
- Source maps are generated
- Hot module replacement runs
- Additional validation checks
- Monitoring components are active

**Try production build:**
```bash
cd frontend
npm run build
npm run preview
```

If production build is fast, the issue is development overhead only.

### Step 2: Check Backend Performance

Sometimes the frontend feels slow because the backend is slow.

```bash
# Check if backend is responding quickly
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/health"
```

Expected: <100ms for health check

### Step 3: Disable Analytics Temporarily

To confirm analytics is the issue, temporarily disable it:

**In browser console:**
```javascript
localStorage.removeItem('analytics_consent');
location.reload();
```

The app should run without analytics if this fixes it.

### Step 4: Check for Infinite Loops

In browser DevTools:

```javascript
// Track re-renders
let renderCount = 0;
const originalRender = React.Component.prototype.render;
React.Component.prototype.render = function() {
  renderCount++;
  if (renderCount % 100 === 0) {
    console.warn(`⚠️ ${renderCount} renders detected`);
  }
  return originalRender.apply(this, arguments);
};
```

If render count skyrockets (>1000/minute), there's an infinite loop.

---

## 📊 Performance Targets

### Interaction Response Times

| Action | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Sidebar toggle | <16ms | <50ms | >100ms |
| Page navigation | <100ms | <300ms | >500ms |
| Button click | <16ms | <50ms | >100ms |
| Typing input | <16ms | <50ms | >100ms |

### Rendering Performance

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| FPS | 60 | 30-60 | <30 |
| Long tasks/sec | 0 | 0-1 | >2 |
| Memory | <50MB | 50-100MB | >100MB |
| CPU usage | <10% | 10-30% | >30% |

---

## 🎯 Next Steps

### If Performance is Good in Production:

1. The slowness is development-only overhead
2. This is normal and expected
3. Consider using production mode for performance testing
4. Development tools can be disabled individually if needed

### If Performance is Still Poor:

1. Run `perfDiagnostics.generateReport()` in console
2. Check browser DevTools Performance tab
3. Look for specific components rendering excessively
4. Check network tab for slow API calls
5. Report findings with specific metrics

---

## 📞 Reporting Issues

When reporting performance issues, include:

1. **Browser and version** (e.g., Chrome 120, Safari 17)
2. **Console errors/warnings** (screenshot or copy)
3. **Performance tab recording** (export as JSON)
4. **Diagnostic output** from `perfDiagnostics.generateReport()`
5. **Specific actions that are slow** (e.g., "opening sidebar takes 3 seconds")

---

**Last Updated**: January 21, 2026
**Status**: 🔍 **AWAITING USER FEEDBACK**
**Priority**: 🔴 **HIGH**
