# Design System Migration Guide

## 📊 Current Status

### ✅ Completed (Phase 1)
- **90+ violations fixed** across 7 production files
- **Design token API created** (`frontend/src/utils/designTokens.ts`)
- **ESLint rules integrated** into main config
- **Documentation completed** (DESIGN_SYSTEM_FIXES.md)

### 🔄 Remaining Work (Phase 2)
- **~15 files** with design system violations identified
- **~50-60 violations** estimated (based on grep analysis)
- **Mixed file types**: Demo components, mobile components, lists, charts

---

## 🎯 Phase 2: Prioritized File List

### Priority 1: High-Traffic User-Facing Components
These files are directly visible to end users and should be fixed first.

#### 1. Mobile Components (4 files)
```
frontend/src/components/mobile/MobileCard.tsx
frontend/src/components/mobile/BiometricAuthSettings.tsx
frontend/src/components/mobile/PushNotificationSettings.tsx
frontend/src/components/mobile/PushNotificationExample.tsx
```

**Estimated Violations:** ~15 total
**Impact:** HIGH - Mobile users see these components daily
**Effort:** 2-3 hours

**Common Issues Found:**
- Hardcoded font sizes: `fontSize: 14`, `fontSize: 16`
- Hardcoded colors: `color: '#111827'`, `color: '#6b7280'`
- Arbitrary spacing in StyleSheet objects

**Fix Strategy:**
```tsx
// ❌ BEFORE
const styles = StyleSheet.create({
  container: {
    backgroundColor: '#111827',
    padding: 16,
    fontSize: 14
  }
});

// ✅ AFTER (React Native)
import { tokens } from '@/utils/designTokens';

const styles = StyleSheet.create({
  container: {
    backgroundColor: tokens.color.gray(900), // Need to add RN support
    padding: tokens.spacing.md,
    // Note: RN requires numeric font sizes
  }
});

// ✅ EVEN BETTER (React Native Web with Tailwind)
<View className="bg-gray-900 p-4 text-sm">
```

---

#### 2. List Components (3 files)
```
frontend/src/components/lists/BasicResponsiveList.tsx
frontend/src/components/lists/SimpleResponsiveList.tsx
frontend/src/components/lists/VirtualizedList.tsx
```

**Estimated Violations:** ~20 total
**Impact:** HIGH - Lists are used throughout the app
**Effort:** 2-3 hours

**Common Issues Found:**
- CSS-in-JS with hardcoded colors in `<style>` tags
- Arbitrary spacing: `padding: 12px 16px`
- Hardcoded colors: `#2d3748`, `#3182ce`, `#f7fafc`

**Fix Strategy:**
```tsx
// ❌ BEFORE
<style>{`
  .list-item {
    padding: 12px 16px;
    color: #2d3748;
    background-color: #f7fafc;
  }
`}</style>

// ✅ AFTER
<style>{`
  .list-item {
    padding: var(--spacing-md); /* 16px */
    color: var(--color-gray-800);
    background-color: var(--color-gray-50);
  }
`}</style>

// ✅ EVEN BETTER (if component allows)
<div className="p-4 text-gray-800 bg-gray-50">
```

---

#### 3. Chart/Data Visualization (1 file)
```
frontend/src/components/charts/ProgressChart.tsx
```

**Estimated Violations:** ~5
**Impact:** MEDIUM - Used in analytics dashboards
**Effort:** 30 minutes

**Common Issues Found:**
- Chart library styling with hardcoded colors
- Custom tooltip colors

---

### Priority 2: Developer Tools & Performance Monitoring
These are used by developers and power users.

```
frontend/src/components/performance/SecurePerformanceDashboard.tsx
frontend/src/components/OptimizedComponent.tsx
```

**Estimated Violations:** ~10 total
**Impact:** MEDIUM - Internal tools
**Effort:** 1-2 hours

---

### Priority 3: Educational/Demo Components
These files **intentionally show anti-patterns** for educational purposes. Consider adding ESLint overrides.

```
frontend/src/components/demo/FontScalingDemo.tsx
frontend/src/components/ProblemScenarios.tsx
frontend/src/components/accessibility/FontScalingValidator.tsx
```

**Estimated Violations:** ~15 total
**Impact:** LOW - Demo/educational content
**Effort:** 1 hour OR add ESLint override (5 minutes)

