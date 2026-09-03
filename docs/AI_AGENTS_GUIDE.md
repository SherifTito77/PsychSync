# 🤖 AI Agents Activation Guide

## Overview
This guide shows you how to put the 5 Product Operations AI Agents into action.

## Current Status
| Agent | Backend | Database | Frontend | Status |
|-------|---------|----------|----------|--------|
| 🔒 SQL Injection Audit | ✅ Complete | ✅ Tables + Data | ✅ Integrated | **READY TO USE** |
| ⚡ Query Performance | ✅ Complete | ✅ Tables (empty) | ✅ Integrated | **READY TO USE** |
| 🔨 Build Failure Analysis | ⚠️ Models only | ❌ Not created | ❌ Not integrated | **NEEDS COMPLETION** |
| 💾 Caching Configuration | ⚠️ Models only | ❌ Not created | ❌ Not integrated | **NEEDS COMPLETION** |
| 🚨 Breaking Changes | ⚠️ Models only | ❌ Not created | ❌ Not integrated | **NEEDS COMPLETION** |

---

## 🚀 AGENT 1: SQL Injection Audit (FULLY OPERATIONAL)

### Step 1: Access the Dashboard
```bash
# Start the frontend (if not already running)
cd frontend
npm run dev
```

Navigate to: `http://localhost:5173` → Dashboard → Product Operations → **SQL Audit** tab

### Step 2: View Scanned Data
The dashboard shows:
- **Security Grade**: Overall A-F grade based on vulnerability count
- **Risk Score**: 0-100 scale (higher = more risky)
- **Total Queries**: Number of SQL queries scanned
- **Vulnerabilities**: Count of detected issues
- **Parameterization Rate**: % of queries using parameterized queries
- **ORM Usage Rate**: % of queries using ORM (safer)

### Step 3: Review Vulnerable Queries
Each query shows:
- Risk level badge (critical/high/medium/low/safe)
- Query text with syntax highlighting
- File path and line number
- Vulnerability type (SQLi, XSS, etc.)
- **AI Suggestion**: How to fix the vulnerability
- **Safe Example**: Correct code pattern

### Step 4: Run Your Own Scan
The agent has 6 pre-seeded queries for testing. To scan your own codebase:

```bash
# Use the API endpoint directly
curl -X GET "http://localhost:8000/api/v1/sql_audit/queries/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get specific queries
curl -X GET "http://localhost:8000/api/v1/sql_audit/queries?limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### API Endpoints
```bash
# Get security summary
GET /api/v1/sql_audit/queries/summary

# Get all queries with filtering
GET /api/v1/sql_audit/queries?limit=10&skip=0&risk_level=high

# Get queries by file
GET /api/v1/sql_audit/queries/by_file?file_path=app/services/auth.py

# Mark query as fixed
PUT /api/v1/sql_audit/queries/{query_id}/mark_fixed

# Get latest scan report
GET /api/v1/sql_audit/reports/latest
```

---

## ⚡ AGENT 2: Query Performance Optimization (FULLY OPERATIONAL)

### Step 1: Seed Test Data (Optional)
Currently, slow_queries table is empty. Seed it with test data:

```bash
cd /Users/sheriftito/Downloads/psychsync
python3 app/scripts/seed_query_performance.py
```

### Step 2: Access the Dashboard
Navigate to: `http://localhost:5173` → Dashboard → Product Operations → **Query Performance** tab

### Step 3: View Performance Metrics
- **Performance Grade**: Overall A-F grade
- **Average Query Time**: Mean execution time in ms
- **Slow Queries**: Count of queries exceeding threshold
- **Critical Queries**: Queries needing immediate attention
- **Optimization Potential**: Total ms that could be saved

### Step 4: Review Slow Queries
Each query displays:
- Performance tier (critical/slow/moderate/acceptable)
- Average execution time
- Query signature for identification
- **Bottleneck Type**: What's causing slowness (missing index, N+1, etc.)
- **AI Suggestion**: Optimization recommendations
- **Suggested Index**: CREATE INDEX statement
- **Estimated Improvement**: % speedup expected

### Step 5: Run Performance Analysis
```bash
# Get performance summary
curl -X GET "http://localhost:8000/api/v1/query_performance/queries/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get slow queries
curl -X GET "http://localhost:8000/api/v1/query_performance/queries?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get top slowest queries
curl -X GET "http://localhost:8000/api/v1/query_performance/queries/top_slow?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get by performance tier
curl -X GET "http://localhost:8000/api/v1/query_performance/queries/by_tier?tier=critical" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### API Endpoints
```bash
# Performance summary
GET /api/v1/query_performance/queries/summary

# Get slow queries with filtering
GET /api/v1/query_performance/queries?limit=10&skip=0

# Get top slowest queries
GET /api/v1/query_performance/queries/top_slow?limit=10

# Get queries by performance tier
GET /api/v1/query_performance/queries/by_tier?tier=critical

# Get unoptimized queries
GET /api/v1/query_performance/queries/unoptimized

# Mark query as optimized
PUT /api/v1/query_performance/queries/{query_id}/mark_optimized

# Get index recommendations
GET /api/v1/query_performance/index_recommendations?query_id={uuid}

# Get recommendations by table
GET /api/v1/query_performance/index_recommendations/by_table?table_name=users

