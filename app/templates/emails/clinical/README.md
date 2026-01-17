# Clinical Email Templates Guide

## 📧 Template Structure

This directory contains HTML email templates for clinical notifications. All templates follow **table-based responsive design** for maximum email client compatibility.

## ✅ Completed Templates

### 1. `crisis_alert.html` ✅
**Purpose**: Urgent notifications for crisis alerts
**Style**: Red gradient header, high contrast, emergency resources prominent
**Status**: Fully implemented and integrated

---

## 📋 TODO(Human) - Templates to Implement

### 2. `pending_review.html` ⏳
**Purpose**: Batch notifications for screenings pending review
**Style**: Blue accent, table format for screening breakdown
**Priority**: Medium

**Template Requirements**:
```html
<!-- Header -->
- Blue gradient background (#3b82f6 to #2563eb)
- Icon: 📋 or 📊
- Title: "Pending Review Required"
- Subtitle: "X screenings awaiting your review"

<!-- Summary Section -->
- Total pending count
- Hours threshold (e.g., "pending >24 hours")
- Completion rate percentage

<!-- Screening Breakdown Table -->
<table>
  <thead>
    <tr>
      <th>Screening Type</th>
      <th>Pending Count</th>
      <th>Average Age</th>
    </tr>
  </thead>
  <tbody>
    <!-- Rows for each screening type -->
    <tr>
      <td>PHQ-9</td>
      <td>12</td>
      <td>36 hours</td>
    </tr>
    <!-- ... more rows -->
  </tbody>
</table>

<!-- CTA Button -->
- "Review Queue" button
- Link to /clinical/reviews

<!-- Footer -->
- Standard PsychSync footer
```

**Variables to Replace**:
- `{{ recipient_name }}`
- `{{ total_pending }}`
- `{{ hours_threshold }}`
- `{{ pending_breakdown }}` (dict: {PHQ9: 12, GAD7: 8, ...})
- `{{ action_url }}`
- `{{ organization_name }}`
- `{{ notification_date }}`

---

### 3. `weekly_summary.html` ⏳
**Purpose**: Weekly clinical analytics digest for clinicians
**Style**: Green/blue color scheme, dashboard layout, printable
**Priority**: Low

**Template Requirements**:
```html
<!-- Header -->
- Green gradient background (#10b981 to #059669)
- Icon: 📈 or 📊
- Title: "Weekly Clinical Summary"
- Date range: "Week of Jan 15 - Jan 21, 2025"

<!-- Key Metrics Cards (2x2 Grid) -->
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
  <!-- Card 1: Total Screenings -->
  <!-- Card 2: Completion Rate -->
  <!-- Card 3: Crisis Alerts -->
  <!-- Card 4: Avg Response Time -->
</div>

<!-- Top Concerns Section -->
- List of top 5-10 concerns
- With counts and trend arrows (↑↓)

<!-- Charts Section -->
- Simple HTML/CSS bar chart for completion trends
- Compare this week vs last week

<!-- CTA Button -->
- "View Full Analytics Dashboard"
- Link to /clinical/analytics

<!-- Print/Export Options -->
- "Download PDF Report" link
- "Print Summary" link
```

**Variables to Replace**:
- `{{ recipient_name }}`
- `{{ week_start }}` (e.g., "2025-01-15")
- `{{ week_end }}` (e.g., "2025-01-21")
- `{{ total_screenings }}`
- `{{ completion_rate }}` (percentage)
- `{{ crisis_count }}`
- `{{ avg_response_time }}` (in minutes)
- `{{ top_concerns }}` (list of tuples: [("suicidal_ideation", 8), ...])
- `{{ action_url }}`
- `{{ organization_name }}`
- `{{ notification_date }}`

---

## 🎨 Design Principles

