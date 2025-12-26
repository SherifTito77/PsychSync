# 🚀 JWT Token Testing Quick Start Guide

**Get your JWT token tests running in 2 minutes!**

---

## ⚡ Quick Start

### 1. Health Check
```bash
# Make sure your API is running
curl http://localhost:8000/api/v1/health

# Should return: {"status": "healthy"}
```

### 2. Run Comprehensive JWT Tests
```bash
# Full comprehensive test suite (recommended)
python comprehensive_jwt_tests.py --full

# Quick test for basic validation
python comprehensive_jwt_tests.py --quick

# Security-focused testing
python comprehensive_jwt_tests.py --security-focus
```

### 3. Run Specialized JWT Tests
```bash
# Test only expiration behavior
python jwt_token_test_suite.py --expiration

# Test refresh token functionality
python jwt_token_test_suite.py --refresh

# Test security scenarios
python jwt_token_test_suite.py --security

# Test concurrent usage
python jwt_token_test_suite.py --concurrent
```

### 4. Run Postman Collection Tests
```bash
# Postman collection for JWT testing
python postman_test_runner.py \
    --collection postman_jwt_token_collection.json \
    --suite "JWT Token Tests" \
    --report console
```

---

## 📋 Test Files Overview

| File | Purpose | When to Use |
|------|---------|-------------|
| `comprehensive_jwt_tests.py` | **Complete automated test suite** | Full validation, CI/CD, security audits |
| `jwt_token_test_suite.py` | Specialized JWT testing | Deep dive into specific JWT behaviors |
| `postman_jwt_token_collection.json` | Postman API tests | Manual testing, API exploration |
| `JWT_TOKEN_TESTING_GUIDE.md` | Complete documentation | Understanding all test scenarios |

---

## 🎯 Common Test Scenarios

### **Scenario 1: Basic JWT Validation**
```bash
# Quick validation that JWT system is working
python comprehensive_jwt_tests.py --quick
```

### **Scenario 2: Security Audit**
```bash
# Comprehensive security assessment
python comprehensive_jwt_tests.py --security-focus --output security_audit.json
```

### **Scenario 3: Performance Testing**
```bash
# Test JWT performance under load
python jwt_token_test_suite.py --concurrent --output performance_report.json
```

### **Scenario 4: Token Expiration Testing**
```bash
# Test expiration and refresh behavior
python jwt_token_test_suite.py --expiration --refresh
```

---

## 📊 Understanding Results

### **Success Indicators**
- ✅ **Security Score > 80**: JWT implementation is secure
- ✅ **Performance Score > 70**: Token operations are fast
- ✅ **All critical tests pass**: Basic functionality works
- ✅ **No critical security issues**: System is safe

### **Warning Signs**
- ⚠️ **Security Score < 80**: Review JWT security implementation
- ⚠️ **Failed refresh token tests**: Fix refresh mechanism
- ⚠️ **Slow response times**: Optimize token validation
- ⚠️ **Token leakage in responses**: Review error handling

### **Critical Issues**
- ❌ **Invalid tokens accepted**: Major security vulnerability
- ❌ **No token blacklisting**: Session hijacking risk
- ❌ **Refresh token reuse**: Authentication bypass possible
- ❌ **Expired tokens working**: Time-based security broken

---

## 🛠️ Test Configuration

### **Environment Variables**
```bash
# API Configuration
export JWT_TEST_BASE_URL="http://localhost:8000"
export JWT_TEST_USER="admin@example.com"
export JWT_TEST_PASSWORD="Admin@12345"

# Performance Thresholds (in comprehensive_jwt_tests.py)
MAX_RESPONSE_TIME=1000  # ms
MAX_TOKEN_GEN_TIME=500   # ms
MAX_VALIDATION_TIME=100 # ms
```

### **Test User Setup**
```bash
# Create test user if not exists
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin@12345",
    "full_name": "Test Admin User"
  }'
```

---

## 📈 Interpreting Test Reports

### **Comprehensive Report Structure**
```json
{
  "summary": {
    "total_tests": 7,
    "passed_tests": 6,
    "failed_tests": 1,
    "security_score": 85.5,
    "performance_score": 92.1
  },
  "security_assessment": {
    "critical_issues": [],
    "security_findings": [
      "Token reuse prevention could be stronger"
    ],
    "risk_level": "LOW"
  },
  "recommendations": [
    "Consider implementing stricter token reuse prevention"
  ]
}
```

### **Performance Metrics**
- **Average Response Time**: Token validation speed
- **95th Percentile**: Worst-case performance
- **Concurrent Handling**: System behavior under load

### **Security Scores**
- **90-100**: Excellent security implementation
- **80-89**: Good security with minor improvements
- **70-79**: Acceptable with improvements needed
- **< 70**: Requires immediate attention

---

## 🔧 Troubleshooting

### **Common Issues**

