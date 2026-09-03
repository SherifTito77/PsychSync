# Security Pipeline Quick Reference

## 🚀 Quick Start (5 minutes)

### One-Time Setup
```bash
# 1. Install pre-commit hook
ln -s .git/hooks/pre-commit.dependency-check .git/hooks/pre-commit

# 2. Verify workflows are present
ls -la .github/workflows/*.yml

# 3. Check allow-lists
cat allowed-dependencies.txt | head -20
cat frontend/allowed-dependencies.json | jq '.allowedDependencies.core' | head -20
```

### Daily Workflow
```bash
# 1. Create branch
git checkout -b feature/my-feature

# 2. Work and commit (hook runs automatically)
git add .
git commit -m "feat: add feature"

# 3. Push and create PR
git push origin feature/my-feature
# CI runs automatically on PR creation
```

## 📦 Adding Dependencies (2 minutes)

### Python
```bash
# 1. Add to allow-list FIRST
echo "package-name==1.0.0,2.0.0  # Purpose" >> allowed-dependencies.txt

# 2. Install
pip install package-name==1.5.0

# 3. Update requirements.txt
echo "package-name==1.5.0" >> requirements.txt

# 4. Commit both together
git add allowed-dependencies.txt requirements.txt
git commit -m "feat: add package-name"
```

### JavaScript
```bash
cd frontend

# 1. Add to allowed-dependencies.json first
# Edit the file and add your package

# 2. Install
npm install package-name@1.5.0

# 3. Commit both together
git add allowed-dependencies.json package.json package-lock.json
git commit -m "feat: add package-name"
```

## 🔧 Local Security Testing

### Run SAST
```bash
./scripts/run-sast.sh
```

### Run DAST
```bash
# Start backend first
uvicorn app.main:app --reload &

# Run DAST
./scripts/run-dast.sh
```

### Check Allow-List
```bash
./scripts/check-allowlist.sh
```

## 📊 CI/CD Status Checks

### What Runs on PRs
```
Dependency Governance (4 jobs, ~30 sec)
├── Allow-List Compliance      ← BLOCKS if violations
├── Version Validation         ← BLOCKS if out of range
├── Blocked Dependencies       ← BLOCKS if dangerous pkgs
└── Dependency Report          ← Summary only

Security CI/CD (7 jobs, ~5-10 min)
├── SAST (Bandit)              ← BLOCKS on high severity
├── SCA (pip-audit/npm)        ← BLOCKS on critical
├── Secret Scanning            ← BLOCKS on secrets
├── SBOM Generation            ← Always runs
├── DAST (Security Tests)      ← Reports findings
├── SLSA Provenance            ← Always runs
└── Container Signing          ← On main branch
```

### Reading the Results

**GitHub Actions Tab:**
- ✅ Green = All checks passed, ready to merge
- ❌ Red = Blocking violation, must fix
- ⚠️ Yellow = Warning, review recommended

**GitHub Security Tab:**
- Dependabot alerts = Dependency vulnerabilities
- Code scanning = SAST findings
- Secret scanning = Leaked secrets

## 🚨 Common Issues & Fixes

### Issue: "Dependency not in allow-list"
```
Error: New Python packages not in allow-list: numpy
```
**Fix:**
```bash
# Add to allow-list first
echo "numpy==1.24.0,2.0.0  # Numerical computing" >> allowed-dependencies.txt
git add allowed-dependencies.txt requirements.txt
git commit -m "feat: add numpy dependency"
```

### Issue: "High-severity security issues"
```
Error: Found 2 high-severity security issues
```
**Fix:**
1. Check Bandit report: `cat bandit-report.json | jq '.results[] | select(.issue_severity == "HIGH")'`
2. Fix the security issues in code
3. Commit fixes
4. CI will re-run

### Issue: "Version outside approved range"
```
Error: fastapi==0.100.0 (allowed: 0.104.0-0.120.0)
```
**Fix:**
```bash
# Use version within range
pip install fastapi==0.104.0
# Update requirements.txt
# Commit changes
```

### Issue: "Blocked dependencies detected"
```
Error: Blocked dependencies found: eval
```
**Fix:**
1. Remove the blocked package immediately
2. Find approved alternative in allow-list
3. Update code to use alternative
4. Commit fixes

## 📈 Pipeline Performance

### Expected Timings
| Check | Duration | When |
|-------|----------|------|
| Pre-commit hook | ~5 sec | On commit |
| Dependency governance | ~30 sec | On PR |
| Security CI/CD | ~5-10 min | On PR |
| Container signing | ~2 min | On merge to main |

### Reducing Wait Time
- Only push to feature branches (not main/develop)
- Use `dependabot.yml` grouping to reduce PR count
- Skip DAST for non-critical changes (configure in workflow)
- Cache dependencies (already configured)

## 🎯 Best Practices

### DO ✅
- Always add to allow-list BEFORE installing
- Commit allow-list changes with dependency changes
- Review Dependabot PRs within 24 hours
- Run SAST locally before pushing
- Use pre-commit hook for early feedback

### DON'T ❌
- Bypass pre-commit hook with `--no-verify`
- Add dependencies outside allow-list
- Ignore security warnings
- Skip version validation
- Merge failing PRs

## 📞 Getting Help

| Question | Resource |
|----------|----------|
| How do I add a dependency? | `docs/DEPENDENCY_GOVERNANCE.md` |
| Why did CI fail? | Check GitHub Actions logs |
| Is this package allowed? | Check `allowed-dependencies.txt` |
| Security vulnerability? | Contact security team |
| Pipeline error? | Check workflow files in `.github/workflows/` |

## 🔍 Verification Commands

### Verify Pipeline is Active
```bash
# Check workflow files exist
ls -la .github/workflows/*.yml

# Check Dependabot config
cat .github/dependabot.yml

# Check allow-lists
cat allowed-dependencies.txt
cat frontend/allowed-dependencies.json
```

### Test with Safe Change
```bash
# Create test branch
git checkout -b test/pipeline-test

# Make safe change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "test: verify pipeline"
git push origin test/pipeline-test

# Create PR in GitHub and verify all checks pass
```

## 📚 Full Documentation

- **Complete Guide**: `SUPPLY_CHAIN_SECURITY_COMPLETE.md`
- **Dependency Governance**: `docs/DEPENDENCY_GOVERNANCE.md`
- **NIST SSDF v1.1**: `NIST_SSDF_v1.1_PLAYBOOK.md`
- **Security Quick Reference**: `docs/SECURITY_QUICK_REFERENCE.md`

---

**Last Updated**: December 25, 2024
**Pipeline Version**: 1.0.0
**Framework**: NIST SSDF v1.1 + SLSA Level 3
