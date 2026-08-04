# React Memory Leak Prevention Workshop

**Interactive hands-on workshop for learning React useEffect cleanup patterns**

---

## 🎯 Workshop Objectives

By the end of this workshop, you will be able to:
1. ✅ Identify memory leak patterns in React code
2. ✅ Apply the 5 golden rules of useEffect cleanup
3. ✅ Use custom hooks to prevent memory leaks
4. ✅ Review code for memory leak issues
5. ✅ Write leak-free React components

**Duration:** 90 minutes
**Prerequisites:** Basic React knowledge, familiarity with hooks

---

## 📚 Workshop Outline

### Part 1: Learn the Patterns (20 min)
- The 5 golden rules
- Common memory leak patterns
- Anti-patterns and how to fix them

### Part 2: Hands-On Practice (40 min)
- Exercise 1: Fix setTimeout leak
- Exercise 2: Fix async operation leak
- Exercise 3: Fix WebSocket leak
- Exercise 4: Fix event listener leak

### Part 3: Code Review Challenge (20 min)
- Review sample PRs
- Find and tag memory leaks
- Propose fixes

### Part 4: Quiz & Discussion (10 min)
- Knowledge check
- Q&A
- Best practices sharing

---

## 🎓 Part 1: Learn the Patterns

### The 5 Golden Rules (Quick Recap)

| Rule | What | Why |
|------|------|------|
| **1** | Return cleanup function | React calls it on unmount |
| **2** | Track mounted status | Prevents setState on unmounted component |
| **3** | Use AbortController | Cancels in-flight requests |
| **4** | Store refs for timers | Need IDs to clear them later |
| **5** | Clear ALL refs | Don't miss any resource |

---

### Common Memory Leak Patterns

#### Pattern 1: The "Zombie setTimeout"
```tsx
// ❌ LEAK: Timeout fires after unmount
useEffect(() => {
  setTimeout(() => {
    showToast('Notification');
  }, 5000);
}, []);
```

**Why it leaks:** Component unmounts, but timeout continues. When it fires, it tries to update state on unmounted component.

**Fix:** Use `useTimeoutWithCleanup` hook or manual cleanup.

---

#### Pattern 2: The "Orphaned Fetch"
```tsx
// ❌ LEAK: Request completes after unmount
useEffect(() => {
  fetch('/api/data')
    .then(res => res.json())
    .then(data => setData(data));  // ← Fires after unmount!
}, []);
```

**Why it leaks:** Fetch may complete after component unmounts. setState on unmounted component causes warning.

**Fix:** Use `useAsyncEffect` with AbortController.

---

#### Pattern 3: The "Forgotten Listener"
```tsx
// ❌ LEAK: Listener never removed
useEffect(() => {
  window.addEventListener('resize', handleResize);
}, []);
```

**Why it leaks:** Listener remains attached to window after component unmounts, causing memory leak.

**Fix:** Always remove event listeners in cleanup.

---

## 🛠️ Part 2: Hands-On Exercises

### Exercise 1: Fix setTimeout Leak (10 min)

**Scenario:** A notification system that auto-dismisses after 5 seconds.

**Problem Code:**
```tsx
function NotificationSystem() {
  const [notifications, setNotifications] = useState([]);

  const showNotification = (message) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message }]);

    // TODO: Fix the memory leak!
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  return <div>{/* render notifications */}</div>;
}
```

**Your Task:**
1. Identify the memory leak
2. Fix it using one of these approaches:
   - Option A: Manual cleanup with useRef
   - Option B: Use `useTimeoutWithCleanup` hook

**Solution:** <details>
<summary>Click to see solution</summary>

```tsx
function NotificationSystem() {
  const [notifications, setNotifications] = useState([]);
  const timeoutRefs = useRef(new Map());

  useEffect(() => {
    return () => {
      // Clear all pending timeouts on unmount
      timeoutRefs.current.forEach(timeout => clearTimeout(timeout));
      timeoutRefs.current.clear();
    };
  }, []);

  const showNotification = (message) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message }]);

    const timeoutId = setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
      timeoutRefs.current.delete(id);
    }, 5000);

    timeoutRefs.current.set(id, timeoutId);
  };

  return <div>{/* render notifications */}</div>;
}
```

</details>

---

### Exercise 2: Fix Async Operation Leak (10 min)

**Scenario:** A user profile component that fetches data on mount.

**Problem Code:**
```tsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      const response = await fetch(`/api/users/${userId}`);
      const data = await response.json();
      setUser(data);  // TODO: May run after unmount!
      setLoading(false);
    };

    fetchUser();
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  return <div>{user.name}</div>;
}
```

**Your Task:**
1. Identify the memory leak
2. Fix it using one of these approaches:
   - Option A: Manual mounted check
   - Option B: Use `useAsyncEffect` hook with AbortController

