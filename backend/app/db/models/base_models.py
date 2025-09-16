# models.py - SQLAlchemy Database Models
from sqlalchemy import Column, UUID(as_uuid=True), String, DateTime, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    role = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(50), default="starter")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owned_teams = relationship("Team", back_populates="owner")
    assessments = relationship("Assessment", back_populates="user")
    team_memberships = relationship("TeamMember", back_populates="user")

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    team_type = Column(String(100), default="agile")  # agile, product, engineering, etc.
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Team configuration
    max_members = Column(UUID(as_uuid=True), default=12)
    methodology = Column(String(50), default="scrum")  # scrum, kanban, safe, etc.
    
    # Relationships
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("TeamMember", back_populates="team")
    predictions = relationship("Prediction", back_populates="team")
    sprints = relationship("Sprint", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(100), nullable=False)  # scrum_master, product_owner, developer, etc.
    join_date = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Member-specific settings
    workload_capacity = Column(Float, default=1.0)  # 0.5 = part-time, 1.0 = full-time
    specializations = Column(JSON, nullable=True)  # ["frontend", "backend", "devops"]
    
    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    framework_type = Column(String(100), nullable=False)  # enneagram, mbti, big_five, etc.
    raw_data = Column(JSON, nullable=False)  # Original assessment responses
    processed_results = Column(JSON, nullable=False)  # Processed personality insights
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    version = Column(String(20), default="1.0")  # Assessment version
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Some assessments expire
    
    # Assessment metadata
    completion_time_minutes = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # For security/fraud detection
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="assessments")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    prediction_type = Column(String(100), nullable=False)  # performance, conflict, velocity
    prediction_data = Column(JSON, nullable=False)  # Detailed prediction results
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    generated_by = Column(String(100), nullable=False)  # AI model version
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Prediction validation
    actual_outcome = Column(JSON, nullable=True)  # For model improvement
    accuracy_score = Column(Float, nullable=True)  # Calculated after outcome known
    feedback_provided = Column(Boolean, default=False)
    
    # Relationships
    team = relationship("Team", back_populates="predictions")

class Sprint(Base):
    __tablename__ = "sprints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    name = Column(String(255), nullable=False)
    goal = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="planned")  # planned, active, completed, cancelled
    
    # Sprint metrics
    planned_points = Column(UUID(as_uuid=True), nullable=True)
    completed_points = Column(UUID(as_uuid=True), nullable=True)
    velocity = Column(Float, nullable=True)
    team_satisfaction = Column(Float, nullable=True)  # 1.0 to 5.0
    
    # Behavioral insights
    collaboration_score = Column(Float, nullable=True)
    conflict_incidents = Column(UUID(as_uuid=True), default=0)
    communication_effectiveness = Column(Float, nullable=True)
    
    # Relationships
    team = relationship("Team", back_populates="sprints")
    stories = relationship("UserStory", back_populates="sprint")

