# tests/test_onboarding_service_layer.py
"""
SERVICE LAYER TESTS FOR PSYCHSYNC ONBOARDING FUNCTIONALITY
Comprehensive testing of onboarding business logic and data processing

Coverage:
- OnboardingService business logic
- AnalyticsService event tracking
- Quick insights generation algorithms
- Team analysis and recommendations
- Data validation and sanitization
- Performance and optimization

Author: QA Team
Version: 1.0 Service Layer Testing
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import asdict

from app.services.onboarding_service import OnboardingService
from app.services.analytics_service import AnalyticsService
from app.schemas.onboarding import (
    UserRole, TeamChallenge, QuickAssessmentRequest,
    QuickInsights, Recommendation, TeamProfile
)
from app.db.models.user import User, UserRole
from app.db.models.team import Team


class TestOnboardingService:
    """Test suite for OnboardingService business logic"""

    @pytest.fixture
    def onboarding_service(self):
        """Create OnboardingService instance"""
        return OnboardingService()

    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing"""
        user = Mock(spec=User)
        user.id = "test-user-uuid-123"
        user.email = "test@psychsync.com"
        user.full_name = "Test User"
        user.role = UserRole.USER
        user.is_active = True
        user.created_at = datetime.utcnow()
        return user

    @pytest.fixture
    def sample_team(self):
        """Create sample team for testing"""
        team = Mock(spec=Team)
        team.id = "test-team-uuid-456"
        team.name = "Test Team"
        team.description = "Test team description"
        team.organization_id = "test-org-uuid"
        team.created_at = datetime.utcnow()
        return team

    @pytest.mark.asyncio
    async def test_generate_quick_insights_all_roles(self, onboarding_service):
        """Test quick insights generation for all user roles"""
        roles = [UserRole.MANAGER, UserRole.HR, UserRole.LEAD, UserRole.MEMBER, UserRole.EXECUTIVE]
        challenges = [TeamChallenge.COMMUNICATION, TeamChallenge.PRODUCTIVITY, TeamChallenge.TURNOVER]

        insights_results = []

        for role in roles:
            for challenge in challenges:
                insights = await onboarding_service.generate_quick_insights(
                    role=role,
                    challenge=challenge,
                    team_size="5-10",
                    industry="technology",
                    user_id=None
                )

                insights_results.append(insights)

                # Verify insights structure
                assert hasattr(insights, 'primary_benefit')
                assert hasattr(insights, 'recommendations')
                assert hasattr(insights, 'conversion_probability')
                assert isinstance(insights.conversion_probability, float)
                assert 0 <= insights.conversion_probability <= 1
                assert len(insights.recommendations) > 0

                # Verify role-specific content
                assert role.value.lower() in insights.primary_benefit.lower() or \
                       challenge.value.lower() in insights.primary_benefit.lower()

        # Ensure all role-challenge combinations produce unique insights
        primary_benefits = [insights.primary_benefit for insights in insights_results]
        assert len(set(primary_benefits)) >= len(roles)  # At least some variety

    @pytest.mark.asyncio
    async def test_generate_quick_insights_team_size_variations(self, onboarding_service):
        """Test insights generation for different team sizes"""
        team_sizes = ["1-5", "5-10", "10-20", "20-50", "50+"]

        for size in team_sizes:
            insights = await onboarding_service.generate_quick_insights(
                role=UserRole.MANAGER,
                challenge=TeamChallenge.COMMUNICATION,
                team_size=size,
                industry="technology",
                user_id=None
            )

            # Larger teams should have different recommendations
            assert insights.recommendations
            for recommendation in insights.recommendations:
                assert recommendation.title
                assert recommendation.description
                assert recommendation.priority in ["High", "Medium", "Low"]
                assert recommendation.effort in ["Low", "Medium", "High"]

    @pytest.mark.asyncio
    async def test_generate_detailed_team_insights(self, onboarding_service, sample_user, sample_team):
        """Test detailed team insights generation"""
        assessment_data = {
            "communication_style": "collaborative",
            "decision_making": "consensus",
            "conflict_resolution": "open_discussion"
        }

        team_composition = [
            {
                "role": "developer",
                "experience": 5,
                "personality": "analytical",
                "communication_preference": "written"
            },
            {
                "role": "designer",
                "experience": 3,
                "personality": "creative",
                "communication_preference": "visual"
            }
        ]

        with patch('app.services.onboarding_service.TeamService') as mock_team_service:
            mock_team_service.get_team_by_id.return_value = sample_team
            mock_team_service.get_team_members.return_value = team_composition

            insights = await onboarding_service.generate_detailed_team_insights(
                user_id=sample_user.id,
                team_id=sample_team.id,
                assessment_data=assessment_data,
                team_composition=team_composition
            )

            # Verify detailed insights structure
            assert hasattr(insights, 'team_profile')
            assert hasattr(insights, 'detailed_insights')
            assert hasattr(insights, 'action_items')
            assert hasattr(insights, 'predicted_outcomes')
            assert hasattr(insights, 'implementation_roadmap')

            # Verify team profile
            team_profile = insights.team_profile
            assert isinstance(team_profile.team_size, int)
            assert 0 <= team_profile.current_performance <= 1
            assert 0 <= team_profile.potential_performance <= 1

    @pytest.mark.asyncio
    async def test_get_onboarding_status(self, onboarding_service, sample_user):
        """Test onboarding status retrieval"""
        with patch('app.services.onboarding_service.UserService') as mock_user_service, \
             patch('app.services.onboarding_service.TeamService') as mock_team_service, \
             patch('app.services.onboarding_service.AssessmentService') as mock_assessment_service:

            # Mock user data
            mock_user_service.get_user_by_id.return_value = sample_user
            mock_user_service.get_user_assessments.return_value = []
            mock_team_service.get_user_teams.return_value = []

            status = await onboarding_service.get_onboarding_status(sample_user.id)

            # Verify status structure
            assert "is_authenticated" in status
            assert "onboarding_complete" in status
            assert "progress" in status
            assert "completed_steps" in status
            assert "next_steps" in status

            assert isinstance(status["progress"], (int, float))
            assert 0 <= status["progress"] <= 1

    @pytest.mark.asyncio
    async def test_process_setup_step(self, onboarding_service, sample_user):
        """Test setup wizard step processing"""
        setup_steps = [
            {
                "step": "profile",
                "data": {
                    "industry": "technology",
                    "company_size": "50-100",
                    "primary_goal": "team_communication"
                }
            },
            {
                "step": "team",
                "data": {
                    "team_name": "Engineering",
                    "team_size": 10,
                    "department": "Technology"
                }
            },
            {
                "step": "assessment",
                "data": {
                    "assessment_type": "team_dynamics",
                    "participants": ["user1", "user2"]
                }
            }
        ]

        for step_data in setup_steps:
            with patch('app.services.onboarding_service.UserService') as mock_user_service:
                mock_user_service.update_user_profile.return_value = True

                result = await onboarding_service.process_setup_step(
                    user_id=sample_user.id,
                    step=step_data["step"],
                    data=step_data["data"]
                )

                # Verify step processing result
                assert "success" in result
                assert "next_step" in result
                assert isinstance(result["success"], bool)

    @pytest.mark.asyncio
    async def test_calculate_value_metrics(self, onboarding_service, sample_user):
        """Test value metrics calculation"""
        with patch('app.services.onboarding_service.AnalyticsService') as mock_analytics, \
             patch('app.services.onboarding_service.TeamService') as mock_team_service:

            # Mock team data
            mock_team = Mock()
            mock_team.id = "test-team-metrics"
            mock_team.name = "Metrics Test Team"
            mock_team_service.get_user_teams.return_value = [mock_team]

            # Mock analytics data
            mock_analytics.get_team_performance_metrics.return_value = {
                "productivity_score": 0.75,
                "communication_score": 0.80,
                "collaboration_score": 0.70,
                "improvement_rate": 0.15
            }

            metrics = await onboarding_service.calculate_value_metrics(sample_user.id)

            # Verify metrics structure
            assert "current_performance" in metrics
            assert "potential_performance" in metrics
            assert "improvement_opportunities" in metrics
            assert "value_generated" in metrics
            assert "roi_estimate" in metrics

            # Verify data types and ranges
            assert isinstance(metrics["current_performance"], (int, float))
            assert isinstance(metrics["potential_performance"], (int, float))
            assert 0 <= metrics["current_performance"] <= 1
            assert 0 <= metrics["potential_performance"] <= 1


