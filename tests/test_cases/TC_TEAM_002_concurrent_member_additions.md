# Test Case: TC_TEAM_002 - Concurrent Team Member Additions

**Test ID**: PSYNC-TEAM-002
**Priority**: P1 (High)
**Automated**: ✅ Yes
**Test Type**: Functional | Race Condition | Concurrency
**Estimated Duration**: 5 seconds
**Tier**: Tier 2 (Full Regression - runs nightly)

---

## Description

Verify that when multiple team members are added to a team concurrently (simulating multiple administrators adding members at the same time), all members are successfully added without data corruption, lost updates, or duplicate records.

---

## User Story

As a team administrator, when multiple admins add members to the same team simultaneously, the system should handle all requests correctly and ensure all members are added without errors.

---

## Acceptance Criteria Reference

See `QA_ACCEPTANCE_CRITERIA.md` Section 3 - Team & Organization Management

---

## Pre-Conditions

### System State
- [x] Application server is running
- [x] PostgreSQL database is accessible
- [x] Team exists with ID: `team-concurrent-001`
- [x] Team has 0 members initially
- [x] Three admin users authenticated (admin1, admin2, admin3)

### Test Data
- **Team ID**: `team-concurrent-001`
- **Organization ID**: `org-concurrent-001`
- **Users to Add**: 10 users (`member001@psychsync.test` through `member010@psychsync.test`)
- **Concurrent Requests**: 3 simultaneous requests

**Admin Users:**
- `admin1@psychsync.test` (Token: token_admin1)
- `admin2@psychsync.test` (Token: token_admin2)
- `admin3@psychsync.test` (Token: token_admin3)

**Members to Add:**
```json
[
  {"email": "member001@psychsync.test", "role": "MEMBER"},
  {"email": "member002@psychsync.test", "role": "MEMBER"},
  {"email": "member003@psychsync.test", "role": "MEMBER"},
  {"email": "member004@psychsync.test", "role": "MEMBER"},
  {"email": "member005@psychsync.test", "role": "MEMBER"},
  {"email": "member006@psychsync.test", "role": "MEMBER"},
  {"email": "member007@psychsync.test", "role": "MEMBER"},
  {"email": "member008@psychsync.test", "role": "MEMBER"},
  {"email": "member009@psychsync.test", "role": "MEMBER"},
  {"email": "member010@psychsync.test", "role": "MEMBER"}
]
```

---

## Test Steps

### Step 1: Prepare Users
Create 10 users in the database who will be added to the team

### Step 2: Execute Concurrent Addition Requests
Three admins simultaneously add members to the same team:

- **Admin 1** adds: member001, member002, member003, member004
- **Admin 2** adds: member005, member006, member007
- **Admin 3** adds: member008, member009, member010

All requests happen simultaneously (within 100ms of each other)

### Step 3: Wait for All Requests to Complete
All HTTP requests should return 200 or 201

### Step 4: Verify Team Members
Query team to verify all 10 members were added

### Step 5: Verify Data Integrity
Check for:
- No duplicate member records
- No lost updates (all members present)
- Correct role assignments
- No data corruption

---

## Expected Results

### HTTP Responses
All 10 member addition requests should succeed:

```json
// Response for each successful addition
{
  "success": true,
  "status": "ok",
  "message": "Member added to team successfully",
  "data": {
    "team_id": "team-concurrent-001",
    "user_id": "member-id-here",
    "email": "member001@psychsync.test",
    "role": "MEMBER",
    "added_at": "2025-01-10T14:40:00Z",
    "added_by": "admin1@psychsync.test"
  }
}
```

### Response Criteria
- [x] **Status Code**: All requests return 200 OK or 201 CREATED
- [x] **Success Field**: All `success: true`
- [x] **No Conflicts**: No 409 CONFLICT errors (duplicate member)
- [x] **No Errors**: No 500 INTERNAL_SERVER_ERROR

### Database Verification
```sql
SELECT COUNT(*) FROM team_members WHERE team_id = 'team-concurrent-001';
```

Expected Result:
```json
{
  "count": 10
}
```

### Data Integrity Checks

#### Check 1: No Duplicate Members
```sql
SELECT email, COUNT(*) as count
FROM team_members
WHERE team_id = 'team-concurrent-001'
GROUP BY email
HAVING COUNT(*) > 1;
```

Expected Result: **0 rows** (no duplicates)

#### Check 2: All Members Present
```sql
SELECT email, role
FROM team_members
WHERE team_id = 'team-concurrent-001'
ORDER BY email;
```

