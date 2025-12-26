"""Add data anonymization and research export tables

Revision ID: 006_add_data_anonymization_tables
Revises: 005_add_growth_trajectories_tables
Create Date: 2025-11-16 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006_add_data_anonymization_tables'
down_revision: Union[str, None] = '005_add_growth_trajectories_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create data anonymization and research export tables"""

    # Anonymization algorithms table
    op.create_table(
        'anonymization_algorithms',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('algorithm_name', sa.String(length=100), nullable=False),
        sa.Column('algorithm_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('privacy_risk_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('data_utility_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('k_anonymity_level', sa.Integer(), nullable=True),
        sa.Column('l_diversity_level', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('t_closeness_threshold', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('is_compliant_with_standards', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('validation_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('performance_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('privacy_risk_score >= 0 AND privacy_risk_score <= 1', name='check_privacy_risk_range'),
        sa.CheckConstraint('data_utility_score >= 0 AND data_utility_score <= 1', name='check_data_utility_range'),
        sa.CheckConstraint('k_anonymity_level > 0', name='check_k_anonymity_positive'),
        sa.CheckConstraint("algorithm_type IN ('generalization', 'suppression', 'perturbation', 'synthetic_data', 'differential_privacy', 'k_anonymity', 'l_diversity', 't_closeness')", name='check_algorithm_type')
    )
    op.create_index(op.f('ix_anonymization_algorithms_id'), 'anonymization_algorithms', ['id'], unique=False)
    op.create_index('ix_anonymization_algorithms_name', 'anonymization_algorithms', ['algorithm_name'], unique=False)
    op.create_index('ix_anonymization_algorithms_type', 'anonymization_algorithms', ['algorithm_type'], unique=False)
    op.create_index('ix_anonymization_algorithms_active', 'anonymization_algorithms', ['is_active'], unique=False)

    # Data anonymization jobs table
    op.create_table(
        'data_anonymization_jobs',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requester_id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('data_source_tables', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('filter_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('anonymization_algorithm_id', sa.Uuid(), nullable=False),
        sa.Column('algorithm_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quasi_identifiers', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('sensitive_attributes', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('progress_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('estimated_completion_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_completion_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('input_record_count', sa.Integer(), nullable=True),
        sa.Column('output_record_count', sa.Integer(), nullable=True),
        sa.Column('privacy_risk_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_utility_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_file_path', sa.String(length=500), nullable=True),
        sa.Column('output_file_hash', sa.String(length=64), nullable=True),
        sa.Column('export_format', sa.String(length=20), nullable=False),
        sa.Column('research_purpose', sa.Text(), nullable=True),
        sa.Column('data_sharing_agreement', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('compliance certifications', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['anonymization_algorithm_id'], ['anonymization_algorithms.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('progress_percentage >= 0 AND progress_percentage <= 100', name='check_progress_range'),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused')", name='check_job_status'),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name='check_job_priority'),
        sa.CheckConstraint("export_format IN ('csv', 'json', 'parquet', 'excel', 'spss', 'sas', 'stata')", name='check_export_format')
    )
    op.create_index(op.f('ix_data_anonymization_jobs_id'), 'data_anonymization_jobs', ['id'], unique=False)
    op.create_index('ix_data_anonymization_jobs_requester', 'data_anonymization_jobs', ['requester_id'], unique=False)
    op.create_index('ix_data_anonymization_jobs_organization', 'data_anonymization_jobs', ['organization_id'], unique=False)
    op.create_index('ix_data_anonymization_jobs_status', 'data_anonymization_jobs', ['status'], unique=False)
    op.create_index('ix_data_anonymization_jobs_created', 'data_anonymization_jobs', ['created_at'], unique=False)

    # Anonymization audit logs table
    op.create_table(
        'anonymization_audit_logs',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('job_id', sa.Uuid(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('action_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('user_role', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('affected_records', sa.Integer(), nullable=True),
        sa.Column('fields_anonymized', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('anonymization_method_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('privacy_impact_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_before_anonymization', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_after_anonymization', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_score_before', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('risk_score_after', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('reversibility_assessment', sa.String(length=20), nullable=True),
        sa.Column('compliance_check_passed', sa.Boolean(), nullable=True),
        sa.Column('violations_detected', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('remediation_actions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('additional_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['data_anonymization_jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("action_type IN ('created', 'started', 'completed', 'failed', 'cancelled', 'paused', 'resumed', 'data_accessed', 'data_modified', 'export_downloaded')", name='check_action_type'),
        sa.CheckConstraint("reversibility_assessment IN ('reversible', 'partially_reversible', 'irreversible', 'unknown')", name='check_reversibility')
    )
    op.create_index(op.f('ix_anonymization_audit_logs_id'), 'anonymization_audit_logs', ['id'], unique=False)
    op.create_index('ix_anonymization_audit_logs_job', 'anonymization_audit_logs', ['job_id'], unique=False)
    op.create_index('ix_anonymization_audit_logs_user', 'anonymization_audit_logs', ['user_id'], unique=False)
    op.create_index('ix_anonymization_audit_logs_timestamp', 'anonymization_audit_logs', ['action_timestamp'], unique=False)
    op.create_index('ix_anonymization_audit_logs_action', 'anonymization_audit_logs', ['action_type'], unique=False)

    # Research data exports table
    op.create_table(
        'research_data_exports',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('export_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('research_project_id', sa.String(length=100), nullable=True),
        sa.Column('researcher_id', sa.Uuid(), nullable=False),
        sa.Column('institution_name', sa.String(length=255), nullable=True),
        sa.Column('research_purpose', sa.Text(), nullable=True),
        sa.Column('anonymization_job_id', sa.Uuid(), nullable=True),
        sa.Column('export_type', sa.String(length=50), nullable=False),
        sa.Column('data_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('population_description', sa.Text(), nullable=True),
        sa.Column('inclusion_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('exclusion_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('variables_included', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('variables_excluded', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('data_dictionary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('anonymization_level', sa.String(length=30), nullable=False),
        sa.Column('privacy_guarantee', sa.Text(), nullable=True),
        sa.Column('usage_restrictions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_sharing_license', sa.String(length=50), nullable=True),
        sa.Column('citation_requirements', sa.Text(), nullable=True),
        sa.Column('embargo_period_days', sa.Integer(), nullable=True),
        sa.Column('access_method', sa.String(length=50), nullable=False),
        sa.Column('download_url', sa.String(length=500), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('access_log', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_quality_report', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ethics_approval_reference', sa.String(length=100), nullable=True),
        sa.Column('irb_approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('approval_status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('approved_by', sa.Uuid(), nullable=True),
        sa.Column('approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['anonymization_job_id'], ['data_anonymization_jobs.id'], ),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['researcher_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('sample_size > 0', name='check_sample_size_positive'),
        sa.CheckConstraint('embargo_period_days >= 0', name='check_embargo_non_negative'),
        sa.CheckConstraint("export_type IN ('longitudinal', 'cross_sectional', 'case_control', 'cohort', 'experimental', 'observational')", name='check_export_type'),
        sa.CheckConstraint("anonymization_level IN ('minimal', 'standard', 'enhanced', 'maximum')", name='check_anonymization_level'),
        sa.CheckConstraint("access_method IN ('direct_download', 'secure_transfer', 'api_access', 'research_portal')", name='check_access_method'),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'expired', 'revoked')", name='check_export_status'),
        sa.CheckConstraint("approval_status IN ('pending', 'approved', 'rejected', 'requires_review')", name='check_approval_status')
    )
    op.create_index(op.f('ix_research_data_exports_id'), 'research_data_exports', ['id'], unique=False)
    op.create_index('ix_research_data_exports_researcher', 'research_data_exports', ['researcher_id'], unique=False)
    op.create_index('ix_research_data_exports_project', 'research_data_exports', ['research_project_id'], unique=False)
    op.create_index('ix_research_data_exports_status', 'research_data_exports', ['status'], unique=False)
    op.create_index('ix_research_data_exports_approval', 'research_data_exports', ['approval_status'], unique=False)
    op.create_index('ix_research_data_exports_created', 'research_data_exports', ['created_at'], unique=False)

    # Data retention policies table
    op.create_table(
        'data_retention_policies',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('policy_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organization_id', sa.Uuid(), nullable=True),
        sa.Column('data_types', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('retention_period_days', sa.Integer(), nullable=False),
        sa.Column('anonymization_before_delete', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('anonymization_method', sa.String(length=50), nullable=True),
        sa.Column('legal_basis', sa.String(length=100), nullable=True),
        sa.Column('regulatory_requirements', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('auto_delete_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notification_period_days', sa.Integer(), nullable=True),
        sa.Column('exception_conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('approval_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('approved_by', sa.Uuid(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_applied', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_scheduled', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('retention_period_days > 0', name='check_retention_positive'),
        sa.CheckConstraint('notification_period_days >= 0', name='check_notification_non_negative'),
        sa.CheckConstraint("anonymization_method IN ('generalization', 'suppression', 'perturbation', 'aggregation', 'pseudonymization')", name='check_retention_anonymization_method')
    )
    op.create_index(op.f('ix_data_retention_policies_id'), 'data_retention_policies', ['id'], unique=False)
    op.create_index('ix_data_retention_policies_organization', 'data_retention_policies', ['organization_id'], unique=False)
    op.create_index('ix_data_retention_policies_active', 'data_retention_policies', ['is_active'], unique=False)
    op.create_index('ix_data_retention_policies_next', 'data_retention_policies', ['next_scheduled'], unique=False)

    # Data access requests table
    op.create_table(
        'data_access_requests',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('request_id', sa.String(length=50), nullable=False, unique=True),
        sa.Column('researcher_id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=True),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('data_purpose', sa.Text(), nullable=False),
        sa.Column('research_question', sa.Text(), nullable=True),
        sa.Column('methodology', sa.Text(), nullable=True),
        sa.Column('requested_data_tables', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('requested_variables', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('time_period_requested', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sample_size_requested', sa.Integer(), nullable=True),
        sa.Column('anonymization_level_required', sa.String(length=30), nullable=False),
        sa.Column('data_use_agreement', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_protection_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('publication_plan', sa.Text(), nullable=True),
        sa.Column('collaborating_institutions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('funding_sources', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ethics_committee_approval', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('reviewer_id', sa.Uuid(), nullable=True),
        sa.Column('review_comments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('approval_conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('approved_by', sa.Uuid(), nullable=True),
        sa.Column('approval_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('data_access_granted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('access_expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_usage_reporting_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('reporting_frequency', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['researcher_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('sample_size_requested > 0', name='check_requested_sample_positive'),
        sa.CheckConstraint("request_type IN ('research', 'commercial', 'educational', 'government', 'non_profit')", name='check_request_type'),
        sa.CheckConstraint("anonymization_level_required IN ('minimal', 'standard', 'enhanced', 'maximum')", name='check_required_anonymization'),
        sa.CheckConstraint("status IN ('pending', 'under_review', 'approved', 'rejected', 'cancelled', 'expired')", name='check_access_request_status'),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name='check_access_priority'),
        sa.CheckConstraint("reporting_frequency IN ('weekly', 'monthly', 'quarterly', 'annually', 'upon_completion')", name='check_reporting_frequency')
    )
    op.create_index(op.f('ix_data_access_requests_id'), 'data_access_requests', ['id'], unique=False)
    op.create_index('ix_data_access_requests_request_id', 'data_access_requests', ['request_id'], unique=True)
    op.create_index('ix_data_access_requests_researcher', 'data_access_requests', ['researcher_id'], unique=False)
    op.create_index('ix_data_access_requests_status', 'data_access_requests', ['status'], unique=False)
    op.create_index('ix_data_access_requests_created', 'data_access_requests', ['created_at'], unique=False)

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
        CREATE TRIGGER update_anonymization_algorithms_updated_at
            BEFORE UPDATE ON anonymization_algorithms
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_data_anonymization_jobs_updated_at
            BEFORE UPDATE ON data_anonymization_jobs
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_research_data_exports_updated_at
            BEFORE UPDATE ON research_data_exports
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_data_retention_policies_updated_at
            BEFORE UPDATE ON data_retention_policies
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_data_access_requests_updated_at
            BEFORE UPDATE ON data_access_requests
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop data anonymization and research export tables"""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_data_access_requests_updated_at ON data_access_requests")
    op.execute("DROP TRIGGER IF EXISTS update_data_retention_policies_updated_at ON data_retention_policies")
    op.execute("DROP TRIGGER IF EXISTS update_research_data_exports_updated_at ON research_data_exports")
    op.execute("DROP TRIGGER IF EXISTS update_data_anonymization_jobs_updated_at ON data_anonymization_jobs")
    op.execute("DROP TRIGGER IF EXISTS update_anonymization_algorithms_updated_at ON anonymization_algorithms")

    # Drop tables in reverse order of creation
    op.drop_index('ix_data_access_requests_created', table_name='data_access_requests')
    op.drop_index('ix_data_access_requests_status', table_name='data_access_requests')
    op.drop_index('ix_data_access_requests_researcher', table_name='data_access_requests')
    op.drop_index('ix_data_access_requests_request_id', table_name='data_access_requests')
    op.drop_index(op.f('ix_data_access_requests_id'), table_name='data_access_requests')
    op.drop_table('data_access_requests')

    op.drop_index('ix_data_retention_policies_next', table_name='data_retention_policies')
    op.drop_index('ix_data_retention_policies_active', table_name='data_retention_policies')
    op.drop_index('ix_data_retention_policies_organization', table_name='data_retention_policies')
    op.drop_index(op.f('ix_data_retention_policies_id'), table_name='data_retention_policies')
    op.drop_table('data_retention_policies')

    op.drop_index('ix_research_data_exports_created', table_name='research_data_exports')
    op.drop_index('ix_research_data_exports_approval', table_name='research_data_exports')
    op.drop_index('ix_research_data_exports_status', table_name='research_data_exports')
    op.drop_index('ix_research_data_exports_project', table_name='research_data_exports')
    op.drop_index('ix_research_data_exports_researcher', table_name='research_data_exports')
    op.drop_index(op.f('ix_research_data_exports_id'), table_name='research_data_exports')
    op.drop_table('research_data_exports')

    op.drop_index('ix_anonymization_audit_logs_action', table_name='anonymization_audit_logs')
    op.drop_index('ix_anonymization_audit_logs_timestamp', table_name='anonymization_audit_logs')
    op.drop_index('ix_anonymization_audit_logs_user', table_name='anonymization_audit_logs')
    op.drop_index('ix_anonymization_audit_logs_job', table_name='anonymization_audit_logs')
    op.drop_index(op.f('ix_anonymization_audit_logs_id'), table_name='anonymization_audit_logs')
    op.drop_table('anonymization_audit_logs')

    op.drop_index('ix_data_anonymization_jobs_created', table_name='data_anonymization_jobs')
    op.drop_index('ix_data_anonymization_jobs_status', table_name='data_anonymization_jobs')
    op.drop_index('ix_data_anonymization_jobs_organization', table_name='data_anonymization_jobs')
    op.drop_index('ix_data_anonymization_jobs_requester', table_name='data_anonymization_jobs')
    op.drop_index(op.f('ix_data_anonymization_jobs_id'), table_name='data_anonymization_jobs')
    op.drop_table('data_anonymization_jobs')

    op.drop_index('ix_anonymization_algorithms_active', table_name='anonymization_algorithms')
    op.drop_index('ix_anonymization_algorithms_type', table_name='anonymization_algorithms')
    op.drop_index('ix_anonymization_algorithms_name', table_name='anonymization_algorithms')
    op.drop_index(op.f('ix_anonymization_algorithms_id'), table_name='anonymization_algorithms')
    op.drop_table('anonymization_algorithms')

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")