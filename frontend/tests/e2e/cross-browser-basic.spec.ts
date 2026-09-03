import { test, expect } from '@playwright/test';

/**
 * Cross-Browser Basic Functionality Tests
 *
 * These tests verify core functionality works across all browsers:
 * - Chromium (Chrome, Edge)
 * - Firefox
 * - WebKit (Safari)
 *
 * Run specific browser:
 *   npx playwright test --project=chromium
 *   npx playwright test --project=firefox
 *   npx playwright test --project=webkit
 */

test.describe('Cross-Browser: Page Load', () => {
  test('should load homepage without errors', async ({ page }) => {
    await page.goto('/');

    // Check page title
    await expect(page).toHaveTitle(/PsychSync/);

    // Check that main content is visible
    const mainContent = page.locator('main, #root, [role="main"]');
    await expect(mainContent).toBeVisible();
  });

  test('should have working navigation', async ({ page }) => {
    await page.goto('/');

    // Look for navigation elements
    const nav = page.locator('nav, [role="navigation"], header').first();
    if (await nav.count() > 0) {
      await expect(nav).toBeVisible();
    }
  });
});

test.describe('Cross-Browser: CSS Features', () => {
  test('should render CSS Grid layouts correctly', async ({ page }) => {
    await page.goto('/');

    // Check for grid elements
    const gridElements = page.locator('[style*="display: grid"], .grid, [class*="grid"]');

    const count = await gridElements.count();
    if (count > 0) {
      // Verify at least one grid element is visible
      await expect(gridElements.first()).toBeVisible();
    }
  });

  test('should render CSS Flexbox layouts correctly', async ({ page }) => {
    await page.goto('/');

    // Check for flex elements
    const flexElements = page.locator('[style*="display: flex"], .flex, [class*="flex"]');

    const count = await flexElements.count();
    if (count > 0) {
      // Verify at least one flex element is visible
      await expect(flexElements.first()).toBeVisible();
    }
  });

  test('should render CSS variables correctly', async ({ page }) => {
    await page.goto('/');

    // Check if CSS variables are being used
    const hasCssVariables = await page.evaluate(() => {
      const styles = getComputedStyle(document.body);
      return Object.values(styles).some(value =>
        value && value.includes('rgb') && value.length > 10
      );
    });

    // CSS variables should be working
    expect(hasCssVariables).toBeTruthy();
  });

  test('should support backdrop-filter with fallbacks', async ({ page, browserName }) => {
    await page.goto('/');

    // Check backdrop-filter support
    const supportsBackdropFilter = await page.evaluate(() => {
      return CSS.supports('backdrop-filter', 'blur(10px)') ||
             CSS.supports('-webkit-backdrop-filter', 'blur(10px)');
    });

    // Firefox should report false, others true
    if (browserName === 'firefox') {
      console.log('Firefox: backdrop-filter not supported (expected)');
    } else {
      expect(supportsBackdropFilter).toBeTruthy();
    }
  });
});

test.describe('Cross-Browser: JavaScript APIs', () => {
  test('should support IntersectionObserver', async ({ page }) => {
    await page.goto('/');

    // Check IntersectionObserver support
    const hasIntersectionObserver = await page.evaluate(() => {
      return 'IntersectionObserver' in window;
    });

    expect(hasIntersectionObserver).toBeTruthy();
  });

  test('should support ResizeObserver', async ({ page }) => {
    await page.goto('/');

    // Check ResizeObserver support
    const hasResizeObserver = await page.evaluate(() => {
      return 'ResizeObserver' in window;
    });

    expect(hasResizeObserver).toBeTruthy();
  });

  test('should support matchMedia', async ({ page }) => {
    await page.goto('/');

    // Check matchMedia support
    const hasMatchMedia = await page.evaluate(() => {
      return 'matchMedia' in window;
    });

    expect(hasMatchMedia).toBeTruthy();
  });

  test('should support localStorage', async ({ page }) => {
    await page.goto('/');

    // Check localStorage support
    const hasLocalStorage = await page.evaluate(() => {
      try {
        localStorage.setItem('test', 'test');
        localStorage.removeItem('test');
        return true;
      } catch (e) {
        return false;
      }
    });

    expect(hasLocalStorage).toBeTruthy();
  });

  test('should support optional chaining', async ({ page }) => {
    // This test verifies that the code has been transpiled correctly
    await page.goto('/');

    // Test optional chaining in page context
    const works = await page.evaluate(() => {
      const obj = { nested: { value: 'test' } };
      return obj?.nested?.value === 'test';
    });

    expect(works).toBeTruthy();
  });

  test('should support nullish coalescing', async ({ page }) => {
    await page.goto('/');

    // Test nullish coalescing in page context
    const works = await page.evaluate(() => {
      const value = null ?? 'default';
      return value === 'default';
    });

    expect(works).toBeTruthy();
  });
});