**Solution:** <details>
<summary>Click to see solution</summary>

```tsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useAsyncEffect(async (signal, isMounted) => {
    try {
      const response = await fetch(`/api/users/${userId}`, {
        signal,  // Pass AbortSignal for cancellation
      });

      if (!isMounted()) return;  // Check if still mounted

      const data = await response.json();

      if (isMounted()) {
        setUser(data);
        setLoading(false);
      }
    } catch (error) {
      if (isMounted() && error.name !== 'AbortError') {
        setLoading(false);
      }
    }
  }, [userId]);

  if (loading) return <div>Loading...</div>;
  return <div>{user.name}</div>;
}
```

</details>

---

### Exercise 3: Fix WebSocket Leak (10 min)

**Scenario:** A real-time dashboard that connects to WebSocket.

**Problem Code:**
```tsx
function RealtimeDashboard() {
  const [data, setData] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://api.example.com/dashboard');

    ws.onmessage = (event) => {
      setData(JSON.parse(event.data));
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    // TODO: Fix the memory leak!
  }, []);

  return <Dashboard data={data} />;
}
```

**Your Task:**
1. Identify the memory leak
2. Fix it by closing the WebSocket in cleanup

**Solution:** <details>
<summary>Click to see solution</summary>

```tsx
function RealtimeDashboard() {
  const [data, setData] = useState([]);

  useEffect(() => {
    const ws = new WebSocket('ws://api.example.com/dashboard');

    ws.onmessage = (event) => {
      // Check if connection is still open before updating
      if (ws.readyState === WebSocket.OPEN) {
        setData(JSON.parse(event.data));
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();  // Close connection on unmount
    };
  }, []);

  return <Dashboard data={data} />;
}
```

</details>

---

### Exercise 4: Fix Event Listener Leak (10 min)

**Scenario:** A component that tracks window size.

**Problem Code:**
```tsx
function WindowTracker() {
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    // TODO: Fix the memory leak!
    window.addEventListener('resize', handleResize);

    // Initial size
    handleResize();
  }, []);

  return <div>Size: {size.width} x {size.height}</div>;
}
```

**Your Task:**
1. Identify the memory leak
2. Fix it by removing event listener in cleanup

**Solution:** <details>
<summary>Click to see solution</summary>

```tsx
function WindowTracker() {
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);

    // Initial size
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);  // Remove listener
    };
  }, []);

  return <div>Size: {size.width} x {size.height}</div>;
}
```

</details>

---

## 🔍 Part 3: Code Review Challenge

### Challenge: Find the Leaks

Review the following code snippets and identify all memory leaks. Tag them with the rule number they violate (1-5).

#### Snippet 1:
```tsx
useEffect(() => {
  const interval = setInterval(() => {
    console.log('Heartbeat');
  }, 1000);
}, []);
```

<details>
<summary>Answer</summary>

**Violation:** Rule #1 (no cleanup), Rule #4 (no ref storage)
**Fix:**
```tsx
useEffect(() => {
  const interval = setInterval(() => {
    console.log('Heartbeat');
  }, 1000);

  return () => clearInterval(interval);
}, []);
```

Or better:
```tsx
useIntervalWithCleanup(() => {
  console.log('Heartbeat');
}, 1000);
```

</details>

---

#### Snippet 2:
```tsx
useEffect(() => {
  const fetchData = async () => {
    const response = await axios.get('/api/data');
    setData(response.data);
  };

  fetchData();
}, [id]);
```

<details>
<summary>Answer</summary>

**Violation:** Rule #2 (no mounted check), Rule #3 (no AbortController)
**Fix:**
```tsx
useAsyncEffect(async (signal, isMounted) => {
  const response = await axios.get('/api/data', { signal });
  if (isMounted()) {
    setData(response.data);
  }
}, [id]);
```

</details>

---

#### Snippet 3:
```tsx
useEffect(() => {
  document.addEventListener('keydown', handleKeyDown);
  document.addEventListener('keyup', handleKeyUp);

  return () => {
    document.removeEventListener('keydown', handleKeyDown);
  };
}, []);
```

<details>
<summary>Answer</summary>

**Violation:** Rule #5 (not all resources cleaned - missing keyup)
**Fix:**
```tsx
useEffect(() => {
  document.addEventListener('keydown', handleKeyDown);
  document.addEventListener('keyup', handleKeyUp);

  return () => {
    document.removeEventListener('keydown', handleKeyDown);
    document.removeEventListener('keyup', handleKeyUp);  // ✅ Add this
  };
}, []);
```

</details>

---

