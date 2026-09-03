"""
Module Classification Registry for PsychSync.

Every service and endpoint is classified into one of:
- CORE: Essential for product operation. Always enabled.
- OPTIONAL: Production-ready features that can be toggled.
- EXPERIMENTAL: In development, may change. Not for production.
- LEGACY: Superseded by newer implementations. Maintained for compatibility.
- CLINICAL: Requires special compliance (HIPAA). Separate deployment.
- DEPRECATED: Scheduled for removal. Do not build on.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ModuleClassification(str, Enum):
    CORE = "core"
    OPTIONAL = "optional"
    EXPERIMENTAL = "experimental"
    LEGACY = "legacy"
    CLINICAL = "clinical"
    DEPRECATED = "deprecated"


@dataclass
class ModuleInfo:
    name: str
    classification: ModuleClassification
    category: (
        str  # "auth", "intelligence", "connector", "analytics", "admin", "clinical"
    )
    description: str
    data_sources: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    api_prefix: str = ""
    enterprise_tier: str = "free"  # "free", "professional", "enterprise"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

MODULE_REGISTRY: Dict[str, ModuleInfo] = {
    # -----------------------------------------------------------------------
    # CORE — always enabled
    # -----------------------------------------------------------------------
    "auth": ModuleInfo(
        name="auth",
        classification=ModuleClassification.CORE,
        category="auth",
        description="JWT authentication, MFA, session management",
        data_sources=["users_table"],
        api_prefix="/api/v1/auth",
        enterprise_tier="free",
    ),
    "organizations": ModuleInfo(
        name="organizations",
        classification=ModuleClassification.CORE,
        category="admin",
        description="Organization CRUD and hierarchy",
        data_sources=["organizations_table"],
        depends_on=["auth"],
        api_prefix="/api/v1/organizations",
        enterprise_tier="free",
    ),
    "users": ModuleInfo(
        name="users",
        classification=ModuleClassification.CORE,
        category="admin",
        description="User CRUD and profile management",
        data_sources=["users_table"],
        depends_on=["auth"],
        api_prefix="/api/v1/users",
        enterprise_tier="free",
    ),
    "teams": ModuleInfo(
        name="teams",
        classification=ModuleClassification.CORE,
        category="admin",
        description="Team CRUD and membership management",
        data_sources=["teams_table", "team_members_table"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/teams",
        enterprise_tier="free",
    ),
    "assessments": ModuleInfo(
        name="assessments",
        classification=ModuleClassification.CORE,
        category="analytics",
        description="Assessment CRUD, templates, and scoring (optional enrichment, not primary data)",
        data_sources=["assessments_table", "responses_table"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/assessments",
        enterprise_tier="free",
    ),
    "security_audit": ModuleInfo(
        name="security_audit",
        classification=ModuleClassification.CORE,
        category="admin",
        description="Audit logging and security event tracking",
        data_sources=["audit_logs_table"],
        depends_on=["auth"],
        api_prefix="/api/v1/audit",
        enterprise_tier="free",
    ),
    # -----------------------------------------------------------------------
    # OPTIONAL — Intelligence Engines (enterprise)
    # -----------------------------------------------------------------------
    "behavioral_intelligence": ModuleInfo(
        name="behavioral_intelligence",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Behavioral Intelligence scores (team health, collaboration, burnout risk, etc.)",
        data_sources=[
            "assessments",
            "enrichment_signals",
            "pulse_surveys",
            "feedback_360",
            "meetings",
        ],
        depends_on=["auth", "organizations", "teams"],
        api_prefix="/api/v1/behavioral-intelligence",
        enterprise_tier="enterprise",
    ),
    "organizational_pulse": ModuleInfo(
        name="organizational_pulse",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Predictive 7-question organizational pulse engine",
        data_sources=["bi_scores", "ona_snapshots", "temporal_signals"],
        depends_on=["auth", "organizations", "behavioral_intelligence"],
        api_prefix="/api/v1/pulse",
        enterprise_tier="enterprise",
    ),
    "organizational_network": ModuleInfo(
        name="organizational_network",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Organizational Network Analysis with Louvain community detection",
        data_sources=[
            "network_edges_table",
            "collaboration_surveys",
            "connector_edges",
        ],
        depends_on=["auth", "organizations", "teams"],
        api_prefix="/api/v1/organizational-network",
        enterprise_tier="enterprise",
    ),
    "org_digital_twin": ModuleInfo(
        name="org_digital_twin",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Organizational digital twin simulation",
        data_sources=["bi_scores", "ona_data", "okr_data", "recognition_data"],
        depends_on=["auth", "organizations", "behavioral_intelligence"],
        api_prefix="/api/v1/org-digital-twin",
        enterprise_tier="enterprise",
    ),
    "manager_intelligence": ModuleInfo(
        name="manager_intelligence",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Manager effectiveness composite (team outcomes, people dev, network, support)",
        data_sources=["bi_scores", "team_data", "feedback_360", "ona_data"],
        depends_on=["auth", "organizations", "behavioral_intelligence"],
        api_prefix="/api/v1/manager-intelligence",
        enterprise_tier="enterprise",
    ),
    "executive_intelligence": ModuleInfo(
        name="executive_intelligence",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="C-suite analytics and executive dashboard",
        data_sources=["bi_scores", "pulse_data", "hris_data"],
        depends_on=[
            "auth",
            "organizations",
            "behavioral_intelligence",
            "organizational_pulse",
        ],
        api_prefix="/api/v1/executive-intelligence",
        enterprise_tier="enterprise",
    ),
    "toxicity_burnout": ModuleInfo(
        name="toxicity_burnout",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Composite toxicity and burnout risk engine with cross-contamination detection",
        data_sources=[
            "toxicity_signals",
            "passive_burnout_signals",
            "metadata_signals",
        ],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/toxicity-burnout",
        enterprise_tier="enterprise",
    ),
    "change_impact": ModuleInfo(
        name="change_impact",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Reorganization impact prediction and change readiness",
        data_sources=["ona_data", "bi_scores", "team_data"],
        depends_on=["auth", "organizations", "organizational_network"],
        api_prefix="/api/v1/change-impact",
        enterprise_tier="enterprise",
    ),
    "skills_graph": ModuleInfo(
        name="skills_graph",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Skill inventory and gap analysis graph",
        data_sources=["assessments", "team_data"],
        depends_on=["auth", "organizations", "teams"],
        api_prefix="/api/v1/skills",
        enterprise_tier="enterprise",
    ),
    # -----------------------------------------------------------------------
    # OPTIONAL — Data Connectors (professional)
    # -----------------------------------------------------------------------
    "hris_connector": ModuleInfo(
        name="hris_connector",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="HRIS workforce data connector (employee records, turnover)",
        data_sources=["hris_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/hris",
        enterprise_tier="professional",
    ),
    "calendar_metadata": ModuleInfo(
        name="calendar_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Calendar meeting pattern analysis (metadata only)",
        data_sources=["calendar_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/calendar",
        enterprise_tier="professional",
    ),
    "email_metadata": ModuleInfo(
        name="email_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Email volume, timing, and response pattern analysis (metadata only)",
        data_sources=["email_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/email-metadata",
        enterprise_tier="professional",
    ),
    "slack_metadata": ModuleInfo(
        name="slack_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Slack channel breadth, DM ratio, context switching analysis (metadata only)",
        data_sources=["slack_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/slack-metadata",
        enterprise_tier="professional",
    ),
    "teams_metadata": ModuleInfo(
        name="teams_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Microsoft Teams chat, call, and meeting fatigue analysis (metadata only)",
        data_sources=["teams_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/teams-metadata",
        enterprise_tier="professional",
    ),
    "git_metadata": ModuleInfo(
        name="git_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Git/GitHub commit timing, PR lifecycle, code churn analysis (metadata only)",
        data_sources=["git_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/git-metadata",
        enterprise_tier="professional",
    ),
    "computer_usage_metadata": ModuleInfo(
        name="computer_usage_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Computer activity levels, session duration, break deficit analysis (metadata only)",
        data_sources=["endpoint_agent"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/computer-usage-metadata",
        enterprise_tier="professional",
    ),
    "badge_access_metadata": ModuleInfo(
        name="badge_access_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Physical badge entry/exit, long days, weekend presence analysis (metadata only)",
        data_sources=["badge_system_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/badge-access-metadata",
        enterprise_tier="professional",
    ),
    "pto_patterns_metadata": ModuleInfo(
        name="pto_patterns_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="PTO vacation avoidance, cancellation rate, recovery deficit analysis",
        data_sources=["hris_api", "calendar_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/pto-patterns",
        enterprise_tier="professional",
    ),
    "video_conference_metadata": ModuleInfo(
        name="video_conference_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Video conference camera-on rate, join latency, meeting fatigue analysis",
        data_sources=["zoom_api", "meet_api", "teams_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/video-conference-metadata",
        enterprise_tier="professional",
    ),
    "knowledge_base_metadata": ModuleInfo(
        name="knowledge_base_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Documentation creation rate, contributor concentration, stale content analysis",
        data_sources=["confluence_api", "notion_api", "sharepoint_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/knowledge-base-metadata",
        enterprise_tier="professional",
    ),
    # -----------------------------------------------------------------------
    # OPTIONAL — Corporate Features (enterprise)
    # -----------------------------------------------------------------------
    "action_plans": ModuleInfo(
        name="action_plans",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="Intervention tracking with source tracking and effectiveness measurement",
        data_sources=["action_plans_table", "bi_scores"],
        depends_on=["auth", "organizations", "behavioral_intelligence"],
        api_prefix="/api/v1/action-plans",
        enterprise_tier="enterprise",
    ),
    "pulse_survey": ModuleInfo(
        name="pulse_survey",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="Micro-survey campaigns with 8 signals, syncs to BI and Wellness",
        data_sources=["pulse_survey_campaigns_table", "pulse_survey_responses_table"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/pulse-survey",
        enterprise_tier="enterprise",
    ),
    "feedback_360": ModuleInfo(
        name="feedback_360",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="360-degree peer feedback with privacy-safe aggregation and blind spot detection",
        data_sources=[
            "feedback_rounds_table",
            "feedback_requests_table",
            "feedback_responses_table",
        ],
        depends_on=["auth", "organizations", "teams"],
        api_prefix="/api/v1/feedback-360",
        enterprise_tier="enterprise",
    ),
    "meeting_effectiveness": ModuleInfo(
        name="meeting_effectiveness",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="Meeting quality ratings with tag frequency and organizer analytics",
        data_sources=["meeting_ratings_table"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/meeting-effectiveness",
        enterprise_tier="enterprise",
    ),
    "peer_recognition": ModuleInfo(
        name="peer_recognition",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="Kudos system with 7 recognition types, wired into Digital Twin engagement",
        data_sources=["peer_recognition_table"],
        depends_on=["auth", "organizations", "teams"],
        api_prefix="/api/v1/peer-recognition",
        enterprise_tier="enterprise",
    ),
    "okr": ModuleInfo(
        name="okr",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="Objectives and Key Results tracking with progress updates and retrospectives",
        data_sources=["objectives_table", "key_results_table", "okr_checkins_table"],
        depends_on=["auth", "organizations", "teams"],
        api_prefix="/api/v1/okr",
        enterprise_tier="enterprise",
    ),
    "external_benchmarks": ModuleInfo(
        name="external_benchmarks",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="Cross-tenant benchmarking with opt-in, Laplace DP noise, industry bucketing",
        data_sources=["benchmark_contributions_table", "benchmark_opt_ins_table"],
        depends_on=["auth", "organizations", "behavioral_intelligence"],
        api_prefix="/api/v1/external-benchmarks",
        enterprise_tier="enterprise",
    ),
    "nudge_bot": ModuleInfo(
        name="nudge_bot",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="Slack nudge bot with 5 nudge types, pull-based trigger model",
        data_sources=["slack_api", "bi_scores"],
        depends_on=[
            "auth",
            "organizations",
            "behavioral_intelligence",
            "slack_metadata",
        ],
        api_prefix="/api/v1/nudge-bot",
        enterprise_tier="enterprise",
    ),
    "onboarding_analytics": ModuleInfo(
        name="onboarding_analytics",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="New hire health from ONA, recognition, engagement, and wellness signals",
        data_sources=["ona_data", "recognition_data", "wellness_data"],
        depends_on=["auth", "organizations", "organizational_network"],
        api_prefix="/api/v1/onboarding-analytics",
        enterprise_tier="enterprise",
    ),
    "narrative_reports": ModuleInfo(
        name="narrative_reports",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="AI-generated narrative reports from intelligence data",
        data_sources=["bi_scores", "pulse_data", "ona_data"],
        depends_on=["auth", "organizations", "behavioral_intelligence"],
        api_prefix="/api/v1/narrative-reports",
        enterprise_tier="enterprise",
    ),
    "organizational_chat": ModuleInfo(
        name="organizational_chat",
        classification=ModuleClassification.OPTIONAL,
        category="analytics",
        description="Conversational AI for organizational intelligence queries",
        data_sources=["bi_scores", "pulse_data", "ona_data"],
        depends_on=["auth", "organizations", "behavioral_intelligence"],
        api_prefix="/api/v1/org-chat",
        enterprise_tier="enterprise",
    ),
    # -----------------------------------------------------------------------
    # OPTIONAL — Monitoring (enterprise)
    # -----------------------------------------------------------------------
    "calendar_toxicity": ModuleInfo(
        name="calendar_toxicity",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Calendar toxicity signals: speaking domination, 1:1 cancel, invite exclusion",
        data_sources=["calendar_api"],
        depends_on=["auth", "organizations", "calendar_metadata"],
        api_prefix="/api/v1/toxicity-burnout",
        enterprise_tier="enterprise",
    ),
    "code_review_toxicity": ModuleInfo(
        name="code_review_toxicity",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Code review toxicity: PR rejection rates, gatekeeping patterns",
        data_sources=["git_api"],
        depends_on=["auth", "organizations", "git_metadata"],
        api_prefix="/api/v1/toxicity-burnout",
        enterprise_tier="enterprise",
    ),
    "communication_toxicity": ModuleInfo(
        name="communication_toxicity",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Communication toxicity: reaction asymmetry, attrition clustering",
        data_sources=["slack_api", "teams_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/toxicity-burnout",
        enterprise_tier="enterprise",
    ),
    "ticket_metadata": ModuleInfo(
        name="ticket_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Ticket toxicity: hot potato patterns, work dumping detection",
        data_sources=["jira_api", "linear_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/toxicity-burnout",
        enterprise_tier="enterprise",
    ),
    "sso_metadata": ModuleInfo(
        name="sso_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="SSO passive burnout signals via Okta/AzureAD login patterns",
        data_sources=["okta_api", "azure_ad_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/toxicity-burnout",
        enterprise_tier="enterprise",
    ),
    "vpn_metadata": ModuleInfo(
        name="vpn_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="VPN passive burnout signals via Cisco/Zscaler session patterns",
        data_sources=["vpn_api"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/toxicity-burnout",
        enterprise_tier="enterprise",
    ),
    "endpoint_metadata": ModuleInfo(
        name="endpoint_metadata",
        classification=ModuleClassification.OPTIONAL,
        category="connector",
        description="Endpoint passive burnout signals via Jamf/Intune activity patterns",
        data_sources=["endpoint_agent"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/toxicity-burnout",
        enterprise_tier="enterprise",
    ),
    "ona_alerts": ModuleInfo(
        name="ona_alerts",
        classification=ModuleClassification.OPTIONAL,
        category="intelligence",
        description="Network threshold monitoring and ONA-based alerts",
        data_sources=["ona_data"],
        depends_on=["auth", "organizations", "organizational_network"],
        api_prefix="/api/v1/ona-alerts",
        enterprise_tier="enterprise",
    ),
    "intelligence_events": ModuleInfo(
        name="intelligence_events",
        classification=ModuleClassification.OPTIONAL,
        category="admin",
        description="Webhook event dispatch for 10 intelligence event types (fire-and-forget)",
        data_sources=["bi_scores", "pulse_data", "okr_data"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/webhooks",
        enterprise_tier="enterprise",
    ),
    # -----------------------------------------------------------------------
    # LEGACY
    # -----------------------------------------------------------------------
    "webhook_manager": ModuleInfo(
        name="webhook_manager",
        classification=ModuleClassification.LEGACY,
        category="admin",
        description="Legacy webhook management, being superseded by intelligence_events",
        data_sources=["webhooks_table"],
        depends_on=["auth", "organizations"],
        api_prefix="/api/v1/webhooks",
        enterprise_tier="enterprise",
    ),
    # -----------------------------------------------------------------------
    # CLINICAL — requires HIPAA
    # -----------------------------------------------------------------------
    "clinical_screening": ModuleInfo(
        name="clinical_screening",
        classification=ModuleClassification.CLINICAL,
        category="clinical",
        description="Clinical psychological screening instruments (requires HIPAA compliance)",
        data_sources=["clinical_assessments_table"],
        depends_on=["auth"],
        api_prefix="/api/v1/clinical",
        enterprise_tier="enterprise",
    ),
    "mental_health_chatbot": ModuleInfo(
        name="mental_health_chatbot",
        classification=ModuleClassification.CLINICAL,
        category="clinical",
        description="Mental health conversational agent (requires HIPAA compliance)",
        data_sources=["chat_sessions_table"],
        depends_on=["auth", "clinical_screening"],
        api_prefix="/api/v1/mental-health",
        enterprise_tier="enterprise",
    ),
    "telehealth": ModuleInfo(
        name="telehealth",
        classification=ModuleClassification.CLINICAL,
        category="clinical",
        description="Telehealth session management (requires HIPAA compliance)",
        data_sources=["telehealth_sessions_table"],
        depends_on=["auth", "clinical_screening"],
        api_prefix="/api/v1/telehealth",
        enterprise_tier="enterprise",
    ),
    # -----------------------------------------------------------------------
    # EXPERIMENTAL
    # -----------------------------------------------------------------------
    "bayesian_burnout_predictor": ModuleInfo(
        name="bayesian_burnout_predictor",
        classification=ModuleClassification.EXPERIMENTAL,
        category="intelligence",
        description="ML-based burnout prediction using Bayesian inference (optional torch dependency)",
        data_sources=["bi_scores", "metadata_signals", "temporal_data"],
        depends_on=["auth", "organizations", "behavioral_intelligence"],
        api_prefix="/api/v1/ml-predictions",
        enterprise_tier="enterprise",
    ),
    "nlp_analysis": ModuleInfo(
        name="nlp_analysis",
        classification=ModuleClassification.EXPERIMENTAL,
        category="intelligence",
        description="NLP-based text analysis for sentiment and themes (optional transformers dependency)",
        data_sources=["text_data"],
        depends_on=["auth"],
        api_prefix="/api/v1/nlp",
        enterprise_tier="enterprise",
    ),
    "pattern_matching_engine": ModuleInfo(
        name="pattern_matching_engine",
        classification=ModuleClassification.EXPERIMENTAL,
        category="intelligence",
        description="sklearn-based clustering for behavioral pattern detection",
        data_sources=["bi_scores", "assessment_data"],
        depends_on=["auth", "organizations", "behavioral_intelligence"],
        api_prefix="/api/v1/patterns",
        enterprise_tier="enterprise",
    ),
}


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


def get_module(name: str) -> Optional[ModuleInfo]:
    """Return a single module by name, or None."""
    return MODULE_REGISTRY.get(name)


def get_modules_by_classification(
    classification: ModuleClassification,
) -> List[ModuleInfo]:
    """Return all modules with the given classification."""
    return [m for m in MODULE_REGISTRY.values() if m.classification == classification]


def get_modules_by_category(category: str) -> List[ModuleInfo]:
    """Return all modules in the given category."""
    return [m for m in MODULE_REGISTRY.values() if m.category == category]


def get_production_modules() -> List[ModuleInfo]:
    """Return CORE + OPTIONAL modules only (production-ready)."""
    return [
        m
        for m in MODULE_REGISTRY.values()
        if m.classification
        in (ModuleClassification.CORE, ModuleClassification.OPTIONAL)
    ]


def get_registry_summary() -> Dict:
    """Aggregate counts by classification and category."""
    by_classification: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    by_tier: Dict[str, int] = {}

    for m in MODULE_REGISTRY.values():
        by_classification[m.classification.value] = (
            by_classification.get(m.classification.value, 0) + 1
        )
        by_category[m.category] = by_category.get(m.category, 0) + 1
        by_tier[m.enterprise_tier] = by_tier.get(m.enterprise_tier, 0) + 1

    return {
        "total_modules": len(MODULE_REGISTRY),
        "by_classification": by_classification,
        "by_category": by_category,
        "by_tier": by_tier,
    }
