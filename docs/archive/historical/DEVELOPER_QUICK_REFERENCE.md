# Product Operations - Developer Quick Reference

## Quick Integration Guide

This guide shows how to integrate A/B testing, churn tracking, and feature requests into your code.

---

## A/B Testing Integration

### Backend (Python/FastAPI)

#### Assign User to Variant

```python
from app.services.ab_testing_service import assign_variant

@router.post("/api/signup")
async def signup(user_data: SignupRequest, current_user: User = Depends(get_current_user)):
    # Assign user to experiment
    variant = await assign_variant(
        user_id=current_user.id,
        experiment_name="signup_form_length_v1"
    )

    # Show different form based on variant
    if variant == "control":
        fields = ["email", "password", "name", "company", "phone"]
    else:  # variant_a (simplified)
        fields = ["email", "password"]

    return {"fields": fields}
```

#### Track Events

```python
from app.services.ab_testing_service import track_event

# Track when user views pricing page
await track_event(
    user_id=current_user.id,
    experiment_name="cta_color_v1",
    event_type="view",
    variant="control",
    properties={"page": "pricing"}
)

# Track conversion
await track_event(
    user_id=current_user.id,
    experiment_name="cta_color_v1",
    event_type="conversion",
    variant="control",
    properties={"value": 99.0}  # Revenue value
)
```

### Frontend (React/TypeScript)

#### Using the Hook

```typescript
import { useExperiment } from '@/hooks/useExperiment';

function PricingPage() {
  const { variant, isLoading } = useExperiment('cta_color_v1');

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <button
      className={
        variant === 'control'
          ? 'bg-blue-600 hover:bg-blue-700'
          : 'bg-green-600 hover:bg-green-700'
      }
    >
      Get Started
    </button>
  );
}
```

#### Using the Wrapper Component

```typescript
import { ExperimentWrapper, Variant } from '@/components/experiments/ExperimentWrapper';

function SignupPage() {
  return (
    <ExperimentWrapper name="signup_form_v1">
      <Variant name="control">
        <LongForm /> {/* 5 fields */}
      </Variant>
      <Variant name="variant_a">
        <ShortForm /> {/* 2 fields */}
      </Variant>
    </ExperimentWrapper>
  );
}
```

#### Tracking Conversions

```typescript
import { ExperimentAnalytics } from '@/services/experimentAnalytics';

// Track when user clicks CTA
const handleSignupClick = async () => {
  await ExperimentAnalytics.trackConversion('cta_color_v1', 99.0);
  // ... proceed with signup
};

// Track custom events
const handlePricingView = async () => {
  await ExperimentAnalytics.trackEvent('cta_color_v1', 'view', {
    page: 'pricing',
    plan: 'premium'
  });
};
```

---

## Churn Prediction Integration

### Backend (Python/FastAPI)

#### Get User's Churn Risk

```python
from app.services.churnPredictionService import ChurnRiskCalculator
from app.core.database import get_db

@router.get("/api/user/churn-risk")
async def get_churn_risk(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    calculator = ChurnRiskCalculator(db)
    risk_data = calculator.calculate_user_risk(str(current_user.id))

    return {
        "risk_level": risk_data["overall_risk"],
        "score": risk_data["overall_score"],
        "top_factors": risk_data["primary_risk_factors"],
        "recommendations": risk_data["recommended_actions"]
    }
```

#### Track User Activity (Optional Enhancement)

The churn prediction system tracks usage automatically via the scheduler, but you can also manually update signals:

```python
from app.db.models.churn_prediction import ChurnRiskScore

# When user exports data (churn signal)
async def handle_data_export(user_id: str):
    # This will be picked up by next churn scoring run
    pass

# When user views pricing (considering upgrade)
async def handle_pricing_view(user_id: str):
    # Log this event for churn prediction
    pass
```

### Frontend Display

```typescript
interface ChurnRiskProps {
  riskLevel: 'critical' | 'high' | 'medium' | 'low' | 'safe';
  score: number;
  factors: string[];
}

function ChurnRiskBanner({ riskLevel, score, factors }: ChurnRiskProps) {
  if (riskLevel === 'safe' || riskLevel === 'low') {
    return null; // Don't show banner for low-risk users
  }

  const colors = {
    critical: 'bg-red-50 border-red-200 text-red-800',
    high: 'bg-orange-50 border-orange-200 text-orange-800',
    medium: 'bg-yellow-50 border-yellow-200 text-yellow-800'
  };

  return (
    <div className={`p-4 border rounded-lg ${colors[riskLevel]}`}>
      <h3 className="font-semibold">We notice you haven't been as active lately</h3>
      <p className="text-sm mt-1">
        Based on your activity, you might benefit from: {factors.join(', ')}
      </p>
      <button className="mt-2 text-sm underline">
        Schedule a call with our team
      </button>
    </div>
  );
}
```

---

## Feature Request API

### Submit Feature Request

```python
from app.db.models.feature_requests import FeatureRequest

@router.post("/api/feature-requests")
async def create_feature_request(
    request: FeatureRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fr = FeatureRequest(
        title=request.title,
        description=request.description,
        theme=request.theme,
        request_type=request.request_type,
        source_type=request.source_type,
        submitted_by=current_user.id,
        customer_id=current_user.id if request.source_type == "customer" else None
    )

    db.add(fr)
    db.commit()

    return {"id": str(fr.id), "status": "created"}
```

### Vote for Feature Request

```python
@router.post("/api/feature-requests/{request_id}/vote")
async def vote_for_feature(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if already voted
    existing = db.query(FeatureRequestVote).filter(
        FeatureRequestVote.feature_request_id == request_id,
        FeatureRequestVote.user_id == current_user.id
    ).first()

    if existing:
        return {"message": "Already voted"}

    # Add vote
    vote = FeatureRequestVote(
        feature_request_id=request_id,
        user_id=current_user.id
    )
    db.add(vote)
    db.commit()

    return {"message": "Vote recorded"}
```

