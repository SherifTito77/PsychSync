# app/api/v1/endpoints/survey_translations.py
"""
Multi-Language Survey Translation Endpoints

Manage translations for survey/assessment content.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.security import get_current_user
from app.services.survey_translation_service import (
    SUPPORTED_LOCALES,
    survey_translation_service,
)

router = APIRouter(prefix="/survey-translations", tags=["survey-translations"])


class SetTranslationRequest(BaseModel):
    content_type: str = Field(
        ..., description="question, option, instruction, campaign_name"
    )
    content_id: UUID
    locale: str = Field(..., description="BCP 47 locale (e.g. es, fr, de, ja, zh-CN)")
    translated_text: str


class BulkTranslationItem(BaseModel):
    content_type: str
    content_id: str
    locale: str
    translated_text: str


class BulkTranslationRequest(BaseModel):
    translations: list[BulkTranslationItem]


class ResolveRequest(BaseModel):
    content_items: list[dict[str, str]] = Field(
        ..., description="[{content_type, content_id, fallback_text}]"
    )
    locale: str


@router.get("/locales", response_model=dict[str, str])
async def list_supported_locales():
    """List all supported locales."""
    return SUPPORTED_LOCALES


@router.get("/{organization_id}/available", response_model=list[dict[str, Any]])
async def get_available_locales(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List locales with translations for this organization."""
    return await survey_translation_service.get_available_locales(db, organization_id)


@router.post("/{organization_id}", response_model=dict[str, Any])
async def set_translation(
    organization_id: UUID,
    body: SetTranslationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Set or update a single translation."""
    return await survey_translation_service.set_translation(
        db,
        organization_id,
        body.content_type,
        body.content_id,
        body.locale,
        body.translated_text,
    )


@router.post("/{organization_id}/bulk", response_model=dict[str, Any])
async def set_translations_bulk(
    organization_id: UUID,
    body: BulkTranslationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Bulk upsert translations."""
    items = [t.model_dump() for t in body.translations]
    return await survey_translation_service.set_translations_bulk(
        db, organization_id, items
    )


@router.post("/{organization_id}/resolve", response_model=dict[str, str])
async def resolve_translations(
    organization_id: UUID,
    body: ResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Resolve translations for multiple content items at once."""
    return await survey_translation_service.resolve_content(
        db, organization_id, body.content_items, body.locale
    )


@router.get("/{organization_id}/coverage/{locale}", response_model=dict[str, Any])
async def get_coverage(
    organization_id: UUID,
    locale: str,
    content_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get translation coverage report for a locale."""
    return await survey_translation_service.get_translation_coverage(
        db, organization_id, locale, content_type
    )


@router.delete(
    "/{organization_id}/{content_type}/{content_id}/{locale}",
    response_model=dict[str, Any],
)
async def delete_translation(
    organization_id: UUID,
    content_type: str,
    content_id: UUID,
    locale: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a specific translation."""
    return await survey_translation_service.delete_translation(
        db, organization_id, content_type, content_id, locale
    )