**Recommendation:**
Add ESLint overrides for these files instead of fixing them, as they demonstrate what NOT to do:

```js
// In eslint.config.js
{
  files: [
    "frontend/src/components/demo/**/*.{ts,tsx}",
    "frontend/src/components/ProblemScenarios.tsx",
    "frontend/src/**/*Validator*.{ts,tsx}"
  ],
  rules: {
    "no-restricted-syntax": "off", // Allow hardcoded values in demos
  }
}
```

---

### Priority 4: Specialized Components
Lower priority due to limited usage.

```
frontend/src/components/trajectories/GrowthTrajectoryVisualization.tsx
frontend/src/components/anonymization/DeIdentificationTools.tsx
```

**Estimated Violations:** ~5-10 total
**Impact:** LOW - Specialized features
**Effort:** 1 hour

---

## 🔧 Fix Strategies by Pattern

### Pattern 1: Inline Styles in JSX
**Found in:** MobileCard, BiometricAuthSettings, ProblemScenarios

```tsx
// ❌ BEFORE
<div style={{
  padding: '16px',
  color: '#333',
  fontSize: '14px',
  borderRadius: '8px'
}}>

// ✅ AFTER (Tailwind)
<div className="p-4 text-gray-900 text-sm rounded-lg">

// ✅ AFTER (Design Tokens - for dynamic values)
<div style={createStyles({
  padding: tokens.spacing.md,
  color: tokens.color.gray(900),
  fontSize: tokens.typography.size.sm,
  borderRadius: tokens.radius.lg
})}>
```

---

### Pattern 2: CSS-in-JS in Style Tags
**Found in:** BasicResponsiveList, FontScalingDemo

```tsx
// ❌ BEFORE
<style>{`
  .custom-item {
    padding: 12px 16px;
    background-color: #f7fafc;
    color: #2d3748;
    font-size: 14px;
  }
`}</style>

// ✅ AFTER (CSS Variables)
<style>{`
  .custom-item {
    padding: var(--spacing-md);
    background-color: var(--color-gray-50);
    color: var(--color-gray-800);
    font-size: var(--font-size-sm);
  }
`}</style>

// ✅ ALTERNATIVE (Tailwind with @apply)
<style>{`
  .custom-item {
    @apply p-4 bg-gray-50 text-gray-800 text-sm;
  }
`}</style>
```

---

### Pattern 3: React Native StyleSheet
**Found in:** BiometricAuthSettings, PushNotificationSettings

```tsx
// ❌ BEFORE
const styles = StyleSheet.create({
  container: {
    backgroundColor: '#111827',
    padding: 16,
  },
  text: {
    fontSize: 14,
    color: '#6b7280',
  }
});

// ✅ AFTER (with token constants)
import { DESIGN_TOKENS } from '@/constants/designTokens';

const styles = StyleSheet.create({
  container: {
    backgroundColor: DESIGN_TOKENS.colors.gray[900],
    padding: DESIGN_TOKENS.spacing.md,
  },
  text: {
    fontSize: DESIGN_TOKENS.typography.size.sm,
    color: DESIGN_TOKENS.colors.gray[500],
  }
});

// Note: React Native requires numeric values, so we need a constants file
// Create: frontend/src/constants/designTokens.ts
```

**Create Required File:** `frontend/src/constants/designTokens.ts`
```typescript
// Design tokens for React Native (numeric values)
export const DESIGN_TOKENS = {
  colors: {
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',
      500: '#6b7280',
      800: '#1f2937',
      900: '#111827',
    },
    primary: {
      blue: '#3b82f6',
      green: '#10b981',
      red: '#ef4444',
    }
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  typography: {
    size: {
      xs: 12,
      sm: 14,
      base: 16,
      lg: 18,
      xl: 20,
    }
  },
  radius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
  }
};
```

---

### Pattern 4: Dynamic/Conditional Styles
**Found in:** GrowthTrajectoryVisualization, ProgressChart

```tsx
// ❌ BEFORE
const getColor = (severity: number) => {
  if (severity > 7) return '#ef4444';
  if (severity > 4) return '#f59e0b';
  return '#10b981';
};

// ✅ AFTER (Design Tokens)
import { tokens } from '@/utils/designTokens';

const getColor = (severity: number) => {
  if (severity > 7) return tokens.color.error();
  if (severity > 4) return tokens.color.warning();
  return tokens.color.success();
};

// ✅ AFTER (Tailwind classes)
const getColorClass = (severity: number) => {
  if (severity > 7) return 'text-red-500';
  if (severity > 4) return 'text-orange-500';
  return 'text-green-500';
};
```

