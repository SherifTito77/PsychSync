"""
Product Management Prompts API Endpoints

Provides REST API access to 50 curated product management prompts.
Supports prompt retrieval, execution, tracking, and workflow management.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.structured_logging import get_logger
from app.db.models.user import User
from app.services.product_management_service import ProductManagementPromptsService

logger = get_logger(__name__)

router = APIRouter(prefix="/product-management", tags=["Product Management Prompts"])


# ============================================================================
# Request/Response Models
# ============================================================================


class PromptResponse(BaseModel):
    """Response model for a single prompt."""

    id: str
    prompt: str
    type: str
    complexity: str
    estimated_time: str
    outputs: List[str]
    related_prompts: List[str]
    use_cases: List[str]
    category: Optional[Dict[str, str]] = None


class CategoryResponse(BaseModel):
    """Response model for a prompt category."""

    id: str
    name: str
    description: str
    icon: str
    prompt_count: int


class PromptExecutionRequest(BaseModel):
    """Request model for executing a prompt."""

    prompt_id: str = Field(..., description="Prompt identifier (e.g., 'rs_001')")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for execution"
    )
    use_ai: bool = Field(False, description="Use AI enhancement for output generation")


class PromptExecutionResponse(BaseModel):
    """Response model for prompt execution result."""

    prompt: PromptResponse
    execution_id: int
    executed_at: str
    use_ai: bool
    ai_suggestion: Optional[str] = None


class PromptWorkflowRequest(BaseModel):
    """Request model for creating a custom workflow."""

    name: str
    description: Optional[str] = None
    goal: str
    prompt_sequence: List[str]
    estimated_total_time: Optional[str] = None
    is_public: bool = False


class PromptFavoriteRequest(BaseModel):
    """Request model for adding to favorites."""

    prompt_id: str


class PromptRatingRequest(BaseModel):
    """Request model for rating a prompt execution."""

    quality_rating: int = Field(..., ge=1, le=5, description="Quality rating from 1-5")
    feedback: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/prompts", response_model=Dict[str, Any])
async def get_all_prompts(
    category: Optional[str] = Query(None, description="Filter by category ID"),
    complexity: Optional[str] = Query(
        None, description="Filter by complexity (low, medium, high)"
    ),
    type: Optional[str] = Query(
        None, description="Filter by type (strategic, tactical, etc.)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all prompts with optional filtering.

    Parameters:
    - category: Filter by category (roadmap_strategy, user_experience, growth_monetization, analytics_metrics, operations_processes)
    - complexity: Filter by complexity level (low, medium, high)
    - type: Filter by prompt type (strategic, tactical, analytical, technical, creative, experimental)

    Returns filtered list of prompts.
    """
    service = ProductManagementPromptsService(db)

    if category:
        prompts = await service.get_prompts_by_category(category, complexity, type)
    else:
        # Get prompts from all categories
        all_prompts = []
        categories = await service.get_all_categories()
        for cat in categories:
            cat_prompts = await service.get_prompts_by_category(
                cat["id"], complexity, type
            )
            all_prompts.extend(cat_prompts)
        prompts = all_prompts

    logger.info(f"User {current_user.id} retrieved {len(prompts)} prompts")

    return {
        "total": len(prompts),
        "prompts": prompts,
        "filters": {"category": category, "complexity": complexity, "type": type},
    }


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific prompt by ID.

    Returns full prompt details including category context.
    """
    service = ProductManagementPromptsService(db)
    prompt = await service.get_prompt_by_id(prompt_id)

    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt not found: {prompt_id}")

    logger.info(f"User {current_user.id} retrieved prompt {prompt_id}")

    return prompt


@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get all prompt categories.

    Returns list of categories with prompt counts.
    """
    service = ProductManagementPromptsService(db)
    categories = await service.get_all_categories()

    logger.info(f"User {current_user.id} retrieved {len(categories)} categories")

    return categories


