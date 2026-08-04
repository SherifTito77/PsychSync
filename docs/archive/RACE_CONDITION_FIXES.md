# useEffect Race Condition Fixes - Implementation Guide

This document provides copy-paste ready fixes for all identified race conditions.

---

## 🔴 Fix 1: AuthContext - Async Initialization

**File:** `frontend/src/contexts/AuthContext.tsx:40-75`

### BEFORE (Race Condition):
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
        } else {
          handleLogout();
        }
      }
    } catch (error) {
      console.error('Authentication initialization failed:', error);
      handleLogout();
    } finally {
      setIsLoading(false);  // ⚠️ May run after unmount
    }
  };

  initAuth();  // ⚠️ No cleanup
}, []);
```

### AFTER (Fixed):
```typescript
useEffect(() => {
  let isMounted = true;  // ✅ Track mount status
  const abortController = new AbortController();  // ✅ Support cancellation
  const signal = abortController.signal;

  const initAuth = async () => {
    try {
      const userData = localStorage.getItem('user');
      if (userData) {
        const currentUser = await getCurrentUser();

        // ✅ Check if still mounted before state updates
        if (!isMounted || signal.aborted) {
          return;
        }

        if (currentUser && SecurityUtils.validateEmail(currentUser.email)) {
          setUser(currentUser);
          setLastActivity(Date.now());
        } else {
          console.warn('Invalid user data received');
          if (isMounted && !signal.aborted) {
            handleLogout();
          }
        }
      }
    } catch (error) {
      console.error('Authentication initialization failed:', error);
      if (isMounted && !signal.aborted) {
        handleLogout();
      }
    } finally {
      // ✅ Only update if still mounted
      if (isMounted && !signal.aborted) {
        setIsLoading(false);
      }
    }
  };

  initAuth();

  // ✅ Cleanup function
  return () => {
    isMounted = false;
    abortController.abort();
  };
}, []);
```

---

## 🔴 Fix 2: CrisisSupport - Safety Plan Loading

**File:** `frontend/src/components/clinical/CrisisSupport.tsx:146-171`

### BEFORE (Race Condition):
```typescript
const loadSafetyPlan = async () => {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const response = await fetch('/api/v1/clinical/crisis/safety-plan', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success && data.data) {
        setSafetyPlan(data.data);  // ⚠️ May run after unmount
      }
    }
  } catch (err) {
    console.error('Error loading safety plan:', err);
  }
};

useEffect(() => {
  loadSafetyPlan();  // ⚠️ No cleanup, no cancellation
}, []);
```

### AFTER (Fixed):
```typescript
const loadSafetyPlan = async () => {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const response = await fetch('/api/v1/clinical/crisis/safety-plan', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success && data.data) {
        setSafetyPlan(data.data);
      }
    }
  } catch (err) {
    console.error('Error loading safety plan:', err);
  }
};

// ✅ Load safety plan safely with cleanup
useEffect(() => {
  let isMounted = true;
  const abortController = new AbortController();
  const signal = abortController.signal;

  const loadSafetyPlanSafe = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token || !isMounted || signal.aborted) return;

      const response = await fetch('/api/v1/clinical/crisis/safety-plan', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        signal,  // ✅ Add signal for cancellation
      });

      // ✅ Check mounted status before state update
      if (!isMounted || signal.aborted) {
        return;
      }

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data && isMounted) {
          setSafetyPlan(data.data);
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {  // ✅ Ignore abort errors
        console.error('Error loading safety plan:', err);
      }
    }
  };

  loadSafetyPlanSafe();

  return () => {
    isMounted = false;
    abortController.abort();  // ✅ Cancel on unmount
  };
}, []);
```

---

## 🔴 Fix 3: CrisisSupport - Emergency Call Timeout

**File:** `frontend/src/components/clinical/CrisisSupport.tsx:250-257`

### BEFORE (Race Condition):
```typescript
const handleEmergencyCall = (contact: string) => {
  if (contact === '911' || contact === '988') {
    setIsCallingEmergency(true);
    setTimeout(() => {
      setIsCallingEmergency(false);  // ⚠️ Will fire even after unmount
      alert(`Calling ${contact}... Please stay on the line.`);
    }, 2000);
  } else {
    window.open(`tel:${contact}`);
  }
};
```

### AFTER (Fixed):
```typescript
const handleEmergencyCall = (contact: string) => {
  if (contact === '911' || contact === '988') {
    setIsCallingEmergency(true);

    // ✅ Use ref to track timeout
    const timeoutId = setTimeout(() => {
      setIsCallingEmergency(false);
      alert(`Calling ${contact}... Please stay on the line.`);
    }, 2000);

    // ✅ Store timeout ID for cleanup
    return () => clearTimeout(timeoutId);
  } else {
    window.open(`tel:${contact}`);
  }
};

