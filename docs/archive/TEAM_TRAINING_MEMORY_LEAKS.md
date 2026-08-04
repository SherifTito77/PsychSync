# 🎓 Team Training Guide: Memory Leak Prevention
## For PsychSync Frontend Developers

**Last Updated**: January 20, 2026
**Training Duration**: 60 minutes
**Prerequisites**: Basic React, TypeScript knowledge

---

## 🎯 Learning Objectives

By the end of this training, you will be able to:
1. ✅ Identify what causes memory leaks in React
2. ✅ Use memory-safe hooks instead of raw timers/events
3. ✅ Write cleanup functions for useEffect
4. ✅ Review code for memory leak patterns
5. ✅ Fix memory leaks when detected by ESLint

---

## 📚 Part 1: Understanding Memory Leaks (15 minutes)

### What is a Memory Leak?

A **memory leak** occurs when your component allocates resources (timers, event listeners, WebSocket connections) but fails to clean them up when the component unmounts.

**In Single Page Apps (SPAs)**:
- Users navigate frequently between pages
- Components mount and unmount constantly
- Each leak accumulates in browser memory
- **Result**: Browser slows down, crashes, or becomes unresponsive

### Real-World Impact

```
Scenario: 20 users × 10 components with leaks
├── Each leak: ~1-5 MB of memory
├── After 1 hour: 200-1000 MB wasted per user
├── Browser garbage collection becomes ineffective
└── User experience degrades significantly
```

### The Four Types of Memory Leaks

#### **1. Timer Leaks** (Most Common)
```tsx
// ❌ LEAK: setTimeout without cleanup
useEffect(() => {
  setTimeout(() => {
    showMessage('Hello!');
  }, 3000);
}, []);

// ✅ FIXED: Proper cleanup
useEffect(() => {
  const timerId = setTimeout(() => {
    showMessage('Hello!');
  }, 3000);
  return () => clearTimeout(timerId);
}, []);
```

#### **2. Event Listener Leaks**
```tsx
// ❌ LEAK: addEventListener without cleanup
useEffect(() => {
  document.addEventListener('click', handleClick);
}, []);

// ✅ FIXED: Proper cleanup
useEffect(() => {
  document.addEventListener('click', handleClick);
  return () => document.removeEventListener('click', handleClick);
}, []);
```

#### **3. WebSocket Leaks**
```tsx
// ❌ LEAK: WebSocket without cleanup
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000');
  ws.onmessage = (e) => console.log(e.data);
}, []);

// ✅ FIXED: Proper cleanup
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000');
  ws.onmessage = (e) => console.log(e.data);
  return () => ws.close();
}, []);
```

#### **4. Subscription Leaks**
```tsx
// ❌ LEAK: Subscription without cleanup
useEffect(() => {
  const subscription = observable.subscribe(data => {
    setState(data);
  });
}, []);

// ✅ FIXED: Proper cleanup
useEffect(() => {
  const subscription = observable.subscribe(data => {
    setState(data);
  });
  return () => subscription.unsubscribe();
}, []);
```

---

## 🛠️ Part 2: Memory-Safe Hooks (20 minutes)

### Introduction to Cleanup Hooks

We've created a library of **memory-safe hooks** that automatically handle cleanup. You should use these instead of raw timers/events/WebSockets.

### Location
```
src/hooks/cleanupHooks.ts - Master export file
src/hooks/useCleanupTimer.ts - Timer hooks
src/hooks/useCleanupEventListener.ts - Event hooks
src/hooks/useCleanupWebSocket.ts - WebSocket hooks
```

### Hook #1: useTimeout

Replaces `setTimeout` with automatic cleanup:

```tsx
// ❌ OLD WAY (Memory Leak Risk)
useEffect(() => {
  setTimeout(() => {
    setShowToast(false);
  }, 3000);
}, []);

// ✅ NEW WAY (Memory Safe)
import { useTimeout } from '@/hooks/cleanupHooks';

function MyComponent() {
  const [showToast, setShowToast] = useState(true);

  useTimeout(() => {
    setShowToast(false);
  }, 3000);

  return showToast ? <Toast /> : null;
}
```

**When to use**:
- Delayed state updates
- Auto-dismissing toasts/modals
- Scheduled actions

### Hook #2: useInterval

Replaces `setInterval` with automatic cleanup:

```tsx
// ❌ OLD WAY
useEffect(() => {
  const interval = setInterval(() => {
    fetchLatestData();
  }, 5000);
  return () => clearInterval(interval);
}, []);

// ✅ NEW WAY
import { useInterval } from '@/hooks/cleanupHooks';

function Dashboard() {
  useInterval(() => {
    fetchLatestData();
  }, 5000);

  return <DashboardContent />;
}
```

