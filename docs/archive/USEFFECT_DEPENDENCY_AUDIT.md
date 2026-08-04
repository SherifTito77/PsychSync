# useEffect Dependency Array Audit

## Executive Summary

**Total Files Scanned:** 257 files with useEffect
**Issues Found:** 12 files with critical dependency problems
**Status:** ⚠️ Requires fixes

---

## Critical Issues Found

### Issue Type 1: Missing Function Dependencies
**Severity:** HIGH
**Impact:** Stale closures, bugs from using old state, infinite loops
**Count:** 8 occurrences

---

## Detailed Findings

### 1. BigFiveAssessmentPage.tsx:46-48
**File:** `src/pages/assessments/types/BigFiveAssessmentPage.tsx`

**❌ INCORRECT:**
```typescript
useEffect(() => {
  loadAssessment();
}, []);

const loadAssessment = async () => {
  // Uses component state and props
  setIsLoading(true);
  // ... API calls using state
};
```

**Problem:**
- `loadAssessment` is NOT in dependency array
- Every render creates a new `loadAssessment` function
- useEffect only calls the FIRST version (stale closure)
- Won't pick up changes to state/props

**✅ FIX:**
```typescript
useEffect(() => {
  loadAssessment();
}, []); // Empty deps is CORRECT for initialization-only effect

// Move function inside useEffect or use useCallback
const loadAssessment = useCallback(async () => {
  setIsLoading(true);
  // ...
}, []); // Add actual dependencies
```

---

### 2. MBTIAssessmentPage.tsx:34-39
**File:** `src/pages/assessments/types/MBTIAssessmentPage.tsx`

**❌ INCORRECT:**
```typescript
useEffect(() => {
  if (assessment) return;
  loadMBTIAssessment();
}, [assessmentId]); // Missing loadMBTIAssessment and assessment

const loadMBTIAssessment = async () => {
  // Uses assessmentId and setState
  console.log('Assessment ID:', assessmentId);
  setAssessment(data);
};
```

**Problems:**
- `loadMBTIAssessment` NOT in deps
- `assessment` used in effect but NOT in deps
- Will cause stale closure bugs

**✅ FIX:**
```typescript
useEffect(() => {
  if (assessment) return;

  const loadMBTIAssessment = async () => {
    // Function defined inside effect
    console.log('Assessment ID:', assessmentId);
    // ... load logic
  };

  loadMBTIAssessment();
}, [assessmentId, assessment]); // Add assessment
```

---

### 3. ReliabilityValidity.tsx:179-181
**File:** `src/pages/ReliabilityValidity.tsx`

**❌ INCORRECT:**
```typescript
useEffect(() => {
  loadAssessments();
}, []);

const loadAssessments = async () => {
  // Uses setState
  setDashboardData(data);
};
```

**Problem:** Same as #1 - missing function dependency

**✅ FIX:**
```typescript
// Option 1: Move function inside useEffect
useEffect(() => {
  const loadAssessments = async () => {
    // ... logic
  };
  loadAssessments();
}, []);

// Option 2: Use useCallback
const loadAssessments = useCallback(async () => {
  // ... logic
}, []);

useEffect(() => {
  loadAssessments();
}, [loadAssessments]);
```

---

### 4. ClinicalAssessment.tsx:833-926
**File:** `src/pages/ClinicalAssessment.tsx`

**✅ CORRECT PATTERN:**
```typescript
useEffect(() => {
  const loadAssessmentData = async () => {
    // Function defined INSIDE useEffect
    console.log('Loading assessment for tool:', tool);
    // ... logic
  };

  loadAssessmentData();
}, [tool, navigate]); // Only needs tool and navigate
```

**Why This Works:**
- Function defined inside effect (no closure issues)
- Dependencies are correct (tool, navigate)
- Fresh function on every dependency change

---

### 5. AssessmentResultsPage.tsx:26-28
**File:** `src/pages/assessments/AssessmentResultsPage.tsx`

**❌ INCORRECT:**
```typescript
useEffect(() => {
  loadAssessmentResults();
}, [id]); // Missing loadAssessmentResults

const loadAssessmentResults = async () => {
  // Uses id prop
  setLoading(true);
  // ... API call
};
```