### Frontend: Feature Request Form

```typescript
function FeatureRequestForm() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiClient.post('/api/v1/feature-requests', {
      title,
      description,
      theme: 'UX',
      request_type: 'ENH',
      source_type: 'customer'
    });
    // Show success message
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Feature title"
        required
      />
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Describe the feature..."
        required
      />
      <button type="submit">Submit Request</button>
    </form>
  );
}
```

---

## Activation Tracking Integration

### Track Milestones

```python
from app.db.models.user_activation import UserActivation

@router.post("/api/assessments/complete")
async def complete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Process assessment...

    # Update activation tracking
    activation = db.query(UserActivation).filter(
        UserActivation.user_id == current_user.id
    ).first()

    if activation:
        activation.mark_assessment_completed()

    db.commit()
```

### Get Activation Dashboard

```python
@router.get("/api/analytics/activation")
async def get_activation_metrics(
    period: str = "month",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Already implemented in app/api/v1/endpoints/activation.py
    pass
```

---

## Testing Your Integrations

### Unit Tests

```python
import pytest
from app.services.ab_testing_service import assign_variant

@pytest.mark.asyncio
async def test_assign_variant_consistency(db_session):
    """Same user should get same variant"""
    user_id = "test-user-123"
    experiment = "test_experiment_v1"

    variant1 = await assign_variant(user_id, experiment)
    variant2 = await assign_variant(user_id, experiment)

    assert variant1 == variant2  # Should be consistent
```

### Integration Tests

```python
import pytest
from fastapi.testclient import TestClient

def test_ab_experiment_assignment(client: TestClient, auth_headers):
    """Test experiment assignment via API"""
    response = client.post(
        "/api/v1/ab/assign",
        json={"experiment": "test_experiment"},
        headers=auth_headers
    )

    assert response.status_code == 200
    assert "variant" in response.json()
    assert response.json()["variant"] in ["control", "variant_a"]
```

---

## Common Patterns

### Pattern 1: Gradual Rollout

```python
# Start with 10% traffic, increase if no issues
async def get_rollout_percentage(experiment_name: str):
    # Could be stored in database or config
    rollout_config = {
        "new_feature_v1": 0.10,  # 10% get feature
        "redesign_v2": 1.00,     # 100% get feature (fully rolled out)
    }
    return rollout_config.get(experiment_name, 0)
```

### Pattern 2: Kill Switch

```python
import os

def is_feature_enabled(feature_name: str) -> bool:
    """Quick way to disable feature without redeploy"""
    return os.getenv(f"FEATURE_{feature_name.upper()}_ENABLED", "true") == "true"

# Usage
if is_feature_enabled("new_dashboard"):
    return NewDashboard()
else:
    return OldDashboard()
```

### Pattern 3: Whitelist Users

```python
async def is_user_in_whitelist(user_id: str, feature_name: str) -> bool:
    """Allow specific users to see feature before rollout"""
    result = await db.execute(
        select(FeatureFlag).where(
            FeatureFlag.user_id == user_id,
            FeatureFlag.feature_name == feature_name,
            FeatureFlag.enabled == True
        )
    )
    return result.first() is not None
```

---

## Performance Considerations

### A/B Testing

- ✅ Good: Low overhead, deterministic assignment
- ⚠️ Watch: Don't create too many experiments (< 100 active)
- ⚠️ Watch: Don't run experiments forever (< 90 days)

### Churn Prediction

- ✅ Good: Batch processing, runs in background
- ⚠️ Watch: Don't run too frequently (daily is enough)
- ⚠️ Watch: Large user bases need longer to process

### Feature Requests

- ✅ Good: Simple CRUD, low impact
- ✅ Good: Can be cached easily
- No major performance concerns

---

## Troubleshooting

### "User not seeing expected variant"

**Check:**
1. Is experiment running? (`status='running'`)
2. Was user assigned before experiment started?
3. Is there caching in the frontend? (Clear localStorage)
4. Is traffic split correct? (Check config)

### "Churn score is always 0"

**Check:**
1. Has churn scheduler run? (`python -m app.services.churnScheduler --mode summary`)
2. Does user have activity data?
3. Are signal calculations implemented? (Check churnPredictionService.py)

### "Feature request not sorting by RICE"

**Check:**
1. Are all RICE fields populated?
2. Is rice_score calculated correctly?
3. Is the query ordering by `rice_score DESC`?

---

## Quick Command Reference

```bash
# Run A/B test assignment (for testing)
curl -X POST http://localhost:8000/api/v1/ab/assign \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"experiment": "test_v1"}'

# Get experiment results
curl http://localhost:8000/api/v1/ab/experiments/{id}/results \
  -H "Authorization: Bearer $TOKEN"

# Run churn scoring
python -m app.services.churnScheduler --mode recent --days 7

# Get churn summary
python -m app.services.churnScheduler --mode summary

# Create feature request
curl -X POST http://localhost:8000/api/v1/feature-requests \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Dark Mode", "description": "...", "theme": "UX", ...}'

# Vote for feature request
curl -X POST http://localhost:8000/api/v1/feature-requests/{id}/vote \
  -H "Authorization: Bearer $TOKEN"
```

---

## Need Help?

- **A/B Testing Questions**: DM @product-ops
- **Churn Prediction Issues**: DM @data-team
- **Feature Request Bugs**: Open GitHub issue
- **Documentation**: See `docs/TEAM_TRAINING_GUIDE.md`

Last updated: 2025-01-12