#### Snippet 4:
```tsx
useEffect(() => {
  const timeout1 = setTimeout(() => setState1('A'), 1000);
  const timeout2 = setTimeout(() => setState2('B'), 2000);
  const timeout3 = setTimeout(() => setState3('C'), 3000);

  return () => {
    clearTimeout(timeout1);
    clearTimeout(timeout2);
  };
}, []);
```

<details>
<summary>Answer</summary>

**Violation:** Rule #5 (not all resources cleaned - missing timeout3)
**Fix:**
```tsx
return () => {
  clearTimeout(timeout1);
  clearTimeout(timeout2);
  clearTimeout(timeout3);  // ✅ Add this
};
```

</details>

---

## ✅ Part 4: Quiz & Discussion

### Quiz Questions

#### Q1: Which of the following is a memory leak?

**A)**
```tsx
useEffect(() => {
  const timer = setTimeout(() => {}, 1000);
  return () => clearTimeout(timer);
}, []);
```

**B)**
```tsx
useEffect(() => {
  setTimeout(() => {}, 1000);
}, []);
```

**C)**
```tsx
useEffect(() => {
  setTimeout(() => {}, 1000);
  return () => {};
}, []);
```

<details>
<summary>Answer</summary>

**Answer:** **B** and **C** are both memory leaks!

**A** ✅ Correct - Has proper cleanup
**B** ❌ Leak - No cleanup function at all
**C** ❌ Leak - Empty cleanup doesn't clear timeout

</details>

---

#### Q2: What's the BEST way to handle async operations in useEffect?

**A)** Manual mounted check
**B)** useAsyncEffect hook
**C)** AbortController
**D)** All of the above, depending on the situation

<details>
<summary>Answer</summary>

**Answer:** **D** - All approaches are valid!

- **A** (Manual check): Works, but requires careful implementation
- **B** (useAsyncEffect): Best for most cases - handles AbortController + mounted check
- **C** (AbortController): Required for fetch/axios to cancel requests

The **recommended** approach is **B** (useAsyncEffect) as it combines A and C.

</details>

---

#### Q3: True or False: Empty cleanup function `return () => {}` is sufficient if no resources are created.

<details>
<summary>Answer</summary>

**Answer:** **TRUE** - ✅

If the useEffect doesn't create any resources (timers, listeners, subscriptions, etc.), then no cleanup is needed. An empty cleanup function or no cleanup function at all is fine in this case.

However, if you're **unsure**, it's safer to add a cleanup function.

</details>

---

#### Q4: How many cleanup functions should one useEffect have?

<details>
<summary>Answer</summary>

**Answer:** **Exactly ONE** - ✅

```tsx
useEffect(() => {
  // Setup code...

  return () => {
    // ALL cleanup happens here
  };
}, []);
```

You cannot have multiple return statements. If you need to clean up multiple resources, do it all in the single cleanup function.

</details>

---

### Discussion Questions

1. **Why does React warn about state updates on unmounted components?**
   - Discussion: Causes memory leaks, stale UI, confusion

2. **What's the downside of NOT using AbortController for HTTP requests?**
   - Discussion: Unnecessary network usage, wasted bandwidth, server load

3. **When should you use a custom hook vs manual cleanup?**
   - Discussion: Custom hooks for reusable patterns, manual for one-off cases

4. **How do you test that your cleanup is working?**
   - Discussion: React DevTools Profiler, memory profiler, console warnings

---

## 🎯 Take-Home Exercise

### Practice Task: Audit Your Own Code

1. Find a component you wrote recently
2. Check all useEffect hooks
3. Run through the 5-rule checklist
4. Fix any memory leaks you find
5. Share with the team for feedback

---

## 📚 Additional Resources

- **Guide:** `frontend/REACT_EFFECT_CLEANUP_GUIDE.md`
- **Checklist:** `frontend/CODE_REVIEW_CHECKLIST.md`
- **Hooks:** `frontend/src/hooks/useAsyncEffect.ts`
- **ESLint:** `frontend/.eslintrc.react-memory-leaks.js`

---

## ✅ Workshop Completion Checklist

After completing this workshop, you should be able to:

- [ ] Explain why memory leaks happen in React
- [ ] Identify memory leak patterns in code
- [ ] Apply all 5 golden rules of useEffect cleanup
- [ ] Use custom hooks (useAsyncEffect, useTimeoutWithCleanup)
- [ ] Review code for memory leak issues
- [ ] Write leak-free React components

**Congratulations!** 🎉 You're now a React memory leak prevention expert!

---

## 💡 Pro Tips

1. **When in doubt, add cleanup** - It's better to over-clean than to leak
2. **Use custom hooks** - They encapsulate best practices
3. **Run ESLint** - Automated rules catch many issues
4. **Profile memory** - Use Chrome DevTools to verify
5. **Review your code** - Use the checklist before committing

---

**Happy Coding! 🚀**
