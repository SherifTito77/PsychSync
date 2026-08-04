# PsychSync Figma Design System
## Complete UI Kit & Component Library

**Updated:** January 2026
**Version:** 2.0
**Platform:** Web Application

---

## 🎨 Color Palette

### Primary Colors
```
Brand Purple:     #6366F1  (RGB: 99, 102, 241)
Brand Indigo:     #818CF8  (RGB: 129, 140, 248)
Brand Light:      #EEF2FF  (RGB: 238, 242, 255)
Brand Dark:       #4338CA  (RGB: 67, 56, 202)
```

### Semantic Colors
```
Success:          #22C55E  (RGB: 34, 197, 94)
Success Light:    #DCFCE7  (RGB: 220, 252, 231)
Warning:          #F59E0B  (RGB: 245, 158, 11)
Warning Light:    #FEF3C7  (RGB: 254, 243, 199)
Danger:           #EF4444  (RGB: 239, 68, 68)
Danger Light:     #FEE2E2  (RGB: 254, 226, 226)
Info:             #3B82F6  (RGB: 59, 130, 246)
Info Light:       #EFF6FF  (RGB: 239, 246, 255)
```

### Section Border Colors
```
Clinical (Green):     #10B981
Telehealth (Blue):    #60A5FA
Email (Indigo):       #818CF8
HRIS (Cyan):          #06B6D4
Services (Purple):    #8B5CF6
Analytics (Orange):   #F97316
```

### Neutral Colors (Dark Theme)
```
Background:       #111827  (Gray 900)
Sidebar:          #111827
Surface:          #1F2937  (Gray 800)
Surface Hover:    #374151  (Gray 700)
Border:           #374151
Text Primary:     #FFFFFF
Text Secondary:   #D1D5DB  (Gray 300)
Text Tertiary:    #9CA3AF  (Gray 400)
Text Disabled:    #6B7280  (Gray 500)
```

### Neutral Colors (Light Theme)
```
Background:       #FAFAFA
Surface:          #FFFFFF
Surface Hover:    #F3F4F6
Border:           #E5E7EB
Text Primary:     #111827
Text Secondary:   #6B7280
Text Tertiary:    #9CA3AF
```

---

## 📝 Typography

### Font Family
```
Primary: Inter
Weights: 300, 400, 500, 600, 700, 800
Source: Google Fonts
URL: https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap
```

### Type Scale

#### Headings
```
H1 - Page Title:       36px / Bold (700) / Line height: 1.2
H2 - Card Title:       20px / Semibold (600) / Line height: 1.3
H3 - Section Title:    16px / Semibold (600) / Line height: 1.4
```

#### Body Text
```
Body Large:       16px / Regular (400) / Line height: 1.5
Body Normal:      14px / Regular (400) / Line height: 1.5
Body Small:       13px / Regular (400) / Line height: 1.4
```

#### UI Elements
```
Button:           16px / Medium (500) / Line height: 1.2
Nav Item:         14px / Medium (500) / Line height: 1.4
Label:            14px / Medium (500) / Line height: 1.4
Caption:          11px / Semibold (600) / Line height: 1.3
Description:      11px / Regular (400) / Line height: 1.4
```

---

## 📐 Spacing System

### Scale (4px base unit)
```
Space 1:  4px
Space 2:  8px
Space 3:  12px
Space 4:  16px
Space 5:  20px
Space 6:  24px
Space 8:  32px
Space 10: 40px
Space 12: 48px
```

### Component Spacing
```
Sidebar Header Padding:    16px horizontal
Nav Item Padding:          12px 16px
Submenu Item Padding:      10px 16px 10px 48px
Card Padding:              24px
Page Content Padding:      24px
Section Title Spacing:     16px 16px 8px
```

---

## 🧩 Component Specifications

### 1. Sidebar

#### Expanded State
```
Width: 280px
Height: 100vh
Background: #111827
Position: Fixed
Left: 0
Top: 0
Overflow: Auto (with custom scrollbar)
Transition: 0.3s ease
```

#### Collapsed State
```
Width: 70px
Hide: .nav-text, .section-title, .chevron
Transition: 0.3s ease
```

#### Sidebar Header
```
Height: 64px
Border-bottom: 1px solid #374151
Display: Flex
Align: Center
Justify: Space-between
Padding: 0 16px
```

