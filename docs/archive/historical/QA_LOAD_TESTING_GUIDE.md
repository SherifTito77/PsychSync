# 🧪 QA Guide: Running Memory Leak Load Tests

**Audience**: QA Engineers, Testers, SREs
**Duration**: 10-15 minutes
**Difficulty**: Beginner-friendly

---

## 🎯 Objective

Run automated memory leak tests before each release to ensure the application doesn't accumulate memory over time.

---

## ⚡ Quick Start (3 Options)

### Option 1: Browser-Based Test (Easiest) ✨

**Best for**: Quick validation before releases
**Time**: 2-10 minutes
**Difficulty**: ⭐ Very Easy

```bash
# 1. Open the test file in Chrome
open frontend/scripts/quick-memory-test.html

# 2. Click "Quick Test (2 min)" for fast validation
#    Or "Start 10-Minute Test" for thorough testing

# 3. Wait for automatic results

# 4. Download results JSON
```

That's it! The test will:
- ✅ Navigate through your app
- ✅ Simulate user interactions
- ✅ Track memory usage
- ✅ Alert you if leaks are detected
- ✅ Generate downloadable report

---

### Option 2: Manual Chrome DevTools Test

**Best for**: Detailed memory profiling
**Time**: 10-30 minutes
**Difficulty**: ⭐⭐ Moderate

#### Step 1: Open DevTools

1. Open Chrome
2. Navigate to `http://localhost:5173`
3. Press **F12** (or **Cmd+Option+I** on Mac)
4. Go to **Memory** tab

#### Step 2: Take Baseline Snapshot

1. Click "Take heap snapshot"
2. Rename it to "Baseline"
3. Note the heap size

#### Step 3: Exercise the Application

Open Chrome Console (Cmd+Option+J) and run:

```javascript
// Load test script - runs for 10 minutes
let iterations = 0;
const maxIterations = 60; // 60 iterations = 10 minutes

const testInterval = setInterval(() => {
    // Random actions
    const actions = [
        () => window.location.reload(),
        () => window.scrollTo(0, document.body.scrollHeight),
        () => window.history.back(),
        () => window.history.forward(),
    ];

    const action = actions[iterations % actions.length];
    action();

    // Log memory every 10 iterations
    if (iterations % 10 === 0 && performance.memory) {
        console.log(`Iteration ${iterations}:`, {
            memory: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
            heap: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB',
        });
    }

    iterations++;

    if (iterations >= maxIterations) {
        clearInterval(testInterval);
        console.log('✅ Load test complete! Take a final heap snapshot now.');
    }
}, 10000); // Every 10 seconds
```

#### Step 4: Take Final Snapshot

1. Click "Take heap snapshot" again
2. Rename it to "Final"
3. Select "Baseline" snapshot
4. Change view from "Summary" to "Comparison"

#### Step 5: Analyze Results

Look for:
- **Detached DOM nodes** > 100 = ❌ Memory leak
- **Event listeners** increasing significantly = ❌ Leak
- **JS Heap Size** growth > 50MB = ⚠️ Review

---

### Option 3: Automated Script (Advanced)

**Best for**: CI/CD integration
**Time**: Runs automatically
**Difficulty**: ⭐⭐⭐ Advanced

See `frontend/scripts/memory-leak-load-test.md` for Puppeteer automation.

---

## 📊 Understanding Results

### Test Output Example

```
=== FINAL RESULTS ===
Initial Memory: 45.2 MB
Final Memory: 52.8 MB
Total Growth: +7.6 MB
Test Duration: 10.0 minutes
Growth Rate: 0.76 MB/min

✅ TEST PASSED: Memory usage is stable
```

### Interpretation Guide

| Growth | Status | Meaning |
|--------|--------|---------|
| **0-20 MB** | ✅ PASS | Excellent! Memory is stable |
| **20-50 MB** | ✅ PASS | Acceptable for 10-minute test |
| **50-100 MB** | ⚠️ WARN | Review before deploying |
| **> 100 MB** | ❌ FAIL | Memory leak detected - fix required |

### Example Scenarios

#### ✅ Good Result
```
Initial: 45 MB
Final: 52 MB
Growth: +7 MB (10 min)
→ PASS: Deploy with confidence
```

#### ⚠️ Warning Result
```
Initial: 45 MB
Final: 95 MB
Growth: +50 MB (10 min)
→ WARN: Review recent changes, consider additional testing
```

#### ❌ Fail Result
```
Initial: 45 MB
Final: 180 MB
Growth: +135 MB (10 min)
→ FAIL: Memory leak! Investigate before deploying
```

---

## 🔍 Troubleshooting

### Issue: "Performance.memory is undefined"

**Cause**: Chrome doesn't have precise memory info enabled

**Solution**:
```bash
# Mac
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --enable-precise-memory-info \
  --js-flags=--expose-gc

# Windows
chrome.exe --enable-precise-memory-info --js-flags=--expose-gc

# Linux
google-chrome --enable-precise-memory-info --js-flags=--expose-gc
```

---

### Issue: Test won't start

**Checklist**:
- [ ] Is the frontend running? (`npm run dev`)
- [ ] Are you on `http://localhost:5173`?
- [ ] Is Chrome DevTools open?
- [ ] Console shows no errors?

---

### Issue: Memory keeps growing

**Don't panic!** Follow these steps:

1. **Verify it's a real leak**:
   - Wait 2 minutes after test completes
   - Click "Collect garbage" in DevTools Memory tab
   - If memory drops significantly, it's not a leak

