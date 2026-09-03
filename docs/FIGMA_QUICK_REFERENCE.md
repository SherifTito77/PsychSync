# 🎨 Figma Quick Reference - PsychSync

**Visual specifications for immediate use in Figma**

---

## 🎨 Complete Color Palette (Copy-Paste Ready)

### Primary Colors (Indigo)

```
#EEF2FF - Primary 50   (Light backgrounds)
#E0E7FF - Primary 100  (Subtle backgrounds)
#C7D2FE - Primary 200  (Hover backgrounds)
#A5B4FC - Primary 300  (Disabled)
#818CF8 - Primary 400  (Active states)
#6366F1 - Primary 500  ⭐ MAIN BRAND COLOR
#4F46E5 - Primary 600  (Hover)
#4338CA - Primary 700  (Active)
#3730A3 - Primary 800  (Dark backgrounds)
#312E81 - Primary 900  (Very dark backgrounds)
```

**Use Cases**:
- Primary buttons, links: `#6366F1`
- Active nav items: `#EEF2FF` (bg), `#4338CA` (text)
- Focus rings: `rgba(99, 102, 241, 0.2)`

### Semantic Colors

```
SUCCESS (Green):
#DCFCE7 - Success 100  (Light bg)
#86EFAC - Success 300  (Border)
#22C55E - Success 500  ⭐ Main
#16A34A - Success 600  (Hover)
#15803D - Success 700  (Text)

WARNING (Amber):
#FEF3C7 - Warning 100  (Light bg)
#FDE68A - Warning 200  (Border)
#F59E0B - Warning 500  ⭐ Main
#D97706 - Warning 600  (Hover)
#B45309 - Warning 700  (Text)

DANGER (Red):
#FEE2E2 - Danger 100   (Light bg)
#FCA5A5 - Danger 300   (Border)
#EF4444 - Danger 500   ⭐ Main
#DC2626 - Danger 600   (Hover)
#B91C1C - Danger 700   (Text)

INFO (Blue):
#DBEAFE - Info 100     (Light bg)
#93C5FD - Info 300     (Border)
#3B82F6 - Info 500     ⭐ Main
#2563EB - Info 600     (Hover)
#1D4ED8 - Info 700     (Text)
```

### Neutral Colors (Grayscale)

```
#FAFAFA - Neutral 50    (Page background)
#F5F5F5 - Neutral 100   (Section background)
#E5E5E5 - Neutral 200   (Borders) ⭐
#D4D4D4 - Neutral 300   (Disabled borders)
#A3A3A3 - Neutral 400   (Placeholders)
#737373 - Neutral 500   (Secondary text)
#525252 - Neutral 600   (Body text) ⭐
#404040 - Neutral 700   (Subheadings)
#262626 - Neutral 800   (Headings)
#171717 - Neutral 900   (Main headings) ⭐
```

**Common Text/Background Combinations**:
```
White background (#FFFFFF) + Dark text (#171717)
Light gray background (#F5F5F5) + Medium text (#525252)
Primary background (#EEF2FF) + Primary text (#4338CA)
Success background (#DCFCE7) + Success text (#15803D)
```

---

## 📐 Standard Component Dimensions

### Buttons

```
SIZE CHART (Width × Height):

┌─────────────────────────────────┐
│ Size    │ Width  │ Height │ Icon │
├─────────────────────────────────┤
│ XS      │ Auto   │ 32px   │ 14px │
│ SM      │ Auto   │ 40px   │ 16px │
│ MD      │ Auto   │ 48px   │ 20px │ ⭐ Default
│ LG      │ Auto   │ 56px   │ 20px │
│ XL      │ Auto   │ 64px   │ 24px │
└─────────────────────────────────┘

PADDING (Horizontal):
  XS: 8px (12px total)
  SM: 12px (24px total)
  MD: 16px (32px total) ⭐
  LG: 20px (40px total)
  XL: 24px (48px total)

BORDER RADIUS: 8px (all sizes)
```

### Form Inputs

```
TEXT INPUT:
┌──────────────────────────────────────┐
│ Height: 48px                         │
│ Padding: 12px (left/right)           │
│ Border: 2px                          │
│ Radius: 8px                          │
│ Font: 16px                           │
│                                      │
│ Placeholder: #A3A3A3 (Neutral-400)   │
│ Default text: #171717 (Neutral-900)  │
│ Border default: #E5E5E5 (Neutral-200)│
│ Border focus: #6366F1 (Primary-500) │
└──────────────────────────────────────┘

CHECKBOX:
┌──────┐
│ 20px │ Size
│ 4px  │ Border
│ 4px  │ Radius
└──────┘

RADIO BUTTON:
┌────────┐
│ 20px   │ Outer diameter
│ 8px    │ Inner dot (when checked)
│ 2px    │ Border
└────────┘
```

