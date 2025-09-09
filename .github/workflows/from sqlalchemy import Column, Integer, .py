from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", back_populates="role")

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    members = relationship("User", back_populates="team")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    role_id = Column(Integer, ForeignKey('roles.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))
    role = relationship("Role", back_populates="users")
    team = relationship("Team", back_populates="members")
    responses = relationship("Response", back_populates="user")

class Framework(Base):
    __tablename__ = 'frameworks'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    assessments = relationship("Assessment", back_populates="framework")

class Assessment(Base):
    __tablename__ = 'assessments'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    framework_id = Column(Integer, ForeignKey('frameworks.id'))
    framework = relationship("Framework", back_populates="assessments")
    questions = relationship("Question", back_populates="assessment")
    results = relationship("Result", back_populates="assessment")

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    assessment_id = Column(Integer, ForeignKey('assessments.id'))
    assessment = relationship("Assessment", back_populates="questions")
    responses = relationship("Response", back_populates="question")

class Response(Base):
    __tablename__ = 'responses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    answer = Column(Text)
    user = relationship("User", back_populates="responses")
    question = relationship("Question", back_populates="responses")

class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessments.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    score = Column(Float)
    assessment = relationship("Assessment", back_populates="results")

class OptimizationReport(Base):
    __tablename__ = 'optimization_reports'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    report_data = Column(Text)
    created_at = Column(DateTime)
    team = relationship("Team")

print("Initial SQLAlchemy models and relationships have been defined.")
