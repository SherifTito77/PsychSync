import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..base import Base


class Analytics(Base):
    __tablename__ = "analytics"

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Entity being analyzed (user, team, organization, or assessment)
    entity_type = sa.Column(
        sa.String(50), nullable=False
    )  # 'user', 'team', 'organization', 'assessment'
    entity_id = sa.Column(UUID(as_uuid=True), nullable=False, index=True)

    # Analytics type and category
    analytics_type = sa.Column(
        sa.String(100), nullable=False
    )  # 'personality', 'performance', 'engagement', 'wellness'
    category = sa.Column(
        sa.String(100), nullable=True
    )  # Specific category within the type

    # Raw data and processed results
    raw_data = sa.Column(JSONB, nullable=True)  # Original data points
    processed_data = sa.Column(JSONB, nullable=True)  # Processed analytics results
    insights = sa.Column(JSONB, nullable=True)  # Generated insights and recommendations

    # Metrics and scores
    overall_score = sa.Column(sa.Float, nullable=True)  # 0-100 scale
    confidence_level = sa.Column(sa.Float, nullable=True)  # 0-1 confidence in analysis

    # Trend data
    trend_data = sa.Column(JSONB, nullable=True)  # Historical trend information
    comparison_data = sa.Column(JSONB, nullable=True)  # Benchmarks and comparisons

    # Context
    period_start = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False)
    period_end = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False)
    sample_size = sa.Column(sa.Integer, nullable=True)  # Number of data points

    # Processing metadata
    algorithm_version = sa.Column(
        sa.String(50), nullable=True
    )  # Version of analytics algorithm used
    processing_time_ms = sa.Column(
        sa.Integer, nullable=True
    )  # Time taken to generate analytics

    # Status and quality indicators
    status = sa.Column(
        sa.String(20), nullable=False, default="pending"
    )  # 'pending', 'processing', 'completed', 'error'
    data_quality_score = sa.Column(sa.Float, nullable=True)  # 0-1 quality of input data
    completeness_score = sa.Column(sa.Float, nullable=True)  # 0-1 completeness of data

    # User interactions
    view_count = sa.Column(
        sa.Integer, default=0
    )  # How many times this analytics was viewed
    last_viewed_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)

    # Timestamps
    created_at = sa.Column(
        sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )
    updated_at = sa.Column(
        sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )

    # Relationships
    creator_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True)
    creator = relationship("User", foreign_keys=[creator_id])

    def __repr__(self):
        return f"<Analytics(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id}, type={self.analytics_type})>"


class AnalyticsEvent(Base):
    """Track events that trigger analytics updates"""

    __tablename__ = "analytics_events"

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Event information
    event_type = sa.Column(
        sa.String(100), nullable=False
    )  # 'assessment_completed', 'user_joined', 'team_changed'
    entity_type = sa.Column(sa.String(50), nullable=False)
    entity_id = sa.Column(UUID(as_uuid=True), nullable=False)

    # Event data
    event_data = sa.Column(JSONB, nullable=True)

    # Processing information
    processed = sa.Column(sa.Boolean, default=False)
    processed_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)

    # Timestamps
    created_at = sa.Column(
        sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, event_type={self.event_type}, entity_type={self.entity_type})>"


# ============================================
# STAR SCHEMA DATA WAREHOUSE MODELS
# ============================================
# Team Analytics Data Warehouse
# Implements star schema for team-level analytics and reporting
# Created: 2025-01-12

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID


