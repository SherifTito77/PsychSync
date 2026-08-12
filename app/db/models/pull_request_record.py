"""
PullRequestRecord — stores synced PR data from GitHub/GitLab webhooks or manual imports.
"""

import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class PullRequestRecord(Base):
    __tablename__ = "pull_request_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(String(36), nullable=True, index=True)
    external_id = Column(String(64), nullable=False, index=True)  # e.g. "PR-001"
    title = Column(String(500), nullable=False)
    author = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="open")  # open|closed|merged
    url = Column(Text, nullable=True)
    base_branch = Column(String(255), nullable=True)
    head_branch = Column(String(255), nullable=True)
    additions = Column(Integer, nullable=True)
    deletions = Column(Integer, nullable=True)
    changed_files = Column(Integer, nullable=True)
    reviewers = Column(ARRAY(String), nullable=True)
    pr_created_at = Column(DateTime(timezone=True), nullable=True)
    pr_updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