### Cards

```
CARD DIMENSIONS:

┌────────────────────────────────────────────┐
│ Type          │ Size        │ Padding      │
├────────────────────────────────────────────┤
│ Compact       │ 288px wide  │ 16px         │
│ Default       │ 384px wide  │ 24px ⭐      │
│ Large         │ 480px wide  │ 32px         │
│ Full-Width    │ 100%        │ 24px         │
└────────────────────────────────────────────┘

BORDER RADIUS:
  Default: 12px (Card / Default)
  Elevated: 16px (Card / Elevated)
  Flat: 8px (Minimal)

SHADOW:
  Default: 0 1px 3px rgba(0, 0, 0, 0.1)
  Elevated: 0 10px 15px rgba(0, 0, 0, 0.1)
  Hover: 0 20px 25px rgba(0, 0, 0, 0.1)
```

### Badges

```
BADGE DIMENSIONS:
  Height: 28px
  Padding: 4px horizontal (auto width)
  Radius: 9999px (fully rounded)
  Font: 12px, Medium
```

---

## 📏 Layout Spacing Guide

### Grid System

```
DESKTOP (1440px canvas):
┌─────────────────────────────────────────────────────────┐
│ Sidebar │  Content Area                                 │
│ 280px   │  1160px (12 columns × 80px + 11 gutters)    │
└─────────────────────────────────────────────────────────┘

COLUMN CONFIGURATION:
  Columns: 12
  Max content width: 80px per column
  Gutter: 24px between columns
  Margins: 32px on sides

TABLET (768px canvas):
┌─────────────────────────────────────────────────┐
│ Sidebar │  Content                              │
│ 80px    │  8 columns × 80px + 7 gutters        │
└─────────────────────────────────────────────────┘

MOBILE (375px canvas):
┌──────────────────────────────┐
│ Content (4 columns × 80px)  │
│ Bottom Nav (64px height)    │
└──────────────────────────────┘
```

### Common Spacing Patterns

```
COMPONENT INTERNAL SPACING:
  Button padding: 12px (md), 16px (lg)
  Card padding: 16px (sm), 24px (md), 32px (lg)
  Input padding: 12px (all sizes)
  Modal padding: 24px (all sides)

LAYOUT SPACING:
  Section margins: 64px (6rem)
  Card grid gaps: 24px (2rem)
  List item spacing: 16px (1rem)
  Form field spacing: 24px (1.5rem)
  Table cell padding: 12px (8px vertically)

RESPONSIVE PADDING:
  Mobile: 16px (1rem)
  Tablet: 24px (1.5rem)
  Desktop: 32px (2rem)
```

---