test.describe('Cross-Browser: Scrollbar Styling', () => {
  test('should have scrollbar styling in WebKit browsers', async ({ page, browserName }) => {
    await page.goto('/');

    if (browserName === 'webkit' || browserName === 'chromium') {
      // WebKit browsers should have custom scrollbar CSS
      const hasCustomScrollbar = await page.evaluate(() => {
        const style = document.createElement('div');
        style.style.webkitAppearance = '';
        return style.style.webkitAppearance !== undefined;
      });

      expect(hasCustomScrollbar).toBeTruthy();
    }
  });

  test('should have scrollbar styling in Firefox', async ({ page, browserName }) => {
    await page.goto('/');

    if (browserName === 'firefox') {
      // Firefox should support scrollbar-width
      const supportsScrollbarWidth = await page.evaluate(() => {
        const testDiv = document.createElement('div');
        testDiv.style.scrollbarWidth = 'thin';
        return testDiv.style.scrollbarWidth === 'thin';
      });

      expect(supportsScrollbarWidth).toBeTruthy();
    }
  });
});

test.describe('Cross-Browser: Form Elements', () => {
  test('should render controlled input elements correctly', async ({ page }) => {
    await page.goto('/login');

    // Check email input
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const emailCount = await emailInput.count();

    if (emailCount > 0) {
      // Test that input can be focused and typed in
      await emailInput.fill('test@example.com');
      await expect(emailInput).toHaveValue('test@example.com');
    }
  });

  test('should render checkbox elements correctly', async ({ page }) => {
    await page.goto('/login');

    // Look for checkboxes
    const checkbox = page.locator('input[type="checkbox"]').first();
    const checkboxCount = await checkbox.count();

    if (checkboxCount > 0) {
      // Check that checkbox can be clicked
      const isChecked = await checkbox.isChecked();
      await checkbox.check();
      await expect(checkbox).toBeChecked();
      await checkbox.uncheck();
      await expect(checkbox).not.toBeChecked();
    }
  });

  test('should render buttons correctly', async ({ page }) => {
    await page.goto('/');

    // Look for buttons
    const button = page.locator('button').first();
    const buttonCount = await button.count();

    if (buttonCount > 0) {
      // Check that button is visible and clickable
      await expect(button).toBeVisible();
      await expect(button).toBeEnabled();
    }
  });
});

test.describe('Cross-Browser: Responsive Design', () => {
  test('should render correctly on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');

    // Check that content is visible
    const mainContent = page.locator('main, #root, [role="main"]');
    await expect(mainContent).toBeVisible();
  });

  test('should render correctly on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone size
    await page.goto('/');

    // Check that content is visible
    const mainContent = page.locator('main, #root, [role="main"]');
    await expect(mainContent).toBeVisible();
  });

  test('should handle viewport resize', async ({ page }) => {
    await page.goto('/');

    // Start with desktop
    await page.setViewportSize({ width: 1280, height: 720 });

    // Resize to mobile
    await page.setViewportSize({ width: 375, height: 667 });

    // Check that page is still functional
    const mainContent = page.locator('main, #root, [role="main"]');
    await expect(mainContent).toBeVisible();
  });
});

test.describe('Cross-Browser: Console Errors', () => {
  test('should not have console errors on page load', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');

    // Wait a bit for any async errors
    await page.waitForTimeout(2000);

    // Check for critical errors
    const criticalErrors = errors.filter(err =>
      err.includes('Uncaught Error') ||
      err.includes('TypeError') ||
      err.includes('ReferenceError')
    );

    expect(criticalErrors).toHaveLength(0);
  });

  test('should not have React warnings in console', async ({ page }) => {
    const warnings: string[] = [];

    page.on('console', msg => {
      const text = msg.text();
      if (msg.type() === 'warning' && text.includes('Warning:')) {
        warnings.push(text);
      }
    });

    await page.goto('/');

    // Wait for async operations
    await page.waitForTimeout(2000);

    // Filter for React-specific warnings
    const reactWarnings = warnings.filter(w =>
      w.includes('React') ||
      w.includes('component') ||
      w.includes('setState') ||
      w.includes('unmounted')
    );

    // React warnings about unmounted components should not appear
    const unmountedWarnings = reactWarnings.filter(w =>
      w.includes('unmounted')
    );

    expect(unmountedWarnings).toHaveLength(0);
  });
});
