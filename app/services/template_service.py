# app/services/template_service.py
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.template import Template
from app.schemas.template import TemplateCreate, TemplateUpdate


class TemplateService:
    """Template service for database operations"""

    @staticmethod
    async def create(
        db: AsyncSession,
        template_in: TemplateCreate,
        creator_id: UUID | None = None
    ) -> Template:
        """Create new template"""
        template = Template(
            name=template_in.name,
            description=template_in.description,
            template_type=template_in.template_type if hasattr(template_in, "template_type") else "assessment",
            content=template_in.content if hasattr(template_in, "content") else {},
            is_public=template_in.is_public if hasattr(template_in, "is_public") else False,
            created_by_id=creator_id
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def get_by_id(db: AsyncSession, template_id: UUID) -> Template | None:
        """Get template by ID"""
        result = await db.execute(select(Template).where(Template.id == template_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        template_type: str | None = None,
        is_public: bool | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Template]:
        """Get all templates"""
        query = select(Template)

        if template_type:
            query = query.where(Template.template_type == template_type)

        if is_public is not None:
            query = query.where(Template.is_public == is_public)

        query = query.offset(skip).limit(limit).order_by(Template.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_user_templates(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Template]:
        """Get templates created by a user"""
        query = select(Template).where(Template.created_by_id == user_id)
        query = query.offset(skip).limit(limit).order_by(Template.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(
        db: AsyncSession,
        template_id: UUID,
        template_in: TemplateUpdate
    ) -> Template | None:
        """Update template"""
        result = await db.execute(select(Template).where(Template.id == template_id))
        template = result.scalar_one_or_none()

        if not template:
            return None

        update_data = template_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(template, field):
                setattr(template, field, value)

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def delete(db: AsyncSession, template_id: UUID) -> bool:
        """Delete template"""
        result = await db.execute(select(Template).where(Template.id == template_id))
        template = result.scalar_one_or_none()

        if not template:
            return False

        await db.delete(template)
        await db.commit()
        return True

    @staticmethod
    async def duplicate(
        db: AsyncSession,
        template_id: UUID,
        new_name: str,
        creator_id: UUID
    ) -> Template | None:
        """Duplicate a template"""
        original = await TemplateService.get_by_id(db, template_id)

        if not original:
            return None

        new_template = Template(
            name=new_name,
            description=original.description,
            template_type=original.template_type,
            content=original.content.copy() if original.content else {},
            is_public=False,  # Duplicated templates are private by default
            created_by_id=creator_id
        )

        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        return new_template

    @staticmethod
    def to_dict(template: Template) -> dict[str, Any]:
        """Convert template to dictionary"""
        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "template_type": template.template_type,
            "content": template.content,
            "is_public": template.is_public,
            "created_by_id": str(template.created_by_id) if template.created_by_id else None,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }


# Backward compatibility functions
async def create_template(db: AsyncSession, template_in: TemplateCreate, creator_id: UUID | None = None) -> Template:
    """Backward compatibility wrapper"""
    return await TemplateService.create(db, template_in, creator_id)

async def get_template_by_id(db: AsyncSession, template_id: UUID) -> Template | None:
    """Backward compatibility wrapper"""
    return await TemplateService.get_by_id(db, template_id)