class DimUser(Base):
    """
    User Dimension Table

    Stores user attributes for analytics slicing and dicing.
    Slowly Changing Dimension (SCD) Type 2 - maintains history.

    Grain: One row per user version (tracks changes over time)
    """

    __tablename__ = "dim_user"

    # Surrogate key
    user_key = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Natural key
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Tenant scoping
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # User attributes
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50))  # admin, user, team_lead, etc.

    # Team membership
    team_id = Column(UUID(as_uuid=True))
    team_name = Column(String(255))  # Denormalized for faster queries

    # SCD Type 2 fields (track changes over time)
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for analytics queries
    __table_args__ = (
        Index("idx_dim_user_tenant", "tenant_id"),
        Index("idx_dim_user_team", "team_id"),
        Index("idx_dim_user_current", "is_current"),
        Index("idx_dim_user_scd", "user_id", "valid_from", "valid_to"),
    )

    def __repr__(self):
        return f"<DimUser(user_key={self.user_key}, email={self.email})>"


class DimAssessment(Base):
    """
    Assessment Dimension Table

    Stores assessment metadata for analytics.
    Slowly Changing Dimension (SCD) Type 2.

    Grain: One row per assessment version
    """

    __tablename__ = "dim_assessment"

    # Surrogate key
    assessment_key = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Natural key
    assessment_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Tenant scoping
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Assessment attributes
    name = Column(String(255), nullable=False)
    framework_code = Column(String(50), nullable=False)  # MBTI, BigFive, etc.
    framework_name = Column(String(100))  # Denormalized
    description = Column(Text)

    # Assessment configuration
    question_count = Column(Integer)
    max_score = Column(Float)
    min_score = Column(Float)

    # Assessment settings
    is_active = Column(Boolean, default=True)
    is_template = Column(Boolean, default=False)  # System template vs custom

    # SCD Type 2 fields
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_dim_assessment_tenant", "tenant_id"),
        Index("idx_dim_assessment_framework", "framework_code"),
        Index("idx_dim_assessment_current", "is_current"),
    )

    def __repr__(self):
        return (
            f"<DimAssessment(assessment_key={self.assessment_key}, name={self.name})>"
        )


class DimTeam(Base):
    """
    Team Dimension Table

    Stores team attributes for analytics grouping.
    Slowly Changing Dimension (SCD) Type 2.

    Grain: One row per team version
    """

    __tablename__ = "dim_team"

    # Surrogate key
    team_key = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Natural key
    team_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Tenant scoping
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Team attributes
    name = Column(String(255), nullable=False)
    description = Column(Text)
    department = Column(String(255))

    # Team leadership
    lead_user_id = Column(UUID(as_uuid=True))
    lead_user_email = Column(String(255))  # Denormalized

    # Team metrics (denormalized for faster queries)
    member_count = Column(Integer, default=0)
    assessment_count = Column(Integer, default=0)

    # SCD Type 2 fields
    valid_from = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_to = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_dim_team_tenant", "tenant_id"),
        Index("idx_dim_team_current", "is_current"),
    )

    def __repr__(self):
        return f"<DimTeam(team_key={self.team_key}, name={self.name})>"


