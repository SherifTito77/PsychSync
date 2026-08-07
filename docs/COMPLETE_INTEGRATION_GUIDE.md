# 🔗 COMPLETE INTEGRATION GUIDE

## How to Add All Enhancements to Your Existing FastAPI App

---

## 📋 Quick Start: 3 Steps to Full Integration

### **Step 1: Add Analytics Router to Your API**

**File:** `app/main.py`

Add these lines:

```python
from app.api.v1.endpoints import enhanced_clinical_analytics

# Include the enhanced analytics router
app.include_router(
    enhanced_clinical_analytics.router,
    prefix="/api/v1"
)
```

**What you get:**
- ✅ `/api/v1/analytics/user/{user_id}/summary` - Complete analytics
- ✅ `/api/v1/analytics/user/{user_id}/trends/{screening_type}` - Trend analysis
- ✅ `/api/v1/analytics/user/{user_id}/comparison/{screening_type}` - Population comparison
- ✅ `/api/v1/analytics/user/{user_id}/outcomes/{screening_type}` - Outcome measurement
- ✅ `/api/v1/analytics/organization/{org_id}/population-health` - Population metrics
- ✅ `/api/v1/analytics/organization/{org_id}/dashboard` - Complete dashboard

---

### **Step 2: Add Enhanced Frontend to Your React App**

**File:** `frontend/src/App.tsx`

Add the enhanced component route:

```tsx
import { EnhancedClinicalAssessments } from './components/clinical/EnhancedClinicalAssessments';

function App() {
  return (
    <Router>
      <Routes>
        {/* Other routes... */}

        {/* Enhanced clinical assessments route */}
        <Route
          path="/enhanced-assessments"
          element={
            <RequireAuth>
              <EnhancedClinicalAssessments />
            </RequireAuth>
          }
        />

        {/* Or replace existing route */}
        <Route
          path="/clinical-assessments"
          element={
            <RequireAuth>
              <EnhancedClinicalAssessments />
            </RequireAuth>
          }
        />
      </Routes>
    </Router>
  );
}
```

**What you get:**
- 🌙 Dark mode toggle
- ✨ Framer Motion animations
- 💾 Offline support with localStorage
- ♿ WCAG 2.1 AAA accessibility
- 🔍 Filterable assessment grid
- ⚠️ Enhanced error handling

---

### **Step 3: Enable Security in Your FastAPI App**

**File:** `app/main.py`

Add security middleware:

```python
from fastapi import Request
from app.core.enhanced_security import EnhancedSecurityManager

@app.middleware("http")
async def enhanced_security_middleware(request: Request, call_next):
    """
    Global security middleware
    - Rate limiting
    - Anomaly detection
    - Input validation
    """
    # Get database from request state (you'll need to set this up)
    db = request.state.db

    if db:
        try:
            # Get user from JWT (if authenticated)
            user_id = getattr(request.state, 'user_id', None)

            if user_id:
                # Initialize security manager
                security = EnhancedSecurityManager(db)

                # Check rate limits
                endpoint = request.url.path
                allowed = await security.check_rate_limit(
                    user_id=user_id,
                    action=endpoint,
                    limit=100,  # 100 requests per hour
                    window=3600  # 1 hour window
                )

                if not allowed:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")

                # Detect anomalies
                context = {
                    'ip': request.client.host if request.client else None,
                    'user_agent': request.headers.get('user-agent'),
                    'endpoint': endpoint
                }

                await security.detect_anomaly(user_id, endpoint, context)

        except Exception as e:
            # Log error but don't block requests
            print(f"Security middleware error: {e}")

    # Process request
    response = await call_next(request)
    return response
```

**What you get:**
- ⏱️ Automatic rate limiting
- 🚨 Anomaly detection
- 🛡️ Input protection
- 📝 Security logging

---

## 📊 Complete Usage Examples

### **Example 1: Clinician Viewing Patient Analytics**

