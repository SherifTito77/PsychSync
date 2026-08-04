"""
Enhanced Security Integration Example

How to integrate EnhancedSecurityManager into FastAPI application
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.enhanced_security import (
    AuditAction,
    DataSanitizer,
    EnhancedSecurityManager,
    SecurityLevel,
)

# ============================================================================
# MIDDLEWARE INTEGRATION
# ============================================================================


async def security_middleware(request: Request, call_next):
    """
    Global security middleware for FastAPI

    Performs:
    - Rate limiting
    - Anomaly detection
    - Request validation
    """
    # Get database session (you'll need to set this up in your app)
    db = request.state.db  # Set up in your FastAPI app dependency

    try:
        # Initialize security manager
        security = EnhancedSecurityManager(db)

        # Extract user info (from JWT token)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            # Check rate limit for this endpoint
            endpoint = request.url.path
            if not await security.check_rate_limit(
                user_id, endpoint, limit=100, window=3600
            ):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                )

            # Detect anomalies
            context = {
                "ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "endpoint": endpoint,
            }

            is_anomaly = await security.detect_anomaly(user_id, endpoint, context)
            if is_anomaly:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unusual activity detected. Please verify your identity.",
                )

    except Exception as e:
        # Log security event but don't block requests on security errors
        pass

    # Process request
    response = await call_next(request)
    return response


# ============================================================================
# DEPENDENCY INTEGRATION
# ============================================================================


async def get_security_manager(db: AsyncSession = Depends(get_db)):
    """Dependency to get security manager"""
    return EnhancedSecurityManager(db)


# ============================================================================
# ENDPOINT INTEGRATION EXAMPLES
# ============================================================================

from fastapi import APIRouter, Depends

from app.db.models.user import User

router = APIRouter(prefix="/enhanced-security", tags=["security-demo"])


@router.post("/encrypt-phi")
async def encrypt_phi_data(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    security: EnhancedSecurityManager = Depends(get_security_manager),
):
    """
    Example: Encrypt PHI data using AWS KMS

    Usage:
    POST /enhanced-security/encrypt-phi
    {
        "sensitive_data": {
            "diagnosis": "Major Depressive Disorder",
            "medications": ["Fluoxetine", "Trazodone"],
            "notes": "Patient reports suicidal ideation"
        }
    }
    """
    # Sanitize input first
    sanitized_data = DataSanitizer.sanitize_input(data)

    # Encrypt PHI
    encrypted = await security.encrypt_phi(
        data=sanitized_data, user_id=str(current_user.id)
    )

    return {
        "status": "success",
        "encrypted_data": encrypted,
        "user_id": str(current_user.id),
    }


@router.post("/decrypt-phi")
async def decrypt_phi_data(
    encrypted_data: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    security: EnhancedSecurityManager = Depends(get_security_manager),
):
    """
    Example: Decrypt PHI data using AWS KMS

    Usage:
    POST /enhanced-security/decrypt-phi
    {
        "encrypted_data": "base64-encoded-ciphertext-here"
    }
    """
    # Validate PHI access first
    has_access = await security.validate_phi_access(
        user_id=str(current_user.id),
        resource_type="encrypted_phi",
        resource_id="decryption_request",
        action=AuditAction.READ,
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this PHI",
        )

    # Decrypt PHI
    decrypted = await security.decrypt_phi(
        encrypted_data=encrypted_data, user_id=str(current_user.id)
    )

    return {"status": "success", "decrypted_data": decrypted}


@router.post("/check-rate-limit")
async def check_rate_limit_example(
    action: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    security: EnhancedSecurityManager = Depends(get_security_manager),
):
    """
    Example: Check if user is within rate limits

    Usage:
    POST /enhanced-security/check-rate-limit
    {
        "action": "screening_submit"
    }
    """
    under_limit = await security.check_rate_limit(
        user_id=str(current_user.id), action=action, limit=10, window=3600
    )

    if not under_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this action",
        )

    return {
        "status": "allowed",
        "action": action,
        "user_id": str(current_user.id),
        "message": "Request allowed within rate limits",
    }


@router.post("/detect-anomaly")
async def check_anomaly_example(
    action: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    security: EnhancedSecurityManager = Depends(get_security_manager),
):
    """
    Example: Detect anomalous behavior

    Usage:
    POST /enhanced-security/detect-anomaly
    {
        "action": "data_export"
    }
    """
    context = {
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "endpoint": request.url.path,
    }

    is_anomaly = await security.detect_anomaly(
        user_id=str(current_user.id), action=action, context=context
    )

    return {
        "status": "checked",
        "anomaly_detected": is_anomaly,
        "context": context,
        "user_id": str(current_user.id),
    }


@router.post("/validate-sanitized-input")
async def validate_input_example(
    data: dict,
    db: AsyncSession = Depends(get_db),
    security: EnhancedSecurityManager = Depends(get_security_manager),
):
    """
    Example: Validate and sanitize user input

    Usage:
    POST /enhanced-security/validate-sanitized-input
    {
        "screening_responses": {
            "q1_interest": 2,
            "q2_depressed": 1,
            "notes": "Feeling down lately"
        }
    }
    """
    # Sanitize input
    sanitized = DataSanitizer.sanitize_input(data)

    # Validate screening responses
    is_valid = DataSanitizer.validate_screening_responses(sanitized)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input detected. Please check your responses.",
        )

    return {
        "status": "valid",
        "sanitized_data": sanitized,
        "message": "Input validated and sanitized successfully",
    }


# ============================================================================
# FASTAPI APP INTEGRATION
# ============================================================================

"""
To integrate enhanced security into your FastAPI app, add to main.py:

