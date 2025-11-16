# app/services/template_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
import json

from app.db.models.template import Template
from app.db.models.assessment import Assessment, AssessmentSection, Question
from app.schemas.template import TemplateCreate, TemplateUpdate


class TemplateService:
    """Template service for database operations"""
    
    @staticmethod
    def create(
        db: Session,
        template_in: TemplateCreate,
        creator_id: Optional[int] = None
    ) -> Template:
        """Create new template"""
        template = Template(
            name=template_in.name,
            description=template_in.description,
            template_type=template_in.template_type if hasattr(template_in, 'template_type') else 'assessment',
            content=template_in.content if hasattr(template_in, 'content') else {},
            is_public=template_in.is_public if hasattr(template_in, 'is_public') else False,
            created_by_id=creator_id
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template
    
    @staticmethod
    def get_by_id(db: Session, template_id: str) -> Optional[Template]:
        """Get template by ID"""
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    def get_all(
        db: Session,
        template_type: Optional[str] = None,
        is_public: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Template]:
        """Get all templates"""
        query = db.query(Template)

        if template_type:
            query = query.filter(Template.template_type == template_type)

        if is_public is not None:
            query = query.filter(Template.is_public == is_public)

        return query.order_by(Template.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def search(db: Session, query: str) -> List[Template]:
        """Search templates"""
        search_term = f"%{query}%"
        return db.query(Template).filter(
            or_(
                Template.name.ilike(search_term),
                Template.description.ilike(search_term)
            )
        ).limit(50).all()
    
    @staticmethod
    def update(
        db: Session,
        template: Template,
        template_in: TemplateUpdate
    ) -> Template:
        """Update template"""
        update_data = template_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(template, field):
                setattr(template, field, value)

        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    def delete(db: Session, template: Template) -> None:
        """Delete template"""
        db.delete(template)
        await db.commit()
    
    @staticmethod
    def create_assessment_from_template(
        db: Session,
        template: Template,
        creator_id: int,
        team_id: Optional[int] = None
    ) -> Assessment:
        """Create assessment from template"""
        # Create basic assessment from template
        assessment = Assessment(
            title=template.name,
            description=template.description or f"Based on template: {template.name}",
            created_by_id=creator_id,
            team_id=team_id
        )
        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)
        return assessment
    
    @staticmethod
    def create_template_from_assessment(
        db: Session,
        assessment: Assessment,
        template_name: str,
        template_description: Optional[str],
        creator_id: int
    ) -> Template:
        """Create template from existing assessment"""
        # Create simple template data from assessment
        template_data = {
            'title': assessment.title,
            'description': assessment.description,
            'sections': []
        }

        # Create template
        template = Template(
            name=template_name,
            description=template_description or assessment.description,
            template_type='assessment',
            content=template_data,
            is_public=False,
            created_by_id=creator_id
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template
        