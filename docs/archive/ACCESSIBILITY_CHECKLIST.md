# Accessibility Checklist for PR Reviews

**Version:** 1.0.0
**Last Updated:** 2025-01-20
**Standard:** WCAG 2.1 Level AA

---

## 🎯 Purpose

This checklist helps reviewers ensure accessibility compliance during PR reviews. Use it for every pull request that modifies UI components, forms, or user interactions.

---

## ✅ Quick Checklist (5-Minute Review)

### Phase 1: Visual Inspection (2 minutes)

- [ ] **Images have meaningful alt text**
  - ❌ `alt="image"` or `alt="photo"` (too generic)
  - ❌ `alt="John Doe"` when name is already visible (redundant)
  - ✅ `alt="Professional headshot of John Doe, Engineering Manager"`
  - ✅ `alt=""` for decorative images

- [ ] **Form inputs have associated labels**
  - Every `<input>`, `<select>`, `<textarea>` has a `<label>`
  - Label uses `htmlFor` to match input `id`
  - Required fields are clearly marked

- [ ] **Buttons have proper attributes**
  - Non-submit buttons have `type="button"`
  - Icon buttons have `aria-label` or `aria-labelledby`
  - Disabled buttons have `disabled` attribute (not just CSS)

### Phase 2: Keyboard Navigation (2 minutes)

- [ ] **Tab through the component**
  - Tab order is logical (left-to-right, top-to-bottom)
  - Focus indicators are visible (contrast ratio ≥ 3:1)
  - Can activate all interactive elements with Enter/Space

- [ ] **Interactive elements are focusable**
  - All buttons/links are keyboard accessible
  - No `tabindex="-1"` on interactive elements (unless intended)
  - Custom dropdowns/widgets manage focus properly

### Phase 3: Screen Reader (1 minute)

- [ ] **Test with screen reader** (NVDA Windows / VoiceOver Mac)
  - Images are announced properly (not "unlabeled image")
  - Form fields have labels announced
  - Error messages are announced (using `role="alert"` or `aria-live`)
  - Dynamic content changes are announced

---

## 🔍 Detailed Checklist (Comprehensive Review)

Use this for complex components or full-page reviews.

### 1. Images & Graphics (WCAG 1.1.1)

- [ ] All `<img>` tags have `alt` attribute
- [ ] Alt text describes content, not repeats adjacent text
- [ ] Decorative images use `alt=""`
- [ ] Informative images use descriptive alt (min. context, max. 150 chars)
- [ ] Complex images have long descriptions or captions
- [ ] SVG images have `<title>` and `desc` elements
- [ ] Charts/graphs have data table alternative or long description

**Check:**
```tsx
// ❌ BAD
<img src="photo.jpg" alt="Image" />
<img src="user.jpg" alt="John Smith" /> {/* Name already visible */}

// ✅ GOOD
<img src="photo.jpg" alt="Bar chart showing 20% increase in sales" />
<img src="user.jpg" alt="Professional portrait of John Smith, CEO" />
<img src="icon.svg" alt="" /> {/* Decorative */}
```

---

### 2. Forms & Inputs (WCAG 1.3.1, 1.3.5)

- [ ] Every input has a visible label
- [ ] Label uses `htmlFor` to match input's `id`
- [ ] Required fields have `required` attribute and visual indicator
- [ ] Error messages use `role="alert"` or `aria-live="polite"`
- [ ] Invalid inputs have `aria-invalid="true"`
- [ ] Help text uses `aria-describedby` to link to input
- [ ] Fieldsets use `<fieldset>` and `<legend>` for radio/checkbox groups
- [ ] Form submission is announced (success/error messages)

**Check:**
```tsx
// ❌ BAD
<input type="text" placeholder="Enter your name" />

// ✅ GOOD
<label htmlFor="name">Full Name *</label>
<input
  type="text"
  id="name"
  required
  aria-invalid={errors.name ? 'true' : 'false'}
  aria-describedby={errors.name ? 'name-error' : 'name-help'}
/>
<p id="name-help" className="text-sm text-gray-600">
  Enter your first and last name
</p>
{errors.name && (
  <p id="name-error" className="text-sm text-red-600" role="alert">
    {errors.name}
  </p>
)}
```

