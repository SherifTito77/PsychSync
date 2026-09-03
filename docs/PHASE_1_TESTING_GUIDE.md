# Phase 1 Testing Guide - Clinical Components

## Overview

Comprehensive testing checklist for the three split Phase 1 components:
1. ClinicalResults
2. ClinicalAssessment
3. WellbeingAssessment

---

## Prerequisites

### Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

### Expected Output
```
VITE v5.x.x ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

---

## Component 1: ClinicalResults Testing

### URL Routes
- Main route: `http://localhost:5173/clinical/results/:tool`
- Tool types: `phq9`, `gad7`, `pcl5`, `dass21`, `audit`, `stress`, `wellbeing`

### Test Scenarios

#### ✅ Test 1: Load PHQ-9 Results
1. Navigate to: `http://localhost:5173/clinical/results/phq9`
2. **Expected**:
   - Page loads without errors
   - Results header displays "PHQ9 Results"
   - Score display shows numerical score
   - Severity banner appears if score is high
   - Recommendations list displays
   - Resources grid shows crisis resources if needed

#### ✅ Test 2: Load GAD-7 Results
1. Navigate to: `http://localhost:5173/clinical/results/gad7`
2. **Expected**:
   - Page loads with "GAD7 Results" title
   - Anxiety-specific recommendations display
   - GAD-7 appropriate resources shown

#### ✅ Test 3: Crisis Alert Display
1. Navigate to: `http://localhost:5173/clinical/results/phq9`
2. **Expected**:
   - If score ≥ 20: Red crisis alert banner displays
   - "Get Immediate Help" button visible
   - Crisis resources prioritized

#### ✅ Test 4: Action Buttons
1. On any results page, test each button:
   - **Share with Provider**: Should navigate to referral page
   - **Save Results**: Should save to localStorage
   - **Retake Assessment**: Should navigate to assessment page
   - **Take Another Assessment**: Should navigate to assessments list
   - **Back Button**: Should navigate to previous page

#### ✅ Test 5: Metadata Display
1. Complete an assessment with responses
2. View results
3. **Expected**:
   - Assessment date displays correctly
   - Time to complete shows
   - Questions answered count shows
   - Provider notification status displays

#### ✅ Test 6: Tool-Specific Education
1. Test each assessment type
2. **Expected**:
   - PHQ-9: Shows depression education
   - PCL-5: Shows PTSD education
   - GAD-7: Shows anxiety education
   - Each has appropriate color coding

### Console Checks
Open browser DevTools (F12) → Console tab:
- ✅ No errors (red text)
- ✅ No warnings (yellow text)
- ✅ API requests show in Network tab

---

## Component 2: ClinicalAssessment Testing

### URL Routes
- Main route: `http://localhost:5173/clinical/assessment/:tool`
- Tool types: `phq9`, `gad7`, `stress`

### Test Scenarios

#### ✅ Test 1: Load PHQ-9 Assessment
1. Navigate to: `http://localhost:5173/clinical/assessment/phq9`
2. **Expected**:
   - Assessment loads without errors
   - Title shows "PHQ-9 Depression Screening"
   - Instructions display
   - First question displays with 4 radio options
   - Progress bar shows "Question 1 of X"

#### ✅ Test 2: Answer Questions
1. Select each answer option in turn
2. **Expected**:
   - Radio button highlights when selected
   - Only one option can be selected per question
   - Selection persists when moving between questions

#### ✅ Test 3: Question Navigation
1. Click "Next" button
2. **Expected**:
   - Progress bar updates
   - Next question displays
   - Previous button becomes enabled
   - Responses are retained

#### ✅ Test 4: Previous Button
1. Answer 2-3 questions
2. Click "Previous" button
3. **Expected**:
   - Previous question displays
   - Previous answer is selected
   - Progress bar updates
   - Can change previous answer

#### ✅ Test 5: Required Questions
1. Try to click "Next" without selecting an answer
2. **Expected**:
   - "Next" button is disabled
   - User cannot proceed without answering

