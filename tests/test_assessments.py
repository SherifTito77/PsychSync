# app/tests/test_assessments.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def create_test_user(client: TestClient, email: str, password: str = "Test1234"):
    """Helper to create and login user"""
    # Register
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": password}
    )
    # Login
    response = client.post(
        "/api/v1/auth/login/json",
        json={"email": email, "password": password}
    )
    return response.json()["access_token"]


def test_create_assessment(client: TestClient, db: Session):
    """Test assessment creation"""
    token = create_test_user(client, "creator@example.com")
    
    response = client.post(
        "/api/v1/assessments",
        json={
            "title": "Test Assessment",
            "description": "Test Description",
            "category": "personality"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Assessment"
    assert data["category"] == "personality"
    assert data["status"] == "draft"


def test_create_assessment_with_sections(client: TestClient, db: Session):
    """Test assessment creation with sections and questions"""
    token = create_test_user(client, "creator@example.com")
    
    response = client.post(
        "/api/v1/assessments",
        json={
            "title": "Full Assessment",
            "category": "cognitive",
            "sections": [
                {
                    "title": "Section 1",
                    "order": 0,
                    "questions": [
                        {
                            "question_type": "multiple_choice",
                            "question_text": "What is your favorite color?",
                            "order": 0,
                            "config": {
                                "options": ["Red", "Blue", "Green"],
                                "allow_multiple": False
                            }
                        }
                    ]
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Full Assessment"


def test_list_assessments(client: TestClient, db: Session):
    """Test listing assessments"""
    token = create_test_user(client, "user@example.com")
    
    # Create an assessment
    client.post(
        "/api/v1/assessments",
        json={"title": "Test Assessment", "category": "personality"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # List assessments
    response = client.get(
        "/api/v1/assessments",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "assessments" in data
    assert len(data["assessments"]) >= 1


def test_get_assessment_detail(client: TestClient, db: Session):
    """Test getting assessment details"""
    token = create_test_user(client, "creator@example.com")
    
    # Create assessment
    create_response = client.post(
        "/api/v1/assessments",
        json={"title": "Test Assessment", "category": "personality"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assessment_id = create_response.json()["id"]
    
    # Get assessment details
    response = client.get(
        f"/api/v1/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Assessment"
    assert "sections" in data
    assert "question_count" in data


def test_update_assessment(client: TestClient, db: Session):
    """Test updating assessment"""
    token = create_test_user(client, "creator@example.com")
    
    # Create assessment
    create_response = client.post(
        "/api/v1/assessments",
        json={"title": "Original Title", "category": "personality"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assessment_id = create_response.json()["id"]
    
    # Update assessment
    response = client.put(
        f"/api/v1/assessments/{assessment_id}",
        json={"title": "Updated Title", "description": "Updated Description"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"


def test_publish_assessment(client: TestClient, db: Session):
    """Test publishing assessment"""
    token = create_test_user(client, "creator@example.com")
    
    # Create assessment with section and question
    create_response = client.post(
        "/api/v1/assessments",
        json={
            "title": "Test Assessment",
            "category": "personality",
            "sections": [
                {
                    "title": "Section 1",
                    "order": 0,
                    "questions": [
                        {
                            "question_type": "text",
                            "question_text": "Test question?",
                            "order": 0
                        }
                    ]
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assessment_id = create_response.json()["id"]
    
    # Publish assessment
    response = client.post(
        f"/api/v1/assessments/{assessment_id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["published_at"] is not None


def test_archive_assessment(client: TestClient, db: Session):
    """Test archiving assessment"""
    token = create_test_user(client, "creator@example.com")
    
    # Create and publish assessment
    create_response = client.post(
        "/api/v1/assessments",
        json={
            "title": "Test Assessment",
            "category": "personality",
            "sections": [
                {
                    "title": "Section 1",
                    "order": 0,
                    "questions": [
                        {
                            "question_type": "text",
                            "question_text": "Test?",
                            "order": 0
                        }
                    ]
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assessment_id = create_response.json()["id"]
    
    client.post(
        f"/api/v1/assessments/{assessment_id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Archive assessment
    response = client.post(
        f"/api/v1/assessments/{assessment_id}/archive",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "archived"


def test_duplicate_assessment(client: TestClient, db: Session):
    """Test duplicating assessment"""
    token = create_test_user(client, "creator@example.com")
    
    # Create assessment
    create_response = client.post(
        "/api/v1/assessments",
        json={
            "title": "Original Assessment",
            "category": "personality",
            "sections": [
                {
                    "title": "Section 1",
                    "order": 0,
                    "questions": [
                        {
                            "question_type": "text",
                            "question_text": "Question?",
                            "order": 0
                        }
                    ]
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assessment_id = create_response.json()["id"]
    
    # Duplicate assessment
    response = client.post(
        f"/api/v1/assessments/{assessment_id}/duplicate",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "Copy" in data["title"]
    assert data["status"] == "draft"


def test_delete_assessment(client: TestClient, db: Session):
    """Test deleting assessment"""
    token = create_test_user(client, "creator@example.com")
    
    # Create assessment
    create_response = client.post(
        "/api/v1/assessments",
        json={"title": "Test Assessment", "category": "personality"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assessment_id = create_response.json()["id"]
    
    # Delete assessment
    response = client.delete(
        f"/api/v1/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
    
    # Verify deleted
    get_response = client.get(
        f"/api/v1/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404


def test_add_section(client: TestClient, db: Session):
    """Test adding section to assessment"""
    token = create_test_user(client, "creator@example.com")
    
    # Create assessment
    create_response = client.post(
        "/api/v1/assessments",
        json={"title": "Test Assessment", "category": "personality"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assessment_id = create_response.json()["id"]
    
    # Add section
    response = client.post(
        f"/api/v1/assessments/{assessment_id}/sections",
        json={"title": "New Section", "order": 0},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Section"


def test_add_question(client: TestClient, db: Session):
    """Test adding question to section"""
    token = create_test_user(client, "creator@example.com")
    
    # Create assessment with section
    create_response = client.post(
        "/api/v1/assessments",
        json={
            "title": "Test Assessment",
            "category": "personality",
            "sections": [{"title": "Section 1", "order": 0}]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assessment_id = create_response.json()["id"]
    
    # Get section ID
    detail_response = client.get(
        f"/api/v1/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    section_id = detail_response.json()["sections"][0]["id"]
    
    # Add question
    response = client.post(
        f"/api/v1/assessments/{assessment_id}/sections/{section_id}/questions",
        json={
            "question_type": "text",
            "question_text": "What is your name?",
            "order": 0
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["question_text"] == "What is your name?"


def test_non_creator_cannot_edit(client: TestClient, db: Session):
    """Test non-creator cannot edit assessment"""
    creator_token = create_test_user(client, "creator@example.com")
    other_token = create_test_user(client, "other@example.com")
    
    # Create assessment
    create_response = client.post(
        "/api/v1/assessments",
        json={"title": "Test Assessment", "category": "personality"},
        headers={"Authorization": f"Bearer {creator_token}"}
    )
    assessment_id = create_response.json()["id"]
    
    # Try to update as non-creator
    response = client.put(
        f"/api/v1/assessments/{assessment_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert response.status_code == 403


def test_filter_by_category(client: TestClient, db: Session):
    """Test filtering assessments by category"""
    token = create_test_user(client, "user@example.com")
    
    # Create assessments with different categories
    client.post(
        "/api/v1/assessments",
        json={"title": "Personality Test", "category": "personality"},
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        "/api/v1/assessments",
        json={"title": "Cognitive Test", "category": "cognitive"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Filter by category
    response = client.get(
        "/api/v1/assessments?category=personality",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(a["category"] == "personality" for a in data["assessments"])
    