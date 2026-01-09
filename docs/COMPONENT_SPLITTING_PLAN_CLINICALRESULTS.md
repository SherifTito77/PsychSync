# ClinicalResults Component Splitting Plan

## Overview

**Current File:** `frontend/src/pages/ClinicalResults.tsx`
**Current Size:** 1,928 lines
**Target Size:** < 200 lines per component
**Estimated Effort:** 16 hours

---

## Current Structure Analysis

The `ClinicalResults` component handles:
1. **Data fetching** - Assessment results from API or location state
2. **Severity calculation** - Color, label, description based on score
3. **Crisis detection** - Check if crisis resources needed
4. **Recommendations** - Generate based on severity
5. **Resources** - Find appropriate resources
6. **Display** - Show results with charts and cards
7. **Actions** - Save, print, share, schedule next assessment
8. **Navigation** - Back button, assessment history

---

## Proposed Split Structure

```
frontend/src/pages/clinical-results/
├── index.tsx                    # Main orchestrator (< 100 lines)
├── types.ts                     # Shared types/interfaces
├── hooks/
│   ├── useClinicalResults.ts   # Data fetching hook
│   └── useClinicalActions.ts   # Save/print/share actions
├── components/
│   ├── ResultsHeader.tsx       # Title, actions, metadata
│   ├── SeverityBanner.tsx       # Crisis alert, severity level
│   ├── ScoreDisplay.tsx         # Main score, visual indicator
│   ├── RecommendationsList.tsx  # Recommendation cards
│   ├── ResourcesGrid.tsx       # Crisis resources, help links
│   ├── ActionsBar.tsx          # Save, print, share buttons
│   ├── MetadataDisplay.tsx     # Assessment date, provider, notes
│   └── Charts/                  # Visualizations (if any)
│       ├── ScoreChart.tsx
│       └── SeverityChart.tsx
└── utils/
    ├── severityCalculator.ts    # Calculate severity from score
    ├── recommendations.ts       # Generate recommendations
    └── resources.ts             # Find appropriate resources
```

---

## Detailed Component Breakdown

### 1. Main Orchestrator (index.tsx)

**Responsibility:** Coordinate sub-components, manage navigation

**Size:** < 100 lines

```typescript
import { useParams } from 'react-router-dom';
import { useClinicalResults } from './hooks/useClinicalResults';
import { ResultsHeader } from './components/ResultsHeader';
import { SeverityBanner } from './components/SeverityBanner';
import { ScoreDisplay } from './components/ScoreDisplay';
import { RecommendationsList } from './components/RecommendationsList';
import { ResourcesGrid } from './components/ResourcesGrid';
import { ActionsBar } from './components/ActionsBar';
import { MetadataDisplay } from './components/MetadataDisplay';

const ClinicalResults = () => {
  const { tool } = useParams<{ tool: string }>();
  const {
    result,
    metadata,
    loading,
    error,
    actions: { handleSave, handlePrint, handleShare }
  } = useClinicalResults(tool);

  if (loading) return <ResultsLoading />;
  if (error) return <ResultsError error={error} />;
  if (!result) return <NoResults />;

  return (
    <div className="clinical-results space-y-6">
      {/* Crisis alert at top */}
      {result.crisisAlert && (
        <SeverityBanner result={result} />
      )}

      {/* Header with title and actions */}
      <ResultsHeader
        tool={tool}
        onSave={handleSave}
        onPrint={handlePrint}
        onShare={handleShare}
      />

      {/* Main score display */}
      <ScoreDisplay result={result} />

      {/* Assessment metadata */}
      <MetadataDisplay metadata={metadata} />

      {/* Recommendations */}
      {result.recommendations.length > 0 && (
        <RecommendationsList recommendations={result.recommendations} />
      )}

      {/* Resources (especially if crisis) */}
      <ResourcesGrid resources={result.resources} />

      {/* Action buttons */}
      <ActionsBar
        onSave={handleSave}
        onPrint={handlePrint}
        onShare={handleShare}
        result={result}
      />
    </div>
  );
};

export default ClinicalResults;
```

---

### 2. Custom Hooks (hooks/)

#### useClinicalResults.ts

**Responsibility:** Data fetching, state management

**Size:** ~150 lines

