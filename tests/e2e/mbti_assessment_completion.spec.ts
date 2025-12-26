import { test, expect } from '@playwright/test';

test.describe('MBTI Assessment Completion', () => {
  test.beforeEach(async ({ page }) => {
    // Setup test environment
    await page.goto('https://psychsync.test/login');
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('MBTI Assessment Completion', async ({ page }) => {
    await page.goto('https://psychsync.test/app');
    await page.check('[data-testid="checkbox"];
    await page.click('[data-testid="submit-button"];
    await expect(page.locator('[data-testid="result"]')).toContainText('All questions displayed correctly');
    await expect(page.locator('[data-testid="result"]')).toContainText('Progress tracked accurately');
    await expect(page.locator('[data-testid="result"]')).toContainText('Results calculated correctly');
    await expect(page.locator('[data-testid="result"]')).toContainText('Personality type displayed with detailed report');
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