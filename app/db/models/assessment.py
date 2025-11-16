# app/db/models/assessment.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum



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
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(AssessmentCategory), nullable=False)
    status = Column(SQLEnum(AssessmentStatus), default=AssessmentStatus.DRAFT)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # FIX: Specify foreign_keys
    # created_by = relationship(
    #     "User",
    #     back_populates="assessments_created",
    #     foreign_keys=[created_by_id]
    # )
    
    # team = relationship(
    #     "Team",
    #     back_populates="assessments",
    #     foreign_keys=[team_id]
    # )
    
    sections = relationship(
        "AssessmentSection", 
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentSection.order"
    )


class AssessmentSection(Base):
    __tablename__ = "assessment_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    
    assessment = relationship("Assessment", back_populates="sections")
    questions = relationship(
        "Question", 
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Question.order"
    )


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("assessment_sections.id"), nullable=False)
    question_type = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    order = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    config = Column(JSON, nullable=True)
    
    section = relationship("AssessmentSection", back_populates="questions")


class ResponseStatus(enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    respondent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(ResponseStatus), default=ResponseStatus.IN_PROGRESS)
    responses = Column(JSON, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # FIX: Specify foreign_keys
    assessment = relationship("Assessment", foreign_keys=[assessment_id])
    respondent = relationship(
        "User",
        foreign_keys=[respondent_id]
    )

class AssessmentAssignment(Base):
    __tablename__ = "assessment_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now())
    completed = Column(Boolean, default=False)

    assessment = relationship("Assessment", backref="assignments")
    user = relationship("User", backref="assignments")
