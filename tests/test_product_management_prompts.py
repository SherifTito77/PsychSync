"""
Tests for Product Management Prompts

Comprehensive test suite covering:
- Prompt retrieval and filtering
- Execution tracking
- Search functionality
- Workflow generation
- API endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.product_management_service import ProductManagementPromptsService
from app.db.models.product_management import PromptExecution, PromptFavorite
from app.db.models.user import User
from app.main import app


# ============================================================================
# Service Layer Tests
# ============================================================================


@pytest.mark.asyncio
class TestProductManagementService:
    """Test suite for ProductManagementPromptsService."""

    async def test_load_prompts(self, db: AsyncSession):
        """Test that prompts can be loaded from JSON file."""
        service = ProductManagementPromptsService(db)
        data = await service._load_prompts()

        assert data is not None
        assert 'metadata' in data
        assert 'categories' in data
        assert data['metadata']['total_prompts'] == 50

    async def test_get_all_categories(self, db: AsyncSession):
        """Test retrieving all prompt categories."""
        service = ProductManagementPromptsService(db)
        categories = await service.get_all_categories()

        assert len(categories) == 5
        category_ids = [cat['id'] for cat in categories]
        assert 'roadmap_strategy' in category_ids
        assert 'user_experience' in category_ids
        assert 'growth_monetization' in category_ids
        assert 'analytics_metrics' in category_ids
        assert 'operations_processes' in category_ids

    async def test_get_prompts_by_category(self, db: AsyncSession):
        """Test retrieving prompts by category."""
        service = ProductManagementPromptsService(db)

        # Get roadmap strategy prompts
        prompts = await service.get_prompts_by_category('roadmap_strategy')

        assert len(prompts) == 10
        assert all('id' in p for p in prompts)
        assert all('prompt' in p for p in prompts)

    async def test_filter_prompts_by_complexity(self, db: AsyncSession):
        """Test filtering prompts by complexity."""
        service = ProductManagementPromptsService(db)

        # Get low complexity prompts
        low_prompts = await service.get_prompts_by_category(
            'roadmap_strategy',
            complexity_filter='low'
        )

        assert all(p['complexity'] == 'low' for p in low_prompts)

    async def test_filter_prompts_by_type(self, db: AsyncSession):
        """Test filtering prompts by type."""
        service = ProductManagementPromptsService(db)

        # Get strategic prompts
        strategic_prompts = await service.get_prompts_by_category(
            'roadmap_strategy',
            type_filter='strategic'
        )

        assert all(p['type'] == 'strategic' for p in strategic_prompts)

    async def test_get_prompt_by_id(self, db: AsyncSession):
        """Test retrieving a specific prompt by ID."""
        service = ProductManagementPromptsService(db)
        prompt = await service.get_prompt_by_id('rs_001')

        assert prompt is not None
        assert prompt['id'] == 'rs_001'
        assert 'Create a roadmap based on user value vs complexity' in prompt['prompt']
        assert len(prompt['outputs']) > 0
        assert len(prompt['use_cases']) > 0

    async def test_search_prompts(self, db: AsyncSession):
        """Test searching prompts by keyword."""
        service = ProductManagementPromptsService(db)

        # Search for "roadmap"
        results = await service.search_prompts('roadmap')

        assert len(results) > 0
        assert any('roadmap' in r['prompt'].lower() for r in results)

    async def test_get_related_prompts(self, db: AsyncSession):
        """Test getting related prompts."""
        service = ProductManagementPromptsService(db)
        related = await service.get_related_prompts('rs_001')

        assert len(related) > 0
        assert all('id' in r for r in related)

    async def test_execute_prompt(self, db: AsyncSession, test_user: User):
        """Test executing a prompt."""
        service = ProductManagementPromptsService(db)

        result = await service.execute_prompt(
            prompt_id='rs_001',
            user_id=test_user.id,
            context={'team_size': 10},
            use_ai=False
        )

        assert 'prompt' in result
        assert 'execution_id' in result
        assert result['use_ai'] is False
        assert result['prompt']['id'] == 'rs_001'

    async def test_get_prompt_workflow(self, db: AsyncSession):
        """Test getting workflow for a goal."""
        service = ProductManagementPromptsService(db)

        workflow = await service.get_prompt_workflow('feature_launch')

        assert len(workflow) > 0
        assert all('id' in w for w in workflow)
        # Verify it includes expected prompts
        workflow_ids = [w['id'] for w in workflow]
        assert 'rs_002' in workflow_ids  # Generate feature brief

    async def test_get_prompts_by_use_case(self, db: AsyncSession):
        """Test getting prompts by use case."""
        service = ProductManagementPromptsService(db)

        prompts = await service.get_prompts_by_use_case('Quarterly planning')

        assert len(prompts) > 0
        assert any(
            'quarterly planning' in uc.lower()
            for p in prompts
            for uc in p['use_cases']
        )

    async def test_execution_tracking(self, db: AsyncSession, test_user: User):
        """Test that executions are tracked in the database."""
        service = ProductManagementPromptsService(db)

        # Execute prompt
        await service.execute_prompt(
            prompt_id='rs_001',
            user_id=test_user.id,
            use_ai=False
        )

        # Verify it was tracked
        from sqlalchemy import select

        query = select(PromptExecution).where(
            PromptExecution.user_id == test_user.id,
            PromptExecution.prompt_id == 'rs_001'
        )
        result = await db.execute(query)
        execution = result.scalar_one_or_none()

        assert execution is not None
        assert execution.status == 'completed'


# ============================================================================
# API Endpoint Tests
# ============================================================================


@pytest.mark.asyncio
class TestProductManagementAPI:
    """Test suite for Product Management API endpoints."""

    async def test_get_prompts_unauthorized(self, client: AsyncClient):
        """Test that getting prompts requires authentication."""
        response = await client.get('/api/v1/product-management/prompts')
        assert response.status_code == 401

    async def test_get_prompts_authorized(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting prompts while authenticated."""
        response = await authenticated_client.get('/api/v1/product-management/prompts')
        assert response.status_code == 200

        data = response.json()
        assert 'total' in data
        assert 'prompts' in data
        assert data['total'] > 0

    async def test_get_prompt_by_id(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting a specific prompt."""
        response = await authenticated_client.get('/api/v1/product-management/prompts/rs_001')
        assert response.status_code == 200

        data = response.json()
        assert data['id'] == 'rs_001'
        assert 'prompt' in data

    async def test_get_nonexistent_prompt(self, authenticated_client: AsyncClient):
        """Test getting a prompt that doesn't exist."""
        response = await authenticated_client.get('/api/v1/product-management/prompts/invalid_id')
        assert response.status_code == 404

    async def test_get_categories(self, authenticated_client: AsyncClient):
        """Test getting all categories."""
        response = await authenticated_client.get('/api/v1/product-management/categories')
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 5
        assert all('name' in cat for cat in data)

    async def test_filter_prompts_by_category(self, authenticated_client: AsyncClient):
        """Test filtering prompts by category."""
        response = await authenticated_client.get(
            '/api/v1/product-management/prompts?category=roadmap_strategy'
        )
        assert response.status_code == 200

        data = response.json()
        assert data['filters']['category'] == 'roadmap_strategy'

    async def test_search_prompts(self, authenticated_client: AsyncClient):
        """Test searching prompts."""
        response = await authenticated_client.get('/api/v1/product-management/prompts/search/roadmap')
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

    async def test_execute_prompt(self, authenticated_client: AsyncClient):
        """Test executing a prompt."""
        response = await authenticated_client.post(
            '/api/v1/product-management/prompts/execute',
            json={
                'prompt_id': 'rs_001',
                'use_ai': False
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert 'execution_id' in data
        assert 'prompt' in data

    async def test_execute_invalid_prompt(self, authenticated_client: AsyncClient):
        """Test executing an invalid prompt."""
        response = await authenticated_client.post(
            '/api/v1/product-management/prompts/execute',
            json={
                'prompt_id': 'invalid_id',
                'use_ai': False
            }
        )
        assert response.status_code == 404

    async def test_add_favorite(self, authenticated_client: AsyncClient):
        """Test adding a prompt to favorites."""
        response = await authenticated_client.post(
            '/api/v1/product-management/favorites',
            json={'prompt_id': 'rs_001'}
        )
        assert response.status_code == 200

        data = response.json()
        assert data['status'] == 'success'

    async def test_add_duplicate_favorite(self, authenticated_client: AsyncClient):
        """Test that duplicate favorites are rejected."""
        # Add once
        await authenticated_client.post(
            '/api/v1/product-management/favorites',
            json={'prompt_id': 'rs_001'}
        )

        # Try to add again
        response = await authenticated_client.post(
            '/api/v1/product-management/favorites',
            json={'prompt_id': 'rs_001'}
        )
        assert response.status_code == 400

    async def test_get_favorites(self, authenticated_client: AsyncClient):
        """Test getting user's favorites."""
        # First add a favorite
        await authenticated_client.post(
            '/api/v1/product-management/favorites',
            json={'prompt_id': 'rs_001'}
        )

        # Get favorites
        response = await authenticated_client.get('/api/v1/product-management/favorites')
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

    async def test_remove_favorite(self, authenticated_client: AsyncClient):
        """Test removing a favorite."""
        # First add a favorite
        await authenticated_client.post(
            '/api/v1/product-management/favorites',
            json={'prompt_id': 'rs_001'}
        )

        # Remove it
        response = await authenticated_client.delete('/api/v1/product-management/favorites/rs_001')
        assert response.status_code == 200

    async def test_get_workflow(self, authenticated_client: AsyncClient):
        """Test getting a workflow."""
        response = await authenticated_client.get('/api/v1/product-management/workflows/feature_launch')
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

    async def test_get_invalid_workflow(self, authenticated_client: AsyncClient):
        """Test getting an invalid workflow."""
        response = await authenticated_client.get('/api/v1/product-management/workflows/invalid_goal')
        assert response.status_code == 404

    async def test_rate_execution(
        self,
        authenticated_client: AsyncClient,
        test_user: User
    ):
        """Test rating an execution."""
        # First execute a prompt
        exec_response = await authenticated_client.post(
            '/api/v1/product-management/prompts/execute',
            json={'prompt_id': 'rs_001', 'use_ai': False}
        )
        execution_data = exec_response.json()
        execution_id = execution_data['execution_id']

        # Rate it
        response = await authenticated_client.post(
            f'/api/v1/product-management/executions/{execution_id}/rate',
            json={'quality_rating': 5, 'feedback': 'Excellent!'}
        )
        assert response.status_code == 200


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
class TestProductManagementIntegration:
    """Integration tests for the complete workflow."""

    async def test_complete_prompt_workflow(
        self,
        db: AsyncSession,
        authenticated_client: AsyncClient
    ):
        """Test the complete workflow from discovery to execution."""
        # 1. Discover prompts
        response = await authenticated_client.get('/api/v1/product-management/prompts')
        assert response.status_code == 200
        prompts = response.json()['prompts']

        # 2. Get a specific prompt
        prompt_id = prompts[0]['id']
        response = await authenticated_client.get(f'/api/v1/product-management/prompts/{prompt_id}')
        assert response.status_code == 200
        prompt = response.json()

        # 3. Add to favorites
        response = await authenticated_client.post(
            '/api/v1/product-management/favorites',
            json={'prompt_id': prompt_id}
        )
        assert response.status_code == 200

        # 4. Execute prompt
        response = await authenticated_client.post(
            '/api/v1/product-management/prompts/execute',
            json={'prompt_id': prompt_id, 'use_ai': False}
        )
        assert response.status_code == 200
        execution = response.json()

        # 5. Rate execution
        response = await authenticated_client.post(
            f"/api/v1/product-management/executions/{execution['execution_id']}/rate",
            json={'quality_rating': 4}
        )
        assert response.status_code == 200

    async def test_workflow_execution(
        self,
        db: AsyncSession,
        authenticated_client: AsyncClient
    ):
        """Test executing a complete workflow."""
        # Get workflow
        response = await authenticated_client.get('/api/v1/product-management/workflows/feature_launch')
        assert response.status_code == 200
        workflow = response.json()

        # Execute each prompt in the workflow
        for prompt in workflow:
            response = await authenticated_client.post(
                '/api/v1/product-management/prompts/execute',
                json={'prompt_id': prompt['id'], 'use_ai': False}
            )
            assert response.status_code == 200


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.asyncio
class TestProductManagementPerformance:
    """Performance tests for prompt operations."""

    async def test_prompt_loading_performance(self, db: AsyncSession):
        """Test that prompts load quickly."""
        import time

        service = ProductManagementPromptsService(db)

        start = time.time()
        await service._load_prompts()
        duration = time.time() - start

        assert duration < 1.0  # Should load in under 1 second

    async def test_search_performance(self, db: AsyncSession):
        """Test that search is performant."""
        import time

        service = ProductManagementPromptsService(db)

        start = time.time()
        results = await service.search_prompts('product')
        duration = time.time() - start

        assert duration < 0.5  # Search should complete in under 500ms
        assert len(results) > 0

    async def test_category_filtering_performance(self, db: AsyncSession):
        """Test that filtering by category is performant."""
        import time

        service = ProductManagementPromptsService(db)

        start = time.time()
        prompts = await service.get_prompts_by_category('roadmap_strategy')
        duration = time.time() - start

        assert duration < 0.5  # Filtering should be fast
        assert len(prompts) == 10


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    from app.services.security import get_password_hash

    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("test123"),
        full_name="Test User",
        is_active=True,
        is_verified=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    test_user: User
) -> AsyncClient:
    """Return an authenticated test client."""
    # Login and get token
    response = await client.post(
        '/api/v1/auth/login',
        json={'email': 'test@example.com', 'password': 'test123'}
    )
    token = response.json()['access_token']

    # Update client with auth header
    client.headers.update({'Authorization': f'Bearer {token}'})
    return client
