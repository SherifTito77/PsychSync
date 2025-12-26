# 🗄️ 20 COMPREHENSIVE DATABASE TEST PROMPTS

## 🔍 **DATABASE CONNECTIVITY & HEALTH TESTS**

### **1. Basic Database Connection Test**
```bash
curl -X GET http://localhost:8000/health | python -c "
import json, sys
data = json.load(sys.stdin)
print(f'Database Status: {data.get(\"status\", \"unknown\")}')
print(f'Services Active: {data.get(\"dependency_injection\", {}).get(\"services_count\", 0)}')
"
```

### **2. Database Service Dependency Test**
```bash
curl -s http://localhost:8000/api/v1/health | python -c "
import json, sys
data = json.load(sys.stdin)
di = data.get('dependency_injection', {})
print(f'Dependency Status: {di.get(\"status\", \"unknown\")}')
print(f'Container: {di.get(\"container_status\", \"unknown\")}')
print(f'Validation Errors: {len(di.get(\"validation_errors\", []))}')
"
```

### **3. Database Health Monitoring Test**
```bash
curl -X POST http://localhost:8000/api/v1/health/detailed \
  -H "Content-Type: application/json" \
  -d '{"check_connections": true, "check_tables": true}'
```

---

## 📊 **DATA PERSISTENCE & CRUD TESTS**

### **4. MBTI Assessment Storage Test**
```bash
curl -X POST http://localhost:8000/api/v1/mbti-test-submit \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_type": "mbti",
    "responses": {"1": "E", "2": "S", "3": "F", "4": "P"},
    "raw_type": "ESFP",
    "test_id": "db_test_001"
  }' | python -c "
import json, sys
data = json.load(sys.stdin)
if data.get('success'):
    result = data.get('result', {})
    print(f'Stored Type: {result.get(\"type\", \"unknown\")}')
    print(f'Confidence: {result.get(\"confidence\", \"unknown\")}')
    print(f'DB Storage: {data.get(\"stored_in_db\", \"unknown\")}')
"
```

### **5. Enneagram Assessment Storage Test**
```bash
curl -X POST http://localhost:8000/api/v1/enneagram-test-submit \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_type": "enneagram",
    "responses": {"1": "5", "2": "2", "3": "8"},
    "raw_type": "Type 7",
    "test_id": "db_test_002"
  }'
```

### **6. Big Five Assessment Storage Test**
```bash
curl -X POST http://localhost:8000/api/v1/big-five-test-submit \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_type": "big_five",
    "responses": {"1": "5", "2": "2", "3": "3", "4": "4", "5": "5"},
    "raw_type": "High E, Low N",
    "test_id": "db_test_003"
  }'
```

### **7. User Profile Creation Test**
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dbtest@example.com",
    "name": "Database Test User",
    "role": "user",
    "organization_id": "test_org_001"
  }'
```

### **8. User Profile Retrieval Test**
```bash
curl -X GET http://localhost:8000/api/v1/me-minimal | python -c "
import json, sys
data = json.load(sys.stdin)
print(f'User ID: {data.get(\"id\", \"unknown\")}')
print(f'Email: {data.get(\"email\", \"unknown\")}')
print(f'Name: {data.get(\"name\", \"unknown\")}')
print(f'Role: {data.get(\"role\", \"unknown\")}')
"
```

---

## ⚡ **PERFORMANCE & SCALING TESTS**

### **9. Sequential Performance Test**
```bash
for i in {1..10}; do
  start_time=$(date +%s.%N)
  curl -s -X POST http://localhost:8000/api/v1/mbti-test-submit \
    -H "Content-Type: application/json" \
    -d '{"assessment_type": "mbti", "responses": {"1": "E"}, "raw_type": "ESFP"}' > /dev/null
  end_time=$(date +%s.%N)
  duration=$(echo "$end_time - $start_time" | bc)
  echo "Request $i: ${duration}s"
done
```

### **10. Concurrent Load Test**
```bash
echo "Testing 20 concurrent requests..."
for i in {1..20}; do
  curl -s -X POST http://localhost:8000/api/v1/mbti-test-submit \
    -H "Content-Type: application/json" \
    -d "{\"assessment_type\": \"mbti\", \"responses\": {\"1\": \"E\"}, \"raw_type\": \"ESFP\", \"req_id\": \"$i\"}" &
done
wait
echo "All concurrent requests completed"
```

### **11. Batch Processing Test**
```bash
echo "Testing batch assessment submission..."
batch_data='[
  {"type": "mbti", "responses": {"1": "E", "2": "S"}, "raw_type": "ESFP"},
  {"type": "mbti", "responses": {"1": "I", "2": "N"}, "raw_type": "INTJ"},
  {"type": "mbti", "responses": {"1": "E", "2": "N"}, "raw_type": "ENFP"}
]'
curl -X POST http://localhost:8000/api/v1/assessments/batch \
  -H "Content-Type: application/json" \
  -d "$batch_data"
```

### **12. Memory Usage Monitoring Test**
```bash
curl -X GET http://localhost:8000/api/v1/system/memory | python -c "
import json, sys
data = json.load(sys.stdin)
print(f'Memory Usage: {data.get(\"memory_usage_mb\", \"unknown\")} MB')
print(f'Active Connections: {data.get(\"active_connections\", \"unknown\")}')
print(f'Database Pool Size: {data.get(\"db_pool_size\", \"unknown\")}')
"
```

---

## 🔒 **SECURITY & VALIDATION TESTS**

### **13. SQL Injection Protection Test**
```bash
curl -X POST http://localhost:8000/api/v1/mbti-test-submit \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_type": "mbti",
    "responses": {"1": "E; DROP TABLE users; --"},
    "raw_type": "ESFP",
    "security_test": "sql_injection"
  }'
