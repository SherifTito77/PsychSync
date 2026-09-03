"""
Clinical Resources API Endpoints.

Serves admin-managed therapist, support group, and resource directory
from the clinical_resources table. Returns empty list until seeded.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.clinical_resource import ClinicalResource
from app.db.models.user import User

router = APIRouter(prefix="/clinical", tags=["Clinical Resources"])


def _serialize(row: ClinicalResource) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "resource_type": row.resource_type,
        "name": row.name,
        "credentials": row.credentials or [],
        "specializations": row.specializations or [],
        "languages": row.languages or [],
        "telehealth": row.telehealth or False,
        "insurance": row.insurance or [],
        "rating": row.rating,
        "distance": row.distance,
        "consultation_fee": row.consultation_fee,
        "availability": row.availability,
        "meeting_schedule": row.meeting_schedule,
        "location": row.location,
        "category": row.category,
        "description": row.description,
        "url": row.url,
    }


@router.get("/resources")
async def list_clinical_resources(
    resource_type: str | None = Query(None, description="therapist | group | resource"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return clinical resources from the database.

    Returns empty lists until an admin seeds the table via
    POST /clinical/resources (admin-only endpoint below).
    """
    query = select(ClinicalResource)
    if resource_type:
        query = query.where(ClinicalResource.resource_type == resource_type)
    query = query.order_by(ClinicalResource.rating.desc().nulls_last())

    result = await db.execute(query)
    rows = result.scalars().all()

    therapists = [_serialize(r) for r in rows if r.resource_type == "therapist"]
    groups = [_serialize(r) for r in rows if r.resource_type == "group"]
    resources = [_serialize(r) for r in rows if r.resource_type == "resource"]

    return {
        "success": True,
        "therapists": therapists,
        "support_groups": groups,
        "resources": resources,
        "total": len(rows),
    }
