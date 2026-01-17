"""
Comprehensive Mock Data Generators for Testing
Provides realistic test data for various scenarios and edge cases
Supports 1000% performance optimization testing with large datasets
"""

import random
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
import string
import itertools

from faker import Faker
import numpy as np

from app.db.models.user import User, UserRole
from app.db.models.team import Team, TeamRole, TeamMember
from app.db.models.organization import Organization
from app.db.models.assessment import Assessment, AssessmentCategory, AssessmentStatus, Question, QuestionType, AnswerOption
from app.db.models.response import Response, ResponseType


class DataComplexity(Enum):
    """Data complexity levels for testing"""
    MINIMAL = "minimal"      # Smallest valid data
    REALISTIC = "realistic"  # Typical production data
    COMPLEX = "complex"      # Complex nested data
    STRESS = "stress"        # Maximum stress testing data


@dataclass
class DataGenerationConfig:
    """Configuration for data generation"""
    complexity: DataComplexity = DataComplexity.REALISTIC
    locale: str = "en_US"
    seed: Optional[int] = None
    include_edge_cases: bool = True
    include_malformed_data: bool = False
    size_multiplier: int = 1  # For generating large datasets


class TestDataGenerator:
    """Comprehensive test data generator"""

    def __init__(self, config: DataGenerationConfig = None):
        self.config = config or DataGenerationConfig()
        self.fake = Faker(self.config.locale)

        if self.config.seed:
            Faker.seed(self.config.seed)
            random.seed(self.config.seed)
            np.random.seed(self.config.seed)

    def generate_user_data(self, complexity: DataComplexity = None, count: int = 1) -> Union[Dict, List[Dict]]:
        """Generate realistic user test data"""
        complexity = complexity or self.config.complexity

        if count == 1:
            return self._generate_single_user(complexity)
        else:
            return [self._generate_single_user(complexity) for _ in range(count)]

    def _generate_single_user(self, complexity: DataComplexity) -> Dict[str, Any]:
        """Generate a single user based on complexity level"""
        base_data = {
            "id": str(uuid.uuid4()),
            "email": self.fake.email(),
            "full_name": self.fake.name(),
            "created_at": self.fake.date_time_between(start_date="-2y", end_date="now"),
            "updated_at": self.fake.date_time_between(start_date="-30d", end_date="now"),
            "is_active": True,
            "is_verified": random.choice([True, False, True, True])  # Bias towards verified
        }

        if complexity == DataComplexity.MINIMAL:
            return base_data

        # Add role information
        base_data["role"] = random.choice(list(UserRole))

        # Add extended profile information
        base_data.update({
            "phone": self.fake.phone_number(),
            "avatar_url": self.fake.image_url(),
            "bio": self.fake.text(max_nb_chars=200),
            "timezone": self.fake.timezone(),
            "language": random.choice(["en", "es", "fr", "de", "zh", "ja"]),
            "department": random.choice(["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"]),
            "job_title": self.fake.job(),
            "location": {
                "city": self.fake.city(),
                "country": self.fake.country(),
                "latitude": float(self.fake.latitude()),
                "longitude": float(self.fake.longitude())
            }
        })

        if complexity in [DataComplexity.COMPLEX, DataComplexity.STRESS]:
            # Add complex nested data
            base_data.update({
                "preferences": {
                    "notifications": {
                        "email": random.choice([True, False]),
                        "push": random.choice([True, False]),
                        "sms": random.choice([True, False])
                    },
                    "privacy": {
                        "profile_visible": random.choice(["public", "team", "private"]),
                        "activity_visible": random.choice([True, False])
                    },
                    "ui": {
                        "theme": random.choice(["light", "dark", "auto"]),
                        "language": base_data["language"],
                        "timezone": base_data["timezone"]
                    }
                },
                "skills": [self.fake.job_skill() for _ in range(random.randint(1, 10))],
                "certifications": [
                    {
                        "name": f"Certificate {i}",
                        "issuer": self.fake.company(),
                        "date": self.fake.date_between(start_date="-5y", end_date="-1y"),
                        "credential_id": str(uuid.uuid4())[:8].upper()
                    }
                    for i in range(random.randint(0, 5))
                ],
                "work_history": [
                    {
                        "company": self.fake.company(),
                        "position": self.fake.job(),
                        "start_date": self.fake.date_between(start_date="-10y", end_date="-2y"),
                        "end_date": self.fake.date_between(start_date="-2y", end_date="-1y"),
                        "description": self.fake.text(max_nb_chars=300)
                    }
                    for i in range(random.randint(1, 5))
                ]
            })

        if complexity == DataComplexity.STRESS:
            # Add stress-level data (large amounts)
            base_data.update({
                "activity_log": [
                    {
                        "timestamp": self.fake.date_time_between(start_date="-30d", end_date="now"),
                        "action": random.choice(["login", "assessment_started", "assessment_completed", "team_joined"]),
                        "metadata": {"ip": self.fake.ipv4(), "user_agent": self.fake.user_agent()}
                    }
                    for _ in range(100 * self.config.size_multiplier)
                ],
                "assessment_results": [
                    {
                        "assessment_id": str(uuid.uuid4()),
                        "score": round(random.uniform(1.0, 5.0), 2),
                        "completed_at": self.fake.date_time_between(start_date="-90d", end_date="now"),
                        "category": random.choice(list(AssessmentCategory))
                    }
                    for _ in range(20 * self.config.size_multiplier)
                ]
            })

        return base_data

    def generate_organization_data(self, complexity: DataComplexity = None, count: int = 1) -> Union[Dict, List[Dict]]:
        """Generate organization test data"""
        complexity = complexity or self.config.complexity

        if count == 1:
            return self._generate_single_organization(complexity)
        else:
            return [self._generate_single_organization(complexity) for _ in range(count)]

    def _generate_single_organization(self, complexity: DataComplexity) -> Dict[str, Any]:
        """Generate a single organization based on complexity level"""
        base_data = {
            "id": str(uuid.uuid4()),
            "name": self.fake.company(),
            "created_at": self.fake.date_time_between(start_date="-5y", end_date="-1y"),
            "updated_at": self.fake.date_time_between(start_date="-30d", end_date="now"),
            "is_active": True,
            "subscription_tier": random.choice(["free", "professional", "enterprise"])
        }

        if complexity == DataComplexity.MINIMAL:
            return base_data

        base_data.update({
            "description": self.fake.catch_phrase(),
            "website": self.fake.url(),
            "industry": random.choice(["Technology", "Healthcare", "Finance", "Education", "Manufacturing", "Retail"]),
            "size": random.choice(["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]),
            "location": {
                "address": self.fake.street_address(),
                "city": self.fake.city(),
                "state": self.fake.state(),
                "country": self.fake.country(),
                "postal_code": self.fake.postcode()
            },
            "contact": {
                "email": f"contact@{self.fake.domain_name()}",
                "phone": self.fake.phone_number(),
                "support_email": f"support@{self.fake.domain_name()}"
            }
        })

        if complexity in [DataComplexity.COMPLEX, DataComplexity.STRESS]:
            base_data.update({
                "settings": {
                    "features": {
                        "advanced_analytics": base_data["subscription_tier"] != "free",
                        "api_access": base_data["subscription_tier"] == "enterprise",
                        "custom_assessments": base_data["subscription_tier"] != "free",
                        "sso_integration": base_data["subscription_tier"] == "enterprise",
                        "priority_support": base_data["subscription_tier"] in ["professional", "enterprise"]
                    },
                    "security": {
                        "require_2fa": random.choice([True, False]),
                        "session_timeout": random.choice([30, 60, 120, 480]),  # minutes
                        "password_policy": {
                            "min_length": random.choice([8, 12, 16]),
                            "require_uppercase": True,
                            "require_numbers": True,
                            "require_symbols": random.choice([True, False])
                        }
                    },
                    "notifications": {
                        "email_digest": random.choice(["daily", "weekly", "never"]),
                        "security_alerts": True,
                        "usage_reports": random.choice([True, False])
                    }
                },
                "billing": {
                    "plan_id": str(uuid.uuid4()),
                    "next_billing_date": self.fake.date_between(start_date="+1d", end_date="+30d"),
                    "payment_method": random.choice(["credit_card", "invoice", "ach"]),
                    "usage_limits": {
                        "users": random.choice([10, 50, 200, 1000]) * self.config.size_multiplier,
                        "assessments_per_month": random.choice([100, 500, 2000, 10000]) * self.config.size_multiplier,
                        "storage_gb": random.choice([5, 50, 200, 1000])
                    }
                },
                "integrations": [
                    {
                        "type": random.choice(["slack", "microsoft_teams", "zoom", "sso"]),
                        "configured": random.choice([True, False]),
                        "last_sync": self.fake.date_time_between(start_date="-7d", end_date="now") if random.choice([True, False]) else None
                    }
                    for _ in range(random.randint(1, 5))
                ]
            })

        if complexity == DataComplexity.STRESS:
            # Add large amounts of stress data
            base_data.update({
                "usage_statistics": {
                    "daily_active_users": [
                        {
                            "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                            "count": random.randint(1, 100 * self.config.size_multiplier)
                        }
                        for i in range(365)
                    ],
                    "assessment_completion_rates": [
                        {
                            "assessment_type": category.value,
                            "total_started": random.randint(10, 1000) * self.config.size_multiplier,
                            "total_completed": random.randint(5, 800) * self.config.size_multiplier,
                            "average_completion_time": random.randint(300, 3600)  # seconds
                        }
                        for category in AssessmentCategory
                    ]
                }
            })

        return base_data

    def generate_assessment_data(self, complexity: DataComplexity = None, count: int = 1) -> Union[Dict, List[Dict]]:
        """Generate assessment test data"""
        complexity = complexity or self.config.complexity

        if count == 1:
            return self._generate_single_assessment(complexity)
        else:
            return [self._generate_single_assessment(complexity) for _ in range(count)]

    def _generate_single_assessment(self, complexity: DataComplexity) -> Dict[str, Any]:
        """Generate a single assessment based on complexity level"""
        category = random.choice(list(AssessmentCategory))
        base_data = {
            "id": str(uuid.uuid4()),
            "title": self.fake.catch_phrase(),
            "description": self.fake.text(max_nb_chars=500),
            "category": category,
            "status": AssessmentStatus.DRAFT,
            "created_at": self.fake.date_time_between(start_date="-6m", end_date="now"),
            "updated_at": self.fake.date_time_between(start_date="-30d", end_date="now"),
            "estimated_duration_minutes": random.randint(5, 60),
            "is_active": True
        }

        if complexity == DataComplexity.MINIMAL:
            return base_data

        base_data.update({
            "instructions": self.fake.paragraph(),
            "tags": [self.fake.word() for _ in range(random.randint(1, 5))],
            "difficulty_level": random.choice(["beginner", "intermediate", "advanced"]),
            "target_audience": random.choice(["individuals", "teams", "organizations", "all"]),
            "language": random.choice(["en", "es", "fr", "de"]),
            "version": f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"
        })

        # Generate questions based on category
        question_count = self._get_question_count_for_category(category, complexity)
        base_data["questions"] = self._generate_questions(category, question_count, complexity)

        if complexity in [DataComplexity.COMPLEX, DataComplexity.STRESS]:
            base_data.update({
                "scoring": {
                    "method": random.choice(["weighted", "normalized", "raw"]),
                    "passing_score": random.randint(60, 90),
                    "max_score": random.randint(100, 1000),
                    "curve_type": random.choice(["linear", "bell_curve", "exponential"]),
                    "dimension_weights": self._generate_dimension_weights()
                },
                "settings": {
                    "allow_review": random.choice([True, False]),
                    "show_results_immediately": random.choice([True, False]),
                    "time_limit": random.choice([None, random.randint(300, 3600)]),  # None or 5-60 minutes
                    "randomize_questions": random.choice([True, False]),
                    "prevent_cheating": {
                        "disable_copy_paste": random.choice([True, False]),
                        "track_mouse_movement": random.choice([True, False]),
                        "webcam_proctoring": random.choice([True, False])
                    }
                },
                "analytics": {
                    "completion_rate": round(random.uniform(0.3, 0.95), 2),
                    "average_score": round(random.uniform(60, 90), 1),
                    "average_completion_time": random.randint(300, 1800),
                    "difficulty_rating": round(random.uniform(1.0, 5.0), 1),
                    "most_common_dropped_question": random.randint(1, question_count)
                }
            })

        if complexity == DataComplexity.STRESS:
            # Add stress-level data
            base_data.update({
                "validation_history": [
                    {
                        "validator_id": str(uuid.uuid4()),
                        "validated_at": self.fake.date_time_between(start_date="-30d", end_date="now"),
                        "changes_made": random.randint(0, 50),
                        "notes": self.fake.sentence()
                    }
                    for _ in range(10 * self.config.size_multiplier)
                ],
                "usage_metrics": {
                    "total_completions": random.randint(100, 10000) * self.config.size_multiplier,
                    "average_completion_rate": round(random.uniform(0.7, 0.95), 3),
                    "peak_usage_time": random.choice(["morning", "afternoon", "evening"]),
                    "device_breakdown": {
                        "desktop": round(random.uniform(0.3, 0.7), 2),
                        "mobile": round(random.uniform(0.2, 0.5), 2),
                        "tablet": round(random.uniform(0.05, 0.2), 2)
                    }
                }
            })

        return base_data

    def _get_question_count_for_category(self, category: AssessmentCategory, complexity: DataComplexity) -> int:
        """Get appropriate question count based on category and complexity"""
        base_counts = {
            AssessmentCategory.PERSONALITY: 50,
            AssessmentCategory.TEAM_BUILDING: 30,
            AssessmentCategory.LEADERSHIP: 25,
            AssessmentCategory.COMMUNICATION: 20,
            AssessmentCategory.SKILLS_ASSESSMENT: 40,
            AssessmentCategory.CULTURE_FIT: 35,
            AssessmentCategory.PERFORMANCE_REVIEW: 15,
            AssessmentCategory.TRAINING_NEEDS: 30
        }

        multipliers = {
            DataComplexity.MINIMAL: 0.2,
            DataComplexity.REALISTIC: 1.0,
            DataComplexity.COMPLEX: 1.5,
            DataComplexity.STRESS: 3.0
        }

        base_count = base_counts.get(category, 25)
        multiplier = multipliers.get(complexity, 1.0)

        return max(5, int(base_count * multiplier * self.config.size_multiplier))

    def _generate_questions(self, category: AssessmentCategory, count: int, complexity: DataComplexity) -> List[Dict]:
        """Generate questions for an assessment"""
        questions = []

        for i in range(count):
            question = self._generate_single_question(category, i + 1, complexity)
            questions.append(question)

        return questions

    def _generate_single_question(self, category: AssessmentCategory, question_number: int, complexity: DataComplexity) -> Dict[str, Any]:
        """Generate a single question"""
        base_question = {
            "id": str(uuid.uuid4()),
            "order": question_number,
            "text": self._generate_question_text(category, question_number),
            "type": self._get_question_type_for_category(category),
            "required": True,
            "created_at": self.fake.date_time_between(start_date="-6m", end_date="now")
        }

        # Add answer options based on question type
        if base_question["type"] in [QuestionType.MULTIPLE_CHOICE, QuestionType.LIKERT, QuestionType.SCALE]:
            base_question["answer_options"] = self._generate_answer_options(base_question["type"])

        if complexity in [DataComplexity.COMPLEX, DataComplexity.STRESS]:
            base_question.update({
                "explanation": self.fake.paragraph(),
                "time_limit_seconds": random.choice([None, 30, 60, 120]),
                "weight": round(random.uniform(0.5, 2.0), 2),
                "dimension_tags": [f"dimension_{i}" for i in range(random.randint(1, 4))],
                "difficulty_rating": random.randint(1, 5)
            })

        if complexity == DataComplexity.STRESS:
            base_question.update({
                "validation_rules": [
                    {
                        "type": "min_length",
                        "value": random.randint(10, 100)
                    },
                    {
                        "type": "max_length",
                        "value": random.randint(500, 2000)
                    }
                ] if base_question["type"] == QuestionType.TEXT else [],
                "metadata": {
                    "author_notes": self.fake.text(max_nb_chars=200),
                    "source_reference": self.fake.url() if random.choice([True, False]) else None,
                    "last_reviewed": self.fake.date_time_between(start_date="-90d", end_date="-30d")
                }
            })

        return base_question

    def _generate_question_text(self, category: AssessmentCategory, question_number: int) -> str:
        """Generate question text based on category"""
        templates = {
            AssessmentCategory.PERSONALITY: [
                "I see myself as someone who is {}",
                "When working in a team, I tend to {}",
                "In stressful situations, I usually {}",
                "I prefer to {} when solving problems",
                "Others would describe me as {}"
            ],
            AssessmentCategory.TEAM_BUILDING: [
                "How would you rate your team's ability to {}?",
                "What is the most important factor for team {}?",
                "How do you handle {} within your team?",
                "Rate your agreement: Our team effectively {}",
                "When conflicts arise, our team tends to {}"
            ],
            AssessmentCategory.LEADERSHIP: [
                "A good leader should always {}",
                "When making decisions, I prefer to {}",
                "I handle leadership challenges by {}",
                "My leadership style is best described as {}",
                "I believe that successful leaders {}"
            ],
            AssessmentCategory.COMMUNICATION: [
                "I prefer to communicate through {}",
                "When giving feedback, I usually {}",
                "In meetings, I tend to {}",
                "I handle difficult conversations by {}",
                "My communication style is most effective when {}"
            ]
        }

        category_templates = templates.get(category, [
            "Please rate your agreement with: {}",
            "How would you describe your ability to {}?",
            "When faced with {}, I typically {}"
        ])

        template = random.choice(category_templates)
        action = random.choice([
            "take initiative", "collaborate with others", "analyze situations carefully",
            "focus on details", "think creatively", "maintain organization",
            "adapt to change", "communicate clearly", "solve problems systematically",
            "lead by example", "support team members", "make decisions confidently"
        ])

        return template.format(action)

    def _get_question_type_for_category(self, category: AssessmentCategory) -> QuestionType:
        """Get appropriate question type for category"""
        if category == AssessmentCategory.PERSONALITY:
            return random.choice([QuestionType.LIKERT, QuestionType.MULTIPLE_CHOICE])
        elif category == AssessmentCategory.TEAM_BUILDING:
            return random.choice([QuestionType.SCALE, QuestionType.LIKERT])
        elif category == AssessmentCategory.LEADERSHIP:
            return random.choice([QuestionType.MULTIPLE_CHOICE, QuestionType.TEXT])
        else:
            return random.choice(list(QuestionType))

    def _generate_answer_options(self, question_type: QuestionType) -> List[Dict]:
        """Generate answer options for a question"""
        if question_type == QuestionType.LIKERT:
            return [
                {"id": str(i), "text": text, "value": i, "order": i-1}
                for i, text in enumerate([
                    "Strongly Disagree",
                    "Disagree",
                    "Neutral",
                    "Agree",
                    "Strongly Agree"
                ], 1)
            ]
        elif question_type == QuestionType.SCALE:
            scale_size = random.choice([5, 7, 10])
            return [
                {"id": str(i), "text": str(i), "value": i, "order": i-1}
                for i in range(1, scale_size + 1)
            ]
        elif question_type == QuestionType.MULTIPLE_CHOICE:
            options_count = random.randint(3, 6)
            return [
                {
                    "id": str(uuid.uuid4()),
                    "text": self.fake.sentence(),
                    "value": chr(65 + i),  # A, B, C, D, E, F
                    "order": i,
                    "is_correct": i == 0  # First option is correct
                }
                for i in range(options_count)
            ]
        else:
            return []

    def _generate_dimension_weights(self) -> Dict[str, float]:
        """Generate dimension weights for assessment scoring"""
        dimensions = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        weights = []

        # Generate weights that sum to 1.0
        remaining_weight = 1.0
        for i in range(len(dimensions) - 1):
            weight = round(random.uniform(0.1, remaining_weight * 0.7), 2)
            weights.append(weight)
            remaining_weight -= weight

        weights.append(round(remaining_weight, 2))

        # Adjust for rounding errors
        weights = [w / sum(weights) for w in weights]

        return dict(zip(dimensions, [round(w, 2) for w in weights]))

    def generate_team_data(self, complexity: DataComplexity = None, count: int = 1) -> Union[Dict, List[Dict]]:
        """Generate team test data"""
        complexity = complexity or self.config.complexity

        if count == 1:
            return self._generate_single_team(complexity)
        else:
            return [self._generate_single_team(complexity) for _ in range(count)]

    def _generate_single_team(self, complexity: DataComplexity) -> Dict[str, Any]:
        """Generate a single team based on complexity level"""
        base_data = {
            "id": str(uuid.uuid4()),
            "name": self.fake.catch_phrase(),
            "description": self.fake.text(max_nb_chars=300),
            "created_at": self.fake.date_time_between(start_date="-1y", end_date="now"),
            "updated_at": self.fake.date_time_between(start_date="-30d", end_date="now"),
            "is_active": True,
            "department": random.choice(["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"])
        }

        if complexity == DataComplexity.MINIMAL:
            return base_data

        base_data.update({
            "team_type": random.choice(["development", "sales", "marketing", "hr", "operations", "executive"]),
            "size": random.choice(["small", "medium", "large"]),
            "purpose": self.fake.text(max_nb_chars=200),
            "goals": [self.fake.sentence() for _ in range(random.randint(1, 5))],
            "communication_channel": random.choice(["slack", "teams", "zoom", "email", "in-person"])
        })

        if complexity in [DataComplexity.COMPLEX, DataComplexity.STRESS]:
            base_data.update({
                "settings": {
                    "privacy": random.choice(["public", "organization", "team", "private"]),
                    "member_permissions": {
                        "can_invite_members": random.choice([True, False]),
                        "can_create_assessments": random.choice([True, False]),
                        "can_view_analytics": random.choice([True, False]),
                        "can_manage_team": random.choice([True, False])
                    },
                    "assessment_preferences": {
                        "required_assessments": random.randint(0, 5),
                        "assessment_frequency": random.choice(["monthly", "quarterly", "bi-annually"]),
                        "auto_reminders": random.choice([True, False])
                    }
                },
                "performance_metrics": {
                    "productivity_score": round(random.uniform(60, 95), 1),
                    "collaboration_score": round(random.uniform(50, 100), 1),
                    "innovation_index": round(random.uniform(30, 90), 1),
                    "communication_effectiveness": round(random.uniform(40, 95), 1),
                    "goal_achievement_rate": round(random.uniform(70, 98), 1)
                },
                "member_roles": [
                    {
                        "role": role,
                        "count": random.randint(1, 5),
                        "responsibilities": [self.fake.sentence() for _ in range(random.randint(1, 3))]
                    }
                    for role in ["leader", "facilitator", "contributor", "reviewer"]
                ]
            })

        if complexity == DataComplexity.STRESS:
            base_data.update({
                "interaction_patterns": [
                    {
                        "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                        "interactions": random.randint(10, 100) * self.config.size_multiplier,
                        "average_response_time": random.randint(1, 60),  # minutes
                        "sentiment_score": round(random.uniform(-1, 1), 2)
                    }
                    for i in range(90)  # 3 months of daily data
                ],
                "skill_matrix": {
                    "technical_skills": [f"skill_{i}" for i in range(20 * self.config.size_multiplier)],
                    "soft_skills": [f"skill_{i}" for i in range(15 * self.config.size_multiplier)],
                    "domain_expertise": [f"skill_{i}" for i in range(10 * self.config.size_multiplier)]
                }
            })

        return base_data

    def generate_response_data(self, assessment_data: Dict, user_data: Dict, complexity: DataComplexity = None) -> Dict:
        """Generate assessment response data"""
        complexity = complexity or self.config.complexity

        base_response = {
            "id": str(uuid.uuid4()),
            "assessment_id": assessment_data["id"],
            "user_id": user_data["id"],
            "status": random.choice(["in_progress", "completed", "abandoned"]),
            "started_at": self.fake.date_time_between(start_date="-30d", end_date="now"),
            "responses": []
        }

        if base_response["status"] == "completed":
            base_response["completed_at"] = self.fake.date_time_between(
                start_date=base_response["started_at"],
                end_date="now"
            )
            base_response["completion_time_seconds"] = random.randint(300, 3600)

        # Generate responses for each question
        if "questions" in assessment_data:
            for question in assessment_data["questions"]:
                response = self._generate_question_response(question, complexity)
                base_response["responses"].append(response)

        if complexity in [DataComplexity.COMPLEX, DataComplexity.STRESS]:
            base_response.update({
                "session_data": {
                    "user_agent": self.fake.user_agent(),
                    "ip_address": self.fake.ipv4(),
                    "device_type": random.choice(["desktop", "mobile", "tablet"]),
                    "browser": random.choice(["chrome", "firefox", "safari", "edge"]),
                    "screen_resolution": f"{random.choice([1920, 1366, 1440])}x{random.choice([1080, 768, 900])}",
                    "time_spent_per_question": [
                        random.randint(5, 120) for _ in range(len(base_response["responses"]))
                    ]
                },
                "behavioral_metrics": {
                    "answer_changes": random.randint(0, 10),
                    "time_suspended": random.randint(0, 300),
                    "window_focus_changes": random.randint(1, 20),
                    "copy_attempts": random.randint(0, 5),
                    "suspicious_activity_detected": random.choice([True, False])
                }
            })

        if complexity == DataComplexity.STRESS:
            base_response.update({
                "detailed_timing": [
                    {
                        "question_id": response["question_id"],
                        "first_viewed": self.fake.date_time_between(start_date="-1h", end_date="now"),
                        "last_modified": self.fake.date_time_between(start_date="-1h", end_date="now"),
                        "time_spent": random.randint(5, 300),
                        "interaction_events": [
                            {
                                "type": random.choice(["view", "click", "type", "scroll"]),
                                "timestamp": self.fake.date_time_between(start_date="-1h", end_date="now"),
                                "coordinates": {"x": random.randint(0, 1920), "y": random.randint(0, 1080)}
                            }
                            for _ in range(random.randint(1, 10))
                        ]
                    }
                    for response in base_response["responses"]
                ]
            })

        return base_response

    def _generate_question_response(self, question: Dict, complexity: DataComplexity) -> Dict:
        """Generate response for a single question"""
        base_response = {
            "question_id": question["id"],
            "response_type": question["type"],
            "created_at": self.fake.date_time_between(start_date="-1h", end_date="now")
        }

        if question["type"] == QuestionType.MULTIPLE_CHOICE:
            options = question.get("answer_options", [])
            if options:
                selected_option = random.choice(options)
                base_response["selected_option_id"] = selected_option["id"]
                base_response["selected_value"] = selected_option["value"]

        elif question["type"] in [QuestionType.LIKERT, QuestionType.SCALE]:
            options = question.get("answer_options", [])
            if options:
                # Bias towards middle values for more realistic data
                weights = [0.1, 0.2, 0.4, 0.2, 0.1] if len(options) == 5 else [0.2] * len(options)
                selected_option = random.choices(options, weights=weights[:len(options)])[0]
                base_response["selected_value"] = selected_option["value"]

        elif question["type"] == QuestionType.TEXT:
            if complexity == DataComplexity.MINIMAL:
                base_response["text_response"] = self.fake.sentence()
            elif complexity == DataComplexity.REALISTIC:
                base_response["text_response"] = self.fake.text(max_nb_chars=100)
            else:
                base_response["text_response"] = self.fake.text(max_nb_chars=500)

        elif question["type"] == QuestionType.BOOLEAN:
            base_response["boolean_response"] = random.choice([True, False])

        if complexity in [DataComplexity.COMPLEX, DataComplexity.STRESS]:
            base_response.update({
                "time_spent_seconds": random.randint(5, 300),
                "confidence_level": random.randint(1, 5),
                "attempts": random.randint(1, 3),
                "is_skipped": random.choice([True, False]) if question.get("required", True) else random.choice([True, False, False])
            })

        return base_response

    def generate_edge_case_data(self, data_type: str) -> Dict:
        """Generate data specifically designed to test edge cases"""

        if data_type == "user":
            return {
                "email": "",  # Empty email
                "full_name": "A" * 1000,  # Extremely long name
                "phone": "1" * 50,  # Invalid phone
                "role": "invalid_role",
                "created_at": "invalid_date",
                "is_active": "not_boolean"
            }

        elif data_type == "assessment":
            return {
                "title": "",  # Empty title
                "description": "X" * 10000,  # Extremely long description
                "estimated_duration_minutes": -1,  # Negative duration
                "category": "invalid_category",
                "status": "invalid_status",
                "questions": []  # No questions
            }

        elif data_type == "response":
            return {
                "assessment_id": "",  # Empty ID
                "user_id": "invalid-uuid",
                "responses": [
                    {
                        "question_id": "non-existent",
                        "selected_value": "invalid-value-type",
                        "text_response": None  # Should be string for text questions
                    }
                ]
            }

        else:
            return {"invalid": "data"}

    def generate_stress_dataset(self, data_type: str, size: int = 1000) -> List[Dict]:
        """Generate large datasets for stress testing"""

        if data_type == "users":
            return self.generate_user_data(DataComplexity.STRESS, count=size)

        elif data_type == "assessments":
            return self.generate_assessment_data(DataComplexity.STRESS, count=size)

        elif data_type == "teams":
            return self.generate_team_data(DataComplexity.STRESS, count=size)

        else:
            return [self.generate_edge_case_data(data_type) for _ in range(size)]


class DataQualityChecker:
    """Utility for checking quality of generated test data"""

    @staticmethod
    def validate_user_data(user_data: Dict) -> List[str]:
        """Validate user data and return list of issues"""
        issues = []

        if not user_data.get("email"):
            issues.append("Missing email")
        elif "@" not in user_data["email"]:
            issues.append("Invalid email format")

        if not user_data.get("full_name"):
            issues.append("Missing full name")
        elif len(user_data["full_name"]) < 2:
            issues.append("Full name too short")

        if user_data.get("role") not in [role.value for role in UserRole]:
            issues.append(f"Invalid role: {user_data.get('role')}")

        return issues

    @staticmethod
    def validate_assessment_data(assessment_data: Dict) -> List[str]:
        """Validate assessment data and return list of issues"""
        issues = []

        if not assessment_data.get("title"):
            issues.append("Missing title")

        if not assessment_data.get("questions"):
            issues.append("No questions in assessment")
        else:
            for i, question in enumerate(assessment_data["questions"]):
                if not question.get("text"):
                    issues.append(f"Question {i+1} missing text")
                if not question.get("type"):
                    issues.append(f"Question {i+1} missing type")

        return issues

    @staticmethod
    def check_data_diversity(data_list: List[Dict], field: str) -> Dict:
        """Check diversity of data in a specific field"""
        values = [item.get(field) for item in data_list if item.get(field)]

        if not values:
            return {"error": f"No values found for field {field}"}

        unique_values = set(values)
        total_values = len(values)

        return {
            "total_count": total_values,
            "unique_count": len(unique_values),
            "diversity_ratio": len(unique_values) / total_values,
            "most_common": max(set(values), key=values.count) if values else None,
            "least_common": min(set(values), key=values.count) if values else None
        }


# Example usage and convenience functions
def generate_complete_test_dataset(complexity: DataComplexity = DataComplexity.REALISTIC) -> Dict:
    """Generate a complete dataset with related entities"""
    generator = TestDataGenerator(DataGenerationConfig(complexity=complexity))

    # Generate organization
    organization = generator.generate_organization_data()

    # Generate teams in organization
    teams = generator.generate_team_data(complexity, count=random.randint(2, 5))

    # Generate users
    users = generator.generate_user_data(complexity, count=random.randint(5, 20))

    # Generate assessments
    assessments = generator.generate_assessment_data(complexity, count=random.randint(3, 8))

    # Generate responses
    responses = []
    for assessment in assessments:
        for user in users[:10]:  # Not all users take all assessments
            response = generator.generate_response_data(assessment, user, complexity)
            responses.append(response)

    return {
        "organization": organization,
        "teams": teams,
        "users": users,
        "assessments": assessments,
        "responses": responses,
        "metadata": {
            "complexity": complexity.value,
            "generated_at": datetime.utcnow().isoformat(),
            "total_entities": {
                "organizations": 1,
                "teams": len(teams),
                "users": len(users),
                "assessments": len(assessments),
                "responses": len(responses)
            }
        }
    }


def generate_performance_test_data() -> Dict:
    """Generate data specifically for performance testing"""
    config = DataGenerationConfig(
        complexity=DataComplexity.STRESS,
        seed=42,  # Reproducible data
        size_multiplier=10
    )

    generator = TestDataGenerator(config)

    return {
        "users": generator.generate_user_data(DataComplexity.STRESS, count=1000),
        "assessments": generator.generate_assessment_data(DataComplexity.STRESS, count=100),
        "teams": generator.generate_team_data(DataComplexity.STRESS, count=50),
        "responses": []
    }


if __name__ == "__main__":
    # Example usage
    generator = TestDataGenerator()

    # Generate sample data
    sample_user = generator.generate_user_data()
    sample_assessment = generator.generate_assessment_data()
    sample_response = generator.generate_response_data(sample_assessment, sample_user)

    print("Sample User:", json.dumps(sample_user, indent=2, default=str))
    print("Sample Assessment:", json.dumps(sample_assessment, indent=2, default=str))
    print("Sample Response:", json.dumps(sample_response, indent=2, default=str))