class DimDate(Base):
    """
    Date Dimension Table

    Stores calendar attributes for time-based analytics.
    Pre-populated table with all dates (10+ years).

    Grain: One row per day
    """

    __tablename__ = "dim_date"

    # Surrogate key
    date_key = Column(Integer, primary_key=True)  # Format: YYYYMMDD (e.g., 20250112)

    # Date attributes
    full_date = Column(Date, nullable=False, unique=True)
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Sunday-Saturday)
    day_name = Column(String(10), nullable=False)  # Monday, Tuesday, etc.
    day_of_month = Column(Integer, nullable=False)  # 1-31
    day_of_year = Column(Integer, nullable=False)  # 1-366

    # Week attributes
    week_of_year = Column(Integer, nullable=False)  # 1-53
    iso_week = Column(Integer, nullable=False)

    # Month attributes
    month_number = Column(Integer, nullable=False)  # 1-12
    month_name = Column(String(10), nullable=False)  # January, February, etc.
    quarter = Column(Integer, nullable=False)  # 1-4

    # Year attributes
    year = Column(Integer, nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_quarter = Column(Integer, nullable=False)

    # Weekend and holiday flags
    is_weekend = Column(Boolean, nullable=False)
    is_holiday = Column(Boolean, default=False, nullable=False)
    holiday_name = Column(String(100))

    # Indexes
    __table_args__ = (
        Index("idx_dim_date_full_date", "full_date"),
        Index("idx_dim_date_year_month", "year", "month_number"),
        Index("idx_dim_date_quarter", "year", "quarter"),
    )

    def __repr__(self):
        return f"<DimDate(date_key={self.date_key}, full_date={self.full_date})>"


class DimFramework(Base):
    """
    Framework Dimension Table

    Stores personality assessment framework metadata.
    Type 1 SCD (overwrite changes).

    Grain: One row per framework
    """

    __tablename__ = "dim_framework"

    # Surrogate key (not primary key - framework_code is the natural key referenced by foreign keys)
    framework_key = Column(UUID(as_uuid=True), default=uuid4, unique=True)

    # Natural key (primary key - referenced by foreign keys in other tables)
    framework_code = Column(String(50), primary_key=True)  # MBTI, BigFive, etc.

    # Framework attributes
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # personality, behavioral, strengths, etc.

    # Framework metadata
    question_count_default = Column(Integer)
    scoring_algorithm = Column(String(50))  # additive, weighted, etc.
    result_type = Column(String(50))  # type, score, profile, etc.

    # Framework settings
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DimFramework(framework_code={self.framework_code}, name={self.name})>"


class FactAssessmentCompletion(Base):
    """
    Assessment Completion Fact Table

    Stores metrics for completed assessments.
    Core fact table for assessment analytics.

    Grain: One row per assessment completion
    """

    __tablename__ = "fact_assessment_completion"

    # Surrogate key
    completion_key = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign keys to dimensions
    user_key = Column(
        UUID(as_uuid=True), ForeignKey("dim_user.user_key"), nullable=False
    )
    assessment_key = Column(
        UUID(as_uuid=True), ForeignKey("dim_assessment.assessment_key"), nullable=False
    )
    team_key = Column(UUID(as_uuid=True), ForeignKey("dim_team.team_key"))
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False)
    framework_key = Column(
        String(50), ForeignKey("dim_framework.framework_code"), nullable=False
    )

    # Tenant scoping
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Degenerate dimensions (IDs from operational system)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    assessment_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), index=True)

    # Facts (metrics)
    completion_time_seconds = Column(Integer)  # Time to complete assessment
    score = Column(Float)  # Final score
    max_score = Column(Float)  # Maximum possible score
    score_percentage = Column(Float)  # Score as percentage

    # Response metrics
    questions_answered = Column(Integer, nullable=False)
    questions_skipped = Column(Integer, default=0)
    questions_total = Column(Integer, nullable=False)

    # Quality metrics
    is_complete = Column(Boolean, default=True, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)  # Passed validation
    completion_percentage = Column(Float)  # % of questions answered

    # Timestamps
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, index=True)

    # Additional metrics (stored as JSONB for flexibility)
    additional_metrics = Column(JSONB)  # {trait_scores: {}, rankings: [], etc.}

    # Relationships
    user = relationship("DimUser")
    assessment = relationship("DimAssessment")
    team = relationship("DimTeam")
    date = relationship("DimDate")
    framework = relationship("DimFramework")

    # Indexes for analytics queries
    __table_args__ = (
        Index("idx_fact_completion_tenant_date", "tenant_id", "date_key"),
        Index("idx_fact_completion_user", "user_id", "completed_at"),
        Index("idx_fact_completion_team", "team_id", "completed_at"),
        Index("idx_fact_completion_assessment", "assessment_id"),
        Index("idx_fact_completion_framework", "framework_key"),
        Index("idx_fact_completion_complete", "is_complete", "is_valid"),
        # Composite index for common analytics queries
        Index("idx_fact_completion_analytics", "tenant_id", "team_key", "date_key"),
    )

    def __repr__(self):
        return f"<FactAssessmentCompletion(completion_key={self.completion_key}, score={self.score})>"


