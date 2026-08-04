# Performance Monitoring Setup Guide

This guide shows you how to use the performance monitoring utilities to detect and fix render performance issues in your React components.

## Quick Start

### 1. Import the Monitoring Tools

```typescript
import {
  useRenderCount,
  useEffectWatch,
  useWhyDidYouUpdate,
  useRenderPerformance,
  useDetectUnnecessaryRenders,
  useAsyncOperation
} from '@/utils/performanceMonitor';
```

### 2. Add Monitoring to Your Component

```typescript
import { useRenderCount, useRenderPerformance } from '@/utils/performanceMonitor';

function MyComponent({ data }) {
  // Track render count
  useRenderCount('MyComponent');

  // Measure render performance (warns if > 16ms)
  useRenderPerformance('MyComponent', 16);

  return <div>{/* ... */}</div>;
}
```

### 3. Check the Browser Console

Open your browser's DevTools console to see performance logs:

```
🔄 [MyComponent] Render count: 1
⚠️  [MyComponent] Slow render detected: 22.45ms (threshold: 16ms)
```

## Monitoring Tools

### 1. `useRenderCount(componentName)`

**Purpose:** Track how many times a component renders

**Use Case:** Detect components rendering too frequently

**Example:**
```typescript
function ExpensiveList({ items }) {
  useRenderCount('ExpensiveList');

  return (
    <ul>
      {items.map(item => <li key={item.id}>{item.name}</li>)}
    </ul>
  );
}
```

**Console Output:**
```
🔄 [ExpensiveList] Render count: 1
🔄 [ExpensiveList] Render count: 2
⚠️  [ExpensiveList] High render count detected: 15
```

**When to Fix:** If render count > 10 during normal usage

---

### 2. `useEffectWatch(effectName, deps)`

**Purpose:** Monitor which dependencies cause effect re-runs

**Use Case:** Debug useEffect running too frequently

**Example:**
```typescript
function UserProfile({ userId, settings }) {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    fetchProfile(userId).then(setProfile);
  }, [userId]);

  // Watch the effect
  useEffectWatch('fetchProfile', [userId]);

  return <div>{profile?.name}</div>;
}
```

**Console Output:**
```
⚡ [fetchProfile] Re-run. Changed dependencies: [
  { index: 0, prev: 123, curr: 456 }
]
```

**When to Fix:** If effect runs when dependencies haven't meaningfully changed

---

### 3. `useWhyDidYouUpdate(props, componentName)`

**Purpose:** Identify which props caused a re-render

**Use Case:** Debug unnecessary re-renders in memoized components

**Example:**
```typescript
function UserCard({ user, onUpdate }) {
  useWhyDidYouUpdate({ user, onUpdate }, 'UserCard');

  return (
    <div>
      <h3>{user.name}</h3>
      <button onClick={onUpdate}>Update</button>
    </div>
  );
}
```

**Console Output:**
```
🔍 [UserCard] Why did it re-render? {
  "user": {
    "from": { name: "John", email: "john@example.com" },
    "to": { name: "John", email: "john.new@example.com" }
  }
}
```

**When to Fix:** If component re-renders with unchanged prop values

---

### 4. `useRenderPerformance(componentName, thresholdMs)`

**Purpose:** Measure render time and warn about slow renders

**Use Case:** Identify performance bottlenecks in components

**Example:**
```typescript
function ComplexChart({ data }) {
  useRenderPerformance('ComplexChart', 16); // Warn if > 16ms (60fps)

  // ... expensive chart rendering

  return <canvas ref={chartRef} />;
}
```

**Console Output:**
```
⚠️  [ComplexChart] Slow render detected: 42.30ms (threshold: 16ms)
```

**When to Fix:** If render consistently exceeds 16ms (60fps threshold)

---

### 5. `useDetectUnnecessaryRenders(componentName, data)`

**Purpose:** Detect renders without prop/state changes

**Use Case:** Find components rendering for no reason

**Example:**
```typescript
function StaticHeader({ title }) {
  useDetectUnnecessaryRenders('StaticHeader', {
    props: { title }
  });

  return <header><h1>{title}</h1></header>;
}
```

**Console Output:**
```
❌ [StaticHeader] Unnecessary render detected! No props or state changed.
```

**When to Fix:** Always - this indicates wasted render cycles

---

### 6. `useAsyncOperation(operationName)`

**Purpose:** Measure async operation performance

**Use Case:** Profile slow API calls or data processing

**Example:**
```typescript
function DataFetcher() {
  const measureFetch = useAsyncOperation('Fetch User Data');

  useEffect(() => {
    measureFetch(async () => {
      const data = await fetchUserData();
      setState(data);
    });
  }, []);

  return <div>{/* ... */}</div>;
}
```

**Console Output:**
```
⏱️  [Fetch User Data] Duration: 1234.56ms
```

---

### 7. `useDevModePerformance(componentName, options)`

**Purpose:** All-in-one monitoring for development

**Use Case:** Quick performance debugging during development

**Example:**
```typescript
function MyComponent({ user, isLoading }) {
  useDevModePerformance('MyComponent', {
    props: { user, isLoading },
    state: { localState },
    logRenders: true,
    logEffects: true
  });

  return <div>{/* ... */}</div>;
}
```

## Advanced Usage

### Custom Performance Marks

