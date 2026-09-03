# Memory Leak Quick-Fix Guide
## For Developers

**Status**: 🚨 19 Memory Leaks Detected - **Fix Required**
**Priority**: 🔴 HIGH

---

## 🔥 Quick Fix Patterns

### Pattern 1: setTimeout/setInterval Cleanup

#### ❌ BAD (Detected by ESLint):
```typescript
useEffect(() => {
  setTimeout(() => {
    console.log('Done');
  }, 1000);
}, []);
```

#### ✅ GOOD (Fixed):
```typescript
useEffect(() => {
  const timer = setTimeout(() => {
    console.log('Done');
  }, 1000);

  return () => clearTimeout(timer); // ← ADD THIS
}, []);
```

#### ✅ EVEN BETTER (With Ref):
```typescript
useEffect(() => {
  const timerRef = { current: setTimeout(() => {
    console.log('Done');
  }, 1000) };

  return () => clearTimeout(timerRef.current);
}, []);
```

---

### Pattern 2: Event Listener Cleanup

#### ❌ BAD (Detected by ESLint):
```typescript
useEffect(() => {
  document.addEventListener('click', handleClick);
}, []);
```

#### ✅ GOOD (Fixed):
```typescript
useEffect(() => {
  document.addEventListener('click', handleClick);

  return () => {
    document.removeEventListener('click', handleClick); // ← ADD THIS
  };
}, []);
```

---

### Pattern 3: WebSocket Cleanup

#### ❌ BAD (Detected by ESLint):
```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000');
  ws.onmessage = (e) => console.log(e.data);
}, []);
```

#### ✅ GOOD (Fixed):
```typescript
const wsRef = useRef<WebSocket | null>(null);

useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000');
  wsRef.current = ws;

  ws.onmessage = (e) => console.log(e.data);

  return () => {
    ws.close(); // ← ADD THIS
    wsRef.current = null;
  };
}, []);
```

---

## 📋 Your Action Items

### Step 1: Run the Linter
```bash
cd frontend
npm run lint | grep "memory-leak"
```

### Step 2: Find Your File
Look for lines like:
```
src/components/YourComponent.tsx
  123:21  error  Potential memory leak: setTimeout created without cleanup
```

### Step 3: Apply the Fix
1. Open the file
2. Go to the line number
3. Add the cleanup function (see patterns above)
4. Save the file

### Step 4: Verify Fix
```bash
npm run lint | grep "YourComponent"
# Should return empty (no errors)
```

---

## 🚀 Common Cleanup Patterns

### Timers
```typescript
// setTimeout
const timer = setTimeout(cb, delay);
return () => clearTimeout(timer);

// setInterval
const interval = setInterval(cb, delay);
return () => clearInterval(interval);
```

### Event Listeners
```typescript
const handler = () => {...};
element.addEventListener('event', handler);
return () => element.removeEventListener('event', handler);
```

### WebSockets
```typescript
const ws = new WebSocket(url);
return () => ws.close();
```

### Subscriptions (RxJS, etc.)
```typescript
const sub = observable.subscribe(next);
return () => sub.unsubscribe();
```

### Fetch with AbortController
```typescript
const abortController = new AbortController();

fetch(url, { signal: abortController.signal });

return () => abortController.abort();
```

---

## 🎯 Best Practices

### 1. **ALWAYS Return Cleanup Function**
If you create anything in useEffect, clean it up.

```typescript
useEffect(() => {
  // Setup
  const thing = createThing();

  // ALWAYS return cleanup
  return () => {
    thing.cleanup();
  };
}, []);
```

### 2. **Store References**
Keep IDs and references in variables so you can clean them up.

```typescript
useEffect(() => {
  const timerId = setTimeout(...);
  const subscription = observable.subscribe(...);

  return () => {
    clearTimeout(timerId);
    subscription.unsubscribe();
  };
}, []);
```

### 3. **Use Custom Hooks**
Don't repeat cleanup logic. Create hooks:

```typescript
// hooks/useCleanupTimer.ts
export function useCleanupTimer(callback: () => void, delay: number) {
  useEffect(() => {
    const timer = setTimeout(callback, delay);
    return () => clearTimeout(timer);
  }, [callback, delay]);
}

// Usage
useCleanupTimer(() => console.log('Done'), 1000);
```

---

## ❓ FAQ

**Q: What if I don't return anything?**
A: ESLint will error. You must return a cleanup function.

**Q: Can I disable the rule?**
A: ❌ NO. Memory leaks are critical. Fix the code instead.

**Q: What if I need the timer to persist?**
A: Store it in a useRef and clean it up when the component unmounts.

**Q: How do I test if the cleanup works?**
A: Use React's StrictMode and watch for console warnings.

---

## 🔗 Resources

- [React useEffect Cleanup](https://react.dev/reference/react/useEffect#cleaning-up-an-effect)
- [Memory Leak Guide](https://www.patterns.dev/posts/react-patterns-clean-up/)
- [Team Report](./MEMORY_LEAK_AUDIT_REPORT.md)

---

**Need Help?**
- Ask in #frontend-questions
- Check the team report for detailed examples
- Review existing hooks in `/src/hooks/` for patterns

---

**Remember**: Clean up as you code. Don't let memory leaks accumulate! 🧹
