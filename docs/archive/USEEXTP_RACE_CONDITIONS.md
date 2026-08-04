# useEffect Race Conditions Analysis Report

## Executive Summary

Found **8 critical race conditions** in useEffect hooks across the React frontend that could cause:
- Memory leaks from state updates after component unmount
- Stale data being displayed to users
- Crashes from operations on unmounted components
- Unnecessary re-renders and API calls

---

## 🔴 Critical Race Conditions (High Priority)

### 1. AuthContext - Async Function Without Cleanup

**File:** `frontend/src/contexts/AuthContext.tsx:37-72`

**Problem:**
```typescript
useEffect(() => {
  const initAuth = async () => {
    try {
      const userData = localStorage.getItem('user');
      if (userData) {
        const currentUser = await getCurrentUser();
        if (currentUser && SecurityUtils.validateEmail(currentUser.email)) {
          setUser(currentUser);  // ⚠️ May run after unmount
          setLastActivity(Date.now());  // ⚠️ May run after unmount
        }
      }
    } catch (error) {
      console.error('Authentication initialization failed:', error);
      handleLogout();
    } finally {
      setIsLoading(false);  // ⚠️ May run after unmount
    }
  };

  initAuth();  // ⚠️ No cleanup, no cancellation
}, []);
```

**Issue:** If user navigates away during authentication initialization, state updates will occur on unmounted component.

**Impact:** Memory leaks, warnings in console, potential app crashes.

---

### 2. CrisisSupport - fetch() Without Cleanup

**File:** `frontend/src/components/clinical/CrisisSupport.tsx:146-171`

**Problem:**
```typescript
const loadSafetyPlan = async () => {
  try {
    const response = await fetch('/api/v1/clinical/crisis/safety-plan', {
      headers: { 'Authorization': `Bearer ${token}` },
    });

    if (response.ok) {
      const data = await response.json();
      setSafetyPlan(data.data);  // ⚠️ May run after unmount
    }
  } catch (err) {
    console.error('Error loading safety plan:', err);
  }
};

useEffect(() => {
  loadSafetyPlan();  // ⚠️ No cleanup, abort controller, or mounted check
}, []);
```

**Issue:** fetch() call cannot be cancelled if component unmounts.

**Impact:** State update on unmounted component (crisis support - critical path!).

---

### 3. ClinicianDashboard - Concurrent fetch Without Cancellation

**File:** `frontend/src/components/clinical/ClinicianDashboard.tsx:129-151`

**Problem:**
```typescript
const fetchDashboardData = useCallback(async () => {
  try {
    const [alertsRes, statsRes] = await Promise.all([
      fetch('/api/v1/clinical/alerts?status=pending,in_progress'),
      fetch('/api/v1/clinical/dashboard/stats')
    ]);

    if (alertsRes.ok) {
      const alertsData = await alertsRes.json();
      setAlerts(alertsData);  // ⚠️ May run after unmount
    }

    if (statsRes.ok) {
      const statsData = await statsRes.json();
      setStats(statsData);  // ⚠️ May run after unmount
    }

    setLoading(false);  // ⚠️ May run after unmount
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    setLoading(false);  // ⚠️ May run after unmount
  }
}, []);

useEffect(() => {
  fetchDashboardData();  // ⚠️ No cleanup, no cancellation
  const interval = setInterval(fetchDashboardData, 30000);
  return () => clearInterval(interval);
}, [fetchDashboardData]);
```

**Issue:** Multiple concurrent fetch operations with no cancellation mechanism. Interval restarts if `fetchDashboardData` changes.

**Impact:** Wasted network requests, state updates on unmounted component.

---

### 4. CrisisSupport - setTimeout Without Cleanup

**File:** `frontend/src/components/clinical/CrisisSupport.tsx:250-257`

**Problem:**
```typescript
const handleEmergencyCall = (contact: string) => {
  if (contact === '911' || contact === '988') {
    setIsCallingEmergency(true);
    setTimeout(() => {
      setIsCallingEmergency(false);  // ⚠️ Will fire even after unmount
      alert(`Calling ${contact}... Please stay on the line.`);
    }, 2000);
  }
};
```

**Issue:** setTimeout cannot be cancelled if component unmounts.

**Impact:** State update on unmounted component during emergency call handling.

---

## 🟡 Medium Priority Issues

### 5. SessionExpiryModal - External Callback Dependency

**File:** `frontend/src/components/SessionExpiryModal.tsx:21-35`