#### Toggle Button
```
Background: None
Border: None
Padding: 4px
Border-radius: 4px
Hover background: #374151
Icon: 16px × 16px SVG
```

### 2. Navigation Items

#### Nav Item (Core Items)
```
Height: Auto (min 48px)
Padding: 12px 16px
Display: Flex
Align: Center
Border-left: 3px solid transparent
Border-radius: 0
Transition: 0.15s ease

Hover:
  Background: #374151
  Color: #FFFFFF

Active:
  Background: #374151
  Border-left-color: #6366F1
```

#### Icon Styling
```
Size: 20px
Min-width: 28px
Margin-right: 12px (when sidebar expanded)
```

### 3. Collapsible Sections

#### Section Header
```
Height: Auto (min 48px)
Padding: 12px 16px
Display: Flex
Align: Center
Border-left: 3px solid (varies by section)
Cursor: Pointer
Transition: 0.15s ease

Hover:
  Background: #374151
  Color: #FFFFFF
```

#### Section-Specific Border Colors
```
Clinical:     #10B981 (Green)
Telehealth:   #60A5FA (Blue)
Email:        #818CF8 (Indigo)
HRIS:         #06B6D4 (Cyan)
Services:     #8B5CF6 (Purple)
Analytics:    #F97316 (Orange)
```

#### Chevron Icon
```
Size: 12px
Transition: Transform 0.2s
Default: ▼ (pointing down)
Rotated: 180deg (pointing up when expanded)
```

### 4. Submenu

#### Container
```
Background: #1F2937
Max-height: 0 (collapsed)
Max-height: 3000px (expanded)
Overflow: Hidden
Transition: Max-height 0.3s ease
Border-left: 3px solid (varies by section)
```

#### Submenu Item
```
Padding: 10px 16px 10px 48px
Display: Flex
Align: Flex-start
Font-size: 13px
Line-height: 1.4
Cursor: Pointer
Transition: 0.15s ease

Hover:
  Background: #374151
  Color: #FFFFFF

Active:
  Background: #374151
  Color: #FFFFFF
```

#### Icon Styling
```
Size: 16px
Min-width: 20px
Margin-right: 8px
```

#### Description Text
```
Font-size: 11px
Color: #6B7280
Margin-top: 2px
```

### 5. Buttons

#### Primary Button
```
Height: 48px
Padding: 12px 24px
Background: #6366F1
Color: #FFFFFF
Border: None
Border-radius: 8px
Font-weight: 500
Font-size: 16px
Cursor: Pointer
Box-shadow: 0 4px 6px rgba(99, 102, 241, 0.2)
Transition: 0.2s

Hover:
  Background: #4F46E5
  Transform: TranslateY(-1px)
```

#### Secondary Button
```
Height: 48px
Padding: 12px 24px
Background: #FFFFFF
Color: #6366F1
Border: 2px solid #6366F1
Border-radius: 8px
Font-weight: 500
Font-size: 16px
Cursor: Pointer
Transition: 0.2s

Hover:
  Background: #EEF2FF
```

### 6. Cards

#### Base Card
```
Background: #FFFFFF
Border: 1px solid #E5E7EB
Border-radius: 12px
Padding: 24px
Margin-bottom: 24px
Box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1)
```

#### Stat Card
```
Padding: 24px
Display in CSS Grid: repeat(auto-fit, minmax(280px, 1fr))

Stat Title:
  Font-size: 14px
  Color: #6B7280
  Margin-bottom: 8px

Stat Value:
  Font-size: 32px
  Font-weight: 700
  Color: #111827
  Margin-bottom: 8px

Stat Change:
  Font-size: 14px
  Color: #10B981
  Font-weight: 500
```

### 7. Form Elements

#### Input Field
```
Width: 100%
Height: 48px
Padding: 0 16px
Border: 1px solid #E5E7EB
Border-radius: 8px
Font-size: 14px
Transition: Border-color 0.2s

Focus:
  Outline: None
  Border-color: #6366F1
  Box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1)
```

#### Textarea
```
Min-height: 120px
Padding: 12px 16px
Resize: Vertical
```

### 8. Badges

#### Base Badge
```
Display: Inline-block
Padding: 4px 12px
Font-size: 12px
Font-weight: 500
Border-radius: 9999px
```

