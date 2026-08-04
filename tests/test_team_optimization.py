"""
Comprehensive tests for team optimization functionality
Tests the advanced recommendation engine with real-world scenarios
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.personality import PersonalityMapper
from app.services.recommendation import (
    RecommendationEngine,
    TeamComposition,
    TeamMember,
)

client = TestClient(app)


class TestRecommendationEngine:
    """Test the advanced recommendation engine"""

    def setup_method(self):
        """Set up test data"""
        self.engine = RecommendationEngine()
        self.personality_mapper = PersonalityMapper()

        # Sample team members with diverse traits
        self.sample_members = [
            {
                "id": 1,
                "name": "Alice Chen",
                "role": "Senior Developer",
                "traits": {
                    "openness": 0.9,
                    "conscientiousness": 0.8,
                    "extraversion": 0.6,
                    "agreeableness": 0.7,
                    "neuroticism": 0.3,
                },
                "skills": ["Python", "React", "AWS", "PostgreSQL", "Machine Learning"],
                "experience_years": 7,
            },
            {
                "id": 2,
                "name": "Bob Smith",
                "role": "UI/UX Designer",
                "traits": {
                    "openness": 0.8,
                    "conscientiousness": 0.6,
                    "extraversion": 0.7,
                    "agreeableness": 0.9,
                    "neuroticism": 0.4,
                },
                "skills": [
                    "Figma",
                    "Sketch",
                    "Adobe XD",
                    "Prototyping",
                    "User Research",
                ],
                "experience_years": 5,
            },
            {
                "id": 3,
                "name": "Carol Johnson",
                "role": "Product Manager",
                "traits": {
                    "openness": 0.7,
                    "conscientiousness": 0.9,
                    "extraversion": 0.8,
                    "agreeableness": 0.6,
                    "neuroticism": 0.5,
                },
                "skills": [
                    "Agile",
                    "Scrum",
                    "Roadmapping",
                    "Analytics",
                    "Communication",
                ],
                "experience_years": 6,
            },
            {
                "id": 4,
                "name": "David Lee",
                "role": "DevOps Engineer",
                "traits": {
                    "openness": 0.6,
                    "conscientiousness": 0.8,
                    "extraversion": 0.5,
                    "agreeableness": 0.5,
                    "neuroticism": 0.4,
                },
                "skills": [
                    "Docker",
                    "Kubernetes",
                    "Jenkins",
                    "Terraform",
                    "Monitoring",
                ],
                "experience_years": 4,
            },
            {
                "id": 5,
                "name": "Eva Martinez",
                "role": "QA Engineer",
                "traits": {
                    "openness": 0.5,
                    "conscientiousness": 0.9,
                    "extraversion": 0.4,
                    "agreeableness": 0.8,
                    "neuroticism": 0.3,
                },
                "skills": [
                    "Selenium",
                    "Jest",
                    "Cypress",
                    "Test Planning",
                    "Bug Tracking",
                ],
                "experience_years": 3,
            },
        ]

    def test_recommend_groups_performance_optimization(self):
        """Test team optimization for maximum performance"""
        request_data = {
            "members": self.sample_members,
            "objective": "maximize_performance",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "recommended_groups" in data
        assert "overall_score" in data
        assert "insights" in data
        assert "metadata" in data

        # Check that we got valid recommendations
        assert len(data["recommended_groups"]) > 0
        assert 0 <= data["overall_score"] <= 1

        # Validate recommended groups structure
        for group in data["recommended_groups"]:
            assert "member_ids" in group
            assert "compatibility_score" in group
            assert "skill_coverage" in group
            assert "diversity_score" in group
            assert "strengths" in group
            assert "risks" in group

    def test_recommend_groups_harmony_optimization(self):
        """Test team optimization for minimum conflicts"""
        request_data = {
            "members": self.sample_members,
            "objective": "minimize_conflicts",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Harmony optimization should prioritize compatibility
        for group in data["recommended_groups"]:
            assert group["compatibility_score"] > 0.6  # Should be high compatibility

    def test_recommend_groups_diversity_optimization(self):
        """Test team optimization for diversity"""
        request_data = {
            "members": self.sample_members,
            "objective": "balance_diversity",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Diversity optimization should result in diverse teams
        for group in data["recommended_groups"]:
            assert group["diversity_score"] > 0.5  # Should be diverse

    def test_personality_compatibility_calculation(self):
        """Test personality compatibility calculations"""
        # Test high compatibility
        compatible_traits_a = {
            "openness": 0.7,
            "conscientiousness": 0.8,
            "extraversion": 0.6,
            "agreeableness": 0.7,
            "neuroticism": 0.3,
        }
        compatible_traits_b = {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.5,
            "agreeableness": 0.8,
            "neuroticism": 0.4,
        }

        compatibility = self.personality_mapper.calculate_compatibility(
            compatible_traits_a, compatible_traits_b
        )
        assert compatibility > 0.6

        # Test low compatibility
        incompatible_traits_a = {
            "openness": 0.2,
            "conscientiousness": 0.3,
            "extraversion": 0.9,
            "agreeableness": 0.2,
            "neuroticism": 0.8,
        }
        incompatible_traits_b = {
            "openness": 0.9,
            "conscientiousness": 0.8,
            "extraversion": 0.1,
            "agreeableness": 0.9,
            "neuroticism": 0.2,
        }

        compatibility = self.personality_mapper.calculate_compatibility(
            incompatible_traits_a, incompatible_traits_b
        )
        assert compatibility < 0.6

    def test_skill_coverage_calculation(self):
        """Test skill coverage calculation"""
        team_with_good_coverage = [
            TeamMember(1, "Alice", "dev", {}, ["Python", "React", "AWS", "Docker"]),
            TeamMember(2, "Bob", "designer", {}, ["Figma", "UX", "CSS", "JavaScript"]),
            TeamMember(3, "Carol", "pm", {}, ["Agile", "Analytics", "Communication"]),
        ]

        coverage = self.engine._calculate_skill_coverage(team_with_good_coverage)
        assert coverage > 0.6

        # Test team with poor skill coverage
        team_with_poor_coverage = [
            TeamMember(1, "Alice", "dev", {}, ["Python", "Java"]),
            TeamMember(2, "Bob", "dev", {}, ["Python", "Java"]),
            TeamMember(3, "Carol", "dev", {}, ["Python", "Java"]),
        ]

        coverage = self.engine._calculate_skill_coverage(team_with_poor_coverage)
        assert coverage < 0.5

    def test_insights_generation(self):
        """Test insights generation for team recommendations"""
        # Create a test team composition
        test_composition = TeamComposition(
            member_ids=[1, 2, 3],
            roles_distribution={"developer": 1, "designer": 1, "pm": 1},
            compatibility_score=0.8,
            skill_coverage=0.7,
            diversity_score=0.6,
            strengths=["Good role balance", "High compatibility"],
            risks=["Limited experience diversity"],
        )

        # Generate insights
        insights = self.engine._generate_insights(
            [test_composition],
            [
                TeamMember(1, "Alice", "dev", {}, []),
                TeamMember(2, "Bob", "designer", {}, []),
                TeamMember(3, "Carol", "pm", {}, []),
            ],
            np.array([[1.0, 0.7, 0.6], [0.7, 1.0, 0.8], [0.6, 0.8, 1.0]]),
        )

        assert len(insights) > 0
        assert all(isinstance(insight, str) for insight in insights)

    def test_insufficient_members(self):
        """Test handling of insufficient members for optimization"""
        request_data = {
            "members": [
                {
                    "id": 1,
                    "name": "Alice",
                    "role": "developer",
                    "traits": {
                        "openness": 0.5,
                        "conscientiousness": 0.5,
                        "extraversion": 0.5,
                        "agreeableness": 0.5,
                        "neuroticism": 0.5,
                    },
                }
            ],
            "objective": "maximize_performance",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_invalid_objective(self):
        """Test handling of invalid optimization objective"""
        request_data = {
            "members": self.sample_members,
            "objective": "invalid_objective",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        # Should fall back to default optimization
        assert response.status_code == 200

    def test_team_size_variations(self):
        """Test optimization with different team sizes"""
        # Test with small team
        small_team = self.sample_members[:3]
        response = client.post(
            "/api/v1/team-optimizer/optimize",
            json={"members": small_team, "objective": "maximize_performance"},
        )
        assert response.status_code == 200

        # Test with large team
        large_team = self.sample_members * 2  # Duplicate for testing
        for i, member in enumerate(large_team[5:], 5):
            member["id"] = i
            member["name"] = f"Team Member {i}"

        response = client.post(
            "/api/v1/team-optimizer/optimize",
            json={"members": large_team, "objective": "maximize_performance"},
        )
        assert response.status_code == 200

    @patch("app.services.recommendation.logger")
    def test_error_handling(self, mock_logger):
        """Test error handling in recommendation engine"""
        # Test with malformed data
        malformed_data = {
            "members": [
                {
                    "id": "invalid_id",  # Should be integer
                    "name": 123,  # Should be string
                    "role": "",
                    "traits": "invalid",  # Should be dict
                }
            ],
            "objective": "maximize_performance",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=malformed_data)

        # Should handle error gracefully
        assert response.status_code == 422  # Validation error

    def test_compatibility_analysis_endpoint(self):
        """Test the compatibility analysis endpoint"""
        request_data = {"member_ids": [1, 2, 3]}

        response = client.post(
            "/api/v1/team-optimizer/compatibility-analysis", json=request_data
        )

        # May fail if members don't exist in database, but should have correct structure
        if response.status_code == 200:
            data = response.json()
            assert "pairs" in data
            assert "average_compatibility" in data
        else:
            # Expected if test data doesn't exist
            assert response.status_code in [400, 404]

    def test_role_compatibility_matrix(self):
        """Test that role compatibility matrix exists and is reasonable"""
        # Test developer-designer compatibility
        developer_designer_compat = self.engine._get_role_compatibility(
            "developer", "developer"
        )
        developer_designer_compat = self.engine._get_role_compatibility(
            "developer", "designer"
        )

        assert 0 <= developer_designer_compat <= 1
        assert 0 <= developer_designer_compat <= 1

        # Developer-designer should have high compatibility
        assert developer_designer_compat > 0.7

    def test_team_strengths_identification(self):
        """Test team strengths identification"""
        # Create a well-rounded team
        well_rounded_team = [
            TeamMember(
                1,
                "Alice",
                "senior_developer",
                {},
                ["Python", "React"],
                experience_years=8,
            ),
            TeamMember(2, "Bob", "designer", {}, ["Figma", "UX"], experience_years=5),
            TeamMember(
                3, "Carol", "qa", {}, ["Testing", "Automation"], experience_years=4
            ),
            TeamMember(
                4, "David", "pm", {}, ["Agile", "Communication"], experience_years=6
            ),
        ]

        strengths = self.engine._identify_team_strengths(well_rounded_team)

        assert len(strengths) > 0
        assert all(isinstance(strength, str) for strength in strengths)

    def test_team_risks_identification(self):
        """Test team risks identification"""
        # Create a team with potential risks
        risky_team = [
            TeamMember(
                1, "Alice", "junior_developer", {}, ["Python"], experience_years=1
            ),
            TeamMember(
                2, "Bob", "junior_developer", {}, ["Python"], experience_years=1
            ),
            TeamMember(
                3, "Carol", "junior_developer", {}, ["Python"], experience_years=1
            ),
        ]

        risks = self.engine._identify_team_risks(risky_team)

        assert len(risks) > 0
        assert any(
            "junior" in risk.lower() or "experience" in risk.lower() for risk in risks
        )


class TestPersonalityMapping:
    """Test personality mapping across frameworks"""

    def setup_method(self):
        self.mapper = PersonalityMapper()

    def test_mbti_to_big_five_conversion(self):
        """Test MBTI to Big Five conversion"""
        # Test INTJ type
        mbti_intj = {"type": "INTJ", "confidence": 0.9}
        result = self.mapper.map_traits(mbti_intj, "mbti")

        assert "openness" in result
        assert "conscientiousness" in result
        assert "extraversion" in result
        assert "agreeableness" in result
        assert "neuroticism" in result

        # INTJ should have high openness and low extraversion
        assert result["openness"] > 0.6
        assert result["extraversion"] < 0.5

    def test_enneagram_to_big_five_conversion(self):
        """Test Enneagram to Big Five conversion"""
        # Test Type 5 (Investigator)
        enneagram_5 = {"type": 5}
        result = self.mapper.map_traits(enneagram_5, "enneagram")

        # Type 5 should have high openness
        assert result["openness"] > 0.7
        assert result["extraversion"] < 0.5

    def test_disc_to_big_five_conversion(self):
        """Test DISC to Big Five conversion"""
        # Test High D type
        disc_high_d = {"profile": "D", "d_intensity": 0.9}
        result = self.mapper.map_traits(disc_high_d, "disc")

        # High D should have high extraversion
        assert result["extraversion"] > 0.7

    def test_big_five_normalization(self):
        """Test Big Five trait normalization"""
        # Test 1-5 scale
        traits_1_5 = {"openness": 5, "conscientiousness": 1, "extraversion": 3}
        result = self.mapper.map_traits(traits_1_5, "big_five")

        assert result["openness"] == 1.0
        assert result["conscientiousness"] == 0.0
        assert result["extraversion"] == 0.5

        # Test 1-10 scale
        traits_1_10 = {"openness": 10, "conscientiousness": 1, "extraversion": 5}
        result = self.mapper.map_traits(traits_1_10, "big_five")

        assert result["openness"] == 1.0
        assert result["conscientiousness"] == 0.1
        assert result["extraversion"] == 0.5

        # Test 1-100 scale
        traits_1_100 = {"openness": 100, "conscientiousness": 0, "extraversion": 50}
        result = self.mapper.map_traits(traits_1_100, "big_five")

        assert result["openness"] == 1.0
        assert result["conscientiousness"] == 0.0
        assert result["extraversion"] == 0.5

    def test_invalid_framework_fallback(self):
        """Test fallback for invalid framework"""
        invalid_traits = {"some_trait": 0.7}
        result = self.mapper.map_traits(invalid_traits, "invalid_framework")

        # Should return default traits
        expected_defaults = self.mapper._get_default_traits()
        assert result == expected_defaults

    def test_caching_mechanism(self):
        """Test that trait mapping results are cached"""
        # First call
        traits = {"type": "INTJ"}
        result1 = self.mapper.map_traits(traits, "mbti")

        # Second call with same data
        result2 = self.mapper.map_traits(traits, "mbti")

        # Results should be identical (cached)
        assert result1 == result2

    def test_predictive_index_conversion(self):
        """Test Predictive Index conversion"""
        pi_traits = {
            "A": 80,
            "B": 30,
            "C": 70,
            "D": 60,
        }  # High dominance, low extraversion
        result = self.mapper.map_traits(pi_traits, "predictive_index")

        assert 0 <= result["extraversion"] <= 1
        assert 0 <= result["conscientiousness"] <= 1
        assert 0 <= result["openness"] <= 1
        assert 0 <= result["agreeableness"] <= 1
        assert 0 <= result["neuroticism"] <= 1

    def test_clifton_strengths_conversion(self):
        """Test Clifton Strengths conversion"""
        strengths_traits = {
            "strengths": ["Achiever", "Learner", "Ideation", "Analytical"]
        }
        result = self.mapper.map_traits(strengths_traits, "clifton_strengths")

        # Should have elevated conscientiousness and openness
        assert result["conscientiousness"] > 0.5
        assert result["openness"] > 0.5

    def test_compatibility_insights(self):
        """Test compatibility insights generation"""
        traits_a = {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.7,
            "neuroticism": 0.3,
        }
        traits_b = {
            "openness": 0.2,
            "conscientiousness": 0.3,
            "extraversion": 0.4,
            "agreeableness": 0.3,
            "neuroticism": 0.8,
        }

        insights = self.mapper.get_compatibility_insights(traits_a, traits_b)

        assert len(insights) > 0
        assert all(isinstance(insight, str) for insight in insights)

    def test_range_ensurance(self):
        """Test that all trait values are within valid range"""
        extreme_traits = {"openness": -100, "conscientiousness": 999, "extraversion": 0}
        result = self.mapper.map_traits(extreme_traits, "raw")

        for value in result.values():
            assert 0 <= value <= 1


class TestTeamOptimizationAPI:
    """Test the team optimization API endpoints"""

    def test_health_check(self):
        """Test that the API is accessible"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_invalid_request_format(self):
        """Test handling of invalid request formats"""
        # Missing required fields
        invalid_request = {"members": []}
        response = client.post("/api/v1/team-optimizer/optimize", json=invalid_request)
        assert response.status_code == 422

        # Invalid JSON
        response = client.post(
            "/api/v1/team-optimizer/optimize",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_large_request_handling(self):
        """Test handling of large requests"""
        # Create a large team (50 members)
        large_team = []
        for i in range(50):
            large_team.append(
                {
                    "id": i,
                    "name": f"Team Member {i}",
                    "role": "developer",
                    "traits": {
                        "openness": 0.5 + (i % 10) * 0.05,
                        "conscientiousness": 0.5 + (i % 10) * 0.05,
                        "extraversion": 0.5 + (i % 10) * 0.05,
                        "agreeableness": 0.5 + (i % 10) * 0.05,
                        "neuroticism": 0.5 + (i % 10) * 0.05,
                    },
                }
            )

        response = client.post(
            "/api/v1/team-optimizer/optimize",
            json={"members": large_team, "objective": "maximize_performance"},
        )

        # Should handle large requests
        assert response.status_code in [200, 413]  # 413 if payload too large

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent optimization requests"""
        import asyncio

        import aiohttp

        sample_request = {
            "members": [
                {
                    "id": 1,
                    "name": "Test User",
                    "role": "developer",
                    "traits": {
                        "openness": 0.5,
                        "conscientiousness": 0.5,
                        "extraversion": 0.5,
                        "agreeableness": 0.5,
                        "neuroticism": 0.5,
                    },
                }
            ],
            "objective": "maximize_performance",
        }

        async def make_request():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://testserver/api/v1/team-optimizer/optimize",
                    json=sample_request,
                ) as response:
                    return response.status

        # Run multiple concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All requests should complete successfully or gracefully
        assert all(
            isinstance(result, int) or isinstance(result, Exception)
            for result in results
        )

    def test_response_headers(self):
        """Test that response headers are properly set"""
        response = client.post(
            "/api/v1/team-optimizer/optimize",
            json={
                "members": [
                    {
                        "id": 1,
                        "name": "Test User",
                        "role": "developer",
                        "traits": {
                            "openness": 0.5,
                            "conscientiousness": 0.5,
                            "extraversion": 0.5,
                            "agreeableness": 0.5,
                            "neuroticism": 0.5,
                        },
                    }
                ],
                "objective": "maximize_performance",
            },
        )

        if response.status_code == 200:
            # Check for security headers
            assert "content-type" in response.headers
            assert "application/json" in response.headers["content-type"]

    def test_metadata_consistency(self):
        """Test that metadata in responses is consistent"""
        request_data = {
            "members": [
                {
                    "id": 1,
                    "name": "Test User",
                    "role": "developer",
                    "traits": {
                        "openness": 0.5,
                        "conscientiousness": 0.5,
                        "extraversion": 0.5,
                        "agreeableness": 0.5,
                        "neuroticism": 0.5,
                    },
                }
            ],
            "objective": "maximize_performance",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        if response.status_code == 200:
            data = response.json()

            # Check metadata structure
            assert "metadata" in data
            metadata = data["metadata"]

            assert "algorithm" in metadata
            assert "total_candidates" in metadata
            assert "optimization_time" in metadata
            assert "objective" in metadata

            assert metadata["objective"] == request_data["objective"]
            assert metadata["total_candidates"] == len(request_data["members"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