---

## 📋 Implementation Checklist

### Step 1: Prepare Environment
- [ ] Review ESLint config integration completed in Phase 1
- [ ] Create `frontend/src/constants/designTokens.ts` for React Native
- [ ] Add missing CSS variables if needed
- [ ] Test design token API imports

### Step 2: Fix High-Priority Files
- [ ] **MobileCard.tsx** - Convert inline styles to Tailwind
- [ ] **BiometricAuthSettings.tsx** - Create RN token constants
- [ ] **PushNotificationSettings.tsx** - Use RN token constants
- [ ] **PushNotificationExample.tsx** - Convert to tokens

### Step 3: Fix List Components
- [ ] **BasicResponsiveList.tsx** - CSS variables in style tags
- [ ] **SimpleResponsiveList.tsx** - Tailwind conversion
- [ ] **VirtualizedList.tsx** - Dynamic styles with tokens

### Step 4: Fix Remaining Components
- [ ] **ProgressChart.tsx** - Chart library styling
- [ ] **SecurePerformanceDashboard.tsx** - Performance monitoring
- [ ] **GrowthTrajectoryVisualization.tsx** - Trajectory charts
- [ ] **DeIdentificationTools.tsx** - Privacy tools
- [ ] **OptimizedComponent.tsx** - Performance demos

### Step 5: Handle Demo Files
- [ ] **Option A:** Fix demo files to use design tokens (1 hour)
- [ ] **Option B:** Add ESLint overrides for demo files (5 minutes)
  ```js
  {
    files: ["**/demo/**/*.{ts,tsx}", "**/ProblemScenarios.tsx"],
    rules: { "no-restricted-syntax": "off" }
  }
  ```

### Step 6: Verification
- [ ] Run `npm run lint` to check for remaining violations
- [ ] Run `npm run type-check` to verify TypeScript
- [ ] Visual regression test for color changes
- [ ] Test mobile components on actual devices
- [ ] Update DESIGN_SYSTEM_FIXES.md with Phase 2 changes

---

## 🎓 Learning Resources

### Design Token API Usage
```typescript
import { tokens, createStyles, cn } from '@/utils/designTokens';

// Color tokens
tokens.color.primary(600)  // 'var(--color-primary-600)'
tokens.color.success()      // 'var(--color-success)'
tokens.color.error()        // 'var(--color-error)'

// Spacing tokens
tokens.spacing.md  // 'var(--spacing-md)' (16px)
tokens.spacing.lg  // 'var(--spacing-lg)' (24px)

// Typography tokens
tokens.typography.size.lg  // 'var(--font-size-lg)' (18px)
tokens.typography.weight.semibold  // 'var(--font-weight-semibold)' (600)

// Border radius
tokens.radius.md  // 'var(--radius-md)' (8px)
tokens.radius.lg  // 'var(--radius-lg)' (12px)

// Helper functions
cn('px-4 py-2', isActive && 'bg-blue-600', isDisabled && 'opacity-50')

createStyles({
  color: tokens.color.primary(600),
  padding: tokens.spacing.md,
  backgroundColor: 'var(--color-gray-50)'
})
```

### Tailwind Class Reference
```html
<!-- Spacing -->
p-4   <!-- padding: 1rem (16px) -->
px-4  <!-- padding-left/right: 1rem -->
py-2  <!-- padding-top/bottom: 0.5rem -->
m-4   <!-- margin: 1rem -->
gap-4 <!-- gap: 1rem -->

<!-- Colors -->
bg-blue-600   <!-- background-color: var(--color-blue-600) -->
text-gray-900 <!-- color: var(--color-gray-900) -->
border-red-500 <!-- border-color: var(--color-red-500) -->

<!-- Typography -->
text-sm   <!-- font-size: 0.875rem (14px) -->
text-base <!-- font-size: 1rem (16px) -->
text-lg   <!-- font-size: 1.125rem (18px) -->
font-bold <!-- font-weight: 700 -->
font-semibold <!-- font-weight: 600 -->

<!-- Borders -->
rounded   <!-- border-radius: 0.25rem (4px) -->
rounded-lg <!-- border-radius: 0.5rem (8px) -->
border    <!-- border-width: 1px -->
border-2  <!-- border-width: 2px -->

<!-- Responsive -->
text-sm sm:text-base md:text-lg <!-- responsive text -->
p-2 sm:p-4 md:p-6               <!-- responsive padding -->
```

