# 📱 Postman Authentication API Testing Guide

**Created:** December 2, 2025
**Version:** 1.0
**Coverage:** Complete PsychSync Authentication Endpoints

---

## 🚀 Quick Start

### 1. Import Collection
1. Open Postman
2. Click **Import** → **Link**
3. Paste the raw JSON from `postman_auth_collection.json`
4. Select the collection and environment
5. Click **Import**

### 2. Setup Environment
1. Select **PsychSync Authentication - Development** environment
2. Update `baseUrl` variable to match your API endpoint:
   - Development: `http://localhost:8000`
   - Staging: `https://api.psychsync.dev`
   - Production: `https://api.psychsync.com`

### 3. Run Tests
- Click the **PsychSync Authentication API** collection
- Click **Run** → **Run entire collection**
- Select the environment
- Click **Run Authentication Endpoints**

---

## 📋 Test Suite Overview

### **Collection Structure**

```
📱 PsychSync Authentication API
├── 🔐 Authentication Endpoints
│   ├── 👤 User Registration
│   │   ├── ✅ Register New User (Success)
│   │   ├── ❌ Register User - Invalid Email
│   │   ├── ⚠️ Register User - Weak Password
│   │   └── 🔄 Register Duplicate User
│   ├── 🔑 User Login
│   │   ├── ✅ Login with Valid Credentials
│   │   ├── ❌ Login with Invalid Credentials
│   │   └── ⚠️ Login - Missing Credentials
│   ├── 🔄 Token Management
│   │   ├── ✅ Get Current User Profile
│   │   ├── 🔄 Refresh Access Token
│   │   ├── ✅ Logout User
│   │   └── ❌ Refresh with Invalid Token
│   ├── 🛡️ Security Features
│   │   ├── ℹ️ Get Password Requirements
│   │   ├── 🔍 Get Security Alerts
│   │   ├── 📊 Get Security Status
│   │   ├── 📱 Get User Sessions
│   │   ├── 🚪 Logout All Devices
│   │   └── ⚠️ Get Risk Assessment
│   └── 🧪 Test Endpoints
│       ├── 🧪 Minimal Token Endpoint
│       ├── 🧪 Minimal User Profile
│       ├── 🧪 Simple Token Endpoint
│       └── 🧪 Test POST Endpoint
├── 🔒 Authorization Tests
│   ├── 🚫 Access Protected Resource Without Token
│   ├── 🚫 Access Protected Resource with Invalid Token
│   └── 🚫 Access Protected Resource with Expired Token
└── 🧪 Edge Cases & Error Handling
    ├── 🛡️ XSS Prevention Test
    ├── 🛡️ SQL Injection Prevention Test
    ├── ⚡ Rate Limiting Test
    ├── 📦 Large Payload Test
    └── 📝 Malformed JSON Test
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example Value |
|----------|-------------|-------------|
| `baseUrl` | API base URL | `http://localhost:8000` |
| `testUserEmail` | Registered test user email | `testuser123@example.com` |
| `testUserId` | Test user ID | `550e8400-e29b-41d4-a716...` |
| `accessToken` | JWT access token | `eyJhbGciOiJIUzI1NiIs...` |
| `refreshToken` | JWT refresh token | `eyJhbGciOiJIUzI1NiIs...` |
| `testToken` | Test token for minimal endpoints | `test_token_12345` |
| `currentUser` | Current user data (JSON) | `{"id": "...", "email": "..."}` |

### Global Scripts

#### **Pre-request Script:**
```javascript
// Generate unique test email
if (!pm.collectionVariables.get('randomEmail')) {
    pm.collectionVariables.set('randomEmail', 'testuser' + Date.now() + '@example.com');
}

// Debug logging
console.log('Environment:', pm.environment.name);
console.log('Base URL:', pm.collectionVariables.get('baseUrl'));
console.log('Has Access Token:', !!pm.collectionVariables.get('accessToken'));
```

#### **Tests Script:**
```javascript
// Performance monitoring
console.log('Request:', pm.info.requestName);
console.log('Status:', pm.response.code);
console.log('Response Time:', pm.response.responseTime + 'ms');

// Store response times
const times = pm.collectionVariables.get('responseTimes') || [];
times.push({
    request: pm.info.requestName,
    status: pm.response.code,
    time: pm.response.responseTime,
    timestamp: new Date().toISOString()
});
pm.collectionVariables.set('responseTimes', times);
```

---

## 🧪 Test Categories

### **1. User Registration Tests**

#### **✅ Register New User (Success)**
- **Purpose:** Test successful user registration
- **Expected Status:** 201 Created
- **Validation:**
  - Valid email format
  - Strong password requirements
  - User properties are correctly set
  - Email is stored in collection variables

#### **❌ Register User - Invalid Email**
- **Purpose:** Test email validation
- **Expected Status:** 422 Unprocessable Entity
- **Test Data:** `"invalid-email"`

#### **⚠️ Register User - Weak Password**
- **Purpose:** Test password strength validation
- **Expected Status:** 400 Bad Request
- **Test Data:** `"123"` (too short, no complexity)

