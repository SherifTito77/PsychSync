# 🎓 Race Condition Prevention - Developer Training

## Session Overview

**Duration**: 60 minutes
**Audience**: Frontend Developers
**Prerequisites**: Basic React knowledge
**Goal**: Master race condition prevention patterns

---

## 📚 Training Modules

### Module 1: Understanding Race Conditions (10 min)

#### Learning Objectives
- What are race conditions?
- Why do they happen in React?
- Real-world consequences
- How to spot them

#### Key Concepts

**Definition**:
> A race condition occurs when the outcome of a system depends on the relative timing of events. In React, this typically happens when:
> 1. Multiple async operations start simultaneously
> 2. Component unmounts before async operations complete
> 3. State updates happen out of sequence

**Example Scenario**:
```typescript
// The Problem
useEffect(() => {
  fetchData();  // Starts async operation
}, []);

const fetchData = async () => {
  const data = await api.get('/endpoint');
  setState(data);  // ⚠️ May run after unmount!
};
```

**Consequences**:
- Memory leaks
- State corruption
- Console warnings
- Poor UX (flickering, inconsistency)

#### Discussion Questions
1. Has anyone seen "state update on unmounted component" warning?
2. What happens when you click refresh 5 times rapidly?
3. Why do timers cause memory leaks?

---

### Module 2: The 5 Protective Patterns (25 min)

#### Pattern 1: Request Guarding

**Problem**: Concurrent requests waste resources

```typescript
// ❌ WITHOUT GUARD
const handleClick = () => {
  fetchData();  // Fires on every click
};

// ✅ WITH GUARD
const isFetchingRef = useRef(false);

const fetchData = async () => {
  if (isFetchingRef.current) return;  // Guard

  isFetchingRef.current = true;
  try {
    const data = await api.get('/endpoint');
    setState(data);
  } finally {
    isFetchingRef.current = false;
  }
};
```

**Exercise**: Implement request guarding in a sample component

---

#### Pattern 2: Debouncing

**Problem**: Rapid user interactions trigger request storms

```typescript
// ❌ WITHOUT DEBOUNCE
<button onClick={fetchData}>Refresh</button>
// 5 clicks = 5 requests

// ✅ WITH DEBOUNCE
const handleRefresh = useDebouncedCallback(() => {
  fetchData();
}, 500, []);  // Wait 500ms after last click

<button onClick={handleRefresh}>Refresh</button>
// 5 clicks = 1 request
```

**Live Demo**: Compare behavior with and without debounce

---

#### Pattern 3: Mount Checks

**Problem**: State updates after component unmounts

```typescript
// ❌ WITHOUT MOUNT CHECK
const updateState = async () => {
  const data = await api.get('/endpoint');
  setState(data);  // ⚠️ May error if unmounted
};

// ✅ WITH MOUNT CHECK
const isMountedRef = useRef(true);

useEffect(() => {
  isMountedRef.current = true;
  return () => {
    isMountedRef.current = false;
  };
}, []);

const updateState = async () => {
  const data = await api.get('/endpoint');
  if (isMountedRef.current) {  // ✅ Safe check
    setState(data);
  }
};
```

**Code Review**: Find examples in current codebase

---

#### Pattern 4: Cleanup Functions

**Problem**: Timers and subscriptions leak memory

```typescript
// ❌ WITHOUT CLEANUP
useEffect(() => {
  setInterval(callback, 1000);
}, []);

// ✅ WITH CLEANUP
useEffect(() => {
  const interval = setInterval(callback, 1000);
  return () => clearInterval(interval);  // ✅ Cleanup
}, []);
```

**Best Practice**: Always return cleanup function from useEffect

---

#### Pattern 5: Optimistic Rollback

**Problem**: Failed updates leave UI in inconsistent state

```typescript
// ✅ OPTIMISTIC UPDATE WITH ROLLBACK
const previousStateRef = useRef(currentState);

const update = async () => {
  // Store previous state
  previousStateRef.current = currentState;

  // Optimistic update (immediate UI feedback)
  setState(newValue);

  try {
    await api.patch('/endpoint', newValue);
  } catch (error) {
    // Rollback on failure
    setState(previousStateRef.current);
    showError('Update failed');
  }
};
```

**Exercise**: Practice with a sample form component

---

### Module 3: Hands-On Workshop (20 min)

#### Exercise 1: Fix a Broken Component

**Task**: Fix the race conditions in this component:

```typescript
// BROKEN COMPONENT (has race conditions)
export const BrokenDashboard = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const result = await api.get('/data');
    setData(result);
  };

  return (
    <div>
      <button onClick={fetchData}>Refresh</button>
      {/* Display data */}
    </div>
  );
};
```

**Solution Steps**:
1. Add request guarding
2. Add debouncing to onClick
3. Add mount checks
4. Add cleanup function

---

#### Exercise 2: Code Review Race

**Review these components and identify race conditions**:

```typescript
// Component A
useEffect(() => {
  setTimeout(() => setState(value), 1000);
}, []);

// Component B
const handleClick = () => {
  api.post('/update', data);
  setState(updated);
};

// Component C
useEffect(() => {
  const interval = setInterval(callback, 5000);
}, []);
```

**Group Activity**: Spot the issues and propose fixes

---

### Module 4: Tooling & Automation (5 min)

#### ESLint Integration

**Demo**: ESLint rules that auto-detect patterns

```bash
# Run race condition lint
npm run lint -- --rule '@psychsync/*'
```

#### CI/CD Integration

