# React Effect Cleanup Guide

**Comprehensive best practices for preventing memory leaks in React useEffect**

---

## 🎯 The 5 Golden Rules

### 1. **Always Return Cleanup Function from useEffect**

**Why:** React calls the cleanup function when the component unmounts or before re-running the effect. This is your chance to clean up subscriptions, timers, and listeners.

**✅ CORRECT:**
```tsx
useEffect(() => {
  const subscription = dataSource.subscribe();

  // ✅ Return cleanup function
  return () => {
    subscription.unsubscribe();
  };
}, []);
```

**❌ WRONG:**
```tsx
useEffect(() => {
  const subscription = dataSource.subscribe();
  // ❌ No cleanup - memory leak!
}, []);
```

---

### 2. **Track Mounted Status for Async Operations**

**Why:** Async operations (fetch, promises) may complete after the component unmounts. Updating state on an unmounted component causes React warnings and memory leaks.

**✅ CORRECT:**
```tsx
useEffect(() => {
  let isMounted = true;

  const fetchData = async () => {
    const data = await apiCall();
    if (isMounted) {  // ✅ Check before setState
      setState(data);
    }
  };

  fetchData();

  return () => {
    isMounted = false;  // ✅ Mark as unmounted
  };
}, []);
```

**❌ WRONG:**
```tsx
useEffect(() => {
  const fetchData = async () => {
    const data = await apiCall();
    setState(data);  // ❌ May run after unmount!
  };

  fetchData();
}, []);
```

---

### 3. **Use AbortController for Fetch/Axios**

**Why:** AbortController allows you to cancel in-flight HTTP requests when the component unmounts, preventing unnecessary network traffic and state updates.

**✅ CORRECT with Fetch:**
```tsx
useEffect(() => {
  const abortController = new AbortController();
  const { signal } = abortController;

  fetch('/api/data', { signal })
    .then(res => res.json())
    .then(data => {
      if (!signal.aborted) {  // ✅ Check aborted flag
        setState(data);
      }
    })
    .catch(err => {
      if (err.name !== 'AbortError') {  // ✅ Ignore abort errors
        console.error(err);
      }
    });

  return () => {
    abortController.abort();  // ✅ Cancel request
  };
}, []);
```

**✅ CORRECT with Axios:**
```tsx
useEffect(() => {
  const abortController = new AbortController();
  const { signal } = abortController;

  axios.get('/api/data', { signal })
    .then(response => {
      if (!signal.aborted) {  // ✅ Check aborted flag
        setState(response.data);
      }
    })
    .catch(err => {
      if (err.name !== 'CanceledError') {  // ✅ Ignore cancel errors
        console.error(err);
      }
    });

  return () => {
    abortController.abort();  // ✅ Cancel request
  };
}, []);
```

**❌ WRONG:**
```tsx
useEffect(() => {
  fetch('/api/data')  // ❌ No AbortController
    .then(res => res.json())
    .then(data => setState(data));
}, []);
```

---

### 4. **Store Refs for Timeouts/Intervals**

**Why:** You need to store timeout/interval IDs to clear them later. Using a ref (useRef) ensures the ID persists across re-renders.

**✅ CORRECT with Single Timeout:**
```tsx
useEffect(() => {
  const timeoutId = setTimeout(() => {
    doSomething();
  }, 5000);

  return () => {
    clearTimeout(timeoutId);  // ✅ Clear timeout
  };
}, []);
```

**✅ CORRECT with Multiple Timeouts:**
```tsx
useEffect(() => {
  const timeoutRefs = new Map<string, NodeJS.Timeout>();

  const addTimeout = (id: string, callback: () => void, delay: number) => {
    const timeoutId = setTimeout(() => {
      callback();
      timeoutRefs.delete(id);
    }, delay);
    timeoutRefs.set(id, timeoutId);
  };

  // Add timeouts
  addTimeout('notification-1', () => showNotification('Hello'), 3000);
  addTimeout('notification-2', () => showNotification('World'), 5000);

  return () => {
    // ✅ Clear all timeouts
    timeoutRefs.forEach(timeoutId => clearTimeout(timeoutId));
    timeoutRefs.clear();
  };
}, []);
```

**✅ CORRECT with Interval:**
```tsx
useEffect(() => {
  const intervalId = setInterval(() => {
    refreshData();
  }, 30000);

  return () => {
    clearInterval(intervalId);  // ✅ Clear interval
  };
}, []);
```

**❌ WRONG:**
```tsx
useEffect(() => {
  setTimeout(() => {
    setState(value);  // ❌ No cleanup - may run after unmount
  }, 5000);
}, []);
```

---

### 5. **Clear All Refs in Cleanup Function**

**Why:** If you're storing multiple resource IDs (timeouts, subscriptions, etc.) in a ref, you must clear ALL of them in the cleanup function.

**✅ CORRECT:**
```tsx
useEffect(() => {
  const resources = {
    timeout1: setTimeout(() => {}, 5000),
    timeout2: setTimeout(() => {}, 10000),
    interval: setInterval(() => {}, 3000),
  };

  return () => {
    // ✅ Clear ALL resources
    clearTimeout(resources.timeout1);
    clearTimeout(resources.timeout2);
    clearInterval(resources.interval);
  };
}, []);
```

