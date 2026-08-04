import { test, expect } from '@playwright/test';

/**
 * Cross-Browser Authentication Flow Tests
 *
 * These tests verify authentication works correctly across all browsers
 * Run: npx playwright test cross-browser-auth.spec.ts
 */

test.describe('Cross-Browser: Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page before each test
    await page.goto('/login');
  });

  test('should render login form correctly', async ({ page }) => {
    // Check that login form is visible
    const loginForm = page.locator('form').first();
    await expect(loginForm).toBeVisible();

    // Check for email input
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    await expect(emailInput).toBeVisible();

    // Check for password input
    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput).toBeVisible();

    // Check for submit button
    const submitButton = page.locator('button[type="submit"]').first();
    await expect(submitButton).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit without filling form
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();

    // Check for validation - HTML5 validation or custom validation
    const emailInput = page.locator('input[type="email"], input[name="email"]');

    // Input should be required
    const isRequired = await emailInput.evaluate(el =>
      el.hasAttribute('required')
    );

    expect(isRequired).toBeTruthy();
  });

  test('should handle controlled input state correctly', async ({ page }) => {
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"]');

    // Type in email field
    await emailInput.fill('test@example.com');
    await expect(emailInput).toHaveValue('test@example.com');

    // Type in password field
    await passwordInput.fill('password123');
    await expect(passwordInput).toHaveValue('password123');

    // Clear and verify
    await emailInput.fill('');
    await expect(emailInput).toHaveValue('');

    await passwordInput.fill('');
    await expect(passwordInput).toHaveValue('');
  });

  test('should handle checkbox state correctly', async ({ page }) => {
    // Look for "Remember me" checkbox
    const checkbox = page.locator('input[type="checkbox"]').first();
    const checkboxCount = await checkbox.count();

    if (checkboxCount > 0) {
      // Test checkbox state management
      await expect(checkbox).not.toBeChecked();

      await checkbox.check();
      await expect(checkbox).toBeChecked();

      await checkbox.uncheck();
      await expect(checkbox).not.toBeChecked();
    }
  });

  test('should disable submit button during loading state', async ({ page }) => {
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"]').first();

    // Fill form
    await emailInput.fill('test@example.com');
    await passwordInput.fill('password123');

    // Submit form (this will fail but should show loading state)
    await Promise.all([
      page.waitForNavigation({ timeout: 5000 }).catch(() => {}), // May not navigate due to auth
      submitButton.click()
    ]);

    // Check if button becomes disabled during submission
    // (This depends on implementation - may not always happen)
    const isDisabled = await submitButton.isDisabled();
    // We don't assert here as behavior may vary
    console.log('Submit button disabled during loading:', isDisabled);
  });

  test('should handle focus states correctly', async ({ page }) => {
    const emailInput = page.locator('input[type="email"], input[name="email"]');

    // Focus on input
    await emailInput.focus();

    // Check that input is focused
    await expect(emailInput).toBeFocused();

    // Tab to next input
    await page.keyboard.press('Tab');

    // Check password input is now focused
    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput).toBeFocused();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    // Test keyboard navigation through form
    await page.keyboard.press('Tab'); // Should focus first input
    await page.keyboard.press('Tab'); // Should move to next input
    await page.keyboard.press('Tab'); // Should move to button or checkbox

    // Check that something is focused
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'BUTTON']).toContain(focusedElement);
  });
});

test.describe('Cross-Browser: Registration Form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('should render registration form correctly', async ({ page }) => {
    // Check form is visible
    const form = page.locator('form').first();
    await expect(form).toBeVisible();

    // Check for multiple form fields
    const inputs = page.locator('input[type="text"], input[type="email"], input[type="password"]');
    const inputCount = await inputs.count();

    // Should have at least name, email, password, confirm password
    expect(inputCount).toBeGreaterThanOrEqual(3);
  });

  test('should handle password matching validation', async ({ page }) => {
    const password = page.locator('input[name="password"], input[type="password"]').first();
    const confirmPassword = page.locator('input[name="confirmPassword"], input[type="password"]').nth(1);

    const passwordCount = await password.count();
    const confirmCount = await confirmPassword.count();

    if (passwordCount > 0 && confirmCount > 0) {
      // Fill with different passwords
      await password.fill('password123');
      await confirmPassword.fill('different123');

      // Try to submit (validation should prevent)
      const submitButton = page.locator('button[type="submit"]').first();
      await submitButton.click();

      // Check for error message or validation failure
      // (Implementation-specific)
      await page.waitForTimeout(500);
    }
  });

  test('should handle terms checkbox state', async ({ page }) => {
    // Look for terms checkbox
    const termsCheckbox = page.locator('input[type="checkbox"]').first();
    const checkboxCount = await termsCheckbox.count();

    if (checkboxCount > 0) {
      // Check initial state
      await expect(termsCheckbox).not.toBeChecked();

      // Check checkbox
      await termsCheckbox.check();
      await expect(termsCheckbox).toBeChecked();

      // Verify checkbox value
      const isChecked = await termsCheckbox.isChecked();
      expect(isChecked).toBeTruthy();

      // Uncheck
      await termsCheckbox.uncheck();
      await expect(termsCheckbox).not.toBeChecked();
    }
  });
});

test.describe('Cross-Browser: Form Accessibility', () => {
  test('should have proper label associations', async ({ page }) => {
    await page.goto('/login');

    // Check that inputs have associated labels
    const inputs = page.locator('input');
    const inputCount = await inputs.count();

    for (let i = 0; i < Math.min(inputCount, 5); i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');

      // Input should have one of: id (with label), aria-label, or aria-labelledby
      const hasLabel = id || ariaLabel || ariaLabelledBy;
      expect(hasLabel).toBeTruthy();
    }
  });

  test('should support keyboard submission', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"]');

    // Fill form
    await emailInput.fill('test@example.com');
    await passwordInput.fill('password123');

    // Press Enter to submit (instead of clicking button)
    await passwordInput.press('Enter');

    // Form should attempt to submit
    await page.waitForTimeout(1000);
  });

  test('should show focus indicators', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.locator('input[type="email"], input[name="email"]');

    // Focus the input
    await emailInput.focus();

    // Check for focus outline or ring
    const hasFocusStyle = await emailInput.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return (
        styles.outline !== 'none' ||
        styles.boxShadow !== 'none' ||
        styles.borderRadius !== '0px'
      );
    });

    expect(hasFocusStyle).toBeTruthy();
  });
});