class UserStory(Base):
    __tablename__ = "user_stories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    sprint_id = Column(UUID(as_uuid=True), ForeignKey("sprints.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    story_points = Column(UUID(as_uuid=True), nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(String(50), default="todo")  # todo, in_progress, review, done
    
    # Assignment based on personality fit
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    personality_fit_score = Column(Float, nullable=True)  # How well suited the assignee is
    collaboration_requirements = Column(JSON, nullable=True)  # Required personality traits
    
    # Story metrics
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    complexity_score = Column(Float, nullable=True)
    
    # Relationships
    sprint = relationship("Sprint", back_populates="stories")
    assignee = relationship("User")

class BehavioralInsight(Base):
    __tablename__ = "behavioral_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    insight_type = Column(String(100), nullable=False)  # compatibility, conflict, optimization
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Insight data
    affected_members = Column(JSON, nullable=True)  # List of affected user IDs
    recommendations = Column(JSON, nullable=False)  # List of recommendation strings
    supporting_data = Column(JSON, nullable=True)  # Data that supports this insight
    
    # Lifecycle
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

class PersonalityProfile(Base):
    __tablename__ = "personality_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Unified personality scores (0.0 to 1.0)
    openness = Column(Float, nullable=True)
    conscientiousness = Column(Float, nullable=True)
    extraversion = Column(Float, nullable=True)
    agreeableness = Column(Float, nullable=True)
    neuroticism = Column(Float, nullable=True)
    
    # Framework-specific types
    mbti_type = Column(String(10), nullable=True)  # INTJ, ENFP, etc.
    enneagram_type = Column(UUID(as_uuid=True), nullable=True)  # 1-9
    enneagram_wing = Column(String(10), nullable=True)  # 1w9, 2w1, etc.
    
    # Strengths (top 5)
    strengths_themes = Column(JSON, nullable=True)  # ["Strategic", "Achiever", ...]
    
    # Social style
    social_style = Column(String(20), nullable=True)  # analytical, driver, amiable, expressive
    assertiveness = Column(Float, nullable=True)
    responsiveness = Column(Float, nullable=True)
    
    # Predictive Index dimensions
    dominance = Column(Float, nullable=True)
    influence = Column(Float, nullable=True)
    steadiness = Column(Float, nullable=True)
    compliance = Column(Float, nullable=True)
    
    # Composite scores
    leadership_potential = Column(Float, nullable=True)
    collaboration_index = Column(Float, nullable=True)
    stress_tolerance = Column(Float, nullable=True)
    adaptability = Column(Float, nullable=True)
    
    # Metadata
    profile_version = Column(String(20), default="1.0")
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    confidence_score = Column(Float, nullable=False, default=0.5)
    
    # Relationships
    user = relationship("User")

class TeamCompatibilityMatrix(Base):
    __tablename__ = "team_compatibility_matrices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    member_a_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    member_b_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Compatibility scores (0.0 to 1.0)
    overall_compatibility = Column(Float, nullable=False)
    communication_compatibility = Column(Float, nullable=True)
    work_style_compatibility = Column(Float, nullable=True)
    conflict_probability = Column(Float, nullable=True)
    collaboration_potential = Column(Float, nullable=True)
    
    # Detailed analysis
    strengths = Column(JSON, nullable=True)  # What works well
    challenges = Column(JSON, nullable=True)  # Potential issues
    recommendations = Column(JSON, nullable=True)  # How to improve
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    algorithm_version = Column(String(20), default="1.0")
    
    # Relationships
    member_a = relationship("User", foreign_keys=[member_a_id])
    member_b = relationship("User", foreign_keys=[member_b_id])

# database.py - Database Configuration and Connection
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://psychsync_user@localhost/psychsync_db
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

# schemas.py - Pydantic Models for API
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    TEAM_LEAD = "team_lead"
    DEVELOPER = "developer"
    PRODUCT_OWNER = "product_owner"
    SCRUM_MASTER = "scrum_master"

class SubscriptionTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    company: Optional[str] = None
    role: Optional[UserRole] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    company: Optional[str]
    role: Optional[str]
    subscription_tier: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    team_type: str = "agile"
    methodology: str = "scrum"
    max_members: int = 12

class TeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    team_type: str
    methodology: str
    status: str
    created_at: datetime
    member_count: int = 0
    
    class Config:
        from_attributes = True

class AssessmentCreate(BaseModel):
    framework_type: str
    raw_data: Dict[str, Any]
    
    @validator('framework_type')
    def validate_framework(cls, v):
        allowed_frameworks = [
            'enneagram', 'mbti', 'big_five', 
            'predictive_index', 'strengths', 'social_styles'
        ]
        if v not in allowed_frameworks:
            raise ValueError(f'Framework must be one of: {allowed_frameworks}')
        return v

class AssessmentResponse(BaseModel):
    id: int
    framework_type: str
    processed_results: Dict[str, Any]
    confidence_score: float
    completed_at: datetime
    version: str
    
    class Config:
        from_attributes = True

class PredictionResponse(BaseModel):
    id: int
    prediction_type: str
    prediction_data: Dict[str, Any]
    confidence_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class BehavioralInsight(BaseModel):
    type: str
    title: str
    description: str
    confidence: float
    priority: str
    recommendations: List[str]
    affected_members: Optional[List[int]] = None

class TeamOptimizationRequest(BaseModel):
    project_requirements: Dict[str, Any]
    optimization_goals: List[str] = ["maximize_compatibility", "minimize_conflict"]
    constraints: Optional[Dict[str, Any]] = None