### Color Scheme by Priority
| Priority | Background | Accent | Use Case |
|----------|-----------|--------|----------|
| **Critical** | Red gradient (#dc2626) | White | Crisis alerts, emergencies |
| **High** | Orange gradient (#ea580c) | White | High-risk screenings |
| **Medium** | Yellow/Amber (#ca8a04) | Dark | Pending reviews, reminders |
| **Low** | Blue (#3b82f6) | White | Informational, summaries |
| **Success** | Green (#10b981) | White | Weekly summaries, reports |

### Typography
- **Headings**: 28-32px, font-weight 700
- **Subheadings**: 16-18px, font-weight 600, uppercase, letter-spacing 1px
- **Body**: 14-16px, line-height 1.6
- **Small Text**: 11-12px (footers, metadata)

### Spacing
- **Container Padding**: 40px (desktop), 20px (mobile)
- **Section Spacing**: 30-40px between major sections
- **Element Spacing**: 15-20px between related elements

### Mobile Optimization
- **Max Width**: 600px container
- **Breakpoint**: 600px (stack columns below)
- **Touch Targets**: Minimum 44x44px buttons
- **Font Scaling**: `text-size: 16px` on mobile minimum (no zoom)

---

## 📧 Email Client Compatibility

### Tested Clients
- ✅ Gmail (web, iOS, Android)
- ✅ Outlook (desktop, web)
- ✅ Apple Mail (iOS, macOS)
- ✅ Yahoo Mail
- ⚠️ Windows Desktop Mail (limited CSS support)

### Compatibility Techniques
1. **Table-based layout** (not div/grid for structure)
2. **Inline CSS** (not external stylesheets)
3. **MSO conditionals** for Outlook-specific fixes
4. **Fallback colors** (gradients degrade to solid colors)
5. **Alt text** on all images
6. **Plain text fallback** for HTML-less clients

---

## 🔧 Implementation Steps

### Step 1: Create Template File
```bash
# Create new template
touch app/templates/emails/clinical/pending_review.html
```

### Step 2: Copy Structure from `crisis_alert.html`
```bash
# Use crisis_alert.html as a template
cp crisis_alert.html pending_review.html
```

### Step 3: Customize for Your Use Case
- Change header color gradient
- Update icon and title
- Add/remove sections as needed
- Replace `{{ variables }}` with your data

### Step 4: Implement Renderer Function
In `email_template_renderer.py`:
```python
def render_pending_review(self, recipient_name: str, ...) -> str:
    template_path = self.template_dir / "pending_review.html"

    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Replace variables
    rendered = template_content.replace('{{ recipient_name }}', recipient_name)
    # ... more replacements

    return rendered
```

### Step 5: Test Your Template
```python
# Test in Python shell
from app.services.clinical.email_template_renderer import get_email_renderer

renderer = get_email_renderer()
html = renderer.render_pending_review(
    recipient_name="Dr. Smith",
    total_pending=15,
    pending_breakdown={"PHQ9": 8, "GAD7": 7},
    hours_threshold=24,
    action_url="https://app.psychsync.io/clinical/reviews"
)

# Save to file for preview
with open("test_email.html", "w") as f:
    f.write(html)
```

### Step 6: Preview in Browser
Open `test_email.html` in Chrome/Safari to see how it looks

### Step 7: Send Test Email
Use email testing service (e.g., Mailtrap, Email on Acid) to test across clients

---

## 📊 Testing Checklist

Before marking template as complete, verify:

- [ ] Renders correctly in Gmail (web)
- [ ] Renders correctly in Outlook (desktop)
- [ ] Renders correctly on mobile (iOS Mail, Gmail app)
- [ ] All buttons are clickable and correct size
- [ ] Colors display correctly (no broken gradients)
- [ ] Text is readable (contrast ratio > 4.5:1)
- [ ] Plain text fallback works
- [ ] No broken images or icons
- [ ] Tables don't overflow on mobile
- [ ] Responsive breakpoint works (stacks correctly)

---

## 🚨 Common Issues & Solutions

### Issue: Gradients don't show in Outlook
**Solution**: Use `background-color` fallback before gradient
```html
<td style="background-color: #dc2626; background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);">
```

### Issue: Buttons not clickable in Gmail
**Solution**: Use `<a>` tag with inline styles, not `<button>`
```html
<a href="{{ action_url }}" style="display: inline-block; padding: 16px 32px; background-color: #dc2626; color: #ffffff; text-decoration: none; border-radius: 8px;">
    Click Here
</a>
```

### Issue: Tables overflow on mobile
**Solution**: Add `max-width: 100%` and `width: auto` on tables
```html
<table style="max-width: 100%; width: auto; table-layout: fixed;">
```

### Issue: Text too small on mobile
**Solution**: Use minimum 16px font size (prevents auto-zoom on iOS)
```html
<td style="font-size: 16px;">
```

---

## 📚 Resources

### Email Testing Tools
- **Mailtrap** (https://mailtrap.io) - Safe email testing
- **Email on Acid** (https://www.emailonacid.com) - Client testing
- **Litmus** (https://litmus.com) - Professional testing

### Design Resources
- **Campaign Monitor** (https://www.campaignmonitor.com/css/) - CSS guide
- **HTMLEmail** (https://htmlemail.io) - Boilerplate templates
- **Really Good Emails** (https://reallygoodemails.com) - Inspiration

### Documentation
- **Email Markup Guide** - HTML email best practices
- **CSS Support** - What CSS works where
- **Responsive Email** - Mobile email design patterns

---

## ✍️ Template Development Workflow

1. **Design Phase**
   - Sketch layout on paper or Figma
   - Identify sections and variables needed
   - Choose color scheme based on priority

2. **Implementation Phase**
   - Copy `crisis_alert.html` as starting point
   - Customize header, colors, content
   - Replace `{{ variables }}` throughout

3. **Renderer Function Phase**
   - Add render method to `email_template_renderer.py`
   - Map variables from notification metadata
   - Implement fallback (plain text) version

4. **Integration Phase**
   - Update `_send_email_notification()` method
   - Add conditional logic for new template type
   - Log template selection for debugging

5. **Testing Phase**
   - Test in browser (save to .html file)
   - Test in email clients (Mailtrap, Email on Acid)
   - Test responsive behavior (mobile viewport)
   - Verify plain text fallback

6. **Documentation Phase**
   - Update README with template details
   - Document variables and usage
   - Add preview screenshot
   - Update CHANGELOG

---

**Last Updated**: 2025-01-15
**Maintained By**: Platform Engineering Team
