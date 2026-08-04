# Team Training Guide: Memory Leak Prevention & Resource Cleanup

**Audience**: Frontend Developers (React/TypeScript)
**Duration**: 45 minutes
**Prerequisites**: Familiarity with React hooks and TypeScript

---

## Learning Objectives

By the end of this training, you will be able to:

1. ✅ **Identify** common memory leak patterns in React applications
2. ✅ **Implement** proper cleanup in useEffect hooks
3. ✅ **Use** ESLint rules to catch memory leaks during development
4. ✅ **Apply** best practices for resource management

---

## Table of Contents

1. [What Are Memory Leaks?](#what-are-memory-leaks)
2. [The Cleanup Pattern](#the-cleanup-pattern)
3. [Common Scenarios](#common-scenarios)
4. [Interactive Exercises](#interactive-exercises)
5. [ESLint Integration](#eslint-integration)
6. [Quick Reference](#quick-reference)
7. [Quiz](#quiz)

---

## What Are Memory Leaks?

### Definition

A **memory leak** occurs when your application allocates memory (resources) but never releases it, causing progressive memory growth that eventually degrades performance or crashes the browser.

### Real-World Analogy

Think of memory leaks like **leaving faucets running**:

```
🏠 Your house has 10 faucets (resources)
✅ Normal: Turn on faucet → Use water → Turn off faucet
❌ Memory leak: Turn on faucet → Use water → NEVER turn off faucet
💥 Result: Water bill (memory) keeps growing!
```

### In React Applications

```
Component Mounts → Creates Resources (timers, listeners, connections)
Component Unmounts → Should Clean Up Resources
❌ Memory Leak: Resources stay alive after component unmounts
💥 Result: Browser gets slower and slower
```

### Impact on Users

| Session Length | Memory Leak Impact |
|----------------|-------------------|
| 5 minutes | Unnoticeable |
| 30 minutes | Slight lag |
| 2+ hours | ⚠️ Browser becomes slow |
| 4+ hours | 🚨 Browser may crash |

---

## The Cleanup Pattern

### The Golden Rule

> **Every resource you create in useEffect must be cleaned up in the return function.**

### Basic Template

```typescript
useEffect(() => {
  // ✅ Phase 1: Create resources
  const resource = createResource();

  // ✅ Phase 2: Return cleanup function
  return () => {
    // ✅ Phase 3: Clean up resources
    resource.cleanup();
  };
}, [dependencies]);
```

### Memory Diagram

```
┌─────────────────────────────────────────────────────┐
│                  Component Lifecycle                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Mount                                           Unmount
│    │                                               │
│    ├─► useEffect runs                             │
│    │   ├─► Create resource                        │
│    │   └─► Return cleanup function ◄──────────────┐
│    │                                              │
│    └──────────────────────────────────────────────┤
│                                                   │
│                    │                              │
│                    └─► Cleanup function runs     │
│                        └─► Destroy resource       │
└─────────────────────────────────────────────────────┘
```

---

## Common Scenarios

### Scenario 1: Timers (setInterval / setTimeout)

#### ❌ Memory Leak

```typescript
useEffect(() => {
  // ⚠️ Timer created but never cleared
  setInterval(() => {
    console.log('Tick');
  }, 1000);
}, []);
```

**Problem**: Timer keeps running forever, even after component unmounts.

#### ✅ Fixed

```typescript
useEffect(() => {
  const intervalId = setInterval(() => {
    console.log('Tick');
  }, 1000);

  // ✅ Cleanup: Clear interval when component unmounts
  return () => clearInterval(intervalId);
}, []);
```

**Why This Works**:
1. `intervalId` stores the timer reference
2. Cleanup function runs on unmount
3. `clearInterval(intervalId)` stops the timer

---

### Scenario 2: Event Listeners

#### ❌ Memory Leak

```typescript
useEffect(() => {
  // ⚠️ Listener added but never removed
  window.addEventListener('resize', handleResize);
}, []);
```

**Problem**: Component adds listener every mount, never removes. Multiple mounts = multiple listeners.

#### ✅ Fixed

```typescript
useEffect(() => {
  window.addEventListener('resize', handleResize);

  // ✅ Cleanup: Remove listener
  return () => window.removeEventListener('resize', handleResize);
}, []);
```

**Pro Tip**: Store the handler if it's defined in the effect:

```typescript
useEffect(() => {
  const handleResize = () => {
    // ... resize logic
  };

  window.addEventListener('resize', handleResize);

  return () => window.removeEventListener('resize', handleResize);
}, []);
```

---

### Scenario 3: WebSocket Connections

#### ❌ Memory Leak

```typescript
useEffect(() => {
  // ⚠️ WebSocket created but never closed
  const ws = new WebSocket('ws://localhost:8000');
  ws.onmessage = (e) => console.log(e.data);
}, []);
```

**Problem**: Connection stays open, continues receiving messages.

#### ✅ Fixed

```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000');
  ws.onmessage = (e) => console.log(e.data);

  // ✅ Cleanup: Close WebSocket
  return () => ws.close();
}, []);
```

#### ✅ Better (with ref)

```typescript
const wsRef = useRef<WebSocket | null>(null);

useEffect(() => {
  wsRef.current = new WebSocket('ws://localhost:8000');
  wsRef.current.onmessage = (e) => console.log(e.data);

  return () => {
    // ✅ Cleanup: Close and nullify
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };
}, []);
```

**Why useRef?**:
- Persists across re-renders
- Can be accessed from other effects
- Safer cleanup pattern

---

### Scenario 4: Subscriptions (RxJS, Observables)

#### ❌ Memory Leak

```typescript
useEffect(() => {
  // ⚠️ Subscription created but never unsubscribed
  const subscription = observable$.subscribe(data => {
    setState(data);
  });
}, []);
```

**Problem**: Observable keeps emitting, even if component is gone.

#### ✅ Fixed

```typescript
useEffect(() => {
  const subscription = observable$.subscribe(data => {
    setState(data);
  });

  // ✅ Cleanup: Unsubscribe
  return () => subscription.unsubscribe();
}, []);
```

---

### Scenario 5: Async State Updates

#### ❌ Memory Leak Warning

```typescript
useEffect(() => {
  const fetchData = async () => {
    const data = await api.get('/data');
    // ⚠️ setState might run after unmount
    setState(data);
  };

  fetchData();
}, []);
```

**Problem**: If component unmounts before fetch completes, React warns about setState on unmounted component.

#### ✅ Fixed

```typescript
useEffect(() => {
  let isMounted = true; // ✅ Track mount status

  const fetchData = async () => {
    const data = await api.get('/data');
    if (isMounted) { // ✅ Only update if mounted
      setState(data);
    }
  };

  fetchData();

  return () => {
    isMounted = false; // ✅ Mark as unmounted
  };
}, []);
```

#### ✅ Even Better (with ref)

```typescript
useEffect(() => {
  const isMountedRef = useRef(true); // ✅ Ref persists

  const fetchData = async () => {
    const data = await api.get('/data');
    if (isMountedRef.current) { // ✅ Check ref
      setState(data);
    }
  };

  fetchData();

  return () => {
    isMountedRef.current = false; // ✅ Update ref
  };
}, []);
```

---

## Interactive Exercises

### Exercise 1: Fix the Timer

**Task**: Fix this memory leak:

```typescript
// ❌ MEMORY LEAK
useEffect(() => {
  setTimeout(() => {
    console.log('Delayed message');
  }, 5000);
}, []);
```

<details>
<summary>🔍 Show Solution</summary>

```typescript
// ✅ FIXED
useEffect(() => {
  const timeoutId = setTimeout(() => {
    console.log('Delayed message');
  }, 5000);

  return () => clearTimeout(timeoutId);
}, []);
```
</details>

---

### Exercise 2: Fix the Event Listener

**Task**: Fix this memory leak:

```typescript
// ❌ MEMORY LEAK
useEffect(() => {
  document.addEventListener('keydown', handleKeyPress);
  document.addEventListener('keyup', handleKeyRelease);
}, []);
```

<details>
<summary>🔍 Show Solution</summary>

```typescript
// ✅ FIXED
useEffect(() => {
  document.addEventListener('keydown', handleKeyPress);
  document.addEventListener('keyup', handleKeyRelease);

  return () => {
    document.removeEventListener('keydown', handleKeyPress);
    document.removeEventListener('keyup', handleKeyRelease);
  };
}, []);
```
</details>

---

### Exercise 3: Implement a Countdown Timer

**Task**: Create a countdown timer that:
- Counts down from 60 to 0
- Updates every second
- Cleans up properly

<details>
<summary>🔍 Show Solution</summary>

```typescript
const [count, setCount] = useState(60);

useEffect(() => {
  const intervalId = setInterval(() => {
    setCount(prev => {
      if (prev <= 1) {
        clearInterval(intervalId);
        return 0;
      }
      return prev - 1;
    });
  }, 1000);

  return () => clearInterval(intervalId);
}, []); // ✅ Empty deps = run once on mount

return <div>Countdown: {count}</div>;
```
</details>

---

## ESLint Integration

### Automatic Detection

We have **custom ESLint rules** that automatically catch memory leaks!

### How It Works

```bash
# Run linting
npm run lint

# ESLint will catch memory leaks:
# ❌ error  Potential memory leak: setInterval created without cleanup
#    Use: const id = setInterval(...); return () => clearInterval(id);
```

### Rule Messages

| Rule | Detects | Message |
|------|---------|---------|
| `no-uncleaned-timers` | setInterval/setTimeout | "Potential memory leak: {{timerType}} created without cleanup" |
| `no-uncleaned-event-listeners` | addEventListener | "Potential memory leak: Event listener added without cleanup" |
| `no-uncleaned-websockets` | new WebSocket() | "Potential memory leak: WebSocket created without cleanup" |
| `no-uncleaned-subscriptions` | .subscribe() | "Potential memory leak: Subscription created without cleanup" |

### Configuration

Already configured in `eslint.config.js`:

```javascript
{
  "memory-leak/no-uncleaned-timers": "error",
  "memory-leak/no-uncleaned-event-listeners": "error",
  "memory-leak/no-uncleaned-websockets": "error",
  "memory-leak/no-uncleaned-subscriptions": "error",
}
```

---

## Quick Reference

### Decision Tree

```
┌─────────────────────────────────────┐
│  Using useEffect with resources?     │
└──────────┬───────────────────────────┘
           │
           ├─► Creating timer? → ✅ Return () => clearTimeout()
           │
           ├─► Adding listener? → ✅ Return () => removeEventListener()
           │
           ├─► Opening WebSocket? → ✅ Return () => ws.close()
           │
           ├─► Subscribing? → ✅ Return () => unsubscribe()
           │
           └─► Fetching data? → ✅ Use mounted ref
```

### Checklist

Before committing code, verify:

- [ ] Every `setInterval` has `clearInterval` in cleanup
- [ ] Every `setTimeout` has `clearTimeout` in cleanup
- [ ] Every `addEventListener` has `removeEventListener` in cleanup
- [ ] Every `WebSocket` has `close()` in cleanup
- [ ] Every `.subscribe()` has `.unsubscribe()` in cleanup
- [ ] Async state updates check `isMounted` ref
- [ ] No ESLint errors

---

## Quiz

Test your knowledge!

### Question 1

What's wrong with this code?

```typescript
useEffect(() => {
  setInterval(() => fetchData(), 5000);
}, []);
```

<details>
<summary>Show Answer</summary>

**Missing cleanup!** The interval will run forever. Fix:

```typescript
useEffect(() => {
  const id = setInterval(() => fetchData(), 5000);
  return () => clearInterval(id);
}, []);
```
</details>

---

### Question 2

True or False: You only need cleanup for `setInterval`, not `setTimeout`.

<details>
<summary>Show Answer</summary>

**False!** Both `setInterval` and `setTimeout` need cleanup. `setTimeout` may fire after unmount if not cleared.

```typescript
// ✅ Both need cleanup
useEffect(() => {
  const interval = setInterval(cb, 1000);
  const timeout = setTimeout(cb, 5000);
  return () => {
    clearInterval(interval);
    clearTimeout(timeout);
  };
}, []);
```
</details>

---

### Question 3

How many event listeners will be added after 5 mounts/unmounts?

```typescript
useEffect(() => {
  window.addEventListener('resize', handleResize);
}, []);
```

<details>
<summary>Show Answer</summary>

**5 listeners!** Each mount adds a listener, none are removed. After 5 mounts, you have 5 listeners all firing on resize.

**Fix**:
```typescript
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```
</details>

---

### Question 4

What does this ESLint error mean?

```
error  Potential memory leak: WebSocket created without cleanup.
Use: return () => ws.close();
```

<details>
<summary>Show Answer</summary>

You created a WebSocket but didn't close it when the component unmounts. **Fix**:

```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000');
  return () => ws.close(); // ✅ Add this
}, []);
```
</details>

---

## Best Practices Summary

### DO ✅

1. **Always return cleanup function** when creating resources in useEffect
2. **Store resource references** in variables for cleanup
3. **Use refs for WebSockets** and async state updates
4. **Run ESLint** before committing
5. **Test with Chrome DevTools** Memory profiler

### DON'T ❌

1. **Don't create resources** without cleanup plan
2. **Don't rely on component unmounting** to clean up automatically
3. **Don't use state** for resource IDs (use refs instead)
4. **Don't ignore ESLint warnings** about memory leaks
5. **Don't setState** after unmount (use mounted ref)

---

## Resources

### Internal Documentation

- [Memory Leak Load Testing Guide](../frontend/scripts/memory-leak-load-test.md)
- [Redis Monitoring Guide](./REDIS_MONITORING_GUIDE.md)
- [ESLint Rules README](../frontend/eslint-rules/README.md)

### External Resources

- [React useEffect Cleanup](https://react.dev/reference/react/useEffect#parameters)
- [Chrome DevTools Memory Profiling](https://developer.chrome.com/docs/devtools/memory-problems/)
- [JavaScript Memory Management](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Memory_Management)

---

## Next Steps

1. **Review existing code**: Look for useEffect hooks without cleanup
2. **Run ESLint**: Fix any memory leak warnings
3. **Test with DevTools**: Profile your components
4. **Pair review**: Have a teammate review your cleanup code
5. **Stay vigilant**: Make cleanup a habit!

---

**Remember**: *A single memory leak may not seem like much, but over time, they compound. Proper cleanup is essential for a healthy application!*

---

## Appendix: Code Examples

### Complete Example: Real-Time Data Component

```typescript
import { useEffect, useRef, useState } from 'react';

interface RealTimeDataProps {
  url: string;
  onUpdate: (data: any) => void;
}

export function RealTimeData({ url, onUpdate }: RealTimeDataProps) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    // ✅ Track mount state
    isMountedRef.current = true;

    // ✅ Create WebSocket
    wsRef.current = new WebSocket(url);

    wsRef.current.onopen = () => {
      if (isMountedRef.current) {
        setIsConnected(true);
      }
    };

    wsRef.current.onmessage = (event) => {
      if (isMountedRef.current) {
        const data = JSON.parse(event.data);
        onUpdate(data);
      }
    };

    wsRef.current.onclose = () => {
      if (isMountedRef.current) {
        setIsConnected(false);

        // ✅ Attempt reconnection after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            // Reconnect logic would go here
          }
        }, 5000);
      }
    };

    // ✅ Cleanup function
    return () => {
      isMountedRef.current = false; // Mark as unmounted

      if (wsRef.current) {
        wsRef.current.close(); // Close WebSocket
        wsRef.current = null;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current); // Clear timeout
        reconnectTimeoutRef.current = null;
      }
    };
  }, [url, onUpdate]);

  return (
    <div>
      Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
    </div>
  );
}
```

This example demonstrates:
- ✅ Proper WebSocket cleanup
- ✅ Reconnection timeout cleanup
- ✅ Mounted ref for async operations
- ✅ Nullifying refs

---

**Questions? Ask in #dev-frontend channel or create a GitHub issue!**