#### ✅ Test 6: Submit Assessment
1. Answer all questions
2. Click "Submit Assessment" on final question
3. **Expected**:
   - Button shows "Submitting..." state
   - API call made to `/api/v1/clinical/screenings`
   - Redirects to results page
   - Results show correct score

#### ✅ Test 7: GAD-7 Assessment
1. Navigate to: `http://localhost:5173/clinical/assessment/gad7`
2. **Expected**:
   - Title shows "GAD-7 Anxiety Screening"
   - 7 anxiety-specific questions
   - Appropriate scoring (0-21 range)

#### ✅ Test 8: Stress Assessment (PSS)
1. Navigate to: `http://localhost:5173/clinical/assessment/stress`
2. **Expected**:
   - Title shows "Perceived Stress Scale (PSS)"
   - PSS-10 questions display
   - Appropriate response options (Never to Very often)

### Console Checks
- ✅ No JavaScript errors
- ✅ API requests in Network tab
- ✅ LocalStorage updates
- ✅ Navigation works correctly

---

## Component 3: WellbeingAssessment Testing

### URL Route
- Main route: `http://localhost:5173/wellbeing-assessment`

### Test Scenarios

#### ✅ Test 1: Load Assessment
1. Navigate to: `http://localhost:5173/wellbeing-assessment`
2. **Expected**:
   - Page loads without errors
   - Title shows "Comprehensive Wellbeing Assessment"
   - Description text displays
   - Info alert shows with tips
   - First category displays (Physical)

#### ✅ Test 2: Category Progress
1. Look at progress bar
2. **Expected**:
   - Shows current category name (e.g., "Physical")
   - Shows "1 of 7 categories"
   - Shows question group number
   - Progress bar animates

#### ✅ Test 3: Answer Physical Questions
1. Answer all 3 Physical questions (group 1)
2. Click "Next"
3. **Expected**:
   - Moves to next question group or category
   - Progress updates
   - Previous button enabled
   - Responses retained

#### ✅ Test 4: Complete Assessment
1. Answer all 54 questions across 7 categories
2. Click "View Results" on final question
3. **Expected**:
   - Shows "Wellbeing Assessment Results" page
   - Overall percentage displays (large number)
   - All 7 category scores show
   - Each category has progress bar and percentage
   - Color coding: Green (high), Yellow (medium), Red (low)

#### ✅ Test 5: Category Breakdown
1. On results page, check each category:
   - Physical
   - Emotional
   - Social
   - Work
   - Purpose
   - Financial
   - SelfCare
2. **Expected**:
   - All categories display
   - Scores are calculated correctly
   - Percentages are accurate
   - Color coding matches level

#### ✅ Test 6: Results Actions
1. Test action buttons:
   - **Retake Assessment**: Reloads page
   - **View Dashboard**: Navigates to home
   - **Back Button**: Navigates to dashboard
2. **Expected**: All navigation works

#### ✅ Test 7: Data Persistence
1. Complete assessment
2. Check localStorage:
   ```javascript
   // In browser console:
   JSON.parse(localStorage.getItem('wellbeingAssessmentHistory'))
   ```
3. **Expected**:
   - Result saved with ID, date, scores
   - History array contains previous assessments

#### ✅ Test 8: Responsive Design
1. Resize browser window
2. Test on mobile view (375px width)
3. **Expected**:
   - Questions display properly on mobile
   - Buttons remain clickable
   - Progress bars visible
   - No horizontal scrolling

### Console Checks
- ✅ No errors on page load
- ✅ No errors during navigation
- ✅ localStorage saves correctly
- ✅ Scoring calculations accurate

---

## Integration Testing

### Cross-Component Flows

#### ✅ Test 1: Assessment → Results Flow
1. Start PHQ-9 assessment
2. Complete all questions
3. Submit
4. **Expected**:
   - Smooth transition to results page
   - Results reflect submitted answers
   - Score calculation matches manual calculation