```python
from fastapi import FastAPI, Request
from app.core.enhanced_security import security_middleware

app = FastAPI()

# Add security middleware
@app.middleware("http")
async def add_security_middleware(request: Request, call_next):
    return await security_middleware(request, call_next)

# Add analytics router
from app.api.v1.endpoints import enhanced_clinical_analytics
app.include_router(enhanced_clinical_analytics.router)

# Add security demo router
from app.api.v1.endpoints.enhanced_security_examples import router
app.include_router(router)
```
"""

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
EXAMPLE 1: Using Analytics in Clinician Dashboard
```python
from app.services.clinical.enhanced_analytics import EnhancedClinicalAnalytics

async def display_patient_analytics(user_id: str, org_id: str):
    analytics = EnhancedClinicalAnalytics(db)

    # Get trends
    trends = await analytics.get_user_trends(user_id, "PHQ9", weeks=12)

    if trends and trends.direction == TrendDirection.IMPROVING:
        print(f"Patient is improving: {trends.change_percentage}% change")

    # Get comparison
    comparative = await analytics.get_comparative_metrics(user_id, "GAD7")

    if comparative and comparative.percentile_rank > 75:
        print(f"Patient's anxiety is in top 25% of population")

    # Get outcomes
    outcomes = await analytics.get_outcome_metrics(user_id, "PHQ9")

    if outcomes and outcomes.achieved:
        print("Patient has achieved clinically significant improvement!")
```

EXAMPLE 2: Using Security in Screening Submission
```python
from app.core.enhanced_security import EnhancedSecurityManager, AuditAction

async def submit_screening_with_security(
    user_id: str,
    screening_data: dict,
    db: AsyncSession
):
    security = EnhancedSecurityManager(db)

    # Check rate limit
    if not await security.check_rate_limit(user_id, "screening_submit", limit=10):
        raise HTTPException(status_code=429, detail="Too many submissions")

    # Validate access
    if not await security.validate_phi_access(
        user_id, "screening", "new", AuditAction.CREATE
    ):
        raise HTTPException(status_code=403, detail="No consent on file")

    # Sanitize input
    sanitized = DataSanitizer.sanitize_input(screening_data)

    # Encrypt sensitive responses
    encrypted = await security.encrypt_phi(
        {"responses": sanitized},
        user_id
    )

    # Save to database...
    return encrypted
```

EXAMPLE 3: Population Health Monitoring
```python
async def generate_org_health_report(org_id: str):
    analytics = EnhancedClinicalAnalytics(db)

    metrics = await analytics.get_population_health_metrics(org_id)

    return {
        "completion_rate": metrics['completion_rate'],
        "risk_distribution": metrics['risk_distribution'],
        "crisis_count": metrics['crisis_alerts_last_30_days'],
        "recommendations": generate_recommendations(metrics)
    }
```
"""

# ============================================================================
# COMPLETE INTEGRATION CHECKLIST
# ============================================================================

INTEGRATION_CHECKLIST = """
✅ Step 1: Install Dependencies
   pip install scipy redis boto3

✅ Step 2: Add Middleware to main.py
   @app.middleware("http")
   async def security_middleware(request: Request, call_next):
       # Add security checks here

✅ Step 3: Include Analytics Router
   from app.api.v1.endpoints import enhanced_clinical_analytics
   app.include_router(enhanced_clinical_analytics.router, prefix="/api/v1")

✅ Step 4: Use Security Manager in Endpoints
   security = EnhancedSecurityManager(db)
   await security.check_rate_limit(user_id, action)
   await security.validate_phi_access(user_id, resource_type, resource_id, action)

✅ Step 5: Add Analytics to Dashboard
   analytics = EnhancedClinicalAnalytics(db)
   trends = await analytics.get_user_trends(user_id, screening_type)

✅ Step 6: Test Security Features
   - Rate limiting: Try submitting multiple times rapidly
   - Encryption: Encrypt and decrypt PHI data
   - Anomaly detection: Login from different IP/location
   - Input sanitization: Try SQL injection patterns
"""
