# app/schemas/template.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, validator


class TemplateBase(BaseModel):
    """Base template schema"""

    name: str
    description: str | None = None
    category: str
    author: str | None = None
    is_public: bool = True


class TemplateCreate(TemplateBase):
    """Template creation schema"""

    template_data: str  # JSON string of assessment structure

    @validator("name")
    def validate_name(cls, v):
        if len(v) < 3:
            raise ValueError("Template name must be at least 3 characters")
        return v


class TemplateUpdate(BaseModel):
    """Template update schema"""

    name: str | None = None
    description: str | None = None
    category: str | None = None
    author: str | None = None
    is_public: bool | None = None
    template_data: str | None = None


class Template(TemplateBase):
    """Template response schema"""

    id: int
    version: str
    is_official: bool
    usage_count: int
    created_by_id: int | None = None
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
