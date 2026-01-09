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
]
