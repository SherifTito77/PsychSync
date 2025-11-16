"""
File: app/services/assessment_service.py
Assessment service with Redis caching implementation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.core.cache import cached, cache_delete_pattern
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# ASSESSMENT RETRIEVAL (WITH CACHING)
# =============================================================================

@cached(expire=3600, key_prefix="assessment")  # Cache for 1 hour
def get_assessment_by_id(db: Session, assessment_id: int) -> Optional[dict]:
    """
    Get assessment by ID with caching
    
    Args:
        db: Database session
        assessment_id: Assessment ID
    
    Returns:
        Assessment dictionary or None
    """
    assessment = result = await db.execute(query)
        return result.scalars().all()
    if assessment:
        return assessment_to_dict(assessment)
    return None


@cached(expire=600, key_prefix="assessment")  # Cache for 10 minutes
def get_user_assessments(db: Session, user_id: int) -> List[dict]:
    """
    Get user's assessments with caching
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        List of assessment dictionaries
    """
    assessments = result = await db.execute(query)
        return result.scalars().all()
    return [assessment_to_dict(a) for a in assessments]


@cached(expire=600, key_prefix="assessment")
def get_organization_assessments(db: Session, organization_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
    """
    Get organization's assessments with caching
    
    Args:
        db: Database session
        organization_id: Organization ID
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of assessment dictionaries
    """
    assessments = db.query(Assessment).filter(
        Assessment.organization_id == organization_id
    ).offset(skip).limit(limit).all()
    
    return [assessment_to_dict(a) for a in assessments]


@cached(expire=3600, key_prefix="assessment")
def get_assessment_results(db: Session, assessment_id: int) -> Optional[dict]:
    """
    Get assessment results with caching (expensive calculation)
    
    Args:
        db: Database session
        assessment_id: Assessment ID
    
    Returns:
        Assessment results dictionary or None
    """
    assessment = result = await db.execute(query)
        return result.scalars().all()
    
    if not assessment:
        return None
    
    # Get all responses for this assessment
    responses = result = await db.execute(query)
        return result.scalars().all()
    
    # Calculate results (this could be expensive)
    results = {
        "assessment_id": assessment.id,
        "user_id": assessment.user_id,
        "framework": assessment.framework_code,
        "status": assessment.status,
        "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
        "scores": calculate_assessment_scores(assessment, responses),
        "insights": generate_assessment_insights(assessment, responses),
        "recommendations": get_assessment_recommendations(assessment, responses),
        "response_count": len(responses)
    }
    
    return results


# =============================================================================
# ASSESSMENT CREATION AND UPDATE (WITH CACHE INVALIDATION)
# =============================================================================

def create_assessment(db: Session, user_id: int, framework_code: str, organization_id: Optional[int] = None) -> Assessment:
    """
    Create new assessment and invalidate related caches
    
    Args:
        db: Database session
        user_id: User ID
        framework_code: Assessment framework code (e.g., 'MBTI', 'BIG_FIVE')
        organization_id: Organization ID (optional)
    
    Returns:
        Created Assessment object
    """
    assessment = Assessment(
        user_id=user_id,
        framework_code=framework_code,
        organization_id=organization_id,
        status='in_progress',
        started_at=datetime.utcnow()
    )
    
    db.add(assessment)
        await db.commit()
    await db.refresh(assessment)
    
    # Invalidate user assessments cache
    cache_delete_pattern(f"assessment:get_user_assessments:*{user_id}*")
    
    if organization_id:
        cache_delete_pattern(f"assessment:get_organization_assessments:*{organization_id}*")
    
    logger.info(f"Created assessment ID: {assessment.id} for user: {user_id}")
    
    return assessment


def update_assessment(db: Session, assessment_id: int, update_data: dict) -> Optional[Assessment]:
    """
    Update assessment and invalidate caches
    
    Args:
        db: Database session
        assessment_id: Assessment ID
        update_data: Dictionary of fields to update
    
    Returns:
        Updated Assessment object or None
    """
    assessment = result = await db.execute(query)
        return result.scalars().all()
    
    if not assessment:
        return None
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(assessment, field):
            setattr(assessment, field, value)
    
    await db.commit()
    await db.refresh(assessment)
    
    # Invalidate caches
    cache_delete_pattern(f"assessment:get_assessment_by_id:*{assessment_id}*")
    cache_delete_pattern(f"assessment:get_assessment_results:*{assessment_id}*")
    cache_delete_pattern(f"assessment:get_user_assessments:*{assessment.user_id}*")
    
    if assessment.organization_id:
        cache_delete_pattern(f"assessment:get_organization_assessments:*{assessment.organization_id}*")
    
    logger.info(f"Updated assessment ID: {assessment_id}")
    
    return assessment


def complete_assessment(db: Session, assessment_id: int) -> Optional[Assessment]:
    """
    Mark assessment as completed and invalidate caches
    
    Args:
        db: Database session
        assessment_id: Assessment ID
    
    Returns:
        Updated Assessment object or None
    """
    assessment = result = await db.execute(query)
        return result.scalars().all()
    
    if not assessment:
        return None
    
    assessment.status = 'completed'
    assessment.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(assessment)
    
    # Invalidate all related caches
    cache_delete_pattern(f"assessment:get_assessment_by_id:*{assessment_id}*")
    cache_delete_pattern(f"assessment:get_assessment_results:*{assessment_id}*")
    cache_delete_pattern(f"assessment:get_user_assessments:*{assessment.user_id}*")
    
    if assessment.organization_id:
        cache_delete_pattern(f"assessment:get_organization_assessments:*{assessment.organization_id}*")
    
    logger.info(f"Completed assessment ID: {assessment_id}")
    
    return assessment


def submit_assessment_response(db: Session, assessment_id: int, question_id: int, response_value: Any) -> Response:
    """
    Submit response and invalidate related caches
    
    Args:
        db: Database session
        assessment_id: Assessment ID
        question_id: Question ID
        response_value: Response value
    
    Returns:
        Created Response object
    """
    # Check if response already exists
    existing_response = result = await db.execute(query)
        return result.scalars().all()
    
    if existing_response:
        # Update existing response
        existing_response.response_value = response_value
        existing_response.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(existing_response)
        response = existing_response
    else:
        # Create new response
        response = Response(
            assessment_id=assessment_id,
            question_id=question_id,
            response_value=response_value
        )
        db.add(response)
        await db.commit()
        await db.refresh(response)
    
    # Invalidate assessment caches
    cache_delete_pattern(f"assessment:get_assessment_by_id:*{assessment_id}*")
    cache_delete_pattern(f"assessment:get_assessment_results:*{assessment_id}*")
    
    logger.info(f"Submitted response for assessment ID: {assessment_id}, question ID: {question_id}")
    
    return response


def delete_assessment(db: Session, assessment_id: int) -> bool:
    """
    Delete assessment and invalidate caches
    
    Args:
        db: Database session
        assessment_id: Assessment ID
    
    Returns:
        True if successful, False otherwise
    """
    assessment = result = await db.execute(query)
        return result.scalars().all()
    
    if not assessment:
        return False
    
    user_id = assessment.user_id
    organization_id = assessment.organization_id
    
    # Delete assessment
    db.delete(assessment)
    await db.commit()
    
    # Invalidate caches
    cache_delete_pattern(f"assessment:get_assessment_by_id:*{assessment_id}*")
    cache_delete_pattern(f"assessment:get_assessment_results:*{assessment_id}*")
    cache_delete_pattern(f"assessment:get_user_assessments:*{user_id}*")
    
    if organization_id:
        cache_delete_pattern(f"assessment:get_organization_assessments:*{organization_id}*")
    
    logger.info(f"Deleted assessment ID: {assessment_id}")
    
    return True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def assessment_to_dict(assessment: Assessment) -> dict:
    """
    Convert Assessment object to dictionary for caching
    
    Args:
        assessment: Assessment object
    
    Returns:
        Assessment dictionary
    """
    return {
        "id": assessment.id,
        "user_id": assessment.user_id,
        "organization_id": assessment.organization_id,
        "framework_code": assessment.framework_code,
        "status": assessment.status,
        "started_at": assessment.started_at.isoformat() if assessment.started_at else None,
        "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
        "created_at": assessment.created_at.isoformat() if hasattr(assessment, 'created_at') and assessment.created_at else None
    }


def calculate_assessment_scores(assessment: Assessment, responses: List[Response]) -> dict:
    """
    Calculate assessment scores based on framework
    This is a placeholder - implement based on your assessment logic
    
    Args:
        assessment: Assessment object
        responses: List of Response objects
    
    Returns:
        Dictionary of scores
    """
    # TODO: Implement actual scoring logic based on framework_code
    framework = assessment.framework_code
    
    if framework == 'MBTI':
        return calculate_mbti_scores(responses)
    elif framework == 'BIG_FIVE':
        return calculate_big_five_scores(responses)
    elif framework == 'ENNEAGRAM':
        return calculate_enneagram_scores(responses)
    else:
        return {"total_score": len(responses)}


def generate_assessment_insights(assessment: Assessment, responses: List[Response]) -> List[str]:
    """
    Generate insights from assessment responses
    This is a placeholder - implement based on your business logic
    
    Args:
        assessment: Assessment object
        responses: List of Response objects
    
    Returns:
        List of insight strings
    """
    # TODO: Implement actual insight generation
    insights = [
        "Assessment completed successfully",
        f"Total responses: {len(responses)}",
        f"Framework: {assessment.framework_code}"
    ]
    return insights


def get_assessment_recommendations(assessment: Assessment, responses: List[Response]) -> List[str]:
    """
    Get recommendations based on assessment results
    This is a placeholder - implement based on your business logic
    
    Args:
        assessment: Assessment object
        responses: List of Response objects
    
    Returns:
        List of recommendation strings
    """
    # TODO: Implement actual recommendation logic
    recommendations = [
        "Continue personal development",
        "Consider team collaboration exercises",
        "Review assessment results with mentor"
    ]
    return recommendations


# Placeholder scoring functions - implement based on your actual logic
def calculate_mbti_scores(responses: List[Response]) -> dict:
    """Calculate MBTI scores"""
    return {
        "E_I": 0.0,  # Extraversion vs Introversion
        "S_N": 0.0,  # Sensing vs Intuition
        "T_F": 0.0,  # Thinking vs Feeling
        "J_P": 0.0   # Judging vs Perceiving
    }


def calculate_big_five_scores(responses: List[Response]) -> dict:
    """Calculate Big Five scores"""
    return {
        "openness": 0.0,
        "conscientiousness": 0.0,
        "extraversion": 0.0,
        "agreeableness": 0.0,
        "neuroticism": 0.0
    }


def calculate_enneagram_scores(responses: List[Response]) -> dict:
    """Calculate Enneagram scores"""
    return {
        "type_1": 0.0,
        "type_2": 0.0,
        "type_3": 0.0,
        "type_4": 0.0,
        "type_5": 0.0,
        "type_6": 0.0,
        "type_7": 0.0,
        "type_8": 0.0,
        "type_9": 0.0
    }