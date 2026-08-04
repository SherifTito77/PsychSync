# Assessment Component Migration Guide

**Quick Reference for Migrating Assessment Components to AssessmentContext**

---

## The Migration Pattern

### Step 1: Add the Import

```tsx
import { useAssessment } from '@/contexts/AssessmentContext';
```

### Step 2: Replace State Variables

**Remove these:**
```tsx
// ❌ DELETE these lines
const [assessment, setAssessment] = useState(null);
const [currentQuestion, setCurrentQuestion] = useState(0);
const [answers, setAnswers] = useState<Record<number, string>>({});
const [isLoading, setIsLoading] = useState(true);
const [isSubmitting, setIsSubmitting] = useState(false);
const [results, setResults] = useState<any>(null);
const [error, setError] = useState<string | null>(null);
```

**Replace with:**
```tsx
// ✅ ADD this hook
const {
  assessment,
  currentQuestion,
  answers,
  isLoading,
  isSubmitting,
  results,
  error,
  setAssessment,
  setError,
  clearError
} = useAssessment<YourQuestionType>();
```

### Step 3: Remove Handler Functions

**Remove these:**
```tsx
// ❌ DELETE these functions
const handleAnswer = (questionId: number, value: string) => {
  setAnswers(prev => ({ ...prev, [questionId]: value }));
};

const handleNext = () => {
  if (currentQuestion < (assessment?.questions.length || 0) - 1) {
    setCurrentQuestion(currentQuestion + 1);
  }
};

const handlePrevious = () => {
  if (currentQuestion > 0) {
    setCurrentQuestion(currentQuestion - 1);
  }
};
```

**They're now provided by the context!**

### Step 4: Update Submission Logic

**Before:**
```tsx
const handleSubmit = async () => {
  try {
    setIsSubmitting(true);
    const response = await apiClient.post('/endpoint', { answers });
    setResults(response.data);
    navigate('/results');
  } catch (err) {
    setError('Failed');
    setIsSubmitting(false);
  }
};
```

**After:**
```tsx
const transformAnswers = (answers) => {
  // Your assessment-specific transformation
  return { answers };
};

const submit = () => {
  handleSubmit('/endpoint', transformAnswers);
};
```

### Step 5: Clean Up useEffect

**Before:**
```tsx
useEffect(() => {
  loadAssessment();
}, []); // Empty deps - runs once
```

**After:**
```tsx
useEffect(() => {
  loadAssessment();
}, [assessmentId]); // Only re-run if ID changes

// Or prevent re-loading if already loaded:
useEffect(() => {
  if (assessment) return; // Don't reload
  loadAssessment();
}, [assessmentId]);
```

---

## Complete Example: MBTI Migration

### Before (Original Code)

```tsx
export default function MBTIAssessmentPage() {
  const [assessment, setAssessment] = useState<MBTIAssessment | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { assessmentId } = useParams();

  useEffect(() => {
    loadMBTIAssessment();
  }, []);

  const loadMBTIAssessment = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.get('/assessment-questions/mbti');
      setAssessment(response.data.assessment);
      setIsLoading(false);
    } catch (error) {
      setError('Failed to load assessment');
      setIsLoading(false);
    }
  };

  const handleAnswer = (questionId: number, value: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const handleNext = () => {
    if (currentQuestion < (assessment?.questions.length || 0) - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      const response = await apiClient.post('/assessments/mbti/submit', { answers });
      setResults(response.data);
      navigate('/results');
    } catch (err) {
      setError('Submission failed');
      setIsSubmitting(false);
    }
  };

  return ( /* ... */ );
}
```

### After (Refactored with AssessmentContext)

