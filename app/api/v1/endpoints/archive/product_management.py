"""
Product Management Prompts API

Simple endpoint serving product management prompts from JSON file.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)

# Path to prompts file
PROMPTS_FILE = Path(
    "/Users/sheriftito/Downloads/psychsync/product_management_prompts/product_management_prompts.json"
)


def load_prompts():
    """Load prompts from JSON file"""
    try:
        with open(PROMPTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading prompts: {e}")
        return {"metadata": {"total_prompts": 0}, "categories": {}}


@router.get("/prompts")
async def get_prompts(
    category: Optional[str] = None,
    complexity: Optional[str] = None,
    type: Optional[str] = None,
):
    """Get all prompts with optional filtering"""
    data = load_prompts()
    all_prompts = []
    categories = data.get("categories", {})

    # Flatten prompts from all categories
    for cat_id, cat_data in categories.items():
        for prompt in cat_data.get("prompts", []):
            prompt_with_category = {
                **prompt,
                "category_id": cat_id,
                "category_name": cat_data.get("name", cat_id),
            }
            all_prompts.append(prompt_with_category)

    # Apply filters
    filtered = all_prompts
    if category:
        filtered = [p for p in filtered if p.get("category_id") == category]
    if complexity:
        filtered = [p for p in filtered if p.get("complexity") == complexity]
    if type:
        filtered = [p for p in filtered if p.get("type") == type]

    return {
        "total": len(filtered),
        "prompts": filtered,
        "filters": {"category": category, "complexity": complexity, "type": type},
    }


@router.get("/categories")
async def get_categories():
    """Get all prompt categories"""
    data = load_prompts()
    categories = []

    for cat_id, cat_data in data.get("categories", {}).items():
        categories.append(
            {
                "id": cat_id,
                "name": cat_data.get("name", cat_id),
                "description": cat_data.get("description", ""),
                "prompt_count": len(cat_data.get("prompts", [])),
            }
        )

    return categories


@router.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    """Get a specific prompt by ID"""
    data = load_prompts()
    categories = data.get("categories", {})

    for cat_id, cat_data in categories.items():
        for prompt in cat_data.get("prompts", []):
            if prompt.get("id") == prompt_id:
                return {
                    **prompt,
                    "category_id": cat_id,
                    "category_name": cat_data.get("name", cat_id),
                }

    raise HTTPException(status_code=404, detail="Prompt not found")


@router.get("/statistics")
async def get_statistics():
    """Get usage statistics (simplified version)"""
    data = load_prompts()
    return {
        "total_executions": 0,
        "most_used_prompts": [],
        "categories_count": len(data.get("categories", {})),
        "total_prompts": data.get("metadata", {}).get("total_prompts", 0),
    }


@router.get("/favorites")
async def get_favorites():
    """Get user's favorite prompts (simplified - returns empty list)"""
    # TODO: Implement proper favorites with database persistence
    return []


@router.post("/favorites")
async def add_favorite(request: dict):
    """Add a prompt to favorites (simplified - no-op)"""
    # TODO: Implement proper favorites with database persistence
    return {"status": "success", "message": "Favorite feature coming soon"}


@router.delete("/favorites/{prompt_id}")
async def remove_favorite(prompt_id: str):
    """Remove a prompt from favorites (simplified - no-op)"""
    # TODO: Implement proper favorites with database persistence
    return {"status": "success", "message": "Favorite feature coming soon"}


@router.post("/prompts/execute")
async def execute_prompt(request: dict):
    """Execute a prompt (returns guidance and structure)"""
    prompt_id = request.get("prompt_id")
    data = load_prompts()
    categories = data.get("categories", {})

    # Find the prompt
    prompt = None
    for cat_id, cat_data in categories.items():
        for p in cat_data.get("prompts", []):
            if p.get("id") == prompt_id:
                prompt = {
                    **p,
                    "category_id": cat_id,
                    "category_name": cat_data.get("name", cat_id),
                }
                break
        if prompt:
            break

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Return execution result with guidance
    return {
        "execution_id": "local_" + prompt_id,
        "prompt": prompt,
        "guidance": f"Follow these steps to complete: {prompt.get('prompt', '')}",
        "outputs": prompt.get("outputs", []),
        "estimated_time": prompt.get("estimated_time", "1-2 hours"),
        "next_steps": [
            "Document your findings",
            "Share with stakeholders",
            "Update project plans",
        ],
        "related_prompts": prompt.get("related_prompts", []),
    }