#### **Authentication Failures**
```bash
# Check test user credentials
python -c "
import requests
response = requests.post('http://localhost:8000/api/v1/auth/login', data={
    'username': 'admin@example.com',
    'password': 'Admin@12345'
})
print(response.status_code)
print(response.text)
"
```

#### **API Server Not Running**
```bash
# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or check if running
curl http://localhost:8000/api/v1/health
```

#### **Token Structure Issues**
```bash
# Decode a sample JWT token
python -c "
import jwt
import json

# Replace with actual token from your API
token = 'your.jwt.token.here'

try:
    decoded = jwt.decode(token, options={'verify_signature': False})
    print(json.dumps(decoded, indent=2))
except Exception as e:
    print(f'Error: {e}')
"
```

#### **Permission Issues**
```bash
# Make test scripts executable
chmod +x *.py

# Check Python dependencies
pip install aiohttp requests jwt
```

### **Debug Mode**
```bash
# Run tests with verbose output
python comprehensive_jwt_tests.py --full 2>&1 | tee jwt_debug.log

# Check for detailed errors
grep -i "error\|failed\|critical" jwt_debug.log
```

---

## 🚀 Production Testing

### **Pre-Production Checklist**
- [ ] All JWT tests pass with 100% success rate
- [ ] Security score >= 90
- [ ] Performance score >= 80
- [ ] No critical security issues
- [ ] Token blacklisting works
- [ ] Refresh token mechanism is secure
- [ ] No token leakage in any responses

### **Load Testing for Production**
```bash
# High-concurrency test (simulate production load)
python jwt_token_test_suite.py --concurrent --scenario=comprehensive --users=500

# Test with different token lifecycles
python comprehensive_jwt_tests.py --full --output production_jwt_validation.json
```

### **Continuous Integration**
```yaml
# GitHub Actions example
- name: JWT Token Tests
  run: |
    python comprehensive_jwt_tests.py --security-focus --output jwt_security_report.json
  # Upload security report as artifact
```

---

## 📚 Advanced Usage

### **Custom Test Configuration**
```python
# Modify test thresholds in comprehensive_jwt_tests.py
test_config = {
    "performance_thresholds": {
        "max_response_time": 500,  # Stricter for production
        "max_token_gen_time": 200,
    },
    "security_thresholds": {
        "min_security_score": 90,  # Higher security standards
    }
}
```

### **Extending Tests**
```python
# Add custom test in comprehensive_jwt_tests.py
async def test_custom_jwt_behavior(self) -> JWTTestResult:
    # Your custom test logic here
    return {
        "status": "pass",
        "response_code": 200,
        "response_time": 100,
        "security_issues": [],
        "details": {"custom_test": "passed"}
    }
```

### **API Endpoint Testing**
```bash
# Test specific JWT-protected endpoints
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/users/me

# Test refresh token directly
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}' \
  http://localhost:8000/api/v1/auth/refresh
```

---

## 🆘 Getting Help

### **Test Results Interpretation**
```bash
# Get detailed analysis
python comprehensive_jwt_tests.py --full --output detailed_analysis.json

# Focus on security issues
python comprehensive_jwt_tests.py --security-focus
```

### **Log Analysis**
```bash
# Check application logs during testing
tail -f logs/app.log | grep -i "jwt\|token\|auth"

# Monitor Redis (if used for blacklisting)
redis-cli monitor
```

### **Common Questions**

**Q: Tests are failing with "Authentication failed"**
A: Verify test user exists and credentials are correct

**Q: Security score is low**
A: Check for failed invalid token tests and missing blacklisting

**Q: Performance score is low**
A: Investigate slow token validation or high response times

**Q: Tests are running slowly**
A: Check API server performance and network latency

---

## 🎯 Quick Test Commands Reference

```bash
# === BASIC TESTING ===
python comprehensive_jwt_tests.py --quick                    # Quick validation
python comprehensive_jwt_tests.py --full                     # Complete validation

# === SECURITY TESTING ===
python comprehensive_jwt_tests.py --security-focus          # Security audit
python jwt_token_test_suite.py --security                   # Security scenarios

# === PERFORMANCE TESTING ===
python jwt_token_test_suite.py --concurrent                 # Concurrency testing
python comprehensive_jwt_tests.py --full --output report.json  # Full report

# === POSTMAN TESTING ===
python postman_test_runner.py --collection postman_jwt_token_collection.json

# === DEBUGGING ===
python comprehensive_jwt_tests.py --full 2>&1 | tee debug.log
```

---

**🎉 Your JWT Token Testing is Ready!**

This comprehensive testing suite provides deep insights into your JWT implementation, covering security, performance, and functionality. Regular testing helps ensure your authentication system remains secure and performant.

**Happy Testing!** 🚀

**Need help? Check the detailed guide: [JWT_TOKEN_TESTING_GUIDE.md](JWT_TOKEN_TESTING_GUIDE.md)**