```typescript
import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useClinicalActions } from './useClinicalActions';

interface AssessmentResult {
  score: number;
  severity_level: string;
  severity?: {
    label: string;
    color: string;
    description: string;
  };
  crisisAlert: boolean;
  recommendations: string[];
  resources: {
    title: string;
    description: string;
    link?: string;
    phone?: string;
  }[];
}

interface AssessmentMetadata {
  assessmentId: string;
  completedAt: string;
  notes: string;
  responseData: any;
  providerNotified: boolean;
  nextAssessmentDate: string;
}

export const useClinicalResults = (tool: string) => {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [metadata, setMetadata] = useState<AssessmentMetadata | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Reuse action hooks
  const actions = useClinicalActions(result, metadata);

  useEffect(() => {
    loadResults();
  }, [tool, location.state, window.location.hash]);

  const loadResults = async () => {
    try {
      setLoading(true);

      // Get from location state, hash, or API
      if (location.state?.result) {
        setResultFromState(location.state);
      } else if (window.location.hash) {
        await fetchByHash(window.location.hash.substring(1));
      } else {
        await fetchFromAPI();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  // Helper functions...
  const setResultFromState = (state: any) => {
    // Set result and metadata from state
  };

  const fetchByHash = async (hash: string) => {
    // Fetch by assessment ID
  };

  const fetchFromAPI = async () => {
    // Fetch latest results
  };

  return {
    result,
    metadata,
    loading,
    error,
    actions,
  };
};
```

---

### 3. Sub-Components (components/)

#### ResultsHeader.tsx (~50 lines)
```typescript
interface ResultsHeaderProps {
  tool: string;
  onSave: () => void;
  onPrint: () => void;
  onShare: () => void;
}

export const ResultsHeader: React.FC<ResultsHeaderProps> = ({
  tool,
  onSave,
  onPrint,
  onShare,
}) => {
  return (
    <div className="flex justify-between items-start">
      <div>
        <h1 className="text-2xl font-bold">{formatToolName(tool)} Results</h1>
        <p className="text-sm text-gray-600">
          Your assessment results are ready
        </p>
      </div>
      <div className="flex gap-2">
        <Button onClick={onSave}>Save</Button>
        <Button onClick={onPrint}>Print</Button>
        <Button onClick={onShare}>Share</Button>
      </div>
    </div>
  );
};
```

#### SeverityBanner.tsx (~40 lines)
```typescript
interface SeverityBannerProps {
  result: AssessmentResult;
}

export const SeverityBanner: React.FC<SeverityBannerProps> = ({ result }) => {
  if (!result.crisisAlert) return null;

  return (
    <Alert variant="error" className="mb-6">
      <AlertTitle>Crisis Resources Available</AlertTitle>
      <p>
        Your assessment results indicate you may benefit from immediate
        support. Please consider the resources below.
      </p>
    </Alert>
  );
};
```

#### ScoreDisplay.tsx (~60 lines)
```typescript
interface ScoreDisplayProps {
  result: AssessmentResult;
}

export const ScoreDisplay: React.FC<ScoreDisplayProps> = ({ result }) => {
  const { score, severity } = result;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-6">
          <div className="text-5xl font-bold">{score}</div>
          <div
            className="px-4 py-2 rounded text-white"
            style={{ backgroundColor: severity?.color || 'gray' }}
          >
            {severity?.label || 'Unknown'}
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-2">
          {severity?.description || ''}
        </p>
      </CardContent>
    </Card>
  );
};
```

#### RecommendationsList.tsx (~50 lines)
```typescript
interface RecommendationsListProps {
  recommendations: string[];
}

export const RecommendationsList: React.FC<RecommendationsListProps> = ({
  recommendations,
}) => {
  if (recommendations.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recommendations</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="list-disc pl-5 space-y-2">
          {recommendations.map((rec, index) => (
            <li key={index}>{rec}</li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
};
```

#### ResourcesGrid.tsx (~80 lines)
```typescript
interface ResourcesGridProps {
  resources: Array<{
    title: string;
    description: string;
    link?: string;
    phone?: string;
  }>;
}

export const ResourcesGrid: React.FC<ResourcesGridProps> = ({ resources }) => {
  if (resources.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Helpful Resources</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {resources.map((resource, index) => (
            <div key={index} className="border rounded p-4">
              <h3 className="font-semibold">{resource.title}</h3>
              <p className="text-sm text-gray-600">{resource.description}</p>
              {resource.link && (
                <a
                  href={resource.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  Learn More →
                </a>
              )}
              {resource.phone && (
                <p className="text-sm font-mono">{resource.phone}</p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
```

---

### 4. Utility Functions (utils/)

#### severityCalculator.ts (~80 lines)
```typescript
export interface SeverityInfo {
  label: string;
  color: string;
  description: string;
  level: 'low' | 'moderate' | 'high' | 'severe';
}

export function calculateSeverity(
  score: number,
  tool: string
): SeverityInfo {
  // Calculate severity based on score and tool type
  // Return color, label, description
}

export function getSeverityColor(level: string): string {
  const colors = {
    low: 'green',
    moderate: 'yellow',
    high: 'orange',
    severe: 'red',
  };
  return colors[level as keyof typeof colors] || 'gray';
}
```