**✅ CORRECT with Pattern:**
```tsx
useEffect(() => {
  const cleanupFunctions: (() => void)[] = [];

  // Add cleanup tasks
  const timeout1 = setTimeout(() => {}, 5000);
  cleanupFunctions.push(() => clearTimeout(timeout1));

  const timeout2 = setTimeout(() => {}, 10000);
  cleanupFunctions.push(() => clearTimeout(timeout2));

  const interval = setInterval(() => {}, 3000);
  cleanupFunctions.push(() => clearInterval(interval));

  return () => {
    // ✅ Run ALL cleanup functions
    cleanupFunctions.forEach(fn => fn());
  };
}, []);
```

**❌ WRONG:**
```tsx
useEffect(() => {
  const timeout1 = setTimeout(() => {}, 5000);
  const timeout2 = setTimeout(() => {}, 10000);
  const interval = setInterval(() => {}, 3000);

  return () => {
    clearTimeout(timeout1);  // ❌ Missed timeout2 and interval!
  };
}, []);
```

---

## 🚨 Common Memory Leak Patterns

### Pattern 1: Event Listeners

**❌ LEAK:**
```tsx
useEffect(() => {
  window.addEventListener('resize', handleResize);
  // ❌ No cleanup
}, []);
```

**✅ FIXED:**
```tsx
useEffect(() => {
  window.addEventListener('resize', handleResize);

  return () => {
    window.removeEventListener('resize', handleResize);
  };
}, []);
```

---

### Pattern 2: WebSocket Connections

**❌ LEAK:**
```tsx
useEffect(() => {
  const ws = new WebSocket('ws://api.example.com');
  ws.onmessage = (msg) => setMessage(msg.data);
  // ❌ No cleanup
}, []);
```

**✅ FIXED:**
```tsx
useEffect(() => {
  const ws = new WebSocket('ws://api.example.com');

  ws.onmessage = (msg) => {
    if (!ws.readyState === WebSocket.OPEN) return;
    setMessage(msg.data);
  };

  return () => {
    ws.close();  // ✅ Close connection
  };
}, []);
```

---

### Pattern 3: Third-Party Libraries

**❌ LEAK:**
```tsx
useEffect(() => {
  const chart = new Chart(canvasRef.current, config);
  // ❌ No cleanup
}, []);
```

**✅ FIXED:**
```tsx
useEffect(() => {
  const chart = new Chart(canvasRef.current, config);

  return () => {
    chart.destroy();  // ✅ Destroy library instance
  };
}, []);
```

---

## 🛠️ Reusable Hooks

The codebase includes these hooks to prevent memory leaks:

### `useAsyncEffect`

For async operations with automatic cancellation:

```tsx
import { useAsyncEffect } from '@/hooks/useAsyncEffect';

useAsyncEffect(async (signal, isMounted) => {
  const data = await fetchData({ signal });
  if (isMounted()) {
    setState(data);
  }
}, []);
```

### `useTimeoutWithCleanup`

For timeouts with automatic cleanup:

```tsx
import { useTimeoutWithCleanup } from '@/hooks/useTimeoutWithCleanup';

useTimeoutWithCleanup(() => {
  setShowToast(false);
}, 5000);
```

### `useIntervalWithCleanup`

For intervals with automatic cleanup:

```tsx
import { useIntervalWithCleanup } from '@/hooks/useTimeoutWithCleanup';

useIntervalWithCleanup(() => {
  refreshData();
}, 30000);
```

---

## 📋 Checklist for Every useEffect

Before committing code with useEffect, verify:

- [ ] Does this effect create any resources (timers, listeners, subscriptions)?
- [ ] Is there a cleanup function returned?
- [ ] Are ALL resources cleaned up in the cleanup function?
- [ ] Are async operations checking mounted status or using AbortController?
- [ ] Are timeouts/intervals stored and cleared?
- [ ] Will this cause warnings in React DevTools?

---

## 🔍 Debugging Memory Leaks

### 1. React DevTools Profiler

```
1. Open React DevTools
2. Go to Profiler tab
3. Start recording
4. Navigate and interact with your app
5. Stop recording
6. Look for components that don't unmount properly
```

### 2. Chrome Memory Profiler

```
1. Open Chrome DevTools
2. Go to Memory tab
3. Take heap snapshot
4. Trigger effects (navigate, mount/unmount)
5. Take another snapshot
6. Compare snapshots for "Detached DOM nodes"
```

### 3. Console Warnings

Look for these warnings:
```
⚠️ Can't perform a React state update on an unmounted component
⚠️ Can't call setState on an unmounted component
```

These indicate memory leaks from uncleaned effects!

---

## 🎓 Quick Reference

| Resource | Cleanup Method | Example |
|----------|----------------|---------|
| **setTimeout** | `clearTimeout(id)` | `clearTimeout(timeoutId)` |
| **setInterval** | `clearInterval(id)` | `clearInterval(intervalId)` |
| **addEventListener** | `removeEventListener()` | `window.removeEventListener('resize', handler)` |
| **fetch/axios** | `AbortController.abort()` | `abortController.abort()` |
| **WebSocket** | `ws.close()` | `ws.close()` |
| **Subscription** | `subscription.unsubscribe()` | `sub.unsubscribe()` |
| **RequestAnimationFrame** | `cancelAnimationFrame(id)` | `cancelAnimationFrame(rafId)` |
| **IntersectionObserver** | `observer.disconnect()` | `observer.disconnect()` |

---

## 📚 Additional Resources

- [React useEffect Documentation](https://react.dev/reference/react/useEffect)
- [React Hook Rules](https://react.dev/reference/rules/hooks)
- [Chrome DevTools Memory Profiling](https://developer.chrome.com/docs/devtools/memory-problems/)

---

**Remember:** Every effect that creates a resource MUST clean it up. When in doubt, add a cleanup function!
