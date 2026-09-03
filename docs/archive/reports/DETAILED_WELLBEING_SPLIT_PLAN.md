# WellbeingAssessment.tsx - Detailed Splitting Plan

## Current State
**File**: `frontend/src/pages/WellbeingAssessment.tsx`
**Lines**: 1,373
**Priority**: 🟡 HIGH (2nd most critical after ClinicalAssessment)

---

## Component Analysis

### Responsibilities (Current Mix)
1. **Question Data** (lines 25-102): 54 wellbeing questions
2. **Assessment Flow** (lines 107-126): State management for question progression
3. **Data Loading** (lines 128-140): Load history, goals, streak
4. **Scoring Logic** (lines TBD): Calculate category scores
5. **Results Display** (lines TBD): Show scores and recommendations
6. **Goal Setting** (lines TBD): Modal for creating wellness goals
7. **Progress Tracking** (lines TBD): Track action items, streaks
8. **History Comparison** (lines TBD): Compare with previous assessments
9. **Export Functionality** (lines TBD): PDF/JSON export
10. **UI Rendering** (lines TBD): All JSX in one massive return

---

## Proposed Structure

```
pages/wellbeing-assessment/
├── index.tsx (180 lines) - Main orchestrator
├── types.ts (60 lines) - Shared interfaces
├── constants/
│   ├── questions.ts (90 lines) - 54 questions data
│   ├── categories.ts (30 lines) - Category definitions
│   └── scoring.ts (80 lines) - Scoring algorithms
├── hooks/
│   ├── useWellbeingAssessment.ts (150 lines) - Main data hook
│   ├── useAssessmentFlow.ts (100 lines) - Question progression
│   ├── useGoalSetting.ts (80 lines) - Goal management
│   └── useProgressTracking.ts (100 lines) - Streaks, history
├── components/
│   ├── assessment-flow/
│   │   ├── QuestionCard.tsx (60 lines) - Single question
│   │   ├── CategoryProgress.tsx (50 lines) - Progress bar
│   │   └── NavigationControls.tsx (40 lines) - Next/Back buttons
│   ├── results/
│   │   ├── ResultsOverview.tsx (100 lines) - Score summary
│   │   ├── CategoryScores.tsx (80 lines) - Per-category scores
│   │   ├── RecommendationsPanel.tsx (90 lines) - AI recommendations
│   │   └── ResultsChart.tsx (70 lines) - Visual charts
│   ├── goals/
│   │   ├── GoalModal.tsx (120 lines) - Create/edit goals
│   │   ├── GoalList.tsx (80 lines) - Display goals
│   │   └── ActionItems.tsx (90 lines) - Track progress
│   ├── history/
│   │   ├── HistoryComparison.tsx (100 lines) - Compare assessments
│   │   └── StreakDisplay.tsx (60 lines) - Show streak
│   └── export/
│       └── ExportControls.tsx (50 lines) - PDF/JSON export
└── utils/
    ├── validation.ts (40 lines) - Response validation
    ├── calculations.ts (60 lines) - Score calculations
    └── formatting.ts (30 lines) - Display formatting
```

**Total Lines**: ~2,000 lines across 25+ files
**Main Orchestrator**: 180 lines (87% reduction!)

---

## Extraction Plan

### Step 1: Extract Question Data (30 minutes)

**From**: Lines 25-102
**To**: `constants/questions.ts`

```typescript
// constants/questions.ts
export const WELLBEING_QUESTIONS = [
  // 54 questions
];

export const QUESTIONS_BY_CATEGORY = {
  Physical: [...],
  Emotional: [...],
  Social: [...],
  Work: [...],
  Purpose: [...],
  Financial: [...],
  SelfCare: [...],
};

export const CATEGORIES = Object.keys(QUESTIONS_BY_CATEGORY);
export const QUESTIONS_PER_GROUP = 3;
```

**Benefits**:
- Questions can be reused
- Easy to modify/add questions
- Can be loaded from API in future

---

### Step 2: Extract Types (15 minutes)

**From**: Throughout the file
**To**: `types.ts`