#### **🔄 Register Duplicate User**
- **Purpose:** Test duplicate email prevention
- **Expected Status:** 409 Conflict
- **Test Data:** `admin@example.com`

---

### **2. User Login Tests**

#### **✅ Login with Valid Credentials**
- **Purpose:** Test successful authentication
- **Expected Status:** 200 OK
- **Response Validation:**
  - JWT tokens (access + refresh)
  - User profile data
  - Token format validation
  - Store tokens for subsequent tests

#### **❌ Login with Invalid Credentials**
- **Purpose:** Test authentication failure
- **Expected Status:** 401 Unauthorized
- **Test Data:** Wrong password

#### **⚠️ Login - Missing Credentials**
- **Purpose:** Test required field validation
- **Expected Status:** 422 Unprocessable Entity
- **Test Data:** Empty form data

---

### **3. Token Management Tests**

#### **✅ Get Current User Profile**
- **Purpose:** Test JWT token validation
- **Expected Status:** 200 OK
- **Authentication:** Requires valid `accessToken`

#### **🔄 Refresh Access Token**
- **Purpose:** Test token refresh mechanism
- **Expected Status:** 200 OK
- **Authentication:** Uses `refreshToken`
- **Side Effect:** Updates `accessToken` in collection

#### **✅ Logout User**
- **Purpose:** Test logout functionality
- **Expected Status:** 200 OK
- **Authentication:** Requires both tokens
- **Side Effect:** Clears stored tokens

#### **❌ Refresh with Invalid Token**
- **Purpose:** Test refresh token validation
- **Expected Status:** 400 Bad Request
- **Test Data:** Invalid refresh token

---

### **4. Security Features Tests**

#### **ℹ️ Get Password Requirements**
- **Purpose:** Test password requirements endpoint
- **Expected Status:** 200 OK
- **Validation:** All requirements are present and valid

#### **🔍 Get Security Alerts**
- **Purpose:** Test security alerts retrieval
- **Expected Status:** 200 OK
- **Authentication:** Required
- **Response:** Array of security alerts

#### **📊 Get Security Status**
- **Purpose:** Test user security status
- **Expected Status:** 200 OK
- **Authentication:** Required
- **Response:** Security score, failed attempts, lockout status

#### **📱 Get User Sessions**
- **Purpose:** Test session management
- **Expected Status:** 200 OK
- **Authentication:** Required
- **Response:** Active sessions list

#### **🚪 Logout All Devices**
- **Purpose:** Test global logout
- **Expected Status:** 200 OK
- **Authentication:** Required
- **Side Effect:** Invalidates all user sessions

#### **⚠️ Get Risk Assessment**
- **Purpose:** Test risk assessment
- **Expected Status:** 200 OK
- **Authentication:** Required
- **Response:** Risk level and factors

---

### **5. Test Endpoints**

#### **🧪 Minimal Token Endpoint**
- **Purpose:** Quick test token generation
- **Expected Status:** 200 OK
- **Response:** Hardcoded test token

#### **🧪 Minimal User Profile**
- **Purpose:** Test user endpoint with minimal auth
- **Expected Status:** 200 OK
- **Authentication:** Uses test token
- **Response:** Mock user data

#### **🧪 Simple Token Endpoint**
- **Purpose:** Test JSON-based login
- **Expected Status:** 200 OK
- **Method:** JSON request body
- **Response:** Simple JWT response

#### **🧪 Test POST Endpoint**
- **Purpose:** Basic POST request test
- **Expected Status:** 200 OK
- **Response:** Success message

---

### **6. Authorization Tests**

#### **🚫 Access Without Token**
- **Purpose:** Test authentication requirement
- **Expected Status:** 401 Unauthorized

#### **🚫 Access with Invalid Token**
- **Purpose:** Test token validation
- **Expected Status:** 401 Unauthorized

#### **🚫 Access with Expired Token**
- **Purpose:** Test token expiration
- **Expected Status:** 401 Unauthorized

---

### **7. Edge Cases & Error Handling**

#### **🛡️ XSS Prevention Test**
- **Purpose:** Test XSS protection
- **Expected Status:** 422 Unprocessable Entity
- **Test Data:** Script tags in input fields

#### **🛡️ SQL Injection Prevention Test**
- **Purpose:** Test SQL injection protection
- **Expected Status:** 401 Unauthorized
- **Test Data:** SQL injection payload

#### **⚡ Rate Limiting Test**
- **Purpose:** Test rate limiting (run multiple times)
- **Expected Status:** 401 → 429 Too Many Requests
- **Instructions:** Run rapidly to trigger rate limiting

#### **📦 Large Payload Test**
- **Purpose:** Test large payload handling
- **Expected Status:** 200/400/413/422
- **Test Data:** Very long name field

#### **📝 Malformed JSON Test**
- **Purpose:** Test JSON parsing error handling
- **Expected Status:** 400/422
- **Test Data:** Invalid JSON syntax

