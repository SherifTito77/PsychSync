# ADR 002: Separate AI Engine into Standalone Package

## Status
**Accepted** - 2025-01-19

## Context

### Current State
AI/ML code is mixed throughout the FastAPI application:

```
app/
├── services/
│   ├── ai_enhanced_analytics.py       # AI logic in services
│   ├── ai_monitoring_service.py       # Mixed with HTTP concerns
│   └── clinical/
│       └── scoring/                    # Scoring algorithms
├── assessments/
│   └── scoring_engine.py              # More scoring logic
└── api/v1/endpoints/
    └── ai_analytics.py                # API + AI logic mixed

ai/                                     # Separate but coupled
├── processors/                        # Inconsistent interfaces
│   ├── mbti_processor.py              # Different return types
│   ├── big_five.py                    # Mixed patterns
│   └── enneagram_processor.py
```

### Problems

1. **Tight Coupling**: AI processors have FastAPI dependencies
2. **Inconsistent Interfaces**: Each processor returns different types (dict, dataclass, custom objects)
3. **Polluted Dependencies**: ML requirements affect main application
4. **Hard to Test**: Need HTTP context to test processors
5. **Versioning Issues**: Can't version AI engine independently
6. **Reusability**: Can't use AI engine in CLI, other services, or standalone

### Code Examples

**Inconsistent Interfaces:**
```python
# ❌ MBTI processor
def process_mbti(data: dict) -> MBTIResult:
    # Returns custom dataclass
    pass

# ❌ Big Five processor
def process_big_five(data: dict) -> dict:
    # Returns plain dict
    pass

# ❌ Enneagram processor
def process_enneagram(data: dict) -> tuple:
    # Returns tuple (!)
    pass
```

**FastAPI Dependencies:**
```python
# ❌ Current: AI processor depends on HTTP
class MBTIProcessor:
    def __init__(self, request: Request):
        self.request = request  # Why?!

    def process(self, data):
        # Uses request.state...
```

## Decision

**Extract AI/ML code into standalone `app.ai/` package** with clean interfaces.

### New Architecture

```
app.ai/                              # 🤖 Standalone Package
├── __init__.py
├── processors/                         # Assessment processors
│   ├── base.py                         # Common interface
│   ├── mbti.py                         # MBTI processor
│   ├── big_five.py                    # Big Five processor
│   ├── enneagram.py                   # Enneagram processor
│   └── ...
├── scoring/                            # Scoring algorithms
│   ├── base.py
│   └── algorithms.py
├── models/                             # Shared types
│   ├── processing_result.py            # Standardized output
│   └── shared_types.py
├── tests/                              # AI-specific tests
└── requirements.txt                    # ML dependencies only

app/                                     # 🚀 FastAPI Application
├── domain/services/
│   └── assessment_processing_service.py  # Integration layer
└── api/v1/endpoints/
    └── assessments.py                    # Thin HTTP layer
```

### Implementation

**Standardized Processor Interface:**

```python
# app.ai/processors/base.py
from abc import ABC, abstractmethod
from app.ai.models.processing_result import ProcessingResult

class BaseProcessor(ABC):
    @abstractmethod
    def process(self, raw_data: Dict[str, Any]) -> ProcessingResult:
        """All processors return this consistent type"""
        pass

    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Input validation"""
        pass
```

**Consistent Return Type:**

```python
# app.ai/models/processing_result.py
@dataclass
class ProcessingResult:
    framework: str                      # "mbti", "big_five", etc.
    status: ProcessingStatus            # SUCCESS, PARTIAL, FAILED
    data: Dict[str, Any]                # Processed data
    confidence: float                   # 0.0 to 1.0
    warnings: List[str]                 # Optional warnings
    errors: List[str]                   # If failed
    processed_at: datetime

    @classmethod
    def success(cls, framework, data, confidence=1.0):
        """Create successful result"""

    @classmethod
    def failure(cls, framework, errors):
        """Create failed result"""
```

**Example Processor:**

```python
# app.ai/processors/mbti.py
class MBTIProcessor(BaseProcessor):
    def process(self, raw_data: Dict) -> ProcessingResult:
        if not self.validate_input(raw_data):
            return ProcessingResult.failure(
                framework="mbti",
                errors=["Invalid input data"]
            )

        try:
            # Process MBTI assessment
            result = self._calculate_type(raw_data)
            confidence = self._calculate_confidence(raw_data)

            return ProcessingResult.success(
                framework="mbti",
                data=result,
                confidence=confidence
            )
        except Exception as e:
            return ProcessingResult.failure(
                framework="mbti",
                errors=[str(e)]
            )

    def validate_input(self, data: Dict) -> bool:
        required = ["responses", "assessment_id"]
        return all(field in data for field in required)
```

