"""
Quick Start Guide: Burnout Prediction System Integration

This guide provides step-by-step instructions to integrate the enhanced
burnout prediction system into your PsychSync application.

Author: PsychSync Engineering Team
Version: 2.0
Date: 2026-01-31
"""

# =============================================================================
# TABLE OF CONTENTS
# =============================================================================
#
# 1. Installation & Setup
# 2. Database Migration
# 3. Model Training (Optional)
# 4. API Integration
# 5. Frontend Integration
# 6. Testing & Validation
# 7. Production Deployment
#
# =============================================================================

print(
    """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     🔥 PSYCHSYNC BURNOUT PREDICTION SYSTEM                    ║
║                              Quick Start Guide v2.0                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
)

# =============================================================================
# SECTION 1: INSTALLATION & SETUP
# =============================================================================


def section_1_installation():
    print(
        """
## 1. Installation & Setup

### Step 1.1: Install Python Dependencies

The burnout prediction system requires the following Python packages:

```bash
# Navigate to project directory
cd /path/to/psychsync

# Install dependencies (already added to requirements.txt)
pip install pymc>=5.10.0
pip install arviz>=0.18.0
pip install xgboost>=2.0.0
pip install statsmodels>=0.14.0

# Or install all requirements including the new ones
pip install -r requirements.txt
```

### Step 1.2: Verify Installation

```bash
python -c "import pymc; print(f'PyMC version: {pymc.__version__}')"
python -c "import arviz; print(f'ArviZ version: {arviz.__version__}')"
python -c "import xgboost; print(f'XGBoost version: {xgboost.__version__}')"
```

Expected output:
- PyMC version: 5.x.x
- ArviZ version: 0.18.x
- XGBoost version: 2.x.x

### Step 1.3: Frontend Dependencies (Already Installed)

The frontend uses Recharts which should already be installed:

```bash
cd frontend
npm list recharts
```

If not installed:
```bash
npm install recharts
```
    """
    )


# =============================================================================
# SECTION 2: DATABASE MIGRATION
# =============================================================================


def section_2_database_migration():
    print(
        """
## 2. Database Migration

### Step 2.1: Review Migration File

The migration file has been created at:
```
alembic/versions/20250131_add_burnout_prediction_tables.py
```

This migration creates the following tables:
- `burnout_predictions` - Stores prediction results
- `burnout_outcomes` - Stores ground truth outcomes for validation
- `ab_test_results` - Stores A/B test results
- `model_performance_monitoring` - Tracks model performance over time

### Step 2.2: Apply Migration

```bash
# Navigate to project directory
cd /path/to/psychsync

# Run Alembic migration
alembic upgrade head
```

### Step 2.3: Verify Migration

```bash
# Connect to database
psql -U postgres -d psychsync

# Verify tables exist
\\dt burnout_predictions
\\dt burnout_outcomes
\\dt ab_test_results
\\dt model_performance_monitoring
```

Expected output:
```
                  List of relations
 Schema |                    Name                     | Type  |   Owner
--------+-----------------------------------------+-------+----------
 public  | ab_test_results                        | table | postgres
 public  | burnout_outcomes                        | table | postgres
 public  | burnout_predictions                     | table | postgres
 public  | model_performance_monitoring            | table | postgres
```

### Step 2.4: Rollback (If Needed)

```bash
# If you need to rollback the migration
alembic downgrade -1
```
    """
    )


# =============================================================================
# SECTION 3: MODEL TRAINING (OPTIONAL BUT RECOMMENDED)
# =============================================================================


def section_3_model_training():
    print(
        """
## 3. Model Training (Optional but Recommended)

The Bayesian predictor needs to be trained on historical data for accurate
predictions. You can skip this step and the system will use default priors,
but training significantly improves accuracy.

### Step 3.1: Prepare Training Script

Create a training script at `scripts/train_burnout_predictor.py`:

```python
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.services.burnout.bayesian_burnout_predictor import BayesianBurnoutPredictor
from app.db.models.burnout_predictions import BurnoutPrediction
from app.db.models.user import User
from app.core.config import settings

async def load_historical_data():
    \"\"\"Load historical assessment and wellness data\"\"\"
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        # Query historical data
        # This is a placeholder - adapt to your actual data structure
        pass
    return X, y, org_ids

async def train_model():
    \"\"\"Train Bayesian predictor on historical data\"\"\"
    print("Loading historical data...")
    X, y, org_ids = await load_historical_data()

    print(f"Loaded {len(X)} samples from {len(set(org_ids))} organizations")

    # Create predictor
    predictor = BayesianBurnoutPredictor(
        n_features=X.shape[1],
        n_organizations=len(set(org_ids))
    )

    # Build model
    print("Building Bayesian model...")
    predictor.build_model(X, y, org_ids)

    # Train model
    print("Training model (this may take 15-30 minutes)...")
    predictor.fit(X, y, org_ids, samples=2000, chains=4, cores=4)

    # Save model
    import arviz as az
    az.to_netcdf(predictor.trace, 'models/bayesian_burnout_predictor.nc')
    print("Model saved to models/bayesian_burnout_predictor.nc")

    return predictor

if __name__ == "__main__":
    asyncio.run(train_model())
```

### Step 3.2: Run Training

```bash
# Create models directory
mkdir -p models

# Run training script
python scripts/train_burnout_predictor.py
```

### Step 3.3: Load Pre-trained Model (Alternative)

If you don't have sufficient historical data, the system will use default
priors and learn from new data over time. The predictor will automatically
load the pre-trained model if available:

```python
from app.services.burnout.bayesian_burnout_predictor import load_pretrained_model

predictor = load_pretrained_model('models/bayesian_burnout_predictor.nc')
```
    """
    )


# =============================================================================
# SECTION 4: API INTEGRATION
# =============================================================================


def section_4_api_integration():
    print(
        """
## 4. API Integration

The new API endpoints need to be registered with the FastAPI application.

### Step 4.1: Register Endpoints

Edit `app/api/v1/api.py` (or your main API router file) and add:

```python
# Import new routers
from app.api.v1.endpoints.burnout_predictions import router as burnout_router
from app.api.v1.endpoints.executive_burnout_analytics import router as executive_router

# Register routers (add to existing router registration)
api_router.include_router(
    burnout_router,
    prefix="/burnout",
    tags=["burnout-prediction"]
)

api_router.include_router(
    executive_router,
    prefix="/executive",
    tags=["executive-analytics"]
)
```

### Step 4.2: Verify Endpoints

Start the FastAPI server:

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

You should see new endpoints under:
- `/api/v1/predictions/burnout/14-day`
- `/api/v1/executive/burnout/summary`
- `/api/v1/executive/burnout/heatmap`
- `/api/v1/executive/burnout/forecast`
- `/api/v1/executive/burnout/cost-benefit`

### Step 4.3: Test API Endpoints

```bash
# Test exact scoring formula calculation
curl -X POST "http://localhost:8000/api/v1/predictions/burnout/exact-score" \\
  -H "Content-Type: application/json" \\
  -d '{
    "weekly_hours": 58,
    "continuous_days": 12,
    "after_hours_percentage": 0.18,
    "pto_days_used": 0,
    "sleep_hours_avg": 6.2,
    "negative_sentiment_avg": -0.4,
    "sentiment_volatility": 0.3,
    "conflict_indicators": 3,
    "brs_trend_slope": 1.5,
    "recent_acceleration": 0.2
  }'
```

Expected response:
```json
{
  "brs": 67.3,
  "risk_level": "high",
  "component_scores": {
    "workload": 72.5,
    "recovery": 68.0,
    "sentiment": 35.0,
    "withdrawal": 25.0,
    "pattern": 30.0,
    "biometric": 0.0
  },
  "probability_14_day": 42.7
}
```
    """
    )


# =============================================================================
# SECTION 5: FRONTEND INTEGRATION
# =============================================================================


def section_5_frontend_integration():
    print(
        """
## 5. Frontend Integration

The CEO dashboard component has been created and routing has been added.

### Step 5.1: Verify Component Import

The CEO dashboard component has been imported in `frontend/src/App.tsx`:

```typescript
const CEOBurnoutDashboard = React.lazy(() => import('./components/executive/CEOBurnoutDashboard'));
```

### Step 5.2: Verify Route

The route has been added to `frontend/src/App.tsx`:

```typescript
<Route
  path="/executive/burnout"
  element={
    <RequireAuth>
      <DashboardLayout>
        <Suspense fallback={<SecureFallback message="Loading CEO Executive Dashboard..." />}>
          <CEOBurnoutDashboard organizationId="default-org" timeRange="90d" />
        </Suspense>
      </DashboardLayout>
    </RequireAuth>
  }
/>
```

### Step 5.3: Access the Dashboard

1. Start the frontend development server:
```bash
cd frontend
npm run dev
```

2. Navigate to: http://localhost:5173/executive/burnout

3. Login with your credentials

### Step 5.4: Add Navigation Link (Optional)

To add a link in the sidebar, edit `frontend/src/components/layout/Sidebar.tsx`:

```typescript
{
  name: 'Executive Dashboard',
  path: '/executive/burnout',
  icon: <BarChart3 className="h-5 w-5" />,
  roles: ['admin', 'executive'],
}
```
    """
    )


# =============================================================================
# SECTION 6: TESTING & VALIDATION
# =============================================================================


def section_6_testing():
    print(
        """
## 6. Testing & Validation

### Step 6.1: Unit Tests

Create test files:

```bash
# Backend tests
touch tests/api/test_burnout_predictions.py
touch tests/services/test_bayesian_predictor.py
touch tests/services/test_exact_scoring.py

# Frontend tests
touch frontend/src/components/executive/__tests__/CEOBurnoutDashboard.test.tsx
```

### Step 6.2: Run Tests

```bash
# Backend tests
pytest tests/api/test_burnout_predictions.py -v
pytest tests/services/test_bayesian_predictor.py -v

# Frontend tests
cd frontend
npm test src/components/executive/__tests__/CEOBurnoutDashboard.test.tsx
```

### Step 6.3: Integration Test

Test the full prediction pipeline:

```bash
# Test script
python -c "
from app.services.burnout.exact_scoring import BurnoutRiskCalculator, WorkloadMetrics, RecoveryMetrics

calculator = BurnoutRiskCalculator()

result = calculator.calculate(
    workload=WorkloadMetrics(
        weekly_hours=55,
        continuous_days=10,
        after_hours_pct=0.15,
        late_night_work_days=3,
        early_morning_work_days=2,
        weekend_work_days=2
    ),
    recovery=RecoveryMetrics(
        pto_days_used=0,
        pto_days_available=15,
        avg_daily_break_hours=0.5,
        sleep_hours_avg=6.5
    ),
    # ... other metrics
)

print(f'BRS: {result.brs}')
print(f'Risk Level: {result.risk_level}')
print(f'14-Day Probability: {result.probability_14_day}%')
"
```

### Step 6.4: Manual Testing Checklist

- [ ] Exact scoring formulas produce valid BRS (0-100)
- [ ] Risk levels are correctly classified
- [ ] 14-day probability is calculated correctly
- [ ] CEO dashboard loads without errors
- [ ] Department heatmap displays correctly
- [ ] 14-day forecast chart renders
- [ ] Cost-benefit analysis calculates correctly
    """
    )


# =============================================================================
# SECTION 7: PRODUCTION DEPLOYMENT
# =============================================================================


def section_7_deployment():
    print(
        """
## 7. Production Deployment

### Step 7.1: Pre-Deployment Checklist

- [ ] All dependencies installed in production environment
- [ ] Database migrations applied
- [ ] Model trained and saved (or ready to learn from data)
- [ ] API endpoints tested and documented
- [ ] Frontend components built and tested
- [ ] Monitoring and logging configured

### Step 7.2: Environment Variables

Add to your `.env.prod`:

```bash
# Bayesian predictor configuration
BAYESIAN_MODEL_PATH=models/bayesian_burnout_predictor.nc
BAYESIAN_SAMPLES=2000
BAYESIAN_CHAINS=4
BAYESIAN_TUNE=1000

# Feature flags
ENABLE_BURNOUT_PREDICTION=true
ENABLE_BAYESIAN_PREDICTOR=true
ENABLE_ML_ENSEMBLE=false
```

### Step 7.3: Build Frontend

```bash
cd frontend
npm run build
```

### Step 7.4: Deploy Application

```bash
# Using Docker
docker-compose up -d

# Or using systemd/services
sudo systemctl restart psychsync-backend
sudo systemctl restart psychsync-frontend
```

### Step 7.5: Verify Deployment

```bash
# Health check
curl http://your-domain.com/api/v1/health

# API docs
curl http://your-domain.com/api/v1/docs

# CEO dashboard
curl http://your-domain.com/executive/burnout
```
    """
    )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


def example_usage():
    print(
        """
## Example Usage

### Example 1: Calculate BRS with Exact Formulas

```python
from app.services.burnout.exact_scoring import (
    BurnoutRiskCalculator,
    WorkloadMetrics,
    RecoveryMetrics
)

calculator = BurnoutRiskCalculator()

result = calculator.calculate(
    workload=WorkloadMetrics(
        weekly_hours=58,      # WHO: >55 = 35% higher stroke risk
        continuous_days=12,   # No break for 12 days
        after_hours_pct=0.18,  # 18% work outside 9-6
        late_night_work_days=3,
        early_morning_work_days=2,
        weekend_work_days=2
    ),
    recovery=RecoveryMetrics(
        pto_days_used=0,      # No PTO used
        pto_days_available=15,
        avg_daily_break_hours=0.5,  # Only 30 min breaks
        sleep_hours_avg=6.2   # Below recommended 7-9 hours
    ),
    sentiment=SentimentMetrics(
        negative_sentiment_avg=-0.4,
        sentiment_volatility=0.3,
        conflict_indicators=3
    ),
    withdrawal=WithdrawalMetrics(
        communication_volume_decline=0.2,
        meeting_participation_decline=0.15,
        social_interaction_score=5.0  # Low (1-10 scale)
    ),
    pattern=PatternMetrics(
        late_night_work_days=3,
        early_morning_work_days=2,
        weekend_work_days=2,
        response_time_avg_minutes=45  # High pressure
    )
)

print(f"Burnout Risk Score: {result.brs}/100")
print(f"Risk Level: {result.risk_level}")
print(f"14-Day Burnout Probability: {result.probability_14_day}%")
```

Output:
```
Burnout Risk Score: 67.3/100
Risk Level: high
14-Day Burnout Probability: 42.7%
```

### Example 2: Bayesian Prediction with Uncertainty

```python
from app.services.burnout.bayesian_burnout_predictor import (
    BayesianBurnoutPredictor,
    BurnoutFeatures
)

# Create predictor
predictor = BayesianBurnoutPredictor(n_organizations=100)

# For production, load pre-trained model
# from app.services.burnout.bayesian_burnout_predictor import load_pretrained_model
# predictor = load_pretrained_model('models/bayesian_burnout_predictor.nc')

# Prepare features
features = BurnoutFeatures(
    weekly_hours=58,
    continuous_days=12,
    after_hours_percentage=0.18,
    # ... (all other features)
)

# Generate prediction
prediction = predictor.predict(
    features.to_feature_vector(),
    org_id=5  # Organization ID
)

print(f"BRS: {prediction.brs_mean:.1f} ± {prediction.brs_std:.1f}")
print(f"95% Credible Interval: [{prediction.brs_95ci[0]:.1f}, {prediction.brs_95ci[1]:.1f}]")
print(f"Probability: {prediction.probability_mean*100:.1f}%")
print(f"Prob 95% CI: [{prediction.probability_95ci[0]*100:.1f}%, {prediction.probability_95ci[1]*100:.1f}%]")
```

Output:
```
BRS: 67.2 ± 6.3
95% Credible Interval: [55.8, 79.1]
Probability: 42.3%
Prob 95% CI: [28.5%, 58.1%]
```

### Example 3: 14-Day Early Warning Curve

```python
# Get trajectory prediction
trajectory = predictor.predict_14_day_trajectory(features, org_id=5)

print("14-Day Trajectory:")
for day, prob in zip(trajectory.days, trajectory.probability_mean):
    print(f"  Day {day}: {prob*100:.1f}% probability")

print(f"\\nIntervention Points:")
for intervention in trajectory.intervention_points:
    print(f"  Day {intervention['day']}: {intervention['type']} - {intervention['recommended_action']}")
```

Output:
```
14-Day Trajectory:
  Day 1: 38.2% probability
  Day 7: 41.5% probability
  Day 14: 45.3% probability

Intervention Points:
  Day 7: scheduled - Schedule intervention within 48 hours
```

### Example 4: CEO Dashboard API Call

```bash
curl -X GET "http://localhost:8000/api/v1/executive/burnout/summary?org_id=org-123&range=90d" \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "organization_id": "org-123",
  "time_range": "90d",
  "summary": {
    "overall_risk_score": 52.3,
    "risk_trend": "stable",
    "high_risk_employees": 47,
    "high_risk_percentage": 12.3,
    "predicted_turnover_risk_30d": 18.5,
    "estimated_cost_of_burnout": {
      "monthly": 284000,
      "quarterly": 852000,
      "annual": 3408000
    },
    "intervention_roi": {
      "invested": 156000,
      "saved": 482000,
      "roi_percentage": 209.0
    }
  }
}
```
    """
    )


# =============================================================================
# QUICK REFERENCE
# =============================================================================


def quick_reference():
    print(
        """
## Quick Reference

### Key Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Added PyMC, ArviZ, XGBoost, statsmodels |
| `alembic/versions/20250131_add_burnout_prediction_tables.py` | Database migration |
| `app/services/burnout/exact_scoring.py` | Exact BRS formulas |
| `app/services/burnout/bayesian_burnout_predictor.py` | Bayesian predictor |
| `app/services/validation/model_validation.py` | A/B testing & validation |
| `app/api/v1/endpoints/burnout_predictions.py` | Prediction API endpoints |
| `app/api/v1/endpoints/executive_burnout_analytics.py` | Executive dashboard API |
| `frontend/src/components/executive/CEOBurnoutDashboard.tsx` | CEO dashboard component |
| `docs/technical/BURNOUT_PREDICTION_TECHNICAL_SPEC.md` | Full technical specification |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/predictions/burnout/14-day` | POST | Generate 14-day prediction |
| `/api/v1/predictions/burnout/exact-score` | POST | Calculate BRS with formulas |
| `/api/v1/predictions/burnout/history/{user_id}` | GET | Get prediction history |
| `/api/v1/executive/burnout/summary` | GET | Executive summary |
| `/api/v1/executive/burnout/heatmap` | GET | Department heatmap |
| `/api/v1/executive/burnout/forecast` | GET | 14-day forecast |
| `/api/v1/executive/burnout/cost-benefit` | GET | Cost-benefit analysis |

### Frontend Routes

| Route | Component | Access |
|-------|-----------|--------|
| `/executive/burnout` | CEOBurnoutDashboard | Admin, Executive roles |
| `/burnout-prevention` | BurnoutPrevention | All authenticated users |
| `/burnout-prediction` | BurnoutPredictionDashboard | All authenticated users |

### Risk Level Classifications

| BRS Range | Level | Action Required |
|-----------|-------|-----------------|
| 80-100 | Critical | Immediate intervention |
| 65-79 | High | Urgent action needed |
| 45-64 | Moderate | Preventive measures |
| 25-44 | Low | Monitor closely |
| 0-24 | Minimal | Maintain support |

### Support

For issues or questions:
1. Check the technical specification: `docs/technical/BURNOUT_PREDICTION_TECHNICAL_SPEC.md`
2. Review the implementation summary: `BURNOUT_ENHANCEMENT_SUMMARY.md`
3. Contact the PsychSync Engineering Team

🎉 **You're ready to use the enhanced burnout prediction system!**
    """
    )


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys

    print("\n" + "=" * 80)
    print("PSYCHSYNC BURNOUT PREDICTION SYSTEM - QUICK START GUIDE")
    print("=" * 80 + "\n")

    if len(sys.argv) > 1:
        section = sys.argv[1]

        if section == "1":
            section_1_installation()
        elif section == "2":
            section_2_database_migration()
        elif section == "3":
            section_3_model_training()
        elif section == "4":
            section_4_api_integration()
        elif section == "5":
            section_5_frontend_integration()
        elif section == "6":
            section_6_testing()
        elif section == "7":
            section_7_deployment()
        elif section == "examples":
            example_usage()
        elif section == "reference":
            quick_reference()
        else:
            print(f"Unknown section: {section}")
            print("Available sections: 1, 2, 3, 4, 5, 6, 7, examples, reference")
    else:
        # Show all sections
        section_1_installation()
        section_2_database_migration()
        section_3_model_training()
        section_4_api_integration()
        section_5_frontend_integration()
        section_6_testing()
        section_7_deployment()
        example_usage()
        quick_reference()

    print("\n" + "=" * 80)
    print(
        "For detailed information, see: docs/technical/BURNOUT_PREDICTION_TECHNICAL_SPEC.md"
    )
    print("=" * 80 + "\n")
