# app/db/models/__init__.py

# Import essential models
from .user import User
from .organization import Organization
from .team import Team, TeamMember

# Import assessment and response models
try:
    from .assessment import Assessment, AssessmentQuestion
    from .response import Response, AssessmentResponse
    from .question import Question
except ImportError:
    # Models not yet implemented
    Assessment = None
    AssessmentQuestion = None
    Response = None
    AssessmentResponse = None
    Question = None

# Import analytics models
from .analytics import Analytics, AnalyticsEvent
from .intervention_effectiveness import (
    Intervention,
    InterventionParticipant,
    PreInterventionMeasurement,
    PostInterventionMeasurement,
    InterventionEffectiveness,
    InterventionOutcomes,
    ComparativeEffectiveness
)
from .growth_trajectories import (
    GrowthTrajectory,
    TrajectoryPrediction,
    GrowthMilestone,
    GrowthPotentialAnalysis,
    TrajectoryBenchmark,
    TrajectorySimulation
)

# Import Employee Safety models
from .employee_safety import (
    SafetyIncident,
    SafetyFollowUpAction,
    WellnessAssessment,
    WellnessAlert,
    SafetyResource,
    SafetyTraining,
    SafetyTrainingCompletion,
    SafetyIncidentType,
    IncidentSeverity,
    IncidentStatus,
    WellnessMetricType,
    AlertLevel
)

# Import email and communication models
try:
    from .email_connection import EmailConnection
    from .email_metadata import EmailMetadata
    from .communication_analysis import CommunicationAnalysis
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