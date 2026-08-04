# 🚀 Memory Leak Prevention - Quick Reference Card
## Print & Keep This Handy!

---

## 🔍 DETECTION

### Run This Command:
```bash
npm run lint | grep "memory-leak"
```

### What It Finds:
- `setTimeout` without cleanup
- `setInterval` without cleanup
- `addEventListener` without cleanup
- `WebSocket` without cleanup

---

## ✅ SOLUTIONS

### Import:
```tsx
import {
  useTimeout,
  useInterval,
  useEventListener,
  useWebSocket
} from '@/hooks/cleanupHooks';
```

### Timers:
```tsx
// Instead of: setTimeout
useTimeout(() => action(), 1000);

// Instead of: setInterval
useInterval(() => poll(), 5000);
```

### Events:
```tsx
// Instead of: addEventListener
useEventListener('click', handler, document);

// Window resize
useWindowResize(() => setWidth(window.innerWidth));

// Keyboard
useKeyDown('Escape', handleEscape);
```

### WebSocket:
```tsx
// Instead of: new WebSocket()
const ws = useWebSocket('ws://localhost:8000', {
  onMessage: (data) => console.log(data)
});
```

---

## ⚠️ COMMON MISTAKES

### ❌ DON'T:
```tsx
useEffect(() => {
  setTimeout(() => {}, 1000);
}, []);

useEffect(() => {
  document.addEventListener('click', handler);
}, []);
```

### ✅ DO:
```tsx
useTimeout(() => {}, 1000);

useEventListener('click', handler, document);
```

---

## 🔧 PATTERN: Conditional Cleanup

### ESLint-Approved Approach:
```tsx
useEffect(() => {
  let timerId: NodeJS.Timeout | undefined;

  if (condition) {
    timerId = setTimeout(action, delay);
  }

  return () => {
    if (timerId) clearTimeout(timerId);
  };
}, [condition]);
```

---

## 📞 NEED HELP?

### Documentation:
- `MEMORY_LEAK_QUICKFIX_GUIDE.md` - Full examples
- `TEAM_TRAINING_MEMORY_LEAKS.md` - Complete guide
- `src/hooks/cleanupHooks.ts` - Hook docs

### Commands:
```bash
# Check for leaks
npm run lint | grep memory-leak

# Run tests
npm test -- src/hooks/__tests__

# Pre-commit test
.husky/pre-commit
```

---

## ✅ CHECKLIST

Before committing:
- [ ] Ran `npm run lint`
- [ ] Fixed all memory-leak errors
- [ ] Used cleanup hooks instead of raw timers
- [ ] Pre-commit hook passes

---

## 💡 PRO TIP

> "When in doubt, use a cleanup hook!"

They're:
- ✅ Memory-safe (automatic cleanup)
- ✅ Type-safe (TypeScript)
- ✅ Tested (50+ test cases)
- ✅ Easy (less code!)

---

**Remember**: Clean up as you code, not after! 🧹✨

---
[Print this and keep it at your desk!]