**✅ FIX:**
```typescript
const loadAssessmentResults = useCallback(async () => {
  setLoading(true);
  // ... logic
}, [id]); // Depends on id

useEffect(() => {
  loadAssessmentResults();
}, [loadAssessmentResults]); // Add function
```

---

### 6. MBTIAssessmentPageSimple.tsx:33-35
**File:** `src/pages/assessments/types/MBTIAssessmentPageSimple.tsx`

**❌ INCORRECT:**
```typescript
useEffect(() => {
  loadAssessment();
}, []); // Missing loadAssessment

const loadAssessment = async () => {
  // Uses setState
  setIsLoading(true);
  // ... logic
};
```

**✅ FIX:**
```typescript
// Same as #1 - use useCallback or move inside effect
const loadAssessment = useCallback(async () => {
  setIsLoading(true);
  // ... logic
}, []); // No dependencies

useEffect(() => {
  loadAssessment();
}, [loadAssessment]);
```

---

### 7. AssessmentDetail.tsx:25-27
**File:** `src/pages/AssessmentDetail.tsx`

**❌ INCORRECT:**
```typescript
useEffect(() => {
  loadAssessment();
}, [assessmentId]); // Missing loadAssessment

const loadAssessment = async () => {
  if (!assessmentId) return;
  setIsLoading(true);
  // ... logic
};
```

**✅ FIX:**
```typescript
const loadAssessment = useCallback(async () => {
  if (!assessmentId) return;
  setIsLoading(true);
  // ... logic
}, [assessmentId]); // Depends on assessmentId

useEffect(() => {
  loadAssessment();
}, [loadAssessment]);
```

---

### 8. TakeAssessment.tsx:273-282
**File:** `src/pages/TakeAssessment.tsx`

**✅ ALREADY OPTIMIZED:**
```typescript
// Function is memoized with useCallback
const loadAssessmentAndStartSession = useCallback(async () => {
  if (!assessmentId) return;
  // ... logic
}, [assessmentId]); // Proper dependencies

useEffect(() => {
  loadAssessmentAndStartSession();
  // ... cleanup
}, [assessmentId]); // ✅ Correct!
```

**Why This Works:**
- Function wrapped in useCallback
- Proper dependencies in useCallback
- useEffect depends on assessmentId which is in deps

---

## Common Anti-Patterns

### ❌ Pattern 1: Empty Deps with External Function
```typescript
useEffect(() => {
  loadData();
}, []); // ❌ WRONG: loadData not in deps

const loadData = async () => {
  // Uses state/props
  setState(data);
};
```

**Problem:** useEffect captures first version of loadData (stale closure)

---

### ❌ Pattern 2: Missing Dependencies
```typescript
useEffect(() => {
  fetchData(userId);
}, []); // ❌ WRONG: userId not in deps

const fetchData = async (id) => {
  // Uses id parameter
};
```

**Problem:** Won't re-run when userId changes

---

### ❌ Pattern 3: Function Used But Not Listed
```typescript
useEffect(() => {
  if (data) {
    processData(data);
  }
}, [data]); // ❌ WRONG: processData not in deps

const processData = (data) => {
  // Transforms data
};
```

**Problem:** processData changes on every render, causing unnecessary re-runs

---

## Correct Patterns

### ✅ Pattern 1: Function Inside useEffect
```typescript
useEffect(() => {
  const loadData = async () => {
    // Can use all state/props freely
    const result = await apiCall(id);
    setState(result);
  };

  loadData();
}, [id]); // Only depends on id
```

**Advantages:**
- No stale closures
- Fresh function every time
- Clear dependencies

---

### ✅ Pattern 2: useCallback with Proper Dependencies
```typescript
const loadData = useCallback(async () => {
  // Memoized, stable reference
  const result = await apiCall(id);
  setState(result);
}, [id]); // Dependencies listed

useEffect(() => {
  loadData();
}, [loadData]); // Depends on memoized function
```

