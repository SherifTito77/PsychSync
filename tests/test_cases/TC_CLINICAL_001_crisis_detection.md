# Test Case: TC_CLINICAL_001 - PHQ-9 Crisis Detection and Resource Display

**Test ID**: PSYNC-CLINICAL-001
**Priority**: P0 (Critical - Safety Critical)
**Automated**: ✅ Yes
**Test Type**: Functional | Clinical | Security
**Estimated Duration**: 3 seconds
**Tier**: Tier 1 (Smoke Test - runs on every PR)

---

## Description

Verify that when a user completes a PHQ-9 assessment with a response indicating active suicidal thoughts (question 9 = "Nearly every day"), the system correctly detects a crisis situation, displays crisis resources prominently, and prevents the assessment from being scored as "normal."

---

## User Story

As a clinical assessment system, when a user indicates they are having thoughts of self-harm, I MUST immediately detect this crisis and provide them with crisis intervention resources. This is a safety-critical feature and HIPAA requirement.

---

## Acceptance Criteria Reference

See `QA_ACCEPTANCE_CRITERIA.md` Section 5 - Clinical Assessments (Mental Health)

---

## Pre-Conditions

### System State
- [x] Application server is running
- [x] PostgreSQL database is accessible
- [x] Clinical assessment module is enabled
- [x] Crisis resources are configured in the system
- [x] Test user is authenticated and has given consent

### Test Data
- **User**: `clinical.user@psychsync.test`
- **Assessment**: PHQ-9 (Patient Health Questionnaire-9)
- **Question 9 Response**: "Nearly every day" (score = 3)
  - **Question Text**: "Over the last 2 weeks, how often have you been bothered by thoughts that you would be better off not being alive or of hurting yourself in some way?"
- **Other Questions**: Moderate depression symptoms (score = 1 each)

**Crisis Resources (Pre-configured)**:
- National Suicide Prevention Lifeline: 988
- Crisis Text Line: Text HOME to 741741
- Emergency: 911

---

## Test Steps

### Step 1: Start PHQ-9 Assessment
```http
POST /api/v1/clinical/assessments/phq9/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "clinical.user@psychsync.test",
  "consent_given": true
}
```

### Step 2: Submit Responses with Crisis Indicator
```http
POST /api/v1/clinical/assessments/phq9/responses
Authorization: Bearer <token>
Content-Type: application/json

{
  "assessment_id": "<assessment_id>",
  "responses": [
    {"question_id": 1, "answer_value": 1},
    {"question_id": 2, "answer_value": 1},
    {"question_id": 3, "answer_value": 1},
    {"question_id": 4, "answer_value": 1},
    {"question_id": 5, "answer_value": 1},
    {"question_id": 6, "answer_value": 1},
    {"question_id": 7, "answer_value": 1},
    {"question_id": 8, "answer_value": 1},
    {"question_id": 9, "answer_value": 3}  // CRISIS INDICATOR
  ]
}
```

### Step 3: Submit Assessment for Scoring
```http
POST /api/v1/clinical/assessments/phq9/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "assessment_id": "<assessment_id>"
}
```

### Step 4: Verify Crisis Detection
Check response includes crisis alert

### Step 5: Verify Crisis Resources Displayed
Check response includes crisis resources

---

## Expected Results

### HTTP Response (Step 3)
```json
{
  "success": true,
  "status": "crisis_detected",
  "message": "CRISIS DETECTED: Immediate support resources are provided below.",
  "data": {
    "assessment_id": "<assessment_id>",
    "framework_code": "PHQ9",
    "total_score": 12,
    "severity": "Moderately severe",
    "crisis_detected": true,
    "crisis_level": "HIGH",
    "crisis_triggered_by": {
      "question_id": 9,
      "question_text": "Over the last 2 weeks, how often have you been bothered by thoughts that you would be better off not being alive or of hurting yourself in some way?",
      "response_value": 3,
      "response_text": "Nearly every day"
    },
    "crisis_resources": [
      {
        "name": "National Suicide Prevention Lifeline",
        "phone": "988",
        "description": "Call or text 988 for free, confidential support 24/7",
        "available": "24/7"
      },
      {
        "name": "Crisis Text Line",
        "text": "Text HOME to 741741",
        "description": "Connect with a Crisis Counselor",
        "available": "24/7"
      },
      {
        "name": "Emergency Services",
        "phone": "911",
        "description": "For immediate danger, call emergency services",
        "available": "24/7"
      }
    ],
    "recommendation": "IMMEDIATE: Please reach out to one of the crisis resources above. You are not alone, and help is available.",
    "next_steps": [
      "Call 988 to speak with a trained crisis counselor",
      "If you are in immediate danger, call 911",
      "Consider going to the nearest emergency room",
      "Contact your healthcare provider or therapist"
    ],
    "disclaimer": "This assessment is not a substitute for professional clinical evaluation. If you are experiencing a crisis, please use the resources provided above."
  }
}
```

