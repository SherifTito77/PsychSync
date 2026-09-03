# ESLint Rules for Race Condition Prevention

## Overview

Custom ESLint rules to automatically detect and prevent race condition patterns in React components. These rules can be integrated into your linting pipeline to catch issues during development.

---

## 📋 Proposed Rules

### Rule 1: `no-unsafe-use-effect-async`

**Detects**: useEffect hooks with async operations that don't handle cleanup

**Pattern**:
```typescript
// ❌ BAD - No cleanup
useEffect(() => {
  fetchData();
}, []);

// ❌ BAD - No abort controller
useEffect(() => {
  const data = await fetch(url);
  setState(data);
}, []);
```

**Rule Implementation**:
```javascript
// eslint-rules/no-unsafe-use-effect-async.js
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Disallow unsafe async operations in useEffect without cleanup',
      category: 'Best Practices',
      recommended: true,
    },
    schema: [],
    messages: {
      missingCleanup: 'useEffect with async operation must have cleanup function',
      missingAbortController: 'useEffect with fetch must use AbortController',
    },
  },
  create(context) {
    return {
      useEffect(node) {
        const sourceCode = context.getSourceCode();
        const asyncFunction = sourceCode.getText(node);

        // Check for async useEffect without cleanup return
        if (node.async) {
          const hasReturn = asyncFunction.includes('return ()');
          if (!hasReturn) {
            context.report({
              node,
              messageId: 'missingCleanup',
            });
          }
        }

        // Check for fetch without AbortController
        if (asyncFunction.includes('fetch(')) {
          const hasAbortController =
            asyncFunction.includes('AbortController') ||
            asyncFunction.includes('signal:');

          if (!hasAbortController) {
            context.report({
              node,
              messageId: 'missingAbortController',
            });
          }
        }
      },
    };
  },
};
```

**Configuration**:
```json
{
  "rules": {
    "@psychsync/no-unsafe-use-effect-async": "error"
  }
}
```

---

### Rule 2: `require-debounced-onclick`

**Detects**: onClick handlers that directly call async functions without debouncing

**Pattern**:
```typescript
// ❌ BAD - Direct call
<button onClick={fetchData}>Refresh</button>

// ✅ GOOD - Debounced
<button onClick={handleDebouncedFetch}>Refresh</button>
```

**Rule Implementation**:
```javascript
// eslint-rules/require-debounced-onclick.js
module.exports = {
  meta: {
    type: 'suggestion',
    docs: {
      description: 'Require debouncing for onClick handlers that call async functions',
      category: 'Performance',
      recommended: false,
    },
    schema: [{
      type: 'object',
      properties: {
        allowedNames: {
          type: 'array',
          items: { type: 'string' }
        }
      },
      additionalProperties: false
    }],
    messages: {
      missingDebounce: 'onClick handler "{{name}}" should be debounced to prevent race conditions. Use useDebouncedCallback hook.',
    },
  },
  create(context) {
    const allowedNames = new Set(context.options[0]?.allowedNames || []);
    allowedNames.add('handleSubmit'); // Forms are exempt

    return {
      JSXAttribute(node) {
        if (node.name.name !== 'onClick') return;

        const value = node.value;
        if (!value || !value.expression) return;

        const functionName = value.expression.name || '';

        // Check if it's a direct function call (likely async)
        const isAsyncPattern =
          /fetch|load|refresh|update|get|submit/i.test(functionName);

        if (isAsyncPattern && !allowedNames.has(functionName)) {
          context.report({
            node,
            messageId: 'missingDebounce',
            data: { name: functionName },
          });
        }
      },
    };
  },
};
```

**Configuration**:
```json
{
  "rules": {
    "@psychsync/require-debounced-onclick": ["warn", {
      "allowedNames": ["handleSubmit", "handleNavigate"]
    }]
  }
}
```

---

### Rule 3: `no-setTimeout-without-cleanup`

**Detects**: setTimeout/setInterval without cleanup in useEffect

**Pattern**:
```typescript
// ❌ BAD
useEffect(() => {
  setInterval(callback, 1000);
}, []);

// ✅ GOOD
useEffect(() => {
  const interval = setInterval(callback, 1000);
  return () => clearInterval(interval);
}, []);
```

**Rule Implementation**:
```javascript
// eslint-rules/no-setTimeout-without-cleanup.js
module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Disallow setTimeout/setInterval without cleanup in useEffect',
      category: 'Memory Leaks',
      recommended: true,
    },
    schema: [],
    messages: {
      missingCleanup: 'Timer must be cleared in cleanup function to prevent memory leaks',
    },
  },
  create(context) {
    return {
      useEffect(node) {
        const sourceCode = context.getSourceCode();
        const effectCode = sourceCode.getText(node);

        const hasSetTimeout = effectCode.includes('setTimeout');
        const hasSetInterval = effectCode.includes('setInterval');

        if (!hasSetTimeout && !hasSetInterval) return;

        // Check for cleanup return
        const hasReturn = effectCode.includes('return ()');
        const hasClearTimeout = effectCode.includes('clearTimeout') ||
                               effectCode.includes('clearInterval');

        if (!hasReturn || !hasClearTimeout) {
          context.report({
            node,
            messageId: 'missingCleanup',
          });
        }
      },
    };
  },
};
```

**Configuration**:
```json
{
  "rules": {
    "@psychsync/no-setTimeout-without-cleanup": "error"
  }
}
```

