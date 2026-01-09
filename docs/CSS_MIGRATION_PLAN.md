# CSS Architecture Migration Plan

**Project:** PsychSync Frontend
**Current State:** Custom CSS utilities + mixed frameworks
**Target State:** Tailwind CSS + CSS Modules
**Estimated Timeline:** 6-7 weeks
**Bundle Reduction:** 50-70% (2,731 lines → ~800 lines)

---

## Executive Summary

The current frontend codebase has **2,731 lines of custom CSS** that manually reimplements Tailwind utilities. By migrating to a proper Tailwind setup with CSS Modules, we will:

- **Reduce CSS bundle size by 50-70%**
- **Improve maintainability** through component-scoped styles
- **Enable tree-shaking** of unused CSS
- **Standardize design tokens** across the application
- **Eliminate duplicate utility classes**

---

## Current State Analysis

### Problems Identified

1. **No Tailwind Configuration** (`tailwind.config.js` is missing)
2. **Manual Utility Implementation** (624 lines in `index.css`)
3. **No CSS Modules** (all styles are global)
4. **Duplicate Mobile Utilities** (729 lines in `mobile-optimizations.css`)
5. **Mixed CSS Frameworks** (Material UI + Emotion + custom utilities)

### Current File Structure

```
frontend/src/
├── index.css (624 lines) - Manual Tailwind utilities
├── App.css (71 lines) - App-level styles
└── styles/
    ├── mobile-optimizations.css (729 lines)
    ├── mobile-utils.css (394 lines)
    ├── pwa.css (469 lines)
    ├── clinical.css (325 lines)
    └── components/
        └── SimpleResponsiveList.css (126 lines)
```

**Total: 2,731 lines of CSS**

---

## Target Architecture

### New File Structure

```
frontend/src/
├── styles/
│   ├── global/
│   │   ├── reset.css         # CSS reset & normalize
│   │   ├── variables.css     # Design tokens (colors, spacing, typography)
│   │   └── base.css          # Base element styles
│   ├── themes/
│   │   ├── light.css         # Light theme overrides
│   │   ├── dark.css          # Dark theme overrides
│   │   └── clinical.css      # Clinical assessment theme
│   └── utilities.css         # Tailwind directives (minimal)
├── components/
│   └── ComponentName.module.css  # Component-scoped styles
└── tailwind.config.js        # Tailwind configuration (NEW)
```

---

## Migration Phases

### Phase 1: Foundation Setup (Week 1)

**Goals:** Set up Tailwind, create design tokens, establish build process

#### Day 1-2: Install and Configure Tailwind

1. **Install dependencies:**
```bash
npm install -D tailwindcss@latest postcss@latest autoprefixer@latest
npm install -D @tailwindcss/forms @tailwindcss/typography
```

2. **Create `tailend.config.js`:**
```javascript
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./index.html",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        clinical: {
          crisis: '#dc2626',
          moderate: '#f97316',
          mild: '#d97706',
          stable: '#10b981',
        }
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'Inter', 'system-ui'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
```

3. **Create `postcss.config.js`:**
```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

4. **Update `vite.config.ts`:**
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: {
      plugins: [
        require('tailwindcss'),
        require('autoprefixer'),
      ],
    },
  },
})
```

#### Day 3-4: Create Design Tokens

1. **Create `src/styles/global/variables.css`:**
```css
/**
 * Design Tokens - CSS Custom Properties
 * These variables can be referenced in CSS modules and Tailwind config
 */

:root {
  /* Colors - Primary */
  --color-primary-50: #eff6ff;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;

  /* Colors - Semantic */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;

  /* Spacing Scale (4px base unit) */
  --spacing-xs: 0.25rem;    /* 4px */
  --spacing-sm: 0.5rem;     /* 8px */
  --spacing-md: 1rem;       /* 16px */
  --spacing-lg: 1.5rem;     /* 24px */
  --spacing-xl: 2rem;       /* 32px */
  --spacing-2xl: 3rem;      /* 48px */

  /* Typography */
  --font-size-xs: 0.75rem;   /* 12px */
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-base: 1rem;    /* 16px */
  --font-size-lg: 1.125rem;  /* 18px */
  --font-size-xl: 1.25rem;   /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 1.875rem; /* 30px */

  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
  --transition-slow: 300ms ease;

  /* Z-index scale */
  --z-dropdown: 1000;
  --z-sticky: 1020;
  --z-fixed: 1030;
  --z-modal-backdrop: 1040;
  --z-modal: 1050;
  --z-popover: 1060;
  --z-tooltip: 1070;
}

/* Dark mode overrides */
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary-500: #60a5fa;
    --color-primary-600: #3b82f6;
  }
}
```

