# 🧪 Race Condition Testing Guide

This guide helps you manually test all the race condition fixes.

---

## 🚀 Setup

**Dev Server:** http://localhost:5177/
**Status:** ✅ Running

Open browser and navigate to: **http://localhost:5177/**

---

## 📋 Test Scenarios

### Test 1: Authentication Flow (AuthContext.tsx)
**Tests:** Async initialization cleanup

**Steps:**
1. Open browser to http://localhost:5177/
2. Log in with your credentials
3. **Quickly navigate away** before authentication completes:
   - Press browser back button
   - Or navigate to a different URL
4. Check browser console for React warnings

**Expected Result:**
- ✅ No "Can't perform a React state update on an unmounted component" warnings
- ✅ No errors about state updates after unmount
- ✅ Authentication either completes or cleanly cancels

**What This Tests:**
- isMounted flag prevents state updates after unmount
- AbortController cancels pending getCurrentUser() request
- Cleanup function runs properly

---

### Test 2: Crisis Support - Safety Plan (CrisisSupport.tsx)
**Tests:** Fetch cancellation in critical flow

**Steps:**
1. Navigate to the Crisis Support page
2. **Before safety plan loads**, quickly navigate away:
   - Click back button within 1-2 seconds
   - Or close the tab
3. Check browser console

**Expected Result:**
- ✅ No crashes or errors
- ✅ No "setState on unmounted component" warnings
- ✅ No memory leaks from pending fetch requests

**What This Tests:**
- AbortController cancels safety plan fetch
- isMounted checks prevent state updates after navigation
- Critical safety path remains stable

---

### Test 3: Crisis Support - Emergency Call (CrisisSupport.tsx)
**Tests:** Timeout cleanup during emergency calls

**Steps:**
1. Navigate to Crisis Support page
2. Click the emergency call button (911 or 988)
3. **Immediately navigate away** before 2-second timeout completes
4. Return to the page
5. Click emergency call button again

**Expected Result:**
- ✅ Only one active timeout at a time
- ✅ No multiple simultaneous alerts
- ✅ Timeout cleans up properly on unmount
- ✅ Can trigger multiple calls in sequence without issues

**What This Tests:**
- useRef tracks timeout ID properly
- Previous timeout cleared before new one
- Cleanup effect clears timeout on unmount
- No memory leaks from abandoned timeouts

---

### Test 4: Clinician Dashboard (ClinicianDashboard.tsx)
**Tests:** Concurrent fetch cancellation and interval stability

**Steps:**
1. Navigate to Clinician Dashboard
2. Watch for data loading (alerts + stats)
3. **Quickly navigate away** before data loads:
   - Click away within 1-2 seconds
4. Return to dashboard
5. Wait 30 seconds and observe auto-refresh

**Expected Result:**
- ✅ No "setState on unmounted component" warnings
- ✅ Fetch requests cancelled on navigation
- ✅ Auto-refresh interval continues working
- ✅ No stale data shown
- ✅ No multiple intervals running

**What This Tests:**
- AbortController cancels concurrent fetches
- isMounted prevents state updates after unmount
- Interval properly cleans up and restarts
- No abandoned requests wasting bandwidth

---

### Test 5: Session Expiry Countdown (SessionExpiryModal.tsx)
**Tests:** Interval stability with callback changes

**Steps:**
1. Let your session expire (or trigger expiry manually)
2. Watch the countdown timer
3. The countdown should decrement smoothly every second
4. Navigate away and back during countdown

**Expected Result:**
- ✅ Countdown decrements smoothly (no skips)
- ✅ Timer doesn't reset or restart unexpectedly
- ✅ Countdown continues from where it left off on return
- ✅ No memory leaks from intervals

**What This Tests:**
- useRef stores stable callback reference
- Interval doesn't restart when onLogout changes
- isMounted check prevents callback after unmount
- Smooth, stable countdown behavior

---

### Test 6: Team Management - Rapid Updates (TeamContext.tsx)
**Tests:** Functional state updates prevent stale closures

**Steps:**
1. Navigate to Teams page
2. Select a team (makes it "currentTeam")
3. **Rapidly update the team:**
   - Change team name quickly multiple times
   - Update team settings
   - Switch between different teams
4. Check that displayed team info matches actual data

