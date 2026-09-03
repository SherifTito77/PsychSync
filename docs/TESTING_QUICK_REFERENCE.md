# 🧪 Testing Quick Reference Card

## 🚀 **Run All Tests (One Command)**

```bash
./run_clinical_tests.sh
```

---

## 📊 **Individual Test Suites**

### **Layer 1: Unit Tests** (Scoring Algorithms)
```bash
# Test all scoring functions
pytest tests/test_clinical_scoring.py -v

# Test specific tool
pytest tests/test_clinical_scoring.py::TestPHQ9Scoring -v

# Test specific case
pytest tests/test_clinical_scoring.py::TestPHQ9Scoring::test_suicide_ideation_triggers_crisis -v

# With coverage
pytest tests/test_clinical_scoring.py --cov=app/services/clinical --cov-report=html
```

### **Layer 2: API Tests** (Endpoints)
```bash
# Test all endpoints
pytest tests/api/test_clinical_screening_api.py -v

# Test specific endpoint
pytest tests/api/test_clinical_screening_api.py::TestPHQ9Endpoint -v

# Test consent flow
pytest tests/api/test_clinical_screening_api.py::TestConsentFlow -v
```

### **Layer 3: Integration Tests** (Full Flow)
```bash
# Test complete user journeys
pytest tests/integration/test_clinical_screening.py -v
```

---

## 🌐 **Manual Browser Testing**

1. **Start servers:**
   ```bash
   # Terminal 1
   uvicorn app.main:app --reload

   # Terminal 2
   cd frontend/ && npm run dev
   ```

2. **Open checklist:**
   - [Manual Testing Guide](MANUAL_CLINICAL_TESTING.md)

3. **Test URLs:**
   - Screening: http://localhost:5173/screening/phq9
   - Dashboard: http://localhost:5173/clinician-dashboard
   - API Docs: http://localhost:8000/docs

---

## 🔍 **Common Test Commands**

```bash
# Run all tests with coverage
pytest tests/ --cov=app --cov-report=html

# Run only failed tests from last run
pytest --lf

# Run tests in parallel (faster)
pytest -n auto

# Stop at first failure
pytest -x

# Show detailed output
pytest -vv --tb=long

# Run specific test file
pytest tests/test_clinical_scoring.py

# Run tests matching pattern
pytest -k "phq9" -v

# Generate JUnit XML report
pytest --junitxml=test-results.xml
```

---

## 📈 **Coverage Reports**

```bash
# Generate HTML coverage report
pytest tests/test_clinical_scoring.py --cov=app/services/clinical --cov-report=html

# Open in browser
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# View in terminal
pytest --cov=app/services/clinical --cov-report=term-missing
```

**Target Coverage:**
- Unit tests: ≥ 90%
- API tests: ≥ 80%
- Integration: ≥ 70%

---

## 🐛 **Debugging Failed Tests**

```bash
# Drop into debugger on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Run with print statements visible
pytest -s

# Run specific failing test
pytest tests/test_clinical_scoring.py::TestPHQ9Scoring::test_minimal_depression -vv --tb=short
```

---

## ✅ **Test Checklist Before Deploy**

```bash
# 1. Run all tests
./run_clinical_tests.sh

# 2. Check coverage
pytest tests/ --cov=app --cov-report=term --cov-fail-under=80

# 3. Run linting
flake8 app/services/clinical/
black --check app/services/clinical/

# 4. Security scan
bandit -r app/services/clinical/

# 5. Manual testing
# Open MANUAL_CLINICAL_TESTING.md
```

---

## 🔧 **Fixtures & Test Data**

**Test User:**
```python
@pytest.fixture
def test_user(db):
    user = User(
        email='test@example.com',
        username='testuser',
        hashed_password='hashed'
    )
    db.add(user)
    db.commit()
    return user
```

**Test Consent:**
```python
@pytest.fixture
def test_consent(test_user, db):
    consent = ClinicalConsent(
        user_id=test_user.id,
        consent_type='screening',
        screening_types=['PHQ9'],
        consented=True
    )
    db.add(consent)
    db.commit()
    return consent
```

---

## 📱 **Mobile Testing**

```bash
# Chrome DevTools
1. Open DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select device: iPhone 12 Pro
4. Reload page
5. Test all features

# Real device
1. Find local IP: ifconfig | grep inet
2. Start frontend: npm run dev -- --host
3. On mobile: http://YOUR_LOCAL_IP:5173
```

---

## 🚨 **Critical Test Paths**

**Always test these first:**

1. ✅ Crisis alert triggers (suicide ideation)
2. ✅ Reverse scoring (PSS-10 items 4,5,7,8)
3. ✅ Consent verification (no consent = 403)
4. ✅ Database record creation
5. ✅ Audit log entries (HIPAA)
6. ✅ Mobile responsiveness
7. ✅ Accessibility (keyboard nav)

**If any fail → BLOCK DEPLOYMENT**

---

## 📊 **Test Results Template**

```
╔════════════════════════════════════════════════════════════╗
║              CLINICAL SCREENING TEST RESULTS               ║
╠════════════════════════════════════════════════════════════╣
║ Date: 2025-01-15                                          ║
║ Tester: Your Name                                         ║
║ Branch: main                                              ║
╠════════════════════════════════════════════════════════════╣
║                                                          ║
║ Unit Tests:        ✅ PASS (45/45)                       ║
║ API Tests:         ✅ PASS (32/32)                       ║
║ Integration:       ✅ PASS (12/12)                       ║
║ Manual Browser:    ✅ PASS (8/8)                         ║
║                                                          ║
║ Coverage:          92.3%                                ║
║ Total Runtime:     45.2s                                ║
║                                                          ║
║ Status:            ✅ READY FOR DEPLOYMENT              ║
╚════════════════════════════════════════════════════════════╝
```

---

`★ Insight ─────────────────────────────────────`
**Test Triangle Strategy**: Notice the 3 layers—**Unit → API → Integration**. Each layer catches different bugs:
- **Unit tests** catch **logic errors** (wrong score calculation)
- **API tests** catch **integration bugs** (auth fails, database rejects)
- **Integration tests** catch **workflow issues** (user can't complete flow)

Missing any layer means **bugs escape to production**. A miscalculated PHQ-9 score could mean someone doesn't get the help they need. Layered testing is **defense in depth**.

**The "Reverse Scoring" Bug Hunt**: PSS-10 items 4, 5, 7, 8 are reverse-scored. This is the **#1 source of bugs** in stress assessments. We wrote **5 specific tests** for this alone (test_reverse_scoring, test_all_zeros_after_reverse, etc.). Why? Because one wrong score = wrong diagnosis = wrong treatment. **Test your edge cases relentlessly**.

**Coverage ≠ Quality**: 90% coverage doesn't mean tests are **good**—it means you executed 90% of code. You could have 90% coverage with all tests always passing `return True`. **Manual testing** validates that the system **actually works** for real humans. Never skip manual testing for clinical systems.
`─────────────────────────────────────────────────`
