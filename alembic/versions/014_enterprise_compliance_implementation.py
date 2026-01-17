"""Enterprise compliance implementation

Revision ID: 014_enterprise_compliance_implementation
Revises: 013_add_critical_performance_indexes
Create Date: 2024-12-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_enterprise_compliance_implementation'
down_revision = '013_add_critical_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create enterprise compliance tables and indexes"""

    # Create audit_logs table for SOC 2 and ISO 27001 compliance
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('event_type', sa.String(length=100), nullable=False, index=True),
        sa.Column('severity', sa.String(length=20), nullable=False, index=True),
        sa.Column('user_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('resource_accessed', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.Column('compliance_standards', sa.Text(), nullable=True),  # JSON string
        sa.Column('metadata', sa.Text(), nullable=True),  # JSON string
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Index('idx_audit_logs_timestamp', 'timestamp'),
        sa.Index('idx_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        sa.Index('idx_audit_logs_event_type_timestamp', 'event_type', 'timestamp'),
        sa.Index('idx_audit_logs_severity_timestamp', 'severity', 'timestamp'),
        sa.Index('idx_audit_logs_outcome', 'outcome')
    )

    # Create data_processing_records table for GDPR compliance
    op.create_table(
        'data_processing_records',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('processing_purpose', sa.Text(), nullable=False),
        sa.Column('legal_basis', sa.String(length=100), nullable=False),
        sa.Column('data_categories', sa.Text(), nullable=False),  # JSON string
        sa.Column('retention_period', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Index('idx_data_processing_user_id', 'user_id'),
        sa.Index('idx_data_processing_legal_basis', 'legal_basis')
    )

    # Create security_incidents table for incident tracking
    op.create_table(
        'security_incidents',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('incident_id', sa.String(length=32), unique=True, nullable=False),
        sa.Column('trigger_event_id', sa.String(length=32), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, default='open'),
        sa.Column('affected_systems', sa.Text(), nullable=True),  # JSON array
        sa.Column('required_actions', sa.Text(), nullable=True),  # JSON array
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Index('idx_security_incidents_severity', 'severity'),
        sa.Index('idx_security_incidents_status', 'status'),
        sa.Index('idx_security_incidents_created_at', 'created_at')
    )

    # Create user_consent_records table for GDPR consent management
    op.create_table(
        'user_consent_records',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('consent_type', sa.String(length=100), nullable=False),
        sa.Column('consent_given', sa.Boolean(), nullable=False),
        sa.Column('consent_text', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('withdrawn_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Index('idx_user_consent_user_id', 'user_id'),
        sa.Index('idx_user_consent_type', 'consent_type'),
        sa.Index('idx_user_consent_valid', 'consent_given', 'valid_until')
    )

    # Create data_retention_policies table for GDPR and HIPAA compliance
    op.create_table(
        'data_retention_policies',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('data_type', sa.String(length=100), nullable=False, unique=True),
        sa.Column('retention_period_days', sa.Integer(), nullable=False),
        sa.Column('legal_basis', sa.String(length=200), nullable=False),
        sa.Column('auto_delete_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('notification_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Index('idx_retention_policies_data_type', 'data_type')
    )

    # Create encryption_keys table for key management
    op.create_table(
        'encryption_keys',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('key_name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('key_algorithm', sa.String(length=50), nullable=False),
        sa.Column('key_size', sa.Integer(), nullable=False),
        sa.Column('key_usage', sa.String(length=100), nullable=False),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('key_version', sa.Integer(), nullable=False, default=1),
        sa.Column('status', sa.String(length=20), nullable=False, default='active'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('rotated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Index('idx_encryption_keys_name', 'key_name'),
        sa.Index('idx_encryption_keys_status', 'status'),
        sa.Index('idx_encryption_keys_usage', 'key_usage')
    )

    # Add security columns to existing users table
    op.add_column('users', sa.Column('mfa_enabled', sa.Boolean(), nullable=False, default=False))
    op.add_column('users', sa.Column('mfa_secret', sa.String(length=32), nullable=True))
    op.add_column('users', sa.Column('last_security_review', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0))
    op.add_column('users', sa.Column('account_locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('gdpr_consent_given', sa.Boolean(), nullable=False, default=False))
    op.add_column('users', sa.Column('data_processing_consent', sa.Boolean(), nullable=False, default=False))
    op.add_column('users', sa.Column('marketing_consent', sa.Boolean(), nullable=False, default=False))
    op.add_column('users', sa.Column('security_question_hash', sa.String(length=255), nullable=True))

    # Add audit columns to assessments table
    op.add_column('assessments', sa.Column('data_classification', sa.String(length=20), nullable=False, default='internal'))
    op.add_column('assessments', sa.Column('retention_schedule', sa.DateTime(timezone=True), nullable=True))
    op.add_column('assessments', sa.Column('access_count', sa.Integer(), nullable=False, default=0))
    op.add_column('assessments', sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True))

    # Add encryption columns to assessment_responses table
    op.add_column('assessment_responses', sa.Column('response_encrypted', sa.Boolean(), nullable=False, default=False))
    op.add_column('assessment_responses', sa.Column('encryption_key_id', sa.String(length=32), nullable=True))

    # Create indexes for performance and security monitoring
    op.create_index('idx_users_mfa_enabled', 'users', ['mfa_enabled'])
    op.create_index('idx_users_account_locked', 'users', ['account_locked_until'])
    op.create_index('idx_users_last_security_review', 'users', ['last_security_review'])
    op.create_index('idx_assessments_classification', 'assessments', ['data_classification'])
    op.create_index('idx_assessments_retention', 'assessments', ['retention_schedule'])
    op.create_index('idx_assessments_last_accessed', 'assessments', ['last_accessed'])
    op.create_index('idx_assessment_responses_encrypted', 'assessment_responses', ['response_encrypted'])

    # Create partitioned audit_logs table for better performance (PostgreSQL specific)
    if op.get_bind().dialect.name == 'postgresql':
        # Create partitioned table structure for audit logs by month
        op.execute("""
            CREATE TABLE audit_logs_partitioned (
                LIKE audit_logs INCLUDING ALL
            ) PARTITION BY RANGE (timestamp);
        """)

        # Create initial partitions
        for month_offset in range(-2, 4):  # Past 2 months to next 3 months
            month_name = datetime.now().replace(day=1) + timedelta(days=month_offset * 30)
            partition_name = f"audit_logs_{month_name.strftime('%Y_%m')}"
            start_date = month_name
            end_date = month_name + timedelta(days=32)
            end_date = end_date.replace(day=1)  # First day of next month

            op.execute(f"""
                CREATE TABLE {partition_name}
                PARTITION OF audit_logs_partitioned
                FOR VALUES FROM ('{start_date}') TO ('{end_date}');
            """)

    # Insert default data retention policies
    op.execute("""
        INSERT INTO data_retention_policies (id, data_type, retention_period_days, legal_basis, auto_delete_enabled)
        VALUES
            ('dp_public_001', 'public_user_data', 2555, 'legitimate_interest', true),
            ('dp_confidential_001', 'assessment_results', 3650, 'contractual_necessity', true),
            ('dp_restricted_001', 'audit_logs', 2555, 'legal_requirement', true),
            ('dp_pii_001', 'personal_identifiable_info', 2555, 'consent', true),
            ('dp_phi_001', 'protected_health_info', 2190, 'hipaa_privacy_rule', true)
        ON CONFLICT (data_type) DO NOTHING;
    """)

    # Create stored procedures for automated cleanup
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_expired_audit_logs()
        RETURNS void AS $$
        BEGIN
            -- Delete audit logs older than 7 years (for compliance)
            DELETE FROM audit_logs
            WHERE timestamp < NOW() - INTERVAL '7 years';

            -- Log the cleanup operation
            INSERT INTO audit_logs (id, timestamp, event_type, severity, user_id, ip_address, resource_accessed, action, outcome)
            VALUES (
                substr(md5(random()::text), 1, 32),
                NOW(),
                'AUTOMATED_CLEANUP',
                'INFO',
                'system',
                '127.0.0.1',
                'audit_logs',
                'DELETE_EXPIRED',
                'success'
            );
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION rotate_encryption_keys()
        RETURNS void AS $$
        DECLARE
            key_record RECORD;
        BEGIN
            -- Deactivate old keys
            UPDATE encryption_keys
            SET status = 'deprecated', rotated_at = NOW()
            WHERE status = 'active'
            AND created_at < NOW() - INTERVAL '90 days';

            -- Create new encryption key (simplified - in production use proper key generation)
            INSERT INTO encryption_keys (id, key_name, key_algorithm, key_size, key_usage, encrypted_key)
            VALUES (
                substr(md5(random()::text), 1, 32),
                'data_encryption_' || EXTRACT(epoch FROM NOW()),
                'AES-256-GCM',
                256,
                'data_encryption',
                'placeholder_encrypted_key'  -- In production, use actual encrypted key
            );

            -- Log key rotation
            INSERT INTO audit_logs (id, timestamp, event_type, severity, user_id, ip_address, resource_accessed, action, outcome)
            VALUES (
                substr(md5(random()::text), 1, 32),
                NOW(),
                'ENCRYPTION_KEY_ROTATION',
                'INFO',
                'system',
                '127.0.0.1',
                'encryption_keys',
                'ROTATE_KEYS',
                'success'
            );
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Remove enterprise compliance tables and columns"""

    # Drop stored procedures
    op.execute("DROP FUNCTION IF EXISTS cleanup_expired_audit_logs()")
    op.execute("DROP FUNCTION IF EXISTS rotate_encryption_keys()")

    # Drop tables
    op.drop_table('encryption_keys')
    op.drop_table('data_retention_policies')
    op.drop_table('user_consent_records')
    op.drop_table('security_incidents')
    op.drop_table('data_processing_records')
    op.drop_table('audit_logs')

    # Drop partitioned table if it exists
    if op.get_bind().dialect.name == 'postgresql':
        op.execute("DROP TABLE IF EXISTS audit_logs_partitioned")

    # Remove columns from existing tables
    for column in [
        'mfa_enabled', 'mfa_secret', 'last_security_review',
        'failed_login_attempts', 'account_locked_until',
        'gdpr_consent_given', 'data_processing_consent',
        'marketing_consent', 'security_question_hash'
    ]:
        op.drop_column('users', column, nullable=False)

    for column in ['data_classification', 'retention_schedule', 'access_count', 'last_accessed']:
        op.drop_column('assessments', column, nullable=False)

    for column in ['response_encrypted', 'encryption_key_id']:
        op.drop_column('assessment_responses', column, nullable=False)

    # Drop indexes
    op.drop_index('idx_users_mfa_enabled', 'users')
    op.drop_index('idx_users_account_locked', 'users')
    op.drop_index('idx_users_last_security_review', 'users')
    op.drop_index('idx_assessments_classification', 'assessments')
    op.drop_index('idx_assessments_retention', 'assessments')
    op.drop_index('idx_assessments_last_accessed', 'assessments')
    op.drop_index('idx_assessment_responses_encrypted', 'assessment_responses')
