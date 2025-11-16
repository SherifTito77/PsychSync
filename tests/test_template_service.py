# app/tests/test_template_service.py
import pytest
import json
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.template import AssessmentTemplate, TemplateCategory
from app.services.template_service import TemplateService

pytestmark = pytest.mark.template


class TestTemplateService:
    """Test template service functionality"""

    def test_create_template(self, db: Session, test_user: User):
        """Test creating a template"""
        from app.schemas.template import TemplateCreate
        
        template_data = {
            "title": "Test Template",
            "sections": [
                {
                    "title": "Section 1",
                    "order": 0,
                    "questions": [
                        {
                            "question_type": "likert",
                            "question_text": "Test question",
                            "order": 0,
                            "is_required": True
                        }
                    ]
                }
            ]
        }
        
        template_in = TemplateCreate(
            name="Test Template",
            description="Test description",
            category="personality",
            template_data=json.dumps(template_data)
        )
        
        template = TemplateService.create(
            db,
            template_in=template_in,
            creator_id=test_user.id
        )
        
        assert template is not None
        assert template.name == "Test Template"
        assert template.category == TemplateCategory.PERSONALITY

    def test_get_all_templates(self, db: Session, test_user: User):
        """Test listing all templates"""
        # Create a template
        from app.schemas.template import TemplateCreate
        
        template_in = TemplateCreate(
            name="Public Template",
            description="Test",
            category="personality",
            is_public=True,
            template_data=json.dumps({"title": "Test"})
        )
        
        TemplateService.create(db, template_in=template_in, creator_id=test_user.id)
        
        # Get all templates
        templates = TemplateService.get_all(db)
        
        assert len(templates) >= 1

    def test_search_templates(self, db: Session, test_user: User):
        """Test searching templates"""
        from app.schemas.template import TemplateCreate
        
        template_in = TemplateCreate(
            name="Unique Search Term Template",
            description="Searchable description",
            category="personality",
            is_public=True,
            template_data=json.dumps({"title": "Test"})
        )
        
        TemplateService.create(db, template_in=template_in, creator_id=test_user.id)
        
        # Search
        results = TemplateService.search(db, query="Unique Search")
        
        assert len(results) >= 1
        assert "Unique Search" in results[0].name

    def test_create_assessment_from_template(self, db: Session, test_user: User):
        """Test creating assessment from template"""
        from app.schemas.template import TemplateCreate
        
        template_data = {
            "title": "Assessment from Template",
            "description": "Test",
            "category": "personality",
            "sections": [
                {
                    "title": "Section 1",
                    "order": 0,
                    "questions": [
                        {
                            "question_type": "likert",
                            "question_text": "How are you?",
                            "order": 0,
                            "is_required": True
                        }
                    ]
                }
            ]
        }
        
        template_in = TemplateCreate(
            name="Source Template",
            category="personality",
            is_public=True,
            template_data=json.dumps(template_data)
        )
        
        template = TemplateService.create(db, template_in=template_in, creator_id=test_user.id)
        
        # Create assessment from template
        assessment = TemplateService.create_assessment_from_template(
            db,
            template=template,
            creator_id=test_user.id
        )
        
        assert assessment is not None
        assert assessment.title == "Assessment from Template"
        assert len(assessment.sections) == 1
        assert len(assessment.sections[0].questions) == 1

    def test_create_template_from_assessment(self, db: Session, test_user: User, test_assessment):
        """Test creating template from assessment"""
        template = TemplateService.create_template_from_assessment(
            db,
            assessment=test_assessment,
            template_name="Template from Assessment",
            template_description="Test",
            creator_id=test_user.id
        )
        
        assert template is not None
        assert template.name == "Template from Assessment"
        
        # Verify template data contains assessment structure
        template_data = json.loads(template.template_data)
        assert "sections" in template_data
        assert len(template_data["sections"]) == 1


class TestTemplateEndpoints:
    """Test template API endpoints"""

    def test_list_templates_endpoint(self, client, auth_headers):
        """Test listing templates"""
        response = client.get("/api/v1/templates")
        
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data

    def test_search_templates_endpoint(self, client):
        """Test searching templates"""
        response = client.get("/api/v1/templates/search?q=test")
        
        assert response.status_code == 200

    def test_use_template_endpoint(self, client, auth_headers, db, test_user):
        """Test creating assessment from template"""
        from app.schemas.template import TemplateCreate
        
        # Create a template first
        template_in = TemplateCreate(
            name="Test Template",
            category="personality",
            is_public=True,
            template_data=json.dumps({
                "title": "From Template",
                "sections": []
            })
        )
        
        template = TemplateService.create(db, template_in=template_in, creator_id=test_user.id)
        
        # Use template
        response = client.post(
            f"/api/v1/templates/{template.id}/use",
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "From Template"
        