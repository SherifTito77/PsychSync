# PsychSync Figma Frame Structure
## Ready-to-Use Setup Instructions

**Created:** January 2026
**Figma Version Compatible:** All current versions

---

## 📐 Frame Setup Structure

### 1. Desktop Frames (Create in this order)

```
📁 PsychSync Web App
├── 📄 Desktop - Dashboard (1440 × 900)
├── 📄 Desktop - Dashboard - Sidebar Collapsed (1440 × 900)
├── 📄 Desktop - Teams Page (1440 × 900)
├── 📄 Desktop - Clinical Screening (1440 × 900)
├── 📄 Desktop - HRIS Analytics (1440 × 900)
└── 📄 Desktop - Settings (1440 × 900)
```

### Frame Dimensions

#### Primary Frame: Desktop
```
Width: 1440px
Height: 900px
Fill: #FAFAFA
```

#### Sidebar Frame (inside each desktop frame)
```
Width: 280px (expanded)
Width: 70px (collapsed)
Height: 900px
Fill: #111827
Position: Fixed (X: 0, Y: 0)
```

#### Main Content Frame
```
Width: 1160px (1440 - 280)
Height: 900px
X: 280px (when sidebar expanded)
X: 70px (when sidebar collapsed)
Y: 0
```

---

## 🎨 Component Layer Structure

### Sidebar Components (Master Component)

```
📁 Sidebar / Expanded
├── 🟦 Background (Rectangle)
│   ├── Width: 280px
│   ├── Height: 900px
│   └── Fill: #111827
│
├── 📝 Header Group
│   ├── Logo Text
│   │   ├── Font: Inter/Bold/20px
│   │   ├── Content: "🧠 PsychSync"
│   │   └── Color: #818CF8
│   │
│   └── Toggle Button
│       ├── Width: 24px
│       ├── Height: 24px
│       ├── Icon: 16px × 16px SVG
│       └── Hover: #374151
│
├── 📍 Navigation Items
│   ├── 📁 Section: Core
│   │   ├── Section Title
│   │   │   ├── Font: Inter/Semibold/11px
│   │   │   ├── Text: "CORE"
│   │   │   ├── Color: #6B7280
│   │   │   └── Padding: 16px 16px 8px
│   │   │
│   │   ├── Nav Item: Dashboard [ACTIVE]
│   │   ├── Nav Item: Icon Gallery
│   │   ├── Nav Item: Teams
│   │   ├── Nav Item: Toxic Behavior
│   │   ├── Nav Item: Burnout
│   │   ├── Nav Item: Anonymous Feedback
│   │   ├── Nav Item: Behavioral Analytics
│   │   ├── Nav Item: Multi-Framework
│   │   ├── Nav Item: Legal Rights
│   │   ├── Nav Item: Equity Dashboard
│   │   └── Nav Item: Settings
│   │
│   ├── 📁 Section: Monitoring
│   │   ├── Section Title
│   │   │
│   │   ├── Collapsible Section: Email Monitoring
│   │   │   ├── Section Header
│   │   │   │   ├── Background: Transparent
│   │   │   │   ├── Border-left: 3px solid #818CF8
│   │   │   │   ├── Icon: 📧 (20px, #818CF8)
│   │   │   │   ├── Text: "Email Monitoring"
│   │   │   │   └── Chevron: ▼
│   │   │   │
│   │   │   └── Submenu (Hidden by default)
│   │   │       ├── Background: #1F2937
│   │   │       ├── Border-left: 3px solid #818CF8
│   │   │       ├── Submenu Item: Scheduled Reports
│   │   │       ├── Submenu Item: Anomaly Detection
│   │   │       ├── Submenu Item: Team Dashboard
│   │   │       └── Submenu Item: Sentiment Analysis
│   │   │
│   │   └── Collapsible Section: HRIS Analytics
│   │       ├── Section Header
│   │       └── Submenu (9 items)
│   │
│   ├── 📁 Section: Clinical
│   │   ├── Section Title
│   │   │
│   │   └── Collapsible Section: Clinical Screening
│   │       ├── Section Header
│   │       └── Submenu (22 items)
│   │
│   ├── 📁 Section: Services
│   │   ├── Collapsible Section: Clinical Services
│   │   │   └── Submenu (12 items)
│   │   │
│   │   └── Collapsible Section: Services & Connectors
│   │       └── Submenu (7 items)
│   │
│   └── 📁 Section: Analytics
│       └── Collapsible Section: Analytics & AI
│           └── Submenu (6 items)
│
└── 🔒 Public Access Section
    ├── Section Title
    ├── Nav Item: Anonymous Feedback
    └── Nav Item: Check Status
```