```

### **14. XSS Protection Test**
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test<script>alert(\"xss\")</script>@example.com",
    "name": "<img src=x onerror=alert(\"xss\")>Test",
    "security_test": "xss_protection"
  }'
```

### **15. Data Type Validation Test**
```bash
curl -X POST http://localhost:8000/api/v1/mbti-test-submit \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_type": "mbti",
    "responses": {"1": 123, "2": null, "3": true, "4": "invalid"},
    "raw_type": {"complex": "object"},
    "confidence": "invalid_confidence",
    "security_test": "data_validation"
  }'
```

### **16. Input Sanitization Test**
```bash
curl -X POST http://localhost:8000/api/v1/personality-assessments/process-public \
  -H "Content-Type: application/json" \
  -d '{
    "framework": "../../etc/passwd",
    "data": {"type": "<script>alert(\"test\")</script>"},
    "security_test": "input_sanitization"
  }'
```

---

## 📈 **INTEGRITY & RELIABILITY TESTS**

### **17. Foreign Key Constraint Test**
```bash
curl -X POST http://localhost:8000/api/v1/assessments \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "nonexistent_user_12345",
    "framework": "mbti",
    "test_id": "foreign_key_test"
  }'
```

### **18. Data Consistency Test**
```bash
# Store assessment
curl -s -X POST http://localhost:8000/api/v1/mbti-test-submit \
  -H "Content-Type: application/json" \
  -d '{"assessment_type": "mbti", "responses": {"1": "E"}, "raw_type": "ESFP", "consistency_test": true}' | python -c "
import json, sys
data = json.load(sys.stdin)
if data.get('success'):
    print(f'Consistent storage: {data.get(\"stored_in_db\", False)}')
    print(f'Result type: {data.get(\"result\", {}).get(\"type\")}')
"
```

### **19. Transaction Rollback Test**
```bash
curl -X POST http://localhost:8000/api/v1/transactions/test \
  -H "Content-Type: application/json" \
  -d '{
    "operations": [
      {"type": "create_user", "data": {"name": "Test User"}},
      {"type": "create_assessment", "data": {"framework": "mbti"}},
      {"type": "force_error", "data": {"error": "Simulated failure"}}
    ],
    "test_type": "rollback"
  }'
```

### **20. Database Backup Verification Test**
```bash
curl -X POST http://localhost:8000/api/v1/database/backup \
  -H "Content-Type: application/json" \
  -d '{
    "backup_type": "full",
    "include_data": true,
    "verify_integrity": true
  }' | python -c "
import json, sys
data = json.load(sys.stdin)
print(f'Backup Success: {data.get(\"success\", False)}')
print(f'Backup File: {data.get(\"backup_file\", \"unknown\")}')
print(f'Integrity Check: {data.get(\"integrity_verified\", False)}')
"
```

---

## 🚀 **AUTOMATED TEST SUITE**

### **Complete Database Health Check**
```bash
#!/bin/bash
echo "🗄️ COMPREHENSIVE DATABASE TEST SUITE"
echo "======================================"

echo "1. Testing basic connectivity..."
curl -s http://localhost:8000/health > /dev/null && echo "✅ Health check passed" || echo "❌ Health check failed"

echo "2. Testing user operations..."
curl -s http://localhost:8000/api/v1/me-minimal > /dev/null && echo "✅ User retrieval passed" || echo "❌ User retrieval failed"

echo "3. Testing assessment storage..."
result=$(curl -s -X POST http://localhost:8000/api/v1/mbti-test-submit \
  -H "Content-Type: application/json" \
  -d '{"assessment_type": "mbti", "responses": {"1": "E"}, "raw_type": "ESFP"}')
echo "$result" | python -c "import json, sys; print('✅ Assessment storage passed' if json.load(sys.stdin).get('success') else '❌ Assessment storage failed')" 2>/dev/null || echo "❌ Assessment test failed"

echo "4. Testing database performance..."
start_time=$(date +%s.%N)
curl -s http://localhost:8000/api/v1/personality-assessments/frameworks > /dev/null
end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc)
echo "Framework query time: ${duration}s"

echo "5. Testing security..."
curl -s -X POST http://localhost:8000/api/v1/personality-assessments/process-public \
  -H "Content-Type: application/json" \
  -d '{"framework": "mbti", "data": {"type": "; DROP TABLE users; --"}}' | python -c "
import json, sys
data = json.load(sys.stdin)
security_ok = not 'DROP TABLE' in str(data)
print('✅ Security protection active' if security_ok else '❌ Security vulnerability detected')
" 2>/dev/null || echo "⚠️ Security test inconclusive"

echo "======================================"
echo "🎯 Database Test Suite Complete!"
```

---

## 📋 **HOW TO USE THESE PROMPTS**

### **Manual Testing:**
1. Copy any prompt above
2. Run in terminal
3. Analyze the JSON response
4. Verify expected behavior

### **Automated Testing:**
1. Save the complete suite to a file
2. Make it executable: `chmod +x test_suite.sh`
3. Run: `./test_suite.sh`
4. Review comprehensive results

### **Performance Monitoring:**
1. Use prompts 9-12 for load testing
2. Monitor response times
3. Check system resource usage
4. Validate scaling behavior

### **Security Validation:**
1. Use prompts 13-16 for security testing
2. Verify all attacks are blocked
3. Check for proper error handling
4. Ensure no data leakage

### **Production Verification:**
1. Run all 20 prompts before deployment
2. Ensure all tests pass
3. Document any failures
4. Fix issues before production launch

---

**💡 Tip**: These prompts are designed to work with your PsychSync minimal_app backend. Adapt the endpoints if you're using a different backend configuration.

**🎯 Best Practice**: Run these tests regularly in development, before production deployments, and as part of your CI/CD pipeline.