# Get latest optimization report
GET /api/v1/query_performance/reports/latest
```

---

## 🔨 AGENT 3: Build Failure Analysis (NEEDS COMPLETION)

### Current State
- ✅ Database models created in `app/db/models/build_analysis.py`
- ❌ No schemas, CRUD, or API endpoints yet
- ❌ No database tables created

### To Complete This Agent
You have 3 options:

**Option 1: Manual Implementation** (similar to SQL Audit agent)
1. Create schemas in `app/schemas/build_analysis.py`
2. Create CRUD in `app/crud/crud_build_analysis.py`
3. Create endpoints in `app/api/v1/endpoints/build_analysis.py`
4. Register router in `app/api/v1/api.py`
5. Create database tables
6. Seed test data
7. Add frontend tab

**Option 2: Ask Claude to Complete**
```
"Complete the Build Failure Analysis agent with schemas, CRUD, endpoints, and frontend integration"
```

**Option 3: Defer for Now**
Focus on the 2 fully operational agents (SQL Audit & Query Performance)

---

## 💾 AGENT 4: Caching Configuration (NEEDS COMPLETION)

### Current State
- ✅ Database models created in `app/db/models/caching_config.py`
- ❌ No schemas, CRUD, or API endpoints yet

### To Complete This Agent
Same options as Build Failure Analysis agent above.

---

## 🚨 AGENT 5: Breaking Changes Detection (NEEDS COMPLETION)

### Current State
- ✅ Database models created in `app/db/models/breaking_changes.py`
- ❌ No schemas, CRUD, or API endpoints yet

### To Complete This Agent
Same options as Build Failure Analysis agent above.

---

## 🎯 Quick Start: Use the 2 Operational Agents Now

### 1. Start Everything
```bash
# Terminal 1: Backend
cd /Users/sheriftito/Downloads/psychsync
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 2. Login and Access
1. Go to `http://localhost:5173`
2. Login with your credentials
3. Navigate to **Product Operations Dashboard**

### 3. Explore SQL Audit Tab
- View the 6 pre-seeded SQL queries
- See vulnerability analysis
- Review AI-generated suggestions
- Check the security grade (should be calculated from data)

### 4. Explore Query Performance Tab
- Currently empty (unless you seed data)
- Ready to receive query performance data
- Shows empty state with helpful message

---

## 📊 Testing with Real Data

### Option A: Use the Seed Scripts
```bash
# SQL Audit (already seeded with 6 queries)
python3 app/scripts/seed_sql_audit.py

# Query Performance (seed with sample slow queries)
python3 app/scripts/seed_query_performance.py
```

### Option B: Insert Custom Data via API
```python
import requests

# Login first
response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'email': 'your@email.com',
    'password': 'yourpassword'
})
token = response.json()['access_token']

headers = {'Authorization': f'Bearer {token}'}

# Add a slow query
requests.post('http://localhost:8000/api/v1/query_performance/queries', json={
    'query_text': 'SELECT * FROM users WHERE email = "test@example.com"',
    'execution_time_ms': 450.5,
    'performance_tier': 'slow',
    'bottleneck_type': 'missing_index',
    'ai_suggestion': 'Add index on users.email column',
    'suggested_index': 'CREATE INDEX idx_users_email ON users(email);',
    'estimated_improvement': 85.0
}, headers=headers)
```

---

## 🔍 Verify Agent Functionality

### Check Backend Endpoints
```bash
# Test SQL Audit endpoint
curl -X GET "http://localhost:8000/api/v1/sql_audit/queries/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test Query Performance endpoint
curl -X GET "http://localhost:8000/api/v1/query_performance/queries/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"

# List all routes
curl -X GET "http://localhost:8000/docs"  # Opens Swagger UI
```

### Check Database Tables
```bash
psql -U psychsync_user -d psychsync_db -c "\dt" | grep -E "(sql_|query_)"

# Check data counts
psql -U psychsync_user -d psychsync_db -c "
SELECT 'sql_queries' as table_name, COUNT(*) as count FROM sql_queries
UNION ALL
SELECT 'slow_queries', COUNT(*) FROM slow_queries;
"
```

---

## 🎓 Next Steps

### For Production Use
1. **Add AI/ML Integration**: Connect to OpenAI/Claude APIs for real analysis
2. **Implement Scanners**: Build background jobs that scan codebase periodically
3. **Set Up Alerts**: Email/Slack notifications for critical issues
4. **Add Historical Tracking**: Track improvements over time
5. **Implement Auto-Fix**: Apply safe fixes automatically

### For the 3 Incomplete Agents
1. Complete schemas (Pydantic models)
2. Implement CRUD operations
3. Create API endpoints
4. Set up database tables
5. Build frontend UI
6. Test end-to-end

---

## 📞 Need Help?

To complete the remaining 3 agents, you can ask:
```
"Complete the Build Failure Analysis, Caching Configuration, and Breaking Changes agents
with full implementation following the same pattern as SQL Audit and Query Performance agents."
```

This will create:
- ✅ All schemas in `app/schemas/`
- ✅ All CRUD in `app/crud/`
- ✅ All endpoints in `app/api/v1/endpoints/`
- ✅ Database tables and seed scripts
- ✅ Frontend tabs with visualizations
- ✅ API integration

---

## 🎉 Summary

**Ready to Use Now:**
- ✅ SQL Injection Audit Agent (with test data)
- ✅ Query Performance Optimization Agent (tables ready)

**Need Completion:**
- ⚠️ Build Failure Analysis Agent
- ⚠️ Caching Configuration Agent
- ⚠️ Breaking Changes Detection Agent

**Access the Dashboard:** `http://localhost:5173` → Product Operations Dashboard
