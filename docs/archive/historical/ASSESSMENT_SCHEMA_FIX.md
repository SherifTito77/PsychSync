# Assessment Schema Fix Summary

## Issues Resolved

This fix resolves the Step 2: Programmatic Assessment Data issues:

### 1. Database Schema Incompatibility ❌ → ✅
**Problem**: Multiple answer columns created confusion in SQL queries
**Solution**: Documented the three-column answer strategy with clear usage patterns:
- `answer_text` for open-ended responses
- `answer_value` for numeric scale responses
- `answer_data` for complex JSON responses

Added CHECK constraint ensuring at least one answer column is populated.

### 2. Complex Foreign Key Relationships ❌ → ✅
**Problem**: Confusion about relationship chain (assessment_questions → assessment_sections → responses)
**Solution**: Created comprehensive documentation showing:
- Clear relationship diagrams
- Query examples for common patterns
- Performance indexes for optimization

### 3. Table Name Mismatch ❌ → ✅
**Problem**: Migration created `questions` table but model expected `assessment_questions`
**Solution**: Migration automatically renames table to match model expectations.

### 4. Missing `responses` Table ❌ → ✅
**Problem**: The `responses` table didn't exist in database
**Solution**: New migration creates the `responses` table with proper schema.

## Files Created/Modified

### Database Migration
- `alembic/versions/59613cde8000_fix_assessment_schema_resolve_response_.py`
  - Renames `questions` → `assessment_questions`
  - Creates `responses` table
  - Adds performance indexes
  - Adds CHECK constraint for answer validation

### Documentation
- `app/db/models/README.md` (updated)
  - Added assessment schema architecture overview
  - Documented response model distinctions
  - Added query examples and relationship diagrams

### Validation Scripts
- `scripts/validate_assessment_schema.sql`
  - SQL script to validate schema health
  - Checks for orphaned records
  - Verifies all constraints and indexes

- `scripts/test_programmatic_assessment_insert.py`
  - Comprehensive test for programmatic data insertion
  - Tests all answer column types
  - Validates complex queries with joins

### Schema Updates
- `app/schemas/response.py` (fixed)
  - Changed `ResponseScore.id` from `int` to `UUID`
  - Changed `ResponseScore.response_id` from `int` to `UUID`

## How to Apply

### Step 1: Run the Migration
```bash
# Stop any running database
docker-compose down

# Start fresh database (optional, for clean slate)
docker-compose up -d db

# Wait for database to be ready
sleep 5

# Apply migration
alembic upgrade head
```

### Step 2: Verify Schema Health
```bash
# Run SQL validation
docker-compose exec -T db psql -U postgres -d psychsync -f scripts/validate_assessment_schema.sql
```

### Step 3: Test Programmatic Insertion
```bash
# Run test script
python scripts/test_programmatic_assessment_insert.py
```

## Schema Architecture After Fix

```
assessments (assessment definitions)
  ├── assessment_sections (organization within assessments)
  │     └── assessment_questions (individual questions)
  │           └── responses (individual question responses) ⭐ NEW
  └── assessment_responses (response sessions)
```

## Response Model Clarification

### `responses` Table (Individual Question Responses)
Use for:
- Detailed analytics on individual question performance
- Tracking response times per question
- Building analytics dashboards
- Aggregating responses across users

### `assessment_responses` Table (Response Sessions)
Use for:
- Quick retrieval of all answers for completed assessment
- Tracking assessment completion rates
- Resuming in-progress assessments
- Storing bulk responses from frontend

## Query Examples

### Get all responses for a user's assessment:
```sql
SELECT r.*, q.question_text, q.question_type
FROM responses r
JOIN assessment_questions q ON r.question_id = q.id
WHERE r.assessment_id = ? AND r.user_id = ?
ORDER BY q.order;
```

### Get all responses to a specific question:
```sql
SELECT r.*, u.email
FROM responses r
JOIN users u ON r.user_id = u.id
WHERE r.question_id = ?
ORDER BY r.created_at DESC;
```

### Get user's responses with all details:
```python
from sqlalchemy import select

result = await session.execute(
    select(Response, AssessmentQuestion)
    .join(AssessmentQuestion, Response.question_id == AssessmentQuestion.id)
    .where(Response.user_id == user_id)
    .where(Response.assessment_id == assessment_id)
    .order_by(AssessmentQuestion.order)
)
responses = result.all()
```

## Performance Indexes Added

| Index | Purpose |
|-------|---------|
| `idx_response_user_created` | Get user's responses ordered by time |
| `idx_response_assessment_user` | Get user's responses for specific assessment |
| `idx_response_user_assessment` | Get all responses for user in assessment |
| `idx_response_question` | Get all responses to a specific question |
| `idx_response_answer_data_gin` | Query JSONB answer_data field |

## Data Validation

### CHECK Constraint
```sql
ALTER TABLE responses
ADD CONSTRAINT chk_at_least_one_answer
CHECK (
    answer_text IS NOT NULL OR
    answer_value IS NOT NULL OR
    answer_data IS NOT NULL
);
```

This ensures each response has at least one answer field populated.

## Rollback Plan

If needed, rollback with:
```bash
alembic downgrade -1
```

This will:
1. Drop the `responses` table
2. Rename `assessment_questions` back to `questions`
3. Remove all new indexes and constraints

**Warning**: Downgrade will DELETE all data in the `responses` table.

## Next Steps

1. **Run Migration**: Apply the schema changes
2. **Validate**: Run SQL validation script
3. **Test**: Run programmatic insertion test
4. **Update Code**: Review and update any code using old table names or response patterns
5. **Monitor**: Check for any issues in production logs

## Summary

The assessment schema is now clean, consistent, and properly documented. The `responses` table enables programmatic data insertion without foreign key issues, and the three-column answer strategy provides flexibility for different question types while maintaining data integrity.
