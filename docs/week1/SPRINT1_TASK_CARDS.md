# Sprint 1 Task Cards - Team Personality Map MVP
**Ready-to-Assign Tasks for Linear/Jira**

**Sprint:** Sprint 1 (Weeks 1-2: January 13-24, 2025)
**Goal:** Launch Team Personality Map feature - aggregate team personality data and generate actionable insights
**Success Criteria:** Backend APIs live, frontend visualizations complete, 80%+ test coverage

---

## 📋 SPRINT 1 OVERVIEW

**Sprint Dates:** January 13-24, 2025 (2 weeks)
**Sprint Goal:** Build Team Personality Map MVP - enable teams to see aggregated personality insights
**Sprint Review:** Friday, January 24, 3:30 PM PT
**Sprint Retro:** Friday, January 24, 4:30 PM PT

**Definition of Done:**
- [ ] Code reviewed and approved
- [ ] Unit tests written (80%+ coverage)
- [ ] Integration tests passing
- [ ] QA sign-off
- [ ] Documentation updated
- [ ] Deployed to staging

**Assignees:**
- Senior Backend Engineer: [Name]
- Senior Frontend Engineer: [Name]
- Data Scientist: [Name]
- QA Engineer: [Name]

---

## 🔴 BACKEND TASKS (7 cards)

### BE-101: Design Team Aggregation API Endpoint
**Priority:** P0 (Critical)
**Estimate:** 3 story points
**Assignee:** [Senior Backend Engineer]

**Description:**
Design the API endpoint for aggregating team personality data. Define request/response schemas, error handling, and caching strategy.

**Requirements:**
- Endpoint: `GET /api/v1/teams/{team_id}/personality`
- Query params: `force_refresh` (boolean, default false)
- Response: TeamPersonalityMap object with OCEAN dimension statistics
- Caching: 24-hour TTL, bypass with `force_refresh=true`
- Error handling: 404 if no assessments found, 400 if invalid team_id

**Technical Notes:**
- Use Pydantic schemas for request/response validation
- Implement async database queries
- Cache results in `team_personality_maps` table
- Use `@router.get()` decorator with proper authentication

**Dependencies:**
- BE-103: Database schema must be created first

**Acceptance Criteria:**
- [ ] API endpoint documented in OpenAPI/Swagger
- [ ] Pydantic schemas defined (request + response)
- [ ] Error cases documented (404, 400, 401, 500)
- [ ] Caching strategy documented
- [ ] Technical design doc reviewed by CTO

**Files to Create/Modify:**
- `app/schemas/team_personality.py` (Pydantic schemas)
- `app/api/v1/endpoints/teams.py` (add endpoint)
- `app/services/team_personality_service.py` (service layer)

---

### BE-102: Implement Team Personality Calculation Service
**Priority:** P0 (Critical)
**Estimate:** 5 story points
**Assignee:** [Senior Backend Engineer]

**Description:**
Implement the core service that aggregates individual personality assessments into team-level insights. Calculate statistics for each OCEAN dimension.