```tsx
import { useAssessment } from '@/contexts/AssessmentContext';

export default function MBTIAssessmentPage() {
  const { assessmentId } = useParams();

  // All state from context
  const {
    assessment,
    currentQuestion,
    answers,
    isLoading,
    isSubmitting,
    error,
    setAssessment,
    handleAnswer,
    handleNext,
    handlePrevious,
    handleSubmit,
    clearError
  } = useAssessment<MBTIQuestion>();

  useEffect(() => {
    if (assessment) return; // Don't reload
    loadMBTIAssessment();
  }, [assessmentId]);

  const loadMBTIAssessment = async () => {
    try {
      const response = await apiClient.get('/assessment-questions/mbti');
      setAssessment(response.data.assessment);
    } catch (error) {
      setError('Failed to load assessment');
    }
  };

  const transformMBTIAnswers = (answers: Record<number, string>) => {
    // Group answers by dimension (E-I, S-N, T-F, J-P)
    const dimensionAnswers: Record<string, string[]> = {};

    assessment?.questions.forEach(q => {
      if (!dimensionAnswers[q.dimension]) {
        dimensionAnswers[q.dimension] = [];
      }
      if (answers[q.id]) {
        dimensionAnswers[q.dimension].push(answers[q.id]);
      }
    });

    return { answers: dimensionAnswers };
  };

  const submit = () => {
    handleSubmit('/assessments/mbti/submit', transformMBTIAnswers);
  };

  return ( /* ... */ );
}
```

**Result:** ~150 lines removed! (37% reduction)

---

## Assessment-Specific Transformations

Each assessment may need different data transformation:

### MBTI
```tsx
const transformMBTIAnswers = (answers) => {
  const dimensionAnswers: Record<string, string[]> = {};

  assessment?.questions.forEach(q => {
    if (!dimensionAnswers[q.dimension]) {
      dimensionAnswers[q.dimension] = [];
    }
    if (answers[q.id]) {
      dimensionAnswers[q.dimension].push(answers[q.id]);
    }
  });

  return { answers: dimensionAnswers };
};
```

### Big Five
```tsx
const transformBigFiveAnswers = (answers) => {
  // Map answers to traits
  const traitAnswers: Record<string, string[]> = {};

  assessment?.questions.forEach(q => {
    if (!traitAnswers[q.trait]) {
      traitAnswers[q.trait] = [];
    }
    if (answers[q.id]) {
      traitAnswers[q.trait].push(answers[q.id]);
    }
  });

  return { responses: traitAnswers };
};
```

### Enneagram
```tsx
const transformEnneagramAnswers = (answers) => {
  // Flat array of answer values
  const answerArray = Object.values(answers);
  return { responses: answerArray };
};
```

---

## Testing Checklist

After migrating an assessment:

- [ ] Assessment loads without errors
- [ ] Can navigate between questions
- [ ] Answers are saved when navigating
- [ ] Can submit assessment
- [ ] Results display correctly
- [ ] Error states work (network errors, validation)
- [ ] Loading states display properly
- [ ] Keyboard navigation works
- [ ] Mobile responsive

---

## Common Issues

### Issue: "AssessmentContext undefined"

**Cause:** Component used outside of AssessmentProvider
**Fix:** Make sure you're within the App routes

### Issue: State not persisting

**Cause:** Component re-mounting on every navigation
**Fix:** Use React Router's state or implement proper caching

### Issue: Type errors

**Cause:** Missing generic type parameter
**Fix:**
```tsx
useAssessment<YourQuestionType>()
```

---

## Migration Priority

**Week 1:**
1. ✅ MBTI (example created)
2. Big Five (similar to MBTI)
3. Enneagram (simple transformation)

**Week 2:**
4. DISC
5. Social Styles

**Week 3:**
6. Strengths Finder
7. Predictive Index

---

## Benefits You'll See

| Before | After | Improvement |
|--------|-------|-------------|
| ~400 lines | ~250 lines | 37% less code |
| 7 useState hooks | 1 hook | Simpler |
| 3 useEffect | 1 useEffect | Fewer renders |
| Custom error handling | Built-in | Consistent UX |
| No localStorage | Automatic persistence | Better UX |
| Manual navigation | Context-provided | Less code |

---

**Happy migrating!** 🚀

For questions, see:
- `frontend/src/contexts/AssessmentContext.tsx` - Full implementation
- `frontend/src/pages/assessments/types/MBTIAssessmentPageRefactored.tsx` - Working example
- `docs/DESIGN_SYSTEM_GUIDE.md` - Design patterns