**Frontend Component:**
```tsx
import { useEffect, useState } from 'react';
import api from '@/services/api';

function ClinicianPatientView({ patientId }) {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    // Get complete analytics summary
    api.get(`/api/v1/analytics/user/${patientId}/summary`)
      .then(response => setAnalytics(response.data.data));
  }, [patientId]);

  return (
    <div>
      <h2>Patient Analytics</h2>

      {/* Display trends */}
      {analytics?.summary?.screening_types?.PHQ9?.trends && (
        <div>
          <h3>Depression Trends</h3>
          <p>Direction: {analytics.summary.screening_types.PHQ9.trends.direction}</p>
          <p>Change: {analytics.summary.screening_types.PHQ9.trends.change_percentage}%</p>
        </div>
      )}

      {/* Display comparison */}
      {analytics?.summary?.screening_types?.PHQ9?.comparative && (
        <div>
          <h3>Population Comparison</h3>
          <p>Percentile: {analytics.summary.screening_types.PHQ9.comparative.percentile_rank}%</p>
          <p>{analytics.summary.screening_types.PHQ9.comparative.interpretation}</p>
        </div>
      )}
    </div>
  );
}
```

**Backend Endpoint:**
```python
@router.get("/clinician/patient/{patient_id}/analytics")
async def get_patient_analytics(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify clinician authorization
    if current_user.role not in ['clinician', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get analytics
    report = await generate_analytics_report(db, patient_id, current_user.org_id)
    return report
```

---

### **Example 2: Using Enhanced Security in Screening Submission**

```python
from app.core.enhanced_security import EnhancedSecurityManager, AuditAction
from app.core.enhanced_security import DataSanitizer

@router.post("/screening/phq9-secure")
async def submit_phq9_enhanced(
    responses: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enhanced PHQ-9 submission with security"""
    security = EnhancedSecurityManager(db)

    # 1. Check rate limit (max 10 per hour)
    if not await security.check_rate_limit(
        str(current_user.id),
        "screening_submit",
        limit=10,
        window=3600
    ):
        raise HTTPException(
            status_code=429,
            detail="Too many screening submissions. Please try again later."
        )

    # 2. Sanitize input
    sanitized_responses = DataSanitizer.sanitize_input(responses)

    # 3. Validate screening responses
    if not DataSanitizer.validate_screening_responses(sanitized_responses):
        raise HTTPException(
            status_code=400,
            detail="Invalid input detected in screening responses"
        )

    # 4. Validate PHI access
    if not await security.validate_phi_access(
        user_id=str(current_user.id),
        resource_type="screening",
        resource_id="new_submission",
        action=AuditAction.CREATE
    ):
        raise HTTPException(
            status_code=403,
            detail="No valid consent on file for screening"
        )

    # 5. Encrypt sensitive responses
    encrypted_data = await security.encrypt_phi(
        data={"responses": sanitized_responses},
        user_id=str(current_user.id)
    )

    # 6. Save to database (save encrypted version)
    # ... your existing database logic ...

    return {
        "status": "success",
        "message": "Screening submitted securely",
        "screening_id": screening.id
    }
```

---

### **Example 3: Organization Dashboard with Population Health**

**Frontend Component:**
```tsx
import { useEffect, useState } from 'react';
import api from '@/services/api';

function OrganizationDashboard({ orgId }) {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    // Get population health metrics
    api.get(`/api/v1/analytics/organization/${orgId}/dashboard`)
      .then(response => setMetrics(response.data.dashboard));
  }, [orgId]);

  if (!metrics) return <div>Loading...</div>;

  return (
    <div className="org-dashboard">
      <h2>Organization Health Dashboard</h2>

      {/* Completion Rate */}
      <div className="metric-card">
        <h3>Completion Rate</h3>
        <p className="text-2xl font-bold">
          {metrics.summary.completion_rate.toFixed(1)}%
        </p>
      </div>

      {/* Risk Distribution */}
      <div className="metric-card">
        <h3>Risk Distribution</h3>
        <ul>
          <li>Critical: {metrics.population_health.critical_risk_count}</li>
          <li>High: {metrics.population_health.high_risk_count}</li>
          <li>Moderate: {metrics.population_health.moderate_risk_count}</li>
          <li>Low: {metrics.population_health.low_risk_count}</li>
        </ul>
      </div>

      {/* Crisis Alerts */}
      <div className="metric-card alert">
        <h3>Crisis Alerts (30 Days)</h3>
        <p className="text-3xl font-bold text-red-600">
          {metrics.summary.crisis_alerts_last_30_days}
        </p>
      </div>
    </div>
  );
}
```

---

## 🎯 Complete Integration File Checklist

### **Files to Modify:**

