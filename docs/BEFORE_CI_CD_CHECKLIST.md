# Before CI/CD - Immediate Action Checklist

## ✅ What You Can Do RIGHT NOW (5 minutes)

### 1. Verify Your Code Compiles
```bash
# Test all your endpoint files compile
for file in app/api/v1/endpoints/*.py; do
  python3 -m py_compile "$file" 2>&1 && echo "✅ $file" || echo "❌ $file"
done

# Count how many are broken
broken=0
for file in app/api/v1/endpoints/*.py; do
  if ! python3 -m py_compile "$file" 2>/dev/null; then
    ((broken++))
  fi
done
echo "Files with syntax errors: $broken"
```

### 2. See Your Generated Tests
```bash
# List all test files that were created
ls -lh tests/api/test_*.py

# View one test file
cat tests/api/test_predictions.py

# Count test functions
grep -r "def test_" tests/api/ | wc -l
```

### 3. Run the Documentation Agent
```bash
# Generate fresh documentation report
python3 agents/doc_completeness_agent.py --code-path app/

# Check the score
cat reports/doc_coverage.json | python3 -c "import json, sys; data=json.load(sys.stdin); print(f'Score: {data[\"overall_score\"]:.1f}/100')"
```

### 4. Run the Dead Code Detector
```bash
# Find unused imports (review only, don't auto-remove)
python3 agents/dead_code_agent.py --code-path app/ --exclude migrations alembic

# View the report
cat reports/dead_code.json | python3 -c "import json, sys; data=json.load(sys.stdin); print(f'Unused imports: {len(data[\"unused_imports\"])}')"
```

### 5. Test One Endpoint Manually
```bash
# Start your server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, test an endpoint
curl http://localhost:8000/api/v1/health
```

---

## 🎯 Priority Actions (Do These First)

### High Priority: Fix Remaining Syntax Errors
```bash
# Check which files are still broken
python3 -m py_compile app/api/v1/endpoints/slack.py
python3 -m py_compile app/api/v1/endpoints/optimizer.py
python3 -m py_compile app/api/v1/endpoints/templates.py

# Get specific error message
python3 -m py_compile app/api/v1/endpoints/YOUR_FILE.py 2>&1
```

### Medium Priority: Review Generated Tests
```bash
# Open a test file and add actual test logic
code tests/api/test_predictions.py

# Implement one simple test
# Add assertions like:
assert response.status_code == 200
assert response.json()["success"] == True
```

### Low Priority: Clean Up Unused Imports
```bash
# Manually check if an import is used
grep -r "Union" app/core/tasks.py

# If count is 0 or only in import statement, safe to remove
```

---

## 📊 Quick Status Check (One Command)

```bash
echo "=== PsychSync Pre-CI/CD Status ==="
echo ""
echo "📁 Test files generated:"
find tests/api/test_*.py 2>/dev/null | wc -l
echo ""
echo "🔨 Syntax errors remaining:"
for file in app/api/v1/endpoints/*.py; do
  if ! python3 -m py_compile "$file" 2>/dev/null; then
    echo "$file"
  fi
done | wc -l
echo ""
echo "📚 Documentation score:"
python3 agents/doc_completeness_agent.py --code-path app/ 2>&1 | grep "Overall Score" | head -1
```

---

## 🚀 After You Do These

Once you've completed the above, you'll have:

✅ **Known syntax error count** - Exact number of files needing fixes
✅ **Generated test scaffolds** - Ready for implementation
✅ **Documentation baseline** - Current coverage score
✅ **Dead code inventory** - Safe cleanup list

**Then** you can add CI/CD with confidence because you'll know exactly what to expect!

---

## 💡 Pro Tips

1. **Fix syntax errors first** - Everything else depends on this
2. **Don't auto-remove dead code** - Always verify manually first
3. **Implement tests gradually** - Start with critical endpoints
4. **Run agents locally first** - See what they find before automating

---

## 📝 Example Session

```bash
# 1. Check compilation
$ for f in app/api/v1/endpoints/*.py; do python3 -m py_compile "$f" 2>&1 || echo "BROKEN: $f"; done

# 2. Run documentation agent
$ python3 agents/doc_completeness_agent.py --code-path app/

# 3. Check test coverage
$ ls tests/api/test_*.py | wc -l
72

# 4. Try to start server
$ uvicorn app.main:app --reload
# If it starts, your syntax fixes worked!
```

This gives you instant feedback without any CI/CD setup! 🎉
