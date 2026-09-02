# app/services/survey_translation_service.py
"""
Survey Translation Service

Manages multi-language translations for survey/assessment content.
Provides locale-aware text resolution with fallback to source language.

Supported content types:
  - question: assessment/survey question text
  - option: answer option text
  - instruction: survey instructions and descriptions
  - campaign_name: pulse survey campaign display names
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.survey_translations import SurveyTranslation

logger = logging.getLogger(__name__)

# Supported locales with display names
SUPPORTED_LOCALES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt-BR": "Portuguese (Brazil)",
    "ja": "Japanese",
    "zh-CN": "Chinese (Simplified)",
    "ar": "Arabic",
    "ko": "Korean",
    "hi": "Hindi",
    "it": "Italian",
    "nl": "Dutch",
}

DEFAULT_LOCALE = "en"


class SurveyTranslationService:
    """Manages survey content translations."""

    async def set_translation(
        self,
        db: AsyncSession,
        org_id: UUID,
        content_type: str,
        content_id: UUID,
        locale: str,
        translated_text: str,
    ) -> Dict[str, Any]:
        """Set or update a translation for a content item."""
        if locale not in SUPPORTED_LOCALES:
            return {
                "error": f"Unsupported locale: {locale}",
                "supported": list(SUPPORTED_LOCALES.keys()),
            }

        # Upsert
        result = await db.execute(
            select(SurveyTranslation).where(
                and_(
                    SurveyTranslation.organization_id == org_id,
                    SurveyTranslation.content_type == content_type,
                    SurveyTranslation.content_id == content_id,
                    SurveyTranslation.locale == locale,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.translated_text = translated_text
            existing.updated_at = datetime.now(timezone.utc)
        else:
            db.add(
                SurveyTranslation(
                    organization_id=org_id,
                    content_type=content_type,
                    content_id=content_id,
                    locale=locale,
                    translated_text=translated_text,
                )
            )

        await db.commit()
        return {
            "content_type": content_type,
            "content_id": str(content_id),
            "locale": locale,
            "status": "updated" if existing else "created",
        }

    async def set_translations_bulk(
        self,
        db: AsyncSession,
        org_id: UUID,
        translations: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Bulk upsert translations.

        Each item: {content_type, content_id, locale, translated_text}
        """
        created = 0
        updated = 0
        errors = []

        for item in translations:
            locale = item.get("locale", "")
            if locale not in SUPPORTED_LOCALES:
                errors.append(f"Unsupported locale: {locale}")
                continue

            result = await db.execute(
                select(SurveyTranslation).where(
                    and_(
                        SurveyTranslation.organization_id == org_id,
                        SurveyTranslation.content_type == item["content_type"],
                        SurveyTranslation.content_id == item["content_id"],
                        SurveyTranslation.locale == locale,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.translated_text = item["translated_text"]
                existing.updated_at = datetime.now(timezone.utc)
                updated += 1
            else:
                db.add(
                    SurveyTranslation(
                        organization_id=org_id,
                        content_type=item["content_type"],
                        content_id=item["content_id"],
                        locale=locale,
                        translated_text=item["translated_text"],
                    )
                )
                created += 1

        await db.commit()
        return {"created": created, "updated": updated, "errors": errors}

    async def get_translation(
        self,
        db: AsyncSession,
        org_id: UUID,
        content_type: str,
        content_id: UUID,
        locale: str,
    ) -> Optional[str]:
        """Get a single translation, falling back to default locale."""
        result = await db.execute(
            select(SurveyTranslation.translated_text).where(
                and_(
                    SurveyTranslation.organization_id == org_id,
                    SurveyTranslation.content_type == content_type,
                    SurveyTranslation.content_id == content_id,
                    SurveyTranslation.locale == locale,
                )
            )
        )
        text = result.scalar_one_or_none()

        # Fallback to default locale
        if text is None and locale != DEFAULT_LOCALE:
            result = await db.execute(
                select(SurveyTranslation.translated_text).where(
                    and_(
                        SurveyTranslation.organization_id == org_id,
                        SurveyTranslation.content_type == content_type,
                        SurveyTranslation.content_id == content_id,
                        SurveyTranslation.locale == DEFAULT_LOCALE,
                    )
                )
            )
            text = result.scalar_one_or_none()

        return text

    async def resolve_content(
        self,
        db: AsyncSession,
        org_id: UUID,
        content_items: List[Dict[str, str]],
        locale: str,
    ) -> Dict[str, str]:
        """Resolve translations for multiple content items at once.

        Args:
            content_items: [{content_type, content_id, fallback_text}]
            locale: Target locale

        Returns:
            Dict of content_id -> translated text (or fallback)
        """
        if locale == DEFAULT_LOCALE:
            return {
                item["content_id"]: item.get("fallback_text", "")
                for item in content_items
            }

        # Batch query all translations for these items
        content_ids = [item["content_id"] for item in content_items]
        fallback_map = {
            item["content_id"]: item.get("fallback_text", "") for item in content_items
        }

        result = await db.execute(
            select(
                SurveyTranslation.content_id, SurveyTranslation.translated_text
            ).where(
                and_(
                    SurveyTranslation.organization_id == org_id,
                    SurveyTranslation.content_id.in_(content_ids),
                    SurveyTranslation.locale == locale,
                )
            )
        )
        translations = {str(r[0]): r[1] for r in result.all()}

        # Merge: use translation if available, else fallback
        resolved = {}
        for cid in content_ids:
            resolved[cid] = translations.get(cid, fallback_map.get(cid, ""))

        return resolved

    async def get_available_locales(
        self, db: AsyncSession, org_id: UUID
    ) -> List[Dict[str, Any]]:
        """List locales that have at least one translation for this org."""
        from sqlalchemy import func as sqla_func

        result = await db.execute(
            select(
                SurveyTranslation.locale,
                sqla_func.count(SurveyTranslation.id),
            )
            .where(SurveyTranslation.organization_id == org_id)
            .group_by(SurveyTranslation.locale)
        )

        locales = []
        for locale, count in result.all():
            locales.append(
                {
                    "locale": locale,
                    "name": SUPPORTED_LOCALES.get(locale, locale),
                    "translation_count": count,
                }
            )

        return sorted(locales, key=lambda l: l["translation_count"], reverse=True)

    async def get_translation_coverage(
        self,
        db: AsyncSession,
        org_id: UUID,
        locale: str,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Report how complete translations are for a locale.

        Compares against the default locale (en) as the source of truth.
        """
        from sqlalchemy import func as sqla_func

        # Count source (default locale) items
        source_q = (
            select(sqla_func.count())
            .select_from(SurveyTranslation)
            .where(
                and_(
                    SurveyTranslation.organization_id == org_id,
                    SurveyTranslation.locale == DEFAULT_LOCALE,
                )
            )
        )
        if content_type:
            source_q = source_q.where(SurveyTranslation.content_type == content_type)
        source_count = (await db.execute(source_q)).scalar() or 0

        # Count target locale items
        target_q = (
            select(sqla_func.count())
            .select_from(SurveyTranslation)
            .where(
                and_(
                    SurveyTranslation.organization_id == org_id,
                    SurveyTranslation.locale == locale,
                )
            )
        )
        if content_type:
            target_q = target_q.where(SurveyTranslation.content_type == content_type)
        target_count = (await db.execute(target_q)).scalar() or 0

        coverage = round(target_count / max(source_count, 1) * 100, 1)

        return {
            "locale": locale,
            "locale_name": SUPPORTED_LOCALES.get(locale, locale),
            "content_type": content_type or "all",
            "source_items": source_count,
            "translated_items": target_count,
            "coverage_pct": coverage,
            "missing": max(source_count - target_count, 0),
        }

    async def delete_translation(
        self,
        db: AsyncSession,
        org_id: UUID,
        content_type: str,
        content_id: UUID,
        locale: str,
    ) -> Dict[str, Any]:
        """Delete a specific translation."""
        result = await db.execute(
            delete(SurveyTranslation).where(
                and_(
                    SurveyTranslation.organization_id == org_id,
                    SurveyTranslation.content_type == content_type,
                    SurveyTranslation.content_id == content_id,
                    SurveyTranslation.locale == locale,
                )
            )
        )
        await db.commit()
        return {"deleted": result.rowcount > 0}


survey_translation_service = SurveyTranslationService()
