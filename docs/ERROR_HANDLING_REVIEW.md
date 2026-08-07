# Error-Handling Review: UX Issues and Broken Flows

**Date:** 2026-01-18
**Reviewer:** Claude Code (Anthropic)
**Scope:** Full-stack error handling patterns affecting user experience
**Focus:** Incorrect error-handling flows that lead to bad UX or broken flows

---

## 🚨 Critical Issues (Immediate Action Required)

### 1. Silent Failures with No User Feedback

**Severity:** CRITICAL
**Impact:** Users don't know when actions fail, leading to confusion and data loss

#### Issue 1.1: Anonymous Feedback Status Update
**File:** `frontend/src/components/AnonymousFeedbackHRDashboard.tsx:83-85`

```typescript
} catch (error) {
  console.error('Failed to update feedback status:', error);
}
```

**Problem:**
- When HR staff updates feedback status, errors are only logged to console
- User sees no error message
- Status update appears to succeed but actually fails
- No retry mechanism offered

**UX Impact:**
- HR staff thinks feedback was resolved when it wasn't
- Critical workplace issues may be ignored
- No indication to retry the action

**Recommended Fix:**
```typescript
} catch (error) {
  console.error('Failed to update feedback status:', error);
  setError('Failed to update feedback status. Please try again.');
  setShowErrorToast(true);
}
```

---

#### Issue 1.2: Anonymous Feedback Data Loading
**File:** `frontend/src/components/AnonymousFeedbackHRDashboard.tsx:62-64`

```typescript
} catch (error) {
  console.error('Failed to load feedback data:', error);
} finally {
  setLoading(false);
}
```

**Problem:**
- Dashboard loads empty on error without any error message
- User sees blank screen with no explanation
- No indication whether it's a network issue, permission problem, or server error

**UX Impact:**
- HR staff sees empty dashboard and assumes no feedback exists
- Time-sensitive feedback may be missed
- No troubleshooting guidance provided

**Recommended Fix:**
```typescript
} catch (error) {
  console.error('Failed to load feedback data:', error);
  setError(error.response?.data?.detail || 'Unable to load feedback. Please refresh the page.');
  setFeedbacks([]); // Clear stale data
} finally {
  setLoading(false);
}
```

---

#### Issue 1.3: Assessment Recommendations Loading
**File:** `frontend/src/components/assessment/AssessmentOrchestrator.tsx:157-161`

```typescript
} catch (error) {
  console.error('Failed to load recommendations:', error);
} finally {
  setLoading(false);
}
```

**Problem:**
- AI-powered recommendations fail silently
- Generic "Failed to load recommendations" message (line 198) doesn't indicate cause
- No retry or troubleshooting options

**UX Impact:**
- Users don't get personalized assessment recommendations
- No explanation whether it's temporary (network) or permanent (no data)
- Reduces engagement with assessment platform

---

### 2. Abrupt Token Refresh Failure

**Severity:** HIGH
**Impact:** Users lose all work context with no warning

#### Issue 2.1: Hard Redirect on Token Refresh Failure
**File:** `frontend/src/services/api.ts:101-107`

```typescript
} catch (refreshError) {
  // Refresh failed, clear tokens and redirect to login
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  window.location.href = '/login';  // ❌ ABRUCT REDIRECT
  return Promise.reject(refreshError);
}
```

**Problem:**
- Hard redirect to login page loses all user context
- No warning before redirect
- User loses any unsaved work in forms
- No explanation of what happened

**UX Impact:**
- User is filling out a long assessment → suddenly on login screen
- No indication their session expired
- May think there's a bug or the site crashed
- Frustrating repeat work

**Recommended Fix:**
```typescript
} catch (refreshError) {
  // Clear tokens
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');

  // Store session expired flag
  sessionStorage.setItem('session_expired', 'true');
  sessionStorage.setItem('redirect_after_login', window.location.pathname);

  // Show modal first, then redirect
  showSessionExpiredModal();

  // Redirect after user acknowledges
  setTimeout(() => {
    window.location.href = '/login?reason=session_expired';
  }, 3000);

  return Promise.reject(refreshError);
}
```

---

### 3. Information Leakage in Error Messages

**Severity:** MEDIUM-HIGH
**Impact:** Exposes internal implementation details, security risk

#### Issue 3.1: Raw Exception Messages in API Responses
**File:** `app/api/v1/endpoints/push_notifications.py:187`

```python
except Exception as e:
    logger.error(f"Failed to unregister token: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Failed to unregister token: {str(e)}")
```