```typescript
import { performanceMark, performanceMeasure } from '@/utils/performanceMonitor';

function DataProcessor({ rawData }) {
  useEffect(() => {
    // Start timing
    performanceMark('process-start');

    const processed = complexDataTransformation(rawData);

    // End timing
    performanceMark('process-end');
    performanceMeasure('Data Processing', 'process-start', 'process-end');

    setResults(processed);
  }, [rawData]);

  return <div>{/* ... */}</div>;
}
```

### HOC with Performance Logging

```typescript
import { withPerformanceLogging } from '@/utils/performanceMonitor';

const OptimizedComponent = withPerformanceLogging(
  'ExpensiveComponent',
  React.memo(function ExpensiveComponent({ data }) {
    // ... component logic
  })
);
```

## Common Performance Issues & Solutions

### Issue 1: Unnecessary Re-renders

**Symptom:** Component renders with unchanged props

**Detection:**
```typescript
useDetectUnnecessaryRenders('MyComponent', { props });
```

**Solution:** Wrap component in React.memo
```typescript
export default React.memo(MyComponent);
```

---

### Issue 2: Callback Dependencies Causing Re-renders

**Symptom:** Child re-renders when parent state changes

**Detection:**
```typescript
useWhyDidYouUpdate({ onClick }, 'ChildComponent');
```

**Solution:** Use useCallback with minimal dependencies
```typescript
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]); // Only depends on id, not other state
```

---

### Issue 3: Effect Running Too Frequently

**Symptom:** useEffect runs on unrelated state changes

**Detection:**
```typescript
useEffectWatch('fetchData', [userId]);
```

**Solution:** Ensure dependency array only has actual dependencies
```typescript
useEffect(() => {
  fetchUserData(userId);
}, [userId]); // NOT [userId, otherState]
```

---

### Issue 4: Slow Renders

**Symptom:** Component takes >16ms to render

**Detection:**
```typescript
useRenderPerformance('SlowComponent', 16);
```

**Solution:** Use useMemo for expensive calculations
```typescript
const expensive = useMemo(() => {
  return heavyComputation(data);
}, [data]); // Only recalculate when data changes
```

---

### Issue 5: Multiple State Updates Causing Cascades

**Symptom:** Multiple useState calls cause multiple renders

**Detection:**
```typescript
useRenderCount('MultiStateComponent');
// Shows: 1, 3, 6, 9, 12... (multiple renders per update)
```

**Solution:** Consolidate related state with useReducer
```typescript
const [state, dispatch] = useReducer(reducer, initialState);
// All related state in one render
```

## Performance Testing

### Run Performance Tests

```bash
# Run all performance tests
npm test -- render-performance.test.tsx --run

# Run specific test
npm test -- render-performance.test.tsx -t "should memoize context value"
```

### Create Custom Performance Tests

```typescript
import { render } from '@testing-library/react';
import { useRenderCount } from '@/utils/performanceMonitor';

describe('MyComponent Performance', () => {
  it('should not re-render unnecessarily', () => {
    let renderCount = 0;

    const TestWrapper = () => {
      const Component = () => {
        renderCount++;
        useRenderCount('Test');
        return <div>Test</div>;
      };

      return <Component />;
    };

    const { rerender } = render(<TestWrapper />);

    const initialCount = renderCount;
    rerender(<TestWrapper />);

    // Should not have re-rendered
    expect(renderCount).toBe(initialCount);
  });
});
```

## Best Practices

### DO ✅

- Monitor all frequently used components
- Set appropriate performance thresholds (16ms for 60fps)
- Remove monitoring before production deployment
- Use performance data to drive optimization decisions
- Profile before and after optimizations

### DON'T ❌

- Leave monitoring in production builds (performance impact)
- Optimize without profiling first (premature optimization)
- Use React.memo on everything (has overhead)
- Ignore performance warnings (they indicate real issues)
- Over-optimize rarely used components

## Production Considerations

### Remove Monitoring in Production

All monitoring utilities check for `process.env.NODE_ENV === 'development'` and automatically disable themselves in production. However, you can also:

1. **Use build tools to strip monitoring code:**
   ```javascript
   // vite.config.ts
   export default defineConfig({
     define: {
       'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV)
     }
   });
   ```

2. **Use environment checks:**
   ```typescript
   if (import.meta.env.DEV) {
     useRenderCount('MyComponent');
   }
   ```

3. **Create separate monitored builds:**
   ```bash
   # Development build with monitoring
   npm run dev

   # Production build without monitoring
   npm run build
   ```

## Troubleshooting

### "Too many logs in console"

**Solution:** Only monitor components you're actively debugging:
```typescript
// Only enable for specific components
const DEBUG_COMPONENTS = ['MyComponent', 'ChildComponent'];

if (DEBUG_COMPONENTS.includes('MyComponent')) {
  useRenderCount('MyComponent');
}
```

### "Performance monitoring affecting app performance"

**Solution:** Monitoring should only add ~1-2ms per render. If it's more:
1. Check you're not monitoring in production
2. Reduce number of monitored components
3. Use selective monitoring (only what you're debugging)

### "Can't see which props changed"

**Solution:** Use useWhyDidYouUpdate for detailed prop comparison:
```typescript
useWhyDidYouUpdate(props, 'MyComponent');
```

## Resources

- **Source:** `src/utils/performanceMonitor.tsx`
- **Tests:** `src/tests/render-performance.test.tsx`
- **React DevTools:** https://react.dev/learn/react-developer-tools
- **Profiler API:** https://react.dev/reference/react/Profiler

## Support

For questions or issues with performance monitoring:
1. Check this guide first
2. Review test examples in `render-performance.test.tsx`
3. Refer to utility source code for detailed documentation