#### Badge Variants
```
Primary:
  Background: #EEF2FF
  Color: #4338CA

Success:
  Background: #DCFCE7
  Color: #15803D

Warning:
  Background: #FEF3C7
  Color: #B45309

Danger:
  Background: #FEE2E2
  Color: #B91C1C
```

### 9. Alerts

#### Base Alert
```
Padding: 16px
Border-radius: 8px
Border-left: 4px solid
Margin-bottom: 24px
Display: Flex
Gap: 12px
```

#### Alert Variants
```
Success:
  Background: #F0FDF4
  Border-left-color: #22C55E

Warning:
  Background: #FFFBEB
  Border-left-color: #F59E0B

Danger:
  Background: #FEF2F2
  Border-left-color: #EF4444

Info:
  Background: #EFF6FF
  Border-left-color: #3B82F6
```

### 10. Progress Bar

#### Container
```
Width: 100%
Height: 8px
Background: #E5E7EB
Border-radius: 9999px
Overflow: Hidden
```

#### Fill
```
Height: 100%
Background: #6366F1
Border-radius: 9999px
Transition: Width 0.3s ease
```

### 11. Tabs

#### Tab Button
```
Padding: 12px 16px
Background: None
Border: None
Border-bottom: 2px solid transparent
Cursor: Pointer
Font-size: 14px
Font-weight: 500
Color: #6B7280
Transition: 0.2s
Margin-bottom: -2px

Hover:
  Color: #111827

Active:
  Color: #6366F1
  Border-bottom-color: #6366F1
```

---

## 🎯 Icon Library

### Core Icons (Emoji-based, 20px)
```
📊 Dashboard
🎨 Icon Gallery
👥 Teams
🛡️ Toxic Behavior Detection
🔥 Burnout Prevention
🔒 Anonymous Feedback
🧠 Behavioral Analytics
🧩 Multi-Framework Synthesis
⚖️ Legal Rights
📈 Equity Dashboard
⚙️ Settings
```

### Section Icons (20px)
```
🏥 Clinical Screening (Yellow: #FBBF24)
🏥 Clinical Services & Resources (Blue: #60A5FA)
📧 Email Monitoring (Indigo: #818CF8)
📊 HRIS Analytics (Cyan: #06B6D4)
🔧 Services & Connectors (Purple: #A78BFA)
🤖 Analytics & AI (Orange: #FB923C)
```

### Clinical Screening Icons (16px)
```
💙 Depression (PHQ-9)
💛 Anxiety (GAD-7)
🚨 Suicide Risk (C-SSRS)
🆘 Crisis Resources
😰 Social Anxiety (LSAS)
🍎 Eating Attitudes (EAT-26)
🔄 OCD Severity (Y-BOCS)
😢 Depression (BDI-II)
😰 Anxiety (BAI)
📊 DASS-21
🎯 PTSD (PCL-5)
🍺 Alcohol Use (AUDIT)
😰 Stress (PSS-10)
😴 Insomnia (ISI)
🔥 Burnout (CBI)
🌈 Mood Disorder (MDQ)
💊 Drug Abuse (DAST-10)
🧩 Autism (AQ-10)
👶 Childhood Trauma (ACE)
💔 Impact of Event (IES-R)
📱 Internet Addiction (IAT)
⚡ ADHD (ASRS)
```

### Clinical Services Icons (16px)
```
📹 Telehealth Schedule
🤖 AI Chat Support
📊 Clinical Analytics
🏥 Population Health
🚨 Alerts Center
🏠 Screening Home
🌟 Wellbeing Check
😰 Stress Assessment
📚 Self-Help Library
🚨 Emergency Resources
👨‍⚕️ Clinical Dashboard
⭐ Enhanced Assessments
```

### Email Monitoring Icons (16px)
```
📅 Scheduled Reports
⚠️ Anomaly Detection
👥 Team Dashboard
😊 Sentiment Analysis
```

### HRIS Analytics Icons (16px)
```
📈 Analytics Dashboard
🔗 HRIS Connector
👥 Workforce Demographics
⭐ Performance Analytics
📉 Turnover Analysis
💰 Compensation Analysis
😊 Engagement Analytics
📚 Learning & Development
🎯 Succession Planning
```

