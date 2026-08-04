# 🎓 Memory Leak Prevention Training
## Team Workshop - Presentation Slides

---

## Slide 1: Title & Overview

# 🔒 Memory Leak Prevention
### Making PsychSync Frontend Memory-Safe

**Presented by**: Frontend Team
**Duration**: 60 minutes
**Goal**: Eliminate memory leaks from our codebase

---

## Slide 2: What We'll Learn

### Agenda 📋

1. ✅ Understanding Memory Leaks (10 min)
2. ✅ Memory-Safe Hooks Demo (15 min)
3. ✅ Hands-On Practice (20 min)
4. ✅ Code Review Patterns (10 min)
5. ✅ Q&A (5 min)

**By the end, you'll know how to:**
- Prevent memory leaks in your code
- Use our new cleanup hooks
- Review PRs for memory leak patterns

---

## Slide 3: What is a Memory Leak?

### Definition 🔍

A **memory leak** occurs when your component allocates resources but fails to clean them up when unmounting.

### Common Causes 🐛

```tsx
❌ setTimeout without cleanup
❌ setInterval without cleanup
❌ addEventListener without removeEventListener
❌ WebSocket without close()
❌ Subscriptions without unsubscribe()
```

---

## Slide 4: Why This Matters 💡

### Real-World Impact

```
User Journey:
├── Logs in → Components mount
├── Navigates → Components should unmount
├── But: Timers/listeners stay in memory! 🐛
├── Result: Memory accumulates over time
└── Outcome: Browser slows down, crashes
```

### The Math 📊

```
20 users × 10 components × 5 MB leaked each
= 1 GB of wasted memory per hour!
```

---

## Slide 5: The Solution 🛡️

### Three Layers of Protection

```
┌─────────────────────────────────────┐
│ 1. PREVENTION: Cleanup Hooks        │
│    - useTimeout(), useInterval()     │
│    - useEventListener()              │
│    - useWebSocket()                 │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 2. DETECTION: Pre-commit Hook       │
│    - Blocks commits with leaks      │
│    - Suggests fixes                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 3. VERIFICATION: CI/CD              │
│    - Runs ESLint on all PRs         │
│    - Comments with results          │
└─────────────────────────────────────┘
```

---

## Slide 6: Cleanup Hooks Demo 🎯

### useTimeout - Simple Replacement

**Before** ❌:
```tsx
useEffect(() => {
  setTimeout(() => {
    setShowToast(false);
  }, 3000);
}, []);
```

**After** ✅:
```tsx
import { useTimeout } from '@/hooks/cleanupHooks';

useTimeout(() => {
  setShowToast(false);
}, 3000);
```

**Benefits**:
- ✅ Automatic cleanup
- ✅ No useEffect needed
- ✅ Less code
- ✅ Type-safe

---

## Slide 7: All Timer Hooks ⏰

### Available Hooks

```tsx
// Instead of setTimeout
useTimeout(callback, delay)

// Instead of setInterval
useInterval(callback, delay)

// Conditional timeout
useConditionalTimeout(callback, delay, condition)

// Debounce user input
const debounced = useDebounce(search, 300)

// Throttle scroll events
const throttled = useThrottle(handleScroll, 100)
```

---

## Slide 8: Event Listener Hooks 🎪

### Common Patterns

```tsx
// Instead of addEventListener
useEventListener('click', handler, document)

// Window resize
useWindowResize(() => setWidth(window.innerWidth))

// Keyboard shortcuts
useKeyDown('Escape', handleEscape)

// Click outside (modals/dropdowns)
useClickOutside(ref, closeModal)

// Media queries
const isMobile = useMediaQuery('(max-width: 768px)')
```

---

## Slide 9: WebSocket Hook 🌐

### Memory-Safe WebSocket

**Before** ❌:
```tsx
useEffect(() => {
  const ws = new WebSocket('ws://...');
  ws.onmessage = (e) => setData(e.data);
  return () => ws.close();
}, []);
```

**After** ✅:
```tsx
const ws = useWebSocket('ws://...', {
  onMessage: (data) => setData(data),
  onOpen: () => console.log('Connected'),
  onClose: () => console.log('Disconnected')
});

// Bonus: Auto-reconnects!
```

---

## Slide 10: Hands-On Exercise #1 ✍️

### Fix This Memory Leak

```tsx
function Notification() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setVisible(false);
    }, 3000);
  }, []);

  return visible ? <div>Notification!</div> : null;
}
```

**Your Task**: Fix the memory leak (2 minutes)

---

## Slide 11: Solution #1 ✅

### Option 1: Manual Cleanup
```tsx
useEffect(() => {
  const timerId = setTimeout(() => {
    setVisible(false);
  }, 3000);
  return () => clearTimeout(timerId);
}, []);
```

### Option 2: Use Cleanup Hook (Better!)
```tsx
useTimeout(() => {
  setVisible(false);
}, 3000);
```

---

## Slide 12: Hands-On Exercise #2 ✍️

### Fix This Event Listener Leak

```tsx
function WindowWidth() {
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
  }, []);

  return <div>Width: {width}px</div>;
}
```

**Your Task**: Fix the memory leak (2 minutes)

---

## Slide 13: Solution #2 ✅

### Option 1: Manual Cleanup
```tsx
useEffect(() => {
  const handleResize = () => setWidth(window.innerWidth);
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);
```

### Option 2: Use Cleanup Hook (Better!)
```tsx
useWindowResize(() => {
  setWidth(window.innerWidth);
});
```

---

## Slide 14: Code Review Checklist 👀

### What to Look For