```typescript
// types.ts
export interface WellbeingQuestion {
  id: string;
  category: string;
  text: string;
  options: string[];
}

export interface WellbeingResponse {
  questionId: string;
  answer: string;
  timestamp: Date;
}

export interface CategoryScore {
  category: string;
  score: number;
  percentage: number;
  level: 'low' | 'medium' | 'high';
}

export interface WellbeingGoal {
  category: string;
  actionItems: string[];
  targetDate: Date;
  completed: boolean;
}
```

---

### Step 3: Extract Scoring Logic (45 minutes)

**From**: Scoring functions in main component
**To**: `constants/scoring.ts` and `utils/calculations.ts`

```typescript
// constants/scoring.ts
export const SCORING_WEIGHTS = {
  Excellent: 4,
  Good: 3,
  Fair: 2,
  Poor: 1,
  // ... all option mappings
};

// utils/calculations.ts
export function calculateCategoryScore(
  questions: WellbeingQuestion[],
  responses: Record<string, string>
): CategoryScore {
  // Calculate score for category
}

export function calculateOverallScore(
  categoryScores: CategoryScore[]
): number {
  // Calculate overall percentage
}

export function getScoreLevel(
  percentage: number
): 'low' | 'medium' | 'high' {
  // Determine level
}
```

---

### Step 4: Create Custom Hooks (2 hours)

#### useAssessmentFlow.ts
```typescript
export function useAssessmentFlow(questions: WellbeingQuestion[]) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [completed, setCompleted] = useState(false);

  const nextQuestion = () => { /* ... */ };
  const prevQuestion = () => { /* ... */ };
  const submitResponse = (answer: string) => { /* ... */ };
  const canProgress = () => { /* ... */ };

  return {
    currentIndex,
    currentQuestion: questions[currentIndex],
    responses,
    completed,
    nextQuestion,
    prevQuestion,
    submitResponse,
    canProgress,
  };
}
```

#### useGoalSetting.ts
```typescript
export function useGoalSetting(category: string) {
  const [goals, setGoals] = useState<WellbeingGoal[]>([]);
  const [showModal, setShowModal] = useState(false);

  const addGoal = (goal: WellbeingGoal) => { /* ... */ };
  const updateGoal = (id: string, updates: Partial<WellbeingGoal>) => { /* ... */ };
  const deleteGoal = (id: string) => { /* ... */ };

  return { goals, showModal, setShowModal, addGoal, updateGoal, deleteGoal };
}
```

#### useProgressTracking.ts
```typescript
export function useProgressTracking() {
  const [history, setHistory] = useState<StoredAssessmentResult[]>([]);
  const [streak, setStreak] = useState<WellnessStreak | null>(null);
  const [actionProgress, setActionProgress] = useState<Record<string, boolean>>({});

  useEffect(() => {
    // Load from wellnessStorage
  }, []);

  const updateActionProgress = (actionId: string, completed: boolean) => { /* ... */ };

  return { history, streak, actionProgress, updateActionProgress };
}
```

---

### Step 5: Create Sub-Components (3 hours)

#### QuestionCard.tsx
```typescript
interface QuestionCardProps {
  question: WellbeingQuestion;
  selectedAnswer: string | undefined;
  onSelect: (answer: string) => void;
}

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  selectedAnswer,
  onSelect,
}) => {
  return (
    <Card>
      <CardHeader>
        <Badge>{question.category}</Badge>
        <CardTitle>{question.text}</CardTitle>
      </CardHeader>
      <CardContent>
        <RadioGroup value={selectedAnswer} onValueChange={onSelect}>
          {question.options.map(option => (
            <RadioGroupItem key={option} value={option}>
              {option}
            </RadioGroupItem>
          ))}
        </RadioGroup>
      </CardContent>
    </Card>
  );
};
```

#### ResultsOverview.tsx
```typescript
interface ResultsOverviewProps {
  overallPercentage: number;
  categoryScores: CategoryScore[];
  onExportPDF: () => void;
  onExportJSON: () => void;
}

export const ResultsOverview: React.FC<ResultsOverviewProps> = ({
  overallPercentage,
  categoryScores,
  onExportPDF,
  onExportJSON,
}) => {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Overall Wellbeing: {overallPercentage}%</CardTitle>
        </CardHeader>
        <CardContent>
          <ScoreProgress value={overallPercentage} />
        </CardContent>
      </Card>

      <CategoryScoresList scores={categoryScores} />

      <div className="flex gap-4">
        <Button onClick={onExportPDF}>Export PDF</Button>
        <Button onClick={onExportJSON}>Export JSON</Button>
      </div>
    </div>
  );
};
```

