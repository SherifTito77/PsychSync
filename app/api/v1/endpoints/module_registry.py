"""
Module Registry API — admin-only endpoints exposing the module classification registry.
"""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_current_admin_user
from app.core.module_registry import (
    MODULE_REGISTRY,
    ModuleClassification,
    get_modules_by_category,
    get_modules_by_classification,
    get_registry_summary,
)

router = APIRouter(prefix="/modules", tags=["Module Registry"])


@router.get("/registry")
async def get_registry(
    classification: ModuleClassification | None = None,
    category: str | None = None,
    current_user=Depends(get_current_admin_user),
):
    """Returns full module registry with classifications.

    Optionally filter by classification or category.
    Admin-only.
    """
    if classification and category:
        modules = [
            m
            for m in get_modules_by_classification(classification)
            if m.category == category
        ]
    elif classification:
        modules = get_modules_by_classification(classification)
    elif category:
        modules = get_modules_by_category(category)
    else:
        modules = list(MODULE_REGISTRY.values())

    return {
        "total": len(modules),
        "modules": [asdict(m) for m in modules],
    }


@router.get("/registry/summary")
async def get_registry_summary_endpoint(
    current_user=Depends(get_current_admin_user),
):
    """Returns counts by classification and category.

    Admin-only.
    """
    return get_registry_summary()