---

### 3. Buttons & Links (WCAG 2.4.4, 4.1.2)

- [ ] Buttons have `type` attribute (`button`, `submit`, `reset`)
- [ ] Icon-only buttons have `aria-label` or `aria-labelledby`
- [ ] Links have descriptive text (not "click here")
- - [ ] Links that open new windows have `aria-label` or text indication
- [ ] Button/link text makes sense out of context
- [ ] Buttons in forms have clear purpose (submit/cancel)

**Check:**
```tsx
// ❌ BAD
<button onClick={handleClick}>Click here</button>
<div role="button" onClick={handleClick}>Submit</div>

// ✅ GOOD
<button type="button" onClick={handleClick}>View Details</button>
<button type="button" onClick={handleSubmit} aria-label="Submit form">
  <Icon className="w-5 h-5" />
</button>
<a href="/details" aria-label="Read more about accessibility standards">
  Learn more →
</a>
```

---

### 4. Keyboard Navigation (WCAG 2.1.1)

- [ ] All interactive elements are keyboard accessible
- [ ] Tab order follows visual layout
- [ ] Focus indicators have ≥ 3:1 contrast ratio
- [ ] No keyboard traps (can Tab in and out)
- [ ] Custom components handle keyboard events:
  - Dropdowns: Enter/Space to open, Arrow keys to navigate, Esc to close
  - Modals: Esc to close, focus trapped inside
  - Tabs: Arrow keys to switch, Enter to activate
- [ ] Skip navigation link present (appears on Tab)

**Check:**
```tsx
// ❌ BAD
<div onClick={handleClick} role="button" tabIndex={0}>
  {/* No keyboard handler */}
</div>

// ✅ GOOD
<button
  type="button"
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
  className="focus:ring-2 focus:ring-blue-500"
>
  Click me
</button>
```

---

### 5. ARIA Attributes (WCAG 4.1.2)

- [ ] `role` is only used when semantic HTML isn't sufficient
- [ ] Interactive elements have `aria-label` if text isn't descriptive
- [ ] `aria-hidden="true"` used on decorative content (not important content)
- [ ] `aria-expanded` used for collapsible content (menus, accordions)
- [ ] `aria-current` used for active navigation links
- [ ] `aria-live` used for dynamic content updates
- [ ] `aria-describedby` links help text to inputs
- [ ] `aria-invalid="true"` for invalid form fields

**Check:**
```tsx
// ❌ BAD
<button aria-hidden="true">Close</button> {/* Don't hide buttons */}

// ✅ GOOD
<button aria-label="Close dialog" onClick={onClose}>
  <XIcon aria-hidden="true" />
</button>

<div aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>
```

---

### 6. Color & Contrast (WCAG 1.4.3)

- [ ] Normal text has ≥ 4.5:1 contrast ratio
- [ ] Large text (18pt+) has ≥ 3:1 contrast ratio
- [ ] Interactive elements have ≥ 3:1 contrast ratio
- [ ] Color is NOT the only way to convey information
  - Charts have patterns/labels in addition to color
  - Error states use icons + text + color
  - Focus states have border/shadow in addition to color

**Check:**
```tsx
// ❌ BAD - Color only
<span className="text-red-500">Error</span>

// ✅ GOOD - Multiple indicators
<div className="flex items-center gap-2 text-red-600">
  <ExclamationCircleIcon aria-hidden="true" className="w-5 h-5" />
  <span role="img" aria-label="Error">Error: Invalid input</span>
</div>
```

---

### 7. Dynamic Content (WCAG 2.2.1, 2.4.1)

- [ ] Page refreshes don't happen without user action
- [ ] Moving/scrolling content can be paused/stopped
- [ ] Auto-updating content has `aria-live` region
- [ ] Modal/dialogs trap focus inside
- [ ] Previous focus is restored when modal closes
- [ ] Skip navigation link present

---

### 8. Responsive Design (WCAG 1.4.4, 1.4.10)

- [ ] Page works at 200% zoom
- [ ] No horizontal scrolling at 320px width
- [ ] Text reflows properly (no loss of content)
- [ ] Touch targets are ≥ 44×44 CSS pixels
- [ ] Spacing between interactive elements is sufficient