#### recommendations.ts (~100 lines)
```typescript
export function generateRecommendations(
  tool: string,
  severityLevel: string,
  score?: number
): string[] {
  // Generate appropriate recommendations based on
  // - Assessment type
  // - Severity level
  // - Score

  const recommendations: string[] = [];

  if (severityLevel === 'severe') {
    recommendations.push(
      'Consider speaking with a mental health professional',
      'Reach out to your support network',
      'Take time off if needed'
    );
  }

  // Tool-specific recommendations...
  if (tool === 'phq9') {
    recommendations.push('Monitor your mood daily');
  }

  return recommendations;
}
```

#### resources.ts (~120 lines)
```typescript
export interface Resource {
  title: string;
  description: string;
  link?: string;
  phone?: string;
}

export function getResources(
  tool: string,
  severityLevel: string,
  crisisAlert: boolean
): Resource[] {
  const resources: Resource[] = [];

  // Crisis resources
  if (crisisAlert) {
    resources.push({
      title: 'National Crisis Hotline',
      description: '24/7 confidential support',
      phone: '988',
      link: 'https://suicidepreventionlifeline.org',
    });
  }

  // Tool-specific resources...
  if (tool === 'phq9') {
    resources.push({
      title: 'National Alliance on Mental Illness',
      description: 'Support, education, and advocacy',
      link: 'https://www.nami.org',
    });
  }

  return resources;
}
```

---

## Implementation Steps

### Step 1: Create Directory Structure (5 minutes)
```bash
mkdir -p frontend/src/pages/clinical-results/{hooks,components,utils}
```

### Step 2: Extract Types (10 minutes)
Create `types.ts` with all interfaces

### Step 3: Extract Utility Functions (30 minutes)
Create:
- `utils/severityCalculator.ts`
- `utils/recommendations.ts`
- `utils/resources.ts`

### Step 4: Create Custom Hooks (40 minutes)
Create:
- `hooks/useClinicalResults.ts`
- `hooks/useClinicalActions.ts`

### Step 5: Create Sub-Components (1 hour)
Create:
- `components/ResultsHeader.tsx`
- `components/SeverityBanner.tsx`
- `components/ScoreDisplay.tsx`
- `components/RecommendationsList.tsx`
- `components/ResourcesGrid.tsx`
- `components/ActionsBar.tsx`
- `components/MetadataDisplay.tsx`

### Step 6: Create Main Orchestrator (20 minutes)
Create `index.tsx` that combines all sub-components

### Step 7: Test Thoroughly (30 minutes)
- Test all paths
- Test loading states
- Test error states
- Test all actions
- Test with different assessment types

### Step 8: Update Imports (10 minutes)
Update any files importing from old location

---

## Benefits of Splitting

| Before | After |
|--------|-------|
| **1,928 lines** | **< 200 lines per file** |
| **Impossible to maintain** | **Easy to understand** |
| **Hard to test** | **Easy to test individually** |
| **Slow renders** | **Fast renders (memoization)** |
| **Changes affect everything** | **Changes isolated to specific components** |
| **No code reuse** | **Reusable components** |

---

## Testing Strategy

### 1. Unit Tests
```typescript
// Test severity calculation
describe('calculateSeverity', () => {
  it('returns severe for scores > 80', () => {
    const result = calculateSeverity(85, 'phq9');
    expect(result.level).toBe('severe');
  });
});

// Test recommendations
describe('generateRecommendations', () => {
  it('includes crisis resources for severe cases', () => {
    const recs = generateRecommendations('phq9', 'severe');
    expect(recs).toContain('Consider speaking with a mental health professional');
  });
});

// Test components
describe('SeverityBanner', () => {
  it('renders when crisisAlert is true', () => {
    const { getByText } = render(
      <SeverityBanner result={{ crisisAlert: true, ... }} />
    );
    expect(getByText('Crisis Resources Available')).toBeInTheDocument();
  });
});
```

### 2. Integration Tests
```typescript
describe('ClinicalResults', () => {
  it('loads results from location state', () => {
    // Test loading flow
  });

  it('fetches from API when no state', () => {
    // Test API integration
  });

  it('displays crisis alert for severe cases', () => {
    // Test conditional rendering
  });
});
```

---

## Migration Checklist

- [ ] Create directory structure
- [ ] Extract types to `types.ts`
- [ ] Extract utility functions
- [ ] Create custom hooks
- [ ] Create sub-components
- [ ] Create main orchestrator
- [ ] Test all components
- [ ] Test integration
- [ ] Update imports
- [ ] Delete old file (or keep as backup)
- [ ] Update documentation

---

## Success Metrics

After splitting:
- ✅ Main component < 200 lines
- ✅ All sub-components < 150 lines
- ✅ Each component has single responsibility
- ✅ All components individually testable
- ✅ No prop drilling > 3 levels
- ✅ Reusable components created
- ✅ Performance improved (faster renders)

---

**Estimated Time to Complete:** 4 hours
**Impact:** VERY HIGH - Makes component maintainable and testable
**Priority:** P1 - Do this after React Query is working

**Next Component to Split:** WellbeingAssessment.tsx (1,373 lines)