---

## 🧩 Master Component List

### Create these as Figma Components (⌘⌥K)

#### 1. Sidebar Components

**Component: Sidebar / Expanded**
```
Width: 280px
Height: Auto (min 900px)
Auto-layout: Vertical, Top, Gap: 0
```

**Component: Sidebar / Collapsed**
```
Width: 70px
Auto-layout: Vertical, Top, Gap: 0
Instance of: Sidebar / Expanded
Override: Hide text layers
```

#### 2. Navigation Components

**Component: Nav Item / Default**
```
Auto-layout: Horizontal, Center, Gap: 12px
Padding: 12px 16px
Height: 48px
├── Icon (20px)
└── Text (14px, Medium, #D1D5DB)
```

**Component: Nav Item / Active**
```
Instance of: Nav Item / Default
Overrides:
├── Fill: #374151
├── Text Color: #FFFFFF
└── Stroke: Left, 3px, #6366F1
```

**Component: Nav Item / Hover**
```
Instance of: Nav Item / Default
Override:
├── Fill: #374151
└── Text Color: #FFFFFF
```

#### 3. Section Components

**Component: Section Header / Collapsed**
```
Auto-layout: Horizontal, Center, Gap: 12px
Padding: 12px 16px
Height: 48px
Stroke: Left, 3px, (varies by section)
├── Icon (20px, colored)
├── Text (14px, Medium, #D1D5DB)
└── Chevron (12px, #9CA3AF)
```

**Component: Section Header / Expanded**
```
Instance of: Section Header / Collapsed
Override:
├── Chevron Rotation: 180deg
└── Fill: #374151
```

#### 4. Submenu Components

**Component: Submenu / Clinical**
```
Auto-layout: Vertical, Top, Gap: 0
Fill: #1F2937
Stroke: Left, 3px, #10B981
Padding: 0
Overflow: Hidden (for prototype)
```

**Component: Submenu Item**
```
Auto-layout: Horizontal vertical, Top, Gap: 8px
Padding: 10px 16px
Min-height: 60px
├── Icon (16px)
└── Text Group (Auto-layout: Vertical, Top, Gap: 2px)
    ├── Title (13px, Regular, #9CA3AF)
    └── Description (11px, Regular, #6B7280)
```

**Component: Submenu Item / Active**
```
Instance of: Submenu Item
Overrides:
├── Fill: #374151
└── Text Colors: #FFFFFF
```

#### 5. Button Components

**Component: Button / Primary**
```
Auto-layout: Horizontal, Center, Gap: 0
Padding: 12px 24px
Height: 48px
Fill: #6366F1
Radius: 8px
Shadow: 0 4px 6px rgba(99, 102, 241, 0.2)
Content: Text (16px, Medium, #FFFFFF)
```

**Component: Button / Primary / Hover**
```
Instance of: Button / Primary
Override: Fill: #4F46E5
```

**Component: Button / Secondary**
```
Auto-layout: Horizontal, Center, Gap: 0
Padding: 12px 24px
Height: 48px
Fill: #FFFFFF
Stroke: 2px, #6366F1
Radius: 8px
Content: Text (16px, Medium, #6366F1)
```

#### 6. Card Components

**Component: Card / Base**
```
Auto-layout: Vertical, Top, Gap: 0
Padding: 24px
Fill: #FFFFFF
Stroke: 1px, #E5E7EB
Radius: 12px
Shadow: 0 1px 3px rgba(0, 0, 0, 0.1)
└── [Content Slot]
```

**Component: Card / Stat**
```
Instance of: Card / Base
Content:
├── Stat Title (14px, #6B7280)
├── Stat Value (32px, Bold, #111827)
└── Stat Change (14px, Medium, #10B981)
```

#### 7. Form Components

**Component: Input / Default**
```
Auto-layout: Horizontal, Center, Gap: 0
Padding: 0 16px
Height: 48px
Width: Fill container
Fill: #FFFFFF
Stroke: 1px, #E5E7EB
Radius: 8px
Placeholder: Text (14px, #9CA3AF)
```

**Component: Input / Focus**
```
Instance of: Input / Default
Overrides:
├── Stroke: 2px, #6366F1
└── Shadow: 0 0 0 3px rgba(99, 102, 241, 0.1)
```

