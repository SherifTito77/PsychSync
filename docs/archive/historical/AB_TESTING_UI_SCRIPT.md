# A/B Testing UI Script
# PsychSync Frontend A/B Testing Framework

## Overview

This document provides a complete, production-ready A/B testing framework for UI experiments in PsychSync. Includes React components, custom hooks, backend integration, and ready-to-use experiment templates.

---

## Table of Contents

1. [Framework Architecture](#framework-architecture)
2. [React Implementation](#react-implementation)
3. [Backend Integration](#backend-integration)
4. [Ready-to-Use UI Experiments](#ready-to-use-ui-experiments)
5. [Analytics & Reporting](#analytics--reporting)
6. [Best Practices](#best-practices)

---

## Framework Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                         │
├─────────────────────────────────────────────────────────────┤
│  React Component                                             │
│  └─> useExperiment() Hook                                    │
│      ├─> Check localStorage (cached variant)                │
│      ├─> If not cached: Call /api/ab/assign                 │
│      ├─> Cache variant in localStorage                      │
│      └─> Return variant + track() function                  │
│           │                                                  │
│           ▼                                                  │
│  Component renders variant A, B, or Control                  │
│           │                                                  │
│           └─> track() sends events to /api/ab/track        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  POST /api/ab/assign                                         │
│  ├─> Check experiment configuration (Redis)                 │
│  ├─> Hash user_id + experiment_name                         │
│  ├─> Assign variant based on traffic split                  │
│  └─> Return variant to client                               │
│                                                              │
│  POST /api/ab/track                                          │
│  ├─> Validate event                                          │
│  ├─> Store in database (analytics_events)                   │
│  ├─> Increment metrics in Redis (for real-time)             │
│  └─> Return 200 OK                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Analytics Database                        │
├─────────────────────────────────────────────────────────────┤
│  Table: ab_experiments                                       │
│  ├─> experiment_id, name, status, start_date, end_date      │
│                                                              │
│  Table: ab_variants                                          │
│  ├─> variant_id, experiment_id, name, traffic_split         │
│                                                              │
│  Table: ab_events                                            │
│  ├─> event_id, user_id, experiment_id, variant_id,          │
│  │   event_type, timestamp, properties                      │
│                                                              │
│  Table: ab_conversions                                       │
│  ├─> conversion_id, user_id, experiment_id, variant_id,     │
│  │   conversion_type, timestamp                             │
└─────────────────────────────────────────────────────────────┘
```

---

## React Implementation

### 1. Experiment Hook

```typescript
// frontend/src/hooks/useExperiment.ts
import { useState, useEffect } from 'react';
import api from '../services/api';

export interface ExperimentConfig {
  name: string;
  variants: string[];
  trafficSplit: Record<string, number>; // { control: 0.5, variant_a: 0.5 }
  startDate: string;
  endDate: string;
}

export interface ExperimentResult {
  variant: string;
  isLoading: boolean;
  error: string | null;
  track: (eventType: string, properties?: Record<string, any>) => void;
  isControl: boolean;
}

export const useExperiment = (experimentName: string): ExperimentResult => {
  const [variant, setVariant] = useState<string>('control');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const assignVariant = async () => {
      try {
        // Check localStorage first
        const cached = localStorage.getItem(`ab_experiment_${experimentName}`);
        if (cached) {
          setVariant(cached);
          setIsLoading(false);
          return;
        }

        // Call assignment API
        const response = await api.post('/ab/assign', {
          experiment: experimentName,
          user_id: getUserId() // From your auth context
        });

        const assignedVariant = response.data.variant;
        setVariant(assignedVariant);

        // Cache in localStorage
        localStorage.setItem(`ab_experiment_${experimentName}`, assignedVariant);

        setIsLoading(false);
      } catch (err) {
        console.error('Experiment assignment failed:', err);
        setError('Assignment failed');
        setVariant('control'); // Fallback to control
        setIsLoading(false);
      }
    };

    assignVariant();
  }, [experimentName]);

  // Track function
  const track = (eventType: string, properties?: Record<string, any>) => {
    api.post('/ab/track', {
      experiment: experimentName,
      variant,
      event_type: eventType,
      properties,
      timestamp: new Date().toISOString(),
      user_id: getUserId()
    }).catch(err => {
      console.error('Event tracking failed:', err);
    });
  };

  return {
    variant,
    isLoading,
    error,
    track,
    isControl: variant === 'control'
  };
};

// Helper: Get user ID from auth
const getUserId = (): string => {
  // Implement based on your auth system
  return localStorage.getItem('user_id') || 'anonymous';
};
```

### 2. Experiment Wrapper Component

```typescript
// frontend/src/components/experiments/ExperimentWrapper.tsx
import React from 'react';
import { useExperiment } from '../../hooks/useExperiment';

interface ExperimentWrapperProps {
  name: string;
  children: React.ReactNode;
  loadingComponent?: React.ReactNode;
  renderAs?: 'div' | 'section' | 'span';
  className?: string;
}

interface VariantProps {
  name: string;
  children: React.ReactNode;
}

export const ExperimentWrapper: React.FC<ExperimentWrapperProps> = ({
  name,
  children,
  loadingComponent,
  renderAs = 'div',
  className = ''
}) => {
  const { variant, isLoading } = useExperiment(name);

  if (isLoading) {
    return <>{loadingComponent || null}</>;
  }

  const Tag = renderAs;

  // Find the matching variant to render
  const variantElements = React.Children.toArray(children);
  const matchingVariant = variantElements.find((child: any) => {
    return child?.props?.name === variant;
  });

  return (
    <Tag className={`ab-experiment-${name} ab-variant-${variant} ${className}`}>
      {matchingVariant || children}
    </Tag>
  );
};

export const Variant: React.FC<VariantProps> = ({ name, children }) => {
  // This component is just a marker – ExperimentWrapper handles the logic
  return <>{children}</>;
};

// Usage example:
// <ExperimentWrapper name="cta_button_color">
//   <Variant name="control">
//     <button className="bg-blue-600">Sign Up</button>
//   </Variant>
//   <Variant name="variant_a">
//     <button className="bg-green-600">Sign Up</button>
//   </Variant>
//   <Variant name="variant_b">
//     <button className="bg-purple-600">Sign Up Now</button>
//   </Variant>
// </ExperimentWrapper>
```

### 3. Feature Flag Hook

```typescript
// frontend/src/hooks/useFeatureFlag.ts
import { useState, useEffect } from 'react';
import api from '../services/api';

export const useFeatureFlag = (flagName: string): boolean => {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkFlag = async () => {
      try {
        const response = await api.get(`/feature-flags/${flagName}`);
        setIsEnabled(response.data.enabled);
      } catch (err) {
        console.error('Feature flag check failed:', err);
        setIsEnabled(false); // Default to disabled
      } finally {
        setIsLoading(false);
      }
    };

    checkFlag();
  }, [flagName]);

  return isEnabled;
};

// Usage:
// const showNewDashboard = useFeatureFlag('new_dashboard');
// {showNewDashboard ? <NewDashboard /> : <OldDashboard />}
```

### 4. Experiment Context Provider

```typescript
// frontend/src/contexts/ExperimentContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';

interface ExperimentContextType {
  getVariant: (experimentName: string) => string;
  trackEvent: (experimentName: string, eventType: string, properties?: any) => void;
  isLoading: boolean;
}

const ExperimentContext = createContext<ExperimentContextType | undefined>(undefined);

export const ExperimentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [assignments, setAssignments] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);

  // Get variant (with caching)
  const getVariant = (experimentName: string): string => {
    if (assignments[experimentName]) {
      return assignments[experimentName];
    }
    return 'control'; // Default
  };

  // Track event
  const trackEvent = (experimentName: string, eventType: string, properties?: any) => {
    const variant = getVariant(experimentName);

    api.post('/ab/track', {
      experiment: experimentName,
      variant,
      event_type: eventType,
      properties,
      timestamp: new Date().toISOString()
    }).catch(err => console.error('Tracking failed:', err));
  };

  return (
    <ExperimentContext.Provider value={{ getVariant, trackEvent, isLoading }}>
      {children}
    </ExperimentContext.Provider>
  );
};

