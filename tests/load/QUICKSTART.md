# 🚀 Rate Limiting Load Testing - Quick Start Guide

## One-Line Quick Test

```bash
python tests/load/quick_rate_limit_test.py
```

That's it! This will validate your rate limiting is working in ~30 seconds.

---

## What to Expect

### ✅ Healthy Rate Limiting

```
╔═══════════════════════════════════════════════════════════════╗
║         Rate Limiting Quick Validation Test                  ║
╚═══════════════════════════════════════════════════════════════╝

✓ Server is running

TEST 1: Health Endpoint Rate Limiting
  Successful (200): 50
  Throttled (429):  10

✓ Rate limiting is WORKING

═══════════════════════════════════════════════════════════════
✓ ALL TESTS PASSED - Rate limiting is working correctly!
═══════════════════════════════════════════════════════════════
```

### ⚠️  If Tests Fail

```
✗ Cannot connect to backend server
```

**Solution:** Start your backend first
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## All Testing Options

### 1. Quick Validation (30s) ⚡
```bash
python tests/load/quick_rate_limit_test.py
```

### 2. Automated Tests (2min) 🔧
```bash
./tests/load/run_load_tests.sh quick
```

### 3. Full Test Suite (5min) 🧪
```bash
python -m pytest tests/load/test_rate_limiting_load.py -v -m load
```

### 4. Interactive Load Testing 🎨
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
# Open http://localhost:8089
```

---

## What Gets Tested

✅ Requests within limits are accepted (200)
✅ Requests exceeding limits are throttled (429)
✅ Rate limit headers are present
✅ Different user tiers have different limits
✅ Sliding window resets properly
✅ Response times stay acceptable
✅ System stays stable under load

---

## Rate Limits Reference

| User Type | Requests/Min | Requests/Hour |
|-----------|--------------|---------------|
| Anonymous | 50 | 200 |
| Basic | 200 | 1,000 |
| Premium | 500 | 2,500 |
| Enterprise | 1,000 | 5,000 |
| Admin | 2,000 | 10,000 |

---

## Troubleshooting

### Server not running?
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Redis not running?
```bash
redis-server
```

### Port already in use?
```bash
lsof -i :8000
kill -9 <PID>
```

---

## Full Documentation

- **Detailed Guide:** `tests/load/README.md`
- **Implementation Summary:** `tests/load/SUMMARY.md`
- **Complete Overview:** `IMPLEMENTATION_RATE_LIMITING_LOAD_TESTS.md`

---

## Next Steps

After running the quick test:

1. ✅ Check that tests pass
2. 📊 Review metrics (response times, throttle rate)
3. 🧪 Run full test suite for detailed validation
4. 🎨 Use Locust for interactive exploration

Ready? Run this now:

```bash
python tests/load/quick_rate_limit_test.py
```
