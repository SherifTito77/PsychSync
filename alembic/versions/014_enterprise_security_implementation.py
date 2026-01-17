"""Enterprise security implementation

Revision ID: 014_enterprise_security_implementation
Revises: 013_add_critical_performance_indexes
Create Date: 2025-01-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json
import logging

# Configure logging for migration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('alembic')

# revision identifiers, used by Alembic.
revision = '014_enterprise_security_implementation'
down_revision = '013_add_critical_performance_indexes'
branch_labels = None
depends_on = None

def upgrade():
    """Implement enterprise-grade security measures"""

    logger.info("Starting enterprise security implementation...")

    # Enable required extensions
    logger.info("Enabling required PostgreSQL extensions...")
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";
        CREATE EXTENSION IF NOT EXISTS "btree_gin";
        CREATE EXTENSION IF NOT EXISTS "btree_gist";
    """)

    # Create secure user roles
    logger.info("Creating secure database roles...")
    op.execute("""
        -- Create roles for RLS implementation
        CREATE ROLE IF NOT EXISTS authenticated_role NOINHERIT;
        CREATE ROLE IF NOT EXISTS service_role NOINHERIT;
        CREATE ROLE IF NOT EXISTS admin_role NOINHERIT;

        -- Grant permissions to authenticated_role
        GRANT USAGE ON SCHEMA public TO authenticated_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated_role;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated_role;

        -- Set default privileges for future tables
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated_role;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT USAGE, SELECT ON SEQUENCES TO authenticated_role;

        -- Grant inheritance
        GRANT authenticated_role TO service_role;
        GRANT authenticated_role TO admin_role;
    """)

    # Create audit logs table
    logger.info("Creating audit logs table...")
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for audit logs
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_table_operation', 'audit_logs', ['table_name', 'operation'])
    op.create_index('idx_audit_logs_record_id', 'audit_logs', ['record_id'])
    op.create_index('idx_audit_logs_risk_score', 'audit_logs', ['risk_score'])

    # Create security events table
    logger.info("Creating security events table...")
    op.create_table(
        'security_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for security events
    op.create_index('idx_security_events_type', 'security_events', ['event_type'])
    op.create_index('idx_security_events_user', 'security_events', ['user_id'])
    op.create_index('idx_security_events_ip', 'security_events', ['ip_address'])
    op.create_index('idx_security_events_timestamp', 'security_events', ['timestamp'])
    op.create_index('idx_security_events_risk', 'security_events', ['risk_score'])
    op.create_index('idx_security_events_resolved', 'security_events', ['resolved'])

    # Create secure data backup table
    logger.info("Creating secure data backup table...")
    op.create_table(
        'secure_backups',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('backup_name', sa.String(255), nullable=False),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('backup_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('encrypted', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for secure backups
    op.create_index('idx_secure_backups_table', 'secure_backups', ['table_name'])
    op.create_index('idx_secure_backups_created', 'secure_backups', ['created_at'])
    op.create_index('idx_secure_backups_expires', 'secure_backups', ['expires_at'])

    # Create data retention policies table
    logger.info("Creating data retention policies table...")
    op.create_table(
        'data_retention_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('auto_delete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('archive_before_delete', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create default data retention policies
    logger.info("Creating default data retention policies...")
    op.execute("""
        INSERT INTO data_retention_policies (table_name, retention_days, created_by) VALUES
        ('users_secure', 2555, gen_random_uuid()), -- 7 years
        ('organizations_secure', 3650, gen_random_uuid()), -- 10 years
        ('assessments_secure', 2555, gen_random_uuid()), -- 7 years
        ('responses_secure', 2555, gen_random_uuid()), -- 7 years
        ('audit_logs', 1825, gen_random_uuid()), -- 5 years
        ('security_events', 1095, gen_random_uuid()); -- 3 years
    """)

    # Create data anonymization functions
    logger.info("Creating data anonymization functions...")
    op.execute("""
        -- Function to anonymize email
        CREATE OR REPLACE FUNCTION anonymize_email(email TEXT)
        RETURNS TEXT AS $$
        BEGIN
            RETURN 'anonymized_' || substr(md5(email || random()::text), 1, 16) || '@anonymized.com';
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;

        -- Function to anonymize text data
        CREATE OR REPLACE FUNCTION anonymize_text(text_data TEXT)
        RETURNS TEXT AS $$
        BEGIN
            IF text_data IS NULL THEN
                RETURN NULL;
            END IF;
            RETURN 'Anonymized content - ' || substr(md5(text_data || random()::text), 1, 32);
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;

        -- Function to anonymize phone number
        CREATE OR REPLACE FUNCTION anonymize_phone(phone TEXT)
        RETURNS TEXT AS $$
        BEGIN
            IF phone IS NULL OR length(phone) < 4 THEN
                return NULL;
            END IF;
            RETURN '***-***-' || substr(phone, -4);
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)

    # Create security monitoring views
    logger.info("Creating security monitoring views...")
    op.execute("""
        -- View for security risk analysis
        CREATE OR REPLACE VIEW security_risk_analysis AS
        SELECT
            u.id as user_id,
            u.email,
            u.login_attempts,
            u.last_login,
            COUNT(se.id) as security_events_count,
            AVG(se.risk_score) as avg_risk_score,
            MAX(se.timestamp) as last_security_event
        FROM users_secure u
        LEFT JOIN security_events se ON u.id = se.user_id
        GROUP BY u.id, u.email, u.login_attempts, u.last_login;

        -- View for data access patterns
        CREATE OR REPLACE VIEW data_access_patterns AS
        SELECT
            al.user_id,
            al.table_name,
            al.operation,
            COUNT(*) as access_count,
            MAX(al.timestamp) as last_access,
            COUNT(DISTINCT al.record_id) as unique_records_accessed
        FROM audit_logs al
        WHERE al.timestamp > NOW() - INTERVAL '7 days'
        GROUP BY al.user_id, al.table_name, al.operation;

        -- View for sensitive data access
        CREATE OR REPLACE VIEW sensitive_data_access AS
        SELECT
            al.user_id,
            al.table_name,
            al.operation,
            al.timestamp,
            al.ip_address,
            al.context->>'sensitivity_level' as sensitivity_level,
            al.context->>'data_classification' as data_classification
        FROM audit_logs al
        WHERE al.context->>'contains_phi' = 'true'
           OR al.context->>'data_classification' IN ('protected_health', 'sensitive', 'special')
        ORDER BY al.timestamp DESC;
    """)

    # Enable Row Level Security on audit tables
    logger.info("Enabling Row Level Security on audit tables...")
    op.execute("""
        -- Enable RLS on audit logs
        ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

        -- Create policy for audit logs
        CREATE POLICY audit_logs_policy ON audit_logs
        FOR ALL TO admin_role
        USING (true);

        -- Enable RLS on security events
        ALTER TABLE security_events ENABLE ROW LEVEL SECURITY;

        -- Create policy for security events
        CREATE POLICY security_events_policy ON security_events
        FOR ALL TO admin_role
        USING (true);

        -- Enable RLS on secure backups
        ALTER TABLE secure_backups ENABLE ROW LEVEL SECURITY;

        -- Create policy for secure backups
        CREATE POLICY secure_backups_policy ON secure_backups
        FOR ALL TO admin_role
        USING (true);
    """)

    # Create triggers for automatic audit logging
    logger.info("Creating triggers for automatic audit logging...")
    op.execute("""
        -- Function for audit logging
        CREATE OR REPLACE FUNCTION audit_trigger_function()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                INSERT INTO audit_logs (table_name, operation, record_id, context)
                VALUES (TG_TABLE_NAME, TG_OP, OLD.id,
                       json_build_object('old_data', row_to_json(OLD)));
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                INSERT INTO audit_logs (table_name, operation, record_id, context)
                VALUES (TG_TABLE_NAME, TG_OP, NEW.id,
                       json_build_object('old_data', row_to_json(OLD), 'new_data', row_to_json(NEW)));
                RETURN NEW;
            ELSIF TG_OP = 'INSERT' THEN
                INSERT INTO audit_logs (table_name, operation, record_id, context)
                VALUES (TG_TABLE_NAME, TG_OP, NEW.id,
                       json_build_object('new_data', row_to_json(NEW)));
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        -- Note: Triggers will be added to individual tables as they are created
        -- This prevents issues with tables that don't exist yet
    """)

    # Create automated data cleanup function
    logger.info("Creating automated data cleanup function...")
    op.execute("""
        -- Function for automated data cleanup based on retention policies
        CREATE OR REPLACE FUNCTION cleanup_expired_data()
        RETURNS TEXT AS $$
        DECLARE
            cleanup_count INTEGER := 0;
            policy_record RECORD;
            sql_query TEXT;
        BEGIN
            -- Process each retention policy
            FOR policy_record IN SELECT * FROM data_retention_policies WHERE auto_delete = true LOOP
                -- Archive data before deletion if required
                IF policy_record.archive_before_delete THEN
                    sql_query := format('INSERT INTO secure_backups (backup_name, table_name, backup_data, created_by)
                                     SELECT CONCAT(''backup_'', table_name, ''_'', NOW()), table_name,
                                     json_agg(row_to_json(t)), gen_random_uuid()
                                     FROM %I
                                     WHERE created_at < NOW() - INTERVAL ''%s days''',
                                     policy_record.table_name, policy_record.retention_days);
                    EXECUTE sql_query;
                END IF;

                -- Delete expired data
                sql_query := format('DELETE FROM %I WHERE created_at < NOW() - INTERVAL ''%s days''',
                                   policy_record.table_name, policy_record.retention_days);
                EXECUTE sql_query;

                GET DIAGNOSTICS cleanup_count = ROW_COUNT;

                RAISE NOTICE 'Cleaned up % records from table %', cleanup_count, policy_record.table_name;
            END LOOP;

            RETURN 'Data cleanup completed';
        END;
        $$ LANGUAGE plpgsql;
    """)

    logger.info("Enterprise security implementation completed successfully")

def downgrade():
    """Remove enterprise security measures"""

    logger.info("Starting downgrade of enterprise security implementation...")

    # Drop triggers and functions
    logger.info("Dropping security functions and triggers...")
    op.execute("""
        DROP FUNCTION IF EXISTS cleanup_expired_data() CASCADE;
        DROP FUNCTION IF EXISTS audit_trigger_function() CASCADE;
        DROP FUNCTION IF EXISTS anonymize_email(TEXT) CASCADE;
        DROP FUNCTION IF EXISTS anonymize_text(TEXT) CASCADE;
        DROP FUNCTION IF EXISTS anonymize_phone(TEXT) CASCADE;
    """)

    # Drop views
    logger.info("Dropping security monitoring views...")
    op.execute("""
        DROP VIEW IF EXISTS security_risk_analysis CASCADE;
        DROP VIEW IF EXISTS data_access_patterns CASCADE;
        DROP VIEW IF EXISTS sensitive_data_access CASCADE;
    """)

    # Drop tables in reverse order
    logger.info("Dropping security tables...")
    op.drop_table('data_retention_policies')
    op.drop_table('secure_backups')
    op.drop_table('security_events')
    op.drop_table('audit_logs')

    # Drop roles
    logger.info("Dropping secure database roles...")
    op.execute("""
        DROP ROLE IF EXISTS admin_role CASCADE;
        DROP ROLE IF EXISTS service_role CASCADE;
        DROP ROLE IF EXISTS authenticated_role CASCADE;
    """)

    logger.info("Enterprise security downgrade completed successfully")