export const useExperimentContext = () => {
  const context = useContext(ExperimentContext);
  if (!context) {
    throw new Error('useExperimentContext must be used within ExperimentProvider');
  }
  return context;
};
```

---

## Backend Integration

### 1. Database Models

```python
# app/db/models/ab_testing.py
from sqlalchemy import Column, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
import uuid
from datetime import datetime

class ABExperiment(Base):
    __tablename__ = "ab_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    status = Column(String(50), default="draft")  # draft, running, paused, completed
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = Column(JSON)  # Store variants, traffic_split, etc.

class ABVariant(Base):
    __tablename__ = "ab_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("ab_experiments.id"), nullable=False)
    name = Column(String(100), nullable=False)  # control, variant_a, variant_b, etc.
    traffic_split = Column(Float, default=0.0)  # 0.0 to 1.0
    is_control = Column(Boolean, default=False)

class ABEvent(Base):
    __tablename__ = "ab_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("ab_experiments.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("ab_variants.id"), nullable=False)
    event_type = Column(String(100), nullable=False, index=True)  # view, click, conversion, etc.
    properties = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class ABConversion(Base):
    __tablename__ = "ab_conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("ab_experiments.id"))
    variant_id = Column(UUID(as_uuid=True), ForeignKey("ab_variants.id"))
    conversion_type = Column(String(100), nullable=False)  # primary, secondary
    timestamp = Column(DateTime, default=datetime.utcnow)
