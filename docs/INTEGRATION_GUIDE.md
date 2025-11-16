
#docs/INTEGRATION_GUIDE.md

# PsychSync Advanced Features Integration Guide

**Version:** 1.0  
**Last Updated:** November 2025  
**Document Purpose:** Integration instructions for experimental features, anonymization, and reporting modules

---

## Table of Contents

1. [Experimental Features Lab](#experimental-features-lab)
2. [Data Anonymization & Research Export](#data-anonymization--research-export)
3. [Reporting & Export System](#reporting--export-system)
4. [Database Schema Extensions](#database-schema-extensions)
5. [API Endpoints](#api-endpoints)
6. [Frontend Integration](#frontend-integration)

---

## 1. Experimental Features Lab

### 🎯 Features Implemented

#### A/B Testing Framework
- **Purpose**: Test different features/UX with subsets of users
- **Components**: Test configuration, variant assignment, statistics tracking
- **Use Cases**: Onboarding flows, UI changes, feature rollouts

#### Gamification Engine
- **Purpose**: Increase client engagement through achievements and points
- **Components**: Achievements, points system, leaderboards, streaks
- **Use Cases**: Session attendance rewards, homework completion badges

#### Feature Flags
- **Purpose**: Gradual feature rollouts and user-specific enablement
- **Components**: Flag management, rollout percentages, whitelists
- **Use Cases**: Beta feature access, A/B tests, staged rollouts

### 📦 Installation

```bash
pip install pydantic
```

### 🔧 Integration Steps

#### 1. Add to Django Models

Create `app/models/experimental.py`:

```python
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField

class ABTest(models.Model):
    test_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    variants = ArrayField(models.CharField(max_length=50))
    allocation_percentages = ArrayField(models.FloatField())
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ABTestAssignment(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    test = models.ForeignKey(ABTest, on_delete=models.CASCADE)
    variant = models.CharField(max_length=50)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'test']

class UserGamification(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE)
    total_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    achievements_earned = ArrayField(models.CharField(max_length=100), default=list)
    streak_days = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)

class Achievement(models.Model):
    achievement_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    achievement_type = models.CharField(max_length=50)
    points = models.IntegerField()
    icon = models.CharField(max_length=10)

class FeatureFlag(models.Model):
    flag_name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    enabled = models.BooleanField(default=False)
    rollout_percentage = models.FloatField(default=0.0)
    whitelist_users = ArrayField(models.CharField(max_length=100), default=list)
```

#### 2. Create API Endpoints

Create `app/api/experimental_routes.py`:

```python
from fastapi import APIRouter
from ai.experimental_features import ABTestingFramework, GamificationEngine, FeatureFlag

router = APIRouter(prefix="/api/v1/experimental", tags=["Experimental"])

ab_framework = ABTestingFramework()
gamification = GamificationEngine()
feature_flags = FeatureFlag()

@router.post("/ab-test/assign/{test_id}")
async def assign_variant(test_id: str, user_id: str):
    variant = ab_framework.assign_variant(user_id, test_id)
    return {"variant": variant}

@router.post("/gamification/award-points")
async def award_points(user_id: str, points: int, reason: str):
    result = gamification.award_points(user_id, points, reason)
    return result

@router.get("/gamification/leaderboard")
async def get_leaderboard(limit: int = 10):
    return gamification.get_leaderboard(limit)

@router.get("/feature-flag/{flag_name}")
async def check_feature_flag(flag_name: str, user_id: str):
    enabled = feature_flags.is_enabled(flag_name, user_id)
    return {"enabled": enabled}
```

#### 3. Frontend Integration

**React Hook for A/B Testing:**

```javascript
// hooks/useABTest.js
import { useState, useEffect } from 'react';
import api from '../services/api';

export const useABTest = (testId, userId) => {
  const [variant, setVariant] = useState(null);
  
  useEffect(() => {
    const fetchVariant = async () => {
      const response = await api.post(`/api/v1/experimental/ab-test/assign/${testId}`, {
        user_id: userId
      });
      setVariant(response.data.variant);
    };
    
    fetchVariant();
  }, [testId, userId]);
  
  return variant;
};

// Usage:
const MyComponent = () => {
  const variant = useABTest('onboarding_flow_v1', currentUser.id);
  
  return variant === 'new_flow' ? <NewOnboarding /> : <OldOnboarding />;
};
```

**Gamification UI Component:**

```javascript
// components/GamificationBadge.jsx
const GamificationBadge = ({ userId }) => {
  const [progress, setProgress] = useState(null);
  
  useEffect(() => {
    api.get(`/api/v1/experimental/gamification/progress/${userId}`)
      .then(res => setProgress(res.data));
  }, [userId]);
  
  if (!progress) return null;
  
  return (
    <div className="gamification-badge">
      <div className="points">⭐ {progress.total_points} pts</div>
      <div className="level">Level {progress.level}</div>
      <div className="streak">🔥 {progress.streak_days} day streak</div>
    </div>
  );
};
```

---

## 2. Data Anonymization & Research Export

### 🔒 Features Implemented

#### Anonymization Methods
- **Hashing**: Deterministic one-way hashing with salt
- **Masking**: Partial masking (e.g., email, phone)
- **Generalization**: Age bins, ZIP code truncation
- **Redaction**: Free-text PHI removal
- **Date Shifting**: Consistent date shifts per patient

#### HIPAA Compliance
- Covers all 18 Safe Harbor identifiers
- Audit logging for all data access
- Configurable anonymization per column

### 📦 Installation

```bash
pip install pandas faker
```

### 🔧 Integration Steps

#### 1. Add Audit Log Model

```python
class DataAccessLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    resource = models.CharField(max_length=200)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
```

#### 2. Create Anonymization API Endpoints

```python
from fastapi import APIRouter, UploadFile, File
from app.utils.anonymize import DataAnonymizer
import pandas as pd

router = APIRouter(prefix="/api/v1/research", tags=["Research"])

@router.post("/anonymize")
async def anonymize_data(file: UploadFile = File(...)):
    # Read uploaded file
    df = pd.read_csv(file.file)
    
    # Anonymize
    anonymizer = DataAnonymizer(salt="your_project_salt")
    df_anon = anonymizer.anonymize_dataframe(df, auto_detect=True)
    
    # Generate report
    report = anonymizer.generate_anonymization_report(df, df_anon)
    
    # Return anonymized data + report
    return {
        "data": df_anon.to_dict(orient='records'),
        "report": report
    }

@router.get("/export-research-data")
async def export_research_data(
    start_date: str,
    end_date: str,
    include_demographics: bool = True,
    anonymize: bool = True
):
    # Query data
    data = query_data_for_research(start_date, end_date)
    
    if anonymize:
        anonymizer = DataAnonymizer()
        data = anonymizer.anonymize_dataframe(data)
    
    # Log access
    logger = AuditLogger()
    logger.log_access(
        user_id=current_user.id,
        action="export_research_data",
        resource=f"data_{start_date}_to_{end_date}",
        details={"anonymized": anonymize, "records": len(data)}
    )
    
    return data.to_dict(orient='records')
```

#### 3. Frontend Export Interface

```javascript
// components/ResearchExport.jsx
const ResearchExport = () => {
  const [config, setConfig] = useState({
    startDate: '',
    endDate: '',
    anonymize: true,
    includeDemographics: true,
    format: 'csv'
  });
  
  const handleExport = async () => {
    const response = await api.post('/api/v1/research/export', config);
    
    if (config.format === 'csv') {
      downloadCSV(response.data);
    } else if (config.format === 'excel') {
      downloadExcel(response.data);
    }
  };
  
  return (
    <div className="export-panel">
      <h2>Research Data Export</h2>
      
      <input 
        type="date" 
        value={config.startDate}
        onChange={(e) => setConfig({...config, startDate: e.target.value})}
      />
      
      <input 
        type="date" 
        value={config.endDate}
        onChange={(e) => setConfig({...config, endDate: e.target.value})}
      />
      
      <label>
        <input 
          type="checkbox" 
          checked={config.anonymize}
          onChange={(e) => setConfig({...config, anonymize: e.target.checked})}
        />
        Anonymize data (HIPAA compliant)
      </label>
      
      <button onClick={handleExport}>Export Data</button>
    </div>
  );
};
```

---

## 3. Reporting & Export System

### 📊 Features Implemented

#### PDF Reports
- Client progress reports
- Outcome summary reports
- Custom report builder

#### Excel Export
- Multi-sheet workbooks
- Client data exports
- Aggregate statistics

#### CSV Export
- Simple data exports
- Metadata headers

### 📦 Installation

```bash
pip install reportlab openpyxl matplotlib
```

### 🔧 Integration Steps

#### 1. Create Report Generation Service

```python
# services/report_service.py
from app.reports.generate_report import PDFReportGenerator, ExcelExporter

class ReportService:
    def generate_client_report(self, client_id: str, output_format: str = 'pdf'):
        # Fetch client data
        client = get_client(client_id)
        assessments = get_assessments(client_id)
        sessions = get_sessions(client_id)
        
        if output_format == 'pdf':
            generator = PDFReportGenerator(title="Client Progress Report")
            generator.generate_client_progress_report(
                client.to_dict(),
                assessments,
                sessions.summary(),
                f"reports/client_{client_id}_report.pdf"
            )
            return f"client_{client_id}_report.pdf"
        
        elif output_format == 'excel':
            ExcelExporter.export_client_data(
                client.to_dict(),
                assessments,
                sessions,
                f"exports/client_{client_id}_data.xlsx"
            )
            return f"client_{client_id}_data.xlsx"
```

#### 2. Create API Endpoints

```python
@router.get("/reports/client/{client_id}")
async def generate_client_report(
    client_id: str,
    format: str = "pdf"
):
    report_service = ReportService()
    filename = report_service.generate_client_report(client_id, format)
    
    # Return file for download
    return FileResponse(
        f"reports/{filename}",
        media_type='application/pdf' if format == 'pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=filename
    )

@router.post("/reports/custom")
async def generate_custom_report(request: CustomReportRequest):
    builder = ReportBuilder()
    
    for section in request.sections:
        builder.add_section(section.title, section.content, section.type)
    
    builder.generate_report(f"reports/custom_{request.report_id}.pdf", format="pdf")
    
    return {"filename": f"custom_{request.report_id}.pdf"}
```

#### 3. Frontend Report Generation

```javascript
// components/ReportGenerator.jsx
const ReportGenerator = ({ clientId }) => {
  const [generating, setGenerating] = useState(false);
  
  const generateReport = async (format) => {
    setGenerating(true);
    
    try {
      const response = await api.get(
        `/api/v1/reports/client/${clientId}`,
        { params: { format }, responseType: 'blob' }
      );
      
      // Download file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `client_report.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error generating report:', error);
    } finally {
      setGenerating(false);
    }
  };
  
  return (
    <div className="report-actions">
      <button 
        onClick={() => generateReport('pdf')}
        disabled={generating}
      >
        📄 Download PDF Report
      </button>
      
      <button 
        onClick={() => generateReport('excel')}
        disabled={generating}
      >
        📊 Download Excel Export
      </button>
    </div>
  );
};
```

---

## 4. Database Schema Extensions

### Required Tables

```sql
-- A/B Testing
CREATE TABLE ab_tests (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    variants JSONB NOT NULL,
    allocation_percentages JSONB NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ab_test_assignments (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    test_id VARCHAR(100) NOT NULL,
    variant VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, test_id)
);

-- Gamification
CREATE TABLE user_gamification (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    total_points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    achievements_earned TEXT[] DEFAULT ARRAY[]::TEXT[],
    streak_days INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    achievement_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    achievement_type VARCHAR(50),
    points INTEGER NOT NULL,
    icon VARCHAR(10)
);

-- Audit Logs
CREATE TABLE data_access_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    resource VARCHAR(200) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address INET
);

CREATE INDEX idx_logs_user ON data_access_logs(user_id);
CREATE INDEX idx_logs_timestamp ON data_access_logs(timestamp);
```

---

## 5. API Endpoints Summary

### Experimental Features

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/experimental/ab-test/create` | POST | Create A/B test |
| `/api/v1/experimental/ab-test/assign/{test_id}` | POST | Assign variant |
| `/api/v1/experimental/ab-test/stats/{test_id}` | GET | Get test statistics |
| `/api/v1/experimental/gamification/points` | POST | Award points |
| `/api/v1/experimental/gamification/achievement` | POST | Unlock achievement |
| `/api/v1/experimental/gamification/leaderboard` | GET | Get leaderboard |
| `/api/v1/experimental/feature-flag/{flag_name}` | GET | Check feature flag |

### Research & Export

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/research/anonymize` | POST | Anonymize uploaded data |
| `/api/v1/research/export` | POST | Export research data |
| `/api/v1/research/audit-logs` | GET | View audit logs |

### Reporting

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/reports/client/{id}` | GET | Generate client report |
| `/api/v1/reports/outcome-summary` | GET | Aggregate outcome report |
| `/api/v1/reports/custom` | POST | Generate custom report |
| `/api/v1/exports/excel/{id}` | GET | Export to Excel |
| `/api/v1/exports/csv/{id}` | GET | Export to CSV |

---

## 6. Frontend Integration

### Key Components

```
src/
├── components/
│   ├── experimental/
│   │   ├── ABTestVariant.jsx
│   │   ├── GamificationBadge.jsx
│   │   └── FeatureFlagWrapper.jsx
│   ├── research/
│   │   ├── DataExport.jsx
│   │   ├── AnonymizationConfig.jsx
│   │   └── AuditLogViewer.jsx
│   └── reports/
│       ├── ReportGenerator.jsx
│       ├── ReportPreview.jsx
│       └── CustomReportBuilder.jsx
├── hooks/
│   ├── useABTest.js
│   ├── useGamification.js
│   └── useFeatureFlag.js
└── services/
    ├── experimentalApi.js
    ├── researchApi.js
    └── reportingApi.js
```

---

## 7. Configuration

### Environment Variables

```bash
# .env
# Anonymization
ANONYMIZATION_SALT=your_secure_salt_here_change_in_production

# A/B Testing
AB_TEST_DEFAULT_DURATION_DAYS=30

# Gamification
GAMIFICATION_POINTS_PER_SESSION=10
GAMIFICATION_POINTS_PER_HOMEWORK=5

# Reports
REPORTS_STORAGE_PATH=/var/psychsync/reports
REPORTS_MAX_AGE_DAYS=90

# Audit
AUDIT_LOG_PATH=/var/psychsync/logs/audit.log
AUDIT_LOG_RETENTION_DAYS=365
```

---

## 8. Testing

### Unit Tests

```python
# tests/test_experimental.py
def test_ab_test_assignment():
    framework = ABTestingFramework()
    test = framework.create_test(...)
    variant = framework.assign_variant("user_1", test.test_id)
    assert variant in test.variants

# tests/test_anonymization.py
def test_email_anonymization():
    anonymizer = DataAnonymizer()
    email = "test@example.com"
    masked = anonymizer.mask_partial(email)
    assert "@" not in masked or masked != email

# tests/test_reports.py
def test_pdf_generation():
    generator = PDFReportGenerator()
    generator.generate_client_progress_report(...)
    assert os.path.exists("output.pdf")
```

---

## 9. Deployment Checklist

- [ ] Database migrations run successfully
- [ ] Environment variables configured
- [ ] Salt values changed from defaults
- [ ] Audit logging enabled and tested
- [ ] Report storage directory created with proper permissions
- [ ] Feature flags initialized for production
- [ ] A/B tests configured (if any active)
- [ ] Gamification achievements seeded
- [ ] HIPAA compliance verified for anonymization
- [ ] PDF generation tested with production fonts
- [ ] Excel exports tested with large datasets

---

## 10. Maintenance

### Regular Tasks

**Weekly:**
- Review A/B test statistics
- Check gamification leaderboards
- Monitor report generation times

**Monthly:**
- Audit data access logs
- Clean up old reports
- Review feature flag usage
- Update achievement definitions

**Quarterly:**
- Comprehensive security audit
- Anonymization effectiveness review
- Performance optimization

---

**End of Integration Guide**

For questions or issues, contact the development team or create a ticket in the project management system.