## 🖼️ Page Layout Templates

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  [Sidebar 280px] │  [Main Content Area 1160px]                │
│  ┌────────────┐ │  ┌────────────────────────────────────────┐ │
│  │ Logo 64px  │ │  │ Top Bar 64px height                    │ │
│  └────────────┘ │  │ [Logo] [Search 320px] [...] [Avatar]   │ │
│  ┌────────────┐ │  ├────────────────────────────────────────┤ │
│  │ Navigation │ │  │ Page Content Padding: 32px             │ │
│  │            │ │  │                                         │ │
│  │ • Dashboard│ │  │ Page Header (80px height)              │ │
│  │ • Teams    │ │  │ ┌─────────────────────────────────┐   │ │
│  │ • Assess   │ │  │ │ Title: "Dashboard" (36px, Bold)  │   │ │
│  │ • Clinical │ │  │ │ Subtitle (16px, Regular)         │   │ │
│  │ • [etc.]   │ │  │ └─────────────────────────────────┘   │ │
│  │            │ │  │                                         │ │
│  └────────────┘ │  │ Section Spacing: 64px                  │ │
│  ┌────────────┐ │  │                                         │ │
│  │ Settings   │ │  │ Stats Row (3 cards, 24px gap):         │ │
│  │            │ │  │ ┌──────┐ ┌──────┐ ┌──────┐            │ │
│  └────────────┘ │  │ │Card 1│ │Card 2│ │Card 3│            │ │
│                 │  │ └──────┘ └──────┘ └──────┘            │ │
│  [Expand/Collapse]│  │                                         │ │
└───────────────────┴─────────────────────────────────────────┘
```

### Assessment Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  [Sidebar + Top Bar - Same as Dashboard]                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Centered Content (800px max width)                    │    │
│  │                                                         │    │
│  │  Progress Bar (8px height, 100% width)                 │    │
│  │  ████████░░░░░░░░░░░░░░░░░░░░░░░ 30%                    │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐  │    │
│  │  │ Question Card (Padding: 48px)                   │  │    │
│  │  │                                                 │  │    │
│  │  │  Header: "Question 3 of 10" (16px, Medium)     │  │    │
│  │  │  Question Text (24px, Semibold, 36px leading)  │  │    │
│  │  │  Description (16px, Regular, 24px leading)      │  │    │
│  │  │                                                 │  │    │
│  │  │  Response Options (Vertical, 16px gap):        │  │    │
│  │  │  ┌───────────────────────────────────────┐    │  │    │
│  │  │  │ ○ Strongly Disagree    (64px height)  │    │  │    │
│  │  │  └───────────────────────────────────────┘    │  │    │
│  │  │  ┌───────────────────────────────────────┐    │  │    │
│  │  │  │ ○ Disagree                           │    │  │    │
│  │  │  └───────────────────────────────────────┘    │  │    │
│  │  │  [... 5 options total ...]                  │  │    │
│  │  │                                                 │  │    │
│  │  └─────────────────────────────────────────────────┘  │    │
│  │                                                         │    │
│  │  Navigation Buttons (Flex, Space Between):            │    │
│  │  [← Previous]  [Next →]                                │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Full Page Template (All Features)

```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 SEARCH: Type to search any page, component, or token       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 PAGES                                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Desktop (1440px)                                        │    │
│  │  ├─ Dashboard / Desktop                                  │    │
│  │  ├─ Teams / Desktop                                      │    │
│  │  ├─ Assessments / Desktop                                 │    │
│  │  ├─ Clinical Screening / Desktop                          │    │
│  │  ├─ Toxic Behavior Detection / Desktop                    │    │
│  │  ├─ Burnout Prevention / Desktop                          │    │
│  │  ├─ Anonymous Feedback / Desktop                          │    │
│  │  ├─ Behavioral Analytics / Desktop                        │    │
│  │  ├─ Multi-Framework Synthesis / Desktop                   │    │
│  │  └─ Settings / Desktop                                    │    │
│  │                                                          │    │
│  │  Tablet (768px)                                          │    │
│  │  └─ [Same pages, 768px width]                            │    │
│  │                                                          │    │
│  │  Mobile (375px)                                          │    │
│  │  └─ [Same pages, 375px width, bottom nav]                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  🧩 COMPONENTS                                                   │
│  ├─ Buttons / All Variants                                      │
│  ├─ Forms / All Inputs                                          │
│  ├─ Cards / All Styles                                          │
│  ├─ Badges / All Colors                                         │
│  ├─ Alerts / All Types                                          │
│  ├─ Navigation / Sidebar, Top Bar, Bottom Nav                  │
│  └─ Data Viz / Progress Bars, Charts, Score Rings              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Component State Matrix

### Button States

```
STATE MATRIX:

┌─────────────┬──────────────┬──────────┬─────────────┬──────────┐
│ Button Type │ Default      │ Hover    │ Active      │ Disabled │
├─────────────┼──────────────┼──────────┼─────────────┼──────────┤
│ Primary     │ #6366F1 bg   │ #4F46E5  │ #4338CA     │ 50% op.  │
│             │ #FFFFFF text │          │ +translateY │          │
├─────────────┼──────────────┼──────────┼─────────────┼──────────┤
│ Secondary   │ Transparent  │ #EEF2FF  │ #E0E7FF     │ 50% op.  │
│             │ #6366F1 text │ bg       │ bg          │          │
│             │ 2px border   │          │             │          │
├─────────────┼──────────────┼──────────┼─────────────┼──────────┤
│ Danger      │ #EF4444 bg   │ #DC2626  │ #B91C1C     │ 50% op.  │
│             │ #FFFFFF text │          │ +translateY │          │
├─────────────┼──────────────┼──────────┼─────────────┼──────────┤
│ Ghost       │ Transparent  │ #F5F5F5  │ #E5E5E5     │ 50% op.  │
│             │ #525252 text │ bg       │ bg          │          │
└─────────────┴──────────────┴──────────┴─────────────┴──────────┘

TRANSITIONS: All 200ms ease, except -translateY (150ms ease-out)
```