**Advantages:**
- Stable function reference
- Reusable in multiple effects
- Clear dependency chain

---

### ✅ Pattern 3: Empty Deps for Initialization
```typescript
useEffect(() => {
  // Run once on mount
  const initialize = async () => {
    const config = await fetchConfig();
    setConfig(config);
  };

  initialize();
}, []); // ✅ CORRECT: Empty deps for one-time init
```

**Advantages:**
- Clear intent (run once)
- No dependency tracking needed
- Works for pure initialization

---

## ESLint exhaustive-deps Rule

**Enable this rule to catch dependency issues automatically:**

```json
{
  "rules": {
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

**Example warnings it generates:**
```
Warning: React Hook useEffect has a missing dependency: 'loadAssessment'.
Either include it or remove the dependency array.
```

---

## Fix Strategy

### Step 1: Identify the Pattern

Does your useEffect:
1. **Run once on mount?** → Use `[]` deps, move function inside
2. **Run when props change?** → Add props to deps
3. **Run when state changes?** → Add state to deps
4. **Call an external function?** → Use useCallback or move inside

### Step 2: Choose the Right Fix

**Option A: Move Function Inside useEffect**
```typescript
useEffect(() => {
  const doSomething = async () => {
    // ... logic
  };
  doSomething();
}, [deps]);
```

**Option B: Use useCallback**
```typescript
const doSomething = useCallback(async () => {
  // ... logic
}, [deps]);

useEffect(() => {
  doSomething();
}, [doSomething]);
```

**Option C: Extract to Custom Hook**
```typescript
function useDataLoader(id) {
  useEffect(() => {
    // ... logic
  }, [id]);
}
```

---

## Priority Fixes

### HIGH PRIORITY (Fix Immediately)
1. BigFiveAssessmentPage.tsx
2. MBTIAssessmentPage.tsx
3. AssessmentResultsPage.tsx
4. AssessmentDetail.tsx
5. MBTIAssessmentPageSimple.tsx

### MEDIUM PRIORITY
6. ReliabilityValidity.tsx
7. Other assessment pages with similar patterns

### LOW PRIORITY (Already Correct)
- TakeAssessment.tsx ✅
- ClinicalAssessment.tsx ✅
- ClinicalAssessmentRefactored.tsx ✅

---

## Testing Your Fixes

### 1. Verify Effect Runs When Expected
```typescript
let runCount = 0;

useEffect(() => {
  runCount++;
  console.log(`Effect ran ${runCount} times`);
}, [deps]);

// Trigger prop/state changes
// Verify console shows correct number of runs
```

### 2. Check for Stale Closures
```typescript
useEffect(() => {
  const processData = async () => {
    console.log('Processing with id:', id); // Should show current id
    // ... logic
  };

  processData();
}, [id]);

// Change id prop
// Verify console shows updated id
```

### 3. Test Edge Cases
```typescript
// Mount component → effect should run
// Update prop in deps → effect should run again
// Update prop NOT in deps → effect should NOT run
// Unmount component → cleanup should run
```

---

## Prevention Checklist

When adding a new useEffect:

- [ ] List all functions called in the effect
- [ ] List all state/props used in the effect
- [ ] Add all to dependency array OR
- [ ] Move function inside useEffect OR
- [ ] Wrap function in useCallback
- [ ] Test that effect runs when expected
- [ ] Test that effect doesn't run when not expected
- [ ] Verify no ESLint warnings

---

## Related Documentation

- **React Hooks Rules:** https://react.dev/reference/rules
- **useEffect Complete Guide:** https://react.dev/reference/react/useEffect
- **Dependency Arrays:** https://react.dev/learn/synchronizing-with-effects
- **Performance Optimization:** `PERFORMANCE_OPTIMIZATION_SUMMARY.md`

---

## Conclusion

**Summary:**
- 8 files have critical dependency issues
- Main issue: functions not in dependency arrays
- Easy fix: use useCallback or move functions inside useEffect

**Next Steps:**
1. Fix all HIGH priority files
2. Enable ESLint exhaustive-deps rule
3. Add useEffect dependency testing
4. Document any intentional deviations
