"""
Locust Configuration File for PsychSync Load Testing
Provides shared configuration and utilities for all Locust test files
"""

import os
import random
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadTestConfig:
    """Centralized configuration for load testing"""

    # API Configuration
    API_BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:8000")
    API_V1_PREFIX = "/api/v1"

    # Test User Credentials Pool
    TEST_USERS = {
        "admin": {"email": "admin@test.com", "password": "TestAdmin123!"},
        "user_1": {"email": "user1@test.com", "password": "TestUser123!"},
        "user_2": {"email": "user2@test.com", "password": "TestUser123!"},
    }

    # Performance thresholds (in milliseconds)
    THRESHOLDS = {
        "p50": 500,  # 50% of requests should complete within 500ms
        "p95": 1500,  # 95% of requests should complete within 1500ms
        "p99": 3000,  # 99% of requests should complete within 3000ms
    }

    # Wait times between requests (in seconds)
    WAIT_TIMES = {
        "min": 1,  # Minimum think time
        "max": 3,  # Maximum think time
    }

    # Test data IDs
    ASSESSMENT_IDS = [
        "mbti-001",
        "big-five-001",
        "enneagram-001",
        "disc-001",
    ]

    TEAM_IDS = [
        "team-001",
        "team-002",
        "team-003",
    ]

    # Personality frameworks
    PERSONALITY_FRAMEWORKS = [
        "mbti",
        "big_five",
        "enneagram",
        "predictive_index",
        "disct",
        "clifton_strengths",
        "social_styles",
    ]

    # Sample assessment responses
    SAMPLE_RESPONSES = {
        "mbti": [{"question_id": f"q{i}", "answer": random.randint(1, 5)} for i in range(1, 94)],
        "big_five": [{"question_id": f"q{i}", "answer": random.randint(1, 5)} for i in range(1, 45)],
        "enneagram": [{"question_id": f"q{i}", "answer": random.randint(1, 5)} for i in range(1, 145)],
    }

    # Load levels
    LOAD_LEVELS = {
        "small": {"users": 100, "spawn_rate": 10},
        "medium": {"users": 1000, "spawn_rate": 50},
        "large": {"users": 10000, "spawn_rate": 200},
    }

    # Custom weights for mixed workload
    WEIGHTS = {
        "auth": 15,  # 15% of users do authentication
        "assessment": 40,  # 40% of users take assessments
        "dashboard": 20,  # 20% of users view dashboard
        "team": 15,  # 15% of users manage teams
        "assessment_mgmt": 5,  # 5% of users manage assessments
        "ai_nlp": 5,  # 5% of users use AI features
    }


class TestDataManager:
    """Manages test data for load tests"""

    def __init__(self):
        self.current_data: Dict[str, Any] = {}
        self.user_pool: List[Dict[str, str]] = []

    def generate_test_users(self, count: int = 1000) -> List[Dict[str, str]]:
        """Generate test user credentials"""
        users = []
        for i in range(count):
            users.append({
                "email": f"loadtest_user_{i}@test.com",
                "password": "LoadTest123!",
                "username": f"loadtest_{i}",
            })
        self.user_pool = users
        return users

    def get_random_user(self) -> Dict[str, str]:
        """Get random test user"""
        if not self.user_pool:
            self.generate_test_users()
        return random.choice(self.user_pool)

    def get_random_assessment_id(self) -> str:
        """Get random assessment ID"""
        return random.choice(LoadTestConfig.ASSESSMENT_IDS)

    def get_random_team_id(self) -> str:
        """Get random team ID"""
        return random.choice(LoadTestConfig.TEAM_IDS)

    def get_random_framework(self) -> str:
        """Get random personality framework"""
        return random.choice(LoadTestConfig.PERSONALITY_FRAMEWORKS)

    def generate_assessment_responses(self, framework: str) -> List[Dict[str, Any]]:
        """Generate random assessment responses"""
        if framework in LoadTestConfig.SAMPLE_RESPONSES:
            return LoadTestConfig.SAMPLE_RESPONSES[framework].copy()

        # Generic response generation
        num_questions = random.randint(20, 100)
        return [
            {"question_id": f"q{i}", "answer": random.randint(1, 5)}
            for i in range(1, num_questions + 1)
        ]


def get_headers(token: str = None) -> Dict[str, str]:
    """Get HTTP headers for requests"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "PsychSync-LoadTest/1.0",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def log_response(response, context: str = ""):
    """Log response details for debugging"""
    if response.status_code >= 400:
        logger.error(
            f"{context} - Failed: {response.status_code} - "
            f"{response.text[:200] if hasattr(response, 'text') else ''}"
        )
    else:
        logger.debug(f"{context} - Success: {response.status_code}")


# Global test data manager instance
test_data_manager = TestDataManager()