### Input States

```
INPUT STATE MATRIX:

┌─────────────┬─────────────┬──────────┬──────────┬──────────────┐
│ Input Type  │ Default     │ Focus    │ Error     │ Disabled     │
├─────────────┼─────────────┼──────────┼──────────┼──────────────┤
│ Text Input  │ 2px border  │ 2px border│ 2px border│ 50% opacity │
│             │ #E5E5E5      │ #6366F1  │ #EF4444  │ + gray bg   │
│             │ #FFFFFF bg   │ +ring    │ +helper  │              │
├─────────────┼─────────────┼──────────┼──────────┼──────────────┤
│ Checkbox    │ 2px border  │ 4px ring │ 2px border│ 40% opacity │
│ Unchecked   │ #D4D4D4      │ #6366F1  │ #EF4444  │              │
│             │ #FFFFFF bg   │          │          │              │
├─────────────┼─────────────┼──────────┼──────────┼──────────────┤
│ Checkbox    │ #6366F1 bg   │ +scale   │ N/A      │ 40% opacity │
│ Checked     │ +checkmark   │ 1.05     │          │              │
├─────────────┼─────────────┼──────────┼──────────┼──────────────┤
│ Radio       │ 2px border  │ 4px ring │ 2px border│ 40% opacity │
│ Unchecked   │ #D4D4D4      │ #6366F1  │ #EF4444  │              │
│             │ #FFFFFF bg   │          │          │              │
├─────────────┼─────────────┼──────────┼──────────┼──────────────┤
│ Radio       │ #6366F1 bg   │ +scale   │ N/A      │ 40% opacity │
│ Checked     │ +dot 8px     │ 1.05     │          │              │
└─────────────┴─────────────┴──────────┴──────────┴──────────────┘

FOCUS RING: 4px rgba(99, 102, 241, 0.1) - always outer
```

---

## 🎨 Gradient Collection

```
PRIMARY GRADIENT:
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

SUCCESS GRADIENT:
background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);

WARNING GRADIENT:
background: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%);

DANGER GRADIENT:
background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%);

DARK GRADIENT:
background: linear-gradient(135deg, #434343 0%, #000000 100%);

SUBTLE GRADIENT (for cards):
background: linear-gradient(180deg, #FFFFFF 0%, #FAFAFA 100%);
```

---

## 📱 Responsive Breakpoints

```
BREAKPOINT SCALE (Figma Frames):

┌───────────────────┬──────────┬────────────┬──────────────┐
│ Breakpoint        │ Width    │ Container  │ Grid Columns │
├───────────────────┼──────────┼────────────┼──────────────┤
│ Mobile (XS)       │ 375px    │ 100%       │ 4 columns    │
│ Mobile (SM)       │ 640px    │ 640px      │ 4 columns    │
│ Tablet (MD)       │ 768px    │ 720px      │ 8 columns    │
│ Desktop (LG)      │ 1024px   │ 960px      │ 12 columns   │
│ Desktop (XL)      │ 1280px   │ 1200px     │ 12 columns   │
│ Desktop (2XL)     │ 1536px   │ 1280px     │ 12 columns   │
└───────────────────┴──────────┴────────────┴──────────────┘

RESPONSIVE ADAPTATIONS:

Sidebar:
  Desktop (1024+): 280px expanded
  Tablet (768-1023): 80px collapsed (icons only)
  Mobile (<768): Hidden, hamburger drawer

Navigation:
  Desktop: Top sidebar navigation
  Tablet: Icon-only sidebar
  Mobile: Bottom tab bar (64px height)

Grid:
  Desktop: 3 columns → 2 columns → 1 column
  Tablet: 2 columns → 1 column
  Mobile: Always 1 column

Typography:
  Desktop: 36px headings, 16px body
  Tablet: 30px headings, 16px body
  Mobile: 24px headings, 14px body
```

---

## ✅ Quick QA Checklist

### Color Contrast (WCAG AA)

```
✓ All text ≥ 4.5:1 contrast ratio
✓ Large text (18px+) ≥ 3:1 contrast ratio
✓ Icons and graphical elements ≥ 3:1

Examples that PASS:
  #FFFFFF on #6366F1 = 4.6:1 ✓
  #171717 on #FFFFFF = 16.1:1 ✓
  #525252 on #FAFAFA = 7.5:1 ✓
  #4338CA on #EEF2FF = 8.2:1 ✓

Examples that FAIL:
  #A3A3A3 on #F5F5F5 = 2.8:1 ✗
  #737373 on #FAFAFA = 4.4:1 ✗ (borderline)

Solution: Use darker text #525252 or lighter background #FFFFFF
```

