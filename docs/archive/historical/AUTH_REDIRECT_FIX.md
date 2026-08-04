# Authentication Redirect Loop Fix

## Problem

The error "No user session found, redirecting to login" was appearing repeatedly, causing redirect loops to the login page even when the user was authenticated.

## Root Cause

There were **duplicate authentication checks** in the application:

1. **`SecureRoute` component** (App.tsx:296) - Checked `localStorage` directly
2. **`RequireAuth` component** - Used `AuthContext` correctly

The `SecureRoute` component was bypassing `AuthContext` and directly checking `localStorage.getItem('user')`. This caused issues when:

- `AuthContext` successfully loaded a user from the backend API
- But `SecureRoute` checked `localStorage` before `AuthContext` finished loading
- `SecureRoute` redirected to login because `localStorage` didn't contain the user data
- Created an infinite redirect loop

## Solution

Modified `SecureRoute` component in `frontend/src/App.tsx` to use `AuthContext` instead of direct `localStorage` access:

### Changes Made

1. **Import `useAuth` hook** (line 12)
   ```typescript
   import { useAuth } from './contexts/AuthContext';
   ```

2. **Remove unnecessary `useState` import** (line 3)
   ```typescript
   import React, { memo, Suspense, lazy, useEffect } from 'react';
   // Removed: useState (no longer needed in SecureRoute)
   ```

3. **Updated `SecureRoute` component** (lines 270-311)
   ```typescript
   const SecureRoute: React.FC<{
     children: React.ReactNode;
     requireAuth?: boolean;
     allowedRoles?: string[];
   }> = memo(({ children, requireAuth = false, allowedRoles }) => {
     const { user, isLoading } = useAuth();

     useEffect(() => {
       // Clear any suspicious data from URL parameters
       const urlParams = new URLSearchParams(window.location.search);
       const suspiciousParams = ['<script', 'javascript:', 'data:text/html', 'vbscript:'];

       urlParams.forEach((value, key) => {
         if (suspiciousParams.some(param => value.toLowerCase().includes(param))) {
           console.warn('Suspicious URL parameter detected:', key, value);
           urlParams.delete(key);
           const newUrl = `${window.location.pathname}${urlParams.toString() ? `?${urlParams.toString()}` : ''}`;
           window.history.replaceState({}, '', newUrl);
         }
       });
     }, []);

     // During initial load, show loading spinner
     if (isLoading) {
       return <SecureFallback message="Authenticating..." />;
     }

     // If auth is required and no user exists, redirect to login
     if (requireAuth && !user) {
       return <Navigate to="/login" replace />;
     }

     // Role-based access control (if specified)
     if (allowedRoles && user && !allowedRoles.includes(user.role || 'employee')) {
       return <Navigate to="/unauthorized" replace />;
     }

     return <>{children}</>;
   });
   ```

## Benefits

1. **Single Source of Truth**: All authentication checks now use `AuthContext`
2. **No Redirect Loops**: Proper loading states prevent premature redirects
3. **Better Loading UX**: Shows "Authenticating..." during API calls
4. **Simpler Code**: Removed duplicate state management (`useState` → `useAuth`)

## Authentication Flow After Fix

```
User logs in
    ↓
AuthContext calls login API
    ↓
Backend returns user data + sets httpOnly cookie
    ↓
AuthContext sets user state
    ↓
SecureRoute checks user from AuthContext ✓
    ↓
User can access protected routes
```

## Related Components

### `RequireAuth` Component (Existing)
- **Purpose**: Provides authentication for route children
- **Implementation**: Uses `AuthContext` with `useAuth()` hook
- **Behavior**: Shows loading during initial auth, debounces redirects

### `SecureRoute` Component (Fixed)
- **Purpose**: Wraps routes with authentication and role-based access
- **Implementation**: Now uses `AuthContext` (was using `localStorage`)
- **Behavior**: Shows loading during auth, checks for user existence and role permissions

### When to Use Each

- **Use `SecureRoute`**: When wrapping route elements in `App.tsx` routing
- **Use `RequireAuth`**: When protecting individual component access within a route

## Testing

To verify the fix works:

1. Clear browser cookies and localStorage
2. Login to the application
3. Navigate to a protected route (e.g., `/personality-assessments`)
4. Verify no redirect loop occurs
5. Refresh the page and verify session persists

## Files Modified

- `frontend/src/App.tsx`:
  - Line 3: Removed `useState` from imports
  - Line 12: Added `useAuth` import
  - Lines 270-311: Rewrote `SecureRoute` to use `AuthContext`

## Additional Notes

- The `AuthContext` is the single source of truth for authentication state
- `localStorage` is used by `AuthContext` for user persistence (not for direct access)
- Tokens are stored in `httpOnly` cookies (handled by backend)
- The `SessionManager` component handles session expiry and refresh