```

### 2. Assignment API Endpoint

```python
# app/api/v1/endpoints/ab_testing.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.ab_testing import ABExperiment, ABVariant
from app.core.security import get_current_user
from app.db.models.user import User
import hashlib
import redis
from datetime import datetime

router = APIRouter()
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@router.post("/assign")
async def assign_variant(
    experiment: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign user to a variant for the given experiment.
    Uses deterministic hashing for consistent assignment.
    """
    # Get experiment
    exp = db.query(ABExperiment).filter(ABExperiment.name == experiment).first()
    if not exp:
        raise HTTPException(status_id=404, detail="Experiment not found")

    # Check if experiment is running
    if exp.status != "running":
        return {"variant": "control", "status": exp.status}

    # Check if experiment is within date range
    now = datetime.utcnow()
    if exp.start_date and now < exp.start_date:
        return {"variant": "control", "status": "not_started"}
    if exp.end_date and now > exp.end_date:
        return {"variant": "control", "status": "ended"}

    # Check cache first
    cache_key = f"ab_assignment:{experiment}:{current_user.id}"
    cached = redis_client.get(cache_key)
    if cached:
        return {"variant": cached, "cached": True}

    # Get variants
    variants = db.query(ABVariant).filter(ABVariant.experiment_id == exp.id).all()

    # Deterministic assignment based on user_id + experiment_name
    hash_input = f"{current_user.id}:{experiment}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()

    # Convert to 0-1 range
    bucket = int(hash_value[:8], 16) / 0xffffffff

    # Assign based on traffic split
    cumulative = 0.0
    assigned_variant = "control"

    for variant in variants:
        cumulative += variant.traffic_split
        if bucket < cumulative:
            assigned_variant = variant.name
            break

    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, assigned_variant)

    # Track assignment event
    track_event(
        user_id=current_user.id,
        experiment_id=exp.id,
        variant_name=assigned_variant,
        event_type="assigned",
        db=db
    )

    return {"variant": assigned_variant, "status": "assigned"}

def track_event(user_id: str, experiment_id: str, variant_name: str,
                event_type: str, properties: dict = None, db: Session = None):
    """Track an A/B testing event"""
    event = ABEvent(
        user_id=user_id,
        experiment_id=experiment_id,
        variant_id=get_variant_id(experiment_id, variant_name, db),
        event_type=event_type,
        properties=properties or {}
    )
    db.add(event)
    db.commit()

    # Also increment in Redis for real-time counting
    redis_key = f"ab_events:{experiment_id}:{variant_name}:{event_type}"
    redis_client.incr(redis_key)
```

### 3. Tracking API Endpoint

```python
@router.post("/track")
async def track_event_endpoint(
    event_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track an event for an A/B test variant.
    """
    experiment_name = event_data.get("experiment")
    variant = event_data.get("variant")
    event_type = event_data.get("event_type")
    properties = event_data.get("properties", {})

    # Get experiment
    exp = db.query(ABExperiment).filter(ABExperiment.name == experiment_name).first()
    if not exp:
        raise HTTPException(status_id=404, detail="Experiment not found")

    # Get variant
    var = db.query(ABVariant).filter(
        ABVariant.experiment_id == exp.id,
        ABVariant.name == variant
    ).first()

    if not var:
        raise HTTPException(status_id=404, detail="Variant not found")

    # Create event
    event = ABEvent(
        user_id=current_user.id,
        experiment_id=exp.id,
        variant_id=var.id,
        event_type=event_type,
        properties=properties
    )

    db.add(event)
    db.commit()

    # If this is a conversion event, also record in conversions table
    if event_type in ["signup", "purchase", "activation", "upgrade"]:
        conversion = ABConversion(
            user_id=current_user.id,
            experiment_id=exp.id,
            variant_id=var.id,
            conversion_type="primary"
        )
        db.add(conversion)
        db.commit()

    return {"status": "tracked"}
```

### 4. Results API Endpoint

```python
@router.get("/results/{experiment_name}")
async def get_experiment_results(
    experiment_name: str,
    db: Session = Depends(get_db)
):
    """
    Get results for an experiment including conversion rates and statistical significance.
    """
    # Get experiment
    exp = db.query(ABExperiment).filter(ABExperiment.name == experiment_name).first()
    if not exp:
        raise HTTPException(status_id=404, detail="Experiment not found")

    # Get variants
    variants = db.query(ABVariant).filter(ABVariant.experiment_id == exp.id).all()

    results = []

    for variant in variants:
        # Count assignments (unique users)
        assignments = db.query(ABEvent).filter(
            ABEvent.experiment_id == exp.id,
            ABEvent.variant_id == variant.id,
            ABEvent.event_type == "assigned"
        ).distinct(ABEvent.user_id).count()

        # Count conversions
        conversions = db.query(ABEvent).filter(
            ABEvent.experiment_id == exp.id,
            ABEvent.variant_id == variant.id,
            ABEvent.event_type == "conversion"
        ).distinct(ABEvent.user_id).count()

        conversion_rate = (conversions / assignments * 100) if assignments > 0 else 0

        results.append({
            "variant": variant.name,
            "assignments": assignments,
            "conversions": conversions,
            "conversion_rate": round(conversion_rate, 2),
            "is_control": variant.is_control
        })

    # Calculate lift and statistical significance
    if len(results) > 1:
        control = next((r for r in results if r["is_control"]), None)
        if control:
            for result in results:
                if not result["is_control"]:
                    # Calculate lift
                    lift = ((result["conversion_rate"] - control["conversion_rate"]) /
                           control["conversion_rate"] * 100)
                    result["lift_vs_control"] = round(lift, 2)

                    # Calculate statistical significance (z-test)
                    p_value = calculate_significance(
                        control["conversions"], control["assignments"],
                        result["conversions"], result["assignments"]
                    )
                    result["p_value"] = round(p_value, 4)
                    result["significant"] = p_value < 0.05

    return {
        "experiment": experiment_name,
        "status": exp.status,
        "results": results
    }

def calculate_significance(c1: int, n1: int, c2: int, n2: int) -> float:
    """
    Calculate p-value using two-proportion z-test.
    c1, c2 = conversions
    n1, n2 = total samples
    """
    from math import sqrt

    p1 = c1 / n1
    p2 = c2 / n2
    pooled_p = (c1 + c2) / (n1 + n2)

    se = sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
    z = (p2 - p1) / se if se > 0 else 0

    # Approximate p-value from z-score (two-tailed)
    import mpmath
    p_value = 2 * (1 - mpmath.ncdf(abs(z)))

    return float(p_value)
```

---

## Ready-to-Use UI Experiments

### Experiment 1: CTA Button Color

**Hypothesis:** Green CTA buttons will increase click-through rate by 5% compared to blue.

```typescript
// frontend/src/components/experiments/CTAButtonExperiment.tsx
import { ExperimentWrapper, Variant } from './ExperimentWrapper';

export const CTAButton: React.FC<{ onClick: () => void }> = ({ onClick }) => {
  return (
    <ExperimentWrapper name="cta_button_color_v1">
      <Variant name="control">
        <button
          onClick={onClick}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg"
        >
          Get Started Free
        </button>
      </Variant>

      <Variant name="variant_a">
        <button
          onClick={onClick}
          className="bg-green-600 hover:bg-green-700 text-white font-semibold px-6 py-3 rounded-lg"
        >
          Get Started Free
        </button>
      </Variant>

      <Variant name="variant_b">
        <button
          onClick={onClick}
          className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-3 rounded-lg"
        >
          Get Started Free
        </button>
      </Variant>
    </ExperimentWrapper>
  );
};
```

**Setup in backend:**
```python
# Create experiment
experiment = ABExperiment(
    name="cta_button_color_v1",
    description="Test CTA button colors",
    status="running",
    start_date=datetime(2025, 1, 15),
    end_date=datetime(2025, 2, 15),
    config={
        "variants": ["control", "variant_a", "variant_b"],
        "traffic_split": {"control": 0.5, "variant_a": 0.25, "variant_b": 0.25}
    }
)
```

---

### Experiment 2: Pricing Page Layout

**Hypothesis:** Annual pricing highlighted first will increase annual conversion rate by 8%.

```typescript
// frontend/src/components/experiments/PricingLayoutExperiment.tsx
import { ExperimentWrapper, Variant } from './ExperimentWrapper';
import { useExperiment } from '../../hooks/useExperiment';

export const PricingTable: React.FC = () => {
  const { track } = useExperiment('pricing_layout_v1');

  const handleSelectPlan = (plan: string, billing: string) => {
    track('plan_selected', { plan, billing });
    // Navigate to checkout...
  };

  return (
    <ExperimentWrapper name="pricing_layout_v1">
      <Variant name="control">
        {/* Monthly first (current) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <PricingCard plan="Free" billing="monthly" onSelect={handleSelectPlan} />
          <PricingCard plan="Premium" billing="monthly" onSelect={handleSelectPlan} highlighted />
          <PricingCard plan="Enterprise" billing="monthly" onSelect={handleSelectPlan} />
        </div>
        <p className="text-center mt-4 text-sm text-gray-600">
          Save 20% with annual billing <a href="#" className="text-blue-600">Switch to Annual →</a>
        </p>
      </Variant>

      <Variant name="variant_a">
        {/* Annual first */}
        <div className="mb-4 text-center">
          <span className="inline-block bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-semibold">
            💰 Most Popular: Annual Plans (Save 20%)
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <PricingCard plan="Free" billing="annual" onSelect={handleSelectPlan} />
          <PricingCard plan="Premium" billing="annual" onSelect={handleSelectPlan} highlighted />
          <PricingCard plan="Enterprise" billing="annual" onSelect={handleSelectPlan} />
        </div>
        <p className="text-center mt-4 text-sm text-gray-600">
          Prefer monthly? <a href="#" className="text-blue-600">Switch to Monthly →</a>
        </p>
      </Variant>

      <Variant name="variant_b">
        {/* Toggle switch */}
        <div className="flex justify-center mb-6">
          <BillingToggle
            options={["Monthly", "Annual"]}
            default="Annual"
            onChange={(value) => track('billing_toggle_change', { value })}
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <PricingCard plan="Free" onSelect={handleSelectPlan} />
          <PricingCard plan="Premium" onSelect={handleSelectPlan} highlighted />
          <PricingCard plan="Enterprise" onSelect={handleSelectPlan} />
        </div>
      </Variant>
    </ExperimentWrapper>
  );
};
```

---

### Experiment 3: Signup Form Length

**Hypothesis:** Reducing signup fields from 5 to 2 will increase completion rate by 12%.

```typescript
// frontend/src/components/experiments/SignupFormExperiment.tsx
import { ExperimentWrapper, Variant } from './ExperimentWrapper';
import { useExperiment } from '../../hooks/useExperiment';

export const SignupForm: React.FC = () => {
  const { track } = useExperiment('signup_length_v1');

  return (
    <ExperimentWrapper name="signup_length_v1">
      <Variant name="control">
        {/* Full form */}
        <form onSubmit={(e) => { e.preventDefault(); track('signup_attempt', { fields: 5 }); }}>
          <input name="name" placeholder="Full name" required />
          <input name="email" type="email" placeholder="Email" required />
          <input name="password" type="password" placeholder="Password" required />
          <input name="company" placeholder="Company name" />
          <select name="role" required>
            <option value="">Select your role</option>
            <option value="hr">HR Professional</option>
            <option value="manager">Manager</option>
            <option value="individual">Individual</option>
          </select>
          <button type="submit">Create Account</button>
        </form>
      </Variant>

      <Variant name="variant_a">
        {/* Minimal form */}
        <form onSubmit={(e) => { e.preventDefault(); track('signup_attempt', { fields: 2 }); }}>
          <input name="email" type="email" placeholder="Work email" required />
          <input name="password" type="password" placeholder="Create password (8+ characters)" required />
          <button type="submit">Continue</button>
          <p className="text-sm text-gray-600 mt-2">
            We'll ask for your name and company later
          </p>
        </form>
      </Variant>

      <Variant name="variant_b">
        {/* Social auth only */}
        <div className="space-y-3">
          <button
            onClick={() => track('signup_attempt', { method: 'google' })}
            className="w-full flex items-center justify-center gap-2 border border-gray-300 rounded-lg px-4 py-3"
          >
            <img src="/google-logo.svg" alt="Google" className="w-5 h-5" />
            Continue with Google
          </button>
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">or</span>
            </div>
          </div>
          <button
            onClick={() => track('signup_attempt', { method: 'email' })}
            className="w-full bg-blue-600 text-white rounded-lg px-4 py-3 font-semibold"
          >
            Continue with Email
          </button>
        </div>
      </Variant>
    </ExperimentWrapper>
  );
};
```

---

### Experiment 4: Results Page Layout

**Hypothesis:** Interactive visualizations will increase time-on-page by 30%.

```typescript
// frontend/src/components/experiments/ResultsLayoutExperiment.tsx
import { ExperimentWrapper, Variant } from './ExperimentWrapper';

export const AssessmentResults: React.FC<{ results: any }> = ({ results }) => {
  return (
    <ExperimentWrapper name="results_layout_v1">
      <Variant name="control">
        {/* Static results */}
        <div className="max-w-2xl mx-auto">
          <h1>Your Big Five Results</h1>
          <ResultsTable data={results} />
          <DownloadButton />
        </div>
      </Variant>

      <Variant name="variant_a">
        {/* Interactive dashboard */}
        <div className="max-w-6xl mx-auto">
          <h1>Your Personality Profile</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <RadarChart data={results} interactive />
            <TraitBreakdown data={results} expandable />
          </div>
          <ActionableInsights data={results} />
          <ShareButton />
          <DownloadButton />
        </div>
      </Variant>

      <Variant name="variant_b">
        {/* Guided tour */}
        <div className="max-w-4xl mx-auto">
          <ResultsTour data={results} stepByStep />
          <div className="mt-8 p-4 bg-blue-50 rounded-lg">
            <h3>What's Next?</h3>
            <RecommendedAssessments basedOn={results} />
            <TeamInvitePrompt />
          </div>
        </div>
      </Variant>
    </ExperimentWrapper>
  );
};
```

---

## Analytics & Reporting

### Frontend Analytics Helper

```typescript
// frontend/src/services/experimentAnalytics.ts
import api from './api';

export class ExperimentAnalytics {
  /**
   * Track a conversion event
   */
  static trackConversion(experimentName: string, value?: number) {
    return api.post('/ab/track', {
      experiment: experimentName,
      event_type: 'conversion',
      properties: { value }
    });
  }

  /**
   * Track a click event
   */
  static trackClick(experimentName: string, element: string) {
    return api.post('/ab/track', {
      experiment: experimentName,
      event_type: 'click',
      properties: { element }
    });
  }

  /**
   * Track a view event
   */
  static trackView(experimentName: string) {
    return api.post('/ab/track', {
      experiment: experimentName,
      event_type: 'view'
    });
  }

  /**
   * Track custom event
   */
  static trackCustom(experimentName: string, eventType: string, properties: any = {}) {
    return api.post('/ab/track', {
      experiment: experimentName,
      event_type: eventType,
      properties
    });
  }
}

// Usage in components:
// ExperimentAnalytics.trackClick('cta_button_color_v1', 'signup_button');
// ExperimentAnalytics.trackConversion('pricing_layout_v1', 2900); // $29.00
```

### Results Dashboard Component

```typescript
// frontend/src/components/analytics/ExperimentResultsDashboard.tsx
import React, { useState, useEffect } from 'react';
import api from '../../services/api';

interface ExperimentResult {
  variant: string;
  assignments: number;
  conversions: number;
  conversion_rate: number;
  lift_vs_control?: number;
  p_value?: number;
  significant?: boolean;
  is_control?: boolean;
}

export const ExperimentResultsDashboard: React.FC = () => {
  const [experiments, setExperiments] = useState<string[]>([]);
  const [selectedExperiment, setSelectedExperiment] = useState<string>('');
  const [results, setResults] = useState<ExperimentResult[]>([]);

  useEffect(() => {
    // Load list of experiments
    api.get('/ab/experiments').then(res => {
      setExperiments(res.data);
      if (res.data.length > 0) {
        setSelectedExperiment(res.data[0]);
      }
    });
  }, []);

  useEffect(() => {
    if (selectedExperiment) {
      // Load results for selected experiment
      api.get(`/ab/results/${selectedExperiment}`).then(res => {
        setResults(res.data.results);
      });
    }
  }, [selectedExperiment]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">A/B Test Results</h1>

      {/* Experiment selector */}
      <select
        value={selectedExperiment}
        onChange={(e) => setSelectedExperiment(e.target.value)}
        className="mb-6 block w-full max-w-md border border-gray-300 rounded-lg p-2"
      >
        {experiments.map(exp => (
          <option key={exp} value={exp}>{exp}</option>
        ))}
      </select>

      {/* Results table */}
      <table className="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Variant</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Users</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Conversions</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Conv. Rate</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lift vs Control</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">P-Value</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Significant</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {results.map(r => (
            <tr key={r.variant} className={r.is_control ? 'bg-gray-50' : ''}>
              <td className="px-6 py-4 whitespace-nowrap font-medium">
                {r.variant} {r.is_control && '(Control)'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">{r.assignments.toLocaleString()}</td>
              <td className="px-6 py-4 whitespace-nowrap">{r.conversions.toLocaleString()}</td>
              <td className="px-6 py-4 whitespace-nowrap">{r.conversion_rate}%</td>
              <td className="px-6 py-4 whitespace-nowrap">
                {r.lift_vs_control !== undefined && (
                  <span className={r.lift_vs_control > 0 ? 'text-green-600' : 'text-red-600'}>
                    {r.lift_vs_control > 0 ? '+' : ''}{r.lift_vs_control}%
                  </span>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">{r.p_value}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                {r.significant !== undefined && (
                  r.significant ? '✅ Yes' : '❌ No'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Winner declaration */}
      {results.some(r => r.significant && !r.is_control && r.lift_vs_control && r.lift_vs_control > 0) && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="font-semibold text-green-800">🎉 Winner Found!</h3>
          <p className="text-green-700">
            {results.find(r => r.significant && !r.is_control)?.variant} is statistically
            significantly better than control.
          </p>
        </div>
      )}
    </div>
  );
};
```

---

## Best Practices

### 1. Sample Size Planning

```typescript
// utils/sampleSizeCalculator.ts
export const calculateSampleSize = (
  baselineRate: number,      // e.g., 0.42 (42%)
  minimumDetectibleEffect: number, // e.g., 0.03 (3% absolute lift)
  alpha: number = 0.05,      // Significance level
  power: number = 0.8        // Statistical power
): number => {
  const zAlpha = 1.96;  // For alpha = 0.05
  const zBeta = 0.84;   // For power = 0.8

  const p1 = baselineRate;
  const p2 = baselineRate + minimumDetectibleEffect;
  const pooledP = (p1 + p2) / 2;

  const sampleSizePerVariant =
    (2 * pooledP * (1 - pooledP) * Math.pow(zAlpha + zBeta, 2)) /
    Math.pow(p2 - p1, 2);

  return Math.ceil(sampleSizePerVariant);
};

// Example:
// To detect a 3% lift from 42% baseline:
// calculateSampleSize(0.42, 0.03) = ~4,300 per variant
```

### 2. Avoiding Common Pitfalls

**❌ Don't:**
```typescript
// Changing experiment mid-flight
const variant = Math.random() > 0.5 ? 'A' : 'B'; // Not deterministic!

// Not tracking control properly
if (variant === 'A') { track('click'); } // Control never tracked!
```

**✅ Do:**
```typescript
// Use deterministic assignment
const variant = getVariant(experimentName, userId); // Consistent!

// Track all variants the same way
track('click', { variant }); // All variants tracked!
```

### 3. Early Stopping Rules

```typescript
// Check for significant negative impact (guardrail)
if (variant.conversion_rate < control.conversion_rate * 0.9) {
  // Variant is performing 10% worse than control
  if (p_value < 0.05 && sampleSize > minSampleSize * 0.5) {
    // Stop experiment early to prevent damage
    stopExperiment(experimentId);
  }
}
```

### 4. Segmentation Analysis

```typescript
// Analyze results by segment
const segmentResults = {
  mobile: { control: 0.38, variant: 0.45 },
  desktop: { control: 0.45, variant: 0.46 }
};

// Variant wins on mobile but not desktop
// Consider device-specific rollout
```

---

## Summary

This A/B testing UI script provides:

✅ **Complete React Implementation** – Custom hooks, wrapper components, context provider
✅ **Backend API Endpoints** – Assignment, tracking, results with statistical significance
✅ **4 Ready-to-Use Experiments** – CTA button, pricing layout, signup form, results page
✅ **Analytics Dashboard** – Real-time results with significance testing
✅ **Best Practices** – Sample size calculators, pitfalls to avoid, early stopping rules

**Quick Start:**
1. Copy `useExperiment` hook to your project
2. Set up backend endpoints (assignment, track, results)
3. Wrap your component in `ExperimentWrapper`
4. Track events with `ExperimentAnalytics`
5. Monitor results in dashboard

**Expected Impact:**
- 5-15% conversion improvements from successful tests
- Data-driven UI decisions
- Reduced risk from major changes

---

**Document Version:** 1.0
**Last Updated:** January 2025
**Next Review:** April 2025
**Maintained By:** Product & Engineering Team
