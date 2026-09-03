# Product Management Prompts - Complete Implementation Guide

## Overview

PsychSync now includes **50 curated product management prompts** organized into 5 strategic categories, enabling product teams to accelerate planning, analysis, and decision-making processes.

### Key Features

- **50 Expert-Curated Prompts**: Covering roadmap strategy, UX, growth, analytics, and operations
- **5 Category Organization**: Logical grouping for easy discovery and workflow building
- **Metadata-Rich**: Each prompt includes complexity, estimated time, outputs, and use cases
- **AI-Enhanced Execution**: Optional AI augmentation for intelligent output generation
- **Usage Tracking**: Monitor prompt effectiveness with execution history and ratings
- **Workflow Support**: Pre-built workflows for common scenarios (feature launch, quarterly planning, etc.)
- **Custom Templates**: Organizations can create custom prompts based on their needs

---

## Prompt Categories

### 1. Roadmap & Strategy (10 prompts)
**Focus**: Strategic planning, prioritization, and vision-setting

**Key Prompts**:
- Create a roadmap based on user value vs complexity
- Generate a feature brief for team analytics
- Create a product strategy for enterprise adoption
- Draft 2-year product vision
- Define upcoming AI capabilities for roadmap

**Use Cases**: Quarterly planning, product strategy reviews, stakeholder alignment

### 2. User Experience & Engagement (10 prompts)
**Focus**: User journey, onboarding, and experience optimization

**Key Prompts**:
- Define the ideal PsychSync user journey
- Define activation milestones for user onboarding
- Develop AI-driven personal insights roadmap
- Develop a freemium-to-paid upgrade journey
- Define roles/personas for PsychSync users

**Use Cases**: UX design, process optimization, customer experience

### 3. Growth & Monetization (8 prompts)
**Focus**: Revenue generation, pricing, and growth optimization

**Key Prompts**:
- Generate new revenue-generating features
- Produce retention levers for B2B SaaS teams
- Turn customer pain points into product opportunities
- Generate upsell opportunities inside the app
- Create pricing experiment frameworks

**Use Cases**: Revenue strategy, feature monetization, growth hacking

### 4. Analytics & Metrics (10 prompts)
**Focus**: KPIs, dashboards, and performance measurement

**Key Prompts**:
- Create a monthly product KPI dashboard
- Define product inputs for engineering specs
- Create KPIs for new feature success
- Generate churn prediction signals and triggers
- Perform product risk analysis

**Use Cases**: Performance tracking, executive reporting, product health

### 5. Operations & Processes (12 prompts)
**Focus**: Workflows, testing, and operational management

**Key Prompts**:
- Create requirements for the assessment engine
- Define user permissions & roles matrix
- Design cross-team collaboration workflows
- Write UX acceptance criteria
- Generate SLAs and SLOs for enterprise

**Use Cases**: Engineering handoff, QA testing, process improvement

---

## API Reference

### Base URL
```
/api/v1/product-management
```

### Endpoints

#### Get All Prompts
```http
GET /api/v1/product-management/prompts
```

**Query Parameters**:
- `category` (optional): Filter by category ID
- `complexity` (optional): Filter by complexity (low, medium, high)
- `type` (optional): Filter by type (strategic, tactical, analytical, technical, creative, experimental)

**Response**:
```json
{
  "total": 50,
  "prompts": [
    {
      "id": "rs_001",
      "prompt": "Create a roadmap based on user value vs complexity.",
      "type": "strategic",
      "complexity": "medium",
      "estimated_time": "2-3 hours",
      "outputs": ["Prioritized feature matrix", "Timeline visualization"],
      "related_prompts": ["rs_003", "gm_003"],
      "use_cases": ["Quarterly planning", "Product strategy reviews"]
    }
  ],
  "filters": {
    "category": null,
    "complexity": null,
    "type": null
  }
}
```

#### Get Prompt by ID
```http
GET /api/v1/product-management/prompts/{prompt_id}
```

**Response**: Full prompt details with category context

#### Get Categories
```http
GET /api/v1/product-management/categories
```

**Response**:
```json
[
  {
    "id": "roadmap_strategy",
    "name": "Roadmap & Strategy",
    "description": "Strategic planning, prioritization, and vision-setting",
    "icon": "roadmap",
    "prompt_count": 10
  }
]
```

#### Execute Prompt
```http
POST /api/v1/product-management/prompts/execute
```

**Request Body**:
```json
{
  "prompt_id": "rs_001",
  "context": {
    "team_size": 10,
    "current_phase": "ideation",
    "constraints": ["budget", "timeline"]
  },
  "use_ai": true
}
```

**Response**:
```json
{
  "prompt": {...},
  "execution_id": 12345,
  "executed_at": "2025-01-17T10:30:00Z",
  "use_ai": true,
  "ai_suggestion": "AI-generated strategic roadmap..."
}
```

#### Search Prompts
```http
GET /api/v1/product-management/prompts/search/{query}
```

