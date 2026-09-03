# 🧪 Memory Leak Testing for QA

## Quick Start (30 seconds)

```bash
# Option 1: Run the script (does everything automatically)
./frontend/scripts/run-memory-test.sh

# Option 2: Open directly in browser
open frontend/scripts/quick-memory-test.html
```

That's it! The test will run automatically and show you results.

---

## What It Does

The automated test:

1. ✅ Opens your PsychSync application
2. ✅ Simulates real user actions (clicking, scrolling, navigating)
3. ✅ Monitors memory usage every 2 seconds
4. ✅ Tracks memory growth over time
5. ✅ Alerts you if memory leaks are detected
6. ✅ Generates downloadable JSON report

---

## Test Duration Options

### ⚡ Quick Test (2 minutes)
- **Best for**: Quick validation before deploying
- **Actions**: 12 iterations over 2 minutes
- **Decision**: Fast PASS/FAIL result

### ▶️ Full Test (10 minutes)
- **Best for**: Thorough pre-release validation
- **Actions**: 60 iterations over 10 minutes
- **Decision**: Detailed memory analysis

---

## Reading Results

### ✅ PASS (Green)
```
Memory Growth: +7.6 MB
Status: ✅ TEST PASSED
```
**Meaning**: Memory is stable. Safe to deploy.

### ⚠️ WARN (Yellow)
```
Memory Growth: +68.2 MB
Status: ⚠️ TEST WARNING
```
**Meaning**: Moderate growth. Review recent changes before deploying.

### ❌ FAIL (Red)
```
Memory Growth: +142.8 MB
Status: 🚨 TEST FAILED
```
**Meaning**: Memory leak detected! Fix before deploying.

---

## Success Criteria

| Test Duration | PASS | WARN | FAIL |
|---------------|------|------|------|
| 2 minutes | < 15 MB | 15-30 MB | > 30 MB |
| 10 minutes | < 50 MB | 50-100 MB | > 100 MB |

---

## Common Issues

### "Performance.memory is undefined"

**Fix**: Launch Chrome with memory flags:
```bash
# Mac
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --enable-precise-memory-info

# Then open the test file again
```

### Test doesn't start

**Check**:
1. Is frontend running? (`npm run dev` in `/frontend` directory)
2. Are you on `http://localhost:5173`?
3. Check browser console for errors

### Results show high growth but no obvious leak

**This might be OK!** Single-page apps normally accumulate 20-40 MB during a session. The key is:
- ✅ Growth should **plateau** (stop increasing)
- ❌ Leaks show **unbounded growth** (keeps rising)

---

## Pre-Release Checklist

Before every release:

```bash
# 1. Ensure frontend is running
cd frontend
npm run dev

# 2. Run the memory test
./scripts/run-memory-test.sh

# 3. Verify result is ✅ PASS

# 4. Document results in release notes
```

---

## Advanced Testing

For detailed memory profiling, see:
- 📖 [Full QA Guide](../../docs/QA_LOAD_TESTING_GUIDE.md)
- 🎓 [Team Training](../../docs/TEAM_TRAINING_MEMORY_MANAGEMENT.md)

---

## Questions?

**Quick Help**: See the interactive test page - it has built-in instructions!

**Detailed Help**: Check `docs/QA_LOAD_TESTING_GUIDE.md`

**Team Support**: Ask in #qa-automation or #dev-frontend channels

---

## Summary

- **Time Required**: 2-10 minutes
- **Difficulty**: Very easy
- **Automation**: Fully automated
- **Results**: Instant PASS/FAIL/WARN

**You're ready to test! 🚀**