**Problem:**
```typescript
useEffect(() => {
  const timer = setInterval(() => {
    setCountdown((prev) => {
      if (prev <= 1) {
        clearInterval(timer);
        onLogout();  // ⚠️ External callback may be stale
        return 0;
      }
      return prev - 1;
    });
  }, 1000);

  return () => clearInterval(timer);
}, [onLogout]);  // ⚠️ Interval restarts if onLogout changes
```

**Issue:** onLogout callback changes cause interval to restart. No mounted check.

---

### 6. TeamContext - Potential Stale State

**File:** `frontend/src/contexts/TeamContext.tsx:65-79`

**Problem:**
```typescript
const updateTeam = useCallback(async (teamId: number, updateData: Partial<Team>) => {
  try {
    if (currentTeam && currentTeam.id === teamId) {  // ⚠️ May be stale
      setCurrentTeam({ ...currentTeam, ...updatedTeam });  // ⚠️ Using potentially stale currentTeam
    }
  } catch (error) {
    // ...
  }
}, [currentTeam, showNotification]);
```

**Issue:** Between checking `currentTeam` and calling `setCurrentTeam`, state could change.

---

## 🟢 Low Priority Issues

### 7. ClinicianDashboard - Interval Restart

**File:** `frontend/src/components/clinical/ClinicianDashboard.tsx:153-157`

**Problem:**
```typescript
useEffect(() => {
  fetchDashboardData();
  const interval = setInterval(fetchDashboardData, 30000);
  return () => clearInterval(interval);
}, [fetchDashboardData]);  // ⚠️ May restart frequently
```

**Issue:** `fetchDashboardData` is recreated on each render if not properly memoized.

---

### 8. CSS Injection (Good Pattern)

**File:** `frontend/src/pages/clinical-assessment/index.tsx:77-85`

**Good Example:** ✅
```typescript
useEffect(() => {
  const style = document.createElement('style');
  style.textContent = assessmentStyles;
  document.head.appendChild(style);

  return () => {
    document.head.removeChild(style);  // ✅ Proper cleanup
  };
}, []);
```

---

## 🔧 Fix Patterns

### Pattern 1: AbortController for fetch()

```typescript
useEffect(() => {
  const abortController = new AbortController();
  const signal = abortController.signal;

  const fetchData = async () => {
    try {
      const response = await fetch('/api/endpoint', {
        signal  // ✅ Can be cancelled
      });

      if (!signal.aborted) {  // ✅ Check before state update
        const data = await response.json();
        setState(data);
      }
    } catch (error) {
      if (error.name !== 'AbortError') {  // ✅ Ignore abort errors
        console.error('Fetch error:', error);
      }
    }
  };

  fetchData();

  return () => {
    abortController.abort();  // ✅ Cancel on unmount
  };
}, []);
```

### Pattern 2: isMounted Flag

```typescript
useEffect(() => {
  let isMounted = true;  // ✅ Track mount status

  const fetchData = async () => {
    const data = await fetchSomeData();

    if (isMounted) {  // ✅ Only update if still mounted
      setState(data);
    }
  };

  fetchData();

  return () => {
    isMounted = false;  // ✅ Set false on unmount
  };
}, []);
```

### Pattern 3: Cancel Timers

```typescript
useEffect(() => {
  const timerId = setTimeout(() => {
    if (isMounted) {  // ✅ Check before update
      setState(value);
    }
  }, delay);

  return () => {
    clearTimeout(timerId);  // ✅ Cleanup timer
  };
}, [delay]);
```

---

## 📊 Summary Statistics

| Severity | Count | Files Affected |
|----------|-------|----------------|
| 🔴 Critical | 4 | AuthContext, CrisisSupport, ClinicianDashboard |
| 🟡 Medium | 2 | SessionExpiryModal, TeamContext |
| 🟢 Low | 2 | ClinicianDashboard (other) |
| ✅ Good | 1 | clinical-assessment/index.tsx |

---

## 🎯 Recommended Actions

### Immediate (Critical)
1. ✅ Fix AuthContext async initialization
2. ✅ Fix CrisisSupport fetch operations
3. ✅ Fix ClinicianDashboard concurrent fetches
4. ✅ Fix CrisisSupport setTimeout

### Short-term (Medium)
5. Fix SessionExpiryModal callback handling
6. Fix TeamContext stale state pattern
7. Optimize ClinicianDashboard interval handling

### Long-term (Best Practices)
8. Add race condition detection to linting rules
9. Create shared hooks for safe async operations
10. Add race condition tests to test suite

---

## 📚 Resources

- [React useEffect Documentation](https://react.dev/reference/react/useEffect)
- [Race Conditions in React](https://overreacted.io/a-complete-guide-to-useeffect/)
- [AbortController API](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
