# Cross-Browser Testing with Playwright

This directory contains automated cross-browser tests using Playwright.

## 🚀 Quick Start

### Install Browsers (First Time Only)
```bash
npx playwright install
```

### Run All Tests
```bash
npm run test:e2e
# Or
npx playwright test
```

### Run Tests in UI Mode
```bash
npm run test:e2e:ui
# Or
npx playwright test --ui
```

### Run Tests in Debug Mode
```bash
npm run test:e2e:debug
# Or
npx playwright test --debug
```

## 🌐 Browser-Specific Testing

### Test in Chromium (Chrome/Edge)
```bash
npm run test:e2e:chromium
# Or
npx playwright test --project=chromium
```

### Test in Firefox
```bash
npm run test:e2e:firefox
# Or
npx playwright test --project=firefox
```

### Test in WebKit (Safari)
```bash
npm run test:e2e:webkit
# Or
npx playwright test --project=webkit
```

## 📱 Mobile Testing

Tests automatically run on mobile viewports:
- **Mobile Chrome**: Pixel 5 (375x667)
- **Mobile Safari**: iPhone 12 (390x844)

## 📊 Test Reports

After running tests, view the HTML report:
```bash
npm run test:e2e:report
# Or
npx playwright show-report
```

## 📁 Test Files

### `cross-browser-basic.spec.ts`
- Page load tests
- CSS feature support (Grid, Flexbox, Variables, backdrop-filter)
- JavaScript API support (IntersectionObserver, ResizeObserver, etc.)
- Scrollbar styling (WebKit vs Firefox)
- Form elements and controlled inputs
- Responsive design
- Console error detection

### `cross-browser-auth.spec.ts`
- Login form rendering and validation
- Controlled input state management
- Checkbox behavior
- Loading states
- Focus management
- Keyboard navigation
- Registration form
- Accessibility (labels, keyboard submission, focus indicators)

## 🧪 Writing New Tests

### Test Template
```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    await page.goto('/some-page');

    // Your test code here
    const element = page.locator('selector');
    await expect(element).toBeVisible();
  });
});
```

### Best Practices
1. **Use Locators**: Prefer `page.locator()` over `page.$()`
2. **Wait for Elements**: Use `await expect(element).toBeVisible()`
3. **Check Console**: Monitor for errors and warnings
4. **Test Accessibility**: Verify keyboard navigation and focus states
5. **Cross-Browser**: Avoid browser-specific APIs

## 🔧 Configuration

See `playwright.config.ts` for configuration:
- Base URL: http://localhost:5176
- Viewports: Desktop (1280x720), Mobile (375x667)
- Browsers: Chromium, Firefox, WebKit
- Reports: HTML, JUnit, List

## 🐛 Debugging Tips

### Run Single Test File
```bash
npx playwright test cross-browser-basic.spec.ts
```

### Run Specific Test
```bash
npx playwright test -g "should load homepage"
```

### Debug with Inspector
```bash
npx playwright test --debug
```

### Trace View
```bash
npx playwright show-trace trace.zip
```

## 📦 CI/CD Integration

### GitHub Actions Example
```yaml
- name: Install dependencies
  run: npm ci

- name: Install Playwright Browsers
  run: npx playwright install --with-deps

- name: Run Playwright tests
  run: npm run test:e2e

- name: Upload test report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## 🔗 Resources

- [Playwright Documentation](https://playwright.dev)
- [Cross-Browser Testing Guide](https://playwright.dev/docs/emulation)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)

## 📈 Current Browser Support

Based on `browserslist` configuration:
- Chrome/Edge: last 2 versions, ≥ 90
- Firefox: last 2 versions, ≥ 88
- Safari: last 2 versions, ≥ 14
- iOS Safari: ≥ 14
- Android Chrome: ≥ 90

**Excluded**: IE 11, dead browsers

## 🎯 Test Coverage Goals

- ✅ Page loads without errors
- ✅ CSS features work (Grid, Flexbox, Variables)
- ✅ JavaScript APIs supported
- ✅ Forms and inputs work correctly
- ✅ No console errors or warnings
- ✅ Responsive design works
- ✅ Accessibility features work
- ✅ Authentication flow works

---

**Last Updated**: 2026-01-21
**Test Framework**: Playwright 1.57+