**Component: Textarea**
```
Instance of: Input / Default
Override: Min-height: 120px, Padding: 12px 16px
```

#### 8. Badge Components

**Component: Badge / Primary**
```
Auto-layout: Horizontal, Center, Gap: 0
Padding: 4px 12px
Height: 24px
Fill: #EEF2FF
Radius: 9999px
Content: Text (12px, Medium, #4338CA)
```

**Component: Badge / Success**
```
Instance of: Badge / Primary
Overrides:
├── Fill: #DCFCE7
└── Text Color: #15803D
```

**Component: Badge / Warning**
```
Instance of: Badge / Primary
Overrides:
├── Fill: #FEF3C7
└── Text Color: #B45309
```

**Component: Badge / Danger**
```
Instance of: Badge / Primary
Overrides:
├── Fill: #FEE2E2
└── Text Color: #B91C1C
```

#### 9. Alert Components

**Component: Alert / Success**
```
Auto-layout: Horizontal, Top, Gap: 12px
Padding: 16px
Fill: #F0FDF4
Stroke: Left, 4px, #22C55E
Radius: 8px
├── Icon (20px)
└── Message (14px, #15803D)
```

**Component: Alert / Warning**
```
Instance of: Alert / Success
Overrides:
├── Fill: #FFFBEB
├── Stroke: #F59E0B
└── Text Color: #B45309
```

**Component: Alert / Danger**
```
Instance of: Alert / Success
Overrides:
├── Fill: #FEF2F2
├── Stroke: #EF4444
└── Text Color: #B91C1C
```

**Component: Alert / Info**
```
Instance of: Alert / Success
Overrides:
├── Fill: #EFF6FF
├── Stroke: #3B82F6
└── Text Color: #1E40AF
```

---

## 🎯 Color Variables Setup

### In Figma: Local Variables Panel

Create these variable groups:

#### `colors/brand`
```
primary:      #6366F1
primary-light: #818CF8
primary-dark:  #4338CA
```

#### `colors/semantic`
```
success:      #22C55E
warning:      #F59E0B
danger:       #EF4444
info:         #3B82F6
```

#### `colors/sections`
```
clinical:     #10B981
telehealth:   #60A5FA
email:        #818CF8
hris:         #06B6D4
services:     #8B5CF6
analytics:    #F97316
```

#### `colors/dark-theme`
```
bg-primary:   #111827
bg-secondary: #1F2937
bg-tertiary:  #374151
border:       #374151
text-primary: #FFFFFF
text-secondary: #D1D5DB
text-tertiary: #9CA3AF
```

#### `colors/light-theme`
```
bg-primary:   #FAFAFA
bg-secondary: #FFFFFF
bg-tertiary:  #F3F4F6
border:       #E5E7EB
text-primary: #111827
text-secondary: #6B7280
text-tertiary: #9CA3AF
```

---

## 📝 Text Styles Setup

### Create in Figma: Text Styles Panel

```
# HEADINGS
Heading/H1/36px/Bold
  Font: Inter
  Size: 36
  Weight: 700
  Line-height: 120%
  Letter-spacing: 0%

Heading/H2/20px/Semibold
  Font: Inter
  Size: 20
  Weight: 600
  Line-height: 130%

Heading/H3/16px/Semibold
  Font: Inter
  Size: 16
  Weight: 600
  Line-height: 140%

# BODY
Body/Large/16px/Regular
  Font: Inter
  Size: 16
  Weight: 400
  Line-height: 150%

Body/Normal/14px/Regular
  Font: Inter
  Size: 14
  Weight: 400
  Line-height: 150%

Body/Small/13px/Regular
  Font: Inter
  Size: 13
  Weight: 400
  Line-height: 140%

# UI ELEMENTS
UI/Button/16px/Medium
  Font: Inter
  Size: 16
  Weight: 500
  Line-height: 120%

UI/Nav/14px/Medium
  Font: Inter
  Size: 14
  Weight: 500
  Line-height: 140%

UI/Label/14px/Medium
  Font: Inter
  Size: 14
  Weight: 500
  Line-height: 140%

UI/Caption/11px/Semibold
  Font: Inter
  Size: 11
  Weight: 600
  Line-height: 130%
  Letter-spacing: 5%

UI/Description/11px/Regular
  Font: Inter
  Size: 11
  Weight: 400
  Line-height: 140%
```

---

## 🔗 Prototype Interactions

### Sidebar Toggle
```
Trigger: On click
Action: Navigate to
Destination: Desktop - Sidebar Collapsed
Transition: Smart Animate, 300ms, Ease Out
```

