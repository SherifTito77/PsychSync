# app/api/v1/endpoints/pull_requests.py
"""
Pull Requests Endpoints — persists PR data synced via webhooks or POST /import.
Returns real stored records; empty until PRs are synced from GitHub/GitLab.
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.pull_request_record import PullRequestRecord
from app.db.models.user import User

router = APIRouter(prefix="/pull-requests", tags=["pull-requests"])


class PullRequest(BaseModel):
    id: str
    title: str
    author: str
    status: str
    created_at: datetime
    updated_at: datetime
    url: str | None = None
    base_branch: str | None = None
    head_branch: str | None = None
    additions: int | None = None
    deletions: int | None = None
    changed_files: int | None = None
    reviewers: list[str] | None = None

    model_config = {"from_attributes": True}


def _serialize(row: PullRequestRecord) -> PullRequest:
    return PullRequest(
        id=row.external_id,
        title=row.title,
        author=row.author,
        status=row.status,
        created_at=row.pr_created_at or row.created_at,
        updated_at=row.pr_updated_at or row.created_at,
        url=row.url,
        base_branch=row.base_branch,
        head_branch=row.head_branch,
        additions=row.additions,
        deletions=row.deletions,
        changed_files=row.changed_files,
        reviewers=row.reviewers or [],
    )


@router.get("/", response_model=list[PullRequest])
async def get_pull_requests(
    limit: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PullRequest]:
    """Return stored pull requests. Empty until synced via /import or webhooks."""
    query = select(PullRequestRecord).order_by(PullRequestRecord.created_at.desc())
    if status:
        query = query.where(PullRequestRecord.status == status)
    query = query.limit(limit)
    result = await db.execute(query)
    return [_serialize(r) for r in result.scalars().all()]


@router.get("/summary")
async def get_pull_requests_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    total = (await db.execute(select(func.count(PullRequestRecord.id)))).scalar() or 0
    open_count = (
        await db.execute(
            select(func.count(PullRequestRecord.id)).where(
                PullRequestRecord.status == "open"
            )
        )
    ).scalar() or 0
    merged = (
        await db.execute(
            select(func.count(PullRequestRecord.id)).where(
                PullRequestRecord.status == "merged"
            )
        )
    ).scalar() or 0
    closed = (
        await db.execute(
            select(func.count(PullRequestRecord.id)).where(
                PullRequestRecord.status == "closed"
            )
        )
    ).scalar() or 0

    avg_add = (
        await db.execute(select(func.avg(PullRequestRecord.additions)))
    ).scalar() or 0
    avg_del = (
        await db.execute(select(func.avg(PullRequestRecord.deletions)))
    ).scalar() or 0

    return {
        "total": total,
        "open": open_count,
        "merged": merged,
        "closed": closed,
        "average_review_time_hours": 0,
        "average_size_additions": round(float(avg_add), 1),
        "average_size_deletions": round(float(avg_del), 1),
    }


class PRImportRequest(BaseModel):
    external_id: str
    title: str
    author: str
    status: str = "open"
    url: str | None = None
    base_branch: str | None = None
    head_branch: str | None = None
    additions: int | None = None
    deletions: int | None = None
    changed_files: int | None = None
    reviewers: list[str] | None = None
    pr_created_at: datetime | None = None
    pr_updated_at: datetime | None = None


@router.post("/import", status_code=201)
async def import_pull_request(
    body: PRImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Accept a PR from a webhook or manual import."""
    # Upsert by external_id
    existing = await db.execute(
        select(PullRequestRecord).where(
            PullRequestRecord.external_id == body.external_id
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.title = body.title
        row.author = body.author
        row.status = body.status
        row.url = body.url
        row.additions = body.additions
        row.deletions = body.deletions
        row.changed_files = body.changed_files
        row.reviewers = body.reviewers
        row.pr_updated_at = body.pr_updated_at
    else:
        row = PullRequestRecord(
            external_id=body.external_id,
            title=body.title,
            author=body.author,
            status=body.status,
            url=body.url,
            base_branch=body.base_branch,
            head_branch=body.head_branch,
            additions=body.additions,
            deletions=body.deletions,
            changed_files=body.changed_files,
            reviewers=body.reviewers,
            pr_created_at=body.pr_created_at,
            pr_updated_at=body.pr_updated_at,
        )
        db.add(row)

    await db.commit()
    return {"id": row.external_id, "status": row.status, "imported": True}
