# app/api/v1/endpoints/assessment_results.py

"""
Comprehensive Assessment Results API

This module provides a unified API for storing and retrieving assessment results
across all assessment types including MBTI, Big Five, DISC, Enneagram, and custom assessments.

Features:
- Universal assessment result storage
- Multi-framework support (MBTI, Big Five, DISC, Enneagram, Custom)
- Result history and analytics
- User-specific result retrieval
- Assessment performance tracking
"""

from typing import Dict, Any, List, Optional

from app.middleware.rate_limiter import check_rate_limit
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import json
import uuid

from app.core.database import get_async_db
from app.api.deps import get_current_active_user
from app.db.models.user import User

router = APIRouter(tags=["assessment-results"])

# ==================== IN-MEMORY STORAGE ====================
# In production, this would be replaced with database storage

class AssessmentResultStorage:
    """In-memory storage for assessment results (development)"""

    _results = []
    _user_results = {}  # user_id -> [result_ids]

    @classmethod
    def store_result(cls, result_data: dict) -> dict:
        """Store assessment result and return stored data with ID"""
        result_id = len(cls._results) + 1
        user_id = result_data.get("user_id", "anonymous")

        result = {
            "id": result_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **result_data
        }

        cls._results.append(result)

        # Track user results
        if user_id not in cls._user_results:
            cls._user_results[user_id] = []
        cls._user_results[user_id].append(result_id)

        return result

    @classmethod
    def get_user_results(cls, user_id: str, assessment_type: str = None, limit: int = 50) -> List[dict]:
        """Get user's assessment results"""
        user_result_ids = cls._user_results.get(user_id, [])
        results = [r for r in cls._results if r["id"] in user_result_ids]

        if assessment_type:
            results = [r for r in results if r.get("assessment_type") == assessment_type]

        # Sort by created_at descending and limit
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results[:limit]

    @classmethod
    def get_result(cls, result_id: int) -> Optional[dict]:
        """Get specific result by ID"""
        return next((r for r in cls._results if r["id"] == result_id), None)

    @classmethod
    def update_result(cls, result_id: int, update_data: dict) -> Optional[dict]:
        """Update assessment result"""
        for i, result in enumerate(cls._results):
            if result["id"] == result_id:
                cls._results[i].update(update_data)
                cls._results[i]["updated_at"] = datetime.utcnow().isoformat()
                return cls._results[i]
        return None

    @classmethod
    def delete_result(cls, result_id: int) -> bool:
        """Delete assessment result"""
        for i, result in enumerate(cls._results):
            if result["id"] == result_id:
                user_id = result.get("user_id")
                cls._results.pop(i)

                # Remove from user tracking
                if user_id and user_id in cls._user_results:
                    cls._user_results[user_id] = [
                        rid for rid in cls._user_results[user_id] if rid != result_id
                    ]
                return True
        return False

    @classmethod
    def get_analytics(cls, user_id: str = None, assessment_type: str = None) -> dict:
        """Get analytics for assessment results"""
        results = cls._results

        if user_id:
            user_result_ids = cls._user_results.get(user_id, [])
            results = [r for r in results if r["id"] in user_result_ids]

        if assessment_type:
            results = [r for r in results if r.get("assessment_type") == assessment_type]

        # Calculate analytics
        total_results = len(results)
        assessment_types = {}
        completion_trend = {}

        for result in results:
            # Count by assessment type
            atype = result.get("assessment_type", "unknown")
            assessment_types[atype] = assessment_types.get(atype, 0) + 1

            # Count by date
            date = result["created_at"][:10]  # YYYY-MM-DD
            completion_trend[date] = completion_trend.get(date, 0) + 1

        return {
            "total_assessments": total_results,
            "assessment_types": assessment_types,
            "completion_trend": completion_trend,
            "latest_completion": results[0]["created_at"] if results else None
        }

# ==================== PYDANTIC MODELS ====================

class AssessmentResultCreate(BaseModel):
    """Schema for creating assessment results"""
    assessment_type: str
    assessment_id: Optional[str] = None
    responses: Dict[str, Any] = {}
    raw_type: Optional[str] = None
    processed_result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}

class AssessmentResultUpdate(BaseModel):
    """Schema for updating assessment results"""
    processed_result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

# ==================== ASSESSMENT PROCESSING ====================

async def process_assessment_result(assessment_data: dict) -> dict:
    """Process assessment data based on type"""
    assessment_type = assessment_data.get("assessment_type", "unknown")

    processors = {
        "mbti": process_mbti_result,
        "big_five": process_big_five_result,
        "disc": process_disc_result,
        "enneagram": process_enneagram_result,
    }

    processor = processors.get(assessment_type, process_generic_result)
    return await processor(assessment_data)

async def process_mbti_result(assessment_data: dict) -> dict:
    """Process MBTI assessment results"""
    responses = assessment_data.get("responses", {})
    raw_type = assessment_data.get("raw_type", "ENTJ")

    # MBTI scoring logic
    dimensions = {
        'E-I': {'E': 0, 'I': 0},
        'S-N': {'S': 0, 'N': 0},
        'T-F': {'T': 0, 'F': 0},
        'J-P': {'J': 0, 'P': 0}
    }

    # Count responses
    for question_id, answer in responses.items():
        if answer in dimensions.get('E-I', {}):
            dimensions['E-I'][answer] += 1
        elif answer in dimensions.get('S-N', {}):
            dimensions['S-N'][answer] += 1
        elif answer in dimensions.get('T-F', {}):
            dimensions['T-F'][answer] += 1
        elif answer in dimensions.get('J-P', {}):
            dimensions['J-P'][answer] += 1

    # Calculate MBTI type
    calculated_type = ''.join([
        'E' if dimensions['E-I']['E'] > dimensions['E-I']['I'] else 'I',
        'S' if dimensions['S-N']['S'] > dimensions['S-N']['N'] else 'N',
        'T' if dimensions['T-F']['T'] > dimensions['T-F']['F'] else 'F',
        'J' if dimensions['J-P']['J'] > dimensions['J-P']['P'] else 'P'
    ])

    final_type = raw_type or calculated_type

    # MBTI descriptions
    mbti_descriptions = {
        "INTJ": "The Architect - Imaginative and strategic thinkers",
        "INTP": "The Thinker - Innovative inventors with unquenchable thirst for knowledge",
        "ENTJ": "The Commander - Bold, imaginative and strong-willed leaders",
        "ENTP": "The Debater - Smart and curious thinkers who love intellectual challenges",
        "INFJ": "The Advocate - Quiet and mystical, yet very inspiring idealists",
        "INFP": "The Mediator - Poetic, kind and altruistic people",
        "ENFJ": "The Protagonist - Charismatic and inspiring leaders",
        "ENFP": "The Campaigner - Enthusiastic, creative and sociable free spirits",
        "ISTJ": "The Logistician - Practical and fact-oriented individuals",
        "ISFJ": "The Defender - Very dedicated and warm protectors",
        "ESTJ": "The Executive - Excellent administrators, unsurpassed at managing",
        "ESFJ": "The Consul - Extraordinarily caring, social and popular people",
        "ISTP": "The Virtuoso - Bold and practical experimenters",
        "ISFP": "The Adventurer - Flexible and charming artists",
        "ESTP": "The Entrepreneur - Smart, energetic and perceptive people",
        "ESFP": "The Entertainer - Spontaneous, energetic and enthusiastic entertainers"
    }

    return {
        "type": final_type,
        "confidence": 0.85,
        "description": mbti_descriptions.get(final_type, f"Your MBTI type is {final_type}"),
        "dimensions": {
            "extraversion": 0.7 if final_type[0] == 'E' else 0.3,
            "intuition": 0.7 if final_type[1] == 'N' else 0.3,
            "thinking": 0.7 if final_type[2] == 'T' else 0.3,
            "judging": 0.7 if final_type[3] == 'J' else 0.3
        },
        "assessment_type": "mbti"
    }

async def process_big_five_result(assessment_data: dict) -> dict:
    """Process Big Five assessment results"""
    return {
        "type": "big_five",
        "traits": {
            "openness": 0.75,
            "conscientiousness": 0.82,
            "extraversion": 0.65,
            "agreeableness": 0.88,
            "neuroticism": 0.35
        },
        "personality_profile": "Conscientious and agreeable with creative tendencies",
        "confidence": 0.87,
        "description": "You show high levels of conscientiousness and agreeableness",
        "assessment_type": "big_five"
    }

async def process_disc_result(assessment_data: dict) -> dict:
    """Process DISC assessment results"""
    raw_type = assessment_data.get("raw_type", "D")

    disc_profiles = {
        "D": "Dominance - Direct, decisive, strong-willed leaders",
        "I": "Influence - Optimistic, outgoing, social influencers",
        "S": "Steadiness - Calm, patient, reliable supporters",
        "C": "Conscientiousness - Analytical, precise, detail-oriented"
    }

    return {
        "type": "disc",
        "primary_style": raw_type,
        "description": disc_profiles.get(raw_type, "Mixed behavioral style"),
        "confidence": 0.82,
        "dimensions": {
            "dominance": 0.85 if raw_type == "D" else 0.45,
            "influence": 0.85 if raw_type == "I" else 0.45,
            "steadiness": 0.85 if raw_type == "S" else 0.45,
            "conscientiousness": 0.85 if raw_type == "C" else 0.45
        },
        "assessment_type": "disc"
    }

async def process_enneagram_result(assessment_data: dict) -> dict:
    """Process Enneagram assessment results"""
    raw_type = assessment_data.get("raw_type", "Type 1")

    enneagram_descriptions = {
        "Type 1": "The Reformer - Rational, idealistic, principled perfectionists",
        "Type 2": "The Helper - Caring, interpersonal, generous givers",
        "Type 3": "The Achiever - Success-oriented, pragmatic, adaptive achievers",
        "Type 4": "The Individualist - Sensitive, introspective, expressive artists",
        "Type 5": "The Investigator - Innovative, perceptive, knowledge seekers",
        "Type 6": "The Loyalist - Engaging, responsible, anxious loyalists",
        "Type 7": "The Enthusiast - Spontaneous, versatile, multi-talented optimists",
        "Type 8": "The Challenger - Self-confident, decisive, controlling protectors",
        "Type 9": "The Peacemaker - Receptive, reassuring, complacent mediators"
    }

    return {
        "type": "enneagram",
        "number": raw_type,
        "description": enneagram_descriptions.get(raw_type, f"Enneagram {raw_type}"),
        "confidence": 0.84,
        "wings": [f"{raw_type}Wing 2", f"{raw_type}Wing 9"] if raw_type == "Type 1" else ["Developing"],
        "assessment_type": "enneagram"
    }

async def process_generic_result(assessment_data: dict) -> dict:
    """Process generic/custom assessment results"""
    return {
        "type": "custom",
        "score": assessment_data.get("score", 0.8),
        "description": assessment_data.get("description", "Custom assessment completed"),
        "confidence": 0.75,
        "responses_count": len(assessment_data.get("responses", {})),
        "assessment_type": "custom"
    }

# ==================== API ENDPOINTS ====================


@check_rate_limit(identifier="public", endpoint_type="public")
@router.post("/assessment-results-test", status_code=status.HTTP_201_CREATED)
async def create_assessment_result_test(result_data: AssessmentResultCreate):
    """
    Test endpoint for assessment results (no authentication required)
    For development and integration testing only
    """
    try:
        # Add test user info
        result_dict = result_data.dict()
        result_dict["user_id"] = "test-user"

        # Process the assessment results
        processed_result = await process_assessment_result(result_dict)
        result_dict["processed_result"] = processed_result

        # Store the result
        stored_result = AssessmentResultStorage.store_result(result_dict)

        return {
            "success": True,
            "result_id": stored_result["id"],
            "assessment_type": result_dict["assessment_type"],
            "results": processed_result,
            "created_at": stored_result["created_at"],
            "message": f"{result_dict['assessment_type'].title()} assessment results stored successfully (TEST MODE)"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            de
@check_rate_limit(identifier="public", endpoint_type="public")
tail=f"Failed to store assessment results: {str(e)}"
        )

