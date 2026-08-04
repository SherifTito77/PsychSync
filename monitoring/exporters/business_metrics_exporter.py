"""
PsychSync Business Metrics Exporter
Custom Prometheus exporter for business KPIs and metrics
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import psycopg2
import redis
import stripe
from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server
from prometheus_client.core import REGISTRY

# Configuration
DATABASE_URL = "postgresql://postgres:password@postgres:5432/psychsync"
REDIS_URL = "redis://redis:6379/0"
STRIPE_API_KEY = "sk_test_your_stripe_key"
METRICS_PORT = 8081
UPDATE_INTERVAL = 60  # seconds

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Metrics definitions
class BusinessMetrics:
    """Business metrics definitions"""

    # User Metrics
    USERS_REGISTERED_TOTAL = Gauge(
        "psychsync_users_registered_total", "Total number of registered users"
    )
    USERS_ACTIVE_DAILY = Gauge("psychsync_users_active_daily", "Daily active users")
    USERS_ACTIVE_WEEKLY = Gauge("psychsync_users_active_weekly", "Weekly active users")
    USERS_ACTIVE_MONTHLY = Gauge(
        "psychsync_users_active_monthly", "Monthly active users"
    )

    # Assessment Metrics
    ASSESSMENTS_COMPLETED_TOTAL = Gauge(
        "psychsync_assessments_completed_total", "Total assessments completed"
    )
    ASSESSMENTS_STARTED_HOURLY = Gauge(
        "psychsync_assessments_started_hourly", "Assessments started per hour"
    )
    ASSESSMENT_COMPLETION_RATE = Gauge(
        "psychsync_assessment_completion_rate", "Assessment completion rate"
    )
    ASSESSMENT_AVERAGE_SCORE = Gauge(
        "psychsync_assessment_average_score", "Average assessment score"
    )

    # Team/Organization Metrics
    ORGANIZATIONS_TOTAL = Gauge("psychsync_organizations_total", "Total organizations")
    TEAMS_TOTAL = Gauge("psychsync_teams_total", "Total teams")
    TEAM_MEMBERS_AVERAGE = Gauge("psychsync_team_members_average", "Average team size")

    # Revenue Metrics
    REVENUE_DAILY = Gauge("psychsync_revenue_daily_dollars", "Daily revenue in dollars")
    REVENUE_MONTHLY = Gauge(
        "psychsync_revenue_monthly_dollars", "Monthly revenue in dollars"
    )
    REVENUE_YEARLY = Gauge(
        "psychsync_revenue_yearly_dollars", "Yearly revenue in dollars"
    )
    SUBSCRIPTIONS_ACTIVE = Gauge(
        "psychsync_subscriptions_active_total", "Active subscriptions"
    )
    SUBSCRIPTIONS_TRIAL = Gauge(
        "psychsync_subscriptions_trial_total", "Trial subscriptions"
    )

    # Conversion Metrics
    CONVERSION_RATE_REGISTRATION_TO_ASSESSMENT = Gauge(
        "psychsync_conversion_registration_to_assessment_rate",
        "Registration to assessment conversion rate",
    )
    CONVERSION_RATE_TRIAL_TO_PAID = Gauge(
        "psychsync_conversion_trial_to_paid_rate", "Trial to paid conversion rate"
    )

    # Engagement Metrics
    SESSION_DURATION_AVERAGE = Gauge(
        "psychsync_session_duration_average_seconds", "Average session duration"
    )
    PAGE_VIEWS_PER_SESSION = Gauge(
        "psychsync_page_views_per_session_average", "Average page views per session"
    )
    BOUNCE_RATE = Gauge("psychsync_bounce_rate", "Website bounce rate")

    # Performance Metrics
    API_RESPONSE_TIME_P95 = Histogram(
        "psychsync_api_response_time_p95_seconds", "P95 API response time"
    )
    DATABASE_QUERY_TIME_AVERAGE = Gauge(
        "psychsync_database_query_time_average_seconds", "Average database query time"
    )
    ERROR_RATE_OVERALL = Gauge(
        "psychsync_error_rate_overall", "Overall system error rate"
    )

    # Health Metrics
    SYSTEM_HEALTH = Info("psychsync_system_health", "Overall system health status")

    @classmethod
    def register_all(cls):
        """Register all metrics with Prometheus"""
        # Registration happens automatically when metrics are defined
        pass


@dataclass
class DatabaseConnection:
    """Database connection manager"""

    conn: Optional[psycopg2.extensions.connection] = None

    def connect(self):
        """Establish database connection"""
        if not self.conn:
            try:
                self.conn = psycopg2.connect(DATABASE_URL)
                logger.info("Connected to database")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def query(self, query: str, params: tuple = None) -> list:
        """Execute query and return results"""
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return []


@dataclass
class RedisConnection:
    """Redis connection manager"""

    client: Optional[redis.Redis] = None

    def connect(self):
        """Establish Redis connection"""
        if not self.client:
            try:
                self.client = redis.from_url(REDIS_URL)
                logger.info("Connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")

    def disconnect(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            self.client = None

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        if not self.client:
            self.connect()

        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None

    def set(self, key: str, value: str, ex: int = None):
        """Set value in Redis"""
        if not self.client:
            self.connect()

        try:
            self.client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")


class BusinessMetricsCollector:
    """Main business metrics collector"""

    def __init__(self):
        self.db = DatabaseConnection()
        self.redis = RedisConnection()
        self.stripe = stripe.api_key = STRIPE_API_KEY

    def collect_user_metrics(self):
        """Collect user-related metrics"""
        try:
            # Total registered users
            result = self.db.query("SELECT COUNT(*) FROM users")
            if result:
                BusinessMetrics.USERS_REGISTERED_TOTAL.set(result[0][0])

            # Daily active users (last 24 hours)
            result = self.db.query(
                """
                SELECT COUNT(DISTINCT user_id) FROM user_sessions
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """
            )
            if result:
                BusinessMetrics.USERS_ACTIVE_DAILY.set(result[0][0])

            # Weekly active users
            result = self.db.query(
                """
                SELECT COUNT(DISTINCT user_id) FROM user_sessions
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """
            )
            if result:
                BusinessMetrics.USERS_ACTIVE_WEEKLY.set(result[0][0])

            # Monthly active users
            result = self.db.query(
                """
                SELECT COUNT(DISTINCT user_id) FROM user_sessions
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """
            )
            if result:
                BusinessMetrics.USERS_ACTIVE_MONTHLY.set(result[0][0])

        except Exception as e:
            logger.error(f"Failed to collect user metrics: {e}")

    def collect_assessment_metrics(self):
        """Collect assessment-related metrics"""
        try:
            # Total assessments completed
            result = self.db.query(
                "SELECT COUNT(*) FROM responses WHERE completed_at IS NOT NULL"
            )
            if result:
                BusinessMetrics.ASSESSMENTS_COMPLETED_TOTAL.set(result[0][0])

            # Assessments started in last hour
            result = self.db.query(
                """
                SELECT COUNT(*) FROM responses
                WHERE created_at >= NOW() - INTERVAL '1 hour'
            """
            )
            if result:
                BusinessMetrics.ASSESSMENTS_STARTED_HOURLY.set(result[0][0])

            # Assessment completion rate
            result = self.db.query(
                """
                SELECT
                    COUNT(CASE WHEN completed_at IS NOT NULL THEN 1 END)::float /
                    COUNT(*)::float as completion_rate
                FROM responses
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """
            )
            if result and result[0][0]:
                BusinessMetrics.ASSESSMENT_COMPLETION_RATE.set(result[0][0])

            # Average assessment score
            result = self.db.query(
                """
                SELECT AVG(total_score) FROM responses
                WHERE completed_at IS NOT NULL AND total_score IS NOT NULL
                AND completed_at >= NOW() - INTERVAL '30 days'
            """
            )
            if result and result[0][0]:
                BusinessMetrics.ASSESSMENT_AVERAGE_SCORE.set(result[0][0])

        except Exception as e:
            logger.error(f"Failed to collect assessment metrics: {e}")

    def collect_organization_metrics(self):
        """Collect organization and team metrics"""
        try:
            # Total organizations
            result = self.db.query("SELECT COUNT(*) FROM organizations")
            if result:
                BusinessMetrics.ORGANIZATIONS_TOTAL.set(result[0][0])

            # Total teams
            result = self.db.query("SELECT COUNT(*) FROM teams")
            if result:
                BusinessMetrics.TEAMS_TOTAL.set(result[0][0])

            # Average team size
            result = self.db.query(
                """
                SELECT AVG(member_count) FROM (
                    SELECT COUNT(tum.user_id) as member_count
                    FROM team_user_memberships tum
                    GROUP BY tum.team_id
                ) team_sizes
            """
            )
            if result and result[0][0]:
                BusinessMetrics.TEAM_MEMBERS_AVERAGE.set(result[0][0])

        except Exception as e:
            logger.error(f"Failed to collect organization metrics: {e}")

    def collect_revenue_metrics(self):
        """Collect revenue and subscription metrics"""
        try:
            # Stripe revenue metrics
            # Daily revenue
            daily_revenue = 0
            for charge in stripe.Charge.list(
                created={"gte": int((datetime.now() - timedelta(days=1)).timestamp())},
                limit=100,
            ).auto_paging_iter():
                if charge.status == "succeeded":
                    daily_revenue += charge.amount

            BusinessMetrics.REVENUE_DAILY.set(
                daily_revenue / 100
            )  # Convert cents to dollars

            # Monthly revenue (simplified - would need proper calculation in production)
            monthly_revenue = daily_revenue * 30  # Approximation
            BusinessMetrics.REVENUE_MONTHLY.set(monthly_revenue / 100)

            # Active subscriptions
            active_subs = 0
            trial_subs = 0

            for subscription in stripe.Subscription.list(
                status="active", limit=100
            ).auto_paging_iter():
                active_subs += 1

            for subscription in stripe.Subscription.list(
                status="trialing", limit=100
            ).auto_paging_iter():
                trial_subs += 1

            BusinessMetrics.SUBSCRIPTIONS_ACTIVE.set(active_subs)
            BusinessMetrics.SUBSCRIPTIONS_TRIAL.set(trial_subs)

        except Exception as e:
            logger.error(f"Failed to collect revenue metrics: {e}")

    def collect_conversion_metrics(self):
        """Collect conversion funnel metrics"""
        try:
            # Registration to assessment completion rate
            result = self.db.query(
                """
                SELECT
                    (SELECT COUNT(DISTINCT r.user_id) FROM responses r
                     WHERE r.completed_at IS NOT NULL
                     AND r.created_at >= NOW() - INTERVAL '7 days')::float /
                    (SELECT COUNT(DISTINCT u.id) FROM users u
                     WHERE u.created_at >= NOW() - INTERVAL '7 days')::float as conversion_rate
            """
            )
            if result and result[0][0]:
                BusinessMetrics.CONVERSION_RATE_REGISTRATION_TO_ASSESSMENT.set(
                    result[0][0]
                )

            # Trial to paid conversion (using Stripe data)
            try:
                # This would need more sophisticated tracking in production
                conversion_rate = 0.15  # Placeholder
                BusinessMetrics.CONVERSION_RATE_TRIAL_TO_PAID.set(conversion_rate)
            except Exception as e:
                pass

        except Exception as e:
            logger.error(f"Failed to collect conversion metrics: {e}")

    def collect_engagement_metrics(self):
        """Collect user engagement metrics"""
        try:
            # Average session duration
            result = self.db.query(
                """
                SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at)))
                FROM user_sessions
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """
            )
            if result and result[0][0]:
                BusinessMetrics.SESSION_DURATION_AVERAGE.set(result[0][0])

            # Page views per session
            result = self.db.query(
                """
                SELECT AVG(page_view_count)
                FROM user_sessions
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                AND page_view_count > 0
            """
            )
            if result and result[0][0]:
                BusinessMetrics.PAGE_VIEWS_PER_SESSION.set(result[0][0])

            # Bounce rate (single page sessions)
            result = self.db.query(
                """
                SELECT
                    COUNT(CASE WHEN page_view_count = 1 THEN 1 END)::float /
                    COUNT(*)::float as bounce_rate
                FROM user_sessions
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """
            )
            if result and result[0][0]:
                BusinessMetrics.BOUNCE_RATE.set(result[0][0])

        except Exception as e:
            logger.error(f"Failed to collect engagement metrics: {e}")

    def collect_performance_metrics(self):
        """Collect system performance metrics"""
        try:
            # P95 API response time (from application metrics)
            api_p95 = self.redis.get("api_response_time_p95")
            if api_p95:
                BusinessMetrics.API_RESPONSE_TIME_P95.observe(float(api_p95))

            # Average database query time
            avg_query_time = self.redis.get("avg_database_query_time")
            if avg_query_time:
                BusinessMetrics.DATABASE_QUERY_TIME_AVERAGE.set(float(avg_query_time))

            # Overall error rate
            error_rate = self.redis.get("overall_error_rate")
            if error_rate:
                BusinessMetrics.ERROR_RATE_OVERALL.set(float(error_rate))

        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")

    def collect_health_metrics(self):
        """Collect system health metrics"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "database": "healthy",
                "redis": "healthy",
                "stripe": "healthy",
            }

            # Check database health
            try:
                self.db.query("SELECT 1")
            except Exception as e:
                health_status["database"] = "unhealthy"

            # Check Redis health
            try:
                self.redis.client.ping()
            except Exception as e:
                health_status["redis"] = "unhealthy"

            # Check Stripe health
            try:
                stripe.Account.retrieve()
            except Exception as e:
                health_status["stripe"] = "unhealthy"

            BusinessMetrics.SYSTEM_HEALTH.info(health_status)

        except Exception as e:
            logger.error(f"Failed to collect health metrics: {e}")

    def collect_all_metrics(self):
        """Collect all business metrics"""
        logger.info("Starting metrics collection")

        try:
            self.collect_user_metrics()
            self.collect_assessment_metrics()
            self.collect_organization_metrics()
            self.collect_revenue_metrics()
            self.collect_conversion_metrics()
            self.collect_engagement_metrics()
            self.collect_performance_metrics()
            self.collect_health_metrics()

            logger.info("Metrics collection completed")

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")

    def cleanup(self):
        """Clean up resources"""
        self.db.disconnect()
        self.redis.disconnect()


def main():
    """Main function to run the metrics exporter"""
    logger.info("Starting PsychSync Business Metrics Exporter")

    # Register all metrics
    BusinessMetrics.register_all()

    # Initialize collector
    collector = BusinessMetricsCollector()

    # Start HTTP server
    start_http_server(METRICS_PORT)
    logger.info(f"Metrics server started on port {METRICS_PORT}")

    try:
        # Main collection loop
        while True:
            collector.collect_all_metrics()
            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Shutting down metrics exporter")
        collector.cleanup()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        collector.cleanup()
        raise


if __name__ == "__main__":
    main()