---

### Step 6: Create Main Orchestrator (1 hour)

```typescript
// index.tsx
const WellbeingAssessment: React.FC = () => {
  const navigate = useNavigate();

  // Hooks
  const {
    currentIndex,
    currentQuestion,
    responses,
    completed,
    nextQuestion,
    prevQuestion,
    submitResponse,
    canProgress,
  } = useAssessmentFlow(WELLBEING_QUESTIONS);

  const { categoryScores, overallPercentage } = useScores(responses);
  const { goals, showModal, addGoal } = useGoalSetting();
  const { history, streak } = useProgressTracking();

  // Early returns
  if (completed) {
    return (
      <div className="space-y-6">
        <ResultsOverview
          overallPercentage={overallPercentage}
          categoryScores={categoryScores}
          onExportPDF={/* ... */}
          onExportJSON={/* ... */}
        />
        <GoalList goals={goals} onAdd={addGoal} />
        <HistoryComparison history={history} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <CategoryProgress
        current={currentIndex}
        total={WELLBEING_QUESTIONS.length}
      />

      <QuestionCard
        question={currentQuestion}
        selectedAnswer={responses[currentQuestion.id]}
        onSelect={submitResponse}
      />

      <NavigationControls
        onBack={prevQuestion}
        onNext={nextQuestion}
        canProgress={canProgress()}
      />
    </div>
  );
};
```

---

## Implementation Checklist

- [ ] Extract question data to `constants/questions.ts`
- [ ] Extract types to `types.ts`
- [ ] Extract scoring logic to `constants/scoring.ts` and `utils/calculations.ts`
- [ ] Create `useAssessmentFlow` hook
- [ ] Create `useGoalSetting` hook
- [ ] Create `useProgressTracking` hook
- [ ] Create `QuestionCard` component
- [ ] Create `CategoryProgress` component
- [ ] Create `NavigationControls` component
- [ ] Create `ResultsOverview` component
- [ ] Create `CategoryScoresList` component
- [ ] Create `GoalModal` component
- [ ] Create `GoalList` component
- [ ] Create `HistoryComparison` component
- [ ] Create main orchestrator `index.tsx`
- [ ] Update router imports
- [ ] Test all functionality
- [ ] Test with real data
- [ ] Remove old file (backup first)

---

## Testing Strategy

### Unit Tests
```typescript
// scoring.test.ts
describe('calculateCategoryScore', () => {
  it('calculates correct percentage for all positive responses', () => {
    const questions = WELLBEING_QUESTIONS.filter(q => q.category === 'Physical');
    const responses = {};
    questions.forEach(q => responses[q.id] = 'Excellent');

    const result = calculateCategoryScore(questions, responses);
    expect(result.percentage).toBe(100);
  });
});
```

### Integration Tests
```typescript
// useAssessmentFlow.test.tsx
describe('useAssessmentFlow', () => {
  it('progresses through questions correctly', () => {
    const { result } = renderHook(() => useAssessmentFlow(QUESTIONS));
    act(() => result.current.submitResponse('Good'));
    act(() => result.current.nextQuestion());
    expect(result.current.currentIndex).toBe(1);
  });
});
```

---

## Benefits of Splitting WellbeingAssessment

1. **Testability**: Can unit test scoring logic independently
2. **Reusability**: QuestionCard can be reused for other assessments
3. **Maintainability**: Change goal logic without touching question flow
4. **Performance**: Only re-render affected components when state changes
5. **Developer Experience**: Easy to understand and modify

---

**Estimated Time**: 5-6 hours
**Difficulty**: Medium (complex state, but clear separation possible)
**Priority**: HIGH (after ClinicalAssessment)

**Next Component**: TeamCompositionOptimizer (1,253 lines)