2. **Create `src/styles/global/reset.css`:**
```css
/* Modern CSS reset with Tailwind compatibility */
*, ::before, ::after {
  box-sizing: border-box;
  border-width: 0;
  border-style: solid;
  border-color: #e5e7eb;
}

::before, ::after {
  --tw-content: '';
}

html {
  line-height: 1.5;
  -webkit-text-size-adjust: 100%;
  -webkit-tap-highlight-color: transparent;
}

body {
  margin: 0;
  line-height: inherit;
}

/* Remove default button styles */
button {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  color: inherit;
  cursor: pointer;
}

/* Remove list styles */
ul, ol {
  list-style: none;
  margin: 0;
  padding: 0;
}

/* Reset headings */
h1, h2, h3, h4, h5, h6 {
  margin: 0;
  font-weight: inherit;
}

/* Reset links */
a {
  color: inherit;
  text-decoration: inherit;
}

/* Reset images */
img, svg, video {
  display: block;
  max-width: 100%;
}

/* Reset inputs */
input, button, textarea, select {
  font: inherit;
  color: inherit;
}
```

3. **Create `src/styles/utilities.css`:**
```css
/**
 * Tailwind CSS Utilities
 * This file replaces index.css manual utilities
 */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom utilities that can't be done with Tailwind */
@layer utilities {
  .text-balance {
    text-wrap: balance;
  }

  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
}
```

**Success Criteria:**
- ✅ `tailwind.config.js` created
- ✅ `postcss.config.js` created
- ✅ Design tokens defined in `variables.css`
- ✅ Build process works without errors

---

### Phase 2: Core Component Migration (Week 2-3)

**Goals:** Migrate high-impact components to CSS Modules

#### Priority Components (High Usage)

1. **Button Component** (`src/components/common/Button.tsx`)
   - Create `Button.module.css`
   - Convert all variants to CSS classes
   - Implement hover, active, focus states

2. **Card Components** (3 systems → 1)
   - Merge: `card.tsx`, `MobileCard.tsx`, `Card.tsx`
   - Create unified `Card.module.css`
   - Implement responsive variants

3. **Input Components** (`src/components/ui/Input.tsx`)
   - Create `Input.module.css`
   - Handle all input types
   - Implement error, disabled states

4. **Modal/Dialog** (`src/components/ui/dialog.tsx`)
   - Create `Dialog.module.css`
   - Implement animations with Tailwind

#### Example: Button Component Migration

**Before (inline styles):**
```tsx
<Button className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
  Click me
</Button>
```

**After (CSS Modules):**
```tsx
// Button.module.css
.button {
  @apply inline-flex items-center justify-center px-4 py-2 rounded-md font-medium transition-colors duration-200;
}

.buttonPrimary {
  @apply bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2;
}

.buttonSecondary {
  @apply bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2;
}

// Button.tsx
import styles from './Button.module.css';

<button className={`${styles.button} ${styles.buttonPrimary}`}>
  Click me
</button>
```

**Success Criteria:**
- ✅ 10 core components migrated
- ✅ No visual regressions
- ✅ All Tailwind classes purged properly
- ✅ Bundle size reduced by 30%

---

### Phase 3: Page-Level Migration (Week 4-5)

**Goals:** Migrate assessment pages and major pages

#### Migration Strategy

1. **Assessment Pages** (7 pages)
   - Use shared `Assessment.module.css`
   - Consolidate duplicate styles