#### ✅ Good Patterns
```tsx
// Using custom hooks
useTimeout(callback, delay)
useEventListener('click', handler)

// Proper cleanup
useEffect(() => {
  const timer = setTimeout(...);
  return () => clearTimeout(timer);
}, []);
```

#### ❌ Bad Patterns
```tsx
// Raw timers without cleanup
useEffect(() => {
  setTimeout(...);
}, []);

// Event listeners without cleanup
useEffect(() => {
  document.addEventListener(...);
}, []);
```

---

## Slide 15: Quick Reference Card 📝

### DO's ✅
- Use cleanup hooks from `@/hooks/cleanupHooks`
- Run `npm run lint` before committing
- Check for cleanup in useEffect

### DON'Ts ❌
- Use raw setTimeout/setInterval without cleanup
- Use addEventListener without removeEventListener
- Ignore ESLint memory-leak warnings

### Import Statement
```tsx
import {
  useTimeout,
  useInterval,
  useEventListener
} from '@/hooks/cleanupHooks';
```

---

## Slide 16: What's Already Fixed ✅

### Files Updated (Week 1-3)

✅ `src/pages/VerifyEmail.tsx`
✅ `src/pages/WellbeingAssessment.tsx`
✅ `src/contexts/AuthContext.tsx`
✅ `src/contexts/ErrorContext.tsx`

### Tools Installed

✅ ESLint memory leak detection
✅ Pre-commit hooks
✅ CI/CD workflow
✅ 13 cleanup hooks

---

## Slide 17: Your Action Items 🎯

### This Week

1. ✅ Review documentation (5 min)
   - `MEMORY_LEAK_QUICKFIX_GUIDE.md`
   - `src/hooks/cleanupHooks.ts`

2. ✅ Practice in next PR (15 min)
   - Use 1-2 cleanup hooks
   - See how easy it is!

3. ✅ Help a teammate (10 min)
   - Share what you learned
   - Review their code together

### Next Week

4. ⏳ Refactor existing components (30 min)
   - Replace old patterns gradually
   - No rush - do it when touching files

---

## Slide 18: Resources 📚

### Documentation

- **Quick Guide**: `MEMORY_LEAK_QUICKFIX_GUIDE.md`
- **Full Training**: `TEAM_TRAINING_MEMORY_LEAKS.md`
- **Hook Docs**: `src/hooks/cleanupHooks.ts`

### Commands

```bash
# Check for leaks
npm run lint | grep "memory-leak"

# Run tests
npm test -- src/hooks/__tests__

# Pre-commit test
.husky/pre-commit
```

---

## Slide 19: Quiz Time! 🧠

### Q1: Which has a memory leak?

A) `useTimeout(() => {}, 1000)`
B) `useEffect(() => { setTimeout(() => {}, 1000); }, [])`
C) `useEventListener('click', handler)`

**Answer**: B (no cleanup)

---

### Q2: How do you fix this?

```tsx
useEffect(() => {
  if (isActive) {
    setInterval(() => {}, 1000);
  }
}, [isActive]);
```

**Answer**:
```tsx
// Option 1:
useEffect(() => {
  let intervalId;
  if (isActive) {
    intervalId = setInterval(() => {}, 1000);
  }
  return () => {
    if (intervalId) clearInterval(intervalId);
  };
}, [isActive]);

// Option 2 (Better!):
useInterval(() => {}, isActive ? 1000 : null);
```

---

## Slide 20: Success Metrics 📊

### What We've Achieved

| **Metric** | **Before** | **After** |
|------------|------------|-----------|
| Memory leaks in prod | 3 critical | 0 ✅ |
| Cleanup hooks | 0 | 13 ✅ |
| Automated detection | ❌ | ✅ |
| Team training | ❌ | ✅ |
| Documentation | ❌ | 5 guides ✅ |

### Next Steps

- Week 4: Team adoption
- Week 5-6: Full rollout
- Ongoing: Zero tolerance for new leaks!

---

## Slide 21: Q&A ❓

### Common Questions

**Q**: Do I need to refactor all my code now?
**A**: No! Refactor when you touch files. New code should always use hooks.

**Q**: What if I forget to add cleanup?
**A**: Pre-commit hook will catch it before you commit!

**Q**: Are hooks always better than manual cleanup?
**A**: Yes! They're tested, type-safe, and consistent.

**Q**: Where can I get help?
**A**:
- Check `MEMORY_LEAK_QUICKFIX_GUIDE.md`
- Ask in #frontend
- Review `src/hooks/cleanupHooks.ts` examples

---

## Slide 22: Thank You! 🎉

### Key Takeaways

1. ✅ **Memory leaks are preventable** - Use cleanup hooks
2. ✅ **Automation helps** - Pre-commit hooks catch issues
3. ✅ **Team effort** - We're all in this together

### Remember

> "Clean up as you code, not after!"

### Questions?

- #frontend channel
- Team standup
- Review the documentation

---

## Slide 23: Bonus: Advanced Pattern 💎

### Conditional Cleanup (The ESLint-Satisfying Pattern)

```tsx
useEffect(() => {
  let timerId: NodeJS.Timeout | undefined;

  if (shouldRun) {
    timerId = setTimeout(action, delay);
  }

  return () => {
    if (timerId) clearTimeout(timerId);
  };
}, [shouldRun]);
```

**Why This Works**:
- ✅ Unconditional cleanup (ESLint can detect)
- ✅ Conditional creation (efficient)
- ✅ Type-safe
- ✅ Handles edge cases

---

## End of Presentation 🎯

### Ready to Write Memory-Safe Code!

**Start Now**:
```tsx
import { useTimeout, useEventListener } from '@/hooks/cleanupHooks';

// Your component here
```

**Questions? Let's discuss!**