Expected Result: All 10 members present
```json
[
  {"email": "member001@psychsync.test", "role": "MEMBER"},
  {"email": "member002@psychsync.test", "role": "MEMBER"},
  ...
  {"email": "member010@psychsync.test", "role": "MEMBER"}
]
```

#### Check 3: No Data Corruption
- [x] All `team_id` values match `team-concurrent-001`
- [x] All `user_id` values are valid UUIDs
- [x] All `role` values are valid (`MEMBER`, `TEAM_LEAD`, or `ADMIN`)
- [x] All `joined_at` timestamps are reasonable (within test execution window)
- [x] All `added_by` values reference valid admins

#### Check 4: Transaction Isolation
- [x] No partial updates (members partially added)
- [x] No orphaned records (foreign key integrity maintained)
- [x] No locking issues (deadlocks resolved or prevented)

---

## Post-Conditions

### Database State
```sql
-- Team member count
SELECT COUNT(*) FROM team_members WHERE team_id = 'team-concurrent-001';
-- Expected: 10

-- Team member list
SELECT * FROM team_members WHERE team_id = 'team-concurrent-001' ORDER BY email;
-- Expected: All 10 members, no duplicates
```

### Audit Logs
- [x] 10 member addition events logged
- [x] Each event includes: admin_id, member_id, team_id, timestamp
- [x] Events show concurrent timestamps (within 100ms)

### Cache State
- [x] Team member count cache is updated or invalidated
- [x] Team analytics reflect correct member count (10)

---

## Race Condition Scenarios Tested

### Scenario A: Same Member Added by Multiple Admins
**What happens if admin1 and admin2 both try to add member001 at the same time?**

**Expected Behavior:**
- First request succeeds (201 CREATED)
- Second request fails with 409 CONFLICT ("User already a team member")
- No duplicate records

### Scenario B: Multiple Members Added Concurrently
**What happens when 10 members are added simultaneously by 3 admins?**

**Expected Behavior:**
- All 10 additions succeed
- No lost updates
- Database handles concurrent INSERTs correctly (using UNIQUE constraints)

### Scenario C: Rapid Additions to Same Team
**What happens when members are added as fast as possible?**

**Expected Behavior:**
- System scales to handle request volume
- No deadlock errors
- Response time remains acceptable (< 500ms)

---

## Edge Cases & Variations

### Related Test Cases

- **TC_TEAM_003**: Concurrent member removals
- **TC_TEAM_004**: Concurrent role updates
- **TC_TEAM_005**: Member addition while team is being deleted
- **TC_TEAM_006**: Member addition during team transfer

---

## Test Automation Script

### File: `tests/integration/test_team_concurrent_operations.py`

