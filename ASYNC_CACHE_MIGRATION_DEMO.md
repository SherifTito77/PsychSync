# 🔧 Async Cache Migration Demonstration

## Real-World Example: Users Endpoint Migration

This document demonstrates the actual migration of the `/users/me` endpoint from synchronous to asynchronous cache.

---

## 📋 Current State (BLOCKING)

**File:** `app/api/v1/endpoints/users.py` (line 43-60)

```python
@router.get("/me")
@measure_performance
@cache_response(expire_seconds=300, key_prefix="user_profile")  # ❌ BLOCKING!
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve the profile of the currently authenticated user.
    """
    return create_success_response(
        data=serialize_model(current_user),
        message="User profile retrieved successfully"
    )
```

**Problem:** The `@cache_response` decorator uses synchronous `cache_get()` and `cache_set()` which **block the event loop** on every cache operation.

**Impact:** Every call to `/api/v1/users/me` blocks ALL other requests while checking cache.

---

## ✅ Solution: Async Cache Migration

### Step 1: Update Imports

**Before:**
```python
from app.core.api_utils import (
    PaginationParams, SortParams, get_pagination_params, get_sort_params,
    create_paginated_list_response, measure_performance, cache_response,  # ❌ SYNC
    apply_filters, apply_sorting, serialize_model, validate_permissions
)
```

**After:**
```python
from app.core.api_utils import (
    PaginationParams, SortParams, get_pagination_params, get_sort_params,
    create_paginated_list_response, measure_performance,
    apply_filters, apply_sorting, serialize_model, validate_permissions
)
from app.core.async_cache import async_cached  # ✅ ASYNC
```

### Step 2: Replace Decorator

**Before:**
```python
@router.get("/me")
@measure_performance
@cache_response(expire_seconds=300, key_prefix="user_profile")  # ❌ SYNC
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    return create_success_response(
        data=serialize_model(current_user),
        message="User profile retrieved successfully"
    )
```

**After:**
```python
@router.get("/me")
@measure_performance
@async_cached(expire=300, key_prefix="user_profile")  # ✅ ASYNC
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    return create_success_response(
        data=serialize_model(current_user),
        message="User profile retrieved successfully"
    )
```

**That's it!** Just replace `@cache_response` with `@async_cached`.

---

## 🚀 Full Migration Script

Let me create the actual migrated file:
