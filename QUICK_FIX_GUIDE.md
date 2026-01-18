# Quick Fix Guide: Environment & Debugging Issues

**Priority:** CRITICAL - Fix before production deployment
**Time Estimate:** 2-3 days

---

## 🚨 Top 5 Critical Fixes

### 1. Remove Console Logging (187 files)

**Find them:**
```bash
cd frontend
find src -name "*.ts" -o -name "*.tsx" | xargs grep -l "console\."
```

**Fix pattern:**
```typescript
// BEFORE (BAD):
console.log('User data:', userData);
console.error('Error:', error);

// AFTER (GOOD):
if (import.meta.env.DEV) {
  logger.debug('User data received', { userId: userData.id });
  logger.error('Error occurred', { error: error.message });
}
```

**Automated fix:**
```bash
# Install ESLint console rule
npm install --save-dev eslint-plugin-no-console

# Add to .eslintrc.js:
{
  "rules": {
    "no-console": "error"
  },
  "env": {
    "browser": true,
    "es2021": true
  }
}
```

### 2. Fix Debug Mode Bypasses

**Find them:**
```bash
cd app
grep -rn "if.*DEBUG.*:" . --include="*.py"
```

**Fix pattern:**
```python
# BEFORE (BAD):
if settings.DEBUG:
    return None  # Bypasses security

# AFTER (GOOD):
if settings.DEBUG:
    return RateLimitConfig(requests_per_minute=1000)
else:
    return RateLimitConfig(requests_per_minute=100)
```

### 3. Complete Security TODOs

**Find security TODOs:**
```bash
grep -rn "TODO.*security" app/
grep -rn "TODO.*lockout" app/
grep -rn "TODO.*consent" app/
grep -rn "TODO.*IP.*block" app/
```

**Priority fixes:**
1. IP blocking (app/middleware/security.py:162)
2. Lockout notification (app/core/account_lockout_enhanced.py:309)
3. Biometric consent (app/api/v1/endpoints/health_monitoring.py:399)

### 4. Enable Performance Services

**File:** app/main.py:103-114

**Action:** Uncomment these lines:
```python
from app.services.enhanced_cache_service import cache_service
from app.services.memory_management_service import memory_service
from app.services.query_optimization_service import QueryOptimizer
```

**Then initialize properly (don't use None placeholders).**

### 5. Fix Hardcoded Environment Configs

**Frontend (env.ts):**
```typescript
// BEFORE (BAD):
switch (ENV) {
  case 'production': return 'https://api.psychsync.com';
  case 'development': return 'http://localhost:8000';
}

// AFTER (GOOD):
return import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

**Backend (config.py):**
```python
# BEFORE (BAD):
if "http://localhost:5177" not in CORS_ORIGINS:
    CORS_ORIGINS.append("http://localhost:5177")

# AFTER (GOOD):
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
```

---

## 📋 Pre-Production Checklist

Run this before deploying to production:

```bash
#!/bin/bash
echo "🔍 Production Readiness Check"
echo "================================"

# 1. Check for console.log in frontend
echo "Checking for console.log..."
CONSOLE_COUNT=$(find frontend/src -name "*.ts" -o -name "*.tsx" | xargs grep -c "console\." 2>/dev/null || echo "0")
if [ "$CONSOLE_COUNT" -gt "0" ]; then
  echo "❌ Found $CONSOLE_COUNT console statements"
else
  echo "✅ No console statements found"
fi

# 2. Check for debug mode bypasses
echo "Checking for DEBUG bypasses..."
DEBUG_BYPASSES=$(grep -r "if.*DEBUG.*:" app/ --include="*.py" | grep -v "settings.DEBUG" | wc -l)
if [ "$DEBUG_BYPASSES" -gt "0" ]; then
  echo "❌ Found $DEBUG_BYPASSES debug mode bypasses"
else
  echo "✅ No debug bypasses found"
fi

# 3. Check for security TODOs
echo "Checking for security TODOs..."
SECURITY_TODOS=$(grep -r "TODO.*security\|TODO.*lockout\|TODO.*consent" app/ --include="*.py" | wc -l)
if [ "$SECURITY_TODOS" -gt "0" ]; then
  echo "❌ Found $SECURITY_TODOS security TODOs"
else
  echo "✅ No security TODOs found"
fi

# 4. Check for disabled performance services
echo "Checking for disabled services..."
DISABLED_SERVICES=$(grep -c "= None" app/main.py)
if [ "$DISABLED_SERVICES" -gt "0" ]; then
  echo "❌ Found disabled services"
else
  echo "✅ All services enabled"
fi

echo "================================"
echo "Check complete!"
```

---

## 🛠️ Automated Fix Script

Create `scripts/remove_debugging_artifacts.sh`:

```bash
#!/bin/bash
echo "Removing debugging artifacts..."

# Remove console.log from TypeScript files
find frontend/src -name "*.ts" -o -name "*.tsx" | while read file; do
  # Replace console.log with conditional logging
  sed -i.bak 's/console\.log(/ logger.debug(/g' "$file"
  rm "${file}.bak"
done

echo "✅ Console statements replaced"
echo "⚠️  Review changes before committing!"
```

---

## 📚 Best Practices

### ✅ DO This:

```typescript
// Use proper logging
import { logger } from '@/utils/logger';
logger.info('User action', { action: 'login', userId: user.id });

// Use environment variables
const apiUrl = import.meta.env.VITE_API_URL;

// Conditional debug code
if (import.meta.env.DEV) {
  logger.debug('Debug info');
}
```

### ❌ DON'T Do This:

```typescript
// Console logging in production
console.log('User data:', userData);  // ❌

// Hardcoded URLs
const apiUrl = 'http://localhost:8000';  // ❌

// Debug mode bypasses security
if (DEBUG) return null;  // ❌
```

---

## 🎯 Priority Order

**Fix in this order:**

1. **Console logging** (187 files) - 4 hours
2. **Debug bypasses** (5-10 files) - 2 hours
3. **Security TODOs** (10-15 files) - 8 hours
4. **Performance services** (1 file) - 2 hours
5. **Environment configs** (5-10 files) - 4 hours

**Total: ~20 hours (2.5 days)**

---

## 📞 Help Needed?

If you encounter issues:

1. See `ENVIRONMENT_DEBUGGING_ANALYSIS.md` for detailed analysis
2. Review code snippets in this guide
3. Test fixes in development environment first
4. Create PR for review after fixing

---

**Last Updated:** 2025-01-18
**Status:** Ready for implementation