// ✅ Better: Use the useSafeTimeout hook
import { useSafeTimeout } from '../hooks/useAsyncEffect';

// In component:
const [isCallingEmergency, setIsCallingEmergency] = useState(false);

const handleEmergencyCall = (contact: string) => {
  if (contact === '911' || contact === '988') {
    setIsCallingEmergency(true);

    // ✅ Automatically cleaned up timeout
    useSafeTimeout(() => {
      setIsCallingEmergency(false);
      alert(`Calling ${contact}... Please stay on the line.`);
    }, 2000);
  } else {
    window.open(`tel:${contact}`);
  }
};
```

---

## 🔴 Fix 4: ClinicianDashboard - Concurrent Fetches

**File:** `frontend/src/components/clinical/ClinicianDashboard.tsx:129-151`

### BEFORE (Race Condition):
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
  fetchDashboardData();  // ⚠️ No cleanup
  const interval = setInterval(fetchDashboardData, 30000);
  return () => clearInterval(interval);
}, [fetchDashboardData]);
```

### AFTER (Fixed):
```typescript
// ✅ Use custom hook for safe async effects
import { useAsyncEffect, useSafeInterval } from '../../hooks/useAsyncEffect';

// In component:
const fetchDashboardData = useCallback(async (signal?: AbortSignal) => {
  try {
    const [alertsRes, statsRes] = await Promise.all([
      fetch('/api/v1/clinical/alerts?status=pending,in_progress', {
        signal  // ✅ Pass signal for cancellation
      }),
      fetch('/api/v1/clinical/dashboard/stats', {
        signal  // ✅ Pass signal for cancellation
      })
    ]);

    if (signal?.aborted) return;  // ✅ Check for abort

    if (alertsRes.ok) {
      const alertsData = await alertsRes.json();
      setAlerts(alertsData);
    }

    if (statsRes.ok) {
      const statsData = await statsRes.json();
      setStats(statsData);
    }

    if (!signal?.aborted) {  // ✅ Check before state update
      setLoading(false);
    }
  } catch (error) {
    if (error.name !== 'AbortError') {  // ✅ Ignore abort errors
      console.error('Error fetching dashboard data:', error);
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }
}, []);

// ✅ Use the safe async effect hook
useAsyncEffect(async (signal, isMounted) => {
  await fetchDashboardData(signal);
}, []);

// ✅ Use safe interval for periodic refresh
useSafeInterval(
  () => {
    fetchDashboardData();
  },
  30000,  // 30 seconds
  { runOnMount: false }  // Don't run immediately (useAsyncEffect already did)
);
```

---

## 🟡 Fix 5: SessionExpiryModal - External Callback

**File:** `frontend/src/components/SessionExpiryModal.tsx:21-35`

### BEFORE (Race Condition):
```typescript
useEffect(() => {
  const timer = setInterval(() => {
    setCountdown((prev) => {
      if (prev <= 1) {
        clearInterval(timer);
        onLogout();  // ⚠️ May be stale callback
        return 0;
      }
      return prev - 1;
    });
  }, 1000);

  return () => clearInterval(timer);
}, [onLogout]);  // ⚠️ Restarts if onLogout changes
```

### AFTER (Fixed):
```typescript
useEffect(() => {
  let isMounted = true;
  let timerId: number;

  const tick = () => {
    setCountdown((prev) => {
      if (prev <= 1) {
        if (isMounted) {
          onLogout();  // ✅ Check mounted first
        }
        return 0;
      }
      return prev - 1;
    });
  };

  timerId = window.setInterval(tick, 1000);

  return () => {
    isMounted = false;
    clearInterval(timerId);
  };
}, [onLogout]);  // ✅ Better: wrap onLogout in useCallback or use ref
```

---

## 🟡 Fix 6: TeamContext - Stale State Pattern

**File:** `frontend/src/contexts/TeamContext.tsx:65-79`

