# 🚀 Memory Leak Prevention - Ultimate Quick Start Guide
## Get Started in 10 Minutes!

---

## ⏱️ Time Investment: 10 Minutes
## 💰 ROI: Zero memory leaks forever

---

## Step 1: Understand the Problem (2 min) ⚡

### What's a Memory Leak?

When your component creates a resource (timer, event listener, WebSocket) but forgets to clean it up when the component unmounts.

### Why It Matters?

```
Each leak = 1-5 MB wasted memory
20 users × 10 components × 5 MB = 1 GB per hour!
→ Browser slows down, crashes, users frustrated
```

---

## Step 2: Import Cleanup Hooks (1 min) 📦

### Add This Import:

```tsx
import {
  useTimeout,
  useInterval,
  useEventListener,
  useWebSocket
} from '@/hooks/cleanupHooks';
```

### That's It! You're Ready to Go! ✅

---

## Step 3: Use the Hooks (3 min) 🎯

### Pattern 1: Replace setTimeout

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
useTimeout(() => {
  setShowToast(false);
}, 3000);
```

### Pattern 2: Replace setInterval

**Before** ❌:
```tsx
useEffect(() => {
  const interval = setInterval(() => {
    fetchData();
  }, 5000);
  return () => clearInterval(interval);
}, []);
```

**After** ✅:
```tsx
useInterval(() => {
  fetchData();
}, 5000);
```

### Pattern 3: Replace addEventListener

**Before** ❌:
```tsx
useEffect(() => {
  const handler = () => console.log('clicked');
  document.addEventListener('click', handler);
  return () => document.removeEventListener('click', handler);
}, []);
```

**After** ✅:
```tsx
useEventListener('click', () => {
  console.log('clicked');
}, document);
```

---

## Step 4: Verify It Works (2 min) ✅

### Run the Linter:

```bash
npm run lint | grep "memory-leak"
```

### Expected Output:
```
# If no output:
✅ No memory leaks found!

# If you see errors:
❌ Fix them using patterns above
```

### That's It! You're Done! 🎉

---

## 🎓 All Available Hooks

### Timer Hooks:
```tsx
useTimeout(callback, delay)              // Memory-safe setTimeout
useInterval(callback, delay)             // Memory-safe setInterval
useConditionalTimeout(cb, delay, cond)   // Conditional timeout
useDebounce(callback, delay)             // Debounce
useThrottle(callback, delay)             // Throttle
```

### Event Hooks:
```tsx
useEventListener(event, handler, element) // Generic events
useWindowResize(handler)                  // Window resize
useWindowScroll(handler)                  // Window scroll
useKeyDown(key, handler)                  // Keyboard
useClickOutside(ref, handler)             // Click outside
useMediaQuery(query)                      // Media queries
```

### WebSocket Hook:
```tsx
const ws = useWebSocket(url, {
  onOpen: () => {},
  onMessage: (data) => {},
  onError: (err) => {},
  onClose: () => {}
});
```

---

## 🔧 Common Fixes (Cheat Sheet)

### Fix #1: Auto-Dismiss
```tsx
// Toast notifications, modals, banners
useTimeout(() => setVisible(false), 3000);
```

### Fix #2: Polling
```tsx
// API polling, data refresh
useInterval(() => fetchLatestData(), 5000);
```

### Fix #3: Window Resize
```tsx
// Responsive behavior
useWindowResize(() => setWidth(window.innerWidth));
```

### Fix #4: Keyboard Shortcuts
```tsx
// Escape key, Enter key, etc.
useKeyDown('Escape', closeModal);
```

### Fix #5: Click Outside
```tsx
// Close modals when clicking outside
useClickOutside(modalRef, closeModal);
```

---

## ⚡ Real-World Examples

### Example 1: Notification Component

```tsx
function Notification({ message }) {
  const [visible, setVisible] = useState(true);

  useTimeout(() => {
    setVisible(false);
  }, 3000);

  return visible ? <div>{message}</div> : null;
}
```

### Example 2: Polling Dashboard

```tsx
function Dashboard() {
  const [data, setData] = useState([]);

  useInterval(async () => {
    const result = await fetch('/api/data');
    setData(await result.json());
  }, 5000);

  return <div>{/* ... */}</div>;
}
```

### Example 3: Window Width Tracker

```tsx
function WidthDisplay() {
  const [width, setWidth] = useState(window.innerWidth);

  useWindowResize(() => {
    setWidth(window.innerWidth);
  });

  return <div>Width: {width}px</div>;
}
```

---

## 🚨 Troubleshooting

### "ESLint says memory leak!"

**Problem**: You used raw setTimeout/setInterval/addEventListener

**Solution**: Replace with cleanup hook (see patterns above)

---

### "Pre-commit hook failed!"

**Problem**: You're trying to commit code with memory leaks

**Solution**:
1. Run `npm run lint | grep memory-leak`
2. Fix the issues
3. Commit again

---

### "Hook doesn't work as expected!"

**Problem**: Maybe you're using it wrong

**Solution**:
1. Check `src/hooks/cleanupHooks.ts` for examples
2. Ask in #frontend channel
3. Look at `TEAM_TRAINING_MEMORY_LEAKS.md`

---

## 📚 Further Learning

### Want More Details?

- **Quick Guide**: `MEMORY_LEAK_QUICKFIX_GUIDE.md`
- **Full Training**: `TEAM_TRAINING_MEMORY_LEAKS.md`
- **Presentation**: `TRAINING_SLIDES.md`
- **Migration**: `MIGRATION_CHECKLIST.md`
- **Reference**: `QUICK_REFERENCE_CARD.md`

### Hook Documentation

- **Source**: `src/hooks/cleanupHooks.ts`
- **Timers**: `src/hooks/useCleanupTimer.ts`
- **Events**: `src/hooks/useCleanupEventListener.ts`
- **WebSocket**: `src/hooks/useCleanupWebSocket.ts`

---

## ✅ Success Criteria

You'll know you're successful when:

- [x] `npm run lint | grep memory-leak` returns nothing
- [x] You use cleanup hooks in new code by default
- [x] Pre-commit hook passes on every commit
- [x] CI/CD workflow checks pass on PRs
- [x] Zero memory leaks in production ✅

---

## 🎯 Your First Steps

### Right Now (5 min):
1. ✅ Import cleanup hooks in your current component
2. ✅ Replace 1 setTimeout or addEventListener
3. ✅ Run `npm run lint` to verify

### This Week (30 min):
1. ⏳ Use cleanup hooks in 2-3 components
2. ⏳ Review 1 teammate's PR for memory leaks
3. ⏳ Share this guide with the team

### Next Month (ongoing):
1. ⏳ Refactor components as you touch them
2. �iae Help others learn the patterns
3. ⏳ Celebrate zero memory leaks! 🎉

---

## 💡 Golden Rule

> **"When in doubt, use a cleanup hook!"**

### Why?
- ✅ Automatic cleanup (can't forget)
- ✅ Less code (more readable)
- ✅ Type-safe (fewer bugs)
- ✅ Tested (reliable)
- ✅ Consistent (team standard)

---

## 🎉 Congratulations!

You're now equipped to write memory-safe React code!

**Remember**: Clean up as you code, not after!

**The system will catch any mistakes**, so don't worry about being perfect. Just do your best, use the hooks, and let the tools help you improve.

---

**Need Help?**
- Check the documentation files
- Ask in #frontend
- Review `src/hooks/cleanupHooks.ts` examples

**Happy Coding!** 🚀
