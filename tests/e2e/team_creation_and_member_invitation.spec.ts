import { test, expect } from '@playwright/test';

test.describe('Team Creation and Member Invitation', () => {
  test.beforeEach(async ({ page }) => {
    // Setup test environment
    await page.goto('https://psychsync.test/login');
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('Team Creation and Member Invitation', async ({ page }) => {
    await page.goto('https://psychsync.test/app');
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Team created successfully');
    await expect(page.locator('[data-testid="result"]')).toContainText('Invitation emails sent');
    await expect(page.locator('[data-testid="result"]')).toContainText('Members can accept invitations');
    await expect(page.locator('[data-testid="result"]')).toContainText('Roles and permissions applied correctly');
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