### BEFORE (Race Condition):
```typescript
const updateTeam = useCallback(async (teamId: number, updateData: Partial<Team>) => {
  try {
    const updatedTeam: Team = { ...updateData, id: teamId } as Team;

    setTeams((prev) => prev.map((team) =>
      team.id === teamId ? { ...team, ...updatedTeam } : team
    ));

    // ⚠️ Race condition: currentTeam could change between check and update
    if (currentTeam && currentTeam.id === teamId) {
      setCurrentTeam({ ...currentTeam, ...updatedTeam });
    }

    showNotification('Team updated successfully', 'success');
    return { success: true, data: updatedTeam };
  } catch (error) {
    // ...
  }
}, [currentTeam, showNotification]);
```

### AFTER (Fixed):
```typescript
const updateTeam = useCallback(async (teamId: number, updateData: Partial<Team>) => {
  try {
    const updatedTeam: Team = { ...updateData, id: teamId } as Team;

    setTeams((prev) => {
      // ✅ Use functional update to avoid stale closure
      return prev.map((team) =>
        team.id === teamId ? { ...team, ...updatedTeam } : team
      );
    });

    // ✅ Use functional update for currentTeam too
    setCurrentTeam((prevCurrentTeam) => {
      // ✅ Check fresh state instead of closure-captured value
      if (prevCurrentTeam && prevCurrentTeam.id === teamId) {
        return { ...prevCurrentTeam, ...updatedTeam };
      }
      return prevCurrentTeam;
    });

    showNotification('Team updated successfully', 'success');
    return { success: true, data: updatedTeam };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to update team';
    showNotification(errorMessage, 'error');
    return { success: false, error: errorMessage };
  }
}, [showNotification]);  // ✅ Remove currentTeam from deps
```

---

## 🟢 Fix 7: ClinicianDashboard - Interval Optimization

**File:** `frontend/src/components/clinical/ClinicianDashboard.tsx:153-157`

### BEFORE (Unnecessary Restarts):
```typescript
useEffect(() => {
  fetchDashboardData();
  const interval = setInterval(fetchDashboardData, 30000);
  return () => clearInterval(interval);
}, [fetchDashboardData]);  // ⚠️ May restart frequently
```

### AFTER (Optimized):
```typescript
// ✅ Memoize properly to prevent restarts
const fetchDashboardDataRef = useRef(fetchDashboardData);

// Keep ref in sync
useEffect(() => {
  fetchDashboardDataRef.current = fetchDashboardData;
}, [fetchDashboardData]);

// ✅ Use ref in interval to prevent restarts
useEffect(() => {
  fetchDashboardDataRef.current();  // Run once on mount

  const interval = setInterval(() => {
    fetchDashboardDataRef.current();  // ✅ Use ref instead
  }, 30000);

  return () => clearInterval(interval);
}, []);  // ✅ Empty deps - no restarts
```

---

## 📊 Quick Reference: Fix Patterns

### Pattern A: AbortController for fetch
```typescript
useEffect(() => {
  const abortController = new AbortController();
  const signal = abortController.signal;

  const fetchData = async () => {
    const response = await fetch(url, { signal });
    if (!signal.aborted) {
      setData(await response.json());
    }
  };

  fetchData();
  return () => abortController.abort();
}, []);
```

### Pattern B: isMounted Flag
```typescript
useEffect(() => {
  let isMounted = true;

  const doSomething = async () => {
    const result = await operation();
    if (isMounted) {
      setState(result);
    }
  };

  doSomething();
  return () => { isMounted = false; };
}, []);
```

### Pattern C: Cleanup Timers
```typescript
useEffect(() => {
  const timerId = setTimeout(() => {
    setState(value);
  }, delay);

  return () => clearTimeout(timerId);
}, [delay]);
```

### Pattern D: Functional Updates
```typescript
// ✅ Avoid stale closures
setState((prev) => prev + 1);

// ❌ Stale closure risk
setState(count + 1);  // Uses current count from closure
```

---

## 🎯 Implementation Priority

1. ✅ **Create safe hooks** (`useAsyncEffect.ts`) - DONE
2. ✅ **Document all race conditions** - DONE
3. ✅ **Provide fix examples** - DONE
4. ⏳ **Apply fixes to critical files:**
   - AuthContext.tsx
   - CrisisSupport.tsx
   - ClinicianDashboard.tsx

5. ⏳ **Add to code review checklist:**
   - Check for async operations in useEffect
   - Verify cleanup functions present
   - Look for setState in async callbacks

---

## 📚 References

- [useEffect complete guide](https://overreacted.io/a-complete-guide-to-useeffect/)
- [React strict mode double invocation](https://react.dev/reference/react/StrictMode)
- [AbortController MDN](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