@router.get("/categories/{category_id}/prompts", response_model=List[PromptResponse])
async def get_category_prompts(
    category_id: str,
    complexity: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all prompts in a specific category.

    Parameters:
    - complexity: Filter by complexity level
    - type: Filter by prompt type
    """
    service = ProductManagementPromptsService(db)

    try:
        prompts = await service.get_prompts_by_category(category_id, complexity, type)
        logger.info(
            f"User {current_user.id} retrieved {len(prompts)} prompts from category {category_id}"
        )
        return prompts
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prompts/{prompt_id}/related", response_model=List[PromptResponse])
async def get_related_prompts(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get prompts related to a specific prompt.

    Returns prompts that are commonly used together or cover similar topics.
    """
    service = ProductManagementPromptsService(db)
    related = await service.get_related_prompts(prompt_id)

    logger.info(
        f"User {current_user.id} retrieved {len(related)} related prompts for {prompt_id}"
    )

    return related


@router.post("/prompts/execute", response_model=PromptExecutionResponse)
async def execute_prompt(
    request: PromptExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute a prompt and track the execution.

    Creates an execution record and optionally generates AI-enhanced output.

    Parameters:
    - prompt_id: The prompt to execute
    - context: Additional context for prompt execution
    - use_ai: Whether to use AI enhancement
    """
    service = ProductManagementPromptsService(db)

    try:
        result = await service.execute_prompt(
            prompt_id=request.prompt_id,
            user_id=current_user.id,
            context=request.context,
            use_ai=request.use_ai,
        )

        # Debug logging
        logger.info(
            f"User {current_user.id} executed prompt {request.prompt_id} (AI: {request.use_ai})"
        )
        logger.debug(f"Execution result keys: {list(result.keys())}")
        logger.debug(f"Prompt in result: {result.get('prompt')}")
        if "prompt" in result:
            logger.debug(f"Prompt keys: {list(result['prompt'].keys())}")
            logger.debug(f"Has outputs: {'outputs' in result['prompt']}")
            if "outputs" in result["prompt"]:
                logger.debug(f"Outputs: {result['prompt']['outputs']}")

        return result

    except ValueError as e:
        logger.error(f"ValueError executing prompt {request.prompt_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/prompts/search/{query}", response_model=List[PromptResponse])
async def search_prompts(
    query: str,
    category: Optional[str] = Query(
        None, description="Limit search to specific category"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search prompts by keyword.

    Searches in prompt text, use cases, and expected outputs.
    """
    service = ProductManagementPromptsService(db)
    results = await service.search_prompts(query, category)

    logger.info(
        f"User {current_user.id} searched for '{query}', found {len(results)} results"
    )

    return results


@router.get("/use-cases/{use_case}", response_model=List[PromptResponse])
async def get_prompts_by_use_case(
    use_case: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get prompts relevant to a specific use case.

    Examples: 'Quarterly planning', 'Feature development', 'Enterprise expansion'
    """
    service = ProductManagementPromptsService(db)
    prompts = await service.get_prompts_by_use_case(use_case)

    logger.info(
        f"User {current_user.id} retrieved {len(prompts)} prompts for use case: {use_case}"
    )

    return prompts


@router.get("/workflows/{goal}", response_model=List[PromptResponse])
async def get_workflow_for_goal(
    goal: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a suggested workflow of prompts for a specific goal.

    Supported goals:
    - Feature launch
    - Retention improvement
    - Enterprise expansion
    - Quarterly planning

    Returns ordered list of prompts to execute.
    """
    service = ProductManagementPromptsService(db)
    workflow = await service.get_prompt_workflow(goal)

    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"No workflow found for goal: {goal}. Try: feature_launch, retention_improvement, enterprise_expansion, quarterly_planning",
        )

    logger.info(f"User {current_user.id} retrieved workflow for goal: {goal}")

    return workflow


@router.get("/executions/history")
async def get_execution_history(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    prompt_id: Optional[str] = Query(None, description="Filter by prompt ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get historical prompt executions for the current user.

    Parameters:
    - limit: Maximum number of results (default: 50)
    - prompt_id: Filter by specific prompt
    """
    service = ProductManagementPromptsService(db)
    history = await service.get_execution_history(
        user_id=current_user.id, prompt_id=prompt_id, limit=limit
    )

    logger.info(f"User {current_user.id} retrieved {len(history)} execution records")

    return {"total": len(history), "executions": history}


@router.post("/executions/{execution_id}/rate")
async def rate_execution(
    execution_id: int,
    request: PromptRatingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rate a prompt execution.

    Allows users to provide feedback on the quality of prompt outputs.
    """
    from sqlalchemy import select, update

    from app.db.models.product_management import PromptExecution

    # Get execution
    query = select(PromptExecution).where(
        PromptExecution.id == execution_id, PromptExecution.user_id == current_user.id
    )
    result = await db.execute(query)
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Update rating
    execution.quality_rating = request.quality_rating
    execution.feedback = request.feedback

    await db.commit()

    logger.info(
        f"User {current_user.id} rated execution {execution_id}: {request.quality_rating}/5"
    )

    return {
        "status": "success",
        "execution_id": execution_id,
        "rating": request.quality_rating,
    }


@router.get("/statistics")
async def get_usage_statistics(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get aggregated usage statistics for prompts.

    Returns metrics on prompt usage patterns.
    """
    service = ProductManagementPromptsService(db)
    stats = await service.get_usage_statistics()

    logger.info(f"User {current_user.id} retrieved usage statistics")

    return stats


# ============================================================================
# Favorites Management
# ============================================================================


@router.post("/favorites", response_model=Dict[str, Any])
async def add_favorite(
    request: PromptFavoriteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a prompt to favorites.

    Allows quick access to frequently used prompts.
    """
    from sqlalchemy import select

    from app.db.models.product_management import PromptFavorite

    # Check if already exists
    existing = await db.execute(
        select(PromptFavorite).where(
            PromptFavorite.user_id == current_user.id,
            PromptFavorite.prompt_id == request.prompt_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Prompt already in favorites")

    # Add to favorites
    favorite = PromptFavorite(user_id=current_user.id, prompt_id=request.prompt_id)
    db.add(favorite)
    await db.commit()

    logger.info(f"User {current_user.id} added prompt {request.prompt_id} to favorites")

    return {"status": "success", "message": "Prompt added to favorites"}


@router.get("/favorites", response_model=List[PromptResponse])
async def get_favorites(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get user's favorite prompts.

    Returns list of bookmarked prompts for quick access.
    """
    from sqlalchemy import select

    from app.db.models.product_management import PromptFavorite

    query = (
        select(PromptFavorite)
        .where(PromptFavorite.user_id == current_user.id)
        .order_by(PromptFavorite.created_at.desc())
    )

    result = await db.execute(query)
    favorites = result.scalars().all()

    # Get full prompt details
    service = ProductManagementPromptsService(db)
    prompt_details = []
    for fav in favorites:
        prompt = await service.get_prompt_by_id(fav.prompt_id)
        if prompt:
            prompt_details.append(prompt)

    logger.info(
        f"User {current_user.id} retrieved {len(prompt_details)} favorite prompts"
    )

    return prompt_details


@router.delete("/favorites/{prompt_id}")
async def remove_favorite(
    prompt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a prompt from favorites.
    """
    from sqlalchemy import delete, select

    from app.db.models.product_management import PromptFavorite

    query = select(PromptFavorite).where(
        PromptFavorite.user_id == current_user.id, PromptFavorite.prompt_id == prompt_id
    )
    result = await db.execute(query)
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    await db.execute(delete(PromptFavorite).where(PromptFavorite.id == favorite.id))
    await db.commit()

    logger.info(f"User {current_user.id} removed prompt {prompt_id} from favorites")

    return {"status": "success", "message": "Prompt removed from favorites"}