#### ✅ Test 2: Multiple Assessment Types
1. Complete PHQ-9 assessment
2. Complete GAD-7 assessment
3. View results for both
4. **Expected**:
   - Each assessment type works independently
   - No data leakage between assessments
   - Correct scoring for each type

#### ✅ Test 3: Error Handling
1. Disconnect from network (DevTools → Network tab → Offline)
2. Try to submit assessment
3. **Expected**:
   - Graceful error handling
   - User-friendly error message
   - Option to retry or save locally

---

## Performance Testing

### Load Time Checks
1. Open DevTools → Network tab
2. Reload page
3. **Expected**:
   - Initial page load: < 3 seconds
   - JavaScript bundles load efficiently
   - No 404 errors for missing files

### Render Performance
1. Open DevTools → Performance tab
2. Record while navigating through assessment
3. **Expected**:
   - Smooth transitions between questions
   - No noticeable lag on button clicks
   - Progress bars animate smoothly

---

## Automated Testing (TODO)

### Unit Tests to Create
```bash
# Create test files
touch frontend/src/pages/clinical-results/hooks/useClinicalResults.test.ts
touch frontend/src/pages/clinical-assessment/hooks/useAssessmentFlow.test.ts
touch frontend/src/pages/wellbeing-assessment/utils/scoring.test.ts
```

### Example Unit Test
```typescript
// clinical-results/utils/severityCalculator.test.ts
import { calculateSeverity, getSeverityColorClass } from './severityCalculator';

describe('calculateSeverity', () => {
  it('returns severe for scores > 20', () => {
    const result = calculateSeverity(22, 'phq9');
    expect(result.label).toBe('Severe Symptoms');
    expect(result.color).toBe('red');
  });

  it('returns moderate for scores 10-14', () => {
    const result = calculateSeverity(12, 'phq9');
    expect(result.label).toBe('Moderate Symptoms');
    expect(result.color).toBe('orange');
  });
});
```

### Run Tests
```bash
cd frontend
npm run test
```

---

## Browser Compatibility

### Test in Multiple Browsers
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari (if on Mac)
- ✅ Mobile browsers (Chrome Mobile, Safari Mobile)

---

## Pre-Launch Checklist

### Before Merging to Main
- [ ] All manual tests pass
- [ ] No console errors
- [ ] All navigation flows work
- [ ] Data persists correctly
- [ ] Responsive design works
- [ ] Cross-browser compatibility verified
- [ ] Performance acceptable (< 3s load time)
- [ ] Accessibility: keyboard navigation works
- [ ] Accessibility: screen reader compatible

---

## Common Issues & Solutions

### Issue 1: "Cannot find module"
**Solution**: Check import paths, ensure all files exist in correct locations

### Issue 2: "TypeError: X is not a function"
**Solution**: Verify exports/imports match, check for circular dependencies

### Issue 3: Results page shows no data
**Solution**: Check localStorage, verify API response format, check network tab

### Issue 4: Navigation not working
**Solution**: Verify React Router setup, check route definitions in App.tsx

### Issue 5: Scoring incorrect
**Solution**: Check SCORE_MAP in scoring.ts, verify calculation logic

---

## Success Criteria

### All Tests Pass When:
- ✅ No console errors
- ✅ All buttons work
- ✅ Data persists correctly
- ✅ Navigation flows work
- ✅ Scoring is accurate
- ✅ Responsive design works
- ✅ Performance acceptable

### Component Status
- [ ] ClinicalResults: All tests pass
- [ ] ClinicalAssessment: All tests pass
- [ ] WellbeingAssessment: All tests pass

---

## Next Steps After Testing

1. **Document any bugs found**
2. **Create GitHub issues** for bugs
3. **Fix critical bugs** before proceeding
4. **Add unit tests** for failed scenarios
5. **Update documentation** with any changes

---

**Testing Time Estimate**: 30-60 minutes
**Automated Testing**: 2-3 hours to create test suite
**Total Time**: 3-4 hours for comprehensive testing