**When to use**:
- Polling APIs
- Countdown timers
- Periodic data refresh

### Hook #3: useEventListener

Replaces `addEventListener` with automatic cleanup:

```tsx
// ❌ OLD WAY
useEffect(() => {
  const handleResize = () => setWidth(window.innerWidth);
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);

// ✅ NEW WAY
import { useWindowResize } from '@/hooks/cleanupHooks';

function ResponsiveComponent() {
  const [width, setWidth] = useState(window.innerWidth);

  useWindowResize(() => {
    setWidth(window.innerWidth);
  });

  return <div>Window width: {width}px</div>;
}
```

**Special variants**:
```tsx
useEventListener('click', handleClick, document)  // Any event
useWindowResize(handler)                          // Window resize
useWindowScroll(handler)                          // Window scroll
useKeyDown('Escape', handleEscape)                // Keyboard shortcuts
useClickOutside(ref, handler)                     // Click outside detection
useMediaQuery('(max-width: 768px)')              // Media queries
```

### Hook #4: useWebSocket

Replaces `new WebSocket()` with automatic cleanup:

```tsx
// ❌ OLD WAY
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000');
  ws.onopen = () => console.log('Connected');
  ws.onmessage = (e) => setData(e.data);
  return () => ws.close();
}, []);

// ✅ NEW WAY
import { useWebSocket } from '@/hooks/cleanupHooks';

function ChatComponent() {
  const [messages, setMessages] = useState([]);

  const ws = useWebSocket('ws://localhost:8000/chat', {
    onOpen: () => console.log('Connected'),
    onMessage: (data) => setMessages(prev => [...prev, data]),
    onClose: () => console.log('Disconnected'),
  });

  const sendMessage = () => {
    ws.send(JSON.stringify({ text: 'Hello' }));
  };

  return (
    <div>
      {messages.map(m => <Message key={m.id} {...m} />)}
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}
```

**Bonus**: Auto-reconnects on connection loss!

---

## 🔍 Part 3: Code Review Patterns (10 minutes)

### Code Review Checklist

When reviewing PRs, check for these patterns:

#### ✅ **Good Patterns**
```tsx
// 1. Using custom hooks
useTimeout(() => {}, 1000);
useInterval(() => {}, 1000);
useEventListener('click', handler);

// 2. Proper cleanup in useEffect
useEffect(() => {
  const timer = setTimeout(...);
  return () => clearTimeout(timer);
}, []);

// 3. Unconditional cleanup
useEffect(() => {
  let timerId: NodeJS.Timeout | undefined;
  if (condition) {
    timerId = setTimeout(...);
  }
  return () => {
    if (timerId) clearTimeout(timerId);
  };
}, [condition]);
```

#### ❌ **Bad Patterns**
```tsx
// 1. Raw setTimeout without cleanup
useEffect(() => {
  setTimeout(...);
}, []);

// 2. addEventListener without cleanup
useEffect(() => {
  document.addEventListener('click', handler);
}, []);

// 3. Nested return (ESLint can't detect)
useEffect(() => {
  if (condition) {
    const timer = setTimeout(...);
    return () => clearTimeout(timer);
  }
}, []);
```

### Review Process

1. **Check ESLint results** in PR
2. **Look for** `setTimeout`, `setInterval`, `addEventListener`, `new WebSocket`
3. **Verify** cleanup exists
4. **Suggest** custom hooks if appropriate

---

## 🎯 Part 4: Hands-On Practice (15 minutes)

### Exercise 1: Fix a Timer Leak

```tsx
// 🐛 BUG: This component has a memory leak
function Notification() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setVisible(false);
    }, 3000);
  }, []);

  return visible ? <div>Notification!</div> : null;
}

// ✅ YOUR FIX: Make it memory-safe
// (Write your solution below)


































// ❌ SOLUTION: Click to reveal

function Notification() {
  const [visible, setVisible] = useState(true);

  // Option 1: Manual cleanup
  useEffect(() => {
    const timerId = setTimeout(() => {
      setVisible(false);
    }, 3000);
    return () => clearTimeout(timerId);
  }, []);

  // Option 2: Using custom hook (BETTER!)
  useTimeout(() => {
    setVisible(false);
  }, 3000);

  return visible ? <div>Notification!</div> : null;
}
```

### Exercise 2: Fix an Event Listener Leak