**Expected Result:**
- ✅ Team updates show immediately
- ✅ No stale data displayed
- ✅ Current team always reflects latest state
- ✅ No lag or mismatch between updates and display

**What This Tests:**
- Functional updates use fresh state instead of closures
- Updates work correctly even when currentTeam changes rapidly
- No race conditions from concurrent updates

---

### Test 7: Team Management - Delete Active Team (TeamContext.tsx)
**Tests:** Functional updates during team deletion

**Steps:**
1. Navigate to Teams page
2. Select a team as current
3. Delete that same team
4. Verify currentTeam is properly cleared

**Expected Result:**
- ✅ currentTeam set to null after deletion
- ✅ No stale team data shown
- ✅ Can select a different team after deletion
- ✅ No errors about accessing deleted team

**What This Tests:**
- Functional update checks fresh state before deletion
- Proper cleanup of currentTeam reference
- No stale closure issues

---

## 🔍 Console Monitoring

**What to Watch For:**

❌ **Bad (indicates race conditions):**
```
Warning: Can't perform a React state update on an unmounted component
Warning: setState(...) on unmounted component
Memory leak warnings
```

✅ **Good (fixes working):**
```
(no warnings)
Clean unmount/destroy logs
Normal application logs
```

---

## 📊 Performance Monitoring

**Open Chrome DevTools:**
1. Press F12 or right-click → Inspect
2. Go to **Performance** tab
3. Press **Record**
4. Perform test scenarios
5. Stop recording
6. Look for:
   - ✅ Timers cleared properly (no long-running timers)
   - ✅ No memory leaks (heap size stable)
   - ✅ No abandoned network requests

---

## 🎯 Quick Checklist

Run through this checklist to verify all fixes:

- [ ] Auth: Log in, immediately navigate away → No warnings
- [ ] Crisis: Load support page, navigate away → No warnings
- [ ] Emergency: Click emergency call, navigate away → No warnings
- [ ] Dashboard: Load dashboard, navigate away → No warnings
- [ ] Session: Watch countdown, navigate away → Smooth countdown
- [ ] Teams: Rapid team updates → Fresh data shown
- [ ] Teams: Delete current team → Properly cleared
- [ ] Console: No React warnings about unmounted components

**All passing?** 🎉 Race conditions are fully fixed!

---

## 🐛 What to Do If You Find Issues

1. **Note the exact scenario** that failed
2. **Copy console errors** if any
3. **Check browser console** for React warnings
4. **Report findings** with:
   - Which test failed
   - What happened vs. expected
   - Console output
   - Browser version

---

## 📚 Additional Resources

- **Fix Details:** `RACE_CONDITION_FIXES.md`
- **Complete Summary:** `RACE_CONDITIONS_COMPLETE.md`
- **Technical Analysis:** `USEEXTP_RACE_CONDITIONS.md`
- **Safe Hooks:** `src/hooks/useAsyncEffect.ts`

---

## 🎓 Learning: What These Patterns Prevent

### Pattern 1: AbortController
**Prevents:** Wasted network requests, crashes from late responses
```typescript
// ✅ Good
useEffect(() => {
  const ctrl = new AbortController();
  fetch(url, { signal: ctrl.signal });
  return () => ctrl.abort(); // Cancels on unmount
}, []);
```

### Pattern 2: isMounted Flag
**Prevents:** State updates after unmount, React warnings
```typescript
// ✅ Good
useEffect(() => {
  let mounted = true;
  fetchData().then(data => {
    if (mounted) setState(data); // Only if mounted
  });
  return () => { mounted = false; };
}, []);
```

### Pattern 3: Functional Updates
**Prevents:** Stale closures, outdated data
```typescript
// ✅ Good
setState(prev => prev + 1); // Always gets fresh state

// ❌ Bad
setState(count + 1); // Uses stale closure value
```

### Pattern 4: Refs for Stable Callbacks
**Prevents:** Unnecessary re-renders, effect restarts
```typescript
// ✅ Good
const callbackRef = useRef(callback);
useEffect(() => { callbackRef.current = callback; }, [callback]);

useEffect(() => {
  const timer = setInterval(() => callbackRef.current(), 1000);
  return () => clearInterval(timer);
}, []); // Empty deps - never restarts
```

---

**Happy Testing!** 🧪✨