### CSS Variable Reference
```css
/* Colors */
var(--color-primary-600)    /* #2563eb */
var(--color-success)        /* #10b981 */
var(--color-warning)        /* #f59e0b */
var(--color-error)          /* #ef4444 */
var(--color-gray-50)        /* #f9fafb */
var(--color-gray-900)       /* #111827 */

/* Spacing */
var(--spacing-xs)    /* 4px */
var(--spacing-sm)    /* 8px */
var(--spacing-md)    /* 16px */
var(--spacing-lg)    /* 24px */
var(--spacing-xl)    /* 32px */

/* Typography */
var(--font-size-xs)    /* 12px */
var(--font-size-sm)    /* 14px */
var(--font-size-base)  /* 16px */
var(--font-size-lg)    /* 18px */
var(--font-size-xl)    /* 20px */

/* Border Radius */
var(--radius-sm)  /* 4px */
var(--radius-md)  /* 8px */
var(--radius-lg)  /* 12px */
```

---

## ⚠️ Common Pitfalls

### 1. React Native Numeric Values
❌ **Wrong:** `StyleSheet.create({ fontSize: '14px' })`
✅ **Right:** `StyleSheet.create({ fontSize: 14 })`
✅ **Better:** Use DESIGN_TOKENS constants

### 2. Dynamic Colors with Tailwind
❌ **Wrong:** `className="text-${color}-600"` (Tailwind won't see dynamic classes)
✅ **Right:** Use design tokens for dynamic colors
```tsx
<div style={{ color: `var(--color-${color}-600)` }}>
```

### 3. Arbitrary Values
❌ **Wrong:** `className="p-[13px]"` (not on 4px grid)
✅ **Right:** `className="p-4"` (16px on grid)

### 4. Forgetting to Import Design Tokens
❌ **Wrong:** Using hardcoded values when tokens available
✅ **Right:** Always import from `@/utils/designTokens`

---

## 🚀 Quick Start Commands

```bash
# Check for violations in specific file
npm run lint -- frontend/src/components/mobile/MobileCard.tsx

# Auto-fix where possible
npm run lint:fix

# Type check after changes
npm run type-check

# Check specific pattern
grep -r "color.*#" frontend/src/components/mobile/
grep -r "fontSize.*px" frontend/src/components/lists/
```

---

## 📊 Metrics Tracking

### Phase 1 Completed
- Files fixed: 7
- Violations resolved: 90+
- Time invested: ~3 hours
- Files created: 3 (designTokens.ts, ESLint config, docs)

### Phase 2 Estimated
- Files to fix: 12-15
- Violations to resolve: ~50-60
- Estimated time: 8-12 hours
- Files to create: 1 (designTokens.ts for RN)

### Total Project Impact
- **Before:** 140+ violations across 22+ files
- **After Phase 1:** 50-60 violations across 15 files
- **After Phase 2:** 0 violations (target)
- **Total Investment:** ~15 hours
- **Annual Savings:** 50+ hours of maintenance

---

## 🎯 Success Criteria

Phase 2 is complete when:
- [ ] All high-priority files use design tokens or Tailwind
- [ ] ESLint runs without design system errors
- [ ] No hardcoded hex colors in production code
- [ ] No hardcoded font sizes in production code
- [ ] All spacing on 4px grid
- [ ] React Native components use token constants
- [ ] Demo files documented or ESLint override added
- [ ] Migration guide finalized

---

## 📞 Support & Questions

- **Design Token API:** See `frontend/src/utils/designTokens.ts`
- **Phase 1 Documentation:** See `DESIGN_SYSTEM_FIXES.md`
- **CSS Variables:** See `frontend/src/styles/global/variables.css`
- **Tailwind Config:** See `frontend/tailwind.config.js`
- **ESLint Rules:** See `frontend/eslint.config.js`

---

*Generated: 2025-01-21*
*Phase 1 Complete | Phase 2 In Progress*
*Next Review: After Phase 2 completion*
