import { test, expect } from '@playwright/test';

test.describe('Microsoft OAuth Login', () => {
  let authContext;
  let page;

  test.beforeAll(async () => {
    // Setup authentication context
    authContext = await browser.newContext();
    page = await authContext.newPage();
  });

  test.afterAll(async () => {
    await authContext.close();
  });

  test('should login with Microsoft OAuth', async () => {
    // Navigate to login page
    await page.goto('http://localhost:3000/login');

    // Click OAuth login button
    await page.click('[data-testid="microsoft-login"]');

    // Handle OAuth redirect
    await page.waitForURL('**/microsoft**');

    // Enter credentials
    await page.fill('#i0116', process.env.MICROSOFT_EMAIL);
    await page.click('#idSIButton9');

    await page.waitForSelector('#i0118', { timeout: 10000 });
    await page.fill('#i0118', process.env.MICROSOFT_PASSWORD);
    await page.click('#idSIButton9');

    // Handle redirect back to app
    await page.waitForURL('http://localhost:3000/dashboard');

    // Verify successful login
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
  });

  test('should handle OAuth errors gracefully', async () => {
    await page.goto('http://localhost:3000/login');
    await page.click('[data-testid="microsoft-login"]');

    // Simulate OAuth error
    await page.route('**/microsoft**', route => {
      route.fulfill({
        status: 500,
        contentType: 'text/html',
        body: '<h1>OAuth Error</h1>'
      });
    });

    await page.waitForURL('**/auth/error');
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Authentication failed');
  });

  test('should persist OAuth session', async () => {
    // Complete OAuth login
    await page.goto('http://localhost:3000/login');
    await page.click('[data-testid="microsoft-login"]');

    // Mock successful OAuth
    await page.route('**/auth/microsoft/callback**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { id: '1', email: 'user@example.com', name: 'Test User' },
          token: 'mock-jwt-token'
        })
      });
    });

    // Navigate away and back
    await page.goto('http://localhost:3000/dashboard');
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

    // Check session persistence
    await page.reload();
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });
});