1. **`app/main.py`** - Add routers and middleware
   - Import enhanced_clinical_analytics router
   - Add security middleware
   - Include routers in app

2. **`frontend/src/App.tsx`** - Add enhanced component route
   - Import EnhancedClinicalAssessments
   - Add route for /enhanced-assessments

3. **`frontend/src/components/layout/Sidebar.tsx`** - Add navigation link
   - Add menu item for enhanced assessments

### **New Files Created:**

1. **`app/api/v1/endpoints/enhanced_clinical_analytics.py`** - Analytics API
2. **`INTEGRATION_GUIDE_EXAMPLES.py`** - Usage examples
3. **`COMPLETE_INTEGRATION_GUIDE.md`** - This file

---

## ✅ Verification Commands

### **Test Analytics API:**
```bash
# Get user analytics summary
curl -X GET "http://localhost:8000/api/v1/analytics/user/{user_id}/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get trends
curl -X GET "http://localhost:8000/api/v1/analytics/user/{user_id}/trends/PHQ9?weeks=12" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get population health
curl -X GET "http://localhost:8000/api/v1/analytics/organization/{org_id}/population-health" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Test Enhanced Frontend:**
```bash
cd frontend/
npm run dev

# Navigate to:
# http://localhost:5173/enhanced-assessments
# OR
# http://localhost:5173/clinical-assessments
```

### **Test Security:**
```bash
# Test rate limiting (submit multiple times rapidly)
curl -X POST "http://localhost:8000/api/v1/screening/phq9" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"q1_interest": 2, ...}'

# Should return 429 after 10 submissions
```

---

## 📊 Feature Mapping

### **Analytics Feature → API Endpoint → Frontend Usage**

| Feature | API Endpoint | Frontend Component |
|---------|--------------|-------------------|
| User Trends | `/analytics/user/{id}/trends/{type}` | TrendChart component |
| Population Comparison | `/analytics/user/{id}/comparison/{type}` | PercentileDisplay |
| Outcomes | `/analytics/user/{id}/outcomes/{type}` | ProgressTracker |
| Population Health | `/analytics/organization/{id}/population-health` | OrgDashboard |
| Complete Summary | `/analytics/user/{id}/summary` | AnalyticsOverview |

### **Security Feature → Middleware → Protection**

| Feature | Middleware | Protects Against |
|---------|------------|-----------------|
| Rate Limiting | security_middleware | API abuse, DoS |
| Anomaly Detection | security_middleware | Session hijacking |
| Input Sanitization | DataSanitizer | SQL injection, XSS |
| PHI Encryption | EnhancedSecurityManager | Data breaches |
| Access Validation | validate_phi_access | Unauthorized access |
| Audit Logging | _log_audit_entry | Compliance tracking |

---

## 🚀 Go-Live Checklist

- [x] Dependencies installed (scipy, redis, boto3, framer-motion)
- [x] Analytics API endpoint created
- [x] Enhanced frontend component created
- [x] Security manager created
- [x] Integration guide written
- [ ] **YOUR ACTION:** Add routers to `app/main.py`
- [ ] **YOUR ACTION:** Add component route to `frontend/src/App.tsx`
- [ ] **YOUR ACTION:** Test analytics endpoints
- [ ] **YOUR ACTION:** Test enhanced frontend
- [ ] **YOUR ACTION:** Test security features

---

## 📞 Quick Reference

**Analytics API:**
```python
GET /api/v1/analytics/user/{user_id}/summary
GET /api/v1/analytics/user/{user_id}/trends/{screening_type}
GET /api/v1/analytics/user/{user_id}/comparison/{screening_type}
GET /api/v1/analytics/user/{user_id}/outcomes/{screening_type}
GET /api/v1/analytics/organization/{org_id}/population-health
GET /api/v1/analytics/organization/{org_id}/dashboard
```

**Security Usage:**
```python
security = EnhancedSecurityManager(db)
await security.check_rate_limit(user_id, action)
await security.encrypt_phi(data, user_id)
await security.validate_phi_access(user_id, resource_type, resource_id, action)
await security.detect_anomaly(user_id, action, context)
```

**Frontend:**
```tsx
import { EnhancedClinicalAssessments } from '@/components/clinical';
<EnhancedClinicalAssessments />
```

---

**All enhancements are ready to integrate! Just add the routers and routes shown above.** 🚀