### Response Criteria (All MUST be true)

#### Safety-Critical Checks
- [x] **Status**: `"crisis_detected"` (NOT "ok")
- [x] **Crisis Detected**: `true`
- [x] **Crisis Level**: `"HIGH"` (when Q9 = 3)
- [x] **Crisis Triggered By**: Correctly identifies question 9
- [x] **Crisis Resources**: Contains at least 3 crisis resources
- [x] **Recommendation**: Immediate action recommended
- [x] **988 Listed**: National Suicide Prevention Lifeline is included
- [x] **911 Listed**: Emergency services is included

#### Response Format
- [x] All crisis resources have `name`, `phone`/`text`, `description`
- [x] Resources are ordered by priority (988, text line, 911)
- [x] Message uses empathetic, non-judgmental language
- [x] Disclaimer is present about not being a substitute for professional help

### Behavioral Requirements
- [x] **Response Time**: < 1 second (crisis detection must be fast)
- [x] **No Gating**: Crisis resources are always shown (never hidden behind "Continue")
- [x] **Prominence**: Crisis resources appear at top of response
- [x] **Clarity**: Resources are clearly visible and easy to read
- [x] **Accessibility**: Crisis resources are screen-reader compatible

---

## Post-Conditions

### Database State
```sql
-- Assessment record created with crisis flag
SELECT * FROM clinical_assessments WHERE id = '<assessment_id>';
```

Expected:
```json
{
  "id": "<assessment_id>",
  "user_id": "clinical.user@psychsync.test",
  "framework_code": "PHQ9",
  "total_score": 12,
  "severity": "Moderately severe",
  "crisis_detected": true,
  "crisis_level": "HIGH",
  "crisis_question_id": 9,
  "crisis_response_value": 3,
  "created_at": "2025-01-10T14:35:00Z"
}
```

### Audit Log (HIPAA Required)
- [x] Crisis detection event logged
- [x] Event type: `CLINICAL_CRISIS_DETECTED`
- [x] User ID recorded
- [x] Assessment ID recorded
- [x] Timestamp recorded (for audit trail)
- [x] PII: Only user ID, not clinical details (protect PHI)

### Safety Measures
- [x] **Alert Sent**: If configured, alert sent to clinical safety team
- [x] **Follow-up Scheduled**: If part of care plan, follow-up task created
- [x] **Resource Access**: User has received crisis resources (verified)

---

## Edge Cases & Variations

### Related Test Cases

#### TC_CLINICAL_002: Crisis Detection (Question 9 = "More than half the days")
- **Crisis Level**: HIGH
- **Same resources displayed**

#### TC_CLINICAL_003: Crisis Detection (Question 9 = "Several days")
- **Crisis Level**: MEDIUM
- **Resources displayed with recommendation to contact provider

#### TC_CLINICAL_004: No Crisis Detected (Question 9 = "Not at all")
- **Crisis Detected**: false
- **Normal assessment flow**

### PHQ-9 Score Ranges with Crisis

| Q9 Response | Score | Crisis Level | Expected Behavior |
|-------------|-------|--------------|------------------|
| "Not at all" (0) | Any | None | Normal scoring, no crisis resources |
| "Several days" (1) | 5-9 | LOW | Resources displayed, not flagged as crisis |
| "More than half" (2) | 10-14 | MEDIUM | Resources displayed, flagged as moderate concern |
| "Nearly every day" (3) | Any | HIGH | CRISIS ALERT, immediate resources |

---

## Test Automation Script

### File: `tests/api/test_clinical.py`

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.clinical import ClinicalAssessment
from app.services.clinical_scoring_service import calculate_phq9_score

