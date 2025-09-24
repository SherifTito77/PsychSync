
# app/db/models/__init__.py

# Import all models to ensure they're registered with SQLAlchemy
from .user import User
from .organization import Organization
from .team import Team
from .team_member import TeamMember
from .assessment import Assessment
from .prediction import Prediction

# Make models available when importing from this package
__all__ = [
    "User",
    "Organization", 
    "Team",
    "TeamMember",
    "Assessment",
    "Prediction"
]



# # Import model modules so Base.metadata collects them for Alembic autogenerate

# from app.db.base import Base
# from .user import User
# # ...existing code...

# from .organization import Organization
# from .user import User
# from .role import Role
# from .org_member import OrgMember
# from .team import Team
# from .team_member import TeamMember
# from .framework import Framework
# from .question import Question
# from .question_option import QuestionOption
# from .assessment import Assessment
# from .response import Response
# from .score import Score
# from .invitation import Invitation
# from .audit_log import AuditLog
# # from .team_compatibility_matrix import TeamCompatibilityMatrix
# # from .personality_profile import PersonalityProfile
# # from .behavioral_insight import BehavioralInsight
# # from .user_story import UserStory
# # from .sprint import Sprint
# from .prediction import Prediction
# # from .user import UserCreate, UserRead
# # from .team import TeamCreate, TeamRead
# # from .organization import OrganizationCreate, OrganizationRead