### Touch Targets

```
✓ All buttons ≥ 44px × 44px (WCAG AAA)
✓ All links ≥ 44px × 44px (or in padding)
✓ All form inputs ≥ 48px height

Minimum sizes:
  Button: 48px height ✓
  Checkbox: 20px ✓ (but with 24px+ padding in label)
  Radio: 20px ✓ (but with 24px+ padding in label)
  Link: Text with padding (tap area = 44px+)
```

### Component Coverage

```
✓ All components have:
  - Default state
  - Hover state
  - Focus state
  - Active state (if applicable)
  - Disabled state
  - Error state (if applicable)

✓ All pages have:
  - Loading state
  - Empty state
  - Error state
  - Success state (if applicable)
```

---

## 🚀 Figma Keyboard Shortcuts

```
Essential Shortcuts:

Frame/Artboard:
  Ctrl + R         → Rectangle tool (create frame)
  F                → Frame tool
  Alt + Drag       → Duplicate

Selection:
  Ctrl + A         → Select all
  Ctrl + D         → Deselect
  Shift + Click    → Multi-select

Editing:
  Ctrl + T         → Text tool
  Ctrl + K         → Insert link
  Ctrl + /         → Comment

View:
  Ctrl + 1         → Zoom to 100%
  Ctrl + 2         → Zoom to 200%
  Ctrl + 0         → Fit to screen
  Z + Drag         → Zoom tool

Align:
  Ctrl + Alt + K   → Alignment options
  Ctrl + Alt + H   → Horizontal center
  Ctrl + Alt + V   → Vertical center

Components:
  Ctrl + Alt + O   → Create component
  Ctrl + Alt + B   → Create instance
```

---

## 📋 Copy-Paste Component Specs

### Primary Button (Default)

```
FRAME:
  Width: Auto (hug contents)
  Height: 48px
  Fill: #6366F1 (Primary-500)
  Stroke: None
  Radius: 8px
  Shadow: 0 4px 6px rgba(99, 102, 241, 0.2)

TEXT LAYER:
  Content: "Button Label"
  Font: Inter
  Weight: Medium (500)
  Size: 16px
  Color: #FFFFFF
  Alignment: Center, Middle

PADDING:
  Top: 12px
  Bottom: 12px
  Left: 16px
  Right: 16px

AUTO LAYOUT:
  Horizontal: 16px gap
  Vertical: Canvas
  Padding: 12, 16, 12, 16
```

### Text Input (Default)

```
FRAME:
  Width: 320px (adjustable)
  Height: 48px
  Fill: #FFFFFF
  Stroke: 2px, #E5E5E5 (Neutral-200)
  Radius: 8px
  Shadow: None

PLACEHOLDER TEXT:
  Content: "Enter text..."
  Font: Inter
  Weight: Regular (400)
  Size: 16px
  Color: #A3A3A3 (Neutral-400)

INPUT TEXT:
  Same as placeholder, but color: #171717 (Neutral-900)

FOCUS STATE:
  Stroke: 2px, #6366F1 (Primary-500)
  Effect: Drop Shadow
    - Color: #6366F1
    - Opacity: 20%
    - Radius: 4px
    - Offset: 0, 0

PADDING:
  All sides: 12px
```

### Card (Default)

```
FRAME:
  Width: 384px (adjustable)
  Height: Auto
  Fill: #FFFFFF
  Stroke: 1px, #E5E5E5 (Neutral-200)
  Radius: 12px
  Shadow: 0 1px 3px rgba(0, 0, 0, 0.1)

PADDING:
  All sides: 24px

AUTO LAYOUT:
  Vertical spacing: 16px between elements

HEADER TEXT:
  Content: "Card Title"
  Font: Inter
  Weight: Semibold (600)
  Size: 20px
  Color: #171717 (Neutral-900)
  Margin bottom: 16px

BODY TEXT:
  Content: "Card body text goes here..."
  Font: Inter
  Weight: Regular (400)
  Size: 16px
  Color: #525252 (Neutral-600)
  Line height: 150%
```

---

**🎨 Now you're ready to design in Figma!**

Copy these specifications directly into Figma to build your PsychSync design system.