2. **Find the leak**:
   - Take heap snapshots during test
   - Compare "Baseline" vs "Final"
   - Look for "Retainers" with high memory
   - Check "Detached DOM nodes"

3. **Common culprits**:
   - Missing `return () => cleanup()` in useEffect
   - Event listeners not removed
   - Timers not cleared
   - WebSocket not closed

4. **Get help**:
   - See `docs/TEAM_TRAINING_MEMORY_MANAGEMENT.md`
   - Ask in #dev-frontend channel

---

## 📋 Pre-Release Checklist

Before every release, run through this checklist:

### Memory Tests
- [ ] Quick 2-minute test passes
- [ ] Full 10-minute test passes (optional but recommended)
- [ ] Memory growth < 50 MB
- [ ] No detached DOM node accumulation

### ESLint
- [ ] `npm run lint` passes with no memory leak warnings
- [ ] No new `no-uncleaned-*` errors

### Redis Cache
- [ ] `python scripts/redis-memory-monitor.py --duration 5` shows < 20 MB growth
- [ ] TTL coverage > 80%

### Sign-off
- [ ] Results documented in release notes
- [ ] Screenshots saved for comparison
- [ ] Any failures investigated and resolved

---

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Memory Leak Test

on:
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

jobs:
  memory-test:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Start dev server
        run: |
          cd frontend
          npm run dev &
          sleep 10

      - name: Run memory test
        run: |
          # Option 1: Use Node.js script
          node scripts/run-memory-test.js

          # Option 2: Use Python Selenium
          python scripts/memory-test-selenium.py

      - name: Check results
        run: |
          python scripts/check-memory-results.py memory-test-results.json

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: memory-test-results
          path: |
            frontend/memory-test-results.json
            frontend/screenshots/
```

---

## 📈 Interpreting Results in Context

### Single Page vs Multi-Page Apps

**SPA (Single Page App)** like PsychSync:
- Memory usage typically increases 20-40 MB during session
- This is **normal** due to component state, data caching
- Look for **unbounded growth** as the red flag

**Expected Pattern**:
```
Time 0:    45 MB
Time 10:   60 MB  ← Normal state/data accumulation
Time 20:   62 MB  ← Should plateau
Time 30:   63 MB  ← Stable = Good!
```

**Abnormal Pattern** (Memory Leak):
```
Time 0:    45 MB
Time 10:   60 MB
Time 20:   95 MB  ← Unbounded growth = BAD!
Time 30:   145 MB ← Leak detected!
```

---

## 🎓 Best Practices for QA

1. **Baseline First**
   - Run tests on known-good version first
   - Save baseline results for comparison

2. **Consistent Environment**
   - Same browser version
   - Same test duration
   - Similar user actions

3. **Document Results**
   - Save results JSON for each test
   - Note any anomalies
   - Track trends over time

4. **Compare Builds**
   - Test current build vs. previous build
   - Watch for regressions

5. **Use Multiple Methods**
   - Browser test (quick check)
   - DevTools (detailed profile)
   - Redis monitoring (backend)

---

## 📞 Getting Help

### Resources

- **Training**: `docs/TEAM_TRAINING_MEMORY_MANAGEMENT.md`
- **Full Guide**: `frontend/scripts/memory-leak-load-test.md`
- **Redis Guide**: `docs/REDIS_MONITORING_GUIDE.md`

### Escalation Path

1. **Minor warnings** (< 50 MB growth)
   - Document in release notes
   - Monitor in production

2. **Moderate warnings** (50-100 MB growth)
   - Discuss with team lead
   - Additional testing required

3. **Critical failures** (> 100 MB growth)
   - Block deployment
   - File GitHub issue with label `memory-leak`
   - Engage frontend team immediately

---

## ✅ Success Stories

### Example 1: Pre-Release Validation

**Scenario**: Before v2.3.0 release

**Test Results**:
```
Initial Memory: 42.5 MB
Final Memory: 48.2 MB
Growth: +5.7 MB
Status: ✅ PASS
```

**Action**: Approved for production deployment

---

### Example 2: Leak Detection

**Scenario**: Testing new real-time features

**Test Results**:
```
Initial Memory: 45.0 MB
Final Memory: 187.3 MB
Growth: +142.3 MB
Status: ❌ FAIL
```

**Investigation**: Found WebSocket not closing in cleanup

**Fix Applied**:
```typescript
// Added cleanup
return () => {
  if (wsRef.current) {
    wsRef.current.close(); // ← This was missing!
    wsRef.current = null;
  }
};
```

**Retest**: Growth reduced to +8 MB ✅

---

## 🎉 Summary

**Running memory leak tests is now:**

1. ✅ **Fast**: 2-10 minutes
2. ✅ **Easy**: Just open HTML file
3. ✅ **Automated**: Results generated automatically
4. ✅ **Reliable**: Consistent test methodology

**Your QA process for memory leaks:**

```bash
# 1. Start frontend
npm run dev

# 2. Open test in browser
open frontend/scripts/quick-memory-test.html

# 3. Click "Quick Test (2 min)"

# 4. Wait for results

# 5. Check status:
#    ✅ PASS → Deploy
#    ⚠️ WARN → Review
#    ❌ FAIL → Fix
```

---

**Questions?** See `docs/TEAM_TRAINING_MEMORY_MANAGEMENT.md` or ask in #qa-automation channel!