class FactTeamMetrics(Base):
    """
    Team Metrics Fact Table

    Stores aggregated metrics at team level.
    Updated daily via ETL batch job.

    Grain: One row per team per day
    """

    __tablename__ = "fact_team_metrics"

    # Surrogate key
    metric_key = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign keys to dimensions
    team_key = Column(
        UUID(as_uuid=True), ForeignKey("dim_team.team_key"), nullable=False
    )
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False)

    # Tenant scoping
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Degenerate dimension
    team_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Assessment completion metrics
    total_assessments_completed = Column(Integer, default=0)
    unique_users_completed = Column(Integer, default=0)
    completion_rate = Column(Float)  # % of team members who completed

    # Score metrics
    avg_score = Column(Float)
    max_score = Column(Float)
    min_score = Column(Float)
    median_score = Column(Float)

    # Time metrics
    avg_completion_time_seconds = Column(Integer)
    total_completion_time_seconds = Column(BigInteger)

    # Engagement metrics
    active_users = Column(Integer, default=0)  # Users who logged in
    engaged_users = Column(Integer, default=0)  # Users who took assessments

    # Framework breakdown (stored as JSONB)
    framework_metrics = Column(JSONB)  # {MBTI: {count: 10, avg_score: 85}, ...}

    # Timestamps
    metric_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    team = relationship("DimTeam")
    date = relationship("DimDate")

    # Indexes
    __table_args__ = (
        Index("idx_fact_team_metrics_tenant_date", "tenant_id", "date_key"),
        Index("idx_fact_team_metrics_team_date", "team_id", "date_key"),
        Index("idx_fact_team_metrics_team", "team_id"),
    )

    def __repr__(self):
        return f"<FactTeamMetrics(metric_key={self.metric_key}, team_id={self.team_id}, metric_date={self.metric_date})>"


class UnifiedAnalyticsEvent(Base):
    """Unified analytics event table for tracking all platform events"""

    __tablename__ = "unified_analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_name = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False)
    timestamp = Column(sa.TIMESTAMP(timezone=True), nullable=False)
    session_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)
    batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    processed = Column(Boolean, default=False, nullable=False)
    event_data = Column(JSONB, nullable=True)
    created_at = Column(
        sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )

    __table_args__ = (
        Index("idx_unified_event_created_at", "created_at"),
        Index("idx_unified_event_processed", "processed"),
        Index("idx_unified_event_batch", "batch_id"),
    )

    def __repr__(self):
        return f"<UnifiedAnalyticsEvent(id={self.id}, event_name={self.event_name})>"


class AssessmentTrend(Base):
    """Tracks longitudinal assessment score trends per user and assessment type"""

    __tablename__ = "assessment_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    assessment_type = Column(String(100), nullable=False)
    trend_direction = Column(String(50), nullable=True)
    slope = Column(sa.Float, nullable=True)
    r_squared = Column(sa.Float, nullable=True)
    mean_score = Column(sa.Float, nullable=True)
    median_score = Column(sa.Float, nullable=True)
    total_assessments = Column(sa.Integer, nullable=True)
    score_change_30d = Column(sa.Float, nullable=True)
    score_change_90d = Column(sa.Float, nullable=True)
    data_points_used = Column(sa.Integer, nullable=True)
    date_range_start = Column(sa.TIMESTAMP(timezone=True), nullable=True)
    date_range_end = Column(sa.TIMESTAMP(timezone=True), nullable=True)
    calculated_at = Column(
        sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )

    __table_args__ = (
        Index(
            "idx_assessment_trend_user_type", "user_id", "assessment_type", unique=True
        ),
    )

    def __repr__(self):
        return f"<AssessmentTrend(user_id={self.user_id}, type={self.assessment_type}, direction={self.trend_direction})>"
