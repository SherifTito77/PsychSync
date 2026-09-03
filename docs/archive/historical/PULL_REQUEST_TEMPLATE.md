## Pull Request Checklist

### 🎯 **Code Quality Requirements**

Before submitting this PR, ensure all of the following are addressed:

#### **Complexity Standards**
- [ ] No function exceeds **15 cyclomatic complexity**
- [ ] No function exceeds **50 lines** (excluding comments/blank lines)
- [ ] No nesting deeper than **3 levels**
- [ ] All functions have **single, clear responsibility**

#### **Testing Requirements**
- [ ] Test coverage **≥ 80%** for modified code
- [ ] All new features have **unit tests**
- [ ] Integration tests for API changes
- [ ] All tests pass locally: `pytest tests/ -v`

#### **Documentation Requirements**
- [ ] All public functions have **docstrings**
- [ ] Complex logic includes **inline comments**
- [ ] README/CHANGELOG updated if user-facing

---

## 🔍 **Complexity Review Section**

### **For Each Modified Function**

#### 1. **Function: `<function_name>`** (`<file>:<line>`)
- **Current Complexity**: `___` (run `radon cc <file> -nb`)
- **Lines of Code**: `___`
- **Nesting Level**: `___`
- **Responsibilities**:
  - [ ] Single responsibility
  - [ ] Multiple responsibilities (needs refactoring)

**If complexity > 10, explain why:**
```
<explain why the complexity is necessary or how to refactor>
```

---

## 📋 **PR Description**

### **Summary**
<!-- Brief description of changes -->

### **Type of Change**
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Refactoring
- [ ] Documentation
- [ ] Tests

### **Breaking Changes**
- [ ] Yes (describe below)
- [ ] No

**If yes, describe impact and migration path:**

---

## 🧪 **Testing**

### **Test Coverage**
```bash
# Run coverage report
pytest tests/ --cov=<modified_modules> --cov-report=term-missing

# Paste output here:
```

### **Manual Testing**
- [ ] Tested locally
- [ ] Tested in staging environment

**Test scenarios covered:**
-

---

## 📊 **Performance Impact**

- [ ] No performance impact
- [ ] Performance improved
- [ ] Performance degraded (explain below)

**If degraded, explain:**

---

## 🔗 **Related Issues**

Closes: #<issue_number>
Related to: #<issue_number>

---

## 📸 **Screenshots (if applicable)**


---

## ✅ **Pre-merge Checklist**

- [ ] All checks pass (CI/CD)
- [ ] At least one approval from code reviewer
- [ ] No merge conflicts
- [ ] Documentation updated
- [ ] Changelog updated (if user-facing)
- [ ] Complexity requirements met
- [ ] Test coverage requirements met

---

## 📝 **Reviewer Notes**

<!-- Any specific areas you'd like reviewers to focus on -->

**Key Changes:**
-

**Potential Concerns:**
-

**Testing Strategy:**
-
