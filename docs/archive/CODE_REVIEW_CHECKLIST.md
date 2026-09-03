# Code Review Checklist: React useEffect Memory Leaks

**Checklist for reviewing React useEffect hooks during code reviews**

---

## 🚦 Quick Checklist (30-Second Review)

For every `useEffect` in a PR, verify:

- [ ] **Has cleanup function?** (Does it `return () => {...}`?)
- [ ] **Timers cleared?** (All `setTimeout`/`setInterval` have matching `clearTimeout`/`clearInterval`)
- [ ] **Listeners removed?** (All `addEventListener` have matching `removeEventListener`)
- [ ] **Async safe?** (Mounted check OR AbortController for async operations)
- [ ] **All resources accounted for?** (Count created vs cleaned up resources)

**If any checkbox is unchecked → Request changes!**

---

## 🔍 Detailed Review Guide

### Step 1: Identify useEffect Hooks

```bash
# In the PR, search for: useEffect
# List all useEffect calls in changed files
```

### Step 2: Check Each useEffect

#### ✅ **Rule 1: Cleanup Function Present**

**What to look for:**
```tsx
// ✅ GOOD - Has cleanup
useEffect(() => {
  // ... setup code
  return () => {
    // ... cleanup code
  };
}, []);

// ❌ BAD - No cleanup
useEffect(() => {
  setTimeout(() => {}, 5000);
}, []);
```

**Review Question:**
> "Does this useEffect return a cleanup function?"

---

#### ✅ **Rule 2: All Timers Cleared**

**What to look for:**
```tsx
// ✅ GOOD - Timer is cleared
useEffect(() => {
  const timeoutId = setTimeout(() => {}, 5000);
  return () => clearTimeout(timeoutId);
}, []);

// ❌ BAD - Timer not cleared
useEffect(() => {
  setTimeout(() => {}, 5000);
  return () => {}; // Empty cleanup!
}, []);

// ❌ BAD - Multiple timers, not all cleared
useEffect(() => {
  setTimeout(() => console.log('1'), 1000);
  setTimeout(() => console.log('2'), 2000);
  return () => clearTimeout(timeout1); // Missed timeout2!
}, []);
```

**Review Questions:**
> "Count setTimeout/setInterval calls. Are there the same number of clearTimeout/clearInterval calls in the cleanup?"

---

#### ✅ **Rule 3: All Event Listeners Removed**

**What to look for:**
```tsx
// ✅ GOOD - Listener removed
useEffect(() => {
  const handler = () => {};
  window.addEventListener('resize', handler);
  return () => window.removeEventListener('resize', handler);
}, []);

// ❌ BAD - Listener not removed
useEffect(() => {
  window.addEventListener('resize', handleResize);
}, []);
```

**Review Questions:**
> "For every addEventListener, is there a matching removeEventListener in cleanup?"

---

#### ✅ **Rule 4: Async Operations Safe**

**What to look for:**

**Option A: Using useAsyncEffect hook (Preferred)**
```tsx
// ✅ GOOD - Uses useAsyncEffect
import { useAsyncEffect } from '@/hooks/useAsyncEffect';

useAsyncEffect(async (signal, isMounted) => {
  const data = await fetchData({ signal });
  if (isMounted()) {
    setState(data);
  }
}, []);
```

**Option B: Manual mounted check**
```tsx
// ✅ GOOD - Manual mounted check
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

**Option C: AbortController for HTTP**
```tsx
// ✅ GOOD - AbortController
useEffect(() => {
  const abortController = new AbortController();

  fetch('/api/data', { signal: abortController.signal })
    .then(res => res.json())
    .then(data => {
      if (!abortController.signal.aborted) {
        setState(data);
      }
    });

  return () => {
    abortController.abort();  // ✅ Cancel request
  };
}, []);
```

**❌ BAD - No mounted check or AbortController**
```tsx
useEffect(() => {
  fetch('/api/data')
    .then(res => res.json())
    .then(data => setState(data));  // ❌ May run after unmount!
}, []);
```

**Review Questions:**
> "Does this async operation check mounted status before setState?"
> "For HTTP requests, is AbortController used and passed to fetch/axios?"
> "Are AbortError/CanceledError properly handled?"

---

#### ✅ **Rule 5: All Resources Accounted For**

**What to look for:**
```tsx
// ✅ GOOD - All resources tracked and cleaned
useEffect(() => {
  const timeout1 = setTimeout(fn1, 1000);
  const timeout2 = setTimeout(fn2, 2000);
  const interval = setInterval(fn3, 5000);

  return () => {
    clearTimeout(timeout1);  // ✅ All cleared
    clearTimeout(timeout2);
    clearInterval(interval);
  };
}, []);