**Query Parameters**:
- `category` (optional): Limit search to specific category

Searches in prompt text, use cases, and expected outputs.

#### Get Workflow for Goal
```http
GET /api/v1/product-management/workflows/{goal}
```

**Supported Goals**:
- `feature_launch`: Complete feature launch workflow
- `retention_improvement`: Retention optimization workflow
- `enterprise_expansion`: Enterprise expansion workflow
- `quarterly_planning`: Quarterly planning workflow

**Response**: Ordered list of prompts for the workflow

#### Get Execution History
```http
GET /api/v1/product-management/executions/history
```

**Query Parameters**:
- `limit`: Maximum number of results (default: 50)
- `prompt_id`: Filter by specific prompt

#### Rate Execution
```http
POST /api/v1/product-management/executions/{execution_id}/rate
```

**Request Body**:
```json
{
  "quality_rating": 5,
  "feedback": "Excellent insights, very actionable"
}
```

#### Favorites Management
```http
POST /api/v1/product-management/favorites
GET /api/v1/product-management/favorites
DELETE /api/v1/product-management/favorites/{prompt_id}
```

---

## Database Schema

### Tables

#### `prompt_executions`
Tracks each prompt execution with context, AI usage, and user feedback.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `prompt_id` | String(50) | Prompt identifier |
| `user_id` | Integer | User who executed |
| `executed_at` | DateTime | Execution timestamp |
| `context` | JSON | Additional context |
| `use_ai` | Boolean | AI enhancement used |
| `outputs_generated` | JSON | Generated outputs |
| `ai_output` | Text | AI suggestion |
| `status` | String(50) | Execution status |
| `quality_rating` | Integer | User rating (1-5) |
| `feedback` | Text | User feedback |

#### `prompt_templates`
Custom prompt templates created by organizations.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `organization_id` | Integer | Owner organization |
| `created_by` | Integer | Creator user |
| `name` | String(255) | Template name |
| `description` | Text | Template description |
| `category` | String(100) | Custom category |
| `prompt_text` | Text | Prompt content |
| `complexity` | String(50) | Complexity level |
| `is_active` | Boolean | Active status |
| `usage_count` | Integer | Usage counter |

#### `prompt_workflows`
Pre-defined workflows combining multiple prompts.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `name` | String(255) | Workflow name |
| `goal` | String(255) | High-level goal |
| `prompt_sequence` | JSON | Ordered prompt IDs |
| `usage_count` | Integer | Usage counter |
| `is_public` | Boolean | Shared status |

#### `prompt_favorites`
User's favorite prompts for quick access.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `user_id` | Integer | User who favorited |
| `prompt_id` | String(50) | Prompt ID |
| `created_at` | DateTime | Created timestamp |

#### `prompt_results`
Stores generated results from prompt executions.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `execution_id` | Integer | Link to execution |
| `title` | String(255) | Result title |
| `result_type` | String(100) | Result type |
| `content` | JSON | Structured data |
| `is_shared` | Boolean | Shared status |

---

## Usage Examples

### Python Client

```python
import httpx

async def execute_prompt_with_ai():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.psychsync.com/api/v1/product-management/prompts/execute",
            headers={"Authorization": "Bearer YOUR_TOKEN"},
            json={
                "prompt_id": "rs_001",
                "context": {
                    "team_size": 15,
                    "timeframe": "Q1 2025"
                },
                "use_ai": True
            }
        )
        result = response.json()
        print(f"Execution ID: {result['execution_id']}")
        print(f"AI Suggestion: {result['ai_suggestion']}")
```

### JavaScript/TypeScript Client

```typescript
import axios from 'axios';

const getWorkflowForGoal = async (goal: string) => {
  const response = await axios.get(
    `/api/v1/product-management/workflows/${goal}`,
    {
      headers: { Authorization: `Bearer ${token}` }
    }
  );
  return response.data; // Ordered list of prompts
};

// Usage
const featureLaunchWorkflow = await getWorkflowForGoal('feature_launch');
```

### React Component Example

```typescript
import { useState, useEffect } from 'react';
import { api } from '@/services/api';

export function PromptLibrary() {
  const [prompts, setPrompts] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);

  useEffect(() => {
    api.get('/product-management/prompts', {
      params: { category: selectedCategory }
    }).then(res => setPrompts(res.data.prompts));
  }, [selectedCategory]);

  return (
    <div>
      <h2>Product Management Prompts</h2>
      {prompts.map(prompt => (
        <PromptCard key={prompt.id} prompt={prompt} />
      ))}
    </div>
  );
}
```

---

## Pre-Built Workflows

### Feature Launch Workflow
```json
["rs_002", "an_002", "ux_001", "op_004", "op_010"]
```
1. Generate feature brief
2. Define product inputs for engineering specs
3. Define user journey
4. Write UX acceptance criteria
5. Design announcement playbook

### Retention Improvement Workflow
```json
["gm_002", "an_005", "ux_007", "gm_003", "an_004"]
```
1. Produce retention levers
2. Generate churn prediction signals
3. Define customer lifecycle
4. Turn pain points into opportunities
5. Create KPIs for feature success