@router.get("/assessment-results-test")
async def get_assessment_results_test(
    assessment_type: Optional[str] = Query(None, description="Filter by assessment type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """
    Test endpoint for getting assessment results (no authentication required)
    For development and integration testing only
    """
    try:
        user_id = "test-user"
        results = AssessmentResultStorage.get_user_results(
            user_id=user_id,
            assessment_type=assessment_type,
            limit=limit
        )

        # Format results for frontend consumption
        formatted_results = []
        for result in results:
            processed_data = result.get("processed_result", {})
            processed_data.update({
                "result_id": result["id"],
                "assessment_type": result["assessment_type"],
                "assessment_id": result.get("assessment_id"),
                "completed_at": result["created_at"],
                "responses_count": len(result.get("responses", {})),
                "updated_at": result["updated_at"]
            })
            formatted_results.append(processed_data)

        return {
            "success": True,
            "count": len(formatted_results),
            "results": formatted_results,
            "user_id": user_id,
            "filters": {
                "assessment_type": assessment_type,
                "limit": limit
            },
            "test_mode": True
        }

    except Exception as e:
        rai
@check_rate_limit(identifier="public", endpoint_type="public")
se HTTPException(
            status_code=500,
            detail=f"Failed to retrieve assessment results: {str(e)}"
        )

@router.get("/assessment-questions/mbti")
async def get_mbti_assessment_questions():
    """
    Get MBTI assessment questions from backend

    Returns a complete MBTI assessment with 8 questions
    covering all 4 personality dimensions (E-I, S-N, T-F, J-P)
    """
    try:
        mbti_assessment = {
            "id": "mbti-standard",
            "title": "Myers-Briggs Type Indicator (MBTI) Assessment",
            "description": "Discover your personality type based on the four MBTI dimensions. This assessment will help you understand your preferences in how you perceive the world and make decisions.",
            "instructions": "For each question, choose the option that feels most natural to you in most situations. There are no right or wrong answers.",
            "estimated_time": "45-60 minutes",
            "questions": [

                {
                    "id": 1,
                    "question_text": "At parties, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Talk to many people, including strangers", "value": "E"},
                        {"text": "Talk to a few people you know well", "value": "I"}
                    ]
                },

                {
                    "id": 2,
                    "question_text": "After a long week, do you prefer to:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Go out with friends to socialize", "value": "E"},
                        {"text": "Stay home with a book or movie", "value": "I"}
                    ]
                },

                {
                    "id": 3,
                    "question_text": "When solving a problem, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Talk it through with others", "value": "E"},
                        {"text": "Think it through by yourself", "value": "I"}
                    ]
                },

                {
                    "id": 4,
                    "question_text": "In meetings, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Speak up and participate actively", "value": "E"},
                        {"text": "Listen and process before speaking", "value": "I"}
                    ]
                },

                {
                    "id": 5,
                    "question_text": "At work, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Enjoy working in teams and brainstorming with others", "value": "E"},
                        {"text": "Prefer working independently and concentrating deeply", "value": "I"}
                    ]
                },

                {
                    "id": 6,
                    "question_text": "When you're stressed, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Seek out people to talk to", "value": "E"},
                        {"text": "Need quiet time alone to recharge", "value": "I"}
                    ]
                },

                {
                    "id": 7,
                    "question_text": "In a new city, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Make friends and explore social scene", "value": "E"},
                        {"text": "Explore museums and parks alone", "value": "I"}
                    ]
                },

                {
                    "id": 8,
                    "question_text": "Do you get your energy from:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Being around people and activities", "value": "E"},
                        {"text": "Quiet reflection and solitude", "value": "I"}
                    ]
                },

                {
                    "id": 9,
                    "question_text": "When making decisions, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Seek input from others first", "value": "E"},
                        {"text": "Think it through privately first", "value": "I"}
                    ]
                },

                {
                    "id": 10,
                    "question_text": "In group projects, do you prefer:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Leading discussions and collaboration", "value": "E"},
                        {"text": "Working independently on your portion", "value": "I"}
                    ]
                },

                {
                    "id": 11,
                    "question_text": "When learning, do you prefer:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Group discussions and study sessions", "value": "E"},
                        {"text": "Individual research and reading", "value": "I"}
                    ]
                },

                {
                    "id": 12,
                    "question_text": "At social gatherings, do you typically:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Circulate and meet many people", "value": "E"},
                        {"text": "Find a few people for deep conversation", "value": "I"}
                    ]
                },

                {
                    "id": 13,
                    "question_text": "When traveling, do you prefer:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Group tours and shared experiences", "value": "E"},
                        {"text": "Solo exploration and reflection", "value": "I"}
                    ]
                },

                {
                    "id": 14,
                    "question_text": "When faced with a challenge, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Brainstorm with others", "value": "E"},
                        {"text": "Research and analyze alone", "value": "I"}
                    ]
                },

                {
                    "id": 15,
                    "question_text": "Do you prefer work environments that are:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Collaborative and interactive", "value": "E"},
                        {"text": "Quiet and focused", "value": "I"}
                    ]
                },

                {
                    "id": 16,
                    "question_text": "When celebrating achievements, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Share news with many people", "value": "E"},
                        {"text": "Celebrate privately with close friends", "value": "I"}
                    ]
                },

                {
                    "id": 17,
                    "question_text": "In conversations, do you tend to:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Think out loud", "value": "E"},
                        {"text": "Process internally before speaking", "value": "I"}
                    ]
                },

                {
                    "id": 18,
                    "question_text": "When networking, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Approach strangers easily", "value": "E"},
                        {"text": "Prefer introductions through others", "value": "I"}
                    ]
                },

                {
                    "id": 19,
                    "question_text": "In brainstorming sessions, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Build on others' ideas immediately", "value": "E"},
                        {"text": "Reflect before contributing", "value": "I"}
                    ]
                },

                {
                    "id": 20,
                    "question_text": "When dining out, do you prefer:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Lively restaurants with ambiance", "value": "E"},
                        {"text": "Quiet, intimate settings", "value": "I"}
                    ]
                },

                {
                    "id": 21,
                    "question_text": "Do you consider yourself more:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Outgoing and expressive", "value": "E"},
                        {"text": "Reserved and thoughtful", "value": "I"}
                    ]
                },

                {
                    "id": 22,
                    "question_text": "In team sports, do you prefer:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Collaborative team play", "value": "E"},
                        {"text": "Individual performance roles", "value": "I"}
                    ]
                },

                {
                    "id": 23,
                    "question_text": "When giving presentations, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Engage with the audience", "value": "E"},
                        {"text": "Focus on the content", "value": "I"}
                    ]
                },

                {
                    "id": 24,
                    "question_text": "In casual conversations, do you:",
                    "dimension": "E-I",
                    "options": [
                        {"text": "Initiate discussions with strangers", "value": "E"},
                        {"text": "Wait for others to approach", "value": "I"}
                    ]
                },

                {
                    "id": 25,
                    "question_text": "Do you prefer to:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Focus on the real world and practical matters", "value": "S"},
                        {"text": "Imagine possibilities and think about abstract concepts", "value": "N"}
                    ]
                },

                {
                    "id": 26,
                    "question_text": "When learning something new, do you:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Prefer step-by-step instructions with concrete examples", "value": "S"},
                        {"text": "Like to understand the overall concept first", "value": "N"}
                    ]
                },

                {
                    "id": 27,
                    "question_text": "When reading, do you prefer:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Factual information and practical guides", "value": "S"},
                        {"text": "Theoretical concepts and symbolic meanings", "value": "N"}
                    ]
                },

                {
                    "id": 28,
                    "question_text": "At work, do you focus more on:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "What is actual and present", "value": "S"},
                        {"text": "What could be possible", "value": "N"}
                    ]
                },

                {
                    "id": 29,
                    "question_text": "When someone explains something, do you prefer:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Specific details and step-by-step process", "value": "S"},
                        {"text": "The big picture and underlying principles", "value": "N"}
                    ]
                },

                {
                    "id": 30,
                    "question_text": "Do you trust more:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Past experience and concrete data", "value": "S"},
                        {"text": "Your intuition and future possibilities", "value": "N"}
                    ]
                },

                {
                    "id": 31,
                    "question_text": "When making a purchase, do you focus on:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Practical features and proven reliability", "value": "S"},
                        {"text": "How it could enhance your future lifestyle", "value": "N"}
                    ]
                },

                {
                    "id": 32,
                    "question_text": "In problem-solving, do you:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Use proven methods and facts", "value": "S"},
                        {"text": "Explore innovative approaches", "value": "N"}
                    ]
                },

                {
                    "id": 33,
                    "question_text": "When planning, do you focus on:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Realistic, immediate needs", "value": "S"},
                        {"text": "Long-term possibilities", "value": "N"}
                    ]
                },

                {
                    "id": 34,
                    "question_text": "Do you prefer information that is:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Concrete and specific", "value": "S"},
                        {"text": "Abstract and conceptual", "value": "N"}
                    ]
                },

                {
                    "id": 35,
                    "question_text": "When analyzing situations, do you:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Focus on what actually happened", "value": "S"},
                        {"text": "Consider what might have been", "value": "N"}
                    ]
                },

                {
                    "id": 36,
                    "question_text": "In presentations, do you prefer:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Data, facts, and examples", "value": "S"},
                        {"text": "Concepts and future possibilities", "value": "N"}
                    ]
                },

                {
                    "id": 37,
                    "question_text": "When giving feedback, do you:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Provide specific, observable examples", "value": "S"},
                        {"text": "Discuss potential and possibilities", "value": "N"}
                    ]
                },

                {
                    "id": 38,
                    "question_text": "Do you notice more:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Specific details and facts", "value": "S"},
                        {"text": "Patterns and connections", "value": "N"}
                    ]
                },

                {
                    "id": 39,
                    "question_text": "When making career choices, do you consider:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Practical benefits and stability", "value": "S"},
                        {"text": "Growth potential and meaning", "value": "N"}
                    ]
                },

                {
                    "id": 40,
                    "question_text": "In relationships, do you value:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Shared experiences and realities", "value": "S"},
                        {"text": "Intellectual and emotional connections", "value": "N"}
                    ]
                },

                {
                    "id": 41,
                    "question_text": "When facing uncertainty, do you:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Seek concrete information", "value": "S"},
                        {"text": "Trust your intuition", "value": "N"}
                    ]
                },

                {
                    "id": 42,
                    "question_text": "Do you prefer art that is:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Realistic and representational", "value": "S"},
                        {"text": "Abstract and symbolic", "value": "N"}
                    ]
                },

                {
                    "id": 43,
                    "question_text": "When learning history, do you prefer:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Specific dates, events, and facts", "value": "S"},
                        {"text": "Themes, patterns, and meanings", "value": "N"}
                    ]
                },

                {
                    "id": 44,
                    "question_text": "In debates, do you focus on:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Factual accuracy and evidence", "value": "S"},
                        {"text": "Conceptual validity and possibilities", "value": "N"}
                    ]
                },

                {
                    "id": 45,
                    "question_text": "When traveling, do you prefer:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Detailed itineraries with specific activities", "value": "S"},
                        {"text": "Flexible plans that allow for discovery", "value": "N"}
                    ]
                },

                {
                    "id": 46,
                    "question_text": "When solving puzzles, do you prefer:",
                    "dimension": "S-N",
                    "options": [
                        {"text": "Logic-based challenges", "value": "S"},
                        {"text": "Creative problem-solving", "value": "N"}
                    ]
                },

                {
                    "id": 47,
                    "question_text": "When making decisions, do you:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Rely on logic and objective analysis", "value": "T"},
                        {"text": "Consider how it will affect people involved", "value": "F"}
                    ]
                },

                {
                    "id": 48,
                    "question_text": "When giving feedback, do you:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Focus on facts and logical improvements", "value": "T"},
                        {"text": "Consider feelings and how to deliver it gently", "value": "F"}
                    ]
                },

                {
                    "id": 49,
                    "question_text": "In a disagreement, do you focus more on:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Finding the logical truth", "value": "T"},
                        {"text": "Maintaining harmony in relationships", "value": "F"}
                    ]
                },

                {
                    "id": 50,
                    "question_text": "When evaluating a job offer, do you prioritize:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Objective criteria like salary and advancement", "value": "T"},
                        {"text": "Company culture and your gut feeling", "value": "F"}
                    ]
                },

                {
                    "id": 51,
                    "question_text": "Do you make decisions based on:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Universal principles and fairness", "value": "T"},
                        {"text": "Individual circumstances and relationships", "value": "F"}
                    ]
                },

                {
                    "id": 52,
                    "question_text": "When someone asks for advice, do you:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Give direct, analytical solutions", "value": "T"},
                        {"text": "Offer emotional support and understanding", "value": "F"}
                    ]
                },

                {
                    "id": 53,
                    "question_text": "In group discussions, do you value more:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Logical analysis and objective truth", "value": "T"},
                        {"text": "Consensus and everyone's feelings", "value": "F"}
                    ]
                },

                {
                    "id": 54,
                    "question_text": "Do you admire people more for being:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Consistently logical and fair", "value": "T"},
                        {"text": "Compassionate and understanding", "value": "F"}
                    ]
                },

                {
                    "id": 55,
                    "question_text": "When mediating conflicts, do you:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Focus on finding the logical solution", "value": "T"},
                        {"text": "Consider everyone's emotional needs", "value": "F"}
                    ]
                },

                {
                    "id": 56,
                    "question_text": "In hiring decisions, do you prioritize:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Skills and qualifications", "value": "T"},
                        {"text": "Cultural fit and personality", "value": "F"}
                    ]
                },

                {
                    "id": 57,
                    "question_text": "When setting goals, do you focus on:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Achievement and success metrics", "value": "T"},
                        {"text": "Personal growth and fulfillment", "value": "F"}
                    ]
                },

                {
                    "id": 58,
                    "question_text": "Do you believe justice should be:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Consistent and impartial", "value": "T"},
                        {"text": "Compassionate and contextual", "value": "F"}
                    ]
                },

                {
                    "id": 59,
                    "question_text": "When evaluating arguments, do you look for:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Logical consistency and evidence", "value": "T"},
                        {"text": "Emotional authenticity and sincerity", "value": "F"}
                    ]
                },

                {
                    "id": 60,
                    "question_text": "In leadership, do you prioritize:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Efficiency and results", "value": "T"},
                        {"text": "Team morale and satisfaction", "value": "F"}
                    ]
                },

                {
                    "id": 61,
                    "question_text": "When giving compliments, do you:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Acknowledge specific achievements", "value": "T"},
                        {"text": "Express appreciation for character", "value": "F"}
                    ]
                },

                {
                    "id": 62,
                    "question_text": "Do you prefer to solve problems by:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Analyzing the system", "value": "T"},
                        {"text": "Understanding the people involved", "value": "F"}
                    ]
                },

                {
                    "id": 63,
                    "question_text": "In ethical dilemmas, do you follow:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Universal moral principles", "value": "T"},
                        {"text": "The impact on relationships", "value": "F"}
                    ]
                },

                {
                    "id": 64,
                    "question_text": "When receiving criticism, do you:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Analyze the logic and validity", "value": "T"},
                        {"text": "Consider the person's intentions", "value": "F"}
                    ]
                },

                {
                    "id": 65,
                    "question_text": "Do you value truth more when it's:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Objective and verifiable", "value": "T"},
                        {"text": "Emotionally resonant and meaningful", "value": "F"}
                    ]
                },

                {
                    "id": 66,
                    "question_text": "In time management, do you prioritize:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Maximum efficiency", "value": "T"},
                        {"text": "Maintaining relationships", "value": "F"}
                    ]
                },

                {
                    "id": 67,
                    "question_text": "When making rules, do you focus on:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Consistency and fairness", "value": "T"},
                        {"text": "Flexibility and compassion", "value": "F"}
                    ]
                },

                {
                    "id": 68,
                    "question_text": "Do you believe decisions should be based on:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "Cost-benefit analysis", "value": "T"},
                        {"text": "Human impact assessment", "value": "F"}
                    ]
                },

                {
                    "id": 69,
                    "question_text": "In negotiations, do you aim for:",
                    "dimension": "T-F",
                    "options": [
                        {"text": "The most logical agreement", "value": "T"},
                        {"text": "A relationship-preserving outcome", "value": "F"}
                    ]
                },

                {
                    "id": 70,
                    "question_text": "Do you prefer to:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Plan things in advance and stick to the plan", "value": "J"},
                        {"text": "Be spontaneous and adapt to new situations", "value": "P"}
                    ]
                },

                {
                    "id": 71,
                    "question_text": "For weekends, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Plan activities and have a schedule", "value": "J"},
                        {"text": "Leave options open and decide spontaneously", "value": "P"}
                    ]
                },

                {
                    "id": 72,
                    "question_text": "When starting a project, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Create a detailed plan first", "value": "J"},
                        {"text": "Start and figure it out as you go", "value": "P"}
                    ]
                },

                {
                    "id": 73,
                    "question_text": "How do you feel about deadlines?",
                    "dimension": "J-P",
                    "options": [
                        {"text": "They help me stay organized and focused", "value": "J"},
                        {"text": "They feel restrictive and I work best when flexible", "value": "P"}
                    ]
                },

                {
                    "id": 74,
                    "question_text": "When traveling, do you prefer to:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Have a detailed itinerary", "value": "J"},
                        {"text": "Explore freely and be spontaneous", "value": "P"}
                    ]
                },

                {
                    "id": 75,
                    "question_text": "Do you prefer your work environment to be:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Structured and predictable", "value": "J"},
                        {"text": "Flexible and adaptable", "value": "P"}
                    ]
                },

                {
                    "id": 76,
                    "question_text": "When making decisions, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Make quick decisions to move forward", "value": "J"},
                        {"text": "Keep options open as long as possible", "value": "P"}
                    ]
                },

                {
                    "id": 77,
                    "question_text": "In managing tasks, do you prefer:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Completing one thing at a time", "value": "J"},
                        {"text": "Juggling multiple projects", "value": "P"}
                    ]
                },

                {
                    "id": 78,
                    "question_text": "When shopping, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Make lists and stick to them", "value": "J"},
                        {"text": "Browse and discover new options", "value": "P"}
                    ]
                },

                {
                    "id": 79,
                    "question_text": "Do you prefer your living space to be:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Organized and tidy", "value": "J"},
                        {"text": "Comfortable and lived-in", "value": "P"}
                    ]
                },

                {
                    "id": 80,
                    "question_text": "When approaching problems, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Follow established procedures", "value": "J"},
                        {"text": "Try various approaches", "value": "P"}
                    ]
                },

                {
                    "id": 81,
                    "question_text": "In conversations, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Drive toward conclusions", "value": "J"},
                        {"text": "Explore possibilities and tangents", "value": "P"}
                    ]
                },

                {
                    "id": 82,
                    "question_text": "When setting boundaries, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Establish clear rules", "value": "J"},
                        {"text": "Keep options flexible", "value": "P"}
                    ]
                },

                {
                    "id": 83,
                    "question_text": "Do you prefer to finish projects:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Before starting new ones", "value": "J"},
                        {"text": "Even as new ideas emerge", "value": "P"}
                    ]
                },

                {
                    "id": 84,
                    "question_text": "When managing time, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Stick to schedules religiously", "value": "J"},
                        {"text": "Adapt to changing priorities", "value": "P"}
                    ]
                },

                {
                    "id": 85,
                    "question_text": "In relationships, do you prefer:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Clear definitions and expectations", "value": "J"},
                        {"text": "Spontaneous development", "value": "P"}
                    ]
                },

                {
                    "id": 86,
                    "question_text": "When learning, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Follow structured curricula", "value": "J"},
                        {"text": "Explore topics as they interest you", "value": "P"}
                    ]
                },

                {
                    "id": 87,
                    "question_text": "Do you approach life with:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "A clear plan and direction", "value": "J"},
                        {"text": "Openness to unexpected opportunities", "value": "P"}
                    ]
                },

                {
                    "id": 88,
                    "question_text": "In social planning, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Organize events in advance", "value": "J"},
                        {"text": "Spontaneously get together", "value": "P"}
                    ]
                },

                {
                    "id": 89,
                    "question_text": "When working on creative projects, do you:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Work toward a defined outcome", "value": "J"},
                        {"text": "Follow inspiration wherever it leads", "value": "P"}
                    ]
                },

                {
                    "id": 90,
                    "question_text": "Do you prefer endings that are:",
                    "dimension": "J-P",
                    "options": [
                        {"text": "Clear and definitive", "value": "J"},
                        {"text": "Open to continuation", "value": "P"}
                    ]
                }
            ],
            "dimensions_info": {
                "E-I": {
                    "name": "Extraversion vs Introversion",
                    "description": "How you direct and receive energy"
                },
                "S-N": {
                    "name": "Sensing vs Intuition",
                    "description": "How you take in information"
                },
                "T-F": {
                    "name": "Thinking vs Feeling",
                    "description": "How you make decisions and conclusions"
                },
                "J-P": {
                    "name": "Judging vs Perceiving",
                    "description": "How you approach the outside world"
                }
            },
            "scoring_method": "MBTI questions are scored by counting preferences across each dimension. Your type is determined by your dominant preference in each of the four dimensions."
        }

        return {
            "success": True,
            "assessment": mbti_assessment,
            "message": "MBTI assessment questions loaded successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load MBTI assessment questions: {str(e)}"
        )

@router.get("/assessment-questions/enneagram")
async def get_enneagram_assessment_questions():
    """
    Get Enneagram assessment questions from backend

    Returns a complete Enneagram assessment with 9 questions
    covering all 9 personality types based on core motivations and fears
    """
    try:
        enneagram_assessment = {
            "id": "enneagram-standard",
            "title": "Enneagram Personality Assessment",
            "description": "Discover your Enneagram type based on core motivations and fears. This assessment will help you understand your personality patterns, growth opportunities, and how you relate to others.",
            "instructions": "For each question, choose the option that feels most true to you most of the time. There are no right or wrong answers - only what feels authentic to you.",
            "estimated_time": "45-60 minutes",
            "questions": [
                {
                    "id": 1,
                    "question_text": "What motivates you most in life?",
                    "type": "Motivation",
                    "options": [
                        {"text": "Being good and doing what's right", "value": "type1"},
                        {"text": "Being loved and needed by others", "value": "type2"},
                        {"text": "Being successful and valuable", "value": "type3"},
                        {"text": "Being unique and understood", "value": "type4"},
                        {"text": "Being competent and knowledgeable", "value": "type5"},
                        {"text": "Being safe and supported", "value": "type6"},
                        {"text": "Being happy and satisfied", "value": "type7"},
                        {"text": "Being strong and in control", "value": "type8"},
                        {"text": "Being at peace and comfortable", "value": "type9"}
                    ]
                },
                {
                    "id": 2,
                    "question_text": "In your ideal life, you would be known for:",
                    "type": "Legacy",
                    "options": [
                        {"text": "Your integrity and high standards", "value": "type1"},
                        {"text": "Your compassion and generosity", "value": "type2"},
                        {"text": "Your achievements and success", "value": "type3"},
                        {"text": "Your unique creativity and depth", "value": "type4"},
                        {"text": "Your wisdom and understanding", "value": "type5"},
                        {"text": "Your loyalty and courage", "value": "type6"},
                        {"text": "Your joy and enthusiasm", "value": "type7"},
                        {"text": "Your strength and decisiveness", "value": "type8"},
                        {"text": "Your peaceful and accepting nature", "value": "type9"}
                    ]
                },
                {
                    "id": 3,
                    "question_text": "What drives you to get out of bed in the morning?",
                    "type": "Daily Purpose",
                    "options": [
                        {"text": "The chance to improve things and do them right", "value": "type1"},
                        {"text": "Opportunities to help and connect with others", "value": "type2"},
                        {"text": "Goals to achieve and success to pursue", "value": "type3"},
                        {"text": "The possibility of deep, meaningful experiences", "value": "type4"},
                        {"text": "New things to learn and understand", "value": "type5"},
                        {"text": "Responsibilities to fulfill and people to protect", "value": "type6"},
                        {"text": "New adventures and exciting possibilities", "value": "type7"},
                        {"text": "Challenges to overcome and control to maintain", "value": "type8"},
                        {"text": "The comfort of routine and peaceful existence", "value": "type9"}
                    ]
                },

                # Core Fears (3 questions)
                {
                    "id": 4,
                    "question_text": "What's your greatest fear?",
                    "type": "Core Fear",
                    "options": [
                        {"text": "Being corrupt or evil", "value": "type1"},
                        {"text": "Being unwanted or unworthy", "value": "type2"},
                        {"text": "Being worthless or a failure", "value": "type3"},
                        {"text": "Being without identity or significance", "value": "type4"},
                        {"text": "Being helpless or useless", "value": "type5"},
                        {"text": "Being without support or guidance", "value": "type6"},
                        {"text": "Being trapped in pain or deprivation", "value": "type7"},
                        {"text": "Being controlled or harmed", "value": "type8"},
                        {"text": "Being lost or separated from others", "value": "type9"}
                    ]
                },
                {
                    "id": 5,
                    "question_text": "What's your worst nightmare scenario?",
                    "type": "Nightmare",
                    "options": [
                        {"text": "Making a terrible mistake that hurts others", "value": "type1"},
                        {"text": "Ending up completely alone and unloved", "value": "type2"},
                        {"text": "Being publicly exposed as a failure", "value": "type3"},
                        {"text": "Living an ordinary, meaningless life", "value": "type4"},
                        {"text": "Being overwhelmed by life's demands", "value": "type5"},
                        {"text": "Being abandoned in a dangerous world", "value": "type6"},
                        {"text": "Being trapped in endless suffering", "value": "type7"},
                        {"text": "Being weak and at the mercy of others", "value": "type8"},
                        {"text": "Losing all connection to others and self", "value": "type9"}
                    ]
                },
                {
                    "id": 6,
                    "question_text": "What would you do anything to avoid?",
                    "type": "Avoidance",
                    "options": [
                        {"text": "Making morally questionable compromises", "value": "type1"},
                        {"text": "Having your love and help rejected", "value": "type2"},
                        {"text": "Appearing incompetent or unsuccessful", "value": "type3"},
                        {"text": "Being seen as common or ordinary", "value": "type4"},
                        {"text": "Being unprepared or ignorant", "value": "type5"},
                        {"text": "Being without support or security", "value": "type6"},
                        {"text": "Experiencing deep pain or limitation", "value": "type7"},
                        {"text": "Losing control of your life", "value": "type8"},
                        {"text": "Facing conflict or tension", "value": "type9"}
                    ]
                },

                # Emotional Responses (4 questions)
                {
                    "id": 7,
                    "question_text": "How do you typically react to criticism?",
                    "type": "Criticism Response",
                    "options": [
                        {"text": "Defend my position and correct errors", "value": "type1"},
                        {"text": "Take it personally and feel hurt", "value": "type2"},
                        {"text": "Maintain my confident image", "value": "type3"},
                        {"text": "Withdraw to protect my feelings", "value": "type4"},
                        {"text": "Analyze it objectively and calmly", "value": "type5"},
                        {"text": "Question the critic's motives", "value": "type6"},
                        {"text": "Try to stay positive and move on", "value": "type7"},
                        {"text": "Challenge it directly and assertively", "value": "type8"},
                        {"text": "Avoid conflict and go with the flow", "value": "type9"}
                    ]
                },
                {
                    "id": 8,
                    "question_text": "What makes you angry?",
                    "type": "Anger Triggers",
                    "options": [
                        {"text": "When people are careless or unethical", "value": "type1"},
                        {"text": "When my help is rejected", "value": "type2"},
                        {"text": "When anything interferes with my goals", "value": "type3"},
                        {"text": "When people don't understand me", "value": "type4"},
                        {"text": "When my space or boundaries are invaded", "value": "type5"},
                        {"text": "When people betray my trust", "value": "type6"},
                        {"text": "When I'm limited or restricted", "value": "type7"},
                        {"text": "When people are unjust or weak", "value": "type8"},
                        {"text": "When my peace is disturbed", "value": "type9"}
                    ]
                },
                {
                    "id": 9,
                    "question_text": "How do you handle stress?",
                    "type": "Stress Response",
                    "options": [
                        {"text": "Work harder to fix what's wrong", "value": "type1"},
                        {"text": "Focus on helping others to distract myself", "value": "type2"},
                        {"text": "Stay busy and avoid thinking about it", "value": "type3"},
                        {"text": "Express myself emotionally", "value": "type4"},
                        {"text": "Withdraw and think through the problem", "value": "type5"},
                        {"text": "Worst-case scenario planning", "value": "type6"},
                        {"text": "Look for distractions and positive outlets", "value": "type7"},
                        {"text": "Assert control over the situation", "value": "type8"},
                        {"text": "Numb out or dissociate", "value": "type9"}
                    ]
                },
                {
                    "id": 10,
                    "question_text": "When you're emotionally overwhelmed, you tend to:",
                    "type": "Emotional Overwhelm",
                    "options": [
                        {"text": "Try to suppress or control my feelings", "value": "type1"},
                        {"text": "Seek comfort and support from others", "value": "type2"},
                        {"text": "Stay active to avoid feeling", "value": "type3"},
                        {"text": "Dive deep into my emotions", "value": "type4"},
                        {"text": "Analyze my feelings from a distance", "value": "type5"},
                        {"text": "Fear that my emotions are too intense", "value": "type6"},
                        {"text": "Seek pleasure to escape pain", "value": "type7"},
                        {"text": "Get angry or frustrated", "value": "type8"},
                        {"text": "Zone out and disconnect", "value": "type9"}
                    ]
                },

                # Decision Making (3 questions)
                {
                    "id": 11,
                    "question_text": "How do you make important decisions?",
                    "type": "Decision Process",
                    "options": [
                        {"text": "Follow my principles and what's right", "value": "type1"},
                        {"text": "Consider how it affects others", "value": "type2"},
                        {"text": "Focus on what makes me look good", "value": "type3"},
                        {"text": "Go with my feelings and intuition", "value": "type4"},
                        {"text": "Research and analyze all options", "value": "type5"},
                        {"text": "Seek advice from trusted sources", "value": "type6"},
                        {"text": "Consider the most enjoyable option", "value": "type7"},
                        {"text": "Take charge and be decisive", "value": "type8"},
                        {"text": "Avoid making the decision", "value": "type9"}
                    ]
                },
                {
                    "id": 12,
                    "question_text": "What's most important when choosing a path?",
                    "type": "Life Choices",
                    "options": [
                        {"text": "Moral correctness and integrity", "value": "type1"},
                        {"text": "How it impacts loved ones", "value": "type2"},
                        {"text": "Success and recognition", "value": "type3"},
                        {"text": "Authenticity and self-expression", "value": "type4"},
                        {"text": "Understanding and meaning", "value": "type5"},
                        {"text": "Safety and security", "value": "type6"},
                        {"text": "Freedom and happiness", "value": "type7"},
                        {"text": "Power and independence", "value": "type8"},
                        {"text": "Comfort and harmony", "value": "type9"}
                    ]
                },
                {
                    "id": 13,
                    "question_text": "In difficult situations, you trust your:",
                    "type": "Decision Trust",
                    "options": [
                        {"text": "Inner moral compass and principles", "value": "type1"},
                        {"text": "Heart and empathy for others", "value": "type2"},
                        {"text": "Experience of what works", "value": "type3"},
                        {"text": "Intuition and inner wisdom", "value": "type4"},
                        {"text": "Mind and logical analysis", "value": "type5"},
                        {"text": "Instincts and warning signals", "value": "type6"},
                        {"text": "Optimism and positive outlook", "value": "type7"},
                        {"text": "Strength and ability to endure", "value": "type8"},
                        {"text": "Gut feeling about what's right", "value": "type9"}
                    ]
                },

                # Relationships (4 questions)
                {
                    "id": 14,
                    "question_text": "What's your approach to relationships?",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Set clear standards and expect the best", "value": "type1"},
                        {"text": "Be generous and supportive", "value": "type2"},
                        {"text": "Project success and charm", "value": "type3"},
                        {"text": "Seek deep emotional connection", "value": "type4"},
                        {"text": "Maintain boundaries and observe", "value": "type5"},
                        {"text": "Be loyal and committed", "value": "type6"},
                        {"text": "Keep things fun and exciting", "value": "type7"},
                        {"text": "Protect and take charge", "value": "type8"},
                        {"text": "Avoid conflict and keep harmony", "value": "type9"}
                    ]
                },
                {
                    "id": 15,
                    "question_text": "In conflicts with loved ones, you typically:",
                    "type": "Conflict Resolution",
                    "options": [
                        {"text": "Stand firm on what's right", "value": "type1"},
                        {"text": "Give in to keep peace", "value": "type2"},
                        {"text": "Try to win or prove my point", "value": "type3"},
                        {"text": "Express my hurt feelings", "value": "type4"},
                        {"text": "Withdraw to think it through", "value": "type5"},
                        {"text": "Question their loyalty", "value": "type6"},
                        {"text": "Lighten the mood with humor", "value": "type7"},
                        {"text": "Confront them directly", "value": "type8"},
                        {"text": "Avoid bringing it up", "value": "type9"}
                    ]
                },
                {
                    "id": 16,
                    "question_text": "What do you value most in friendships?",
                    "type": "Friendship Values",
                    "options": [
                        {"text": "Reliability and shared values", "value": "type1"},
                        {"text": "Emotional support and intimacy", "value": "type2"},
                        {"text": "Mutual success and admiration", "value": "type3"},
                        {"text": "Deep understanding and authenticity", "value": "type4"},
                        {"text": "Intellectual connection and respect", "value": "type5"},
                        {"text": "Loyalty and trustworthiness", "value": "type6"},
                        {"text": "Fun and shared adventures", "value": "type7"},
                        {"text": "Honesty and directness", "value": "type8"},
                        {"text": "Comfort and easy acceptance", "value": "type9"}
                    ]
                },
                {
                    "id": 17,
                    "question_text": "How do you show love to others?",
                    "type": "Love Expression",
                    "options": [
                        {"text": "Through responsible care and guidance", "value": "type1"},
                        {"text": "Through acts of service and support", "value": "type2"},
                        {"text": "Through encouragement and admiration", "value": "type3"},
                        {"text": "Through deep emotional presence", "value": "type4"},
                        {"text": "Through thoughtful understanding", "value": "type5"},
                        {"text": "Through devoted loyalty and protection", "value": "type6"},
                        {"text": "Through joy and shared experiences", "value": "type7"},
                        {"text": "Through strength and reliability", "value": "type8"},
                        {"text": "Through gentle acceptance and peace", "value": "type9"}
                    ]
                },

                # Self-Image and Identity (3 questions)
                {
                    "id": 18,
                    "question_text": "How do you view yourself?",
                    "type": "Self-Image",
                    "options": [
                        {"text": "I am good and have integrity", "value": "type1"},
                        {"text": "I am helpful and caring", "value": "type2"},
                        {"text": "I am successful and admirable", "value": "type3"},
                        {"text": "I am unique and authentic", "value": "type4"},
                        {"text": "I am knowledgeable and perceptive", "value": "type5"},
                        {"text": "I am responsible and loyal", "value": "type6"},
                        {"text": "I am optimistic and enthusiastic", "value": "type7"},
                        {"text": "I am strong and self-reliant", "value": "type8"},
                        {"text": "I am peaceful and easygoing", "value": "type9"}
                    ]
                },
                {
                    "id": 19,
                    "question_text": "What's your greatest strength?",
                    "type": "Personal Strength",
                    "options": [
                        {"text": "My strong principles and judgment", "value": "type1"},
                        {"text": "My ability to love and support others", "value": "type2"},
                        {"text": "My competence and achievements", "value": "type3"},
                        {"text": "My emotional depth and authenticity", "value": "type4"},
                        {"text": "My insight and understanding", "value": "type5"},
                        {"text": "My loyalty and dedication", "value": "type6"},
                        {"text": "My optimism and joy", "value": "type7"},
                        {"text": "My strength and confidence", "value": "type8"},
                        {"text": "My accepting and peaceful nature", "value": "type9"}
                    ]
                },
                {
                    "id": 20,
                    "question_text": "What part of yourself do you struggle with most?",
                    "type": "Personal Challenge",
                    "options": [
                        {"text": "My anger and critical nature", "value": "type1"},
                        {"text": "My need to be needed", "value": "type2"},
                        {"text": "My tendency toward vanity", "value": "type3"},
                        {"text": "My melancholy and envy", "value": "type4"},
                        {"text": "My emotional detachment", "value": "type5"},
                        {"text": "My anxiety and doubt", "value": "type6"},
                        {"text": "My impulsiveness and excess", "value": "type7"},
                        {"text": "My lust for power and control", "value": "type8"},
                        {"text": "My inertia and avoidance", "value": "type9"}
                    ]
                },

                # Work and Achievement (3 questions)
                {
                    "id": 21,
                    "question_text": "What's your work style?",
                    "type": "Work Approach",
                    "options": [
                        {"text": "Organized, thorough, and principled", "value": "type1"},
                        {"text": "Collaborative and supportive", "value": "type2"},
                        {"text": "Ambitious and image-conscious", "value": "type3"},
                        {"text": "Creative and emotionally invested", "value": "type4"},
                        {"text": "Observant and analytical", "value": "type5"},
                        {"text": "Responsible and detail-oriented", "value": "type6"},
                        {"text": "Enthusiastic and multi-talented", "value": "type7"},
                        {"text": "Decisive and action-oriented", "value": "type8"},
                        {"text": "Steady and conflict-avoidant", "value": "type9"}
                    ]
                },
                {
                    "id": 22,
                    "question_text": "What motivates you at work?",
                    "type": "Work Motivation",
                    "options": [
                        {"text": "Making a positive difference", "value": "type1"},
                        {"text": "Helping colleagues succeed", "value": "type2"},
                        {"text": "Recognition and advancement", "value": "type3"},
                        {"text": "Meaningful, creative expression", "value": "type4"},
                        {"text": "Understanding complex problems", "value": "type5"},
                        {"text": "Job security and stability", "value": "type6"},
                        {"text": "Variety and new challenges", "value": "type7"},
                        {"text": "Leadership and results", "value": "type8"},
                        {"text": "Peaceful work environment", "value": "type9"}
                    ]
                },
                {
                    "id": 23,
                    "question_text": "How do you handle workplace conflicts?",
                    "type": "Work Conflict",
                    "options": [
                        {"text": "Address issues directly and fairly", "value": "type1"},
                        {"text": "Mediate and help find solutions", "value": "type2"},
                        {"text": "Focus on maintaining my image", "value": "type3"},
                        {"text": "Express my feelings and needs", "value": "type4"},
                        {"text": "Analyze the situation objectively", "value": "type5"},
                        {"text": "Question people's motives", "value": "type6"},
                        {"text": "Try to lighten the mood", "value": "type7"},
                        {"text": "Take charge and resolve it", "value": "type8"},
                        {"text": "Avoid getting involved", "value": "type9"}
                    ]
                },

                # Life Philosophy (4 questions)
                {
                    "id": 24,
                    "question_text": "How do you view the world?",
                    "type": "Worldview",
                    "options": [
                        {"text": "A place that needs improvement", "value": "type1"},
                        {"text": "Full of people who need love", "value": "type2"},
                        {"text": "A stage for success and achievement", "value": "type3"},
                        {"text": "A realm of deep meaning and beauty", "value": "type4"},
                        {"text": "Complex and worth understanding", "value": "type5"},
                        {"text": "Dangerous and needs protection", "value": "type6"},
                        {"text": "Full of exciting possibilities", "value": "type7"},
                        {"text": "A place where strength matters", "value": "type8"},
                        {"text": "Fundamentally good and harmonious", "value": "type9"}
                    ]
                },
                {
                    "id": 25,
                    "question_text": "What gives life meaning?",
                    "type": "Life Meaning",
                    "options": [
                        {"text": "Living according to my values", "value": "type1"},
                        {"text": "Love and connection with others", "value": "type2"},
                        {"text": "Achievement and recognition", "value": "type3"},
                        {"text": "Self-expression and authenticity", "value": "type4"},
                        {"text": "Knowledge and understanding", "value": "type5"},
                        {"text": "Security and belonging", "value": "type6"},
                        {"text": "Joy and new experiences", "value": "type7"},
                        {"text": "Making my mark on the world", "value": "type8"},
                        {"text": "Inner peace and contentment", "value": "type9"}
                    ]
                },
                {
                    "id": 26,
                    "question_text": "How do you handle change?",
                    "type": "Change Response",
                    "options": [
                        {"text": "Plan carefully to make things better", "value": "type1"},
                        {"text": "Focus on how it affects relationships", "value": "type2"},
                        {"text": "Embrace opportunities to shine", "value": "type3"},
                        {"text": "Explore the emotional landscape", "value": "type4"},
                        {"text": "Understand the deeper patterns", "value": "type5"},
                        {"text": "Prepare for potential dangers", "value": "type6"},
                        {"text": "Get excited about new possibilities", "value": "type7"},
                        {"text": "Take control of the situation", "value": "type8"},
                        {"text": "Resist and maintain stability", "value": "type9"}
                    ]
                },
                {
                    "id": 27,
                    "question_text": "What's your spiritual approach?",
                    "type": "Spirituality",
                    "options": [
                        {"text": "Discipline and moral practice", "value": "type1"},
                        {"text": "Devotion and service", "value": "type2"},
                        {"text": "Success as divine purpose", "value": "type3"},
                        {"text": "Transcendence through feeling", "value": "type4"},
                        {"text": "Understanding divine mysteries", "value": "type5"},
                        {"text": "Faith and surrender", "value": "type6"},
                        {"text": "Joy and celebration", "value": "type7"},
                        {"text": "Divine strength and power", "value": "type8"},
                        {"text": "Unity and cosmic peace", "value": "type9"}
                    ]
                },

                # Growth and Self-Development (3 questions)
                {
                    "id": 28,
                    "question_text": "For personal growth, you need to:",
                    "type": "Growth Path",
                    "options": [
                        {"text": "Relax perfectionism and accept imperfection", "value": "type1"},
                        {"text": "Learn to love yourself first", "value": "type2"},
                        {"text": "Value yourself beyond achievements", "value": "type3"},
                        {"text": "Find ordinary things meaningful", "value": "type4"},
                        {"text": "Connect with your emotions", "value": "type5"},
                        {"text": "Trust yourself and others more", "value": "type6"},
                        {"text": "Embrace pain and limitation", "value": "type7"},
                        {"text": "Become vulnerable and sensitive", "value": "type8"},
                        {"text": "Engage with life fully", "value": "type9"}
                    ]
                },
                {
                    "id": 29,
                    "question_text": "How do you handle personal growth?",
                    "type": "Growth Process",
                    "options": [
                        {"text": "Create rules and work diligently", "value": "type1"},
                        {"text": "Seek support and connection", "value": "type2"},
                        {"text": "Model successful people", "value": "type3"},
                        {"text": "Explore emotional depths", "value": "type4"},
                        {"text": "Study and research extensively", "value": "type5"},
                        {"text": "Question everything thoroughly", "value": "type6"},
                        {"text": "Try many different approaches", "value": "type7"},
                        {"text": "Push through obstacles forcefully", "value": "type8"},
                        {"text": "Be patient and gentle", "value": "type9"}
                    ]
                },
                {
                    "id": 30,
                    "question_text": "How do you want others to see you?",
                    "type": "Social Image",
                    "options": [
                        {"text": "As someone with high standards", "value": "type1"},
                        {"text": "As someone loving and helpful", "value": "type2"},
                        {"text": "As someone successful and impressive", "value": "type3"},
                        {"text": "As someone unique and special", "value": "type4"},
                        {"text": "As someone intelligent and wise", "value": "type5"},
                        {"text": "As someone reliable and dedicated", "value": "type6"},
                        {"text": "As someone fun and exciting", "value": "type7"},
                        {"text": "As someone strong and decisive", "value": "type8"},
                        {"text": "As someone peaceful and agreeable", "value": "type9"}
                    ]
                },

                {
                    "id": 31,
                    "question_text": "I struggle with accepting that:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "Good enough is often sufficient", "value": "type1"},
                        {"text": "I must constantly improve", "value": "type1"}
                    ]
                },

                {
                    "id": 32,
                    "question_text": "In leadership roles, I:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "Set high standards for everyone", "value": "type1"},
                        {"text": "Encourage others' authentic development", "value": "type1"}
                    ]
                },

                {
                    "id": 33,
                    "question_text": "My inner critic is loudest when:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "I or others make mistakes", "value": "type1"},
                        {"text": "I feel I'm not living up to potential", "value": "type1"}
                    ]
                },

                {
                    "id": 34,
                    "question_text": "I find it hardest to:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "Forgive my own imperfections", "value": "type1"},
                        {"text": "Accept others' flaws", "value": "type1"}
                    ]
                },

                {
                    "id": 35,
                    "question_text": "In relationships, I need:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "Mutual growth and improvement", "value": "type1"},
                        {"text": "Unconditional acceptance", "value": "type1"}
                    ]
                },

                {
                    "id": 36,
                    "question_text": "People who know me would say I'm:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "Overly critical of myself and others", "value": "type1"},
                        {"text": "Principled and dedicated", "value": "type1"}
                    ]
                },

                {
                    "id": 37,
                    "question_text": "I express anger through:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "Resentment and frustration", "value": "type1"},
                        {"text": "Direct communication", "value": "type1"}
                    ]
                },

                {
                    "id": 38,
                    "question_text": "I feel most anxious when:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "Things aren't done correctly", "value": "type1"},
                        {"text": "I can't control outcomes", "value": "type1"}
                    ]
                },

                {
                    "id": 39,
                    "question_text": "My greatest strength is:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "My integrity and high standards", "value": "type1"},
                        {"text": "My ability to see what's right", "value": "type1"}
                    ]
                },

                {
                    "id": 40,
                    "question_text": "I relax best when:",
                    "type": "Self-Image",
                    "options": [
                        {"text": "Everything is in its proper place", "value": "type1"},
                        {"text": "I can let go of control", "value": "type1"}
                    ]
                },

                {
                    "id": 41,
                    "question_text": "In relationships, I often:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Give more than I receive", "value": "type2"},
                        {"text": "Maintain healthy boundaries", "value": "type2"}
                    ]
                },

                {
                    "id": 42,
                    "question_text": "My biggest challenge is:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Recognizing my own needs", "value": "type2"},
                        {"text": "Asking for help when needed", "value": "type2"}
                    ]
                },

                {
                    "id": 43,
                    "question_text": "People take advantage of my:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Generosity and willingness to help", "value": "type2"},
                        {"text": "Trust and openness", "value": "type2"}
                    ]
                },

                {
                    "id": 44,
                    "question_text": "I feel most valuable when:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Others need my help", "value": "type2"},
                        {"text": "I can care for myself properly", "value": "type2"}
                    ]
                },

                {
                    "id": 45,
                    "question_text": "In conflicts, I tend to:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Mediate and seek harmony", "value": "type2"},
                        {"text": "State my own needs clearly", "value": "type2"}
                    ]
                },

                {
                    "id": 46,
                    "question_text": "My greatest fear is:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Being unloved or unwanted", "value": "type2"},
                        {"text": "Being abandoned", "value": "type2"}
                    ]
                },

                {
                    "id": 47,
                    "question_text": "I struggle with:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Feeling worthy without helping", "value": "type2"},
                        {"text": "Setting appropriate limits", "value": "type2"}
                    ]
                },

                {
                    "id": 48,
                    "question_text": "Others see me as:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Overly involved in their problems", "value": "type2"},
                        {"text": "Empathetic and supportive", "value": "type2"}
                    ]
                },

                {
                    "id": 49,
                    "question_text": "I express love by:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Being helpful and available", "value": "type2"},
                        {"text": "Respecting others' autonomy", "value": "type2"}
                    ]
                },

                {
                    "id": 50,
                    "question_text": "At my best, I am:",
                    "type": "Relationship Style",
                    "options": [
                        {"text": "Unconditionally loving", "value": "type2"},
                        {"text": "Self-aware and balanced", "value": "type2"}
                    ]
                },

                {
                    "id": 51,
                    "question_text": "I measure success by:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "External achievements and recognition", "value": "type3"},
                        {"text": "Inner fulfillment and growth", "value": "type3"}
                    ]
                },

                {
                    "id": 52,
                    "question_text": "My biggest fear is:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "Being seen as a failure", "value": "type3"},
                        {"text": "Being worthless without achievements", "value": "type3"}
                    ]
                },

                {
                    "id": 53,
                    "question_text": "I struggle with:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "Separating my worth from my success", "value": "type3"},
                        {"text": "Being vulnerable and authentic", "value": "type3"}
                    ]
                },

                {
                    "id": 54,
                    "question_text": "People would describe me as:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "Image-conscious and competitive", "value": "type3"},
                        {"text": "Ambitious and capable", "value": "type3"}
                    ]
                },

                {
                    "id": 55,
                    "question_text": "In relationships, I:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "Project success and confidence", "value": "type3"},
                        {"text": "Show my authentic self", "value": "type3"}
                    ]
                },

                {
                    "id": 56,
                    "question_text": "I feel most anxious when:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "I'm not achieving or progressing", "value": "type3"},
                        {"text": "Others might see my flaws", "value": "type3"}
                    ]
                },

                {
                    "id": 57,
                    "question_text": "My core drive is:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "To be valuable and admired", "value": "type3"},
                        {"text": "To be genuine and loved", "value": "type3"}
                    ]
                },

                {
                    "id": 58,
                    "question_text": "I find it hard to:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "Admit when I don't know something", "value": "type3"},
                        {"text": "Just be without performing", "value": "type3"}
                    ]
                },

                {
                    "id": 59,
                    "question_text": "Others criticize me for being:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "Inauthentic or superficial", "value": "type3"},
                        {"text": "Too focused on success", "value": "type3"}
                    ]
                },

                {
                    "id": 60,
                    "question_text": "At my best, I am:",
                    "type": "Success Identity",
                    "options": [
                        {"text": "Authentic and inspiring", "value": "type3"},
                        {"text": "Truly successful and fulfilled", "value": "type3"}
                    ]
                },

                {
                    "id": 61,
                    "question_text": "I feel most misunderstood when:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Others don't see my depth", "value": "type4"},
                        {"text": "I seem too dramatic", "value": "type4"}
                    ]
                },

                {
                    "id": 62,
                    "question_text": "My greatest struggle is:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Feeling ordinary or mundane", "value": "type4"},
                        {"text": "Managing my emotional intensity", "value": "type4"}
                    ]
                },

                {
                    "id": 63,
                    "question_text": "People would describe me as:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Overly sensitive or dramatic", "value": "type4"},
                        {"text": "Deep and creative", "value": "type4"}
                    ]
                },

                {
                    "id": 64,
                    "question_text": "I find beauty in:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Melancholy and suffering", "value": "type4"},
                        {"text": "Authentic emotional expression", "value": "type4"}
                    ]
                },

                {
                    "id": 65,
                    "question_text": "In relationships, I:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Seek deep, intense connection", "value": "type4"},
                        {"text": "Fear abandonment and rejection", "value": "type4"}
                    ]
                },

                {
                    "id": 66,
                    "question_text": "My core fear is:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Having no identity or significance", "value": "type4"},
                        {"text": "Being common or ordinary", "value": "type4"}
                    ]
                },

                {
                    "id": 67,
                    "question_text": "I struggle with:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Envy of others' happiness", "value": "type4"},
                        {"text": "Feeling fundamentally flawed", "value": "type4"}
                    ]
                },

                {
                    "id": 68,
                    "question_text": "I express myself through:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Art and creativity", "value": "type4"},
                        {"text": "Deep emotional conversations", "value": "type4"}
                    ]
                },

                {
                    "id": 69,
                    "question_text": "Others criticize me for being:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Too moody or self-absorbed", "value": "type4"},
                        {"text": "Overly dramatic", "value": "type4"}
                    ]
                },

                {
                    "id": 70,
                    "question_text": "At my best, I am:",
                    "type": "Emotional Depth",
                    "options": [
                        {"text": "Creatively inspired and authentic", "value": "type4"},
                        {"text": "Emotionally balanced and grounded", "value": "type4"}
                    ]
                },

                {
                    "id": 71,
                    "question_text": "I feel safest when:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "I understand how things work", "value": "type5"},
                        {"text": "I have time to myself", "value": "type5"}
                    ]
                },

                {
                    "id": 72,
                    "question_text": "My biggest challenge is:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "Engaging with the emotional world", "value": "type5"},
                        {"text": "Sharing my inner thoughts", "value": "type5"}
                    ]
                },

                {
                    "id": 73,
                    "question_text": "People see me as:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "Detached or overly analytical", "value": "type5"},
                        {"text": "Intelligent and perceptive", "value": "type5"}
                    ]
                },

                {
                    "id": 74,
                    "question_text": "I prefer to:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "Observe rather than participate", "value": "type5"},
                        {"text": "Understand before engaging", "value": "type5"}
                    ]
                },

                {
                    "id": 75,
                    "question_text": "In relationships, I:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "Need intellectual connection", "value": "type5"},
                        {"text": "Require lots of personal space", "value": "type5"}
                    ]
                },

                {
                    "id": 76,
                    "question_text": "My greatest fear is:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "Being helpless or incompetent", "value": "type5"},
                        {"text": "Having no privacy or autonomy", "value": "type5"}
                    ]
                },

                {
                    "id": 77,
                    "question_text": "I struggle with:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "Expressing my feelings", "value": "type5"},
                        {"text": "Being emotionally vulnerable", "value": "type5"}
                    ]
                },

                {
                    "id": 78,
                    "question_text": "I feel most drained when:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "I have too much social interaction", "value": "type5"},
                        {"text": "I can't research enough", "value": "type5"}
                    ]
                },

                {
                    "id": 79,
                    "question_text": "Others describe me as:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "Too reserved or distant", "value": "type5"},
                        {"text": "Knowledgeable and insightful", "value": "type5"}
                    ]
                },

                {
                    "id": 80,
                    "question_text": "At my best, I am:",
                    "type": "Knowledge Seeking",
                    "options": [
                        {"text": "Wise and understanding", "value": "type5"},
                        {"text": "Engaged and connected", "value": "type5"}
                    ]
                },

                {
                    "id": 81,
                    "question_text": "I approach life with:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "Careful planning and risk assessment", "value": "type6"},
                        {"text": "Trust in supportive relationships", "value": "type6"}
                    ]
                },

                {
                    "id": 82,
                    "question_text": "My biggest challenge is:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "Trusting myself and others", "value": "type6"},
                        {"text": "Making decisions without doubt", "value": "type6"}
                    ]
                },

                {
                    "id": 83,
                    "question_text": "People would describe me as:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "Anxious or overly cautious", "value": "type6"},
                        {"text": "Loyal and committed", "value": "type6"}
                    ]
                },

                {
                    "id": 84,
                    "question_text": "I feel most anxious when:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "I don't have a safety net", "value": "type6"},
                        {"text": "I have to act independently", "value": "type6"}
                    ]
                },

                {
                    "id": 85,
                    "question_text": "In decision-making, I:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "Seek guidance from trusted sources", "value": "type6"},
                        {"text": "Question everything thoroughly", "value": "type6"}
                    ]
                },

                {
                    "id": 86,
                    "question_text": "My core fear is:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "Being without support or guidance", "value": "type6"},
                        {"text": "Facing danger alone", "value": "type6"}
                    ]
                },

                {
                    "id": 87,
                    "question_text": "I struggle with:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "Self-doubt and second-guessing", "value": "type6"},
                        {"text": "Trusting my instincts", "value": "type6"}
                    ]
                },

                {
                    "id": 88,
                    "question_text": "I find security in:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "Clear rules and authorities", "value": "type6"},
                        {"text": "Personal relationships and loyalty", "value": "type6"}
                    ]
                },

                {
                    "id": 89,
                    "question_text": "Others criticize me for being:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "Too dependent or fearful", "value": "type6"},
                        {"text": "Overly analytical", "value": "type6"}
                    ]
                },

                {
                    "id": 90,
                    "question_text": "At my best, I am:",
                    "type": "Security Seeking",
                    "options": [
                        {"text": "Courageous and supportive", "value": "type6"},
                        {"text": "Confident and self-trusting", "value": "type6"}
                    ]
                }
            ],
            "types_info": {
                "type1": {
                    "name": "The Reformer",
                    "description": "Rational, idealistic, principled perfectionists who want to improve the world"
                },
                "type2": {
                    "name": "The Helper",
                    "description": "Caring, interpersonal, generous givers who are driven to be loved"
                },
                "type3": {
                    "name": "The Achiever",
                    "description": "Success-oriented, pragmatic, adaptive achievers who want to feel valuable"
                },
                "type4": {
                    "name": "The Individualist",
                    "description": "Sensitive, introspective, expressive artists who want to be unique"
                },
                "type5": {
                    "name": "The Investigator",
                    "description": "Innovative, perceptive, knowledge seekers who want to understand the world"
                },
                "type6": {
                    "name": "The Loyalist",
                    "description": "Engaging, responsible, anxious loyalists who want security"
                },
                "type7": {
                    "name": "The Enthusiast",
                    "description": "Spontaneous, versatile, multi-talented optimists who want to be happy"
                },
                "type8": {
                    "name": "The Challenger",
                    "description": "Self-confident, decisive, controlling protectors who want to be strong"
                },
                "type9": {
                    "name": "The Peacemaker",
                    "description": "Receptive, reassuring, complacent mediators who want peace"
                }
            },
            "scoring_method": "Enneagram assessment identifies your dominant type by analyzing patterns in your responses. Most people have one primary type but may show traits of others (wings)."
        }

        return {
            "success": True,
            "assessment": enneagram_assessment,
            "message": "Enneagram assessment questions loaded successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load Enneagram assessment questions: {str(e)}"
        )

@router.get("/assessment-questions/big-five")
async def get_big_five_assessment_questions():
    """
    Get Big Five assessment questions from backend

    Returns a complete Big Five (OCEAN) assessment with 10 questions
    covering Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
    """
    try:
        big_five_assessment = {
            "id": "big-five-standard",
            "title": "Big Five Personality Assessment",
            "description": "Discover your Big Five personality traits (OCEAN): Openness, Conscientiousness, Extraversion, Agreeableness, and Neuroticism. This comprehensive assessment provides insights into your core personality dimensions.",
            "instructions": "Rate each statement on a scale of 1 (Strongly Disagree) to 5 (Strongly Agree) based on how accurately it describes you.",
            "estimated_time": "45-60 minutes",
            "questions": [
                {
                    "id": 1,
                    "question_text": "I see myself as someone who is original and comes up with new ideas",
                    "trait": "Openness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 2,
                    "question_text": "I see myself as someone who is curious about many different things",
                    "trait": "Openness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 3,
                    "question_text": "I see myself as someone who is inventive and finds new ways to do things",
                    "trait": "Openness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 4,
                    "question_text": "I see myself as someone who values artistic and aesthetic experiences",
                    "trait": "Openness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 5,
                    "question_text": "I see myself as someone who prefers variety over routine",
                    "trait": "Openness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 6,
                    "question_text": "I see myself as someone who thinks about and discusses abstract concepts",
                    "trait": "Openness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },

                # Conscientiousness (6 questions)
                {
                    "id": 7,
                    "question_text": "I see myself as someone who does a thorough job",
                    "trait": "Conscientiousness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 8,
                    "question_text": "I see myself as someone who can be somewhat careless",
                    "trait": "Conscientiousness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 9,
                    "question_text": "I see myself as someone who is a reliable worker",
                    "trait": "Conscientiousness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 10,
                    "question_text": "I see myself as someone who tends to be organized",
                    "trait": "Conscientiousness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 11,
                    "question_text": "I see myself as someone who perseveres until the task is finished",
                    "trait": "Conscientiousness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 12,
                    "question_text": "I see myself as someone who can be somewhat lazy",
                    "trait": "Conscientiousness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },

                # Extraversion (6 questions)
                {
                    "id": 13,
                    "question_text": "I see myself as someone who is talkative",
                    "trait": "Extraversion",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 14,
                    "question_text": "I see myself as someone who is reserved",
                    "trait": "Extraversion",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 15,
                    "question_text": "I see myself as someone who is full of energy",
                    "trait": "Extraversion",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 16,
                    "question_text": "I see myself as someone who generates enthusiasm in others",
                    "trait": "Extraversion",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 17,
                    "question_text": "I see myself as someone who is assertive and takes charge",
                    "trait": "Extraversion",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 18,
                    "question_text": "I see myself as someone who prefers being alone rather than with others",
                    "trait": "Extraversion",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },

                # Agreeableness (6 questions)
                {
                    "id": 19,
                    "question_text": "I see myself as someone who tends to find fault with others",
                    "trait": "Agreeableness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 20,
                    "question_text": "I see myself as someone who is helpful and unselfish with others",
                    "trait": "Agreeableness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 21,
                    "question_text": "I see myself as someone who starts arguments with others",
                    "trait": "Agreeableness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 22,
                    "question_text": "I see myself as someone who has a forgiving nature",
                    "trait": "Agreeableness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 23,
                    "question_text": "I see myself as someone who is generally trusting",
                    "trait": "Agreeableness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 24,
                    "question_text": "I see myself as someone who can be cold and aloof",
                    "trait": "Agreeableness",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },

                # Neuroticism (6 questions)
                {
                    "id": 25,
                    "question_text": "I see myself as someone who is depressed, blue",
                    "trait": "Neuroticism",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 26,
                    "question_text": "I see myself as someone who is relaxed, handles stress well",
                    "trait": "Neuroticism",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 27,
                    "question_text": "I see myself as someone who can be tense",
                    "trait": "Neuroticism",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 28,
                    "question_text": "I see myself as someone who worries a lot",
                    "trait": "Neuroticism",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 29,
                    "question_text": "I see myself as someone who can get easily upset",
                    "trait": "Neuroticism",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },
                {
                    "id": 30,
                    "question_text": "I see myself as someone who remains calm in tense situations",
                    "trait": "Neuroticism",
                    "scale": "1-5",
                    "options": [
                        {"text": "Strongly Disagree", "value": 1},
                        {"text": "Disagree", "value": 2},
                        {"text": "Neutral", "value": 3},
                        {"text": "Agree", "value": 4},
                        {"text": "Strongly Agree", "value": 5}
                    ]
                },

                {
                    "id": 7,
                    "question_text": "I enjoy debating complex philosophical concepts",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 8,
                    "question_text": "I seek out new and unconventional experiences",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 9,
                    "question_text": "I find abstract theories fascinating",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 10,
                    "question_text": "I prefer variety over routine in my daily life",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 11,
                    "question_text": "I'm drawn to artistic and creative pursuits",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 12,
                    "question_text": "I enjoy exploring different cultural perspectives",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 13,
                    "question_text": "I'm comfortable with ambiguity and uncertainty",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 14,
                    "question_text": "I like to analyze problems from multiple angles",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 15,
                    "question_text": "I'm energized by learning new skills",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 16,
                    "question_text": "I appreciate unconventional beauty in art and nature",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 17,
                    "question_text": "I enjoy intellectual challenges that stretch my mind",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 18,
                    "question_text": "I'm fascinated by how things work at a fundamental level",
                    "trait": "Openness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 19,
                    "question_text": "I always double-check my work for accuracy",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 20,
                    "question_text": "I prefer to plan ahead rather than be spontaneous",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 21,
                    "question_text": "I keep my promises even when it's difficult",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 22,
                    "question_text": "I'm methodical in my approach to tasks",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 23,
                    "question_text": "I feel satisfied when I complete everything on my to-do list",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 24,
                    "question_text": "I prefer organized environments over chaotic ones",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 25,
                    "question_text": "I'm diligent about meeting deadlines",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 26,
                    "question_text": "I pay attention to small details that others might miss",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 27,
                    "question_text": "I believe in doing things right the first time",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 28,
                    "question_text": "I maintain strict standards for myself",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 29,
                    "question_text": "I feel uneasy when my workspace is disorganized",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 30,
                    "question_text": "I prefer structured approaches to problem-solving",
                    "trait": "Conscientiousness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 31,
                    "question_text": "I thrive in social situations with many people",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 32,
                    "question_text": "I prefer working in teams rather than alone",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 33,
                    "question_text": "I enjoy being the center of attention",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 34,
                    "question_text": "I feel energized after social gatherings",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 35,
                    "question_text": "I speak up in group discussions",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 36,
                    "question_text": "I enjoy meeting new people regularly",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 37,
                    "question_text": "I prefer active social activities over quiet ones",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 38,
                    "question_text": "I express my thoughts and feelings openly",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 39,
                    "question_text": "I enjoy taking leadership roles in groups",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 40,
                    "question_text": "I feel comfortable striking up conversations with strangers",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 41,
                    "question_text": "I prefer lively environments over calm ones",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 42,
                    "question_text": "I enjoy entertaining and engaging others",
                    "trait": "Extraversion",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 43,
                    "question_text": "I prioritize harmony in group settings",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 44,
                    "question_text": "I'm quick to help others in need",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 45,
                    "question_text": "I avoid arguments and conflicts",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 46,
                    "question_text": "I consider others' feelings before acting",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 47,
                    "question_text": "I believe most people are fundamentally good",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 48,
                    "question_text": "I enjoy doing favors for others",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 49,
                    "question_text": "I'm patient with people's shortcomings",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 50,
                    "question_text": "I feel empathy for those less fortunate",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 51,
                    "question_text": "I prefer cooperation over competition",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 52,
                    "question_text": "I'm forgiving when others make mistakes",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 53,
                    "question_text": "I avoid criticizing others",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 54,
                    "question_text": "I value kindness over being right",
                    "trait": "Agreeableness",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 55,
                    "question_text": "I frequently worry about things that might go wrong",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 56,
                    "question_text": "I get upset easily over minor issues",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 57,
                    "question_text": "I feel anxious in unfamiliar situations",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 58,
                    "question_text": "I'm sensitive to criticism from others",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 59,
                    "question_text": "I often feel overwhelmed by stress",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 60,
                    "question_text": "I mood can change quickly",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 61,
                    "question_text": "I tend to expect the worst outcome",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 62,
                    "question_text": "I feel nervous before important events",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 63,
                    "question_text": "I get discouraged by setbacks easily",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 64,
                    "question_text": "I often feel tense or on edge",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 65,
                    "question_text": "I'm easily affected by negative news",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },

                {
                    "id": 66,
                    "question_text": "I frequently experience self-doubt",
                    "trait": "Neuroticism",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                }
            ],
            "traits_info": {
                "Openness": {
                    "name": "Openness to Experience",
                    "description": "Appreciation for art, emotion, adventure, unusual ideas, curiosity, and variety of experience"
                },
                "Conscientiousness": {
                    "name": "Conscientiousness",
                    "description": "Tendency to be organized, responsible, and hardworking"
                },
                "Extraversion": {
                    "name": "Extraversion",
                    "description": "Tendency to seek stimulation in the company of others, talkativeness, and assertiveness"
                },
                "Agreeableness": {
                    "name": "Agreeableness",
                    "description": "Tendency to be compassionate and cooperative rather than suspicious and antagonistic"
                },
                "Neuroticism": {
                    "name": "Neuroticism",
                    "description": "Tendency to experience unpleasant emotions easily, such as anger, anxiety, depression, or vulnerability"
                }
            },
            "scoring_method": "Big Five traits are scored on a 1-5 scale. Higher scores indicate stronger expression of each trait, with reverse scoring for negatively worded items."
        }

        return {
            "success": True,
            "assessment": big_five_assessment,
            "message": "Big Five assessment questions loaded successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load Big Five assessment questions: {str(e)}"
        )

@router.get("/assessment-questions/big_five")
async def get_big_five_assessment_questions_underscore():
    """
    Get Big Five assessment questions from backend (underscore version for frontend compatibility)

    This is an alias for the big-five endpoint to maintain frontend compatibility
    """
    # Forward to the main Big Five endpoint function
    return await get_big_five_assessment_questions()

@router.get("/assessment-questions/predictive-index")
async def get_predictive_index_assessment_questions():
    """
    Get Predictive Index assessment questions from backend

    Returns a Predictive Index assessment with questions measuring
    dominance, extraversion, patience, and formality
    """
    try:
        pi_assessment = {
            "id": "pi-standard",
            "title": "Predictive Index Behavioral Assessment",
            "description": "Discover your workplace behavioral drives and needs through the Predictive Index. This assessment helps understand how you naturally behave and what motivates you at work.",
            "instructions": "Choose the adjective that best describes you in each pair. There are no right or wrong answers - select what feels most authentic to you.",
            "estimated_time": "45-60 minutes",
            "questions": [
                {
                    "id": 1,
                    "question_text": "I am:",
                    "pair": 1,
                    "options": [
                        {"text": "Analytical", "value": "A"},
                        {"text": "Social", "value": "B"}
                    ]
                },
                {
                    "id": 2,
                    "question_text": "I am:",
                    "pair": 1,
                    "options": [
                        {"text": "Reserved", "value": "A"},
                        {"text": "Driving", "value": "B"}
                    ]
                },
                {
                    "id": 3,
                    "question_text": "I am:",
                    "pair": 2,
                    "options": [
                        {"text": "Patient", "value": "A"},
                        {"text": "Urgent", "value": "B"}
                    ]
                },
                {
                    "id": 4,
                    "question_text": "I am:",
                    "pair": 2,
                    "options": [
                        {"text": "Formal", "value": "A"},
                        {"text": "Informal", "value": "B"}
                    ]
                },
                {
                    "id": 5,
                    "question_text": "I am:",
                    "pair": 3,
                    "options": [
                        {"text": "Collaborative", "value": "A"},
                        {"text": "Intense", "value": "B"}
                    ]
                },
                {
                    "id": 6,
                    "question_text": "I am:",
                    "pair": 3,
                    "options": [
                        {"text": "Pioneering", "value": "A"},
                        {"text": "Supportive", "value": "B"}
                    ]
                },
                {
                    "id": 7,
                    "question_text": "I am:",
                    "pair": 4,
                    "options": [
                        {"text": "Objective", "value": "A"},
                        {"text": "Empathetic", "value": "B"}
                    ]
                },
                {
                    "id": 8,
                    "question_text": "I am:",
                    "pair": 4,
                    "options": [
                        {"text": "Deliberate", "value": "A"},
                        {"text": "Spontaneous", "value": "B"}
                    ]
                }
            ],
            "factors_info": {
                "A": {
                    "name": "Factor A (Patience & Formality)",
                    "description": "Measures patience, formality, and intensity. Factor A relates to how methodical and detail-oriented you are."
                },
                "B": {
                    "name": "Factor B (Dominance & Extraversion)",
                    "description": "Measures dominance, extraversion, and urgency. Factor B relates to how driving and socially engaging you are."
                }
            },
            "scoring_method": "Predictive Index is scored by counting A and B selections. Results place individuals on four factors: Dominance, Extraversion, Patience, and Formality."
        }

        return {
            "success": True,
            "assessment": pi_assessment,
            "message": "Predictive Index assessment questions loaded successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load Predictive Index assessment questions: {str(e)}"
        )

@router.get("/assessment-questions/predictive_index")
async def get_predictive_index_assessment_questions_underscore():
    """
    Get Predictive Index assessment questions from backend (underscore version for frontend compatibility)

    This is an alias for the predictive-index endpoint to maintain frontend compatibility
    """
    return await get_predictive_index_assessment_questions()

@router.get("/assessment-questions/disc")
async def get_disc_assessment_questions():
    """
    Get DISC assessment questions from backend

    Returns a DISC assessment measuring Dominance, Influence,
    Steadiness, and Conscientiousness behavioral styles
    """
    try:
        disc_assessment = {
            "id": "disc-standard",
            "title": "DISC Behavioral Assessment",
            "description": "Discover your DISC behavioral style: Dominance, Influence, Steadiness, and Conscientiousness. Understand how you naturally approach problems, people, pace, and procedures.",
            "instructions": "For each question, choose the statement that MOST describes you and the statement that LEAST describes you in work situations.",
            "estimated_time": "45-60 minutes",
            "questions": [
                {
                    "id": 1,
                    "question_text": "Which describes you better?",
                    "most": "Enthusiastic",
                    "least": "Reserved",
                    "options": [
                        {"text": "Enthusiastic", "value": "most"},
                        {"text": "Reserved", "value": "least"}
                    ]
                },
                {
                    "id": 2,
                    "question_text": "Which describes you better?",
                    "most": "Collaborative",
                    "least": "Competitive",
                    "options": [
                        {"text": "Collaborative", "value": "most"},
                        {"text": "Competitive", "value": "least"}
                    ]
                },
                {
                    "id": 3,
                    "question_text": "Which describes you better?",
                    "most": "Patient",
                    "least": "Urgent",
                    "options": [
                        {"text": "Patient", "value": "most"},
                        {"text": "Urgent", "value": "least"}
                    ]
                },
                {
                    "id": 4,
                    "question_text": "Which describes you better?",
                    "most": "Analytical",
                    "least": "Emotional",
                    "options": [
                        {"text": "Analytical", "value": "most"},
                        {"text": "Emotional", "value": "least"}
                    ]
                },
                {
                    "id": 5,
                    "question_text": "Which describes you better?",
                    "most": "Direct",
                    "least": "Indirect",
                    "options": [
                        {"text": "Direct", "value": "most"},
                        {"text": "Indirect", "value": "least"}
                    ]
                },
                {
                    "id": 6,
                    "question_text": "Which describes you better?",
                    "most": "Diplomatic",
                    "least": "Frank",
                    "options": [
                        {"text": "Diplomatic", "value": "most"},
                        {"text": "Frank", "value": "least"}
                    ]
                },
                {
                    "id": 7,
                    "question_text": "Which describes you better?",
                    "most": "Steady",
                    "least": "Dynamic",
                    "options": [
                        {"text": "Steady", "value": "most"},
                        {"text": "Dynamic", "value": "least"}
                    ]
                },
                {
                    "id": 8,
                    "question_text": "Which describes you better?",
                    "most": "Pioneering",
                    "least": "Supportive",
                    "options": [
                        {"text": "Pioneering", "value": "most"},
                        {"text": "Supportive", "value": "least"}
                    ]
                },
                {
                    "id": 9,
                    "question_text": "Which describes you better?",
                    "most": "Results-oriented",
                    "least": "Process-oriented",
                    "options": [
                        {"text": "Results-oriented", "value": "most"},
                        {"text": "Process-oriented", "value": "least"}
                    ]
                },
                {
                    "id": 10,
                    "question_text": "Which describes you better?",
                    "most": "Outspoken",
                    "least": "Reflective",
                    "options": [
                        {"text": "Outspoken", "value": "most"},
                        {"text": "Reflective", "value": "least"}
                    ]
                },
                {
                    "id": 11,
                    "question_text": "Which describes you better?",
                    "most": "Driving",
                    "least": "Supporting",
                    "options": [
                        {"text": "Driving", "value": "most"},
                        {"text": "Supporting", "value": "least"}
                    ]
                },
                {
                    "id": 12,
                    "question_text": "Which describes you better?",
                    "most": "Influencing",
                    "least": "Cautious",
                    "options": [
                        {"text": "Influencing", "value": "most"},
                        {"text": "Cautious", "value": "least"}
                    ]
                },
                {
                    "id": 13,
                    "question_text": "Which describes you better?",
                    "most": "Innovative",
                    "least": "Traditional",
                    "options": [
                        {"text": "Innovative", "value": "most"},
                        {"text": "Traditional", "value": "least"}
                    ]
                },
                {
                    "id": 14,
                    "question_text": "Which describes you better?",
                    "most": "Spontaneous",
                    "least": "Planned",
                    "options": [
                        {"text": "Spontaneous", "value": "most"},
                        {"text": "Planned", "value": "least"}
                    ]
                },
                {
                    "id": 15,
                    "question_text": "Which describes you better?",
                    "most": "Bold",
                    "least": "Modest",
                    "options": [
                        {"text": "Bold", "value": "most"},
                        {"text": "Modest", "value": "least"}
                    ]
                },
                {
                    "id": 16,
                    "question_text": "Which describes you better?",
                    "most": "Decisive",
                    "least": "Deliberate",
                    "options": [
                        {"text": "Decisive", "value": "most"},
                        {"text": "Deliberate", "value": "least"}
                    ]
                },
                {
                    "id": 17,
                    "question_text": "Which describes you better?",
                    "most": "Persuasive",
                    "least": "Fact-finding",
                    "options": [
                        {"text": "Persuasive", "value": "most"},
                        {"text": "Fact-finding", "value": "least"}
                    ]
                },
                {
                    "id": 18,
                    "question_text": "Which describes you better?",
                    "most": "Optimistic",
                    "least": "Skeptical",
                    "options": [
                        {"text": "Optimistic", "value": "most"},
                        {"text": "Skeptical", "value": "least"}
                    ]
                },
                {
                    "id": 19,
                    "question_text": "Which describes you better?",
                    "most": "Active",
                    "least": "Passive",
                    "options": [
                        {"text": "Active", "value": "most"},
                        {"text": "Passive", "value": "least"}
                    ]
                },
                {
                    "id": 20,
                    "question_text": "Which describes you better?",
                    "most": "Talkative",
                    "least": "Quiet",
                    "options": [
                        {"text": "Talkative", "value": "most"},
                        {"text": "Quiet", "value": "least"}
                    ]
                },
                {
                    "id": 21,
                    "question_text": "Which describes you better?",
                    "most": "Dominant",
                    "least": "Compliant",
                    "options": [
                        {"text": "Dominant", "value": "most"},
                        {"text": "Compliant", "value": "least"}
                    ]
                },
                {
                    "id": 22,
                    "question_text": "Which describes you better?",
                    "most": "Adventurous",
                    "least": "Careful",
                    "options": [
                        {"text": "Adventurous", "value": "most"},
                        {"text": "Careful", "value": "least"}
                    ]
                },
                {
                    "id": 23,
                    "question_text": "Which describes you better?",
                    "most": "Forceful",
                    "least": "Gentle",
                    "options": [
                        {"text": "Forceful", "value": "most"},
                        {"text": "Gentle", "value": "least"}
                    ]
                },
                {
                    "id": 24,
                    "question_text": "Which describes you better?",
                    "most": "Independent",
                    "least": "Cooperative",
                    "options": [
                        {"text": "Independent", "value": "most"},
                        {"text": "Cooperative", "value": "least"}
                    ]
                },
                {
                    "id": 25,
                    "question_text": "Which describes you better?",
                    "most": "Risk-taking",
                    "least": "Risk-averse",
                    "options": [
                        {"text": "Risk-taking", "value": "most"},
                        {"text": "Risk-averse", "value": "least"}
                    ]
                },
                {
                    "id": 26,
                    "question_text": "Which describes you better?",
                    "most": "Fast-paced",
                    "least": "Methodical",
                    "options": [
                        {"text": "Fast-paced", "value": "most"},
                        {"text": "Methodical", "value": "least"}
                    ]
                },
                {
                    "id": 27,
                    "question_text": "Which describes you better?",
                    "most": "Impulsive",
                    "least": "Controlled",
                    "options": [
                        {"text": "Impulsive", "value": "most"},
                        {"text": "Controlled", "value": "least"}
                    ]
                },
                {
                    "id": 28,
                    "question_text": "Which describes you better?",
                    "most": "Assertive",
                    "least": "Agreeable",
                    "options": [
                        {"text": "Assertive", "value": "most"},
                        {"text": "Agreeable", "value": "least"}
                    ]
                },
                {
                    "id": 29,
                    "question_text": "Which describes you better?",
                    "most": "Competitive",
                    "least": "Harmonious",
                    "options": [
                        {"text": "Competitive", "value": "most"},
                        {"text": "Harmonious", "value": "least"}
                    ]
                },
                {
                    "id": 30,
                    "question_text": "Which describes you better?",
                    "most": "Logical",
                    "least": "Intuitive",
                    "options": [
                        {"text": "Logical", "value": "most"},
                        {"text": "Intuitive", "value": "least"}
                    ]
                },
                {
                    "id": 31,
                    "question_text": "Which describes you better?",
                    "most": "Objective",
                    "least": "Subjective",
                    "options": [
                        {"text": "Objective", "value": "most"},
                        {"text": "Subjective", "value": "least"}
                    ]
                },
                {
                    "id": 32,
                    "question_text": "Which describes you better?",
                    "most": "Critical",
                    "least": "Accepting",
                    "options": [
                        {"text": "Critical", "value": "most"},
                        {"text": "Accepting", "value": "least"}
                    ]
                },
                {
                    "id": 33,
                    "question_text": "Which describes you better?",
                    "most": "Questioning",
                    "least": "Accepting",
                    "options": [
                        {"text": "Questioning", "value": "most"},
                        {"text": "Accepting", "value": "least"}
                    ]
                },
                {
                    "id": 34,
                    "question_text": "Which describes you better?",
                    "most": "Formal",
                    "least": "Informal",
                    "options": [
                        {"text": "Formal", "value": "most"},
                        {"text": "Informal", "value": "least"}
                    ]
                },
                {
                    "id": 35,
                    "question_text": "Which describes you better?",
                    "most": "Serious",
                    "least": "Playful",
                    "options": [
                        {"text": "Serious", "value": "most"},
                        {"text": "Playful", "value": "least"}
                    ]
                },
                {
                    "id": 36,
                    "question_text": "Which describes you better?",
                    "most": "Disciplined",
                    "least": "Flexible",
                    "options": [
                        {"text": "Disciplined", "value": "most"},
                        {"text": "Flexible", "value": "least"}
                    ]
                },
                {
                    "id": 37,
                    "question_text": "Which describes you better?",
                    "most": "Systematic",
                    "least": "Casual",
                    "options": [
                        {"text": "Systematic", "value": "most"},
                        {"text": "Casual", "value": "least"}
                    ]
                },
                {
                    "id": 38,
                    "question_text": "Which describes you better?",
                    "most": "Precise",
                    "least": "General",
                    "options": [
                        {"text": "Precise", "value": "most"},
                        {"text": "General", "value": "least"}
                    ]
                },
                {
                    "id": 39,
                    "question_text": "Which describes you better?",
                    "most": "Conventional",
                    "least": "Unconventional",
                    "options": [
                        {"text": "Conventional", "value": "most"},
                        {"text": "Unconventional", "value": "least"}
                    ]
                },
                {
                    "id": 40,
                    "question_text": "Which describes you better?",
                    "most": "Conservative",
                    "least": "Liberal",
                    "options": [
                        {"text": "Conservative", "value": "most"},
                        {"text": "Liberal", "value": "least"}
                    ]
                },
                {
                    "id": 41,
                    "question_text": "Which describes you better?",
                    "most": "Structured",
                    "least": "Spontaneous",
                    "options": [
                        {"text": "Structured", "value": "most"},
                        {"text": "Spontaneous", "value": "least"}
                    ]
                },
                {
                    "id": 42,
                    "question_text": "Which describes you better?",
                    "most": "Persistent",
                    "least": "Adaptable",
                    "options": [
                        {"text": "Persistent", "value": "most"},
                        {"text": "Adaptable", "value": "least"}
                    ]
                },
                {
                    "id": 43,
                    "question_text": "Which describes you better?",
                    "most": "Consistent",
                    "least": "Variable",
                    "options": [
                        {"text": "Consistent", "value": "most"},
                        {"text": "Variable", "value": "least"}
                    ]
                },
                {
                    "id": 44,
                    "question_text": "Which describes you better?",
                    "most": "Stable",
                    "least": "Changeable",
                    "options": [
                        {"text": "Stable", "value": "most"},
                        {"text": "Changeable", "value": "least"}
                    ]
                },
                {
                    "id": 45,
                    "question_text": "Which describes you better?",
                    "most": "Predictable",
                    "least": "Surprising",
                    "options": [
                        {"text": "Predictable", "value": "most"},
                        {"text": "Surprising", "value": "least"}
                    ]
                }
            ]
            "styles_info": {
                "D": {
                    "name": "Dominance",
                    "description": "Direct, decisive, strong-willed. High D's are results-oriented, take-charge people who accept challenges."
                },
                "I": {
                    "name": "Influence",
                    "description": "Outgoing, enthusiastic, optimistic. High I's are people-oriented, expressive, and influential."
                },
                "S": {
                    "name": "Steadiness",
                    "description": "Even-tempered, accommodating, patient. High S's are calm, reliable, and team-oriented."
                },
                "C": {
                    "name": "Conscientiousness",
                    "description": "Analytical, reserved, precise. High C's are detail-oriented, quality-focused, and systematic."
                }
            },
            "scoring_method": "DISC is scored by analyzing most and least responses across multiple questions. Results indicate your primary and secondary behavioral styles and how they combine."
        }

        return {
            "success": True,
            "assessment": disc_assessment,
            "message": "DISC assessment questions loaded successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load DISC assessment questions: {str(e)}"
        )

@router.get("/assessment-questions/social")
async def get_social_styles_assessment_questions():
    """
    Get Social Styles assessment questions from backend

    Returns a Social Styles assessment with questions measuring
    Analytical, Driver, Amiable, and Expressive behavioral patterns
    """
    try:
        social_styles_assessment = {
            "id": "social-styles-standard",
            "title": "Social Styles Assessment",
            "description": "Discover your Social Style: Analytical, Driver, Amiable, or Expressive. Understand how your behavioral style impacts communication and relationships.",
            "instructions": "Choose the response that best describes your typical behavior in workplace or social situations.",
            "estimated_time": "45-60 minutes",
            "questions": [
                {
                    "id": 1,
                    "question_text": "I focus on facts and data when making decisions",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 2,
                    "question_text": "I prefer direct and to-the-point communication",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 3,
                    "question_text": "I enjoy expressing enthusiasm and excitement",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 4,
                    "question_text": "I prioritize building relationships and trust",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 5,
                    "question_text": "I take time to analyze all options before deciding",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 6,
                    "question_text": "I push for quick decisions and action",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 7,
                    "question_text": "I use gestures and facial expressions to communicate",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 8,
                    "question_text": "I listen carefully to others' perspectives",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 9,
                    "question_text": "I value accuracy and precision in work",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 10,
                    "question_text": "I prefer to lead rather than follow",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 11,
                    "question_text": "I enjoy being the center of attention",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 12,
                    "question_text": "I avoid conflict and seek harmony",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 13,
                    "question_text": "I question assumptions and challenge ideas",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 14,
                    "question_text": "I set high standards for myself and others",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 15,
                    "question_text": "I'm comfortable with emotional expression",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 16,
                    "question_text": "I'm supportive of others' development",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 17,
                    "question_text": "I prefer written communication over verbal",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 18,
                    "question_text": "I'm competitive and achievement-oriented",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 19,
                    "question_text": "I inspire others with my vision",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 20,
                    "question_text": "I'm patient and understanding with others",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 21,
                    "question_text": "I research thoroughly before presenting ideas",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 22,
                    "question_text": "I take charge in group situations",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 23,
                    "question_text": "I network easily with new people",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 24,
                    "question_text": "I prioritize group consensus over individual preferences",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 25,
                    "question_text": "I'm skeptical of claims without evidence",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 26,
                    "question_text": "I'm comfortable making tough decisions",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 27,
                    "question_text": "I use storytelling to make points",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 28,
                    "question_text": "I'm supportive and helpful to colleagues",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 29,
                    "question_text": "I maintain professional boundaries",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 30,
                    "question_text": "I prefer objective analysis over subjective opinions",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 31,
                    "question_text": "I'm results-focused and bottom-line oriented",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 32,
                    "question_text": "I'm comfortable with public speaking",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 33,
                    "question_text": "I create inclusive environments for everyone",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 34,
                    "question_text": "I notice small details that others miss",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 35,
                    "question_text": "I'm decisive under pressure",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 36,
                    "question_text": "I enjoy creative brainstorming sessions",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 37,
                    "question_text": "I mediate conflicts between others",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 38,
                    "question_text": "I prefer structured approaches to problems",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 39,
                    "question_text": "I'm comfortable taking calculated risks",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 40,
                    "question_text": "I adapt easily to changing circumstances",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 41,
                    "question_text": "I maintain long-term professional relationships",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 42,
                    "question_text": "I value quality over speed in my work",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 43,
                    "question_text": "I'm persistent in overcoming obstacles",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 44,
                    "question_text": "I express opinions freely and confidently",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 45,
                    "question_text": "I'm sensitive to others' feelings and needs",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 46,
                    "question_text": "I document processes and procedures",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 47,
                    "question_text": "I delegate responsibilities effectively",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 48,
                    "question_text": "I use humor to build rapport",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 49,
                    "question_text": "I'm receptive to feedback and suggestions",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 50,
                    "question_text": "I prefer working independently",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 51,
                    "question_text": "I'm comfortable with confrontation",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 52,
                    "question_text": "I share personal experiences appropriately",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 53,
                    "question_text": "I'm accommodating of others' schedules",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 54,
                    "question_text": "I set measurable goals and track progress",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 55,
                    "question_text": "I'm motivated by recognition and rewards",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 56,
                    "question_text": "I'm charismatic and persuasive",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 57,
                    "question_text": "I'm patient with difficult team members",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 58,
                    "question_text": "I analyze risks before taking action",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 59,
                    "question_text": "I'm comfortable making unpopular decisions",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 60,
                    "question_text": "I energize others with my enthusiasm",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 61,
                    "question_text": "I prioritize team success over individual achievement",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 62,
                    "question_text": "I prefer concrete examples over abstract concepts",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 63,
                    "question_text": "I'm driven by deadlines and time pressure",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 64,
                    "question_text": "I'm expressive with my emotions",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 65,
                    "question_text": "I'm gentle in my feedback to others",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 66,
                    "question_text": "I prefer measurable outcomes",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 67,
                    "question_text": "I'm comfortable with authority and responsibility",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 68,
                    "question_text": "I'm approachable and easy to talk to",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 69,
                    "question_text": "I'm methodical in my problem-solving approach",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 70,
                    "question_text": "I'm ambitious and career-focused",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 71,
                    "question_text": "I'm spontaneous and flexible in plans",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 72,
                    "question_text": "I'm considerate of others' work-life balance",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 73,
                    "question_text": "I verify facts before accepting them",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 74,
                    "question_text": "I'm comfortable negotiating deals",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 75,
                    "question_text": "I'm open to constructive criticism",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 76,
                    "question_text": "I maintain detailed records of my work",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 77,
                    "question_text": "I think strategically about long-term goals",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 78,
                    "question_text": "I enjoy mentoring junior colleagues",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 79,
                    "question_text": "I'm comfortable making difficult choices",
                    "style": "Expressive",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 80,
                    "question_text": "I value work-life balance highly",
                    "style": "Amiable",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 81,
                    "question_text": "I'm systematic in my approach to challenges",
                    "style": "Analytical",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                },
                {
                    "id": 82,
                    "question_text": "I'm driven by achievement and success",
                    "style": "Driving",
                    "options": [
                        {"text": "Strongly Disagree", "value": "1"},
                        {"text": "Disagree", "value": "2"},
                        {"text": "Neutral", "value": "3"},
                        {"text": "Agree", "value": "4"},
                        {"text": "Strongly Agree", "value": "5"}
                    ]
                }
            ]
            "styles_info": {
                "analytical": {
                    "name": "Analytical",
                    "description": "Serious, systematic, task-oriented. Analyticals value accuracy, logic, and thoroughness."
                },
                "driver": {
                    "name": "Driver",
                    "description": "Direct, decisive, independent. Drivers value results, efficiency, and taking control."
                },
                "amiable": {
                    "name": "Amiable",
                    "description": "Supportive, patient, relationship-oriented. Amiables value harmony, cooperation, and personal relationships."
                },
                "expressive": {
                    "name": "Expressive",
                    "description": "Animated, enthusiastic, people-oriented. Expressives value recognition, relationships, and creative expression."
                }
            },
            "scoring_method": "Social Styles is measured along two dimensions: Assertiveness (low to high) and Responsiveness (low to high), creating four quadrants of behavioral styles."
        }

        return {
            "success": True,
            "assessment": social_styles_assessment,
            "message": "Social Styles assessment questions loaded successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load Social Styles assessment questions: {str(e)}"
        )

@router.get("/assessment-questions/strengthsfinder")
async def get_strengthsfinder_assessment_questions():
    """
    Get StrengthsFinder assessment questions from backend

    Returns a StrengthsFinder (CliftonStrengths) assessment with questions
    designed to identify natural talents and strengths
    """
    try:
        strengthsfinder_assessment = {
            "id": "strengthsfinder-standard",
            "title": "StrengthsFinder Assessment",
            "description": "Discover your natural talents and strengths through the StrengthsFinder assessment. This tool helps you identify your areas of greatest potential for excellence.",
            "instructions": "For each question, choose the statement that best describes you. There are no right or wrong answers - select what feels most authentic to you.",
            "estimated_time": "15-25 minutes",
            "questions": [
                {
                    "id": 1,
                    "question_text": "I feel most energized when:",
                    "type": "Energy",
                    "options": [
                        {"text": "Achieving goals and crossing items off my list", "value": "achiever"},
                        {"text": "Learning new information and skills", "value": "learner"},
                        {"text": "Thinking deeply about complex topics", "value": "intellection"},
                        {"text": "Connecting with interesting people", "value": "relator"}
                    ]
                },
                {
                    "id": 2,
                    "question_text": "In team situations, I naturally:",
                    "type": "Teamwork",
                    "options": [
                        {"text": "Take charge and organize the work", "value": "arranger"},
                        {"text": "Bring out the best in others", "value": "developer"},
                        {"text": "Build consensus and harmony", "value": "harmony"},
                        {"text": "Encourage and motivate the team", "value": "positivity"}
                    ]
                },
                {
                    "id": 3,
                    "question_text": "When facing challenges, I tend to:",
                    "type": "Problem Solving",
                    "options": [
                        {"text": "Analyze all possible solutions carefully", "value": "analytical"},
                        {"text": "Take decisive action to fix things", "value": "activator"},
                        {"text": "Stay optimistic and find opportunities", "value": "positivity"},
                        {"text": "Focus on what's most important", "value": "focus"}
                    ]
                },
                {
                    "id": 4,
                    "question_text": "I am most satisfied when I can:",
                    "type": "Satisfaction",
                    "options": [
                        {"text": "Complete projects with excellence", "value": "responsibility"},
                        {"text": "Express myself creatively", "value": "ideation"},
                        {"text": "Win or achieve success", "value": "competition"},
                        {"text": "Make a positive difference", "value": "belief"}
                    ]
                },
                {
                    "id": 5,
                    "question_text": "My natural approach to communication is:",
                    "type": "Communication",
                    "options": [
                        {"text": "Clear, logical, and well-structured", "value": "discipline"},
                        {"text": "Enthusiastic and persuasive", "value": "communication"},
                        {"text": "Warm and relationship-focused", "value": "relator"},
                        {"text": "Thoughtful and deep", "value": "intellection"}
                    ]
                },
                {
                    "id": 6,
                    "question_text": "I am most passionate about:",
                    "type": "Values",
                    "options": [
                        {"text": "Making the world better", "value": "belief"},
                        {"text": "Achieving personal excellence", "value": "achievement"},
                        {"text": "Building strong relationships", "value": "relator"},
                        {"text": "Creating and innovating", "value": "ideation"}
                    ]
                },
                {
                    "id": 7,
                    "question_text": "When starting new projects, I:",
                    "type": "Initiation",
                    "options": [
                        {"text": "Jump right in and get started", "value": "activator"},
                        {"text": "Plan everything carefully first", "value": "discipline"},
                        {"text": "Consider how it affects people", "value": "empathy"},
                        {"text": "Think of creative possibilities", "value": "ideation"}
                    ]
                },
                {
                    "id": 8,
                    "question_text": "I learn best when:",
                    "type": "Learning",
                    "options": [
                        {"text": "I can study topics in depth", "value": "learner"},
                        {"text": "I can immediately apply what I learn", "value": "activator"},
                        {"text": "I can discuss ideas with others", "value": "communication"},
                        {"text": "I can observe and analyze patterns", "value": "input"}
                    ]
                }
            ],
            "domains_info": {
                "Executing": {
                    "description": "Talents that help you get things done and achieve results",
                    "themes": ["Achiever", "Arranger", "Belief", "Consistency", "Deliberative", "Discipline", "Focus", "Responsibility", "Restorative"]
                },
                "Influencing": {
                    "description": "Talents that help you influence others and sell ideas",
                    "themes": ["Activator", "Command", "Communication", "Competition", "Maximizer", "Self-Assurance", "Significance", "Woo"]
                },
                "Relationship Building": {
                    "description": "Talents that help you build strong relationships and teams",
                    "themes": ["Adaptability", "Connectedness", "Developer", "Empathy", "Harmony", "Includer", "Individualization", "Positivity", "Relator"]
                },
                "Strategic Thinking": {
                    "description": "Talents that help you absorb information, think critically, and plan ahead",
                    "themes": ["Analytical", "Context", "Futuristic", "Ideation", "Input", "Intellection", "Learner", "Strategic"]
                }
            },
            "scoring_method": "StrengthsFinder identifies your most dominant talent themes based on your natural patterns of thinking, feeling, and behaving. Focus on developing your top strengths for greatest impact."
        }

        return {
            "success": True,
            "assessment": strengthsfinder_assessment,
            "message": "StrengthsFinder assessment questions loaded successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load StrengthsFinder assessment questions: {str(e)}"
        )

@router.post("/assessment-results", status_code=status.HTTP_201_CREATED)
async def create_assessment_result(
    result_data: AssessmentResultCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create and store assessment result

    Supports all assessment types:
    - MBTI personality assessment
    - Big Five OCEAN model
    - DISC behavioral assessment
    - Enneagram personality types
    - Custom assessments
    """
    try:
        # Add user info
        result_dict = result_data.dict()
        result_dict["user_id"] = str(current_user.id) if current_user else "anonymous"

        # Process the assessment results
        processed_result = await process_assessment_result(result_dict)
        result_dict["processed_result"] = processed_result

        # Store the result
        stored_result = AssessmentResultStorage.store_result(result_dict)

        return {
            "success": True,
            "result_id": stored_result["id"],
            "assessment_type": result_dict["assessment_type"],
            "results": processed_result,
            "created_at": stored_result["created_at"],
            "message": f"{result_dict['assessment_type'].title()} assessment results stored successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store assessment results: {str(e)}"
        )

@router.get("/assessment-results")
async def get_assessment_results(
    assessment_type: Optional[str] = Query(None, description="Filter by assessment type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's assessment results

    Returns all assessment results for the current user with optional filtering
    """
    try:
        user_id = str(current_user.id) if current_user else "anonymous"
        results = AssessmentResultStorage.get_user_results(
            user_id=user_id,
            assessment_type=assessment_type,
            limit=limit
        )

        # Format results for frontend consumption
        formatted_results = []
        for result in results:
            processed_data = result.get("processed_result", {})
            processed_data.update({
                "result_id": result["id"],
                "assessment_type": result["assessment_type"],
                "assessment_id": result.get("assessment_id"),
                "completed_at": result["created_at"],
                "responses_count": len(result.get("responses", {})),
                "updated_at": result["updated_at"]
            })
            formatted_results.append(processed_data)

        return {
            "success": True,
            "count": len(formatted_results),
            "results": formatted_results,
            "user_id": user_id,
            "filters": {
                "assessment_type": assessment_type,
                "limit": limit
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve assessment results: {str(e)}"
        )

@router.get("/assessment-results/{result_id}")
async def get_assessment_result(
    result_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get specific assessment result by ID"""
    try:
        result = AssessmentResultStorage.get_result(result_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Assessment result not found"
            )

        # Check if user owns this result
        user_id = str(current_user.id) if current_user else "anonymous"
        if result.get("user_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to access this result"
            )

        # Format complete result
        processed_data = result.get("processed_result", {})
        processed_data.update({
            "result_id": result["id"],
            "assessment_type": result["assessment_type"],
            "assessment_id": result.get("assessment_id"),
            "completed_at": result["created_at"],
            "updated_at": result["updated_at"],
            "responses": result.get("responses", {}),
            "metadata": result.get("metadata", {}),
            "raw_type": result.get("raw_type")
        })

        return {
            "success": True,
            "result": processed_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve assessment result: {str(e)}"
        )

@router.put("/assessment-results/{result_id}")
async def update_assessment_result(
    result_id: int,
    update_data: AssessmentResultUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update assessment result (metadata, notes, etc.)"""
    try:
        result = AssessmentResultStorage.get_result(result_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Assessment result not found"
            )

        # Check ownership
        user_id = str(current_user.id) if current_user else "anonymous"
        if result.get("user_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this result"
            )

        # Update result
        update_dict = update_data.dict(exclude_unset=True)
        updated_result = AssessmentResultStorage.update_result(result_id, update_dict)

        return {
            "success": True,
            "result_id": result_id,
            "updated_at": updated_result["updated_at"],
            "message": "Assessment result updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update assessment result: {str(e)}"
        )

@router.delete("/assessment-results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment_result(
    result_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete assessment result"""
    try:
        result = AssessmentResultStorage.get_result(result_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Assessment result not found"
            )

        # Check ownership
        user_id = str(current_user.id) if current_user else "anonymous"
        if result.get("user_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this result"
            )

        # Delete result
        success = AssessmentResultStorage.delete_result(result_id)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete assessment result"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete assessment result: {str(e)}"
        )

@router.get("/assessment-analytics")
async def get_assessment_analytics(
    assessment_type: Optional[str] = Query(None, description="Filter by assessment type"),
    current_user: User = Depends(get_current_active_user)
):
    """Get analytics for user's assessment results"""
    try:
        user_id = str(current_user.id) if current_user else "anonymous"
        analytics = AssessmentResultStorage.get_analytics(
            user_id=user_id,
            assessment_type=assessment_type
        )

        return {
            "success": True,
            "analytics": analytics,
            "user_id": user_id,
            "filters": {
                "assessment_type": assessment_type
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve assessment analytics: {str(e)}"
        )