### Services & Connectors Icons (16px)
```
🔗 Corporate Integrations
❤️ Health Dashboard
📊 Team Health Analytics
🧘 Mental Health
🧠 Personality Assessments
📊 Behavioral Analysis
📧 Email Connector
```

### Analytics & AI Icons (16px)
```
⚡ Team Optimizer
🔥 Burnout Prediction
🧩 Team Composition
🤖 Predictive Analytics
🔬 Reliability & Validity
📈 General Analytics
```

### UI Icons
```
🔔 Notifications
🛡️ Anonymous Feedback (Public)
🔍 Check Status
```

---

## 📱 Navigation Structure

### Main Navigation Groups

#### 1. Core (11 items)
```
1. Dashboard
2. Icon Gallery
3. Teams
4. Toxic Behavior Detection
5. Burnout Prevention
6. Anonymous Feedback
7. Behavioral Analytics
8. Multi-Framework Synthesis
9. Legal Rights
10. Equity Dashboard
11. Settings
```

#### 2. Email Monitoring (4 items - Collapsible)
```
1. Scheduled Reports
2. Anomaly Detection
3. Team Dashboard
4. Sentiment Analysis
```

#### 3. HRIS Analytics (9 items - Collapsible)
```
1. Analytics Dashboard
2. HRIS Connector
3. Workforce Demographics
4. Performance Analytics
5. Turnover Analysis
6. Compensation Analysis
7. Engagement Analytics
8. Learning & Development
9. Succession Planning
```

#### 4. Clinical Screening (22 items - Collapsible)
```
1. Depression Screening (PHQ-9)
2. Anxiety Screening (GAD-7)
3. Suicide Risk (C-SSRS)
4. Crisis Resources
5. Social Anxiety (LSAS)
6. Eating Attitudes (EAT-26)
7. OCD Severity (Y-BOCS)
8. Depression (BDI-II)
9. Anxiety (BAI)
10. DASS-21
11. PCL-5
12. AUDIT
13. PSS-10
14. ISI
15. CBI
16. MDQ
17. DAST-10
18. AQ-10
19. ACE
20. IES-R
21. IAT
22. ASRS
```

#### 5. Clinical Services & Resources (12 items - Collapsible)
```
1. Telehealth - Schedule Consultation
2. AI Chat Support
3. Clinical Analytics
4. Population Health
5. Alerts Center
6. Screening Home
7. Wellbeing Check
8. Stress Assessment
9. Self-Help Library
10. Emergency Resources
11. Clinical Dashboard
12. Enhanced Assessments
```

#### 6. Services & Connectors (7 items - Collapsible)
```
1. Corporate Integrations
2. Health Dashboard
3. Team Health Analytics
4. Mental Health
5. Personality Assessments
6. Behavioral Analysis
7. Email Connector
```

#### 7. Analytics & AI (6 items - Collapsible)
```
1. Team Optimizer
2. Burnout Prediction
3. Team Composition
4. Predictive Analytics
5. Reliability & Validity
6. General Analytics
```

#### 8. Public Access (2 items)
```
1. Anonymous Feedback
2. Check Status
```

---

## 🖼️ Layout Grids

### Stats Grid
```
Display: Grid
Grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))
Gap: 24px
Margin-bottom: 32px
```

### Two Column Grid
```
Display: Grid
Grid-template-columns: repeat(2, 1fr)
Gap: 24px
```

### Three Column Grid
```
Display: Grid
Grid-template-columns: repeat(3, 1fr)
Gap: 24px
```

### Responsive Breakpoints
```
Desktop: > 1024px (3 columns)
Tablet:  768px - 1024px (2 columns)
Mobile:  < 768px (1 column, sidebar collapsed to 70px)
```

---

## 🎨 Effects & Shadows

### Box Shadows
```
Sm:   0 1px 2px rgba(0, 0, 0, 0.05)
Md:   0 1px 3px rgba(0, 0, 0, 0.1)
Lg:   0 4px 6px rgba(99, 102, 241, 0.2)
Xl:   0 10px 15px rgba(0, 0, 0, 0.1)
```

### Transitions
```
Fast:   0.15s ease
Normal: 0.2s ease
Slow:   0.3s ease
```

### Custom Scrollbar (Sidebar)
```
Width: 6px
Track: #111827
Thumb: #374151
Thumb Hover: #4B5563
Border-radius: 3px
```