### Enterprise Expansion Workflow
```json
["rs_003", "ux_005", "op_002", "op_011", "gm_006"]
```
1. Create enterprise strategy
2. Define enterprise personas
3. Define permissions matrix
4. Generate SLAs and SLOs
5. Create pricing tiers

### Quarterly Planning Workflow
```json
["rs_001", "an_007", "rs_005", "an_001", "op_003"]
```
1. Create roadmap based on value vs complexity
2. Build quarterly OKRs
3. Create innovation roadmap
4. Create KPI dashboard
5. Design collaboration workflows

---

## Integration with AI Services

The system supports optional AI enhancement for prompt outputs. When `use_ai: true` is set in execution requests:

1. The system constructs an enhanced prompt including:
   - Original prompt text
   - Expected outputs
   - User-provided context
   - Relevant product information

2. Sends to configured AI service (OpenAI, Anthropic, etc.)

3. Returns AI-generated suggestions alongside standard prompt details

**TODO(human)**: Integrate with actual AI service in `app/services/product_management_service.py:_generate_ai_output()`

---

## Deployment

### Database Migration

```bash
# Apply migration
alembic upgrade head

# Verify tables created
psql -U postgres -d psychsync -c "\dt prompt_*"
```

### Configuration

No additional configuration required. Prompts are loaded from `app/db/product_management_prompts.json`.

### Verification

```bash
# Test API endpoints
curl -X GET http://localhost:8000/api/v1/product-management/categories \
  -H "Authorization: Bearer YOUR_TOKEN"

# Execute a prompt
curl -X POST http://localhost:8000/api/v1/product-management/prompts/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt_id": "rs_001", "use_ai": false}'
```

---

## Analytics and Monitoring

### Usage Metrics

Track prompt effectiveness with built-in analytics:

- **Most Used Prompts**: Identify popular prompts
- **Average Quality Ratings**: Measure prompt effectiveness
- **Execution Frequency**: Monitor usage patterns
- **Category Distribution**: Understand focus areas

### Example Query

```sql
-- Top 10 most used prompts
SELECT
    prompt_id,
    COUNT(*) as execution_count,
    AVG(quality_rating) as avg_rating
FROM prompt_executions
WHERE executed_at >= NOW() - INTERVAL '30 days'
GROUP BY prompt_id
ORDER BY execution_count DESC
LIMIT 10;
```

---

## Best Practices

### For Product Managers

1. **Start with Workflows**: Use pre-built workflows before customizing
2. **Provide Context**: Include relevant context when executing prompts
3. **Rate Outputs**: Help improve the system by rating prompt executions
4. **Build Favorites**: Save frequently used prompts for quick access
5. **Iterate**: Use related prompts to explore different angles

### For Developers

1. **Cache Prompts**: The service caches prompts for performance
2. **Handle Errors**: Prompts may not exist, handle 404s gracefully
3. **Use Workflows**: Leverage workflow endpoints for common scenarios
4. **Track Executions**: Store execution IDs for later reference and rating

### For Organizations

1. **Custom Templates**: Create organization-specific prompt templates
2. **Share Workflows**: Build and share custom workflows with teams
3. **Monitor Usage**: Review prompt usage to understand team needs
4. **Gather Feedback**: Use quality ratings to identify improvement areas

---

## Extending the System

### Adding Custom Prompts

Create organization-specific prompts via the API:

```http
POST /api/v1/product-management/templates
```

### Creating Custom Workflows

Combine prompts into reusable workflows:

```http
POST /api/v1/product-management/workflows
```

### AI Service Integration

Implement custom AI service integration in:

`app/services/product_management_service.py:_generate_ai_output()`

---

## Troubleshooting

### Common Issues

**Issue**: Prompts not loading
- **Solution**: Verify `app/db/product_management_prompts.json` exists and is valid JSON

**Issue**: Database errors
- **Solution**: Run migration: `alembic upgrade head`

**Issue**: AI enhancement not working
- **Solution**: Check AI service configuration in `_generate_ai_output()`

**Issue**: Slow response times
- **Solution**: The service uses in-memory caching, first request will be slower

---

## Future Enhancements

- [ ] Multi-language support for prompts
- [ ] Advanced AI models for prompt generation
- [ ] Integration with project management tools (Jira, Linear)
- [ ] Prompt versioning and A/B testing
- [ ] Real-time collaborative prompt execution
- [ ] Export to popular formats (PDF, Notion, Confluence)
- [ ] Scheduled prompt execution with notifications
- [ ] Prompt marketplace for community contributions

---

## Support

For questions or issues:
- GitHub Issues: [psychsync/issues](https://github.com/psychsync/issues)
- Documentation: `/api/v1/docs` (Swagger UI)
- API Support: api@psychsync.com

---

**Version**: 1.0.0
**Last Updated**: 2025-01-17
**Maintainer**: PsychSync Product Team