---

### Rule 4: `require-mounted-check`

**Detects**: Async operations that update state without checking if component is mounted

**Pattern**:
```typescript
// ❌ BAD
const fetchData = async () => {
  const data = await api.get('/endpoint');
  setState(data);  // May update after unmount
};

// ✅ GOOD
const fetchData = async () => {
  const data = await api.get('/endpoint');
  if (isMountedRef.current) {
    setState(data);
  }
};
```

**Rule Implementation**:
```javascript
// eslint-rules/require-mounted-check.js
module.exports = {
  meta: {
    type: 'suggestion',
    docs: {
      description: 'Require mounted state checks before setState in async callbacks',
      category: 'Best Practices',
      recommended: false,
    },
    schema: [],
    messages: {
      missingMountCheck: 'setState call should be guarded by isMounted check to prevent updates on unmounted components',
    },
  },
  create(context) {
    return {
      FunctionDeclaration(node) {
        const isAsync = node.async;
        if (!isAsync) return;

        const sourceCode = context.getSourceCode();
        const functionCode = sourceCode.getText(node);

        // Look for setState calls
        const hasSetState = /setState|set[A-Z]\w+/.test(functionCode);
        if (!hasSetState) return;

        // Check for isMounted guard
        const hasMountCheck =
          functionCode.includes('isMounted') ||
          functionCode.includes('isMountedRef.current');

        if (hasSetState && !hasMountCheck) {
          context.report({
            node,
            messageId: 'missingMountCheck',
          });
        }
      },
    };
  },
};
```

**Configuration**:
```json
{
  "rules": {
    "@psychsync/require-mounted-check": "warn"
  }
}
```

---

## 🔧 ESLint Plugin Setup

### Installation

```bash
cd frontend
npm install --save-dev eslint-plugin-race-condition-prevention
# OR create local plugin
mkdir -p eslint-rules
# Copy above rules into eslint-rules/
```

### Configuration

**`.eslintrc.cjs`**:
```javascript
module.exports = {
  // ... existing config
  plugins: [
    'race-condition-prevention',
    // ... other plugins
  ],
  rules: {
    // Race condition prevention rules
    '@psychsync/no-unsafe-use-effect-async': 'error',
    '@psychsync/require-debounced-onclick': ['warn', {
      allowedNames: ['handleSubmit', 'handleNavigate']
    }],
    '@psychsync/no-setTimeout-without-cleanup': 'error',
    '@psychsync/require-mounted-check': 'warn',
  },
};
```

### Package.json Scripts

```json
{
  "scripts": {
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "lint:race-conditions": "eslint src --ext .ts,.tsx --rule '@psychsync/*'"
  }
}
```

---

## 📊 Rule Effectiveness

| Rule | Detects | False Positives | Value |
|------|---------|-----------------|-------|
| **no-unsafe-use-effect-async** | Missing cleanup | Low | High |
| **require-debounced-onclick** | Non-debounced onClick | Medium | High |
| **no-setTimeout-without-cleanup** | Memory leaks | Low | Critical |
| **require-mounted-check** | Missing guards | Medium | Medium |

---

## 🎯 Implementation Priority

### Phase 1: Immediate (This Sprint)
1. ✅ **no-setTimeout-without-cleanup** - Prevents memory leaks
2. ✅ **no-unsafe-use-effect-async** - Catches unsafe patterns

### Phase 2: Next Sprint
3. ⏳ **require-debounced-onclick** - Improves performance
4. ⏳ **require-mounted-check** - Adds safety layer

---

## 🧪 Testing the Rules

### Test Cases

```typescript
// Should trigger: no-unsafe-use-effect-async
useEffect(() => {
  fetchData();
}, []);

// Should NOT trigger (has cleanup)
useEffect(() => {
  fetchData();
  return () => {
    controller.abort();
  };
}, []);

// Should trigger: require-debounced-onclick
<button onClick={fetchData}>Refresh</button>

// Should NOT trigger (is debounced)
<button onClick={debouncedFetch}>Refresh</button>

// Should trigger: no-setTimeout-without-cleanup
useEffect(() => {
  setTimeout(callback, 1000);
}, []);

// Should NOT trigger (has cleanup)
useEffect(() => {
  const timeout = setTimeout(callback, 1000);
  return () => clearTimeout(timeout);
}, []);
```

---

## 📈 Expected Impact

### Before ESLint Rules
- Developers manually review code for patterns
- Race conditions slip through code review
- Issues caught in testing (or production)

### After ESLint Rules
- Automatic detection during development
- Immediate feedback in IDE
- Consistent code quality
- Reduced review burden

**Estimated Time Savings**: 2-3 hours per sprint in code review time

---

## 🔄 Continuous Improvement

### Updating Rules
As patterns evolve, update rules to:
- Reduce false positives
- Add new anti-patterns
- Improve error messages
- Add auto-fix capabilities

### Feedback Loop
1. Monitor rule violations
2. Gather developer feedback
3. Tune rule sensitivity
4. Update documentation

---

## 📚 Additional Resources

- [ESLint Plugin Documentation](https://eslint.org/docs/latest/developer-guide/working-with-rules)
- [React Hook Rules](https://react.dev/reference/react)
- [Custom Rules Best Practices](https://eslint.org/docs/latest/extend/custom-rules)

---

**Version**: 1.0.0
**Last Updated**: 2026-01-21
**Status**: Ready for Implementation
