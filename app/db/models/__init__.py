# app/db/models/__init__.py

# Import essential models
from .framework import Framework
from .organization import Organization
from .refresh_token import RefreshToken
from .team import Team, TeamMember
from .user import User

# Import assessment and response models
try:
    from .assessment import Assessment, AssessmentQuestion
    from .question import Question
    from .response import AssessmentResponse, Response
except ImportError:
    # Models not yet implemented
    Assessment = None
    AssessmentQuestion = None
    Response = None
    AssessmentResponse = None
    Question = None

# Import analytics models
from .analytics import Analytics, AnalyticsEvent, UnifiedAnalyticsEvent

# Import Employee Safety models
from .employee_safety import (
    AlertLevel,
    IncidentSeverity,
    IncidentStatus,
    SafetyFollowUpAction,
    SafetyIncident,
    SafetyIncidentType,
    SafetyResource,
    SafetyTraining,
    SafetyTrainingCompletion,
    WellnessAlert,
    WellnessAssessment,
    WellnessMetricType,
)
from .growth_trajectories import (
    GrowthMilestone,
    GrowthPotentialAnalysis,
    GrowthTrajectory,
    TrajectoryBenchmark,
    TrajectoryPrediction,
    TrajectorySimulation,
)
from .intervention_effectiveness import (
    ComparativeEffectiveness,
    Intervention,
    InterventionEffectiveness,
    InterventionOutcomes,
    InterventionParticipant,
    PostInterventionMeasurement,
    PreInterventionMeasurement,
)

# Import email and communication models
try:
    from .communication_analysis import CommunicationAnalysis
    from .email_connection import EmailConnection
    from .email_metadata import EmailMetadata
except ImportError:
    # Models not yet implemented or have circular imports
    EmailConnection = None
    EmailMetadata = None
    CommunicationAnalysis = None

# Import biometric health models
try:
    from .biometric_health import BiometricHealthData, DataSourceType, HealthDataConsent
except ImportError:
    BiometricHealthData = None
    HealthDataConsent = None
    DataSourceType = None

# Import clinical screening models (HIPAA-compliant mental health screening)
try:
    from .clinical_screening import (
        ClinicalAlert,
        ClinicalAuditLog,
        ClinicalConsent,
        ClinicalReferral,
        ClinicalScreening,
    )
except ImportError:
    ClinicalScreening = None
    ClinicalAlert = None
    ClinicalReferral = None
    ClinicalAuditLog = None
    ClinicalConsent = None

# Import notification system models (comprehensive notification system)
try:
    from .notifications import (
        Notification,
        NotificationTemplate,
        NotificationCampaign,
        NotificationPreferences,
        NotificationAnalytics,
    )
except ImportError:
    Notification = None
    NotificationTemplate = None
    NotificationCampaign = None
    NotificationPreferences = None
    NotificationAnalytics = None

# Import advanced clinical features models (telehealth, chatbot, mobile)
try:
    from .clinical_advanced import (
        ChatbotConversation,
        ClinicalAnalyticsSnapshot,
        MobileDevice,
        TelehealthSession,
    )
except ImportError:
    TelehealthSession = None
    ChatbotConversation = None
    MobileDevice = None
    ClinicalAnalyticsSnapshot = None

# Import biometric authentication models
try:
    from .biometric import BiometricAttempt, BiometricChallenge, BiometricKey
except ImportError:
    BiometricKey = None
    BiometricChallenge = None
    BiometricAttempt = None

# Import SQL audit and query performance models
try:
    from .sql_audit import SQLQuery, SQLVulnerability, SQLScanReport
    from .query_performance import (
        SlowQuery,
        IndexRecommendation,
        QueryPerformanceHistory,
        QueryOptimizationReport,
    )
except ImportError:
    SQLQuery = None
    SQLVulnerability = None
    SQLScanReport = None
    SlowQuery = None
    IndexRecommendation = None
    QueryPerformanceHistory = None
    QueryOptimizationReport = None