---

## 🚨 Common Issues & Solutions

### **Issue: Connection Refused**
**Error:** `ConnectionError: [Errno 61] Connection refused`
**Solution:**
- Ensure API server is running on correct port
- Check `baseUrl` environment variable
- Verify firewall settings

### **Issue: Invalid Credentials**
**Error:** 401 Unauthorized
**Solution:**
- Use existing user credentials: `admin@example.com` / `Admin@12345`
- Check for trailing spaces in credentials
- Verify user is active in database

### **Issue: Token Expired**
**Error:** 401 Unauthorized with "Could not validate credentials"
**Solution:**
- Run login test to refresh tokens
- Check token expiration time
- Use refresh token endpoint

### **Issue: Rate Limited**
**Error:** 429 Too Many Requests
**Solution:**
- Wait before retrying
- Check rate limiting settings
- Use different test user

---

## 🤖 Automated Testing

### **Using the Python Test Runner**

```bash
# Install dependencies
pip install requests

# Run all tests
python postman_test_runner.py

# Custom configuration
python postman_test_runner.py --url=https://api.psychsync.dev --report=json --output=test_results.json

# Quick test
python postman_test_runner.py --suite=Authentication
```

### **Continuous Integration**

```yaml
# GitHub Actions example
- name: Run Auth Tests
  run: |
    python postman_test_runner.py --report=json --output auth_test_results.json
  # Upload test results as artifacts
```

### **Test Performance Monitoring**

The collection includes automatic performance monitoring:

```javascript
// Access response times
const responseTimes = pm.collectionVariables.get('responseTimes');
console.log('Average response time:', responseTimes.reduce((a, b) => a + b.time, 0) / responseTimes.length);
```

---

## 📊 Test Metrics & KPIs

### **Success Criteria**
- ✅ All happy path tests pass
- ✅ Security validations work
- ✅ Error handling is robust
- ✅ Performance under 2s average
- ✅ Rate limiting effective

### **Performance Benchmarks**
- 🟢 **Excellent:** < 500ms average response time
- 🟡 **Good:** 500ms - 1s average response time
- 🔴 **Poor:** > 1s average response time

### **Security Validation**
- ✅ XSS prevention: All inputs sanitized
- ✅ SQL injection: No successful injections
- ✅ Authentication: Proper token validation
- ✅ Authorization: Resource protection working
- ✅ Rate limiting: Abuse prevention active

---

## 🔄 Test Execution Order

### **Recommended Test Sequence**

1. **Setup Tests**
   - Get password requirements
   - Test POST endpoint

2. **Authentication Flow**
   - Register new user
   - Login with valid credentials
   - Get user profile
   - Refresh token
   - Logout user

3. **Security Tests**
   - Login attempts (fail cases)
   - Authorization tests
   - XSS/SQL injection tests

4. **Session Management**
   - Get user sessions
   - Security status
   - Logout all devices

5. **Edge Cases**
   - Large payloads
   - Malformed data
   - Rate limiting

---

## 📝 Customization

### **Adding New Tests**

1. Create new request in Postman
2. Add to appropriate folder
3. Write test assertions in Tests tab
4. Update documentation

### **Modifying Existing Tests**

1. Edit request in Postman
2. Update test assertions
3. Test with runner
4. Update documentation

### **Environment-Specific Config**

```json
// Environment variables for different stages
{
  "development": { "baseUrl": "http://localhost:8000" },
  "staging": { "baseUrl": "https://api.psychsync.dev" },
  "production": { "baseUrl": "https://api.psychsync.com" }
}
```

---

## 📚 Additional Resources

### **API Documentation**
- [PsychSync API Documentation](API.md)
- [Authentication Security Features](SECURITY_FEATURES_GUIDE.md)
- [Database Schema](docs/database_schema.md)

### **Testing Best Practices**
- [OWASP API Security Testing](https://owasp.org/www-project-api-security/)
- [Postman Best Practices](https://learning.postman.com/docs/postman/collections/)
- [REST API Testing Guide](https://restfulapi.net/testing/)

### **Security Testing**
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

---

## 🎯 Success Metrics

A successful test run should achieve:

### **Functional Requirements**
- ✅ **100%** happy path tests pass
- ✅ **100%** error scenarios handled correctly
- ✅ **100%** security validations working
- ✅ **0** security vulnerabilities

### **Performance Requirements**
- ✅ **< 500ms** average response time
- ✅ **< 2s** maximum response time
- ✅ **< 5s** timeout tolerance

### **Security Requirements**
- ✅ **Zero** XSS vulnerabilities
- ✅ **Zero** SQL injection vulnerabilities
- ✅ **100%** authentication enforcement
- ✅ **100%** authorization enforcement

---

**🎉 Your Postman Authentication Test Suite is now ready!**

This comprehensive collection covers all authentication endpoints, security validations, edge cases, and error handling scenarios. Use it to ensure your PsychSync authentication system is robust, secure, and performing well.

**Happy Testing!** 🚀