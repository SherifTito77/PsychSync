# Corporate Integrations - Icon System Guide

Complete visual reference for all icons used in the Corporate Integrations dashboard.

---

## 🎨 Icon Categories

### 1. Data Source Icons

#### Communication Category 📨

| Icon | Name | Usage |
|------|------|-------|
| ✉️ | Email | Gmail, Outlook email metadata |
| 💬 | Slack | Slack messages, reactions |
| 👥 | Teams | Microsoft Teams chat & meetings |
| 🎥 | Zoom | Zoom transcripts & recordings |

#### Productivity Category 📈

| Icon | Name | Usage |
|------|------|-------|
| 📅 | Calendar | Google/Outlook calendar events |
| 📋 | Jira | Jira tickets & activity |
| 🔧 | GitHub | GitHub commits & PRs |
| 📝 | Confluence | Confluence edits & page views |

#### HR Category 👤

| Icon | Name | Usage |
|------|------|-------|
| 🏢 | Workday | Workday HR data |
| 🎋 | BambooHR | Bamboo HR metrics |
| ⏱️ | Time Tracking | Hours worked, overtime |
| ⭐ | Performance | Reviews & feedback |

#### Other Category 📦

| Icon | Name | Usage |
|------|------|-------|
| 📊 | Pulse Surveys | Employee feedback surveys |
| ⌚ | Wearables | Health & fitness data |
| 🔐 | VPN | Remote work logs |
| 🏷️ | Badge Swipes | Office access logs |

---

### 2. Status Icons

| Status | Icon | Color | Description |
|--------|------|-------|-------------|
| **Active** | ● | Green | Integration is connected and syncing |
| **Disabled** | ○ | Gray | Integration is disabled |
| **Error** | ⚠️ | Red | Integration has errors |
| **Syncing** | 🔄 | Blue | Currently syncing data |

---

### 3. Severity Icons

| Severity | Icon | Emoji | Color | Description |
|----------|------|-------|-------|-------------|
| **Low** | ℹ️ | ℹ️ | Blue | Informational, no action needed |
| **Medium** | ⚠️ | ⚠️ | Yellow | Monitor, may need attention |
| **High** | 🔶 | 🔶 | Orange | Action recommended |
| **Critical** | 🚨 | 🚨 | Red | Immediate action required |

---

### 4. Insight Category Icons

| Category | Icon | Description |
|----------|------|-------------|
| **Burnout Risk** | 🔥 | Employee burnout indicators |
| **Toxicity** | ☣️ | Toxic behavior exposure |
| **Engagement** | 👍 | Employee engagement levels |
| **Retention** | 🛡️ | Retention risk factors |
| **Work-Life Balance** | ⚖️ | Work-life balance metrics |

---

### 5. UI Action Icons

| Action | Icon | Usage |
|--------|------|-------|
| **Sync** | 🔄 | Manual sync trigger |
| **Settings** | ⚙️ | Configuration |
| **Add** | ➕ | Create new integration |
| **Delete** | 🗑️ | Remove integration |
| **Edit** | ✏️ | Modify integration |
| **View** | 👁️ | View details |
| **Export** | 📤 | Export data |
| **Download** | 📥 | Download reports |

---

## 🎯 Usage Examples

### React Component Example

```tsx
import { getDataSourceIcon, getCategoryIcon, getSeverityIcon } from './IntegrationIcons';

const IntegrationCard = ({ integration, insight }) => {
  const DataSourceIcon = getDataSourceIcon(integration.type);
  const CategoryIcon = getCategoryIcon(integration.category);
  const SeverityIcon = getSeverityIcon(insight.severity);

  return (
    <div className="integration-card">
      <DataSourceIcon className="w-6 h-6" />
      <CategoryIcon className="w-5 h-5" />
      <SeverityIcon className={`w-5 h-5 ${getSeverityColor(insight.severity)}`} />
    </div>
  );
};
```

### Icon Sizes

```tsx
// Small icons (buttons, badges)
<Icon className="w-4 h-4" />

// Medium icons (cards, lists)
<Icon className="w-5 h-5" />

// Large icons (headers, hero sections)
<Icon className="w-6 h-6" />

// Extra large icons (featured sections)
<Icon className="w-8 h-8" />
```

### Icon Colors

```tsx
// Category colors
<Icon className={getCategoryColor('communication')} />  // text-blue-600
<Icon className={getCategoryColor('productivity')} />   // text-green-600
<Icon className={getCategoryColor('hr')} />            // text-purple-600
<Icon className={getCategoryColor('other')} />          // text-gray-600

// Severity colors
<Icon className={getSeverityColor('low')} />      // text-blue-500
<Icon className={getSeverityColor('medium')} />   // text-yellow-500
<Icon className={getSeverityColor('high')} />     // text-orange-500
<Icon className={getSeverityColor('critical')} /> // text-red-500

// Status colors
<Icon className={getStatusColor('active')} />    // text-green-500
<Icon className={getStatusColor('disabled')} />  // text-gray-400
<Icon className={getStatusColor('error')} />     // text-red-500
<Icon className={getStatusColor('syncing')} />   // text-blue-500
```

---

## 🎨 Icon Design Principles

### 1. **Consistency**
- All icons use the same stroke width (2px)
- Consistent corner radius (rounded)
- Uniform visual weight

### 2. **Clarity**
- Simple, recognizable shapes
- Avoid visual clutter
- Clear at small sizes

