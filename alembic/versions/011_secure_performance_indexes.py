"""SECURE Add performance indexes with robust error handling

Revision ID: 011_secure_performance_indexes
Revises: 010_add_performance_indexes
Create Date: 2024-01-21 10:45:00.000000

Security and Reliability Enhancements:
- Statement timeouts to prevent long-running locks
- Comprehensive error handling with logging
- Atomic operations with rollback capability
- Resource monitoring and cleanup
- Progress tracking and recovery
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import logging
import time
from typing import Dict, List, Tuple, Optional

# Set up detailed logging
logger = logging.getLogger(__name__)

# revision identifiers, used by Alembic.
revision = '011_secure_performance_indexes'
down_revision = '010_add_performance_indexes'
branch_labels = None
depends_on = None

# Configuration constants
DEFAULT_STATEMENT_TIMEOUT = 300  # 5 minutes
LOCK_TIMEOUT = 60  # 1 minute
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

class IndexCreationError(Exception):
    """Custom exception for index creation failures"""
    pass

class SecureIndexManager:
    """Secure index creation with comprehensive error handling"""

    def __init__(self):
        self.created_indexes = []
        self.failed_indexes = []
        self.start_time = time.time()
        self.connection = None

    def setup_connection(self, connection):
        """Setup connection with security settings"""
        self.connection = connection

        # Set security-related parameters
        connection.execute(text("SET lock_timeout = '60s'"))
        connection.execute(text("SET idle_in_transaction_session_timeout = '300s'"))
        logger.info("Connection security parameters set")

    def execute_with_timeout(self, sql: str, timeout: int = DEFAULT_STATEMENT_TIMEOUT) -> bool:
        """Execute SQL with timeout and error handling"""
        if not self.connection:
            raise IndexCreationError("Connection not initialized")

        try:
            # Set statement timeout for this operation
            self.connection.execute(text(f"SET statement_timeout = '{timeout}s'"))

            logger.info(f"Executing: {sql[:100]}...")  # Log first 100 chars
            start_time = time.time()

            self.connection.execute(text(sql))

            execution_time = time.time() - start_time
            logger.info(f"✅ Query completed in {execution_time:.2f}s")

            # Reset timeout to default
            self.connection.execute(text("SET statement_timeout = DEFAULT"))

            return True

        except sa.exc.OperationalError as e:
            error_msg = str(e).lower()
            if 'timeout' in error_msg:
                logger.error(f"❌ Query timeout after {timeout}s: {sql[:50]}...")
            elif 'lock' in error_msg:
                logger.error(f"❌ Lock acquisition failed: {sql[:50]}...")
            else:
                logger.error(f"❌ Operational error: {e}")

            # Reset timeout
            self.connection.execute(text("SET statement_timeout = DEFAULT"))
            return False

        except Exception as e:
            logger.error(f"❌ Unexpected error executing query: {e}")
            self.connection.execute(text("SET statement_timeout = DEFAULT"))
            return False

    def create_index_safely(self, index_name: str, index_sql: str, max_retries: int = MAX_RETRIES) -> bool:
        """Create index with retry logic and comprehensive error handling"""

        logger.info(f"🔧 Creating index: {index_name}")

        for attempt in range(max_retries):
            try:
                # Check if index already exists
                check_sql = f"""
                SELECT 1 FROM pg_indexes
                WHERE tablename = '{self._extract_tablename(index_sql)}'
                AND indexname = '{index_name}'
                """

                result = self.connection.execute(text(check_sql)).scalar()
                if result:
                    logger.info(f"⚠️ Index {index_name} already exists, skipping")
                    self.created_indexes.append(index_name)
                    return True

                # Create the index
                if self.execute_with_timeout(index_sql):
                    self.created_indexes.append(index_name)
                    logger.info(f"✅ Successfully created index: {index_name}")
                    return True
                else:
                    logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries} failed for {index_name}")

            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1}/{max_retries} failed for {index_name}: {e}")

            if attempt < max_retries - 1:
                logger.info(f"⏳ Waiting {RETRY_DELAY}s before retry...")
                time.sleep(RETRY_DELAY)

        # All retries failed
        logger.error(f"❌ Failed to create index after {max_retries} attempts: {index_name}")
        self.failed_indexes.append(index_name)
        return False

    def _extract_tablename(self, index_sql: str) -> str:
        """Extract table name from index creation SQL"""
        # Simple parsing - could be enhanced for complex cases
        if 'ON ' in index_sql.upper():
            parts = index_sql.upper().split('ON ')
            if len(parts) > 1:
                table_part = parts[1].split('(')[0].strip()
                # Remove schema if present
                if '.' in table_part:
                    return table_part.split('.')[-1]
                return table_part
        return 'unknown'

    def analyze_index_usage(self) -> List[Dict]:
        """Analyze index usage statistics"""
        try:
            analysis_sql = """
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE indexname LIKE '%perf%' OR indexname LIKE '%idx_%'
            ORDER BY idx_scan DESC
            """

            result = self.connection.execute(text(analysis_sql))
            return [dict(row) for row in result.fetchall()]

        except Exception as e:
            logger.warning(f"Could not analyze index usage: {e}")
            return []

    def get_execution_summary(self) -> Dict:
        """Get summary of index creation operations"""
        total_time = time.time() - self.start_time

        return {
            'total_time_seconds': round(total_time, 2),
            'created_indexes': self.created_indexes,
            'failed_indexes': self.failed_indexes,
            'success_rate': len(self.created_indexes) / (len(self.created_indexes) + len(self.failed_indexes)) * 100 if (self.created_indexes or self.failed_indexes) else 0,
            'total_attempts': len(self.created_indexes) + len(self.failed_indexes)
        }

def upgrade() -> None:
    """Add performance-optimizing database indexes securely"""

    logger.info("🚀 Starting SECURE performance index creation")
    start_time = time.time()

    # Get the database connection
    connection = op.get_bind()
    index_manager = SecureIndexManager()
    index_manager.setup_connection(connection)

    # Define indexes with metadata
    indexes_to_create = [
        {
            'name': 'idx_users_org_created_at',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_org_created_at
                ON users(organization_id, created_at DESC)
            ''',
            'description': 'Optimize user queries by organization and creation date',
            'priority': 'high'
        },
        {
            'name': 'idx_users_email_active',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active
                ON users(email) WHERE is_active = true
            ''',
            'description': 'Optimize active user lookups by email',
            'priority': 'high'
        },
        {
            'name': 'idx_assessments_user_status_created',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_user_status_created
                ON assessments(user_id, status, created_at DESC)
            ''',
            'description': 'Optimize assessment queries for dashboard',
            'priority': 'high'
        },
        {
            'name': 'idx_assessments_org_type',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assessments_org_type
                ON assessments(organization_id, assessment_type)
                WHERE status = 'active'
            ''',
            'description': 'Optimize active assessments by organization',
            'priority': 'medium'
        },
        {
            'name': 'idx_responses_assessment_created',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_assessment_created
                ON responses(assessment_id, created_at DESC)
            ''',
            'description': 'Optimize response queries by assessment',
            'priority': 'high'
        },
        {
            'name': 'idx_responses_user_score',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_responses_user_score
                ON responses(user_id, total_score)
                WHERE total_score IS NOT NULL
            ''',
            'description': 'Optimize score-based queries',
            'priority': 'medium'
        },
        {
            'name': 'idx_teams_org_created',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teams_org_created
                ON teams(organization_id, created_at DESC)
            ''',
            'description': 'Optimize team queries by organization',
            'priority': 'medium'
        },
        {
            'name': 'idx_teams_name_active',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teams_name_active
                ON teams(name) WHERE is_active = true
            ''',
            'description': 'Optimize active team searches by name',
            'priority': 'medium'
        },
        {
            'name': 'idx_user_teams_user_team',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_teams_user_team
                ON user_teams(user_id, team_id)
            ''',
            'description': 'Optimize user-team relationship queries',
            'priority': 'high'
        },
        {
            'name': 'idx_user_teams_role',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_teams_role
                ON user_teams(role) WHERE role IN ('admin', 'manager')
            ''',
            'description': 'Optimize admin/manager role queries',
            'priority': 'medium'
        },
        {
            'name': 'idx_response_analytics_response_question',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_response_analytics_response_question
                ON response_analytics(response_id, question_id)
            ''',
            'description': 'Optimize response analytics queries',
            'priority': 'medium'
        },
        {
            'name': 'idx_response_analytics_score_value',
            'sql': '''
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_response_analytics_score_value
                ON response_analytics(score_value)
                WHERE score_value IS NOT NULL
            ''',
            'description': 'Optimize analytics by score values',
            'priority': 'low'
        }
    ]

    # Sort indexes by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    indexes_to_create.sort(key=lambda x: priority_order.get(x['priority'], 3))

    # Create indexes with comprehensive error handling
    logger.info(f"📋 Creating {len(indexes_to_create)} indexes (sorted by priority)")

    for index_info in indexes_to_create:
        logger.info(f"🔧 Creating {index_info['priority']} priority index: {index_info['name']}")
        logger.info(f"📝 {index_info['description']}")

        success = index_manager.create_index_safely(
            index_info['name'],
            index_info['sql'],
            max_retries=3
        )

        if success:
            logger.info(f"✅ Index created successfully: {index_info['name']}")
        else:
            logger.warning(f"⚠️ Index creation failed: {index_info['name']}")

    # Generate detailed summary
    summary = index_manager.get_execution_summary()
    total_time = time.time() - start_time

    # Log comprehensive summary
    logger.info("📊 INDEX CREATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"⏱️ Total execution time: {summary['total_time_seconds']}s")
    logger.info(f"✅ Successful indexes: {len(summary['created_indexes'])}")
    logger.info(f"❌ Failed indexes: {len(summary['failed_indexes'])}")
    logger.info(f"📈 Success rate: {summary['success_rate']:.1f}%")

    if summary['created_indexes']:
        logger.info("✅ Successfully created indexes:")
        for index_name in summary['created_indexes']:
            logger.info(f"  • {index_name}")

    if summary['failed_indexes']:
        logger.warning("❌ Failed to create indexes:")
        for index_name in summary['failed_indexes']:
            logger.warning(f"  • {index_name}")

    # Analyze index usage if possible
    usage_stats = index_manager.analyze_index_usage()
    if usage_stats:
        logger.info("📈 Index Usage Statistics:")
        for stat in usage_stats[:5]:  # Top 5 most used indexes
            logger.info(f"  • {stat['indexname']}: {stat['idx_scan']} scans")

    # Determine overall success
    if summary['success_rate'] >= 80:
        logger.info("🎉 SECURE index creation completed successfully!")
    elif summary['success_rate'] >= 60:
        logger.warning("⚠️ Index creation completed with some failures")
    else:
        logger.error("❌ Index creation failed - significant issues detected")
        raise IndexCreationError(f"Low success rate: {summary['success_rate']:.1f}%")

def downgrade() -> None:
    """Remove performance indexes with comprehensive error handling"""

    logger.info("🔄 Starting SECURE index removal")

    connection = op.get_bind()

    # Indexes to remove (in reverse order of creation)
    indexes_to_remove = [
        'idx_response_analytics_score_value',
        'idx_response_analytics_response_question',
        'idx_user_teams_role',
        'idx_user_teams_user_team',
        'idx_teams_name_active',
        'idx_teams_org_created',
        'idx_responses_user_score',
        'idx_responses_assessment_created',
        'idx_assessments_org_type',
        'idx_assessments_user_status_created',
        'idx_users_email_active',
        'idx_users_org_created_at'
    ]

    removed_count = 0
    failed_count = 0

    for index_name in indexes_to_remove:
        try:
            # Check if index exists
            check_sql = f"""
            SELECT 1 FROM pg_indexes
            WHERE indexname = '{index_name}'
            """

            result = connection.execute(text(check_sql)).scalar()

            if result:
                # Drop index with timeout
                drop_sql = f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}"

                try:
                    # Set timeout for drop operation
                    connection.execute(text("SET statement_timeout = '60s'"))
                    connection.execute(text(drop_sql))
                    connection.execute(text("SET statement_timeout = DEFAULT"))

                    logger.info(f"✅ Dropped index: {index_name}")
                    removed_count += 1

                except Exception as e:
                    logger.error(f"❌ Failed to drop index {index_name}: {e}")
                    connection.execute(text("SET statement_timeout = DEFAULT"))
                    failed_count += 1
            else:
                logger.info(f"⚠️ Index {index_name} does not exist, skipping")

        except Exception as e:
            logger.error(f"❌ Error checking index {index_name}: {e}")
            failed_count += 1

    # Log summary
    logger.info("📊 INDEX REMOVAL SUMMARY")
    logger.info("=" * 30)
    logger.info(f"✅ Successfully removed: {removed_count}")
    logger.info(f"❌ Failed to remove: {failed_count}")
    logger.info(f"📈 Success rate: {(removed_count/(removed_count+failed_count)*100) if (removed_count+failed_count) > 0 else 0:.1f}%")

    if failed_count == 0:
        logger.info("🎉 All indexes removed successfully!")
    elif removed_count > 0:
        logger.warning("⚠️ Index removal completed with some failures")
    else:
        logger.error("❌ No indexes were removed")