class TestAnalyticsService:
    """Test suite for AnalyticsService functionality"""

    @pytest.fixture
    def analytics_service(self):
        """Create AnalyticsService instance"""
        return AnalyticsService()

    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing"""
        user = Mock(spec=User)
        user.id = "analytics-user-uuid"
        user.email = "analytics@test.com"
        return user

    @pytest.mark.asyncio
    async def test_track_onboarding_event_success(self, analytics_service):
        """Test successful onboarding event tracking"""
        event_data = {
            "role": "manager",
            "challenge": "communication",
            "team_size": "5-10",
            "conversion_probability": 0.75
        }

        with patch('app.core.redis_client.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            # Mock Redis operations
            mock_client.setex.return_value = True
            mock_client.incr.return_value = 1
            mock_client.expire.return_value = True

            result = await analytics_service.track_onboarding_event(
                event_type="quick_assessment_completed",
                user_id="test-user-uuid",
                session_id="test-session-123",
                data=event_data
            )

            assert result is True
            assert mock_client.setex.called or mock_client.incr.called

    @pytest.mark.asyncio
    async def test_track_onboarding_event_data_validation(self, analytics_service):
        """Test event tracking with data validation"""
        invalid_data = {
            "malicious_payload": "'; DROP TABLE events; --",
            "large_data": "x" * 10000,  # Should be truncated
            "nested_object": {"deep": {"very": {"deep": {"data": "test"}}}}
        }

        with patch('app.core.redis_client.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.setex.return_value = True

            # Should handle invalid data gracefully
            result = await analytics_service.track_onboarding_event(
                event_type="test_event",
                user_id="test-user-uuid",
                session_id="test-session",
                data=invalid_data
            )

            assert result is True

            # Verify data was sanitized
            call_args = mock_client.setex.call_args
            if call_args:
                stored_data = call_args[0][2]  # Third argument (data)
                # Check that malicious SQL was not stored
                assert "DROP TABLE" not in stored_data

    @pytest.mark.asyncio
    async def test_get_conversion_analytics(self, analytics_service):
        """Test conversion analytics retrieval"""
        with patch('app.core.redis_client.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            # Mock Redis responses
            mock_client.get.return_value = json.dumps({
                "total_sessions": 1000,
                "completed_quick_assessment": 800,
                "registered_users": 300,
                "created_teams": 150
            })
            mock_client.keys.return_value = ["conversion:2024-01-01", "conversion:2024-01-02"]

            analytics = await analytics_service.get_conversion_analytics(
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow()
            )

            # Verify analytics structure
            assert "total_sessions" in analytics
            assert "conversion_rates" in analytics
            assert "funnel_performance" in analytics
            assert "trends" in analytics

            # Verify conversion rates calculation
            conversion_rates = analytics["conversion_rates"]
            assert "assessment_completion_rate" in conversion_rates
            assert "registration_rate" in conversion_rates
            assert "team_creation_rate" in conversion_rates

    @pytest.mark.asyncio
    async def test_get_user_journey_analytics(self, analytics_service, sample_user):
        """Test user journey analytics"""
        with patch('app.core.redis_client.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            # Mock journey events
            journey_events = [
                {
                    "timestamp": "2024-01-01T10:00:00Z",
                    "event_type": "quick_assessment_started",
                    "data": {"role": "manager"}
                },
                {
                    "timestamp": "2024-01-01T10:05:00Z",
                    "event_type": "quick_assessment_completed",
                    "data": {"conversion_probability": 0.8}
                },
                {
                    "timestamp": "2024-01-01T10:10:00Z",
                    "event_type": "user_registered",
                    "data": {"email": sample_user.email}
                }
            ]

            mock_client.get.return_value = json.dumps(journey_events)

            journey = await analytics_service.get_user_journey_analytics(sample_user.id)

            # Verify journey structure
            assert len(journey["events"]) == len(journey_events)
            assert "total_time" in journey
            assert "conversion_points" in journey
            assert "drop_off_points" in journey
            assert "engagement_score" in journey

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, analytics_service):
        """Test performance metrics collection"""
        with patch('app.core.redis_client.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            # Mock performance data
            performance_data = {
                "avg_response_time": 1.2,
                "p95_response_time": 2.5,
                "error_rate": 0.01,
                "throughput": 100,
                "concurrent_users": 25
            }

            mock_client.mget.return_value = [
                json.dumps(performance_data),
                json.dumps({"timestamp": datetime.utcnow().isoformat()})
            ]

            metrics = await analytics_service.get_performance_metrics(
                time_range="1h"
            )

            # Verify metrics structure
            assert "response_time" in metrics
            assert "throughput" in metrics
            assert "error_rate" in metrics
            assert "user_load" in metrics
            assert "system_health" in metrics


class TestDataValidationAndSecurity:
    """Test suite for data validation and security in onboarding"""

    @pytest.fixture
    def onboarding_service(self):
        """Create OnboardingService instance"""
        return OnboardingService()

    @pytest.mark.asyncio
    async def test_assessment_request_validation(self, onboarding_service):
        """Test assessment request input validation"""
        valid_requests = [
            {
                "role": "manager",
                "challenge": "communication",
                "team_size": "5-10",
                "industry": "technology"
            },
            {
                "role": "hr",
                "challenge": "turnover",
                "team_size": "10-20",
                "industry": "healthcare"
            }
        ]

        for request_data in valid_requests:
            # Should not raise validation errors
            try:
                request = QuickAssessmentRequest(**request_data)
                assert request.role in UserRole
                assert request.challenge in TeamChallenge
            except Exception as e:
                pytest.fail(f"Valid request failed validation: {e}")

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, onboarding_service):
        """Test SQL injection prevention in assessment data"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "'; INSERT INTO users (email) VALUES ('hacker@evil.com'); --",
            "UNION SELECT * FROM sensitive_data --"
        ]

        for malicious_input in malicious_inputs:
            # Test that malicious input doesn't cause errors
            try:
                insights = await onboarding_service.generate_quick_insights(
                    role=UserRole.MANAGER,
                    challenge=TeamChallenge.COMMUNICATION,
                    team_size=malicious_input,  # Try to inject in team_size
                    industry=malicious_input,   # Try to inject in industry
                    user_id=None
                )

                # Should return insights without database errors
                assert insights is not None
                assert hasattr(insights, 'primary_benefit')

            except Exception as e:
                # Should not be database errors
                assert "DROP TABLE" not in str(e)
                assert "SQL" not in str(e).upper()

    @pytest.mark.asyncio
    async def test_xss_prevention(self, onboarding_service):
        """Test XSS prevention in user inputs"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:void(0)",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]

        for xss_payload in xss_payloads:
            insights = await onboarding_service.generate_quick_insights(
                role=UserRole.MANAGER,
                challenge=TeamChallenge.COMMUNICATION,
                team_size=xss_payload,  # Try XSS in team_size
                industry=xss_payload,   # Try XSS in industry
                user_id=None
            )

            # Verify XSS payload doesn't appear in raw form in output
            insights_str = str(insights.__dict__)
            assert "<script>" not in insights_str
            assert "javascript:" not in insights_str.lower()
            assert "onerror=" not in insights_str.lower()

    @pytest.mark.asyncio
    async def test_data_size_limits(self, onboarding_service):
        """Test data size limits enforcement"""
        oversized_data = {
            "team_size": "x" * 1000,  # Oversized team size
            "industry": "x" * 1000,   # Oversized industry
            "custom_field": "x" * 10000  # Very large field
        }

        # Should handle oversized data gracefully
        try:
            insights = await onboarding_service.generate_quick_insights(
                role=UserRole.MANAGER,
                challenge=TeamChallenge.COMMUNICATION,
                team_size=oversized_data["team_size"],
                industry=oversized_data["industry"],
                user_id=None
            )

            # Should still return insights but with sanitized/limited data
            assert insights is not None

        except Exception as e:
            # Should fail gracefully with validation error
            assert "too large" in str(e).lower() or "limit" in str(e).lower()


class TestPerformanceOptimization:
    """Test suite for performance optimization in onboarding services"""

    @pytest.fixture
    def onboarding_service(self):
        """Create OnboardingService instance"""
        return OnboardingService()

    @pytest.mark.asyncio
    async def test_concurrent_quick_assessments(self, onboarding_service):
        """Test concurrent quick assessment generation"""
        async def generate_assessment():
            return await onboarding_service.generate_quick_insights(
                role=UserRole.MANAGER,
                challenge=TeamChallenge.COMMUNICATION,
                team_size="5-10",
                industry="technology",
                user_id=None
            )

        # Generate 10 assessments concurrently
        tasks = [generate_assessment() for _ in range(10)]
        start_time = asyncio.get_event_loop().time()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()

        # Verify all assessments completed successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 10

        # Verify performance (should complete within reasonable time)
        total_time = end_time - start_time
        assert total_time < 10.0, f"Concurrent assessments took {total_time:.2f}s, expected < 10.0s"
        assert total_time / 10 < 2.0, f"Average time per assessment: {total_time/10:.2f}s, expected < 2.0s"

    @pytest.mark.asyncio
    async def test_caching_performance(self, onboarding_service):
        """Test caching performance for repeated requests"""
        # Mock Redis cache
        with patch('app.core.redis_client.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client

            # First request - cache miss
            mock_client.get.return_value = None
            mock_client.setex.return_value = True

            insights1 = await onboarding_service.generate_quick_insights(
                role=UserRole.MANAGER,
                challenge=TeamChallenge.COMMUNICATION,
                team_size="5-10",
                industry="technology",
                user_id=None
            )

            # Second request - cache hit
            cached_insights = json.dumps({
                "primary_benefit": insights1.primary_benefit,
                "recommendations": [asdict(rec) for rec in insights1.recommendations]
            })
            mock_client.get.return_value = cached_insights

            insights2 = await onboarding_service.generate_quick_insights(
                role=UserRole.MANAGER,
                challenge=TeamChallenge.COMMUNICATION,
                team_size="5-10",
                industry="technology",
                user_id=None
            )

            # Verify caching worked
            assert mock_client.get.called
            assert insights1.primary_benefit == insights2.primary_benefit

    @pytest.mark.asyncio
    async def test_memory_usage_optimization(self, onboarding_service):
        """Test memory usage optimization in large team analysis"""
        # Create large team composition
        large_team = [
            {
                "name": f"Team Member {i}",
                "role": "developer",
                "assessment_data": {
                    f"question_{j}": f"answer_{j}" for j in range(100)
                },
                "metadata": {
                    f"field_{k}": f"value_{k}" * 10 for k in range(50)
                }
            }
            for i in range(100)  # 100 team members with substantial data
        ]

        with patch('app.services.onboarding_service.TeamService') as mock_team_service:
            mock_team_service.get_team_members.return_value = large_team

            start_time = asyncio.get_event_loop().time()

            # Process large team
            insights = await onboarding_service.generate_detailed_team_insights(
                user_id="test-user-uuid",
                team_id="large-team-uuid",
                assessment_data={"test": "data"},
                team_composition=large_team
            )

            end_time = asyncio.get_event_loop().time()

            # Should complete in reasonable time even with large data
            processing_time = end_time - start_time
            assert processing_time < 5.0, f"Large team processing took {processing_time:.2f}s, expected < 5.0s"

            # Should return valid insights
            assert insights is not None
            assert hasattr(insights, 'team_profile')

    @pytest.mark.asyncio
    async def test_batch_operations_performance(self, onboarding_service):
        """Test performance of batch operations"""
        batch_size = 50
        assessment_requests = [
            {
                "role": UserRole.MANAGER,
                "challenge": TeamChallenge.COMMUNICATION,
                "team_size": "5-10",
                "industry": "technology"
            }
            for _ in range(batch_size)
        ]

        start_time = asyncio.get_event_loop().time()

        # Process assessments in batch
        tasks = [
            onboarding_service.generate_quick_insights(
                **req, user_id=None
            )
            for req in assessment_requests
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()

        # Verify batch processing performance
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == batch_size

        total_time = end_time - start_time
        avg_time_per_assessment = total_time / batch_size
        assert avg_time_per_assessment < 1.0, f"Avg time per assessment: {avg_time_per_assessment:.2f}s, expected < 1.0s"


# Test execution configuration
if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings",
        "-x"  # Stop on first failure
    ])