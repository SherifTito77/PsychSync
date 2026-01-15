# PsychSync Services Layer

## Overview

The services layer contains business logic, data processing, and integration services. Services act as intermediaries between API endpoints and database/data sources, implementing core application functionality.

## Architecture

```
app/services/
├── satisfaction_service.py       # Customer satisfaction tracking
├── okr_service.py                # OKR (Objectives and Key Results) management
├── team_personality_service.py   # Team personality analysis
├── ai_insights_service.py        # AI-powered insights generation
└── ...
```

## Design Principles

1. **Separation of Concerns**: Services separate business logic from API routing
2. **Reusability**: Service methods can be called from multiple endpoints
3. **Testability**: Business logic can be tested independently of API
4. **Transaction Management**: Services handle database transactions

## Common Service Patterns

### CRUD Operations

```python
class AssessmentService:
    """Assessment management service"""

    def create_assessment(self, data: AssessmentCreate, db: Session):
        """Create new assessment"""
        assessment = Assessment(**data.dict())
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    def get_assessment(self, assessment_id: int, db: Session):
        """Get assessment by ID"""
        return db.query(Assessment).filter(
            Assessment.id == assessment_id
        ).first()
```

### Complex Business Logic

```python
class TeamPersonalityService:
    """Team personality analysis service"""

    def analyze_team_dynamics(self, team_id: int, db: Session):
        """
        Analyze team personality composition

        Returns:
            Team dynamics insights including:
            - Personality diversity metrics
            - Collaboration patterns
            - Potential conflicts
            - Strengths and weaknesses
        """
        # 1. Fetch team members
        # 2. Get personality profiles
        # 3. Run analysis algorithms
        # 4. Generate insights
        pass
```

### External Integration

```python
class HRISIntegrationService:
    """HRIS system integration"""

    def sync_employee_data(self, organization_id: int):
        """
        Sync employee data from external HRIS system

        Supported providers:
        - Workday
        - BambooHR
        - ADP
        """
        # 1. Connect to external API
        # 2. Fetch employee data
        # 3. Transform and store locally
        pass
```

## Key Services

### SatisfactionService (`satisfaction_service.py`)
**Purpose**: Track customer satisfaction across the journey

**Key Methods**:
- `record_survey_response()` - Record CSAT/NPS surveys
- `calculate_csi()` - Composite Satisfaction Index
- `get_satisfaction_trends()` - Historical trends

**Usage**:
```python
service = SatisfactionService()
service.record_survey_response(
    user_id=123,
    survey_type=SurveyType.CSAT,
    score=5,
    touchpoint_type=TouchpointType.ONBOARDING
)
```

### OKRService (`okr_service.py`)
**Purpose**: Manage quarterly OKRs

**Key Methods**:
- `create_objective()` - Create quarterly objectives
- `create_key_result()` - Add measurable key results
- `update_progress()` - Track OKR progress

### AIOpenAIService (`ai_insights_service.py`)
**Purpose**: Generate AI-powered insights

**Features**:
- Personality pattern recognition
- Team composition recommendations
- Predictive analytics

## Creating New Services

1. **Create service class** in `app/services/`:

```python
from typing import Optional
from sqlalchemy.orm import Session

class MyService:
    """Brief description of service purpose"""

    def __init__(self):
        """Initialize service with dependencies"""
        pass

    def do_something(self, param: str, db: Session):
        """
        Method description

        Args:
            param: Parameter description
            db: Database session

        Returns:
            Result description
        """
        # Business logic here
        pass
```

2. **Use in endpoints**:

```python
from app.services.my_service import MyService

@router.post("/action")
async def perform_action(
    request: RequestSchema,
    db: Session = Depends(get_db)
):
    service = MyService()
    result = service.do_something(request.param, db)
    return result
```

## Error Handling

Services should raise specific exceptions:

```python
from fastapi import HTTPException

class AssessmentService:
    def get_assessment(self, assessment_id: int, db: Session):
        assessment = db.query(Assessment).filter(
            Assessment.id == assessment_id
        ).first()

        if not assessment:
            raise HTTPException(
                status_code=404,
                detail="Assessment not found"
            )

        return assessment
```

## Database Transactions

Services manage database transactions:

```python
def update_multiple_items(self, updates: List[Update]):
    try:
        for update in updates:
            # Perform update
            db.add(update)

        db.commit()  # Commit all changes
    except Exception as e:
        db.rollback()  # Rollback on error
        raise HTTPException(
            status_code=500,
            detail=f"Update failed: {str(e)}"
        )
```

## Testing Services

```python
import pytest
from app.services.my_service import MyService

def test_service_method():
    service = MyService()
    result = service.do_something("test", db_session)
    assert result is not None
    assert result.status == "success"
```

## Related Documentation

- [API Layer](../api/README.md) - How services are called
- [Database Models](../db/models/README.md) - Data structures
- [Core Config](../core/README.md) - Configuration management