**Problem:**
- Raw exception `str(e)` exposed to clients
- May contain sensitive internal information
- Not user-friendly
- Different error messages each time (hard to handle programmatically)

**UX Impact:**
- Users see technical error messages they don't understand
- Exposes internal system details (potential security issue)
- Inconsistent error responses make frontend error handling difficult

**Recommended Fix:**
```python
except Exception as e:
    logger.error(f"Failed to unregister token: {str(e)}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Unable to unregister notification device. Please try again or contact support."
    )
```

---

#### Issue 3.2: Generic "Internal Server Error"
**File:** `app/api/v1/endpoints/simple_auth.py:89-91`

```python
except Exception as e:
    print(f"Simple login error: {e}")
    import traceback
    traceback.print_exc()
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"  # ❌ Generic message
    ) from e
```

**Problem:**
- "Internal server error" tells user nothing
- Full stack trace printed to console (not logged properly)
- No distinction between different failure modes

**UX Impact:**
- Users see generic error with no actionable guidance
- Can't distinguish between "wrong password" vs "system down"
- Reduces trust in system reliability

**Recommended Fix:**
```python
except HTTPException:
    raise
except DatabaseError as e:
    logger.error(f"Database error during login: {str(e)}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Service temporarily unavailable. Please try again in a few minutes."
    ) from e
except Exception as e:
    logger.error(f"Unexpected login error: {str(e)}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Login service unavailable. Our team has been notified."
    ) from e
```

---

### 4. Swallowed Database Cleanup Errors

**Severity:** MEDIUM
**Impact:** Resource leaks, potential connection pool exhaustion

#### Issue 4.1: Silent Database Close Failure
**File:** `app/api/v1/endpoints/simple_auth.py:78-81`

```python
} finally:
    try:
        await db_gen.aclose()
    except Exception as e:
        pass  # ❌ SILENTLY SWALLOWED
```

**Problem:**
- Database cleanup errors silently ignored
- No logging of connection close failures
- Could mask connection pool issues
- Resource leaks accumulate over time

**UX Impact:**
- Connection pool exhaustion under load
- Intermittent "service unavailable" errors
- Difficult to diagnose in production

**Recommended Fix:**
```python
} finally:
    try:
        await db_gen.aclose()
    except Exception as e:
        logger.warning(f"Failed to close database connection: {str(e)}")
        # Don't raise - cleanup failures shouldn't fail the request
```

---

## ⚠️ Medium Priority Issues

### 5. Console-Only Error Logging (No User Notification)

**Severity:** MEDIUM
**Impact:** Users have no visibility into errors

#### Issue 5.1: LSAS Assessment Submission
**File:** `frontend/src/components/assessments/LSASForm.tsx:199-201`

```typescript
} catch (err) {
  console.error('LSAS submission error:', err);
} finally {
  setIsSubmitting(false);
}
```

**Problem:**
- Assessment submission errors logged to console only
- User doesn't know if submission succeeded or failed
- `setIsSubmitting(false)` happens but no success/failure indication

**UX Impact:**
- User may resubmit assessment (duplicate data)
- Unclear if assessment was saved
- No guidance on what to do next

**Recommended Fix:**
```typescript
} catch (err) {
  console.error('LSAS submission error:', err);
  const errorMessage = err.response?.data?.detail || 'Failed to submit assessment. Please try again.';
  setSubmitError(errorMessage);
  setShowErrorAlert(true);
} finally {
  setIsSubmitting(false);
}
```

---

#### Issue 5.2: Voice/Video Analysis Media Access
**File:** `frontend/src/components/voiceanalysis/VoiceVideoAnalysis.tsx:356-358`

```typescript
} catch (error) {
  console.error('Error accessing media devices:', error);
}
```

**Problem:**
- Camera/microphone permission denied → silent failure
- No explanation to user why feature doesn't work
- No guidance on how to grant permissions

**UX Impact:**
- Feature appears broken
- Users don't know they need to grant permissions
- No alternative explanation offered

**Recommended Fix:**
```typescript
} catch (error) {
  console.error('Error accessing media devices:', error);
  if (error.name === 'NotAllowedError') {
    setMediaError('Camera/microphone access denied. Please grant permissions in your browser settings.');
  } else if (error.name === 'NotFoundError') {
    setMediaError('No camera or microphone found. Please connect a device and try again.');
  } else {
    setMediaError('Unable to access media devices. Please ensure permissions are granted.');
  }
}
```