---

## 📐 Component States

### Hover States
```
Nav Items: Background #374151, Color #FFFFFF
Buttons: Transform translateY(-1px)
Cards: Box-shadow increase
```

### Active States
```
Nav Items: Background #374151, Left border colored
Tabs: Bottom border colored, text color change
```

### Focus States
```
Inputs: Border #6366F1, Box-shadow 0 0 0 3px rgba(99, 102, 241, 0.1)
Buttons: Outline 2px solid #6366F1
```

### Disabled States
```
Opacity: 0.5
Cursor: Not-allowed
Pointer-events: None
```

---

## ✏️ Figma Implementation Guide

### Step 1: Create Color Variables
1. Open Figma
2. Go to Local Variables (previously Design Tokens)
3. Create variable groups:
   - `colors/primary`
   - `colors/semantic`
   - `colors/neutral`
   - `colors/borders`

### Step 2: Create Text Styles
```
Heading/H1/36px/Bold
Heading/H2/20px/Semibold
Heading/H3/16px/Semibold
Body/Large/16px/Regular
Body/Normal/14px/Regular
Body/Small/13px/Regular
UI/Button/16px/Medium
UI/Nav/14px/Medium
UI/Label/14px/Medium
UI/Caption/11px/Semibold
UI/Description/11px/Regular
```

### Step 3: Create Components
Create these as master components:
1. `Sidebar / Expanded`
2. `Sidebar / Collapsed`
3. `Nav Item / Default`
4. `Nav Item / Active`
5. `Section Header / Collapsed`
6. `Section Header / Expanded`
7. `Submenu Item`
8. `Button / Primary`
9. `Button / Secondary`
10. `Card / Base`
11. `Card / Stat`
12. `Input / Default`
13. `Input / Focus`
14. `Badge / All variants`
15. `Alert / All variants`

### Step 4: Create Auto-Layout
```
Sidebar Header:
  - Auto-layout: Horizontal
  - Space between: 16px
  - Padding: 0 16px
  - Height: 64px

Nav Item:
  - Auto-layout: Horizontal
  - Gap: 12px
  - Padding: 12px 16px
  - Vertical alignment: Center

Submenu Item:
  - Auto-layout: Horizontal vertical
  - Gap: 8px
  - Padding: 10px 16px
  - Vertical alignment: Top
```

### Step 5: Create Variants
For each component, create variants for:
- State (Default, Hover, Active, Focus, Disabled)
- Size (if applicable)
- Color theme (if applicable)

---

## 📦 Export Assets

### Recommended Export Settings
```
Icons: SVG (1x, 2x)
Photos: PNG (2x, 3x)
Illustrations: SVG

Format: SVG
Scale: 1x, 2x
Suffix: -1x, -2x
```

---

## 🔄 Version History

```
v2.0 (January 2026)
  - Added HRIS Analytics section
  - Added Email Monitoring section
  - Expanded Clinical Screening to 22 items
  - Enhanced Clinical Services & Resources
  - Added Services & Connectors section
  - Updated Analytics & AI section
  - All dropdowns collapsed by default

v1.0 (Initial Release)
  - Base design system
  - Core navigation
  - Clinical screening tools
  - Basic components
```

---

## 📞 Design Resources

### Fonts
- **Inter**: https://fonts.google.com/specimen/Inter

### Color Tools
- **Coolors**: https://coolors.co/
- **Adobe Color**: https://color.adobe.com/

### Icon Libraries
- **Emoji**: Native system emojis (used in this design)
- **Lucide**: https://lucide.dev/
- **Heroicons**: https://heroicons.com/

### Figma Plugins
- **Autoname**: Auto-renames layers
- **Stark**: Accessibility checking
- **Unsplash**: Stock photos
- **Iconify**: Icon library

---

## ✅ Accessibility Checklist

- [ ] Color contrast ratios meet WCAG AA (4.5:1 for normal text)
- [ ] All interactive elements have focus states
- [ ] Touch targets are at least 44×44px
- [ ] Text is resizable up to 200%
- [ ] Color is not the only means of conveying information
- [ ] Keyboard navigation is supported
- [ ] ARIA labels are included where needed

---

**End of Design System Documentation**

For questions or updates, contact the design team.