### Section Expand/Collapse
```
Trigger: On click
Action: Open overlay
Destination: [Same frame with submenu visible]
Transition: Smart Animate, 300ms, Ease Out
```

### Navigation
```
Trigger: On click
Action: Navigate to
Destination: [Target page frame]
Transition: Dissolve, 200ms
```

---

## 📐 Grid & Layout Setup

### Desktop Grid (1440px)
```
Columns: 12
Gutter: 24px
Margins: 24px
Width: 1160px (content area)
```

### Sidebar Grid (280px)
```
Columns: 1
Gutter: 0
Margins: 16px
Width: 248px (content area)
```

---

## 🎨 Layer Naming Convention

```
📁 Pages/
  📁 Desktop - Dashboard/
    🔲 Frame
    📁 Sidebar/
      📁 Sections/
      📁 Nav Items/
    📁 Main Content/
      📁 Topbar/
      📁 Content/

🧩 Components/
  📁 Navigation/
  📁 Buttons/
  📁 Forms/
  📁 Cards/
  📁 Badges/
  📁 Alerts/

🎨 Design System/
  📁 Colors/
  📁 Typography/
  📁 Effects/
  📁 Icons/
```

---

## ✅ Setup Checklist

### Phase 1: Foundation (30 minutes)
- [ ] Create color variables
- [ ] Create text styles
- [ ] Set up grid layouts
- [ ] Create base frame structure

### Phase 2: Components (1 hour)
- [ ] Create sidebar components
- [ ] Create navigation components
- [ ] Create button components
- [ ] Create card components
- [ ] Create form components
- [ ] Create badge components
- [ ] Create alert components

### Phase 3: Pages (2 hours)
- [ ] Build Dashboard page
- [ ] Build Teams page
- [ ] Build Clinical Screening page
- [ ] Build HRIS Analytics page
- [ ] Build Settings page

### Phase 4: Prototyping (1 hour)
- [ ] Add sidebar toggle interaction
- [ ] Add section expand/collapse
- [ ] Add navigation between pages
- [ ] Test all interactions

---

## 📦 Export Package

### Handoff to Developers
Export these assets:
1. All components as `.fig` file
2. Icon set as SVG sprites
3. Color tokens as JSON (Figma Dev Mode)
4. Typography tokens as JSON
5. CSS variables file
6. Component documentation PDF

### CSS Variables Export
```css
:root {
  /* Brand Colors */
  --color-primary: #6366F1;
  --color-primary-light: #818CF8;
  --color-primary-dark: #4338CA;

  /* Semantic Colors */
  --color-success: #22C55E;
  --color-warning: #F59E0B;
  --color-danger: #EF4444;
  --color-info: #3B82F6;

  /* Section Colors */
  --color-clinical: #10B981;
  --color-telehealth: #60A5FA;
  --color-email: #818CF8;
  --color-hris: #06B6D4;
  --color-services: #8B5CF6;
  --color-analytics: #F97316;

  /* Dark Theme */
  --dark-bg-primary: #111827;
  --dark-bg-secondary: #1F2937;
  --dark-border: #374151;
  --dark-text-primary: #FFFFFF;
  --dark-text-secondary: #D1D5DB;

  /* Light Theme */
  --light-bg-primary: #FAFAFA;
  --light-bg-secondary: #FFFFFF;
  --light-border: #E5E7EB;
  --light-text-primary: #111827;
  --light-text-secondary: #6B7280;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  /* Typography */
  --font-family: 'Inter', sans-serif;
  --font-size-h1: 36px;
  --font-size-h2: 20px;
  --font-size-h3: 16px;
  --font-size-body: 14px;
  --font-size-small: 13px;
  --font-size-caption: 11px;
}
```

---

**Total Setup Time: ~4-5 hours**
**Difficulty: Intermediate**
**Figma Skills Required: Auto-layout, Components, Variables, Prototyping**

---

## 🎓 Tips & Best Practices

1. **Use Auto-layout for everything** - Makes responsive design easier
2. **Create variants before instances** - Set up component states first
3. **Use variables for colors** - Easy theme switching
4. **Name layers clearly** - Better developer handoff
5. **Prototype as you build** - Test interactions early
6. **Use constraints** - Set how layers resize
7. **Document components** - Add descriptions to components panel
8. **Team Library** - Publish when ready for collaboration

---

**End of Figma Setup Guide**

Ready to start building! 🚀
