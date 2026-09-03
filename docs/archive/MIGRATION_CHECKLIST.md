# ✅ Memory Leak Prevention Migration Checklist

**For**: PsychSync Frontend Team
**Timeline**: 4 weeks (flexible)
**Goal**: Eliminate all memory leaks from codebase

---

## Week 1: Foundation ✅

### Day 1-2: Setup
- [ ] Review `MEMORY_LEAK_QUICKFIX_GUIDE.md`
- [ ] Import cleanup hooks in your first component
- [ ] Run `npm run lint` to check for existing leaks

### Day 3-5: Practice
- [ ] Use cleanup hooks in 1-2 new components
- [ ] Get comfortable with the patterns
- [ ] Ask questions if unsure!

**✅ Status**: All team members should have:
- [ ] Read the quick guide
- [ ] Used at least 1 cleanup hook
- [ ] Run lint successfully

---

## Week 2: Active Migration

### Day 1-3: Low-Risk Components
Pick 2-3 simple components you're already modifying:

- [ ] Identify components with `setTimeout`/`setInterval`
- [ ] Replace with `useTimeout`/`useInterval`
- [ ] Test the changes locally
- [ ] Submit PR for review

**Example Components**:
- [ ] Toast/notification components
- [ ] Auto-dismissing modals
- [ ] Loading timers

### Day 4-5: Event Listeners
Find components with `addEventListener`:

- [ ] Replace with `useEventListener`
- [ ] Use specialized variants (`useWindowResize`, `useKeyDown`)
- [ ] Test event handling works correctly

---

## Week 3: Context & Hooks

### High-Value Targets
These are touched frequently and benefit most from cleanup:

- [ ] **AuthContext.tsx** - Session monitoring
- [ ] **NotificationContext.tsx** - Toast timers
- [ ] **ErrorContext.tsx** - Error timeouts
- [ ] **Custom hooks** in `/src/hooks/`

### Priority Order
1. [ ] User-facing components (auth, notifications)
2. [ ] Shared components (modals, dropdowns)
3. [ ] Page-level components
4. [ ] Utility hooks

---

## Week 4: Final Push

### Remaining Components
- [ ] Run full scan: `npm run lint | grep "memory-leak"`
- [ ] Fix any remaining leaks
- [ ] All ESLint memory-leak errors = 0 ✅

### Verification
- [ ] Run pre-commit hook test: `.husky/pre-commit`
- [ ] Verify CI/CD workflow runs on PR
- [ ] Check test suite passes

---

## 📋 Daily Checklist

### Before Starting Work
- [ ] Pull latest changes
- [ ] Run `npm run lint`
- [ ] Check for any new memory leak warnings

### During Coding
- [ ] Use cleanup hooks for new timers/events
- [ ] Don't use raw `setTimeout`/`setInterval`
- [ ] Don't use `addEventListener` without cleanup

### Before Committing
- [ ] Run `npm run lint | grep "memory-leak"`
- [ ] Fix any issues found
- [ ] Pre-commit hook will verify automatically

---

## 🎯 Component Refactoring Process

### Step 1: Identify
```
Search component for:
□ setTimeout
□ setInterval
□ addEventListener
□ new WebSocket
□ .subscribe()
```

### Step 2: Replace
```tsx
// Import hooks
import { useTimeout, useEventListener } from '@/hooks/cleanupHooks';

// Replace patterns
setTimeout → useTimeout
setInterval → useInterval
addEventListener → useEventListener
```

### Step 3: Test
```
□ Component mounts correctly
□ Timers/events work as expected
□ Cleanup happens (check console)
□ No ESLint errors
```

### Step 4: Commit
```
□ npm run lint passes
□ Tests pass
□ Pre-commit hook passes
□ Create PR
```

---

## 🚨 Quick Fixes

### Common Pattern #1: Auto-Dismiss
```tsx
// BEFORE
useEffect(() => {
  setTimeout(() => setShow(false), 3000);
}, []);

// AFTER
useTimeout(() => setShow(false), 3000);
```

### Common Pattern #2: Window Events
```tsx
// BEFORE
useEffect(() => {
  const handleResize = () => setSize(window.innerWidth);
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);

// AFTER
useWindowResize(() => setSize(window.innerWidth));
```

### Common Pattern #3: Polling
```tsx
// BEFORE
useEffect(() => {
  const interval = setInterval(() => fetch(), 5000);
  return () => clearInterval(interval);
}, []);

// AFTER
useInterval(() => fetch(), 5000);
```

---

## 📊 Progress Tracking

### Team Progress
| Week | Components Fixed | PRs Merged | ESLint Errors |
|------|-----------------|------------|---------------|
| Week 1 | 0 | 0 | Baseline |
| Week 2 | 5-10 | 3-5 | ↓ 30% |
| Week 3 | 15-25 | 10-15 | ↓ 60% |
| Week 4 | All | All | ✅ 0 |

### Individual Tracking
Track your progress:

**Components Refactored**: ___/___

**PRs Submitted**: ___/___

**Memory Leaks Fixed**: ___/___

**Cleanup Hooks Used**:
- [ ] `useTimeout` - ___ times
- [ ] `useInterval` - ___ times
- [ ] `useEventListener` - ___ times
- [ ] `useWebSocket` - ___ times

---

## ✅ Completion Criteria

### Team Level
- [ ] All components in `/src/components` refactored
- [ ] All contexts in `/src/contexts` refactored
- [ ] All custom hooks in `/src/hooks` refactored
- [ ] ESLint memory-leak errors = 0
- [ ] Pre-commit hook working for all developers
- [ ] CI/CD workflow enabled

### Individual Level
- [ ] Refactored at least 5 components
- [ ] Used all cleanup hook types at least once
- [ ] Reviewed 3+ PRs for memory leaks
- [ ] Helped a teammate with migration

---

## 🆘 Getting Help

### Stuck on a Refactor?
1. Check `MEMORY_LEAK_QUICKFIX_GUIDE.md`
2. Look at `src/hooks/cleanupHooks.ts` examples
3. Ask in #frontend channel
4. Schedule pair programming session

### ESLint Errors?
1. Run `npm run lint | grep "memory-leak"`
2. Check line numbers and file paths
3. Apply fix patterns from guide
4. Verify with `npm run lint` again

### Pre-commit Hook Failing?
1. It's working as designed!
2. Fix the memory leaks it found
3. Run `npm run lint` to verify
4. Commit again

---

## 🎉 Celebrate Progress!

### After Each Week
- [ ] Share wins in standup
- [ ] Update progress tracker
- [ ] Help teammate who's stuck

### Completion Party (Week 4)
- [ ] Zero ESLint memory-leak errors ✅
- [ ] All components refactored ✅
- [ ] Team trained on best practices ✅
- [ ] Codebase is memory-safe ✅

**Reward**: Celebration lunch/team outing! 🍕

---

## 📝 Notes Section

Use this space to track your specific challenges and solutions:

```
Component: _________________
Issue: _____________________
Solution: ___________________
Date: ______________________
```

```
Component: _________________
Issue: _____________________
Solution: ___________________
Date: ______________________
```

---

**Remember**: It's a marathon, not a sprint. Consistent progress over 4 weeks will eliminate all memory leaks! 🏃‍♂️💨
