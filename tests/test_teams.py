# app/tests/test_teams.py
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
    # app/tests/test_teams.py - Continue from create_test_user
    # Login
    response = client.post(
        "/api/v1/auth/login/json",
        json={"email": email, "password": password}
    )
    return response.json()["access_token"]


def test_create_team(client: TestClient, db: Session):
    """Test team creation"""
    token = create_test_user(client, "owner@example.com")
    
    response = client.post(
        "/api/v1/teams",
        json={"name": "Test Team", "description": "Test Description"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Team"
    assert data["description"] == "Test Description"
    assert data["is_active"] is True


def test_create_team_short_name(client: TestClient, db: Session):
    """Test team creation with short name"""
    token = create_test_user(client, "user@example.com")
    
    response = client.post(
        "/api/v1/teams",
        json={"name": "AB", "description": "Test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


def test_list_teams(client: TestClient, db: Session):
    """Test listing teams"""
    token = create_test_user(client, "user@example.com")
    
    # Create a team
    client.post(
        "/api/v1/teams",
        json={"name": "Test Team", "description": "Test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # List teams
    response = client.get(
        "/api/v1/teams",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "teams" in data
    assert len(data["teams"]) >= 1


def test_get_team_detail(client: TestClient, db: Session):
    """Test getting team details"""
    token = create_test_user(client, "owner@example.com")
    
    # Create team
    create_response = client.post(
        "/api/v1/teams",
        json={"name": "Test Team", "description": "Test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    team_id = create_response.json()["id"]
    
    # Get team details
    response = client.get(
        f"/api/v1/teams/{team_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Team"
    assert "members" in data
    assert data["member_count"] >= 1


def test_update_team(client: TestClient, db: Session):
    """Test updating team"""
    token = create_test_user(client, "owner@example.com")
    
    # Create team
    create_response = client.post(
        "/api/v1/teams",
        json={"name": "Original Name", "description": "Original"},
        headers={"Authorization": f"Bearer {token}"}
    )
    team_id = create_response.json()["id"]
    
    # Update team
    response = client.put(
        f"/api/v1/teams/{team_id}",
        json={"name": "Updated Name", "description": "Updated"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated"


def test_delete_team(client: TestClient, db: Session):
    """Test deleting team"""
    token = create_test_user(client, "owner@example.com")
    
    # Create team
    create_response = client.post(
        "/api/v1/teams",
        json={"name": "Test Team", "description": "Test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    team_id = create_response.json()["id"]
    
    # Delete team
    response = client.delete(
        f"/api/v1/teams/{team_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204
    
    # Verify deleted
    get_response = client.get(
        f"/api/v1/teams/{team_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 404


def test_add_member_to_team(client: TestClient, db: Session):
    """Test adding member to team"""
    owner_token = create_test_user(client, "owner@example.com")
    
    # Create another user
    member_response = client.post(
        "/api/v1/auth/register",
        json={"email": "member@example.com", "full_name": "Member", "password": "Test1234"}
    )
    member_id = member_response.json()["id"]
    
    # Create team
    create_response = client.post(
        "/api/v1/teams",
        json={"name": "Test Team"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    team_id = create_response.json()["id"]
    
    # Add member
    response = client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": member_id, "role": "member"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == member_id
    assert data["role"] == "member"


def test_remove_member_from_team(client: TestClient, db: Session):
    """Test removing member from team"""
    owner_token = create_test_user(client, "owner@example.com")
    
    # Create another user
    member_response = client.post(
        "/api/v1/auth/register",
        json={"email": "member@example.com", "full_name": "Member", "password": "Test1234"}
    )
    member_id = member_response.json()["id"]
    
    # Create team and add member
    create_response = client.post(
        "/api/v1/teams",
        json={"name": "Test Team"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    team_id = create_response.json()["id"]
    
    client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": member_id, "role": "member"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    
    # Remove member
    response = client.delete(
        f"/api/v1/teams/{team_id}/members/{member_id}",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert response.status_code == 204


def test_update_member_role(client: TestClient, db: Session):
    """Test updating member role"""
    owner_token = create_test_user(client, "owner@example.com")
    
    # Create another user
    member_response = client.post(
        "/api/v1/auth/register",
        json={"email": "member@example.com", "full_name": "Member", "password": "Test1234"}
    )
    member_id = member_response.json()["id"]
    
    # Create team and add member
    create_response = client.post(
        "/api/v1/teams",
        json={"name": "Test Team"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    team_id = create_response.json()["id"]
    
    client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": member_id, "role": "member"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    
    # Update role
    response = client.patch(
        f"/api/v1/teams/{team_id}/members/{member_id}",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"


def test_non_member_cannot_access_team(client: TestClient, db: Session):
    """Test non-member cannot access team"""
    owner_token = create_test_user(client, "owner@example.com")
    non_member_token = create_test_user(client, "nonmember@example.com")
    
    # Create team
    create_response = client.post(
        "/api/v1/teams",
        json={"name": "Test Team"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    team_id = create_response.json()["id"]
    
    # Try to access as non-member
    response = client.get(
        f"/api/v1/teams/{team_id}",
        headers={"Authorization": f"Bearer {non_member_token}"}
    )
    assert response.status_code == 403


def test_member_cannot_add_members(client: TestClient, db: Session):
    """Test regular member cannot add members"""
    owner_token = create_test_user(client, "owner@example.com")
    member_token = create_test_user(client, "member@example.com")
    
    # Get member ID
    member_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    member_id = member_response.json()["id"]
    
    # Create team
    create_response = client.post(
        "/api/v1/teams",
        json={"name": "Test Team"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    team_id = create_response.json()["id"]
    
    # Add member as regular member
    client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": member_id, "role": "member"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    
    # Create another user to try to add
    new_user_response = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "full_name": "New", "password": "Test1234"}
    )
    new_user_id = new_user_response.json()["id"]
    
    # Try to add as member (should fail)
    response = client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": new_user_id, "role": "member"},
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert response.status_code == 403
    