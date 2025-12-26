"""Add Longitudinal Analysis Tables
Create database schema for time-series behavioral analysis and change detection.

Revision ID: 003_longitudinal_analysis
Revises: 002_add_analytics
Create Date: 2024-01-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_longitudinal_analysis'
down_revision = '002_add_analytics'
branch_labels = None
depends_on = None


def upgrade():
    """Create tables for longitudinal analysis and change detection."""

    # Time series behavioral metrics table
    op.create_table(
        'behavioral_time_series',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('team_id', sa.UUID(), nullable=True),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Numeric(15, 4), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),  # count, rate, duration, score
        sa.Column('time_bucket', sa.DateTime(timezone=True), nullable=False),  # hour/day/week bucket
        sa.Column('bucket_size', sa.String(20), nullable=False),  # hour, day, week, month
        sa.Column('context', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.Index('idx_behavioral_time_series_user_time', 'user_id', 'time_bucket'),
        sa.Index('idx_behavioral_time_series_metric_time', 'metric_name', 'time_bucket'),
        sa.Index('idx_behavioral_time_series_org_time', 'organization_id', 'time_bucket'),
        sa.UniqueConstraint('user_id', 'metric_name', 'time_bucket', 'bucket_size', name='uq_behavioral_time_series')
    )

    # Change detection events table
    op.create_table(
        'change_detection_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('change_type', sa.String(50), nullable=False),  # trend, level, variance, pattern
        sa.Column('detection_method', sa.String(50), nullable=False),  # cusum, edivisive, bayesian, ml
        sa.Column('change_point', sa.DateTime(timezone=True), nullable=False),
        sa.Column('baseline_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('baseline_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('post_change_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('baseline_mean', sa.Numeric(15, 4), nullable=False),
        sa.Column('post_change_mean', sa.Numeric(15, 4), nullable=False),
        sa.Column('change_magnitude', sa.Numeric(15, 4), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=False),
        sa.Column('statistic_value', sa.Numeric(15, 4), nullable=True),
        sa.Column('p_value', sa.Numeric(10, 6), nullable=True),
        sa.Column('significance_level', sa.Numeric(5, 4), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('impact_level', sa.String(20), nullable=False),  # low, medium, high, critical
        sa.Column('requires_attention', sa.Boolean(), default=False, nullable=False),
        sa.Column('investigated', sa.Boolean(), default=False, nullable=False),
        sa.Column('investigated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('investigated_by', sa.UUID(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['investigated_by'], ['users.id'], ),
        sa.Index('idx_change_detection_user_change', 'user_id', 'change_point'),
        sa.Index('idx_change_detection_metric', 'metric_name', 'change_point'),
        sa.Index('idx_change_detection_impact', 'impact_level', 'requires_attention')
    )

    # Trend analysis table
    op.create_table(
        'trend_analysis',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('analysis_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('analysis_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('trend_direction', sa.String(20), nullable=False),  # increasing, decreasing, stable
        sa.Column('trend_slope', sa.Numeric(15, 8), nullable=False),
        sa.Column('trend_intercept', sa.Numeric(15, 8), nullable=False),
        sa.Column('r_squared', sa.Numeric(5, 4), nullable=False),
        sa.Column('p_value', sa.Numeric(10, 6), nullable=False),
        sa.Column('seasonal_component', sa.Boolean(), default=False, nullable=False),
        sa.Column('seasonal_period', sa.Integer(), nullable=True),
        sa.Column('seasonal_strength', sa.Numeric(5, 4), nullable=True),
        sa.Column('confidence_level', sa.Numeric(5, 4), nullable=False),
        sa.Column('forecast_next_period', sa.Numeric(15, 4), nullable=True),
        sa.Column('forecast_confidence_lower', sa.Numeric(15, 4), nullable=True),
        sa.Column('forecast_confidence_upper', sa.Numeric(15, 4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.Index('idx_trend_analysis_user_metric', 'user_id', 'metric_name'),
        sa.Index('idx_trend_analysis_period', 'analysis_period_start', 'analysis_period_end'),
        sa.UniqueConstraint('user_id', 'metric_name', 'analysis_period_start', 'analysis_period_end', name='uq_trend_analysis')
    )

    # User behavior baseline table
    op.create_table(
        'behavioral_baselines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('baseline_type', sa.String(50), nullable=False),  # personal, peer_group, organizational
        sa.Column('baseline_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('baseline_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('mean_value', sa.Numeric(15, 4), nullable=False),
        sa.Column('median_value', sa.Numeric(15, 4), nullable=False),
        sa.Column('std_deviation', sa.Numeric(15, 4), nullable=False),
        sa.Column('min_value', sa.Numeric(15, 4), nullable=False),
        sa.Column('max_value', sa.Numeric(15, 4), nullable=False),
        sa.Column('percentile_25', sa.Numeric(15, 4), nullable=False),
        sa.Column('percentile_75', sa.Numeric(15, 4), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('confidence_level', sa.Numeric(5, 4), nullable=False),
        sa.Column('margin_of_error', sa.Numeric(15, 4), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.Index('idx_behavioral_baselines_user_metric', 'user_id', 'metric_name'),
        sa.Index('idx_behavioral_baselines_type', 'baseline_type', 'is_active'),
        sa.UniqueConstraint('user_id', 'metric_name', 'baseline_type', 'baseline_period_start', name='uq_behavioral_baselines')
    )

    # Longitudinal cohort analysis table
    op.create_table(
        'longitudinal_cohorts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('cohort_name', sa.String(100), nullable=False),
        sa.Column('cohort_definition', postgresql.JSONB(), nullable=False),  # criteria for cohort membership
        sa.Column('cohort_type', sa.String(50), nullable=False),  # static, dynamic, time_based
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cohort_name', name='uq_longitudinal_cohorts')
    )

    # Cohort membership table
    op.create_table(
        'cohort_memberships',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('cohort_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cohort_id'], ['longitudinal_cohorts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.Index('idx_cohort_memberships_cohort_active', 'cohort_id', 'is_active'),
        sa.Index('idx_cohort_memberships_user', 'user_id'),
        sa.UniqueConstraint('cohort_id', 'user_id', 'joined_at', name='uq_cohort_memberships')
    )

    # Comparative analysis results table
    op.create_table(
        'comparative_analysis',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('analysis_name', sa.String(100), nullable=False),
        sa.Column('analysis_type', sa.String(50), nullable=False),  # cohort_comparison, time_comparison, ab_test
        sa.Column('control_group', postgresql.JSONB(), nullable=True),
        sa.Column('treatment_group', postgresql.JSONB(), nullable=True),
        sa.Column('comparison_period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('comparison_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metrics_analyzed', postgresql.JSONB(), nullable=False),
        sa.Column('statistical_tests', postgresql.JSONB(), nullable=False),
        sa.Column('effect_sizes', postgresql.JSONB(), nullable=False),
        sa.Column('confidence_intervals', postgresql.JSONB(), nullable=False),
        sa.Column('significance_results', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.Index('idx_comparative_analysis_type', 'analysis_type'),
        sa.Index('idx_comparative_analysis_period', 'comparison_period_start', 'comparison_period_end')
    )

    # Retention analysis table
    op.create_table(
        'retention_analysis',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('cohort_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('initial_period', sa.DateTime(timezone=True), nullable=False),
        sa.Column('retention_periods', postgresql.JSONB(), nullable=False),  # Period-by-period retention data
        sa.Column('retention_rate_7d', sa.Numeric(5, 4), nullable=True),
        sa.Column('retention_rate_30d', sa.Numeric(5, 4), nullable=True),
        sa.Column('retention_rate_90d', sa.Numeric(5, 4), nullable=True),
        sa.Column('churn_prediction_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cohort_id'], ['longitudinal_cohorts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.Index('idx_retention_analysis_cohort', 'cohort_id'),
        sa.Index('idx_retention_analysis_user', 'user_id'),
        sa.Index('idx_retention_analysis_churn', 'churn_prediction_score')
    )

    # Add comments to tables
    op.execute("COMMENT ON TABLE behavioral_time_series IS 'Time series data for behavioral metrics analysis'")
    op.execute("COMMENT ON TABLE change_detection_events IS 'Detected changes in behavioral patterns over time'")
    op.execute("COMMENT ON TABLE trend_analysis IS 'Statistical trend analysis results for user metrics'")
    op.execute("COMMENT ON TABLE behavioral_baselines IS 'Baseline metrics for behavioral comparison'")
    op.execute("COMMENT ON TABLE longitudinal_cohorts IS 'Definition of user cohorts for longitudinal analysis'")
    op.execute("COMMENT ON TABLE cohort_memberships IS 'User membership in longitudinal cohorts'")
    op.execute("COMMENT ON TABLE comparative_analysis IS 'Results of comparative behavioral analysis'")
    op.execute("COMMENT ON TABLE retention_analysis IS 'User retention and churn analysis over time'")


def downgrade():
    """Drop longitudinal analysis tables."""
    op.drop_table('retention_analysis')
    op.drop_table('comparative_analysis')
    op.drop_table('cohort_memberships')
    op.drop_table('longitudinal_cohorts')
    op.drop_table('behavioral_baselines')
    op.drop_table('trend_analysis')
    op.drop_table('change_detection_events')
    op.drop_table('behavioral_time_series')