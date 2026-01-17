"""Add growth trajectories tracking tables

Revision ID: 005_add_growth_trajectories_tables
Revises: 004_add_intervention_effectiveness_tables
Create Date: 2025-11-16 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_add_growth_trajectories_tables'
down_revision: Union[str, None] = '004_add_intervention_effectiveness_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create growth trajectories tracking tables"""

    # Growth trajectory definitions table
    op.create_table(
        'growth_trajectories',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('team_id', sa.Uuid(), nullable=True),
        sa.Column('organization_id', sa.Uuid(), nullable=True),
        sa.Column('trajectory_type', sa.String(length=50), nullable=False),
        sa.Column('competency_domain', sa.String(length=100), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('model_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('training_data_points', sa.Integer(), nullable=False),
        sa.Column('training_start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('training_end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('model_accuracy', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('confidence_level', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('prediction_horizon_days', sa.Integer(), nullable=False),
        sa.Column('growth_velocity', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('acceleration_rate', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('asymptotic_potential', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('growth_stage', sa.String(length=30), nullable=True),
        sa.Column('plateau_probability', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('inflection_point_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('development_recommendations', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('optimal_intervention_timing', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('prediction_horizon_days > 0', name='check_positive_horizon'),
        sa.CheckConstraint('confidence_level >= 0 AND confidence_level <= 1', name='check_confidence_range'),
        sa.CheckConstraint("trajectory_type IN ('individual', 'team', 'role_based', 'competency_based')", name='check_trajectory_type'),
        sa.CheckConstraint("model_type IN ('linear', 'exponential', 'logistic', 'power_law', 'polynomial', 'sigmoidal')", name='check_model_type')
    )
    op.create_index(op.f('ix_growth_trajectories_id'), 'growth_trajectories', ['id'], unique=False)
    op.create_index('ix_growth_trajectories_user', 'growth_trajectories', ['user_id'], unique=False)
    op.create_index('ix_growth_trajectories_domain', 'growth_trajectories', ['competency_domain'], unique=False)
    op.create_index('ix_growth_trajectories_type', 'growth_trajectories', ['trajectory_type'], unique=False)
    op.create_index('ix_growth_trajectories_model', 'growth_trajectories', ['model_type'], unique=False)
    op.create_index('ix_growth_trajectories_dates', 'growth_trajectories', ['training_start_date', 'training_end_date'], unique=False)

    # Trajectory predictions table
    op.create_table(
        'trajectory_predictions',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('trajectory_id', sa.Uuid(), nullable=False),
        sa.Column('prediction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('predicted_value', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('confidence_interval_lower', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('confidence_interval_upper', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('prediction_accuracy', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('growth_rate', sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column('milestone_achieved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('risk_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('external_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('development_opportunities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('potential_barriers', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('intervention_suggestions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('prediction_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trajectory_id'], ['growth_trajectories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trajectory_predictions_id'), 'trajectory_predictions', ['id'], unique=False)
    op.create_index('ix_trajectory_predictions_trajectory', 'trajectory_predictions', ['trajectory_id'], unique=False)
    op.create_index('ix_trajectory_predictions_date', 'trajectory_predictions', ['prediction_date'], unique=False)
    op.create_index('ix_trajectory_predictions_milestone', 'trajectory_predictions', ['milestone_achieved'], unique=False)

    # Growth milestones table
    op.create_table(
        'growth_milestones',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('trajectory_id', sa.Uuid(), nullable=False),
        sa.Column('milestone_name', sa.String(length=255), nullable=False),
        sa.Column('milestone_type', sa.String(length=50), nullable=False),
        sa.Column('target_value', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('target_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('achievement_probability', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('current_progress', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('milestone_status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('difficulty_level', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('required_resources', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('prerequisite_skills', postgresql.ARRAY(sa.String()), nullable=None),
        sa.Column('success_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('achievement_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('achievement_notes', sa.Text(), nullable=True),
        sa.Column('celebration_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trajectory_id'], ['growth_trajectories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("achievement_probability >= 0 AND achievement_probability <= 1", name='check_achievement_probability'),
        sa.CheckConstraint("current_progress >= 0 AND current_progress <= 1", name='check_progress_range'),
        sa.CheckConstraint("milestone_type IN ('skill', 'competency', 'role', 'project', 'certification', 'performance')", name='check_milestone_type'),
        sa.CheckConstraint("milestone_status IN ('pending', 'in_progress', 'achieved', 'delayed', 'cancelled')", name='check_milestone_status'),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name='check_milestone_priority'),
        sa.CheckConstraint("difficulty_level IN ('easy', 'medium', 'hard', 'expert')", name='check_difficulty_level')
    )
    op.create_index(op.f('ix_growth_milestones_id'), 'growth_milestones', ['id'], unique=False)
    op.create_index('ix_growth_milestones_trajectory', 'growth_milestones', ['trajectory_id'], unique=False)
    op.create_index('ix_growth_milestones_status', 'growth_milestones', ['milestone_status'], unique=False)
    op.create_index('ix_growth_milestones_priority', 'growth_milestones', ['priority'], unique=False)
    op.create_index('ix_growth_milestones_date', 'growth_milestones', ['target_date'], unique=False)

    # Growth potential analysis table
    op.create_table(
        'growth_potential_analysis',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('analysis_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('potential_score', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('potential_category', sa.String(length=30), nullable=False),
        sa.Column('growth_readiness', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('learning_agility', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('adaptability_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('time_to_mastery', sa.Integer(), nullable=True),
        sa.Column('ceiling_estimate', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('growth_velocity_percentile', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('key_drivers', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('limiting_factors', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('development_focus_areas', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('optimal_development_path', postgresql.ARRAY(sa.String()), nullable=None),
        sa.Column('career_trajectory_alignment', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('success_probability', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('roi_estimate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('analysis_methodology', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('comparative_benchmarks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('next_review_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('potential_score >= 0 AND potential_score <= 1', name='check_potential_score_range'),
        sa.CheckConstraint("potential_category IN ('low', 'medium', 'high', 'very_high', 'exceptional')", name='check_potential_category'),
        sa.CheckConstraint('growth_readiness >= 0 AND growth_readiness <= 1', name='check_growth_readiness_range'),
        sa.CheckConstraint('learning_agility >= 0 AND learning_agility <= 1', name='check_learning_agility_range'),
        sa.CheckConstraint('adaptability_score >= 0 AND adaptability_score <= 1', name='check_adaptability_score_range')
    )
    op.create_index(op.f('ix_growth_potential_analysis_id'), 'growth_potential_analysis', ['id'], unique=False)
    op.create_index('ix_growth_potential_analysis_user', 'growth_potential_analysis', ['user_id'], unique=False)
    op.create_index('ix_growth_potential_analysis_date', 'growth_potential_analysis', ['analysis_date'], unique=False)
    op.create_index('ix_growth_potential_analysis_category', 'growth_potential_analysis', ['potential_category'], unique=False)
    op.create_index('ix_growth_potential_analysis_score', 'growth_potential_analysis', ['potential_score'], unique=False)

    # Comparative trajectory benchmarks table
    op.create_table(
        'trajectory_benchmarks',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('competency_domain', sa.String(length=100), nullable=False),
        sa.Column('role_category', sa.String(length=100), nullable=False),
        sa.Column('experience_level', sa.String(length=50), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('median_trajectory', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('percentile_25_trajectory', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('percentile_75_trajectory', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('growth_velocity_stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('time_to_mastery_stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('plateau_probability_stats', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('key_success_factors', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('common_barriers', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('optimal_development_patterns', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('industry_specific_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('benchmark_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_collection_period', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("experience_level IN ('entry', 'junior', 'mid', 'senior', 'lead', 'principal')", name='check_experience_level')
    )
    op.create_index(op.f('ix_trajectory_benchmarks_id'), 'trajectory_benchmarks', ['id'], unique=False)
    op.create_index('ix_trajectory_benchmarks_domain', 'trajectory_benchmarks', ['competency_domain'], unique=False)
    op.create_index('ix_trajectory_benchmarks_role', 'trajectory_benchmarks', ['role_category'], unique=False)
    op.create_index('ix_trajectory_benchmarks_experience', 'trajectory_benchmarks', ['experience_level'], unique=False)
    op.create_index('ix_trajectory_benchmarks_unique', 'trajectory_benchmarks', ['competency_domain', 'role_category', 'experience_level'], unique=True)

    # Growth trajectory simulations table
    op.create_table(
        'trajectory_simulations',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('trajectory_id', sa.Uuid(), nullable=False),
        sa.Column('simulation_type', sa.String(length=50), nullable=False),
        sa.Column('scenario_description', sa.Text(), nullable=True),
        sa.Column('intervention_scenario', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('environmental_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('simulated_trajectory', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('outcome_probability', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('success_probability', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('expected_time_to_goal', sa.Integer(), nullable=True),
        sa.Column('confidence_in_simulation', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('sensitivity_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('resource_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('alternative_scenarios', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('simulation_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('actionable_insights', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('recommended_actions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trajectory_id'], ['growth_trajectories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("simulation_type IN ('intervention', 'career_change', 'skill_development', 'role_transition', 'leadership', 'environmental')", name='check_simulation_type'),
        sa.CheckConstraint('confidence_in_simulation >= 0 AND confidence_in_simulation <= 1', name='check_simulation_confidence')
    )
    op.create_index(op.f('ix_trajectory_simulations_id'), 'trajectory_simulations', ['id'], unique=False)
    op.create_index('ix_trajectory_simulations_trajectory', 'trajectory_simulations', ['trajectory_id'], unique=False)
    op.create_index('ix_trajectory_simulations_type', 'trajectory_simulations', ['simulation_type'], unique=False)

    # Trigger to update updated_at columns
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Add triggers for updated_at
    op.execute("""
        CREATE TRIGGER update_growth_trajectories_updated_at
            BEFORE UPDATE ON growth_trajectories
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_growth_milestones_updated_at
            BEFORE UPDATE ON growth_milestones
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop growth trajectories tracking tables"""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_growth_trajectories_updated_at ON growth_trajectories")
    op.execute("DROP TRIGGER IF EXISTS update_growth_milestones_updated_at ON growth_milestones")

    # Drop tables in reverse order of creation
    op.drop_index('ix_trajectory_simulations_type', table_name='trajectory_simulations')
    op.drop_index('ix_trajectory_simulations_trajectory', table_name='trajectory_simulations')
    op.drop_index(op.f('ix_trajectory_simulations_id'), table_name='trajectory_simulations')
    op.drop_table('trajectory_simulations')

    op.drop_index('ix_trajectory_benchmarks_unique', table_name='trajectory_benchmarks')
    op.drop_index('ix_trajectory_benchmarks_experience', table_name='trajectory_benchmarks')
    op.drop_index('ix_trajectory_benchmarks_role', table_name='trajectory_benchmarks')
    op.drop_index('ix_trajectory_benchmarks_domain', table_name='trajectory_benchmarks')
    op.drop_index(op.f('ix_trajectory_benchmarks_id'), table_name='trajectory_benchmarks')
    op.drop_table('trajectory_benchmarks')

    op.drop_index('ix_growth_potential_analysis_score', table_name='growth_potential_analysis')
    op.drop_index('ix_growth_potential_analysis_category', table_name='growth_potential_analysis')
    op.drop_index('ix_growth_potential_analysis_date', table_name='growth_potential_analysis')
    op.drop_index('ix_growth_potential_analysis_user', table_name='growth_potential_analysis')
    op.drop_index(op.f('ix_growth_potential_analysis_id'), table_name='growth_potential_analysis')
    op.drop_table('growth_potential_analysis')

    op.drop_index('ix_growth_milestones_date', table_name='growth_milestones')
    op.drop_index('ix_growth_milestones_priority', table_name='growth_milestones')
    op.drop_index('ix_growth_milestones_status', table_name='growth_milestones')
    op.drop_index('ix_growth_milestones_trajectory', table_name='growth_milestones')
    op.drop_index(op.f('ix_growth_milestones_id'), table_name='growth_milestones')
    op.drop_table('growth_milestones')

    op.drop_index('ix_trajectory_predictions_milestone', table_name='trajectory_predictions')
    op.drop_index('ix_trajectory_predictions_date', table_name='trajectory_predictions')
    op.drop_index('ix_trajectory_predictions_trajectory', table_name='trajectory_predictions')
    op.drop_index(op.f('ix_trajectory_predictions_id'), table_name='trajectory_predictions')
    op.drop_table('trajectory_predictions')

    op.drop_index('ix_growth_trajectories_dates', table_name='growth_trajectories')
    op.drop_index('ix_growth_trajectories_model', table_name='growth_trajectories')
    op.drop_index('ix_growth_trajectories_type', table_name='growth_trajectories')
    op.drop_index('ix_growth_trajectories_domain', table_name='growth_trajectories')
    op.drop_index('ix_growth_trajectories_user', table_name='growth_trajectories')
    op.drop_index(op.f('ix_growth_trajectories_id'), table_name='growth_trajectories')
    op.drop_table('growth_trajectories')

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
