# app/db/models/assessment.py
import enum

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AssessmentCategory(enum.Enum):
    PERSONALITY = "personality"
    SKILLS = "skills"
    BEHAVIORAL = "behavioral"
    COGNITIVE = "cognitive"


class AssessmentStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(AssessmentCategory), nullable=False)
    status = Column(SQLEnum(AssessmentStatus), default=AssessmentStatus.DRAFT)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    framework_code = Column(String(50), nullable=True)  # e.g., 'MBTI', 'BIG_FIVE', 'ENNEAGRAM'
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
# created_by = relationship(  # TEMPORARILY DISABLED
#        "User", back_populates="assessments_created", foreign_keys=[created_by_id], lazy="select"
#    )

# team = relationship("Team", back_populates="assessments", foreign_keys=[team_id], lazy="select")  # TEMPORARILY DISABLED

# sections = relationship(  # TEMPORARILY DISABLED
#        "AssessmentSection",
#        back_populates="assessment",
#        cascade="all, delete-orphan",
#        order_by="AssessmentSection.order",
#    )

    # Direct relationship to questions (through AssessmentSection)
    questions = relationship(
        "AssessmentQuestion",
        secondary="assessment_sections",
        primaryjoin="and_(Assessment.id == AssessmentSection.assessment_id, AssessmentQuestion.section_id == AssessmentSection.id)",
        viewonly=True,
        cascade="all, delete-orphan",
    )

# responses = relationship(  # TEMPORARILY DISABLED
#        "AssessmentResponse",
#        back_populates="assessment",
#        cascade="all, delete-orphan",
#        foreign_keys="[AssessmentResponse.assessment_id]",
#    )


class AssessmentSection(Base):
    __tablename__ = "assessment_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)

# assessment = relationship("Assessment", back_populates="sections")  # TEMPORARILY DISABLED
# questions = relationship(  # TEMPORARILY DISABLED
#        "AssessmentQuestion",
#        back_populates="section",
#        cascade="all, delete-orphan",
#        order_by="AssessmentQuestion.order",
#    )


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    section_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sections.id"), nullable=False)
    question_type = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    order = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    config = Column(JSON, nullable=True)

# section = relationship("AssessmentSection", back_populates="questions")  # TEMPORARILY DISABLED

# responses = relationship("Response", back_populates="question", cascade="all, delete-orphan")  # TEMPORARILY DISABLED


class ResponseStatus(enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    respondent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(ResponseStatus), default=ResponseStatus.IN_PROGRESS)
    responses = Column(JSON, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

# assessment = relationship(  # TEMPORARILY DISABLED
#        "Assessment", back_populates="responses", foreign_keys=[assessment_id]
#    )
    respondent = relationship("User", foreign_keys=[respondent_id])


class AssessmentAssignment(Base):
    __tablename__ = "assessment_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now())
    completed = Column(Boolean, default=False)

    assessment = relationship("Assessment", backref="assignments")
    user = relationship("User", backref="assignments")