2. **Dashboard Pages**
   - Migrate to grid-based layouts with Tailwind
   - Create reusable layout modules

3. **Clinical Pages**
   - Merge `clinical.css` into `Clinical.module.css`
   - Implement theme tokens

#### Migration Pattern

For each page:
1. Create `PageName.module.css`
2. Extract page-specific styles
3. Replace global classes with module classes
4. Remove unused CSS from global files
5. Test for visual regressions

**Success Criteria:**
- ✅ All assessment pages migrated
- ✅ Dashboard pages migrated
- ✅ Clinical pages migrated
- ✅ Bundle size reduced by 50%

---

### Phase 4: Mobile Optimization Migration (Week 6)

**Goals:** Consolidate mobile utilities

#### Current State
- `mobile-optimizations.css` (729 lines)
- `mobile-utils.css` (394 lines)
- **Total: 1,123 lines**

#### Target State
Use Tailwind's responsive utilities:
```css
/* Instead of: */
.mobile-lg-text {
  @media (min-width: 768px) {
    font-size: 1.125rem;
  }
}

/* Use Tailwind: */
className="text-base md:text-lg"
```

**Success Criteria:**
- ✅ Mobile CSS files removed
- ✅ All responsive styles use Tailwind breakpoints
- ✅ Bundle size reduced by 60%

---

### Phase 5: Cleanup & Optimization (Week 7)

**Goals:** Remove unused CSS, optimize build

#### Tasks

1. **Remove Deprecated Files**
   - Delete old CSS files
   - Update all imports
   - Remove unused dependencies

2. **Optimize Build**
   - Enable CSS purging
   - Minify CSS in production
   - Add bundle size monitoring

3. **Documentation**
   - Update style guide
   - Document component patterns
   - Create migration guide for future components

**Success Criteria:**
- ✅ No deprecated CSS files
- ✅ CSS bundle < 50KB (gzipped)
- ✅ 100% code coverage for new components
- ✅ Documentation complete

---

## Bundle Size Projection

### Current State
```
index.css:              45KB
mobile-optimizations:   52KB
mobile-utils:           28KB
pwa.css:                33KB
clinical.css:           23KB
other:                  20KB
─────────────────────────────
Total:                 201KB (uncompressed)
                      ~45KB (gzipped)
```

### Target State
```
reset.css:              2KB
variables.css:          3KB
base.css:               5KB
utilities.css:          8KB (Tailwind purged)
component modules:      25KB (only used styles)
─────────────────────────────
Total:                  43KB (uncompressed)
                      ~12KB (gzipped)

Reduction: 73% smaller
```

---

## Rollout Strategy

### Option A: Big Bang (Not Recommended)
- Migrate everything at once
- **Risk:** High chance of regressions
- **Timeline:** 7 weeks

### Option B: Incremental (Recommended) ✅
- Migrate component-by-component
- New components use new system
- Old components migrated during feature work
- **Risk:** Low, gradual rollout
- **Timeline:** 7-10 weeks, but always shippable

### Option C: Parallel Systems (During Transition)
- Both systems coexist temporarily
- Flag for new components: `USE_NEW_CSS = true`
- Gradual migration over 3 months
- **Risk:** Medium, temporary bundle bloat
- **Timeline:** 12 weeks

---

## Testing Strategy

### Visual Regression Testing

1. **Automated Screenshots**
```bash
npm install -D @percy/cli @percy/playwright

# Percy configuration
npx percy snapshot ./frontend/src/pages
```

2. **Manual Testing Checklist**
- [ ] All color schemes render correctly
- [ ] Responsive breakpoints work
- [ ] Dark mode functions
- [ ] Animations are smooth
- [ ] No layout shifts

### Performance Testing

```bash
# Bundle analysis
npm run build
npx bundle-wizard dist/assets/*.css

# Lighthouse CI
npm install -D @lhci/cli
npx lhci autorun
```

---

## Migration Tools

### Automated Tools

1. **Tailwind CSS Intellisense** (VS Code)
   - Auto-complete for Tailwind classes
   - Preview of styles

