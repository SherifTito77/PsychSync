# app/api/v1/api.py
"""
Improved API router for PsychSync AI v1 endpoints
Clean, modular endpoint inclusion with proper error handling
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)


def safe_import_endpoint(module_name: str) -> APIRouter | None:
    """Safely import an endpoint module with proper error handling"""
    try:
        module = __import__(f"app.api.v1.endpoints.{module_name}", fromlist=[module_name])
        router = getattr(module, "router", None)
        if router is None:
            logger.warning(f"Module {module_name} imported but no router found")
            return None
        logger.info(f"Successfully imported endpoint: {module_name}")
        return router
    except ImportError as e:
        logger.warning(f"Could not import endpoint {module_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error importing endpoint {module_name}: {e}")
        return None


# Core endpoints (always required)
CORE_ENDPOINTS = [
    # SECURITY: standalone_auth disabled - backdoor endpoint allowing any login
    # This is a TEST endpoint that bypasses proper authentication
    # TODO: Delete standalone_auth.py entirely after confirming no dependencies
    # "standalone_auth",  # ❌ DISABLED - Security backdoor
    "simple_auth",  # ✅ ENABLED - Simple auth without CSRF requirements
    # Temporarily disabled due to syntax errors:
    # "users",  # ❌ unterminated string literal at line 41
    # "admin",  # ❌ invalid syntax at line 76
    # "dns_security",  # ❌ invalid syntax at line 86
    # "security_monitoring",  # ❌ invalid syntax at line 193
    "docs_local",  # ✅ NEW: Local documentation (no CDN dependencies)
    "security_monitoring_public",  # ✅ NEW: Security monitoring dashboard API
    "auth_unified",  # ✅ NEW: Unified auth with MFA support (replaces auth.py)
    # "auth",  # ⚠️ TEMPORARILY DISABLED - Using auth_unified instead
    "health",  # ✅ Health check endpoint
    # "two_factor_auth",  # ⚠️ DISABLED - MFA now integrated in auth_unified
    # "database_security"  # TEMPORARILY DISABLED - has syntax error on line 306
]

# Broken endpoints that need fixing (made optional for now)
BROKEN_ENDPOINTS = [
    # "standalone_auth",  # ❌ DISABLED - Security backdoor (accepts any credentials)
    # "simple_auth",  # ✅ MOVED TO CORE_ENDPOINTS - Now working
    "users",
    "admin",
    "dns_security",
    "security_monitoring",
]

# Feature endpoints (optional, can fail gracefully)
FEATURE_ENDPOINTS = [
    # Temporarily minimized for debugging - enabling only essential endpoints
    "assessments",
    "responses",
    "ai_analytics",  # NEW: AI-enhanced analytics endpoints
    "ai_monitoring",  # NEW: AI engine monitoring endpoints
    "gdpr",  # GDPR compliance endpoints
    "sql_audit",  # NEW: SQL injection vulnerability scanning
    "query_performance",  # NEW: Slow query optimization and analysis
    "build_analysis",  # NEW: Build failure analysis and root cause detection
    "caching_config",  # NEW: Caching configuration optimization
    "breaking_changes",  # NEW: Breaking changes detection before merge
    "corporate_integrations",  # ✅ ENABLED - Corporate data source integrations
    "toxic_behavior_detection",  # ✅ NEW: Toxic behavior detection and prevention
    # Temporarily disabled potentially problematic endpoints:
    # "teams",
    # "team_optimization",
    # "predictions",
    # "reliability_validity",
    # "csrf",
    # "analytics",
    # "backups",
    # "scoring",
    # "succession_planning",
    # "longitudinal_analysis",
    # "nlp_routes",
    # "users_gdpr",
    # "email_connections",
    # "email_simple",
    # "onboarding"  # NEW: Value-first onboarding endpoints
    # "assessment_results",  # NEW: Comprehensive assessment results API - temporarily disabled due to syntax error
    # "billing",  # NEW: Revenue generation and subscription management
    # "enterprise_sales"  # NEW: B2B account management and customer success
]

# Separated Service Areas (NEW: Five distinct service areas)
SEPARATED_SERVICE_ENDPOINTS = [
    "personality_assessments",  # MBTI, Enneagram, Big Five, etc.
    # "behavioral_analysis",         # Behavioral patterns, anomaly detection - temporarily disabled due to import issues
    "clinical_assessments",  # Mental health screening, wellness
    "screening",  # NEW: Clinical screening tools (PHQ-9, GAD-7, C-SSRS) with crisis intervention
    "health_monitoring",  # NEW: Real-time stress & burnout monitoring with automated interventions
    # "email_connector",            # Email integration and analytics - temporarily disabled due to missing schemas
    # "hris_connector",             # HR system integration and workforce analytics - temporarily disabled due to syntax errors
    # Temporarily disabled new analytics:
    # "growth_analytics"            # Advanced growth analytics and conversion optimization
]

# Create the main API router
api_router = APIRouter(prefix="/api/v1", tags=["PsychSync API v1"])


def register_endpoints(router: APIRouter, endpoints: list[str], required: bool = True) -> None:
    """Register endpoints with the main router"""
    failed_imports = []

    for endpoint_name in endpoints:
        endpoint_router = safe_import_endpoint(endpoint_name)
        if endpoint_router:
            router.include_router(endpoint_router)
        elif required:
            failed_imports.append(endpoint_name)

    if failed_imports and required:
        error_msg = f"Failed to import required endpoints: {', '.join(failed_imports)}"
        logger.error(error_msg)
        raise ImportError(error_msg)


# Register core endpoints (required)
register_endpoints(api_router, CORE_ENDPOINTS, required=True)

# Register feature endpoints (optional)
register_endpoints(api_router, FEATURE_ENDPOINTS, required=False)

# Register separated service area endpoints (NEW)
register_endpoints(api_router, SEPARATED_SERVICE_ENDPOINTS, required=False)

# Attempt to register broken endpoints (optional - won't fail if they have syntax errors)
register_endpoints(api_router, BROKEN_ENDPOINTS, required=False)

# Log final status
logger.info(f"API router initialized with {len(api_router.routes)} routes")

# TODO(human): Implement dynamic endpoint registration
# Context: The current endpoint registration is static and requires manual updates
# Your task is to implement dynamic endpoint discovery and registration
#
# Guidance:
# 1. Scan the endpoints directory for Python files
# 2. Automatically import and register modules that contain a 'router' object
# 3. Add configuration for enabling/disabling endpoints via settings
# 4. Implement health check for registered endpoints
# 5. Add version compatibility checking for endpoints
#
# The system should support:
# - Hot-loading of endpoints in development
# - Endpoint dependency management
# - Automatic endpoint health monitoring
# - Configuration-driven endpoint enablement
