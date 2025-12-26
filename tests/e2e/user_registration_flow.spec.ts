import { test, expect } from '@playwright/test';

test.describe('User Registration Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Setup test environment
    await page.goto('https://psychsync.test/login');
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('User Registration Flow', async ({ page }) => {
    await page.goto('https://psychsync.test/app');
    await page.fill('[data-testid="input-field"], 'Fill in valid user details (name, email, password)');
    await page.click('[data-testid="submit-button"];
    await page.check('[data-testid="checkbox"];
    await page.click('[data-testid="submit-button"];
    await expect(page.locator('[data-testid="success-message"]')).toContainText('User account created successfully');
    await expect(page.locator('[data-testid="result"]')).toContainText('Verification email sent');
    await expect(page.locator('[data-testid="result"]')).toContainText('Email verification works');
    await expect(page.locator('[data-testid="result"]')).toContainText('User can login after verification');
  });
});

export default {
  use: { chromium },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] }
    }
  ]]
};