**Requirements:**
- Query all assessments for a team (filter by `team_id` and `framework_code="BIG_FIVE"`)
- Query all scores for those assessments
- Aggregate by Big Five dimensions (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- Calculate: avg, min, max, std_dev, distribution (quintiles)
- Generate strengths and gaps (rule-based)
- Calculate compatibility score (0-1)
- Calculate diversity score (0-1)
- Cache results in `team_personality_maps` table
- Return `TeamPersonalityMap` object

**Technical Notes:**
- Use `TeamPersonalityService` class (already implemented in `app/services/team_personality_service.py`)
- Use numpy for statistical calculations
- Handle edge cases: 0 assessments, 1 assessment, large teams (100+ members)
- Use JSONB fields for OCEAN dimension statistics

**Dependencies:**
- BE-103: Database schema must be created first

**Acceptance Criteria:**
- [ ] Service returns TeamPersonalityMap object
- [ ] Handles teams with 0 assessments (returns None)
- [ ] Handles teams with 1 assessment (graceful degradation)
- [ ] Calculates accurate statistics (validated with test data)
- [ ] Updates cache after calculation
- [ ] Unit tests cover 80%+ of code paths
- [ ] Integration test with database passes

**Files to Create/Modify:**
- `app/services/team_personality_service.py` (already created, verify it works)
- `tests/test_team_personality_service.py` (unit tests, already created)

**Test Data:**
```python
# Test with 3 team members, each with Big Five scores
# Member 1: O=4.0, C=3.5, E=4.2, A=3.8, N=2.0
# Member 2: O=3.8, C=4.0, E=3.5, A=4.0, N=2.5
# Member 3: O=4.2, C=3.8, E=4.0, A=3.5, N=2.2
# Expected: Openness avg=4.0, Conscientiousness avg=3.77, etc.
```

---

### BE-103: Create Database Schema for Team Personality Maps
**Priority:** P0 (Critical, blocks other backend tasks)
**Estimate:** 2 story points
**Assignee:** [Senior Backend Engineer]

**Description:**
Create the `team_personality_maps` table to cache aggregated team personality data.

**Requirements:**
- Table: `team_personality_maps`
- Columns:
  - `id` (UUID, primary key)
  - `team_id` (UUID, foreign key → teams.id, unique, on_delete CASCADE)
  - `assessment_ids` (JSONB, list of assessment IDs used)
  - `team_size` (integer, count of team members with assessments)
  - `composition_type` (string, e.g., "Creative & Social", "Strategic Thinkers")
  - `openness` (JSONB, statistics: avg, min, max, std_dev, distribution)
  - `conscientiousness` (JSONB, same structure)
  - `extraversion` (JSONB, same structure)
  - `agreeableness` (JSONB, same structure)
  - `neuroticism` (JSONB, same structure)
  - `strengths` (JSONB, array of strings)
  - `gaps` (JSONB, array of strings)
  - `internal_compatibility` (float, 0-1)
  - `diversity_score` (float, 0-1)
  - `calculation_version` (string, e.g., "1.0")
  - `created_at` (timestamp)
  - `updated_at` (timestamp)
- Indexes: `team_id` (unique), `updated_at` (for cache freshness)

**Technical Notes:**
- SQLAlchemy model: `app/db/models/team_personality_map.py`
- Alembic migration: `alembic/versions/XXXX_add_team_personality_map.py`
- Use JSONB for flexible schema (dimension statistics)
- Add `on_delete=CASCADE` to `team_id` foreign key

**Dependencies:**
- None (this is the first backend task)

**Acceptance Criteria:**
- [ ] SQLAlchemy model created
- [ ] Alembic migration created
- [ ] Migration run successfully (`alembic upgrade head`)
- [ ] Table exists in database (`\d team_personality_maps` in psql)
- [ ] Foreign key constraint works (cascade delete when team deleted)
- [ ] Indexes created (verify with `\d team_personality_maps`)

**Files to Create:**
- `app/db/models/team_personality_map.py` (SQLAlchemy model)
- `alembic/versions/20250112_add_team_personality_map.sql` (migration)

**SQL Schema:**
```sql
CREATE TABLE team_personality_maps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL UNIQUE REFERENCES teams(id) ON DELETE CASCADE,
    assessment_ids JSONB,
    team_size INTEGER,
    composition_type VARCHAR(100),
    openness JSONB,
    conscientiousness JSONB,
    extraversion JSONB,
    agreeableness JSONB,
    neuroticism JSONB,
    strengths JSONB,
    gaps JSONB,
    internal_compatibility FLOAT,
    diversity_score FLOAT,
    calculation_version VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_team_personality_maps_team_id ON team_personality_maps(team_id);
CREATE INDEX idx_team_personality_maps_updated_at ON team_personality_maps(updated_at);
```

---

### BE-104: Write Migration Scripts
**Priority:** P0 (Critical)
**Estimate:** 2 story points
**Assignee:** [Senior Backend Engineer]

**Description:**
Write Alembic migration scripts to create the `team_personality_maps` table and handle rollback.

**Requirements:**
- Create upgrade migration: Creates table, indexes, foreign keys
- Create downgrade migration: Drops table (cascade)
- Test migration: Run `alembic upgrade head` and `alembic downgrade -1`
- Verify rollback: Downgrade + upgrade should be idempotent

**Technical Notes:**
- Use `alembic revision --autogenerate -m "Add team personality maps"`
- Review generated migration before committing
- Add manual SQL if autogenerate misses something
- Test on local database first

**Dependencies:**
- BE-103: Database schema design must be complete

**Acceptance Criteria:**
- [ ] Migration file created
- [ ] `alembic upgrade head` succeeds
- [ ] Table created in database
- [ ] `alembic downgrade -1` succeeds
- [ ] Table dropped after downgrade
- [ ] `alembic upgrade head` again succeeds (idempotent)

**Files to Create:**
- `alembic/versions/20250112_add_team_personality_map.sql`

---

### BE-105: Implement AI-Generated Insights Service
**Priority:** P1 (High, but not blocking for MVP)
**Estimate:** 5 story points
**Assignee:** [Senior Backend Engineer]

**Description:**
Implement AI-powered insights generation using GPT-4, with fallback to rule-based insights.

**Requirements:**
- Endpoint: `GET /api/v1/teams/{team_id}/insights`
- Query params: `force_refresh` (boolean)
- Use GPT-4 API to generate 3-5 actionable insights
- Fallback to rule-based insights if GPT-4 unavailable
- Cache insights for 24 hours
- Each insight: heading, rationale, action

**Technical Notes:**
- OpenAI API: `openai.AsyncOpenAI()` client
- Prompt engineering: Structure team composition data into GPT-4 prompt
- Rule-based fallback: If OpenAI API fails, use pre-written templates
- Error handling: Timeout, rate limits, API failures
- Environment variable: `OPENAI_API_KEY` (may be unset in dev)

**Dependencies:**
- BE-102: Team composition service must be complete (uses its output)

**Acceptance Criteria:**
- [ ] GPT-4 integration working (with valid API key)
- [ ] Rule-based fallback working (without API key)
- [ ] Returns 3-5 insights per team
- [ ] Each insight has heading, rationale, action
- [ ] Caches insights for 24 hours
- [ ] Handles OpenAI API errors gracefully
- [ ] Unit tests cover both GPT-4 and fallback paths

**Files to Create/Modify:**
- `app/services/ai_insights_service.py` (AI insights service)
- `app/api/v1/endpoints/teams.py` (add `/insights` endpoint)

**GPT-4 Prompt Template:**
```
You are an expert organizational psychologist. Analyze this team's personality data and generate 3-5 actionable insights for their manager.

Team Data:
- Team size: {team_size}
- Composition type: {composition_type}
- Openness: avg={avg}, min={min}, max={max}
- Conscientiousness: avg={avg}, min={min}, max={max}
- Extraversion: avg={avg}, min={min}, max={max}
- Agreeableness: avg={avg}, min={min}, max={max}
- Neuroticism: avg={avg}, min={min}, max={max}
- Strengths: {strengths}
- Gaps: {gaps}

Generate insights in JSON format:
[
  {
    "heading": "Leverage Creative Problem-Solving",
    "rationale": "Your team scores high in Openness...",
    "action": "In your next team meeting..."
  }
]
```

---

### BE-106: Create Pydantic Schemas for API Responses
**Priority:** P0 (Critical)
**Estimate:** 2 story points
**Assignee:** [Senior Backend Engineer]

**Description:**
Create Pydantic schemas for request/response validation for team personality endpoints.

**Requirements:**
- `DimensionStats`: avg, min, max, std_dev, distribution
- `TeamCompositionResponse`: All team composition fields
- `Insight`: heading, rationale, action
- `InsightsResponse`: team_id, insights (array), generated_at, insight_count
- `TeamComparisonRequest`: team_ids (array)
- `TeamComparisonResponse`: teams (array), insights (array)

**Technical Notes:**
- Use `pydantic BaseModel`
- Add type hints for all fields
- Add validation rules (e.g., min/max values)
- Add `orm_mode = True` for compatibility with SQLAlchemy models
- Add example values for OpenAPI documentation

**Dependencies:**
- BE-103: Database schema must be defined

**Acceptance Criteria:**
- [ ] All Pydantic schemas created
- [ ] Type hints correct
- [ ] Validation rules working
- [ ] Examples render in Swagger UI
- [ ] Request/response validation works in API tests

**Files to Create:**
- `app/schemas/team_personality.py`

**Schema Example:**
```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class DimensionStats(BaseModel):
    avg: float
    min: float
    max: float
    std_dev: float
    distribution: List[float]  # [very low, low, medium, high, very high] as percentages

    class Config:
        orm_mode = True

class TeamCompositionResponse(BaseModel):
    team_id: str
    team_size: int
    composition_type: str
    openness: Optional[DimensionStats]
    conscientiousness: Optional[DimensionStats]
    extraversion: Optional[DimensionStats]
    agreeableness: Optional[DimensionStats]
    neuroticism: Optional[DimensionStats]
    strengths: List[str]
    gaps: List[str]
    internal_compatibility: Optional[float]
    diversity_score: Optional[float]
    updated_at: str

    class Config:
        orm_mode = True
```

---

### BE-107: Write Unit Tests for Aggregation Service
**Priority:** P1 (High)
**Estimate:** 3 story points
**Assignee:** [Senior Backend Engineer]

**Description:**
Write comprehensive unit tests for the team personality aggregation service.

**Requirements:**
- Test file: `tests/test_team_personality_service.py`
- Test coverage: 80%+ of code paths
- Test cases: Normal cases, edge cases, error cases
- Use pytest for test framework
- Mock database queries for unit tests

**Test Cases:**
- `TestCalculateDimensionStats` (5 tests)
  - Normal case with multiple scores
  - Empty list returns zeros
  - Uniform scores (all same)
  - Extreme values (1.0 and 5.0)
  - Distribution calculation (quintiles)
- `TestDetermineCompositionType` (5 tests)
  - Creative & Social team
  - Strategic Thinkers team
  - Balanced team
  - Empty stats
  - People-Oriented team
- `TestGenerateStrengthsAndGaps` (7 tests)
  - High openness → creative strength
  - Low conscientiousness → organization gap
  - Low neuroticism → stability strength
  - High extraversion → communication strength
  - Low diversity → diversity gap
  - Empty stats
  - Multiple strengths and gaps
- `TestCalculateCompatibility` (4 tests)
  - Optimal compatibility (std_dev ~0.7-1.0)
  - Low diversity compatibility (std_dev < 0.5)
  - High diversity compatibility (std_dev > 1.5)
  - Empty stats
- `TestCalculateDiversity` (4 tests)
  - High diversity (std_dev ~2.0)
  - Medium diversity (std_dev ~1.0)
  - Low diversity (std_dev ~0.2)
  - Empty stats

**Dependencies:**
- BE-102: Aggregation service must be implemented

**Acceptance Criteria:**
- [ ] Test file created
- [ ] All tests pass (`pytest tests/test_team_personality_service.py`)
- [ ] Coverage report shows 80%+ (`pytest --cov`)
- [ ] Edge cases covered (empty data, single member, large teams)
- [ ] Error cases covered (invalid input, database errors)

**Files to Create:**
- `tests/test_team_personality_service.py` (already created, verify it works)

**Run Tests:**
```bash
# Run all tests
pytest tests/test_team_personality_service.py -v

# Run with coverage
pytest tests/test_team_personality_service.py --cov=app.services.team_personality_service --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## 🎨 FRONTEND TASKS (7 cards)

### FE-101: Design Team Personality Map Visualization Component
**Priority:** P0 (Critical)
**Estimate:** 3 story points
**Assignee:** [Senior Frontend Engineer]

**Description:**
Design the React component for displaying team personality insights, including radar chart, strengths, gaps, and recommendations.

**Requirements:**
- Component: `TeamPersonalityMap.tsx`
- Sections:
  - Header: Team name, team size, composition type badge
  - Radar Chart: 5-axis spider chart (OCEAN dimensions)
  - Dimension Stats: Table with avg, min, max, std_dev for each dimension
  - Strengths: List of team strengths (with icons)
  - Gaps: List of potential gaps (with warning icons)
  - Scores: Compatibility score, diversity score (with progress bars)
  - Footer: Last updated timestamp, "Refresh" button
- Responsive design: Mobile, tablet, desktop
- Loading states: Skeleton loaders
- Error states: User-friendly error messages

**Technical Notes:**
- Use Recharts for radar chart (or Chart.js with react-chartjs-2)
- Use TypeScript for type safety
- Use Lucide React for icons
- Use Tailwind CSS for styling
- API integration: `GET /api/v1/teams/{team_id}/personality`

**Dependencies:**
- BE-101: Backend API endpoint must be live

**Acceptance Criteria:**
- [ ] Component renders without errors
- [ ] Radar chart displays OCEAN dimensions correctly
- [ ] Dimension stats table shows accurate data
- [ ] Strengths and gaps render with icons
- [ ] Compatibility and diversity scores show progress bars
- [ ] Refresh button triggers API call with `force_refresh=true`
- [ ] Loading skeleton displays during API call
- [ ] Error message displays if API fails
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] Component tests pass (React Testing Library)

**Files to Create:**
- `frontend/src/components/team/TeamPersonalityMap.tsx`
- `frontend/src/components/team/TeamPersonalityMap.module.css` (or use Tailwind)

**Component Structure:**
```tsx
interface TeamPersonalityMapProps {
  teamId: string;
}

interface DimensionData {
  avg: number;
  min: number;
  max: number;
  std_dev: number;
  distribution: number[];
}

interface TeamComposition {
  team_id: string;
  team_size: number;
  composition_type: string;
  openness: DimensionData | null;
  conscientiousness: DimensionData | null;
  extraversion: DimensionData | null;
  agreeableness: DimensionData | null;
  neuroticism: DimensionData | null;
  strengths: string[];
  gaps: string[];
  internal_compatibility: number | null;
  diversity_score: number | null;
  updated_at: string;
}

export default function TeamPersonalityMap({ teamId }: TeamPersonalityMapProps) {
  // Fetch team composition from API
  // Display radar chart, stats, strengths, gaps
  // Handle loading, error, empty states
}
```

---

### FE-102: Build Team Radar Chart (Spider Chart)
**Priority:** P0 (Critical)
**Estimate:** 3 story points
**Assignee:** [Senior Frontend Engineer]

**Description:**
Build a radar chart (spider chart) component to visualize team personality across 5 OCEAN dimensions.

**Requirements:**
- Component: `RadarChart.tsx`
- 5 axes: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
- Scale: 0-5 (1-5 score range)
- Team average: Shaded polygon
- Team min/max: Range indicators (optional)
- Hover tooltips: Show exact values on hover
- Responsive: Resizes on mobile
- Accessibility: Keyboard navigation, screen reader support

**Technical Notes:**
- Use Recharts `RadarChart`, `PolarGrid`, `PolarAngleAxis`, `PolarRadiusAxis`, `Radar`, `ResponsiveContainer`
- Or use Chart.js with `react-chartjs-2` (more customization)
- Color palette: Brand colors (indigo/purple)
- Animation: Smooth entry animation

**Dependencies:**
- FE-101: Team Personality Map component must be designed

**Acceptance Criteria:**
- [ ] Radar chart renders with 5 axes
- [ ] Team average displays as shaded polygon
- [ ] Hover tooltips show exact values
- [ ] Responsive design works on mobile
- [ ] Entry animation plays on mount
- [ ] Accessibility: Keyboard navigation works
- [ ] Component tests pass

**Files to Create:**
- `frontend/src/components/charts/RadarChart.tsx`

**Radar Chart Data Format:**
```typescript
interface RadarData {
  dimension: string;
  value: number;
  fullMark: number;
}

const data: RadarData[] = [
  { dimension: 'Openness', value: 4.2, fullMark: 5 },
  { dimension: 'Conscientiousness', value: 3.8, fullMark: 5 },
  { dimension: 'Extraversion', value: 4.0, fullMark: 5 },
  { dimension: 'Agreeableness', value: 3.5, fullMark: 5 },
  { dimension: 'Neuroticism', value: 2.3, fullMark: 5 },
];
```

---

### FE-103: Create Team Comparison View Component
**Priority:** P2 (Medium, can defer to Sprint 2)
**Estimate:** 5 story points
**Assignee:** [Senior Frontend Engineer]

**Description:**
Build a component to compare personality composition across multiple teams side-by-side.

**Requirements:**
- Component: `TeamComparisonView.tsx`
- UI: Team selector (multi-select), side-by-side comparison cards
- Comparison metrics:
  - Composition type badges
  - Team size
  - Diversity score (bar chart comparison)
  - Compatibility score (bar chart comparison)
  - OCEAN dimension averages (grouped bar chart)
- Insights: Auto-generated comparison insights
- Export: CSV/PDF export (optional)
- Responsive: Scrollable comparison cards on mobile

**Technical Notes:**
- Use `react-select` for multi-select dropdown
- Use Recharts for grouped bar charts
- API integration: `POST /api/v1/teams/compare-personality`
- State management: React useState for selected teams

**Dependencies:**
- BE-101: Team composition API must be live
- FE-101: Team Personality Map component must exist

**Acceptance Criteria:**
- [ ] Multi-select dropdown renders team options
- [ ] Comparison cards display side-by-side
- [ ] Grouped bar chart compares OCEAN dimensions
- [ ] Diversity/compatibility scores show bar comparison
- [ ] Auto-generated insights display
- [ ] Export button works (CSV/PDF)
- [ ] Responsive design (scrollable on mobile)
- [ ] Component tests pass

**Files to Create:**
- `frontend/src/components/team/TeamComparisonView.tsx`

---

### FE-104: Implement Insights Display Component
**Priority:** P1 (High)
**Estimate:** 2 story points
**Assignee:** [Senior Frontend Engineer]

**Description:**
Build a component to display AI-generated actionable insights for a team.

**Requirements:**
- Component: `TeamInsights.tsx`
- UI: Card-based layout, one insight per card
- Each insight card:
  - Heading (bold)
  - Rationale (italic, smaller text)
  - Action (bullet point or callout)
  - Icon: Lightbulb or similar
- Actions: "Generate New Insights" button (calls API with `force_refresh=true`)
- Loading: Skeleton loader while generating
- Error: Fallback to rule-based insights message
- Expand/collapse: Show all insights by default, allow collapsing

**Technical Notes:**
- API integration: `GET /api/v1/teams/{team_id}/insights`
- Use Lucide React icons (`Lightbulb`, `RefreshCw`)
- Use Tailwind for card styling

**Dependencies:**
- BE-105: AI insights service must be live

**Acceptance Criteria:**
- [ ] Insights display as cards
- [ ] Each insight has heading, rationale, action
- [ ] "Generate New Insights" button works
- [ ] Loading skeleton shows during generation
- [ ] Error message displays if AI fails
- [ ] Collapse/expand functionality works
- [ ] Component tests pass

**Files to Create:**
- `frontend/src/components/team/TeamInsights.tsx`

**Insight Card Example:**
```tsx
<div className="insight-card">
  <div className="insight-header">
    <Lightbulb className="icon" />
    <h3>Leverage Creative Problem-Solving</h3>
  </div>
  <p className="insight-rationale">
    Your team scores high in Openness (avg 4.2/5), which means they thrive on innovation...
  </p>
  <div className="insight-action">
    <strong>Action:</strong> In your next team meeting, introduce a "wild idea" brainstorming session...
  </div>
</div>
```

---

### FE-105: Add Loading States and Error Handling
**Priority:** P0 (Critical)
**Estimate:** 2 story points
**Assignee:** [Senior Frontend Engineer]

**Description:**
Add loading skeletons and error handling to all team personality components.

**Requirements:**
- Loading states:
  - Skeleton loaders for team composition data
  - Skeleton loader for radar chart
  - Skeleton loader for insights
- Error handling:
  - User-friendly error messages (not technical errors)
  - Retry buttons for failed API calls
  - Fallback UI when no data available
- Empty states:
  - Friendly message when team has no assessments
  - CTA to invite team members to take assessments

**Technical Notes:**
- Use React Suspense for lazy loading (optional)
- Use error boundaries for component-level error handling
- Use Tailwind for skeleton styling (`animate-pulse`)

**Dependencies:**
- FE-101: Team Personality Map component must exist
- FE-104: Insights component must exist

**Acceptance Criteria:**
- [ ] Skeleton loaders display during API calls
- [ ] Error messages show user-friendly text
- [ ] Retry buttons trigger API refetch
- [ ] Empty state displays when no data
- [ ] CTA button redirects to assessment invitation flow
- [ ] Error boundary catches component errors
- [ ] Component tests cover loading/error/empty states

**Files to Modify:**
- `frontend/src/components/team/TeamPersonalityMap.tsx`
- `frontend/src/components/team/TeamInsights.tsx`

---

### FE-106: Integrate with Backend API
**Priority:** P0 (Critical)
**Estimate:** 3 story points
**Assignee:** [Senior Frontend Engineer]

**Description:**
Integrate frontend components with backend API endpoints using axios or fetch.

**Requirements:**
- API service layer: `src/services/teamService.ts`
- Endpoints:
  - `getTeamComposition(teamId, forceRefresh?)`
  - `getTeamInsights(teamId, forceRefresh?)`
  - `compareTeams(teamIds)`
- Authentication: Include JWT token in Authorization header
- Error handling: Parse API errors, display user-friendly messages
- Caching: Cache responses in React state (or use React Query)
- Refresh: Support `force_refresh` query parameter

**Technical Notes:**
- Use `axios` with interceptors for JWT refresh
- Or use `React Query` for caching and background refetch
- TypeScript interfaces for API responses (match Pydantic schemas)

**Dependencies:**
- BE-101: Backend APIs must be live

**Acceptance Criteria:**
- [ ] Service layer functions created
- [ ] API calls include JWT token
- [ ] Error handling works for 401, 404, 500 errors
- [ ] Force refresh parameter works
- [ ] Response types match backend schemas
- [ ] Unit tests for service layer pass

**Files to Create:**
- `frontend/src/services/teamService.ts`
- `frontend/src/types/team.ts` (TypeScript interfaces)

**Service Layer Example:**
```typescript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export interface DimensionStats {
  avg: number;
  min: number;
  max: number;
  std_dev: number;
  distribution: number[];
}

export interface TeamComposition {
  team_id: string;
  team_size: number;
  composition_type: string;
  openness: DimensionStats | null;
  conscientiousness: DimensionStats | null;
  extraversion: DimensionStats | null;
  agreeableness: DimensionStats | null;
  neuroticism: DimensionStats | null;
  strengths: string[];
  gaps: string[];
  internal_compatibility: number | null;
  diversity_score: number | null;
  updated_at: string;
}

export async function getTeamComposition(
  teamId: string,
  forceRefresh: boolean = false
): Promise<TeamComposition> {
  const response = await axios.get(
    `${API_BASE}/teams/${teamId}/personality`,
    { params: { force_refresh: forceRefresh } }
  );
  return response.data;
}
```

---

### FE-107: Write Component Tests (React Testing Library)
**Priority:** P1 (High)
**Estimate:** 3 story points
**Assignee:** [Senior Frontend Engineer]

**Description:**
Write component tests for all team personality components using React Testing Library.

**Requirements:**
- Test file: `TeamPersonalityMap.test.tsx`
- Test coverage: 80%+ of component code
- Test cases:
  - Renders without crashing
  - Displays loading state
  - Displays error state
  - Displays empty state
  - Displays team composition data
  - Refresh button triggers API call
- Mock API calls using `jest.mock()` or `msw`
- Test user interactions (clicks, hovers)

**Dependencies:**
- FE-101: Team Personality Map component must exist
- FE-106: API integration must be complete

**Acceptance Criteria:**
- [ ] Test file created for each component
- [ ] All tests pass (`npm test`)
- [ ] Coverage report shows 80%+ (`npm test -- --coverage`)
- [ ] API calls mocked correctly
- [ ] User interactions tested

**Files to Create:**
- `frontend/src/components/team/TeamPersonalityMap.test.tsx`
- `frontend/src/components/team/TeamInsights.test.tsx`
- `frontend/src/components/charts/RadarChart.test.tsx`

**Test Example:**
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TeamPersonalityMap from './TeamPersonalityMap';
import { getTeamComposition } from '../../services/teamService';

jest.mock('../../services/teamService');

describe('TeamPersonalityMap', () => {
  it('renders loading state initially', () => {
    (getTeamComposition as jest.Mock).mockImplementation(() => new Promise(() => {}));
    render(<TeamPersonalityMap teamId="test-team" />);
    expect(screen.getByTestId('skeleton-loader')).toBeInTheDocument();
  });

  it('renders team composition data', async () => {
    const mockData = {
      team_id: 'test-team',
      team_size: 10,
      composition_type: 'Creative & Social',
      openness: { avg: 4.2, min: 3.0, max: 5.0, std_dev: 0.6, distribution: [0, 10, 20, 40, 30] },
      // ... other fields
    };
    (getTeamComposition as jest.Mock).mockResolvedValue(mockData);

    render(<TeamPersonalityMap teamId="test-team" />);

    await waitFor(() => {
      expect(screen.getByText('Creative & Social')).toBeInTheDocument();
      expect(screen.getByText('10 members')).toBeInTheDocument();
    });
  });
});
```

---

## 🔬 DATA SCIENCE TASKS (5 cards)

### DS-101: Validate Team Aggregation Algorithm
**Priority:** P0 (Critical)
**Estimate:** 3 story points
**Assignee:** [Data Scientist]

**Description:**
Validate the team personality aggregation algorithm for statistical accuracy and psychological validity.

**Requirements:**
- Test data: Create synthetic team data with known personality profiles
- Validation:
  - Verify avg, min, max, std_dev calculations (compare with numpy/pandas)
  - Verify distribution calculation (quintiles)
  - Test edge cases: 1 member, 100 members, extreme values
- Psychological validity:
  - Ensure composition types make sense (e.g., high O + high E = "Creative & Social")
  - Ensure strengths/gaps are psychologically meaningful
  - Review rule-based insights for accuracy

**Technical Notes:**
- Use Jupyter notebooks for validation
- Compare with manual calculations in Excel/Google Sheets
- Document validation results in markdown

**Dependencies:**
- BE-102: Aggregation service must be implemented

**Acceptance Criteria:**
- [ ] Test dataset created (10+ teams with varying sizes)
- [ ] Statistical calculations validated (avg, min, max, std_dev)
- [ ] Distribution calculation validated (quintiles)
- [ ] Edge cases tested and passing
- [ ] Composition type mapping reviewed
- [ ] Strengths/gaps rules reviewed
- [ ] Validation document created

**Files to Create:**
- `docs/validation/team_aggregation_validation.md`

---

### DS-102: Create Rule-Based Insights Fallback
**Priority:** P1 (High)
**Estimate:** 3 story points
**Assignee:** [Data Scientist]

**Description:**
Create rule-based insights as fallback when GPT-4 is unavailable. Ensure insights are psychologically sound and actionable.

**Requirements:**
- 10-15 rule-based insight templates covering common team profiles
- Each template: Heading, rationale template, action template
- Trigger conditions: High/low OCEAN scores, specific composition types
- Insights must be:
  - Psychologically grounded (based on Big Five research)
  - Actionable (specific steps, not vague advice)
  - Varied (not repetitive)
- Document the psychological basis for each rule

**Insight Template Examples:**
1. High Openness (≥4.0) → "Leverage Creative Problem-Solving"
2. Low Conscientiousness (≤2.5) → "Strengthen Project Management"
3. High Extraversion (≥4.0) → "Capitalize on Social Energy"
4. Low Neuroticism (≤2.0) → "Handle High-Pressure Situations"
5. High Agreeableness (≥4.0) → "Foster Collaborative Environment"

**Technical Notes:**
- Create templates in Markdown or JSON
- Use variables (e.g., `{avg_openness}`) for dynamic insertion
- Test with real team data

**Dependencies:**
- BE-105: AI insights service must exist (to integrate fallback)

**Acceptance Criteria:**
- [ ] 10-15 insight templates created
- [ ] Each template has heading, rationale, action
- [ ] Trigger conditions defined
- [ ] Insights are psychologically sound
- [ ] Insights are actionable
- [ ] Templates tested with real data
- [ ] Documentation created

**Files to Create:**
- `app/services/insights_templates.py` (or JSON file)
- `docs/insights/rule_based_insights_guide.md`

---

### DS-103: Test GPT-4 Prompt Engineering
**Priority:** P2 (Medium)
**Estimate:** 3 story points
**Assignee:** [Data Scientist]

**Description:**
Test and optimize GPT-4 prompts for generating high-quality team insights.

**Requirements:**
- Create 5-10 prompt variations
- Test with real team data
- Evaluate insight quality:
  - Actionability (specific vs. vague)
  - Relevance (matches team profile)
  - Variety (not repetitive)
  - Tone (professional, encouraging)
- Select best prompt template
- Document prompt engineering process

**Technical Notes:**
- Use OpenAI API playground for testing
- Compare outputs across prompt variations
- Use rating rubric for quality assessment

**Dependencies:**
- BE-105: AI insights service must be implemented
- DS-102: Rule-based insights must exist (for comparison)

**Acceptance Criteria:**
- [ ] 5-10 prompt variations created
- [ ] Tested with 10+ real teams
- [ ] Quality rubric defined
- [ ] Best prompt selected
- [ ] Prompt engineering documented

**Files to Create:**
- `docs/insights/gpt4_prompt_testing.md`

---

### DS-104: Benchmark Insights Quality
**Priority:** P2 (Medium)
**Estimate:** 5 story points
**Assignee:** [Data Scientist]

**Description:**
Benchmark AI-generated insights against rule-based insights and human expert insights.

**Requirements:**
- Create test dataset: 20 teams with varying profiles
- Generate insights using 3 methods:
  1. GPT-4 AI insights
  2. Rule-based insights
  3. Human expert insights (from organizational psychologist)
- Evaluation metrics:
  - Actionability (1-5 scale)
  - Relevance (1-5 scale)
  - Novelty (1-5 scale)
  - Psychological soundness (1-5 scale)
- Statistical analysis: Compare mean scores across methods
- Document findings and recommendations

**Technical Notes:**
- Use blinded evaluation (don't know which method generated which insight)
- Recruit 3-5 raters (organizational psychologists, managers)
- Use inter-rater reliability metrics (Fleiss' kappa)

**Dependencies:**
- DS-102: Rule-based insights must exist
- DS-103: GPT-4 prompts must be optimized

**Acceptance Criteria:**
- [ ] Test dataset created (20 teams)
- [ ] 3 insight generation methods tested
- [ ] Evaluation rubric defined
- [ ] Human expert insights collected
- [ ] Statistical analysis completed
- [ ] Benchmark report written

**Files to Create:**
- `docs/insights/insights_quality_benchmark.md`

---

### DS-105: Document Methodology
**Priority:** P1 (High)
**Estimate:** 2 story points
**Assignee:** [Data Scientist]

**Description:**
Document the team personality aggregation and insights generation methodology.

**Requirements:**
- Whitepaper sections:
  1. Introduction (what is team personality analysis?)
  2. Big Five Model (OCEAN dimensions)
  3. Team Aggregation Algorithm (how we calculate team stats)
  4. Composition Types (how we map profiles to types)
  5. Strengths and Gaps (how we generate them)
  6. AI Insights (how GPT-4 generates recommendations)
  7. Validation (statistical and psychological validity)
  8. Limitations (what the system doesn't do)
  9. Future Work (what's coming next)
- Include formulas, diagrams, examples
- Cite academic research (Big Five, team dynamics)

**Technical Notes:**
- Use Markdown or LaTeX
- Include diagrams (using Mermaid or external tools)
- Target audience: Technical customers, researchers, regulators

**Dependencies:**
- DS-101: Validation must be complete
- DS-104: Benchmarking must be complete

**Acceptance Criteria:**
- [ ] Whitepaper drafted (2000+ words)
- [ ] Formulas documented
- - [ ] Diagrams included
- [ ] Academic research cited
- [ ] Limitations section included
- [ ] Reviewed by Head of Data Science

**Files to Create:**
- `docs/whitepapers/team_personality_methodology.md`

---

## 🧪 QA TASKS (3 cards)

### QA-101: Write Integration Tests for API Endpoints
**Priority:** P0 (Critical)
**Estimate:** 5 story points
**Assignee:** [QA Engineer]

**Description:**
Write integration tests for the 3 new team personality API endpoints.

**Requirements:**
- Test file: `tests/integration/test_api_team_personality.py`
- Test cases:
  - `GET /teams/{team_id}/personality`:
    - Returns 200 with valid team_id
    - Returns 404 with invalid team_id
    - Returns cached data (fast response)
    - Returns fresh data with `force_refresh=true`
  - `GET /teams/{team_id}/insights`:
    - Returns 200 with valid team_id
    - Returns 404 with no assessments
    - Returns GPT-4 insights (if API key available)
    - Returns rule-based insights (if API key unavailable)
  - `POST /teams/compare-personality`:
    - Returns 200 with valid team_ids
    - Returns 400 with <2 team_ids
    - Returns 400 with >10 team_ids
    - Returns comparison data
- Use `pytest-asyncio` for async tests
- Use test database (not production)

**Dependencies:**
- BE-101: All backend endpoints must be implemented

**Acceptance Criteria:**
- [ ] Integration test file created
- [ ] All tests pass (`pytest tests/integration/test_api_team_personality.py`)
- [ ] Coverage includes happy path and error cases
- [ ] Tests use test database (isolated from production)
- [ ] Test data includes edge cases

**Files to Create:**
- `tests/integration/test_api_team_personality.py`

---

### QA-102: Create Test Data Set
**Priority:** P0 (Critical)
**Estimate:** 3 story points
**Assignee:** [QA Engineer]

**Description:**
Create a comprehensive test dataset for testing team personality features.

**Requirements:**
- 20 test teams with varying profiles:
  - 5 small teams (3-10 members)
  - 10 medium teams (11-50 members)
  - 5 large teams (51-100 members)
- Personality diversity:
  - 5 "Creative & Social" teams (high O, high E)
  - 5 "Strategic Thinkers" teams (high O, high C)
  - 5 "Balanced" teams (all dimensions ~3.0)
  - 5 edge cases (extreme high/low scores)
- Each team member has:
  - User account
  - Team membership
  - Completed Big Five assessment
  - Valid scores (1-5 range)
- Document test data characteristics

**Technical Notes:**
- Use factory pattern (e.g., `factory_boy`) for test data
- Use pytest fixtures for reusable test data
- Seed test database with `alembic` or custom script

**Dependencies:**
- None (can create in parallel with development)

**Acceptance Criteria:**
- [ ] Test dataset created (20 teams, 200+ users)
- [ ] All teams have members with assessments
- [ ] Test data covers edge cases
- [ ] Test data script created
- [ ] Test data documented

**Files to Create:**
- `tests/fixtures/test_team_data.py`
- `tests/scripts/seed_test_data.py`

---

### QA-103: Perform End-to-End Testing
**Priority:** P0 (Critical)
**Estimate:** 3 story points
**Assignee:** [QA Engineer]

**Description:**
Perform end-to-end testing of the Team Personality Map feature from frontend to backend.

**Requirements:**
- Test scenarios:
  1. User logs in → navigates to team dashboard → clicks "View Team Insights" → sees radar chart
  2. User clicks "Refresh" → sees updated data with force_refresh=true
  3. User clicks "Get Recommendations" → sees AI-generated insights
  4. User selects 3 teams → clicks "Compare Teams" → sees comparison view
  5. Team with no assessments → sees empty state + CTA to invite members
- Test environments:
  - Local development (localhost:8000 + localhost:5173)
  - Staging environment (if available)
- Test browsers:
  - Chrome (latest)
  - Firefox (latest)
  - Safari (latest)
  - Mobile (iOS Safari, Android Chrome)
- Document bugs in Jira/Linear

**Dependencies:**
- BE-101: All backend tasks complete
- FE-101: All frontend tasks complete

**Acceptance Criteria:**
- [ ] All 5 test scenarios pass
- [ ] Tested on 3 desktop browsers
- [ ] Tested on 2 mobile browsers
- [ ] Bugs documented in Jira/Linear
- [ ] E2E test report created

**Files to Create:**
- `docs/qa/team_personality_e2e_test_report.md`

---

## 📊 SPRINT TRACKER

### Sprint 1 Progress Dashboard

**Updated:** Daily (standup update in #sprint-updates)

**Backend Progress:**
- [ ] BE-101: Design API (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] BE-102: Implement service (5 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] BE-103: Create schema (2 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] BE-104: Write migrations (2 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] BE-105: AI insights (5 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] BE-106: Pydantic schemas (2 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] BE-107: Unit tests (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done

**Frontend Progress:**
- [ ] FE-101: Design component (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] FE-102: Radar chart (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] FE-103: Comparison view (5 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] FE-104: Insights display (2 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] FE-105: Loading/error (2 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] FE-106: API integration (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] FE-107: Component tests (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done

**Data Science Progress:**
- [ ] DS-101: Validate algorithm (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] DS-102: Rule-based insights (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] DS-103: GPT-4 prompts (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] DS-104: Benchmark quality (5 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] DS-105: Document methodology (2 pts) - [ ] Todo / [ ] In Progress / [ ] Done

**QA Progress:**
- [ ] QA-101: Integration tests (5 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] QA-102: Test dataset (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done
- [ ] QA-103: E2E testing (3 pts) - [ ] Todo / [ ] In Progress / [ ] Done

**Total Story Points:** 78 points
**Completed:** [ ] / 78 points
**In Progress:** [ ] tasks
**Blocked:** [ ] tasks

**Sprint Burndown:**
- Day 1 (Mon Jan 13): 78 pts remaining
- Day 2 (Tue Jan 14): [ ] pts remaining
- Day 3 (Wed Jan 15): [ ] pts remaining
- Day 4 (Thu Jan 16): [ ] pts remaining
- Day 5 (Fri Jan 17): [ ] pts remaining
- Day 6 (Mon Jan 20): [ ] pts remaining
- Day 7 (Tue Jan 21): [ ] pts remaining
- Day 8 (Wed Jan 22): [ ] pts remaining
- Day 9 (Thu Jan 23): [ ] pts remaining
- Day 10 (Fri Jan 24): 0 pts remaining (goal!)

---

## 🎯 DEFINITION OF DONE CHECKLIST

### For Each Task:
- [ ] Code written and committed to Git
- [ ] Code reviewed by peer/lead
- [ ] Unit tests passing (80%+ coverage)
- [ ] Integration tests passing
- [ ] Documentation updated (if applicable)
- [ ] Task moved to "Done" in Linear/Jira

### For Sprint 1 (Overall):
- [ ] All backend tasks complete (7/7)
- [ ] All frontend tasks complete (7/7)
- [ ] All data science tasks complete (5/5)
- [ ] All QA tasks complete (3/3)
- [ ] QA sign-off received
- [ ] Demo ready for sprint review
- [ ] Deployment to staging successful
- [ ] Sprint retro scheduled

---

## 📞 SPRINT 1 CONTACTS

**Sprint Lead:** [CTO Name] - cto@psychsync.io
**Product Owner:** [CPO Name] - cpo@psychsync.io
**QA Lead:** [QA Lead Name] - qa@psychsync.io

**Daily Standup:** Post updates in #sprint-updates by 10 AM PT
**Sprint Review:** Friday, January 24, 3:30 PM PT
**Sprint Retro:** Friday, January 24, 4:30 PM PT

**Sprint Board:** [Link to Linear/Jira]
**Design Mockups:** [Link to Figma]
**API Documentation:** `docs/api/TEAM_PERSONALITY_MAP_API.md`

---

**Let's build Team Personality Map MVP! 🚀**

*Document: SPRINT1_TASK_CARDS.md*
*Created: January 12, 2025*
*Sprint: Sprint 1 (Weeks 1-2, January 13-24, 2025)*