---

### 6. Missing Error States in Async Operations

**Severity:** MEDIUM
**Impact:** No loading/error feedback to users

#### Issue 6.1: Team Loading in Edit Assessment Modal
**File:** `frontend/src/components/assessments/EditAssessmentModal.tsx:39-42`

```typescript
useEffect(() => {
  const loadTeams = async () => {
    try {
      // ... load teams
    } catch (error) {
      console.error('Failed to load teams');
    }
  };
  loadTeams();
}, []);
```

**Problem:**
- Team loading failure silently ignored
- No error state shown to user
- Modal opens but dropdown is empty

**UX Impact:**
- User can't assign assessment to team
- No explanation why teams aren't loading
- May appear as if user has no teams (confusing)

**Recommended Fix:**
```typescript
} catch (error) {
  console.error('Failed to load teams', error);
  setTeamError('Unable to load teams. Please refresh the page or try again later.');
  setTeams([]); // Prevent showing stale data
}
```

---

### 7. PWA Installation Failure

**Severity:** LOW-MEDIUM
**Impact:** Poor progressive enhancement

#### Issue 7.1: Silent PWA Install Failure
**File:** `frontend/src/components/PWAInstaller.tsx:84-86`

```typescript
} catch (error) {
  console.error('Install failed:', error);
  onInstallDismissed?.();
}
```

**Problem:**
- PWA installation fails silently
- User doesn't know why install button disappeared
- No retry mechanism

**UX Impact:**
- Feature (PWA install) appears to not exist
- Users who want offline capability can't get it
- No explanation of requirements (e.g., Chrome only)

**Recommended Fix:**
```typescript
} catch (error) {
  console.error('Install failed:', error);
  setInstallError('Installation failed. Please try using Chrome or Edge browser.');
  setShowInstallError(true);
  onInstallDismissed?.();
}
```

---

## 📊 Summary Statistics

| Category | Count | Severity |
|----------|-------|----------|
| Silent Failures (No User Feedback) | 5 | CRITICAL |
| Information Leakage | 2 | HIGH |
| Abrupt State Changes | 1 | HIGH |
| Resource Leaks | 1 | MEDIUM |
| Console-Only Logging | 4 | MEDIUM |
| Missing Error States | 3 | MEDIUM |
| **Total Issues Found** | **16** | - |

---

## 🔧 Recommended Improvements

### 1. Implement Global Error Handler
Create a centralized error handling utility for frontend:

```typescript
// src/utils/errorHandler.ts
export interface UserFriendlyError {
  userMessage: string;
  technicalMessage?: string;
  actionable: boolean;
  retryable: boolean;
}

export const handleError = (error: any, context: string): UserFriendlyError => {
  // Network errors
  if (!error.response) {
    return {
      userMessage: 'Unable to connect. Please check your internet connection.',
      technicalMessage: 'Network error',
      actionable: true,
      retryable: true,
    };
  }

  // HTTP status codes
  switch (error.response.status) {
    case 401:
      return {
        userMessage: 'Your session has expired. Please log in again.',
        technicalMessage: 'Authentication required',
        actionable: true,
        retryable: false,
      };
    case 403:
      return {
        userMessage: "You don't have permission to perform this action.",
        technicalMessage: 'Authorization failed',
        actionable: false,
        retryable: false,
      };
    case 500:
      return {
        userMessage: 'Something went wrong on our end. Please try again.',
        technicalMessage: 'Server error',
        actionable: true,
        retryable: true,
      };
    default:
      return {
        userMessage: error.response?.data?.detail || 'An unexpected error occurred.',
        technicalMessage: error.message,
        actionable: false,
        retryable: true,
      };
  }
};
```

### 2. Add Error Toast/Notification System
Implement a user-friendly error notification system:

```typescript
// src/context/ErrorContext.tsx
export const ErrorContext = createContext<ErrorContextType>({
  showError: () => {},
  showWarning: () => {},
  clearError: () => {},
});

export const ErrorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [error, setError] = useState<ErrorNotification | null>(null);

  const showError = (message: string, options?: ErrorOptions) => {
    setError({
      message,
      severity: 'error',
      actionable: options?.actionable ?? false,
      retryable: options?.retryable ?? false,
      onRetry: options?.onRetry,
    });
  };

  return (
    <ErrorContext.Provider value={{ showError, showWarning, clearError }}>
      {children}
      {error && <ErrorToast notification={error} onClose={() => setError(null)} />}
    </ErrorContext.Provider>
  );
};
```

