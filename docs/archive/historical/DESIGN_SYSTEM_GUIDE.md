# PsychSync Design System Guide

**Version:** 1.0.0
**Last Updated:** 2025-01-09
**Status:** Active

---

## Overview

The PsychSync Design System provides a unified set of reusable components, design tokens, and guidelines to ensure consistency across the application. This guide explains how to use the design system effectively.

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Design Tokens](#design-tokens)
3. [Component Library](#component-library)
4. [Usage Patterns](#usage-patterns)
5. [Accessibility Guidelines](#accessibility-guidelines)
6. [Best Practices](#best-practices)

---

## Installation & Setup

### For New Components

```tsx
// Import design system components
import { Alert, Button, Card } from '@/components/ui';
import styles from './YourComponent.module.css';

// Use them in your component
export default function YourComponent() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Your Title</CardTitle>
        <CardDescription>Your description</CardDescription>
      </CardHeader>
      <CardContent>
        <Alert variant="info">Your message</Alert>
      </CardContent>
    </Card>
  );
}
```

---

## Design Tokens

Design tokens are the visual design atoms of the design system. They include colors, spacing, typography, and more.

### Color Tokens

```css
/* Primary Colors */
--color-primary-50: #eff6ff;
--color-primary-500: #3b82f6;
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;

/* Semantic Colors */
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #3b82f6;
```

**Usage:**
```tsx
// In CSS Modules
.myComponent {
  background-color: var(--color-primary-500);
  color: var(--color-primary-50);
}

// Or using Tailwind classes
<div className="bg-primary-500 text-primary-50">
```

### Spacing Tokens

```css
/* Spacing Scale (4px base unit) */
--spacing-xs: 0.25rem;    /* 4px */
--spacing-sm: 0.5rem;     /* 8px */
--spacing-md: 1rem;       /* 16px */
--spacing-lg: 1.5rem;     /* 24px */
--spacing-xl: 2rem;       /* 32px */
--spacing-2xl: 3rem;      /* 48px */
```

### Typography Scale

```css
--font-size-xs: 0.75rem;   /* 12px */
--font-size-sm: 0.875rem;  /* 14px */
--font-size-base: 1rem;    /* 16px */
--font-size-lg: 1.125rem;  /* 18px */
--font-size-xl: 1.25rem;   /* 20px */
--font-size-2xl: 1.5rem;   /* 24px */
--font-size-3xl: 1.875rem; /* 30px */
```

---

## Component Library

### Alert Component

The Alert component displays short, important messages in a way that attracts the user's attention without interrupting the user's task.

**Variants:** `info` | `success` | `warning` | `error`

#### Basic Usage

```tsx
import { Alert } from '@/components/ui';

<Alert variant="info">
  This is an informational message.
</Alert>
```

#### With Title

```tsx
<Alert variant="success" title="Success!">
  Your changes have been saved successfully.
</Alert>
```

#### Dismissible

```tsx
<Alert
  variant="warning"
  title="Warning"
  dismissible
  onDismiss={() => console.log('Dismissed')}
>
  Please review before proceeding.
</Alert>
```

#### Convenience Exports

```tsx
import { InfoAlert, SuccessAlert, WarningAlert, ErrorAlert } from '@/components/ui/Alert';

<SuccessAlert title="Done!">
  Operation completed successfully.
</SuccessAlert>

<ErrorAlert title="Error">
  Something went wrong. Please try again.
</ErrorAlert>
```

#### Accessibility Features

- ✅ Proper ARIA roles (`alert` or `status`)
- ✅ Appropriate `aria-live` regions (`assertive` for errors, `polite` for info)
- ✅ Semantic icons with `aria-hidden="true"`
- ✅ Keyboard-accessible dismiss button
- ✅ Screen reader-friendly labels

---

### Button Component

The Button component allows users to perform actions or navigate with a single click.

**Variants:** `default` | `outline` | `ghost` | `destructive`
**Sizes:** `small` | `medium` | `large`

#### Basic Usage

```tsx
import Button from '@/components/common/Button';

<Button variant="default">Click me</Button>
<Button variant="outline">Cancel</Button>
<Button variant="ghost">Learn more</Button>
```

#### With Icons

```tsx
<Button variant="default">
  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
  Add Item
</Button>
```

#### Disabled State

```tsx
<Button disabled>Cannot click</Button>
```

#### Loading State

```tsx
<Button isLoading>Loading...</Button>
```

---

### Card Component

Cards are used to group related concepts and tasks together.

#### Basic Structure

```tsx
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter
} from '@/components/ui';

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Additional context</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Main content goes here.</p>
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

#### Interactive Card

```tsx
<Card className="hover:shadow-lg transition-shadow cursor-pointer">
  <CardHeader>
    <CardTitle>Click me</CardTitle>
  </CardHeader>
  <CardContent>
    <p>This card is interactive</p>
  </CardContent>
</Card>
```

#### Custom Styling

```tsx
<Card className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
  <CardHeader>
    <CardTitle>Styled Card</CardTitle>
  </CardHeader>
</Card>
```

---

## Usage Patterns

### Form Layouts

```tsx
<Card>
  <CardHeader>
    <CardTitle>User Information</CardTitle>
  </CardHeader>
  <CardContent>
    <form className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Name
        </label>
        <input
          type="text"
          id="name"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
        />
      </div>
    </form>
  </CardContent>
  <CardFooter>
    <Button variant="outline" className="mr-2">Cancel</Button>
    <Button>Save</Button>
  </CardFooter>
</Card>
```

### Error Handling

```tsx
import { ErrorAlert } from '@/components/ui/Alert';

function MyComponent() {
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    try {
      await api.submit();
    } catch (err) {
      setError('Failed to submit. Please try again.');
    }
  };

  return (
    <div>
      {error && (
        <ErrorAlert
          title="Submission Error"
          dismissible
          onDismiss={() => setError(null)}
        >
          {error}
        </ErrorAlert>
      )}
      {/* Rest of component */}
    </div>
  );
}
```

### Loading States

```tsx
function DataList() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState([]);

  useEffect(() => {
    fetchData().then(result => {
      setData(result);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="flex justify-center p-8">Loading...</div>;
  }

  return <Card>{/* Data rendering */}</Card>;
}
```

---

## Accessibility Guidelines

### ARIA Labels

Always provide ARIA labels for icon-only buttons:

```tsx
// ❌ Bad - no label
<button>
  <svg>...</svg>
</button>

// ✅ Good - has aria-label
<button aria-label="Close">
  <svg>...</svg>
</button>

// ✅ Also Good - visible text + icon
<button>
  <svg className="w-4 h-4 mr-2">...</svg>
  Close
</button>
```

### Color Contrast

Ensure text meets WCAG AA standards:
- Normal text: 4.5:1 contrast ratio
- Large text (18pt+): 3:1 contrast ratio
- Interactive elements: 3:1 contrast ratio

Use the design tokens which already meet these standards.

### Keyboard Navigation

All interactive elements must be keyboard accessible:

```tsx
// ✅ Good - button is keyboard accessible by default
<button onClick={handleAction}>Action</button>

// ❌ Bad - div is not keyboard accessible
<div onClick={handleAction}>Action</div>

// ✅ Good - div made keyboard accessible
<div
  role="button"
  tabIndex={0}
  onClick={handleAction}
  onKeyDown={(e) => e.key === 'Enter' && handleAction()}
>
  Action
</div>
```

### Focus Indicators

Always provide visible focus indicators:

```css
/* In CSS Modules */
.myButton:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}
```

---

## Best Practices

### 1. Component Composition

Compose small, reusable components:

```tsx
// ✅ Good - composable
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>

// ❌ Bad - monolithic
<div className="bg-white rounded-xl border border-gray-200 p-4">
  <div className="mb-4 pb-4 border-b">
    <h3 className="text-lg font-semibold">Title</h3>
  </div>
  <div>Content</div>
</div>
```

### 2. Use CSS Modules for Component-Specific Styles

```tsx
// ✅ Good - scoped styles
import styles from './MyComponent.module.css';

<div className={styles.container}>

// ❌ Bad - global styles
<div className="my-custom-container">
```

### 3. Use Tailwind for Layout and Spacing

```tsx
// ✅ Good - Tailwind utilities
<div className="flex gap-4 p-4">

// ❌ Bad - custom CSS for simple layout
<div style={{ display: 'flex', gap: '16px', padding: '16px' }}>
```

### 4. Semantic HTML

```tsx
// ✅ Good - semantic
<nav>
  <ul>
    <li><a href="/home">Home</a></li>
  </ul>
</nav>

// ❌ Bad - non-semantic
<div className="navbar">
  <div className="nav-item" onClick={() => navigate('/home')}>
    Home
  </div>
</div>
```

### 5. Error Boundaries

Wrap components in error boundaries:

```tsx
<ErrorBoundary fallback={<ErrorAlert>Something went wrong</ErrorAlert>}>
  <MyComponent />
</ErrorBoundary>
```

---

## Migration Guide

### Migrating from Inline Styles

**Before:**
```tsx
<div
  style={{
    backgroundColor: '#3b82f6',
    padding: '1rem',
    borderRadius: '0.5rem'
  }}
>
  Content
</div>
```

**After:**
```tsx
<div className="bg-primary-500 p-4 rounded-md">
  Content
</div>
```

### Migrating from Custom CSS

**Before:**
```css
/* custom.css */
.my-card {
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

**After:**
```tsx
// Use Card component
<Card>Content</Card>

// Or CSS Module with Tailwind
/* MyComponent.module.css */
.card {
  @apply bg-white border border-gray-200 rounded-xl p-4 shadow-sm;
}
```

---

## Contributing to the Design System

### Adding New Components

1. Create component file: `src/components/ui/NewComponent.tsx`
2. Create CSS Module: `src/components/ui/NewComponent.module.css`
3. Add TypeScript interfaces for props
4. Include accessibility features (ARIA, keyboard nav)
5. Write usage examples
6. Update this documentation

### Component Checklist

- [ ] Follows naming conventions
- [ ] Has TypeScript types
- [ ] Includes accessibility attributes
- [ ] Supports keyboard navigation
- [ ] Has proper focus states
- [ ] Works in dark mode
- [ ] Responsive on mobile
- [ ] Documented with examples
- [ ] Tested with screen readers

---

## Resources

- **Component Examples:** See `frontend/src/stories/` for Storybook stories
- **Design Tokens:** `frontend/src/styles/global/variables.css`
- **Color Palette:** Figma design file
- **Accessibility:** WCAG 2.1 AA Guidelines
- **Tailwind Docs:** https://tailwindcss.com/docs

---

## Changelog

### v1.0.0 (2025-01-09)
- Initial release of unified design system
- Added Alert component with 4 variants
- Standardized Card component
- Created design token system
- Established accessibility guidelines
- Added comprehensive documentation

---

**Need Help?**
- Check the component examples in the codebase
- Review the accessibility guidelines
- Consult the Figma design file
- Ask the team in the #design-system channel