2. **PurgeCSS** (Built into Tailwind)
   - Removes unused CSS automatically
   - Configurable safelists

3. **Stylelint** (Linting)
```bash
npm install -D stylelint stylelint-config-standard
```

### Manual Tools

1. **DevTools CSS Coverage**
   - Chrome DevTools → More tools → Coverage
   - Shows unused CSS percentage

2. **CSS Stats** (Bundle analysis)
```bash
npx cssstats frontend/src/**/*.css
```

---

## Success Metrics

### Quantitative Metrics
- [ ] CSS bundle size reduced by 50%+
- [ ] Build time maintained or improved
- [ ] Zero visual regressions
- [ ] 90%+ components use CSS Modules

### Qualitative Metrics
- [ ] Developer feedback: easier to maintain
- [ ] Faster feature development
- [ ] Consistent design system
- [ ] Better TypeScript integration

---

## Risk Mitigation

### Potential Risks

1. **Learning Curve**
   - **Mitigation:** Team training, documentation
   - **Timeline:** 1 week training during Phase 1

2. **Visual Regressions**
   - **Mitigation:** Automated screenshot testing
   - **Timeline:** Set up in Phase 1

3. **Build Failures**
   - **Mitigation:** Incremental migration, feature flags
   - **Timeline:** Use Option B (Incremental)

4. **Performance Regression**
   - **Mitigation:** Bundle size monitoring, Lighthouse CI
   - **Timeline:** Continuous monitoring

---

## Next Steps

### Immediate Actions (This Week)

1. ✅ **Review and approve this migration plan**
2. **Set up Tailwind in development environment**
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```
3. **Create feature branch:**
   ```bash
   git checkout -b feature/css-migration-phase1
   ```
4. **Migrate 1-2 components as proof of concept**
5. **Get team feedback and adjust plan**

### Long-term Actions

1. **Schedule migration sprints**
2. **Assign component ownership**
3. **Set up CI/CD for visual regression tests**
4. **Document lessons learned**

---

## Appendix: Code Examples

### A. Complete Button Component Migration

**`Button.module.css`:**
```css
.button {
  @apply inline-flex items-center justify-center rounded-md font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed;
}

/* Sizes */
.buttonSmall {
  @apply px-3 py-1.5 text-sm;
}

.buttonMedium {
  @apply px-4 py-2 text-base;
}

.buttonLarge {
  @apply px-6 py-3 text-lg;
}

/* Variants */
.buttonPrimary {
  @apply bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500;
}

.buttonSecondary {
  @apply bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500;
}

.buttonOutline {
  @apply border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50 focus:ring-indigo-500;
}

.buttonGhost {
  @apply bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500;
}
```

**`Button.tsx`:**
```tsx
import styles from './Button.module.css';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}

export default function Button({
  variant = 'primary',
  size = 'medium',
  children,
  ...props
}: ButtonProps) {
  const className = [
    styles.button,
    styles[`button${variant.charAt(0).toUpperCase()}${variant.slice(1)}`],
    styles[`button${size.charAt(0).toUpperCase()}${size.slice(1)}`]
  ].join(' ');

  return (
    <button className={className} {...props}>
      {children}
    </button>
  );
}
```

### B. Tailwind Config with Design Tokens

**`tailwind.config.js`:**
```javascript
const colors = require('tailwindcss/colors')

module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: 'var(--color-primary-50)',
          500: 'var(--color-primary-500)',
          600: 'var(--color-primary-600)',
          // ... etc
        }
      },
      spacing: {
        'xs': 'var(--spacing-xs)',
        'sm': 'var(--spacing-sm)',
        'md': 'var(--spacing-md)',
        // ... etc
      }
    }
  }
}
```

---

## Conclusion

This migration plan provides a structured, low-risk approach to modernizing the CSS architecture. By following the incremental rollout strategy (Option B), we can achieve:

- **73% bundle size reduction**
- **Improved maintainability**
- **Better developer experience**
- **Consistent design system**

The 7-week timeline is achievable with minimal risk, and the benefits will be immediate and long-lasting.

**Ready to start Phase 1?** Let's begin! 🚀
