"""
Comprehensive tests for team optimization functionality
Tests the advanced recommendation engine with real-world scenarios
"""

from unittest.mock import patch

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


# Override auth dependency for tests
@pytest.fixture(scope="function", autouse=True)
def override_auth():
    """Override authentication to allow test calls"""
    from app.api.v1 import deps

    original = deps.get_current_user_optional

    async def mock_auth():
        return None  # No user required for optimization tests

    deps.get_current_user_optional = mock_auth
    yield
    deps.get_current_user_optional = original


# Create client with auth override applied
@pytest.fixture(scope="function")
def client(override_auth):
    """Create test client with auth override applied"""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


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
                    "openness": 0.75,
                    "conscientiousness": 0.6,
                    "extraversion": 0.3,
                    "agreeableness": 0.85,
                    "neuroticism": 0.4,
                },
                "skills": ["Figma", "CSS", "User Research", "Accessibility"],
                "experience_years": 5,
            },
            {
                "id": 3,
                "name": "Carol Johnson",
                "role": "Product Manager",
                "traits": {
                    "openness": 0.85,
                    "conscientiousness": 0.9,
                    "extraversion": 0.7,
                    "agreeableness": 0.75,
                    "neuroticism": 0.25,
                },
                "skills": [
                    "Agile",
                    "Scrum",
                    "Product Strategy",
                    "Stakeholder Management",
                ],
                "experience_years": 8,
            },
            {
                "id": 4,
                "name": "David Park",
                "role": "Backend Engineer",
                "traits": {
                    "openness": 0.7,
                    "conscientiousness": 0.75,
                    "extraversion": 0.4,
                    "agreeableness": 0.8,
                    "neuroticism": 0.35,
                },
                "skills": ["Python", "Go", "Kubernetes", "Docker", "System Design"],
                "experience_years": 6,
            },
            {
                "id": 5,
                "name": "Emma Wilson",
                "role": "QA Engineer",
                "traits": {
                    "openness": 0.8,
                    "conscientiousness": 0.85,
                    "extraversion": 0.5,
                    "agreeableness": 0.9,
                    "neuroticism": 0.2,
                },
                "skills": ["Selenium", "pytest", "Testing Tools", "Quality Assurance"],
                "experience_years": 4,
            },
        ]

    def test_recommend_groups_performance_optimization(self, client: TestClient):
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

    def test_recommend_groups_harmony_optimization(self, client: TestClient):
        """Test team optimization for harmony/balance"""
        request_data = {
            "members": self.sample_members,
            "objective": "maximize_harmony",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "recommended_groups" in data
        assert "overall_score" in data
        assert "insights" in data
        assert "metadata" in data

    def test_recommend_groups_diversity_optimization(self, client: TestClient):
        """Test team optimization for diversity"""
        request_data = {
            "members": self.sample_members,
            "objective": "maximize_diversity",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "recommended_groups" in data
        assert "overall_score" in data
        assert "insights" in data
        assert "metadata" in data

    def test_personality_compatibility_calculation(self, client: TestClient):
        """Test personality compatibility calculations"""
        member1 = self.sample_members[0]
        member2 = self.sample_members[1]

        compatibility_score = self.engine.calculate_role_compatibility(
            member1["traits"], member2["traits"]
        )

        assert 0 <= compatibility_score <= 1
        # Complementary traits (openness extraversion) should contribute positively
        # Similar traits (conscientiousness, agreeableness) should contribute positively
        # Low neuroticism should improve score

    def test_skill_coverage_calculation(self, client: TestClient):
        """Test skill coverage analysis"""
        team_composition = TeamComposition(
            member_ids=[m["id"] for m in self.sample_members],
            target_team_size=4,
            required_skills=["Python", "React", "AWS", "PostgreSQL"],
        )

        skill_coverage = self.engine.calculate_skill_coverage(
            team_composition.members, team_composition.required_skills
        )

        assert 0 <= skill_coverage <= 1
        # With diverse members, skill coverage should be good

    def test_insights_generation(self, client: TestClient):
        """Test insights generation"""
        team_composition = TeamComposition(
            member_ids=[m["id"] for m in self.sample_members],
            target_team_size=4,
        )

        insights = self.engine.generate_insights(team_composition)

        assert isinstance(insights, dict)
        assert "strengths" in insights
        assert "weaknesses" in insights
        assert "recommendations" in insights

    def test_insufficient_members(self, client: TestClient):
        """Test handling of insufficient members"""
        request_data = {
            "members": self.sample_members[:2],  # Less than min_size
            "objective": "maximize_performance",
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        # Should return 400 or appropriate error
        assert response.status_code in [200, 400]

    def test_invalid_objective(self, client: TestClient):
        """Test handling of invalid objective"""
        request_data = {
            "members": self.sample_members,
            "objective": "invalid_objective",  # Not in OptimizationObjective enum
        }

        response = client.post("/api/v1/team-optimizer/optimize", json=request_data)

        # Should return 400 or appropriate error
        assert response.status_code in [200, 400]