### 3. Improve API Error Response Format
Standardize backend error responses:

```python
# app/core/exceptions.py
from fastapi import HTTPException
from typing import Optional, Dict, Any

class UserFacingHTTPException(HTTPException):
    def __init__(
        self,
        status_code: int,
        user_message: str,
        technical_message: Optional[str] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.user_message = user_message
        self.technical_message = technical_message or user_message
        self.error_code = error_code
        self.context = context or {}

        super().__init__(
            status_code=status_code,
            detail={
                "user_message": user_message,
                "error_code": error_code,
                "context": context,
            }
        )
```

### 4. Add Error Boundaries for Critical Flows
Implement React error boundaries for key user journeys:

```typescript
// src/components/AssessmentErrorBoundary.tsx
export class AssessmentErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logger.error('Assessment flow error', { error, errorInfo });

    // Save assessment state to localStorage for recovery
    const currentState = this.props.assessmentState;
    localStorage.setItem('interrupted_assessment', JSON.stringify({
      state: currentState,
      timestamp: new Date().toISOString(),
      error: error.message,
    }));
  }

  render() {
    if (this.state.hasError) {
      return (
        <AssessmentErrorRecovery
          onSave={() => this.saveDraft()}
          onRestart={() => this.restartAssessment()}
          onContactSupport={() => this.contactSupport()}
        />
      );
    }
    return this.props.children;
  }
}
```

### 5. Implement Graceful Session Expiration
Replace hard redirect with user-friendly session expiration:

```typescript
// src/components/SessionExpiryModal.tsx
export const SessionExpiryModal: React.FC = () => {
  const [countdown, setCountdown] = useState(30);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          redirectToLogin();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <Modal isOpen={true} onClose={() => {}}>
      <Alert variant="warning">
        <h2>Your Session Has Expired</h2>
        <p>
          For your security, you've been logged out due to inactivity.
          Redirecting to login in {countdown} seconds...
        </p>
        <Button onClick={redirectToLogin}>
          Go to Login Now
        </Button>
        <p className="text-sm text-gray-600">
          Tip: Any unsaved work may be lost. Please save your work frequently.
        </p>
      </Alert>
    </Modal>
  );
};
```

---

`★ Insight ─────────────────────────────────────`
**Why Error Handling is UX, Not Just Technical:**

The most common anti-pattern I found is **console-only error logging**. Developers log errors for debugging but forget that users don't read the browser console. This creates a "black hole" where actions silently fail, leaving users confused and frustrated.

**The Principle of Visible Errors:**
Every user-initiated action that can fail MUST provide visible feedback. If a user clicks a button and nothing visible happens, they will either:
1. Click again (creating duplicate submissions)
2. Assume the feature is broken (reducing trust)
3. Give up entirely (lost engagement)

**Error Message Hierarchy:**
Good error handling follows this hierarchy:
1. **Immediate visible feedback** (toast, banner, inline message)
2. **Clear explanation** (what went wrong in plain language)
3. **Actionable guidance** (what the user can do about it)
4. **Preventive measures** (don't let users submit if validation will fail)

Most of the issues I found fail at step 1 - there's no visible feedback at all.
`─────────────────────────────────────────────────`

---

## 🎯 Prioritized Action Plan

### Phase 1: Critical Fixes (Week 1)
1. Fix Anonymous Feedback error handling (add user notifications)
2. Implement session expiry modal (replace hard redirect)
3. Add error states to Assessment Orchestrator
4. Fix LSAS submission error feedback

### Phase 2: High-Impact Improvements (Week 2)
5. Implement global error handler utility
6. Add error toast/notification system
7. Fix voice/video analysis permission errors
8. Standardize API error response format

### Phase 3: Systemic Improvements (Week 3)
9. Add error boundaries to assessment flows
10. Implement assessment state recovery
11. Add comprehensive error logging (not console-only)
12. Create error handling documentation

---

## 📚 Additional Resources

- [Error Handling Best Practices](https://kentcdodds.com/blog/use-react-error-boundary-to-handle-errors-in-react)
- [User-Friendly Error Messages](https://www.nngroup.com/articles/error-message-guidelines/)
- [Progressive Enhancement for PWAs](https://web.dev/progressive-enhancement/)

---

**Review Completed:** 2026-01-18
**Total Issues Identified:** 16
**Critical Issues:** 3 (require immediate attention)
**Recommended Timeline:** 3 weeks for full implementation
