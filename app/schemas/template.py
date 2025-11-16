# app/schemas/template.py
from typing import Optional, Dict, Any
from pydantic import BaseModel, validator, ConfigDict
from datetime import datetime


class TemplateBase(BaseModel):
    """Base template schema"""
    name: str
    description: Optional[str] = None
    category: str
    author: Optional[str] = None
    is_public: bool = True


class TemplateCreate(TemplateBase):
    """Template creation schema"""
    template_data: str  # JSON string of assessment structure
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 3:
            raise ValueError('Template name must be at least 3 characters')
        return v


class TemplateUpdate(BaseModel):
    """Template update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    author: Optional[str] = None
    is_public: Optional[bool] = None
    template_data: Optional[str] = None


class Template(TemplateBase):
    """Template response schema"""
    id: int
    version: str
    is_official: bool
    usage_count: int
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TemplateWithData(Template):
    """Template with full data"""
    template_data: str
    
    model_config = ConfigDict(from_attributes=True)


class TemplateList(BaseModel):
    """Template list response"""
    templates: list[Template]
    total: int
    
    