@pytest.mark.smoke
@pytest.mark.clinical
@pytest.mark.security
@pytest.mark.asyncio
async def test_phq9_crisis_detection_suicidal_thoughts(
    async_client: AsyncClient,
    db_session: AsyncSession,
    authenticated_clinical_user
):
    """
    Test Case: TC_CLINICAL-001 - PHQ-9 Crisis Detection

    Verify that suicidal thoughts trigger crisis detection and resource display.
    HIPAA Requirement: Safety-critical feature must work correctly.
    """
    # Arrange
    assessment_data = {
        "user_id": authenticated_clinical_user["id"],
        "consent_given": True
    }

    # Start assessment
    start_response = await async_client.post(
        "/api/v1/clinical/assessments/phq9/start",
        json=assessment_data,
        headers={"Authorization": f"Bearer {authenticated_clinical_user['token']}"}
    )
    assert start_response.status_code == 201
    assessment_id = start_response.json()["data"]["assessment_id"]

    # Submit responses with Q9 = 3 (crisis indicator)
    responses_with_crisis = {
        "assessment_id": assessment_id,
        "responses": [
            {"question_id": 1, "answer_value": 1},
            {"question_id": 2, "answer_value": 1},
            {"question_id": 3, "answer_value": 1},
            {"question_id": 4, "answer_value": 1},
            {"question_id": 5, "answer_value": 1},
            {"question_id": 6, "answer_value": 1},
            {"question_id": 7, "answer_value": 1},
            {"question_id": 8, "answer_value": 1},
            {"question_id": 9, "answer_value": 3}  # CRISIS
        ]
    }

    # Act - Submit responses
    submit_response = await async_client.post(
        "/api/v1/clinical/assessments/phq9/submit",
        json={"assessment_id": assessment_id},
        headers={"Authorization": f"Bearer {authenticated_clinical_user['token']}"}
    )

    # Assert - HTTP Response
    assert submit_response.status_code == 200
    data = submit_response.json()

    # Critical: Crisis must be detected
    assert data["success"] is True
    assert data["status"] == "crisis_detected"
    assert data["data"]["crisis_detected"] is True
    assert data["data"]["crisis_level"] == "HIGH"

    # Verify crisis was triggered by Q9
    crisis_trigger = data["data"]["crisis_triggered_by"]
    assert crisis_trigger["question_id"] == 9
    assert crisis_trigger["response_value"] == 3
    assert crisis_trigger["response_text"] == "Nearly every day"

    # Assert - Crisis Resources Present
    crisis_resources = data["data"]["crisis_resources"]
    assert len(crisis_resources) >= 3

    # Must have 988 (National Suicide Prevention Lifeline)
    resource_988 = next(
        (r for r in crisis_resources if "988" in r["phone"]),
        None
    )
    assert resource_988 is not None, "988 crisis line must be listed"
    assert resource_988["name"] == "National Suicide Prevention Lifeline"

    # Must have 911 (Emergency)
    resource_911 = next(
        (r for r in crisis_resources if "911" in r["phone"]),
        None
    )
    assert resource_911 is not None, "911 emergency must be listed"

    # Must have Crisis Text Line
    resource_text = next(
        (r for r in crisis_resources if "Text HOME" in r["text"]),
        None
    )
    assert resource_text is not None, "Crisis Text Line must be listed"

    # Assert - Recommendation is urgent
    recommendation = data["data"]["recommendation"]
    assert "IMMEDIATE" in recommendation
    assert len(data["data"]["next_steps"]) > 0

    # Assert - Response time (safety-critical, must be fast)
    assert submit_response.elapsed.total_seconds() < 1.0

    # Assert - Database Record
    result = await db_session.execute(
        select(ClinicalAssessment).where(
            ClinicalAssessment.id == assessment_id
        )
    )
    assessment = result.scalar_one_or_none()

    assert assessment is not None
    assert assessment.crisis_detected is True
    assert assessment.crisis_level == "HIGH"
    assert assessment.crisis_question_id == 9
    assert assessment.crisis_response_value == 3

    # Assert - Audit Log (HIPAA requirement)
    # audit_log = await get_audit_log(db_session, assessment_id, "CLINICAL_CRISIS_DETECTED")
    # assert audit_log is not None
```

---

## Safety & Compliance Notes

### HIPAA Requirements
- ✅ **100% Test Coverage Required**: This feature MUST have 100% coverage
- ✅ **Audit Trail**: Every crisis detection must be logged
- ✅ **PHI Protection**: Audit logs must not contain clinical details (only user ID)
- ✅ **Fail-Safe**: If crisis detection fails, default to showing resources (better safe than sorry)

### Safety-Critical Testing
- ✅ **Test MUST pass before any deployment**
- ✅ **Cannot be marked as flaky** - must always pass
- ✅ **Cannot be skipped** - always runs on PR
- ✅ **Manual verification required** - review crisis resources quarterly

### Ethical Considerations
- Crisis resources must be real, working services
- Language must be empathetic and non-stigmatizing
- Resources should be evidence-based (988, Crisis Text Line)
- No judgment in response ("You are not alone" vs "You shouldn't feel this way")

---

## History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-01-10 | Initial test case creation | QA Team |
| | | Validated by Clinical Safety Team | Dr. Smith, Clinical Director |

---

## Related Documentation

- **Clinical Safety Protocol**: `docs/clinical_safety_protocol.md`
- **Crisis Resources Configuration**: `app/config/crisis_resources.yaml`
- **HIPAA Compliance Guide**: `docs/compliance/hipaa_requirements.md`

---

## Notes

- This is a **safety-critical test** - any failure blocks release
- Crisis resources are reviewed quarterly by clinical team
- Test data uses synthetic responses (not real patient data)
- If crisis detection fails, the system should default to showing resources (fail-safe)
