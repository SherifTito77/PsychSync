# app/api/v1/endpoints/templates.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, get_current_admin_user
from app.db.models.user import User
from app.db.models.template import Template
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    Template as TemplateSchema,
    TemplateWithData,
    TemplateList
)
from app.schemas.assessment import Assessment as AssessmentSchema
# Temporarily disabled due to async conversion issues
# from app.services.template_service import TemplateService

# Placeholder TemplateService class
class TemplateService:
    @staticmethod
    async def get_templates(*args, **kwargs):
        return []

    @staticmethod
    async def get_template_by_id(*args, **kwargs):
        return None

    @staticmethod
    async def create_template(*args, **kwargs):
        return None

    @staticmethod
    async def update_template(*args, **kwargs):
        return None

    @staticmethod
    async def delete_template(*args, **kwargs):
        return False

router = APIRouter()


@router.post("", response_model=TemplateSchema, status_code=status.HTTP_201_CREATED)
def create_template(
    template_in: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new assessment template.
    """
    template = TemplateService.create(
        db,
        template_in=template_in,
        creator_id=current_user.id
    )
    return template


@router.get("", response_model=TemplateList)
def list_templates(
    category: Optional[str] = Query(None),
    is_official: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List all public templates.
    """
    templates = TemplateService.get_all(
        db,
        category=category,
        is_official=is_official,
        skip=skip,
        limit=limit
    )
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/search", response_model=List[TemplateSchema])
def search_templates(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    """
    Search templates by name or description.
    """
    templates = TemplateService.search(db, query=q)
    return templates


@router.get("/{template_id}", response_model=TemplateWithData)
def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    Get template details with full data.
    """
    template = TemplateService.get_by_id(db, template_id=template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    if not template.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This template is not public"
        )
    
    return template


@router.post("/{template_id}/use", response_model=AssessmentSchema, status_code=status.HTTP_201_CREATED)
def create_assessment_from_template(
    template_id: int,
    team_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new assessment from a template.
    """
    template = TemplateService.get_by_id(db, template_id=template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    if not template.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This template is not public"
        )
    
    assessment = TemplateService.create_assessment_from_template(
        db,
        template=template,
        creator_id=current_user.id,
        team_id=team_id
    )
    
    return assessment


@router.post("/from-assessment/{assessment_id}", response_model=TemplateSchema, status_code=status.HTTP_201_CREATED)
def create_template_from_assessment(
    assessment_id: int,
    name: str = Query(..., min_length=3),
    description: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a template from an existing assessment.
    """
    import app.services.assessment_service as AssessmentService
    
    assessment = AssessmentService.get_by_id(db, assessment_id=assessment_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Check permission
    if assessment.created_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create templates from your own assessments"
        )
    
    template = TemplateService.create_template_from_assessment(
        db,
        assessment=assessment,
        template_name=name,
        template_description=description,
        creator_id=current_user.id
    )
    
    return template


@router.put("/{template_id}", response_model=TemplateSchema)
def update_template(
    template_id: int,
    template_in: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update template.
    """
    template = TemplateService.get_by_id(db, template_id=template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check permission
    if template.created_by_id != current_user.id:
        from app.services.user_service import user_service
        if not user_service.is_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this template"
            )
    
    updated_template = TemplateService.update(db, template=template, template_in=template_in)
    return updated_template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete template.
    """
    template = TemplateService.get_by_id(db, template_id=template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check permission
    if template.created_by_id != current_user.id:
        from app.services.user_service import user_service
        if not user_service.is_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this template"
            )
    
    TemplateService.delete(db, template=template)
    return None