### 3. **Accessibility**
- Color alone doesn't convey meaning
- Pair icons with text labels
- Maintain sufficient contrast ratios

### 4. **Purpose-Built**
- Each icon has specific meaning
- Don't reuse icons for different purposes
- Match mental models

---

## 📱 Responsive Icon Guidelines

### Breakpoint Sizes

| Screen Size | Icon Size | Usage |
|-------------|-----------|-------|
| Mobile (< 640px) | w-4 h-4 (16px) | Compact cards, navigation |
| Tablet (640-1024px) | w-5 h-5 (20px) | Standard cards, lists |
| Desktop (> 1024px) | w-6 h-6 (24px) | Hero sections, featured |

### Touch Targets

- Minimum tap target: 44x44px
- Icon with padding: 32px + 12px padding = 44px
- Group related icons together

---

## 🎭 Icon Animation States

### Hover State

```tsx
<svg className="w-5 h-5 hover:scale-110 transition-transform">
```

### Active State

```tsx
<svg className="w-5 h-5 active:scale-95 transition-transform">
```

### Loading State

```tsx
<svg className="w-5 h-5 animate-spin">
```

### Pulse State (for syncing)

```tsx
<svg className="w-5 h-5 animate-pulse">
```

---

## 🔧 Custom Icons

### Creating Custom Data Source Icons

```tsx
// 1. Define your icon component
export const CustomDataSourceIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    {/* Your icon paths */}
  </svg>
);

// 2. Add to the icon map
const iconMap = {
  // ... existing icons
  custom_data_source: CustomDataSourceIcon,
};

// 3. Use it
const CustomIcon = getDataSourceIcon('custom_data_source');
```

---

## 📦 Icon Libraries Used

### Primary
- **Heroicons** - Base icon set (MIT License)
- Custom SVG components for specific data sources

### Guidelines for Adding Icons
1. Use consistent stroke width (2px)
2. Maintain 24x24 viewBox
3. Use stroke="currentColor" for flexibility
4. Support className prop for sizing
5. Include proper title/desc for accessibility

---

## 🎨 Icon Color Palettes

### Category Colors
```css
.communication { color: #2563EB; }  /* Blue 600 */
.productivity { color: #16A34A; }   /* Green 600 */
.hr { color: #9333EA; }            /* Purple 600 */
.other { color: #4B5563; }          /* Gray 600 */
```

### Severity Colors
```css
.low { color: #3B82F6; }       /* Blue 500 */
.medium { color: #EAB308; }    /* Yellow 500 */
.high { color: #F97316; }      /* Orange 500 */
.critical { color: #EF4444; }  /* Red 500 */
```

### Status Colors
```css
.active { color: #22C55E; }    /* Green 500 */
.disabled { color: #9CA3AF; }  /* Gray 400 */
.error { color: #EF4444; }     /* Red 500 */
.syncing { color: #3B82F6; }   /* Blue 500 */
```

---

## ♿ Accessibility Considerations

### ARIA Labels

```tsx
<svg role="img" aria-label="Email integration">
  <title>Email</title>
  <EmailIcon />
</svg>
```

### Screen Reader Support

```tsx
<button aria-label="Sync integration">
  <SyncIcon aria-hidden="true" />
</button>
```

### Focus Indicators

```tsx
<svg className="w-5 h-5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
```

---

## 🚀 Performance Optimization

### Tree Shaking

Icons are exported as individual components, enabling tree-shaking:

```tsx
// ✅ Good - Only imports what's needed
import { EmailIcon } from './IntegrationIcons';

// ❌ Bad - Imports entire library
import * as Icons from './IntegrationIcons';
```

### Lazy Loading

For rarely used icons:

```tsx
const HeavyIcon = React.lazy(() => import('./IntegrationIcons').then(m => ({ default: m.HeavyIcon })));
```

---

## 📝 Icon Naming Conventions

### File Structure
```
frontend/src/components/integrations/
├── IntegrationIcons.tsx          # All icon components
├── IntegrationCard.tsx           # Uses icons
└── InsightsDashboard.tsx         # Uses severity icons
```

### Component Names
- PascalCase for components: `EmailIcon`
- camelCase for utilities: `getDataSourceIcon`
- kebab-case for files: `integration-icons.tsx`

---

`★ Insight ─────────────────────────────────────`
**Icon System Architecture**: The icon system uses **component composition** over icon fonts. Each icon is a **React component** accepting `className` props, enabling **Tailwind integration** and **dynamic styling**. This approach provides **better performance** (no extra HTTP requests) and **greater flexibility** (color, size, animation via props).

**Semantic Color Mapping**: Colors aren't arbitrary—**blue** communicates information (low severity), **yellow** indicates caution (medium), **orange** signals warning (high), **red** demands action (critical). This **universal color language** aligns with **UI/UX best practices** and **accessibility guidelines** (WCAG 2.1).

**Icon as Mental Models**: Data source icons mirror **real-world associations**—email ✉️, calendar 📅, Slack 💬. This **reduces cognitive load** by leveraging **existing mental models**. Users don't need to learn new symbols—they instantly recognize familiar metaphors, improving **usability** and **time-to-competency**.
`─────────────────────────────────────────────────`

---

## 🔗 Related Documentation

- [Corporate Integrations Guide](./CORPORATE_DATA_INTEGRATION_GUIDE.md)
- [Quick Start Guide](./QUICK_START_CORPORATE.md)
- [API Examples](./API_EXAMPLES.md)

---

**Icon System Version: 1.0.0**
**Last Updated: January 14, 2026**
