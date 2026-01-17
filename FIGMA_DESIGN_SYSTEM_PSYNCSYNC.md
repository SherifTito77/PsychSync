# 🎨 PsychSync SaaS - Complete Figma Design System

**Version**: 1.0
**Last Updated**: 2025-01-16
**Designer**: Claude (Anthropic)
**Platform**: Web Application (Responsive)

---

## 📋 Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Design Tokens](#design-tokens)
3. [Color System](#color-system)
4. [Typography](#typography)
5. [Spacing & Layout](#spacing--layout)
6. [Component Library](#component-library)
7. [Page Layouts](#page-layouts)
8. [Interactive States](#interactive-states)
9. [Responsive Design](#responsive-design)
10. [Dark Mode](#dark-mode)
11. [Figma File Structure](#figma-file-structure)

---

## 🎯 Design Philosophy

PsychSync's design system balances **clinical professionalism** with **approachable warmth**, creating an environment that feels:

- **Trustworthy**: Clean, organized, reliable
- **Empathetic**: Warm, supportive, non-judgmental
- **Professional**: Polished, consistent, sophisticated
- **Accessible**: Clear, readable, usable by all
- **Scientific**: Data-driven, precise, evidence-based

### Core Principles

1. **Safety First**: Always prioritize user wellbeing (crisis resources prominent)
2. **Privacy Conscious**: Clear visual indicators of data security
3. **Clarity Over Cleverness**: Obvious is better than clever
4. **Emotional Hierarchy**: Critical alerts > Important warnings > Neutral info > Positive feedback
5. **Progressive Disclosure**: Show complexity only when needed

---

## 🎨 Design Tokens

### Color Tokens (CSS Variables)

```css
/* Primary Colors */
--primary-50: #EEF2FF;
--primary-100: #E0E7FF;
--primary-200: #C7D2FE;
--primary-300: #A5B4FC;
--primary-400: #818CF8;
--primary-500: #6366F1; /* Primary Brand Color */
--primary-600: #4F46E5;
--primary-700: #4338CA;
--primary-800: #3730A3;
--primary-900: #312E81;

/* Secondary Colors */
--secondary-50: #F0FDF4;
--secondary-100: #DCFCE7;
--secondary-200: #BBF7D0;
--secondary-300: #86EFAC;
--secondary-400: #4ADE80;
--secondary-500: #22C55E; /* Success/Positive */
--secondary-600: #16A34A;
--secondary-700: #15803D;
--secondary-800: #166534;
--secondary-900: #14532D;

/* Accent Colors */
--accent-purple: #8B5CF6;
--accent-pink: #EC4899;
--accent-orange: #F97316;
--accent-teal: #14B8A6;

/* Neutral Colors */
--neutral-50: #FAFAFA;
--neutral-100: #F5F5F5;
--neutral-200: #E5E5E5;
--neutral-300: #D4D4D4;
--neutral-400: #A3A3A3;
--neutral-500: #737373;
--neutral-600: #525252;
--neutral-700: #404040;
--neutral-800: #262626;
--neutral-900: #171717;

/* Semantic Colors */
--danger-50: #FEF2F2;
--danger-100: #FEE2E2;
--danger-500: #EF4444;
--danger-600: #DC2626;
--danger-700: #B91C1C;

--warning-50: #FFFBEB;
--warning-100: #FEF3C7;
--warning-500: #F59E0B;
--warning-600: #D97706;
--warning-700: #B45309;

--info-50: #EFF6FF;
--info-100: #DBEAFE;
--info-500: #3B82F6;
--info-600: #2563EB;
--info-700: #1D4ED8;

--success-50: #F0FDF4;
--success-100: #DCFCE7;
--success-500: #22C55E;
--success-600: #16A34A;
--success-700: #15803D;
```

### Typography Tokens

```css
/* Font Families */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
--text-5xl: 3rem;      /* 48px */

/* Font Weights */
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;

/* Line Heights */
--leading-tight: 1.25;
--leading-snug: 1.375;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
--leading-loose: 2;
```

### Spacing Tokens

```css
/* Spacing Scale (4px base unit) */
--spacing-0: 0;
--spacing-1: 0.25rem;  /* 4px */
--spacing-2: 0.5rem;   /* 8px */
--spacing-3: 0.75rem;  /* 12px */
--spacing-4: 1rem;     /* 16px */
--spacing-5: 1.25rem;  /* 20px */
--spacing-6: 1.5rem;   /* 24px */
--spacing-8: 2rem;     /* 32px */
--spacing-10: 2.5rem;  /* 40px */
--spacing-12: 3rem;    /* 48px */
--spacing-16: 4rem;    /* 64px */
--spacing-20: 5rem;    /* 80px */
--spacing-24: 6rem;    /* 96px */
```

### Border Radius

```css
--radius-none: 0;
--radius-sm: 0.125rem;   /* 2px */
--radius-base: 0.25rem;  /* 4px */
--radius-md: 0.375rem;   /* 6px */
--radius-lg: 0.5rem;     /* 8px */
--radius-xl: 0.75rem;    /* 12px */
--radius-2xl: 1rem;      /* 16px */
--radius-3xl: 1.5rem;    /* 24px */
--radius-full: 9999px;
```

### Shadows

```css
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
--shadow-base: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
--shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
--shadow-xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

---

## 🌈 Color System

### Primary Color Psychology
- **Primary (#6366F1)**: Trust, wisdom, calm (indigo)
- **Use Cases**: Primary buttons, links, active states, brand presence

### Secondary Color Psychology
- **Success (#22C55E)**: Growth, safety, positivity (green)
- **Use Cases**: Success messages, completed states, positive indicators

### Semantic Color Mapping

#### Success States
- High burnout recovery: `#22C55E`
- Low toxicity score: `#22C55E`
- Healthy team dynamics: `#22C55E`

#### Warning States
- Moderate burnout risk: `#F59E0B`
- Elevated toxicity: `#F59E0B`
- Declining trends: `#F59E0B`

#### Danger States
- Critical burnout risk: `#EF4444`
- High toxicity detected: `#EF4444`
- Crisis indicators: `#DC2626`

#### Info States
- Neutral information: `#3B82F6`
- System notifications: `#3B82F6`
- Help tooltips: `#2563EB`

### Gradient Definitions

```css
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--gradient-success: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
--gradient-warning: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%);
--gradient-danger: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%);
--gradient-dark: linear-gradient(135deg, #434343 0%, #000000 100%);
```

---

## ✍️ Typography

### Type Scale

| Token | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `--text-5xl` | 48px | 700 (bold) | 1.2 | Hero titles |
| `--text-4xl` | 36px | 700 (bold) | 1.2 | Page titles |
| `--text-3xl` | 30px | 600 (semibold) | 1.3 | Section headers |
| `--text-2xl` | 24px | 600 (semibold) | 1.4 | Card titles |
| `--text-xl` | 20px | 500 (medium) | 1.5 | Subsection headers |
| `--text-lg` | 18px | 400 (normal) | 1.5 | Lead paragraphs |
| `--text-base` | 16px | 400 (normal) | 1.6 | Body text |
| `--text-sm` | 14px | 400 (normal) | 1.5 | Secondary text |
| `--text-xs` | 12px | 500 (medium) | 1.4 | Labels, captions |

### Hierarchy Examples

#### Page Title
```
H1: Dashboard (36px, Bold, #171717)
    ↓
H2: Welcome back, Sarah (24px, Semibold, #404040)
    ↓
Body: Here's your team's wellness overview... (16px, Normal, #525252)
```

#### Card Title
```
H3: Burnout Risk Score (20px, Medium, #171717)
    ↓
Value: 78/100 (48px, Bold, #EF4444)
    ↓
Label: High Risk (14px, Semibold, #EF4444, Badge)
```

### Font Pairing

**Primary**: Inter (UI text, body content)
**Secondary**: JetBrains Mono (code, data, technical labels)

---

## 📐 Spacing & Layout

### Grid System

**Desktop**: 12-column grid, 80px max-content width, 24px gutters
**Tablet**: 8-column grid, 48px gutters
**Mobile**: 4-column grid, 16px gutters

### Container Widths

```css
--container-sm: 640px;   /* Mobile */
--container-md: 768px;   /* Tablet */
--container-lg: 1024px;  /* Desktop */
--container-xl: 1280px;  /* Wide Desktop */
--container-2xl: 1536px; /* Extra Wide */
```

### Standard Spacing Patterns

**Component Internal Padding**:
- Buttons: 12px (sm), 16px (md), 20px (lg)
- Cards: 16px (sm), 24px (md), 32px (lg)
- Inputs: 12px (sm), 16px (md)
- Modals: 24px all sides

**Layout Margins**:
- Section spacing: 64px (6rem)
- Card grid gaps: 24px (2rem)
- List item spacing: 16px (1rem)
- Form field spacing: 24px (1.5rem)

**Responsive Padding**:
- Mobile: 16px (1rem)
- Tablet: 24px (1.5rem)
- Desktop: 32px (2rem)

---

## 🧩 Component Library

### Buttons

#### Primary Button
```
Size: Medium (48px height)
Padding: 16px horizontal, 12px vertical
Background: #6366F1 (Primary-500)
Text: #FFFFFF, 500 (Medium), 16px
Radius: 8px (Radius-lg)
Shadow: 0 4px 6px rgba(99, 102, 241, 0.2)
Hover: #4F46E5 (Primary-600), -translateY(1px)
Active: #4338CA (Primary-700), 0 translateY
Disabled: #A5B4FC (Primary-300), cursor: not-allowed
```

#### Secondary Button
```
Size: Medium (48px height)
Padding: 16px horizontal, 12px vertical
Background: transparent
Border: 2px solid #6366F1 (Primary-500)
Text: #6366F1 (Primary-500), 500 (Medium), 16px
Radius: 8px (Radius-lg)
Hover: Background #EEF2FF (Primary-50)
```

#### Danger Button
```
Size: Medium
Padding: 16px horizontal, 12px vertical
Background: #EF4444 (Danger-500)
Text: #FFFFFF, 500 (Medium), 16px
Radius: 8px (Radius-lg)
Hover: #DC2626 (Danger-600)
```

#### Ghost Button
```
Size: Medium
Padding: 16px horizontal, 12px vertical
Background: transparent
Text: #525252 (Neutral-600), 500 (Medium), 16px
Hover: Background #F5F5F5 (Neutral-100)
```

#### Icon Button
```
Size: 40px × 40px (Square)
Background: transparent
Icon: 20px × 20px, #525252 (Neutral-600)
Radius: 8px (Radius-lg)
Hover: Background #F5F5F5 (Neutral-100), Icon #171717 (Neutral-900)
```

### Cards

#### Default Card
```
Background: #FFFFFF
Border: 1px solid #E5E5E5 (Neutral-200)
Radius: 12px (Radius-xl)
Shadow: 0 1px 3px rgba(0, 0, 0, 0.1)
Padding: 24px
Header: 20px bold, #171717, margin-bottom: 16px
Body: 16px normal, #525252, line-height: 1.6
```

#### Elevated Card
```
Background: #FFFFFF
Border: none
Radius: 16px (Radius-2xl)
Shadow: 0 10px 15px rgba(0, 0, 0, 0.1)
Padding: 32px
```

#### Interactive Card
```
Default: Same as Default Card
Hover: Shadow 0 20px 25px rgba(0, 0, 0, 0.1), -translateY(2px)
Transition: All 200ms ease
```

### Form Elements

#### Text Input
```
Height: 48px
Padding: 12px 16px
Background: #FFFFFF
Border: 2px solid #E5E5E5 (Neutral-200)
Radius: 8px (Radius-lg)
Text: 16px, #171717 (Neutral-900)
Placeholder: 16px, #A3A3A3 (Neutral-400)
Focus: Border #6366F1 (Primary-500), Ring 4px rgba(99, 102, 241, 0.1)
Error: Border #EF4444 (Danger-500)
```

#### Select Dropdown
```
Same as Text Input
Dropdown Arrow: Lucide icon, 20px, #525252
Dropdown Menu:
  Background: #FFFFFF
  Border: 1px solid #E5E5E5
  Shadow: 0 10px 15px rgba(0, 0, 0, 0.1)
  Option Height: 48px
  Option Padding: 12px 16px
  Option Hover: #EEF2FF (Primary-50)
```

#### Checkbox
```
Size: 20px × 20px
Border: 2px solid #D4D4D4 (Neutral-300)
Radius: 4px (Radius-base)
Unchecked: Background #FFFFFF, Border #D4D4D4
Checked: Background #6366F1 (Primary-500), Border #6366F1
Checkmark: White, 14px
Focus: Ring 4px rgba(99, 102, 241, 0.1)
```

#### Radio Button
```
Outer Circle: 20px diameter
Border: 2px solid #D4D4D4 (Neutral-300)
Unchecked: Background #FFFFFF
Checked: Background #6366F1 (Primary-500), Border #6366F1
Inner Dot: 8px diameter, #FFFFFF
Focus: Ring 4px rgba(99, 102, 241, 0.1)
```

### Alerts & Banners

#### Success Alert
```
Background: #F0FDF4 (Success-50)
Border: 1px solid #86EFAC (Success-300)
Border-Left: 4px solid #22C55E (Success-500)
Radius: 8px (Radius-lg)
Padding: 16px
Icon: CheckCircle, 24px, #16A34A (Success-600)
Text: 16px, #15803D (Success-700)
```

#### Warning Alert
```
Background: #FFFBEB (Warning-50)
Border: 1px solid #FDE68A (Warning-200)
Border-Left: 4px solid #F59E0B (Warning-500)
Radius: 8px (Radius-lg)
Padding: 16px
Icon: AlertTriangle, 24px, #D97706 (Warning-600)
Text: 16px, #B45309 (Warning-700)
```

#### Danger Alert
```
Background: #FEF2F2 (Danger-50)
Border: 1px solid #FCA5A5 (Danger-300)
Border-Left: 4px solid #EF4444 (Danger-500)
Radius: 8px (Radius-lg)
Padding: 16px
Icon: XCircle, 24px, #DC2626 (Danger-600)
Text: 16px, #B91C1C (Danger-700)
```

#### Info Alert
```
Background: #EFF6FF (Info-50)
Border: 1px solid #93C5FD (Info-300)
Border-Left: 4px solid #3B82F6 (Info-500)
Radius: 8px (Radius-lg)
Padding: 16px
Icon: Info, 24px, #2563EB (Info-600)
Text: 16px, #1D4ED8 (Info-700)
```

### Badges

#### Default Badge
```
Padding: 4px 12px
Background: #F5F5F5 (Neutral-100)
Text: 14px, 500 (Medium), #404040 (Neutral-700)
Radius: 9999px (Radius-full)
```

#### Primary Badge
```
Padding: 4px 12px
Background: #EEF2FF (Primary-50)
Text: 14px, 500 (Medium), #4338CA (Primary-700)
Radius: 9999px (Radius-full)
```

#### Success Badge
```
Padding: 4px 12px
Background: #DCFCE7 (Success-100)
Text: 14px, 500 (Medium), #15803D (Success-700)
Radius: 9999px (Radius-full)
```

#### Warning Badge
```
Padding: 4px 12px
Background: #FEF3C7 (Warning-100)
Text: 14px, 500 (Medium), #B45309 (Warning-700)
Radius: 9999px (Radius-full)
```

#### Danger Badge
```
Padding: 4px 12px
Background: #FEE2E2 (Danger-100)
Text: 14px, 500 (Medium), #B91C1C (Danger-700)
Radius: 9999px (Radius-full)
```

### Navigation

#### Sidebar (Desktop)
```
Width: 280px (Expanded), 80px (Collapsed)
Background: #FFFFFF
Border-Right: 1px solid #E5E5E5 (Neutral-200)
Header Height: 64px
Logo: 32px × 32px
Menu Item:
  Height: 48px
  Padding: 12px 16px
  Text: 16px, 500 (Medium), #525252 (Neutral-600)
  Icon: 24px × 24px
  Hover: Background #F5F5F5 (Neutral-100)
  Active: Background #EEF2FF (Primary-50), Text #4338CA (Primary-700)
```

#### Top Navigation
```
Height: 64px
Background: #FFFFFF
Border-Bottom: 1px solid #E5E5E5 (Neutral-200)
Padding: 0 24px
Logo: 32px × 32px
Nav Links:
  Padding: 12px 16px
  Text: 16px, 500 (Medium), #525252 (Neutral-600)
  Hover: Text #171717 (Neutral-900)
  Active: Text #6366F1 (Primary-500)
User Menu:
  Avatar: 40px × 40px, Circle
  Dropdown:
    Background: #FFFFFF
    Shadow: 0 10px 15px rgba(0, 0, 0, 0.1)
    Radius: 8px
```

### Data Visualization

#### Progress Bar
```
Height: 8px
Background: #E5E5E5 (Neutral-200)
Radius: 9999px (Radius-full)
Fill:
  Background: #6366F1 (Primary-500)
  Radius: 9999px
  Transition: Width 300ms ease
```

#### Score/Ring Chart
```
Size: 120px diameter
Stroke Width: 12px
Background Circle: #E5E5E5 (Neutral-200)
Progress Circle: #6366F1 (Primary-500)
Center Text: 36px bold, #171717
```

#### Heatmap Cell
```
Size: 40px × 40px
Radius: 4px (Radius-base)
Low Risk: #DCFCE7 (Success-100)
Medium Risk: #FEF3C7 (Warning-100)
High Risk: #FEE2E2 (Danger-100)
Critical: #FECACA (Danger-200)
Hover: +2px scale, 200ms ease
```

---

## 📄 Page Layouts

### Dashboard Layout

```
┌────────────────────────────────────────────────────────────┐
│  Sidebar (280px) │ Main Content Area                      │
│  ┌──────────────┐│ ┌────────────────────────────────────┐ │
│  │ Logo         ││ │ Top Bar (64px height)              │ │
│  │              ││ │ [Logo] [Search] [Notifications]    │ │
│  │ Navigation   ││ │        [User Avatar]               │ │
│  │ • Dashboard  ││ ├────────────────────────────────────┤ │
│  │ • Teams      ││ │ Page Content                       │ │
│  │ • Assessments││ │ ┌─────────┐ ┌─────────┐ ┌───────┐│ │
│  │ • Clinical   ││ │ │Stat Card│ │Stat Card│ │Stat   ││ │
│  │              ││ │ │         │ │         │ │Card   ││ │
│  │ [More...]    ││ │ └─────────┘ └─────────┘ └───────┘│ │
│  │              ││ │ ┌─────────────────────────────────┐│ │
│  │ Settings     ││ │ │ Main Content Section           ││ │
│  │              ││ │ │                                ││ │
│  └──────────────┘│ │ │                                ││ │
│                 ││ │                                ││ │
│  [Collapsible]  ││ └─────────────────────────────────┘│ │
└─────────────────┴─────────────────────────────────────────┘
```

### Assessment Page Layout

```
┌────────────────────────────────────────────────────────────┐
│                        Header                              │
│  ← Back    [Assessment Name]    Progress: 3/10 (30%)       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Question 3 of 10                                      │ │
│  │                                                        │ │
│  │ To what extent do you agree with the following:       │ │
│  │ "I feel overwhelmed by my responsibilities"            │ │
│  │                                                        │ │
│  │  ┌────┐   ┌────┐   ┌────┐   ┌────┐   ┌────┐        │ │
│  │  │ 1  │   │ 2  │   │ 3  │   │ 4  │   │ 5  │        │ │
│  │  │Strongly│     │     │     │  Strongly       │ │
│  │  │Disagree│     │     │     │  Agree         │ │
│  │  └────┘   └────┘   └────┘   └────┘   └────┘        │ │
│  │                                                        │ │
│  │  [Previous Question]  [Next Question →]               │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  [Progress Bar] ████████░░░░░░░░░░░░░░░░░░░░░░░░░         │
└────────────────────────────────────────────────────────────┘
```

### Results Page Layout

```
┌────────────────────────────────────────────────────────────┐
│  Header: "Your Results"                                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────┐  ┌────────────────────────────────┐ │
│  │ Overall Score    │  │ Detailed Breakdown              │ │
│  │                  │  │ ┌──────────────────────────────┐│ │
│  │        78        │  │ │ Openness:     ████████░░ 82% ││ │
│  │      /100        │  │ │ Conscientious: █████████░ 92% ││ │
│  │                  │  │ │ Extraversion: █████░░░░░ 45% ││ │
│  │  [Large Radial]  │  │ │ Agreeableness: ███████░░░ 72% ││ │
│  │                  │  │ │ Neuroticism:   ███░░░░░░░ 35% ││ │
│  └──────────────────┘  │ └──────────────────────────────┘│ │
│                         └────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Personality Type: INTJ-A (The Architect)             │ │
│  │                                                        │ │
│  │ "Strategic, independent, determined - you have a     │ │
│  │  natural ability to see the big picture..."          │ │
│  │                                                        │ │
│  │  [View Full Profile]  [Download PDF]  [Share]        │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## 🎭 Interactive States

### Button States
```
Default:  Base styles
Hover:     Darker background/lighter border, -translateY(1px), Shadow increases
Active:    Even darker, 0 translateY
Focus:     2px outline ring (Primary-500 with opacity)
Disabled:  Opacity 0.5, cursor: not-allowed, no hover effects
Loading:   Spinner (16px) replaces text, button remains clickable
```

### Input States
```
Default:  Border Neutral-200
Focus:    Border Primary-500, Ring 4px Primary-500 with opacity
Error:    Border Danger-500, Helper text "This field is required"
Success:  Border Success-500, Helper text with checkmark icon
Disabled: Background Neutral-100, Border Neutral-200, Text Neutral-400
```

### Card States
```
Default:  Base shadow, no transform
Hover:    Increased shadow (0 20px 25px), -translateY(2px)
Active:   Border Primary-500, Ring 2px Primary-500 with opacity
Disabled: Opacity 0.6, no pointer events
```

---

## 📱 Responsive Design

### Breakpoints

```css
--breakpoint-xs: 375px;   /* Small Mobile */
--breakpoint-sm: 640px;   /* Mobile */
--breakpoint-md: 768px;   /* Tablet */
--breakpoint-lg: 1024px;  /* Desktop */
--breakpoint-xl: 1280px;  /* Wide Desktop */
--breakpoint-2xl: 1536px; /* Extra Wide */
```

### Mobile Adaptations

**Sidebar**:
- Desktop: 280px wide, always visible
- Tablet: 80px collapsed, overlay on expand
- Mobile: Hidden, hamburger menu, full-screen drawer

**Cards**:
- Desktop: 3 columns (32px gaps)
- Tablet: 2 columns (24px gaps)
- Mobile: 1 column (16px gaps)

**Typography**:
- Desktop: 16px body, 36px headings
- Tablet: 16px body, 30px headings
- Mobile: 14px body, 24px headings

**Touch Targets**:
- Minimum: 44px × 44px (WCAG AA)
- Recommended: 48px × 48px

---

## 🌙 Dark Mode

### Color Overrides (Dark Mode)

```css
--bg-primary: #171717;      /* was #FFFFFF */
--bg-secondary: #262626;    /* was #F5F5F5 */
--bg-tertiary: #404040;     /* was #E5E5E5 */

--text-primary: #FAFAFA;    /* was #171717 */
--text-secondary: #A3A3A3;  /* was #525252 */
--text-tertiary: #737373;   /* was #A3A3A3 */

--border-color: #404040;    /* was #E5E5E5 */
```

### Dark Mode Components

**Cards**:
```
Background: #262626
Border: 1px solid #404040
Shadow: 0 4px 6px rgba(0, 0, 0, 0.3)
```

**Inputs**:
```
Background: #171717
Border: 1px solid #404040
Text: #FAFAFA
Focus: Border #818CF8 (Primary-400)
```

---

## 📁 Figma File Structure

### Pages (Frames)

```
📁 PsychSync Design System
├── 📁 00-Design Tokens
│   ├── 🎨 Colors
│   ├── ✍️ Typography
│   ├── 📐 Spacing
│   └── 🎭 Effects
├── 📁 01-Components
│   ├── 🔘 Buttons
│   ├── 📝 Forms
│   ├── 🃏 Cards
│   ├── 🏷️ Badges
│   ├── ⚠️ Alerts
│   ├── 📊 Data Visualization
│   └── 🧭 Navigation
├── 📁 02-Pages
│   ├── 📊 Dashboard
│   ├── 👥 Teams
│   ├── 🧠 Assessments
│   ├── 🏥 Clinical Screening
│   ├── 🔥 Burnout Prevention
│   ├── 🛡️ Toxic Behavior Detection
│   ├── 🔒 Anonymous Feedback
│   ├── 🧩 Multi-Framework Synthesis
│   └── ⚙️ Settings
├── 📁 03-Responsive
│   ├── 📱 Mobile (375px)
│   ├── 📱 Tablet (768px)
│   └── 💻 Desktop (1440px)
├── 📁 04-States
│   ├── 🌙 Dark Mode
│   ├── ⚡ Interactive States
│   └── ❌ Error States
└── 📁 05-Icons
    ├── 🎯 Lucide Icons
    └── ✨ Custom Icons
```

### Naming Convention

```
[Component]/[Variant]/[State]/[Size]

Examples:
• Button/Primary/Default/Medium
• Button/Danger/Hover/Large
• Card/Elevated/Active/Default
• Input/Text/Error/Full
• Alert/Success/Default/Default
```

### Component Structure (Figma)

```
Component Frame (Auto Layout)
├── Icon Layer (Optional)
├── Text Layer
└── Background Layer

Variants Property:
• State: Default, Hover, Active, Disabled, Focus, Error
• Size: XS, SM, MD, LG, XL
• Color: Primary, Secondary, Success, Warning, Danger
```

---

## 🎯 Design Deliverables

### 1. Component Library (Priority 1)
- ✅ All button variants
- ✅ All form inputs
- ✅ Card styles
- ✅ Navigation components
- ✅ Data visualization components

### 2. Page Templates (Priority 2)
- ✅ Dashboard
- ✅ Assessment flow
- ✅ Results page
- ✅ Settings page
- ✅ All 4 defensible IP feature pages

### 3. Responsive Mockups (Priority 3)
- ✅ Mobile (375px)
- ✅ Tablet (768px)
- ✅ Desktop (1440px)

### 4. Dark Mode (Priority 4)
- ✅ All components in dark mode
- ✅ All pages in dark mode

---

## 🚀 Implementation Guide

### Figma to React Mapping

```typescript
// Figma Component → React Component
<Button
  variant="primary"        // Figma Variant
  size="medium"           // Figma Size
  state="hover"           // Figma State
>
  Submit
</Button>

// CSS Variables → Design Tokens
const Button = styled.button<{ variant: Variant, size: Size }>`
  background: var(--${variant}-500);
  padding: var(--spacing-${size === 'medium' ? 4 : 6});
  border-radius: var(--radius-lg);
`;
```

### Export Settings

**Icons**:
- Format: SVG
- Scale: 1x
- Suffix: .svg

**Images**:
- Format: WebP (with PNG fallback)
- Scale: 1x, 2x (for retina)
- Quality: 85%

**Design Tokens**:
- Export as: JSON
- Include: Colors, typography, spacing, effects

---

## ✅ Quality Checklist

### Accessibility (WCAG 2.1 AA)
- ✅ Color contrast ratio ≥ 4.5:1 for normal text
- ✅ Color contrast ratio ≥ 3:1 for large text (18px+)
- ✅ Touch targets ≥ 44px × 44px
- ✅ Focus indicators visible on all interactive elements
- ✅ Form labels associated with inputs
- ✅ Alt text for all images
- ✅ Keyboard navigation support

### Design Consistency
- ✅ 4px spacing grid alignment
- ✅ Consistent border radius (4px, 8px, 12px, 16px)
- ✅ Consistent shadows (no custom shadows)
- ✅ Typography scale adherence
- ✅ Component state coverage

### Responsive Design
- ✅ All pages work on mobile (375px)
- ✅ All pages work on tablet (768px)
- ✅ All pages work on desktop (1440px)
- ✅ Touch targets appropriate for device
- ✅ Text is readable without zooming

---

## 📊 Asset Export

### Required Exports

1. **Logo**
   - Full color (horizontal): logo-horizontal.svg
   - Full color (icon): logo-icon.svg
   - Monochrome: logo-mono.svg

2. **Icons**
   - All Lucide icons as SVG
   - Custom icons as SVG
   - Organized by category

3. **Images**
   - Team avatars (placeholder)
   - Empty state illustrations
   - Error state illustrations

4. **Design Tokens**
   - JSON export of all tokens
   - CSS export of all tokens
   - iOS/Android exports if needed

---

## 🎓 Design Guidelines

### Do's

1. ✅ Use the 4px spacing grid
2. ✅ Maintain visual hierarchy with typography scale
3. ✅ Use semantic colors for meaning
4. ✅ Ensure 4.5:1 color contrast for accessibility
5. ✅ Design mobile-first
6. ✅ Test with real content
7. ✅ Consider loading and error states
8. ✅ Maintain consistent padding ratios

### Don'ts

1. ❌ Don't use arbitrary colors or spacing
2. ❌ Don't create one-off components
3. ❌ Don't ignore dark mode
4. ❌ Don't design without real content
5. ❌ Don't forget accessibility
6. ❌ Don't use < 12px font size
7. ❌ Don't make touch targets < 44px
8. ❌ Don't skip responsive breakpoints

---

## 📞 Support

For design questions or clarifications:
- Design System Version: 1.0
- Last Updated: 2025-01-16
- Maintained by: Design Team

---

**This design system is the foundation for all PsychSync UI/UX work. Any deviations must be approved and documented.**
