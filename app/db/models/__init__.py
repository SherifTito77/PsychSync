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
from .analytics import Analytics, AnalyticsEvent, AssessmentTrend, UnifiedAnalyticsEvent

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
        NotificationAnalytics,
        NotificationCampaign,
        NotificationPreferences,
        NotificationTemplate,
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
    from .query_performance import (
        IndexRecommendation,
        QueryOptimizationReport,
        QueryPerformanceHistory,
        SlowQuery,
    )
    from .sql_audit import SQLQuery, SQLScanReport, SQLVulnerability
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
    from .dead_letter import DeadLetterTask, DLQReason, DLQStatus
except ImportError:
    DeadLetterTask = None
    DLQStatus = None
    DLQReason = None

# Import Kafka Dead Letter Queue models
try:
    from .kafka_dead_letter import KafkaDeadLetterTask
except ImportError:
    KafkaDeadLetterTask = None

# Import password history model
try:
    from .password_history import PasswordHistory
except ImportError:
    PasswordHistory = None

# Import ONA (Organizational Network Analysis) models
try:
    from .network_analysis import (
        CollaborationSurveyResponse,
        EdgeType,
        NetworkEdge,
        NetworkSnapshot,
    )
except ImportError:
    NetworkEdge = None
    NetworkSnapshot = None
    CollaborationSurveyResponse = None
    EdgeType = None

# Import Organizational Pulse models
try:
    from .organizational_pulse import PulseSnapshot
except ImportError:
    PulseSnapshot = None

# Import Toxicity & Burnout models
try:
    from .toxicity_burnout import (
        AlertSeverity,
        SnapshotScope,
        ToxicityBurnoutAlert,
        ToxicityBurnoutSnapshot,
    )
except ImportError:
    ToxicityBurnoutSnapshot = None
    ToxicityBurnoutAlert = None
    SnapshotScope = None
    AlertSeverity = None

# Import HIPAA-compliant secure models (encrypted PHI at rest)
try:
    from .assessment_secure import SecureAssessment
    from .organization_secure import SecureOrganization
    from .response_secure import SecureResponse
    from .team_secure import SecureTeam, SecureTeamMember
    from .user_secure import SecureUser
except ImportError:
    SecureUser = None
    SecureOrganization = None
    SecureTeam = None
    SecureTeamMember = None
    SecureAssessment = None
    SecureResponse = None

# Import Org Digital Twin models
try:
    from .org_digital_twin import OrgDigitalTwinSnapshot
except ImportError:
    OrgDigitalTwinSnapshot = None

# Import Action Plan models
try:
    from .action_plan import (
        ActionPlan,
        ActionPlanPriority,
        ActionPlanSource,
        ActionPlanStatus,
    )
except ImportError:
    ActionPlan = None
    ActionPlanStatus = None
    ActionPlanSource = None
    ActionPlanPriority = None

# Import 360-Degree Feedback models
try:
    from .feedback_360 import (
        FeedbackCompetency,
        FeedbackRequest,
        FeedbackResponse as FeedbackResponse360,
        FeedbackRound,
        FeedbackRoundStatus,
        RaterCategory,
    )
except ImportError:
    FeedbackRound = None
    FeedbackRequest = None
    FeedbackResponse360 = None
    FeedbackCompetency = None
    FeedbackRoundStatus = None
    RaterCategory = None

# Import Pulse Survey models
try:
    from .pulse_survey import (
        PulseSurveyCampaign,
        PulseSurveyResponse,
        SurveyCampaignStatus,
        SurveyFrequency,
    )
except ImportError:
    PulseSurveyCampaign = None
    PulseSurveyResponse = None
    SurveyFrequency = None
    SurveyCampaignStatus = None

# Import Meeting Effectiveness models
try:
    from .meeting_effectiveness import MeetingRating
except ImportError:
    MeetingRating = None

# Import External Benchmark models
try:
    from .external_benchmark import BenchmarkContribution, BenchmarkOptIn
except ImportError:
    BenchmarkContribution = None
    BenchmarkOptIn = None

# Import OKR models
try:
    from .okr import (
        Initiative,
        KRProgressUpdate,
        KeyResult,
        Objective,
        OKRCheckIn,
        OKRRetrospective,
    )
except ImportError:
    Objective = None
    KeyResult = None
    KRProgressUpdate = None
    Initiative = None
    OKRCheckIn = None
    OKRRetrospective = None

# Import Peer Recognition models
try:
    from .peer_recognition import PeerRecognition, RecognitionType
except ImportError:
    PeerRecognition = None
    RecognitionType = None

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
    "AssessmentTrend",
    "UnifiedAnalyticsEvent",
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
    # Password history
    "PasswordHistory",
    # HIPAA-compliant secure models
    "SecureUser",
    "SecureOrganization",
    "SecureTeam",
    "SecureTeamMember",
    "SecureAssessment",
    "SecureResponse",
    # ONA (Organizational Network Analysis) models
    "NetworkEdge",
    "NetworkSnapshot",
    "CollaborationSurveyResponse",
    "EdgeType",
    # Organizational Pulse models
    "PulseSnapshot",
    # Toxicity & Burnout models
    "ToxicityBurnoutSnapshot",
    "ToxicityBurnoutAlert",
    "SnapshotScope",
    "AlertSeverity",
    # Org Digital Twin models
    "OrgDigitalTwinSnapshot",
    # Action Plan models
    "ActionPlan",
    "ActionPlanStatus",
    "ActionPlanSource",
    "ActionPlanPriority",
    # 360-Degree Feedback models
    "FeedbackRound",
    "FeedbackRequest",
    "FeedbackResponse360",
    "FeedbackCompetency",
    "FeedbackRoundStatus",
    "RaterCategory",
    # Pulse Survey models
    "PulseSurveyCampaign",
    "PulseSurveyResponse",
    "SurveyFrequency",
    "SurveyCampaignStatus",
    # Meeting Effectiveness models
    "MeetingRating",
    # External Benchmark models
    "BenchmarkContribution",
    "BenchmarkOptIn",
    # OKR models
    "Objective",
    "KeyResult",
    "KRProgressUpdate",
    "Initiative",
    "OKRCheckIn",
    "OKRRetrospective",
    # Peer Recognition models
    "PeerRecognition",
    "RecognitionType",
]