---

### 9. Media & Time-Based Media (WCAG 1.2)

- [ ] Autoplay is disabled by default
- [ ] Videos have captions
- [ ] Audio-only content has transcripts
- [ ] Media can be paused/stopped
- [ ] No flashing content (3 flashes/second limit)

---

### 10. Code Quality & Patterns

- [ ] Semantic HTML used (`<button>`, `<nav>`, `<main>`, `<header>`)
- [ ] Heading levels are hierarchical (h1 → h2 → h3)
- [ ] Lists use `<ul>`, `<ol>`, `<li>` (not divs)
- [ ] No `alert()` or `confirm()` (use accessible dialogs)
- [ ] Custom hooks/components follow accessible patterns

**Check:**
```tsx
// ❌ BAD
<div className="font-bold">Title</div> {/* Should be heading */}

// ✅ GOOD
<h2 className="text-xl font-bold">Title</h2>
```

---

## 🧪 Testing Tools

### Automated Tools
- **ESLint:** `npm run lint` (jsx-a11y plugin)
- **axe DevTools:** Chrome extension for automated testing
- **Lighthouse:** Chrome DevTools → Audit
- **WAVE:** WebAIM's browser extension

### Manual Testing
- **Keyboard:** Tab through entire page, test all interactions
- **Screen Reader:**
  - Windows: NVDA (free) or JAWS (paid)
  - Mac: VoiceOver (Cmd + F5 to enable)
  - Mobile: TalkBack (Android) / VoiceOver (iOS)
- **Color Contrast:**
  - Chrome DevTools → Color picker → Contrast ratio
  - WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/

### Browser Extensions
- axe DevTools
- WAVE Extension
- Lighthouse
- Colour Contrast Analyzer

---

## 📝 PR Review Template

Copy this when reviewing PRs:

```markdown
## Accessibility Review

### Automated Checks
- [ ] ESLint a11y rules pass (jsx-a11y)
- [ ] No new a11y violations introduced

### Manual Checks
- [ ] Keyboard navigation tested
- [ ] Screen reader tested (brief check)
- [ ] Color contrast verified
- [ ] Focus indicators visible

### Specific Components Changed
- [ ] Component Name: Status/Notes

### Issues Found
- List any accessibility issues with severity (HIGH/MEDIUM/LOW)

### Approval
- [ ] ✅ Approved (meets WCAG 2.1 AA)
- [ ] ⚠️ Approved with minor issues (non-blocking)
- [ ] ❌ Needs revision (blocking issues)
```

---

## 🚨 Red Flags (Immediate Failure)

**Reject PR if any of these are present:**

1. ❌ Missing `alt` attributes on `<img>` tags
2. ❌ Forms without labels
3. ❌ Interactive elements not keyboard accessible
4. ❌ No focus indicators on interactive elements
5. ❌ Color-only indicators (e.g., red error text without icon)
6. ❌ `alert()` or `confirm()` dialogs
7. ❌ Auto-playing video/audio

---

## 📚 Resources

### Documentation
- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Checklist](https://webaim.org/standards/wcag/checklist)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)
- [React Accessibility Docs](https://react.dev/learn/accessibility)

### Tools
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE Browser Extension](https://wave.webaim.org/)
- [Lighthouse](https://developers.google.com/web/tools/lighthouse/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### Training
- [WebAIM Training](https://webaim.org/training/)
- [A11y Cast](https://www.a11ycast.com/)
- [Accessibility Club YouTube](https://www.youtube.com/c/a11y)

---

## 🎓 Quick Reference Card

Print this for quick reference during reviews:

```
IMAGES: alt="" (decorative) OR alt="descriptive text"
FORMS: label + htmlFor=id, aria-describedby, aria-invalid
BUTTONS: type="button", aria-label for icons
KEYBOARD: Tab order logical, focus visible (ring/border)
ARIA: Only when semantic HTML insufficient
COLOR: ≥4.5:1 (text), ≥3:1 (large text/UI)
MEDIA: No autoplay, captions on video
```

---

**Version:** 1.0.0
**Maintained by:** Development Team
**Last Updated:** 2025-01-20

**Remember:** Accessibility is a team sport! Everyone plays a role in building an inclusive web.