```python
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.team import Team, TeamMember
from app.db.models.user import User

@pytest.mark.regression
@pytest.mark.team
@pytest.mark.asyncio
@pytest.mark.concurrent
async def test_concurrent_team_member_additions(
    async_client: AsyncClient,
    db_session: AsyncSession,
    three_admin_users
):
    """
    Test Case: TC_TEAM_002 - Concurrent Team Member Additions

    Verify that multiple concurrent member additions work correctly
    without data corruption or lost updates.
    """
    # Arrange
    team_id = "team-concurrent-001"
    admin1, admin2, admin3 = three_admin_users

    # Create 10 test users
    test_users = []
    for i in range(1, 11):
        user = await create_test_user(
            db_session,
            email=f"member{i:03d}@psychsync.test"
        )
        test_users.append(user)

    # Divide users among 3 admins
    admin1_users = test_users[0:4]    # 4 users
    admin2_users = test_users[4:7]    # 3 users
    admin3_users = test_users[7:10]   # 3 users

    # Act - Concurrent additions
    async def add_members(admin, users, delay_ms=0):
        """Add members to team with optional delay"""
        await asyncio.sleep(delay_ms / 1000)  # Simulate network delay

        results = []
        for user in users:
            response = await async_client.post(
                f"/api/v1/teams/{team_id}/members",
                json={
                    "user_id": user.id,
                    "role": "MEMBER"
                },
                headers={"Authorization": f"Bearer {admin['token']}"}
            )
            results.append(response)

        return results

    # Execute all additions concurrently
    tasks = [
        add_members(admin1, admin1_users),
        add_members(admin2, admin2_users),
        add_members(admin3, admin3_users)
    ]

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)

    # Flatten results
    all_responses = [response for task_results in results for response in task_results]

    # Assert - All requests succeeded
    for response in all_responses:
        assert response.status_code in [200, 201], \
            f"Expected 200/201, got {response.status_code}: {response.text}"

    # Assert - Verify count in database
    result = await db_session.execute(
        select(func.count(TeamMember.id)).where(
            TeamMember.team_id == team_id
        )
    )
    member_count = result.scalar_one()

    assert member_count == 10, \
        f"Expected 10 team members, got {member_count}"

    # Assert - No duplicates
    result = await db_session.execute(
        select(TeamMember.email, func.count(TeamMember.id))
        .where(TeamMember.team_id == team_id)
        .group_by(TeamMember.email)
        .having(func.count(TeamMember.id) > 1)
    )
    duplicates = result.all()

    assert len(duplicates) == 0, \
        f"Found duplicate team members: {duplicates}"

    # Assert - All expected members present
    result = await db_session.execute(
        select(TeamMember)
        .where(TeamMember.team_id == team_id)
        .order_by(TeamMember.email)
    )
    members = result.scalars().all()

    member_emails = [m.email for m in members]
    for user in test_users:
        assert user.email in member_emails, \
            f"User {user.email} not found in team members"

    # Assert - Data integrity
    for member in members:
        assert member.team_id == team_id
        assert member.role == "MEMBER"
        assert member.joined_at is not None

    # Assert - Performance (should be fast)
    # All requests should complete in < 5 seconds total
    max_duration = max(r.elapsed.total_seconds() for r in all_responses)
    assert max_duration < 2.0, \
        f"Slow response detected: {max_duration:.2f}s"

@pytest.mark.parametrize("delay_ms", [0, 10, 50, 100])
async def test_concurrent_additions_with_varying_delays(
    delay_ms,
    async_client: AsyncClient,
    db_session: AsyncSession,
    three_admin_users
):
    """
    Test concurrent additions with different network delays
    to simulate real-world conditions.
    """
    # Similar test with delay parameter
    # ...
```

---

## Concurrency Testing Strategy

### Database-Level Protection

#### UNIQUE Constraint (Primary Protection)
```sql
-- Schema definition prevents duplicates
ALTER TABLE team_members
ADD CONSTRAINT unique_team_user
UNIQUE (team_id, user_id);
```

This ensures that even with concurrent INSERTs, the database prevents duplicates.

#### Transaction Isolation Level
```python
# Use READ_COMMITTED isolation
async with AsyncSession(
    db_session.bind,
    isolation_level="READ_COMMITTED"
) as session:
    # Add member
    ...
```

### Application-Level Protection

#### Optimistic Locking
```python
# Check if member exists before adding
existing = await db_session.execute(
    select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    )
)
if existing.first():
    raise HTTPException(status_code=409, detail="Already a member")
```

#### Retry Logic
```python
from sqlalchemy.exc import IntegrityError

async def add_member_with_retry(team_id, user_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await add_member(team_id, user_id)
        except IntegrityError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
```

---

## Performance Expectations

### Response Time
- **Target**: < 500ms per request (p95)
- **Acceptable**: < 1s per request
- **Total Time**: All 10 requests should complete in < 5 seconds

### Throughput
- **Target**: Handle at least 50 concurrent member additions per team
- **Current Test**: 10 members, 3 concurrent admins

### Scalability
- System should scale to handle:
  - 100 concurrent member additions
  - 50 teams being modified simultaneously
  - 1000 team member operations per minute

---

## Test Data Cleanup

### Cleanup Procedure
```python
@pytest.fixture(autouse=True)
async def cleanup_concurrent_test_data(db_session: AsyncSession):
    """Clean up test data after concurrent test"""
    yield
    # Delete test team members
    await db_session.execute(
        delete(TeamMember).where(
            TeamMember.team_id == "team-concurrent-001"
        )
    )
    # Delete test users
    await db_session.execute(
        delete(User).where(
            User.email.like("member%@psychsync.test")
        )
    )
    await db_session.commit()
```

---

## History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-01-10 | Initial test case creation | QA Team |

---

## Related Documentation

- **Database Schema**: `app/db/models/team.py`
- **Team Service**: `app/services/team_service.py`
- **Concurrency Strategy**: `docs/architecture/concurrency_patterns.md`

---

## Notes

- This test runs nightly (not on every PR) due to longer execution time
- Test is marked as `@pytest.mark.concurrent` for easy filtering
- Database UNIQUE constraint is the primary protection against duplicates
- Application-level checks provide better error messages
- In production, consider using Redis locks for very high-traffic teams