// ❌ BAD - Missing cleanup for timeout2
useEffect(() => {
  const timeout1 = setTimeout(fn1, 1000);
  const timeout2 = setTimeout(fn2, 2000);

  return () => {
    clearTimeout(timeout1);  // ❌ Missed timeout2!
  };
}, []);
```

**Review Questions:**
> "Count all resources created (timers, listeners, subscriptions). Does cleanup clear ALL of them?"

---

## 🚨 Red Flags (Request Changes Immediately)

### Pattern 1: Async useEffect Without Cleanup
```tsx
useEffect(() => {
  const fetchData = async () => {
    const data = await fetch('/api/data');
    setState(data);  // 🚩 RED FLAG
  };
  fetchData();
}, []);
```
**Action:** Reject PR. Request using `useAsyncEffect` hook or adding mounted check.

---

### Pattern 2: setTimeout/setInterval Without Cleanup
```tsx
useEffect(() => {
  setTimeout(() => {
    showToast('Hello');  // 🚩 RED FLAG
  }, 5000);
}, []);
```
**Action:** Reject PR. Request using `useTimeoutWithCleanup` hook.

---

### Pattern 3: Event Listeners Without Cleanup
```tsx
useEffect(() => {
  window.addEventListener('scroll', handleScroll);  // 🚩 RED FLAG
}, []);
```
**Action:** Reject PR. Request adding `removeEventListener` in cleanup.

---

### Pattern 4: Empty Cleanup Function
```tsx
useEffect(() => {
  const timeout = setTimeout(() => {}, 5000);
  return () => {};  // 🚩 RED FLAG - Does nothing!
}, []);
```
**Action:** Reject PR. Cleanup function must actually clean up resources.

---

## ✅ Green Flags (Approved Patterns)

### Pattern 1: Using Custom Hooks
```tsx
// ✅ APPROVED - useAsyncEffect
useAsyncEffect(async (signal, isMounted) => {
  const data = await fetchData({ signal });
  if (isMounted()) setState(data);
}, []);

// ✅ APPROVED - useTimeoutWithCleanup
useTimeoutWithCleanup(() => {
  setToast(null);
}, 5000);

// ✅ APPROVED - useIntervalWithCleanup
useIntervalWithCleanup(() => {
  refreshData();
}, 30000);
```

### Pattern 2: Proper AbortController Usage
```tsx
// ✅ APPROVED
useEffect(() => {
  const abortController = new AbortController();

  fetch('/api/data', { signal: abortController.signal })
    .then(res => res.json())
    .then(data => {
      if (!abortController.signal.aborted) {
        setState(data);
      }
    })
    .catch(err => {
      if (err.name !== 'AbortError') {
        console.error(err);
      }
    });

  return () => abortController.abort();
}, []);
```

### Pattern 3: Manual Mounted Check
```tsx
// ✅ APPROVED
useEffect(() => {
  let isMounted = true;

  const fetchData = async () => {
    const data = await apiCall();
    if (isMounted) {
      setState(data);
    }
  };

  fetchData();

  return () => {
    isMounted = false;
  };
}, []);
```

---

## 📋 Pre-Merge Checklist

Before approving any PR with React hooks, verify:

### Files Changed
- [ ] All files with useEffect changes reviewed
- [ ] ESLint passes with memory leak rules
- [ ] No React warnings in console

### useEffect Hooks in PR
- [ ] Every useEffect has a cleanup function (if it creates resources)
- [ ] All timers (setTimeout/setInterval) are cleared
- [ ] All event listeners (addEventListener) are removed
- [ ] All async operations have mounted checks or AbortController
- [ ] All WebSocket connections are closed
- [ ] All subscriptions are unsubscribed

### Testing
- [ ] Component mounts and unmounts without errors
- [ ] Rapid navigation doesn't cause warnings
- [ ] Memory profiler shows no detached DOM nodes

---

## 💡 Comments to Use

### Requesting Changes
```markdown
@developer This useEffect has a memory leak:

**Issue:** Async operation without mounted check or AbortController

**Fix:** Use the `useAsyncEffect` hook from `@/hooks/useAsyncEffect`:

\`\`\`tsx
import { useAsyncEffect } from '@/hooks/useAsyncEffect';

useAsyncEffect(async (signal, isMounted) => {
  const data = await fetchData({ signal });
  if (isMounted()) {
    setState(data);
  }
}, [dependency]);
\`\`\`

**Why:** If the component unmounts before the fetch completes, it will try to update state on an unmounted component, causing a memory leak and React warning.

**Reference:** See `frontend/REACT_EFFECT_CLEANUP_GUIDE.md` Rule #2 and #3
```

### Approving
```markdown
✅ All useEffect hooks have proper cleanup functions.
✅ Async operations use AbortController.
✅ Timers and listeners are properly cleaned up.

LGTM! Great job following the memory leak prevention patterns.
```

---

## 🎓 Learning Resources

For developers new to these patterns:

1. **Read the guide:** `frontend/REACT_EFFECT_CLEANUP_GUIDE.md`
2. **Review examples:** Check `hooks/useAsyncEffect.ts` for reference implementations
3. **Practice:** Try the interactive workshop (see `WORKSHOP_MEMORY_LEAKS.md`)
4. **Ask questions:** Tag team lead for review if unsure

---

## 🔧 ESLint Integration

The codebase includes automated ESLint rules to catch these issues:

```bash
# Run ESLint with memory leak rules
npm run lint -- --plugin=react-memory-leaks

# Fix auto-fixable issues
npm run lint -- --plugin=react-memory-leaks --fix
```

**Note:** Some issues require manual review and can't be auto-fixed.

---

**Remember:** When in doubt, add a cleanup function! It's better to over-clean than to leak memory.