**Integration Layer:**

```python
# app/domain/services/assessment_processing_service.py
from app.ai.processors.mbti import MBTIProcessor
from app.ai.processors.big_five import BigFiveProcessor

class AssessmentProcessingService:
    """Integrates AI engine with application"""

    def __init__(self):
        self._processors = {
            "mbti": MBTIProcessor(),
            "big_five": BigFiveProcessor(),
            # Register all processors
        }

    async def process_assessment(
        self,
        framework: str,
        responses: Dict
    ) -> ProcessingResult:
        """Process assessment using appropriate processor"""

        processor = self._processors.get(framework)
        if not processor:
            raise ValueError(f"Unknown framework: {framework}")

        # Can add caching, logging, monitoring here
        result = processor.process(responses)

        # Log processing metrics
        logger.info(
            f"Processed {framework} assessment",
            extra={
                "framework": framework,
                "status": result.status.value,
                "confidence": result.confidence
            }
        )

        return result
```

**Dependencies:**

```python
# app.ai/requirements.txt
# Only ML-specific dependencies
numpy>=1.24.0
scipy>=1.10.0
scikit-learn>=1.2.0
pandas>=2.0.0

# NOT included:
# - fastapi
# - sqlalchemy
# - pydantic (except for app.ai internal use)
```

## Consequences

### Positive
✅ **Clean Separation**: AI logic independent of HTTP/Database
✅ **Consistent Interface**: All processors return `ProcessingResult`
✅ **Testable**: Can test processors without FastAPI
✅ **Reusable**: Use AI engine in CLI, batch jobs, other services
✅ **Independent Versioning**: Can version AI engine separately
✅ **Isolated Dependencies**: ML packages don't affect main app
✅ **Clear Ownership**: AI team owns app.ai/, backend team owns app/

### Negative
❌ **More Files**: Additional package structure
❌ **Integration Layer**: Need service to bridge AI and app
❌ **Migration Effort**: Need to move existing code

### Mitigation
- Clear integration examples
- Comprehensive tests
- Gradual migration (move processors one at a time)

## Implementation Plan

### Phase 1: Create AI Engine Structure
- [x] Create `app.ai/` package directories
- [x] Create `BaseProcessor` abstract class
- [x] Create `ProcessingResult` standardized type

### Phase 2: Migrate Processors
- [ ] Migrate MBTI processor to new structure
- [ ] Migrate Big Five processor
- [ ] Migrate Enneagram processor
- [ ] Migrate remaining processors
- [ ] Ensure all return `ProcessingResult`

### Phase 3: Create Integration Layer
- [ ] Create `AssessmentProcessingService`
- [ ] Register all processors
- [ ] Add error handling and logging
- [ ] Add caching for expensive operations

### Phase 4: Update API Layer
- [ ] Refactor endpoints to use `AssessmentProcessingService`
- [ ] Remove AI logic from endpoints
- [ ] Add integration tests

### Phase 5: Testing
- [ ] Unit tests for each processor
- [ ] Tests for integration service
- [ ] E2E tests for API endpoints

## Testing Example

```python
# tests/app.ai/test_mbti_processor.py
def test_mbti_processor_valid_input():
    """Test MBTI processor with valid input"""
    processor = MBTIProcessor()

    result = processor.process({
        "responses": [1, 2, 3, 4, ...],
        "assessment_id": "test-123"
    })

    assert result.is_successful()
    assert result.framework == "mbti"
    assert "type" in result.data
    assert result.confidence > 0.5

# No FastAPI, no database - just pure business logic!
```

## Alternatives Considered

### Alternative 1: Keep in app/services
**Rejected** - Tight coupling, hard to test, mixed concerns

### Alternative 2: Separate Microservice
**Rejected** - Over-engineering, adds network latency, deployment complexity

### Alternative 3: Use External AI Service
**Rejected** - Vendor lock-in, latency, cost, data privacy concerns

## Related Decisions
- [ADR 001: Use Repository Pattern](001-use-repository-pattern.md) - Complements separation of concerns
- [ADR 003: Standardize UUIDs](003-standardize-uuids.md) - Consistent ID types across systems

## References
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Package Structure for Python](https://docs.python-guide.org/writing/structure/)