```tsx
// 🐛 BUG: This component has a memory leak
function WindowWidth() {
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
  }, []);

  return <div>Width: {width}px</div>;
}

// ✅ YOUR FIX: Make it memory-safe
// (Write your solution below)


































// ❌ SOLUTION: Click to reveal

function WindowWidth() {
  const [width, setWidth] = useState(window.innerWidth);

  // Option 1: Manual cleanup
  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Option 2: Using custom hook (BETTER!)
  useWindowResize(() => {
    setWidth(window.innerWidth);
  });

  return <div>Width: {width}px</div>;
}
```

### Exercise 3: Conditional Cleanup (Advanced)

```tsx
// 🐛 BUG: This component has a memory leak AND ESLint error
function DelayedMessage({ show, delay }) {
  useEffect(() => {
    if (show) {
      setTimeout(() => {
        console.log('Message shown!');
      }, delay);
    }
  }, [show, delay]);

  return show ? <div>Message!</div> : null;
}

// ✅ YOUR FIX: Make it memory-safe AND satisfy ESLint
// (Hint: Cleanup must be unconditional)


































// ❌ SOLUTION: Click to reveal

function DelayedMessage({ show, delay }) {
  useEffect(() => {
    let timerId: NodeJS.Timeout | undefined;
    if (show) {
      timerId = setTimeout(() => {
        console.log('Message shown!');
      }, delay);
    }
    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, [show, delay]);

  return show ? <div>Message!</div> : null;
}

// OR using custom hook:
function DelayedMessage({ show, delay }) {
  useConditionalTimeout(
    () => console.log('Message shown!'),
    delay,
    show
  );

  return show ? <div>Message!</div> : null;
}
```

---

## 📋 Part 5: Quick Reference Card

### **Memory Leak Prevention Cheat Sheet**

#### ✅ **DO:**
- Use `useTimeout()`, `useInterval()`, `useEventListener()`, `useWebSocket()`
- Always return cleanup from useEffect
- Declare timer/event variables at top level for conditional cleanup
- Run `npm run lint` before committing

#### ❌ **DON'T:**
- Use raw `setTimeout`, `setInterval` without cleanup
- Use `addEventListener` without `removeEventListener`
- Nest return statements inside if blocks
- Ignore ESLint memory-leak warnings

### **Common Patterns**

```tsx
// Pattern 1: Simple timeout
useTimeout(() => action(), delay);

// Pattern 2: Conditional timeout with manual cleanup
useEffect(() => {
  let timerId: NodeJS.Timeout | undefined;
  if (condition) {
    timerId = setTimeout(() => action(), delay);
  }
  return () => {
    if (timerId) clearTimeout(timerId);
  };
}, [condition]);

// Pattern 3: Event listener
useEventListener('click', handler, element);

// Pattern 4: WebSocket
const ws = useWebSocket(url, { onMessage, onOpen, onClose });
```

---

## 🧪 Part 6: Testing Your Knowledge

### Quiz

**Q1**: Which of these has a memory leak?
```tsx
A) useEffect(() => {
     const timer = setTimeout(() => {}, 1000);
     return () => clearTimeout(timer);
   }, []);

B) useEffect(() => {
     setTimeout(() => {}, 1000);
   }, []);

C) useTimeout(() => {}, 1000);
```

**Answer**: B (no cleanup)

---

**Q2**: How do you fix this leak?
```tsx
useEffect(() => {
  if (isActive) {
    const interval = setInterval(() => {}, 1000);
  }
}, [isActive]);
```

**Answer**:
```tsx
useEffect(() => {
  let intervalId: NodeJS.Timeout | undefined;
  if (isActive) {
    intervalId = setInterval(() => {}, 1000);
  }
  return () => {
    if (intervalId) clearInterval(intervalId);
  };
}, [isActive]);

// OR:
useInterval(() => {}, isActive ? 1000 : null);
```

---

**Q3**: True or False: Pre-commit hooks will prevent you from committing code with memory leaks.

**Answer**: True ✅

---

## 🎯 Conclusion

### What You've Learned:
1. ✅ What memory leaks are and why they matter
2. ✅ How to use memory-safe hooks
3. ✅ How to review code for leaks
4. ✅ How to fix leaks when found

### Next Steps:
1. ✅ Start using `useTimeout`, `useInterval`, `useEventListener` in new code
2. ✅ Review existing PRs for memory leaks
3. ✅ Refactor 1-2 old components per week to use new hooks
4. ✅ Help teammates learn these patterns

### Resources:
- **Quick Reference**: `MEMORY_LEAK_QUICKFIX_GUIDE.md`
- **Hook Documentation**: `src/hooks/cleanupHooks.ts`
- **Week 2 Report**: `WEEK_2_COMPLETE.md`

### Questions?
Ask in #frontend or during the next team standup!

---

**Training Complete!** 🎉

You're now equipped to write memory-safe React code. Remember: **Clean up as you code, not after!**