**Demo**: GitHub Actions workflow that:
- Detects anti-patterns
- Runs automated tests
- Generates reports
- Alerts on failures

---

## 🎓 Knowledge Check

### Quiz Questions

**Q1**: What's the purpose of `isFetchingRef`?
<details>
<summary>Answer</summary>
Prevents multiple concurrent requests by tracking if a request is already in progress.
</details>

**Q2**: Why use debouncing on onClick handlers?
<details>
<summary>Answer</summary>
Prevents request storms from rapid user clicks by waiting for a pause (500ms) before executing.
</details>

**Q3**: When should you use mount checks?
<details>
<summary>Answer</summary>
Before any setState call in async operations that might complete after component unmounts.
</details>

**Q4**: What's the rollback pattern used for?
<details>
<summary>Answer</summary>
Optimistic UI updates - revert to previous state if the API call fails.
</details>

---

## 📖 Quick Reference Card

### The 5 Commandments of Race Condition Prevention

1. ✅ **Always guard** concurrent requests with `isFetchingRef`
2. ✅ **Always debounce** onClick handlers that call async functions
3. ✅ **Always check** `isMountedRef` before setState in async operations
4. ✅ **Always return** cleanup functions from useEffect with timers
5. ✅ **Always store** previous state for optimistic updates

### Code Template

```typescript
// Safe Component Template
export const SafeComponent = () => {
  const [data, setData] = useState(null);

  // Mount tracking
  const isMountedRef = useRef(true);
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Request guarding
  const isFetchingRef = useRef(false);
  const fetchData = useCallback(async () => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    try {
      const result = await api.get('/endpoint');
      if (isMountedRef.current) {
        setData(result);
      }
    } finally {
      isFetchingRef.current = false;
    }
  }, []);

  // Initial load
  useAsyncEffect(async (signal, isMounted) => {
    await fetchData(signal);
  }, [fetchData]);

  // Debounced handler
  const handleRefresh = useDebouncedCallback(() => {
    if (!isFetchingRef.current) {
      fetchData();
    }
  }, 500, []);

  return <button onClick={handleRefresh}>Refresh</button>;
};
```

---

## 🚀 Take-Home Resources

### Documentation
- 📄 `/frontend/RACE_CONDITION_FIX_GUIDE.md` - Comprehensive patterns guide
- 📄 `/RACE_CONDITION_TEST_PLAN.md` - Testing procedures
- 📄 `/CHANGES_REVIEW.md` - Changes made in this project

### Code Examples
- ✅ AutomatedAlertsCenter.tsx - Complete example
- ✅ ProductOperationsDashboard.tsx - Complex example
- ✅ All 10 fixed components - Reference implementations

### Tools
- 🔧 ESLint rules (see ESLINT_RULES_PROPOSAL.md)
- 🔧 CI/CD monitoring workflow
- 🔧 Quick test checklist

---

## 🎯 Post-Training Action Items

### For Each Developer

1. **Review** the 10 fixed components
2. **Practice** the patterns on a new component
3. **Run** the quick test checklist (30 min)
4. **Share** learnings with team

### For Team Lead

1. **Assign** code review buddies for next sprint
2. **Schedule** follow-up session in 2 weeks
3. **Track** metrics (console warnings, duplicate requests)
4. **Plan** integration into existing workflow

---

## 📊 Training Evaluation

### Feedback Form

Please rate this training (1-5):

| Aspect | Rating |
|--------|--------|
| Content clarity | ⭐⭐⭐⭐⭐ |
| Relevance to work | ⭐⭐⭐⭐⭐ |
| Hands-on exercises | ⭐⭐⭐⭐⭐ |
| Tool demonstrations | ⭐⭐⭐⭐⭐ |
| Overall quality | ⭐⭐⭐⭐⭐ |

**What was most helpful?**
___________________________

**What needs more coverage?**
___________________________

**Suggestions for improvement:**
___________________________

---

## 🎓 Certification

### Quiz: Race Condition Prevention

**Passing Score**: 4/5 correct

1. Which hook should you use for async effects?
   - A) useEffect
   - B) useAsyncEffect ✅
   - C) useLayoutEffect
   - D) useMemo

2. What's the debounce delay we use?
   - A) 100ms
   - B) 500ms ✅
   - C) 1000ms
   - D) 2000ms

3. How do you prevent concurrent requests?
   - A) Lock the button
   - B) Use isFetchingRef ✅
   - C) Disable onClick
   - D) Add timeout

4. When should you check isMounted?
   - A) Before setState in async operations ✅
   - B) In useEffect cleanup
   - C) In render
   - D) Before return

5. What's rollback used for?
   - A) Undo optimistic updates ✅
   - B) Clear memory
   - C) Cancel requests
   - D) Reset timers

---

## 📞 Support

### Questions?
- **Slack**: #frontend-help
- **Email**: frontend-team@company.com
- **Office Hours**: Fridays 2-4 PM

### Resources
- **Documentation**: `/docs/race-conditions/`
- **Examples**: `/frontend/src/components/*/`
- **Templates**: `/docs/component-templates/`

---

## ✅ Training Complete!

**What You Learned**:
- ✅ Understanding race conditions
- ✅ 5 protective patterns
- ✅ Hands-on practice
- ✅ Tooling & automation

**Next Steps**:
1. Apply patterns to next component you build
2. Review a teammate's code for race conditions
3. Complete the certification quiz
4. Share knowledge with others

**Thank you for your attention!** 🙌

---

**Presentation Version**: 1.0.0
**Date**: 2026-01-21
**Presenter**: Frontend Team Lead
**Duration**: 60 minutes
