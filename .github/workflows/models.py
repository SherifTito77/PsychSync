

from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Boolean, Float #UUID(as_uuid=True)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy.dialects.postgresql import UUID  # <-- This is the correct way to import UUID
import uuid  # <-- You also need to import the base uuid library to generate UUIDs

Base = declarative_base()

class Role(Base):
    __tablename__ = 'roles'
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", back_populates="role")

class Team(Base):
    __tablename__ = 'teams'
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    members = relationship("User", back_populates="team")

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'))
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'))
    role = relationship("Role", back_populates="users")
    team = relationship("Team", back_populates="members")
    responses = relationship("Response", back_populates="user")

class Framework(Base):
    __tablename__ = 'frameworks'
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    assessments = relationship("Assessment", back_populates="framework")

class Assessment(Base):
    __tablename__ = 'assessments'
    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String, nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey('frameworks.id'))
    framework = relationship("Framework", back_populates="assessments")
    questions = relationship("Question", back_populates="assessment")
    results = relationship("Result", back_populates="assessment")

class Question(Base):
    __tablename__ = 'questions'
    id = Column(UUID(as_uuid=True), primary_key=True)
    text = Column(Text, nullable=False)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey('assessments.id'))
    assessment = relationship("Assessment", back_populates="questions")
    responses = relationship("Response", back_populates="question")

class Response(Base):
    __tablename__ = 'responses'
    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'))
    answer = Column(Text)
    user = relationship("User", back_populates="responses")
    question = relationship("Question", back_populates="responses")

class Result(Base):
    __tablename__ = 'results'
    id = Column(UUID(as_uuid=True), primary_key=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey('assessments.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    score = Column(Float)
    assessment = relationship("Assessment", back_populates="results")

class OptimizationReport(Base):
    __tablename__ = 'optimization_reports'
    id = Column(UUID(as_uuid=True), primary_key=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'))
    report_data = Column(Text)
    created_at = Column(DateTime)
    team = relationship("Team")

print("Initial SQLAlchemy models and relationships have been defined.")
