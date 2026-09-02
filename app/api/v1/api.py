# app/api/v1/api.py
"""
PsychSync API v1 Router - Static endpoint registration.

All core endpoints use explicit imports that fail loudly at startup.
Optional feature endpoints use try/except so one broken module doesn't
bring down the entire server, but failures ARE logged as errors.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api/v1", tags=["PsychSync API v1"])


def _try_include(module_path: str, name: str) -> bool:
    """Import an optional endpoint module and include it if available."""
    try:
        import importlib

        mod = importlib.import_module(module_path)
        router = getattr(mod, "router", None)
        if router is None:
            logger.error("Module %s has no 'router' attribute", name)
            return False
        api_router.include_router(router)
        logger.debug(
            "Registered optional endpoint: %s (%d routes)", name, len(router.routes)
        )
        return True
    except Exception as exc:
        logger.error("Failed to load optional endpoint '%s': %s", name, exc)
        return False


# =============================================================================
# CORE ENDPOINTS — static imports, fail loudly at startup if broken
# =============================================================================

from app.api.v1.endpoints.auth_unified import router as _auth_unified_router
from app.api.v1.endpoints.simple_auth import router as _simple_auth_router
from app.api.v1.endpoints.health import router as _health_router
from app.api.v1.endpoints.users import router as _users_router
from app.api.v1.endpoints.admin import router as _admin_router
from app.api.v1.endpoints.dns_security import router as _dns_security_router
from app.api.v1.endpoints.security_monitoring import (
    router as _security_monitoring_router,
)
from app.api.v1.endpoints.docs_local import router as _docs_local_router
from app.api.v1.endpoints.security_monitoring_public import (
    router as _security_monitoring_public_router,
)

api_router.include_router(_auth_unified_router)
api_router.include_router(_simple_auth_router)
api_router.include_router(_health_router)
api_router.include_router(_users_router)
api_router.include_router(_admin_router)
api_router.include_router(_dns_security_router)
api_router.include_router(_security_monitoring_router)
api_router.include_router(_docs_local_router)
api_router.include_router(_security_monitoring_public_router)

# =============================================================================
# FEATURE ENDPOINTS — optional, logged as errors if broken but server still starts
# =============================================================================

_FEATURE_ENDPOINTS = [
    "frontend_logs",
    "client_errors",
    "assessments",
    "responses",
    "clinical_analytics",
    "notifications",
    "ai_analytics",
    "ai_monitoring",
    "gdpr",
    "sql_audit",
    "query_performance",
    "build_analysis",
    "caching_config",
    "breaking_changes",
    "corporate_integrations",
    "toxic_behavior_detection",
    "legal_rights",
    "discrimination_analysis",
    "anonymous_feedback",
    "teams",
    "team_optimization",
    "predictions",
    "analytics",
    "reliability_validity",
    "encryption",
    "audit",
    "rbac",
    "ai_agents",
    "product_management",
    "executive_burnout",
    "radar",
    "advanced_burnout_analytics",
    "safety",
    "jira_integration",
    "pull_requests",
    "settings",
    "anomaly_detection",
    "code_quality",
    "wellness",
    "behavioral_user_dashboard",
    "email_connector",
    "hris_connector",
    "security_analytics",
    "corporate_psychology",
    "performance_monitoring",
    "telehealth",
    "behavioral_intelligence",
    "executive_intelligence",
    "org_digital_twin",
    "manager_intelligence",
    "organizational_network",
    "organizational_pulse",
    "work_systems",
    "ai_behavioral_coach",
    "calendar_integration",
    "communication_analytics",
    "scheduled_reports",
    "clinical_resources",
    "succession_planning",
    "ai",
    "heuristic",
    "monitoring",
    "behavioral_patterns",
    "burnout_predictions",
    "backups",
    "voice_video_analysis",
    "okr",
    "peer_recognition",
    "ona_alerts",
    "okr_health",
    "interventions",
    "slack_events",
    "org_chat",
    "narrative_reports",
    "benchmarks",
    "pulse_survey",
    "action_plans",
    "onboarding_analytics",
    "feedback_360",
    "meeting_effectiveness",
    "external_benchmarks",
    "nudge_bot",
    "skills",
    "change_impact",
    "survey_translations",
    "email_metadata",
    "slack_metadata",
    "teams_metadata",
    "computer_usage_metadata",
    "badge_access_metadata",
    "pto_patterns",
    "git_metadata",
    "toxicity_burnout",
    "video_conference_metadata",
    "knowledge_base_metadata",
]

_SEPARATED_SERVICE_ENDPOINTS = [
    "personality_assessments",
    "behavioral_analysis",
    "clinical_assessments",
    "clinical_assessments_extended",
    "clinical_ml_predictions",
    "population_health",
    "automated_alerts",
    "push_notifications",
    "biometric_auth",
    "screening",
    "health_monitoring",
    "biometric_integrations",
]

_BASE = "app.api.v1.endpoints"
_loaded = sum(
    _try_include(f"{_BASE}.{name}", name)
    for name in _FEATURE_ENDPOINTS + _SEPARATED_SERVICE_ENDPOINTS
)

logger.info(
    "API router initialized: %d core + %d/%d optional endpoints registered (%d total routes)",
    9,
    _loaded,
    len(_FEATURE_ENDPOINTS) + len(_SEPARATED_SERVICE_ENDPOINTS),
    len(api_router.routes),
)
