"""
DEADLOCK PREVENTION: NESTED LOCK ACQUISITION
============================================

This document explains how to prevent nested lock deadlocks in your codebase.

PROBLEM: Nested Lock Deadlock
-------------------------------

When you acquire locks in inconsistent order, you can create deadlocks:

    Task A:                    Task B:
    Acquire lock 1              Acquire lock 2
      ↓                              ↓
    Waiting for lock 2          Waiting for lock 1
      🔒 DEADLOCK!

SOLUTION: Always Acquire Locks in Consistent Order
------------------------------------------

❌ BAD: Inconsistent Lock Ordering
```python
async def update_user_and_assessment(user_id, assessment_id):
    async with monitor_lock("update_user"):  # 🔒 Lock 1
        # ... update user ...

    async with monitor_lock("update_assessment"):  # 🔒 Lock 2
        # ... update assessment ...
```

**Deadlock Scenario**:
```
Task A: update_user_and_assessment(1, 2)
  → Locks "update_user", waits for "update_assessment"
Task B: update_user_and_assessment(2, 1)
  → Locks "update_assessment", waits for "update_user"
Result: DEADLOCK!
```

✅ GOOD: Consistent Lock Ordering
```python
# Define lock acquisition order
LOCK_ORDER = [
    "update_user",
    "update_assessment",
    "update_response",
]

async def update_user_and_assessment(user_id, assessment_id):
    # ✅ Always acquire locks in same order
    for lock_name in LOCK_ORDER:
        async with monitor_lock(lock_name):
            if lock_name == "update_user":
                # ... update user ...
            elif lock_name == "update_assessment":
                # ... update assessment ...
```

**Why This Works**:
```
Task A: update_user_and_assessment(1, 2)
  → Locks "update_user" (1st in order)
  → Waits for "update_assessment" (2nd in order)
Task B: update_user_and_assessment(2, 1)
  → Locks "update_user" (1st in order)
  → Waits for "update_assessment" (2nd in order)
Result: Task B waits for Task A to finish, NO DEADLOCK!
```

IMPLEMENTATION GUIDELINES
----------------------

1. **Define Lock Order Constants**
   ```python
   # In app/core/locks.py
   LOCK_ORDER = {
       "user": 1,
       "assessment": 2,
       "response": 3,
   }
   ```

2. **Use with_lock_all() Helper**
   ```python
   async def with_lock_all(*lock_names):
       """Acquire multiple locks in consistent order"""
       locks = []
       for lock_name in sorted(lock_names, key=lambda x: LOCK_ORDER[x]):
           async with monitor_lock(lock_name):
               locks.append(lock_name)
       return locks

   # Usage:
   async with with_lock_all("update_user", "update_assessment"):
       # ... updates both user and assessment ...
   ```

3. **Avoid Lock Chaining**
   ❌ BAD: One function acquires lock, calls another that acquires lock
   ✅ GOOD: Function acquires all needed locks before calling other functions

4. **Use Timeouts on All Locks**
   ```python
   async with monitor_lock("update_user", timeout=5.0):
       # ... operation ...
       # Automatically releases after 5 seconds
   ```

5. **Document Lock Requirements**
   ```python
   async def update_assessment(assessment_id):
       """
       Requires locks: update_assessment (5s timeout)
       Side effects: Updates assessment.status, updates response counts
       """
       async with monitor_lock("update_assessment", timeout=5.0):
           # ... implementation ...
   ```

DETECTION AND MONITORING
----------------------

Add to app/core/monitoring/database_lock_monitor.py:

```python
class NestedLockDetector:
    """Detect and alert on potential nested lock deadlocks"""

    def __init__(self):
        self.lock_stack = {}  # task_id -> [lock_names]

    async def enter_lock(self, task_id, lock_name):
        if task_id not in self.lock_stack:
            self.lock_stack[task_id] = []

        locks_held = self.lock_stack[task_id]

        # Check for potential deadlock
        for lock_name in locks_held:
            if lock_name in locks_held:
                # Re-entering same lock (OK if reentrant)
                continue

            # Check if we're waiting for a lock held by another task
            for other_task_id, other_locks in self.lock_stack.items():
                if lock_name in other_locks:
                    if any(l in locks_held for l in other_locks if l != lock_name):
                        logger.critical(
                            f"POTENTIAL DEADLOCK: "
                            f"Task {task_id} waiting for {lock_name}, "
                            f"but {lock_name} held by {other_task_id}"
                        )

        locks_held.append(lock_name)

    async def exit_lock(self, task_id, lock_name):
        if task_id in self.lock_stack:
            self.lock_stack[task_id].remove(lock_name)
```

USAGE EXAMPLES
-------------

See: app/services/user_service.py:447 (update_user)
See: app/services/assessment_service.py:275 (update_assessment)
See: app/services/response_service.py:105 (update_response)

Author: Security Team
Created: February 12, 2026
"""