# Import audit logging models
try:
    from .audit import (
        AuditLog,
        AuthenticationLog,
        ComplianceReport,
        DataAccessLog,
        SecurityIncident,
    )
except ImportError:
    AuditLog = None
    DataAccessLog = None
    AuthenticationLog = None
    ComplianceReport = None
    SecurityIncident = None

# Import Corporate Psychology models
try:
    from .corporate_psychology import (
        CorporatePsychologyMetrics,
        InterventionCategory,
        InterventionStatus,
        RiskHorizon,
        StructuralIntervention,
        SystemSignalAlert,
    )
except ImportError:
    CorporatePsychologyMetrics = None
    SystemSignalAlert = None
    StructuralIntervention = None
    RiskHorizon = None
    InterventionCategory = None
    InterventionStatus = None

# Import Dead Letter Queue models
try:
    from .dead_letter import DeadLetterTask, DLQStatus, DLQReason
except ImportError:
    DeadLetterTask = None
    DLQStatus = None
    DLQReason = None

# Import Kafka Dead Letter Queue models
try:
    from .kafka_dead_letter import KafkaDeadLetterTask
except ImportError:
    KafkaDeadLetterTask = None

# Make models available when importing from this package
__all__ = [
    "User",
    "Organization",
    "Team",
    "TeamMember",
    "Framework",
    "RefreshToken",
    # Assessment and response models
    "Assessment",
    "AssessmentQuestion",
    "Response",
    "AssessmentResponse",
    "Question",
    # Analytics models
    "Analytics",
    "AnalyticsEvent",
    "Intervention",
    "InterventionParticipant",
    "PreInterventionMeasurement",
    "PostInterventionMeasurement",
    "InterventionEffectiveness",
    "InterventionOutcomes",
    "ComparativeEffectiveness",
    "GrowthTrajectory",
    "TrajectoryPrediction",
    "GrowthMilestone",
    "GrowthPotentialAnalysis",
    "TrajectoryBenchmark",
    "TrajectorySimulation",
    # Safety models
    "SafetyIncident",
    "SafetyFollowUpAction",
    "WellnessAssessment",
    "WellnessAlert",
    "SafetyResource",
    "SafetyTraining",
    "SafetyTrainingCompletion",
    "SafetyIncidentType",
    "IncidentSeverity",
    "IncidentStatus",
    "WellnessMetricType",
    "AlertLevel",
    # Email and communication models
    "EmailConnection",
    "EmailMetadata",
    "CommunicationAnalysis",
    # Biometric health models
    "BiometricHealthData",
    "HealthDataConsent",
    "DataSourceType",
    # Clinical screening models
    "ClinicalScreening",
    "ClinicalAlert",
    "ClinicalReferral",
    "ClinicalAuditLog",
    "ClinicalConsent",
    # Notification system models
    "Notification",
    "NotificationTemplate",
    "NotificationCampaign",
    "NotificationPreferences",
    "NotificationAnalytics",
    # Advanced clinical features models
    "TelehealthSession",
    "ChatbotConversation",
    "MobileDevice",
    "ClinicalAnalyticsSnapshot",
    # Biometric authentication models
    "BiometricKey",
    "BiometricChallenge",
    "BiometricAttempt",
    # SQL audit and query performance models
    "SQLQuery",
    "SQLVulnerability",
    "SQLScanReport",
    "SlowQuery",
    "IndexRecommendation",
    "QueryPerformanceHistory",
    "QueryOptimizationReport",
    # Audit logging models
    "AuditLog",
    "DataAccessLog",
    "AuthenticationLog",
    "ComplianceReport",
    "SecurityIncident",
    # Corporate Psychology models
    "CorporatePsychologyMetrics",
    "SystemSignalAlert",
    "StructuralIntervention",
    "RiskHorizon",
    "InterventionCategory",
    "InterventionStatus",
    # Dead Letter Queue models
    "DeadLetterTask",
    "DLQStatus",
    "DLQReason",
    "KafkaDeadLetterTask",
]
