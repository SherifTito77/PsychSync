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
from .analytics import Analytics, AnalyticsEvent

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
    from .biometric_health import (
        BiometricHealthData,
        HealthDataConsent,
        DataSourceType
    )
except ImportError:
    BiometricHealthData = None
    HealthDataConsent = None
    DataSourceType = None

# Import clinical screening models (HIPAA-compliant mental health screening)
try:
    from .clinical_screening import (
        ClinicalScreening,
        ClinicalAlert,
        ClinicalReferral,
        ClinicalAuditLog,
        ClinicalConsent
    )
except ImportError:
    ClinicalScreening = None
    ClinicalAlert = None
    ClinicalReferral = None
    ClinicalAuditLog = None
    ClinicalConsent = None

# Import notification system models (clinician alerts and preferences)
try:
    from .notification import (
        Notification,
        NotificationPreference,
        NotificationQueue
    )
except ImportError:
    Notification = None
    NotificationPreference = None
    NotificationQueue = None

# Import advanced clinical features models (telehealth, chatbot, mobile)
try:
    from .clinical_advanced import (
        TelehealthSession,
        ChatbotConversation,
        MobileDevice,
        ClinicalAnalyticsSnapshot
    )
except ImportError:
    TelehealthSession = None
    ChatbotConversation = None
    MobileDevice = None
    ClinicalAnalyticsSnapshot = None

# Import biometric authentication models
try:
    from .biometric import (
        BiometricKey,
        BiometricChallenge,
        BiometricAttempt
    )
except ImportError:
    BiometricKey = None
    BiometricChallenge = None
    BiometricAttempt = None

# Import audit logging models
try:
    from .audit import (
        AuditLog,
        DataAccessLog,
        AuthenticationLog,
        ComplianceReport,
        SecurityIncident
    )
except ImportError:
    AuditLog = None
    DataAccessLog = None
    AuthenticationLog = None
    ComplianceReport = None
    SecurityIncident = None

# Import product management prompts models
try:
    from .product_management import (
        PromptExecution,
        PromptTemplate,
        PromptWorkflow,
        PromptFavorite,
        PromptResult
    )
except ImportError:
    PromptExecution = None
    PromptTemplate = None
    PromptWorkflow = None
    PromptFavorite = None
    PromptResult = None

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
    "NotificationPreference",
    "NotificationQueue",
    # Advanced clinical features models
    "TelehealthSession",
    "ChatbotConversation",
    "MobileDevice",
    "ClinicalAnalyticsSnapshot",
    # Biometric authentication models
    "BiometricKey",
    "BiometricChallenge",
    "BiometricAttempt",
    # Audit logging models
    "AuditLog",
    "DataAccessLog",
    "AuthenticationLog",
    "ComplianceReport",
    "SecurityIncident",
    # Product management prompts models
    "PromptExecution",
    "PromptTemplate",
    "PromptWorkflow",
    "PromptFavorite",
    "PromptResult",
]
