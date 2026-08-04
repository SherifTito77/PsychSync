#!/usr/bin/env node

/**
 * PsychSync Screenshot Automation with Auth
 *
 * This script automatically logs in and captures screenshots
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Configuration
const CONFIG = {
  baseUrl: 'http://localhost:5173',
  apiUrl: 'http://localhost:8000',
  screenshotsDir: './screenshots',
  viewport: {
    desktop: { width: 1920, height: 1080 },
    mobile: { width: 375, height: 812 }
  },
  // Credentials from environment variables or defaults
  credentials: {
    email: process.env.SCREENSHOT_USER_EMAIL || 'testuser@psychsync.com',
    password: process.env.SCREENSHOT_USER_PASSWORD || 'testpass123'
  }
};

/**
 * Helper function to create a delay
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Screenshot definitions
 */
const SCREENSHOTS = [
  {
    name: '01-dashboard',
    url: '/dashboard',
    description: 'Main Dashboard page'
  },
  {
    name: '02-burnout-prevention',
    url: '/burnout-prevention',
    description: 'Burnout Prevention feature'
  },
  {
    name: '03-behavioral-analytics',
    url: '/behavioral-analytics',
    description: 'Behavioral Analytics feature'
  },
  {
    name: '04-toxic-behavior-detection',
    url: '/toxic-behavior-detection',
    description: 'Toxic Behavior Detection feature'
  },
  {
    name: '05-employee-safety',
    url: '/employee-safety',
    description: 'Employee Safety feature'
  },
  {
    name: '06-anomaly-detection',
    url: '/anomaly-detection',
    description: 'Anomaly Detection feature'
  },
  {
    name: '07-predictive-analytics',
    url: '/predictive-analytics',
    description: 'Predictive Analytics feature'
  },
  {
    name: '08-teams',
    url: '/teams',
    description: 'Teams page'
  },
  {
    name: '09-mobile-dashboard',
    url: '/dashboard',
    viewport: 'mobile',
    description: 'Dashboard - Mobile view'
  },
  {
    name: '10-mobile-burnout',
    url: '/burnout-prevention',
    viewport: 'mobile',
    description: 'Burnout Prevention - Mobile view'
  },
  {
    name: '11-mobile-behavioral',
    url: '/behavioral-analytics',
    viewport: 'mobile',
    description: 'Behavioral Analytics - Mobile view'
  }
];

/**
 * Ensure screenshots directory exists
 */
function ensureScreenshotsDir() {
  if (!fs.existsSync(CONFIG.screenshotsDir)) {
    fs.mkdirSync(CONFIG.screenshotsDir, { recursive: true });
  }
}

/**
 * Initialize browser and page
 */
async function initBrowser() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport(CONFIG.viewport.desktop);
  return { browser, page };
}

/**
 * Authenticate with the application
 */
async function login(page) {
  console.log('\n🔐 Logging in...');

  try {
    // Navigate to login page
    await page.goto(`${CONFIG.baseUrl}/login`, {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    await delay(1000);

    // Fill in login form
    await page.waitForSelector('input[type="email"], input[name="email"]', { timeout: 10000 });

    await page.evaluate((email) => {
      const emailInput = document.querySelector('input[type="email"], input[name="email"]');
      if (emailInput) emailInput.value = email;
    }, CONFIG.credentials.email);

    await page.evaluate((password) => {
      const passwordInput = document.querySelector('input[type="password"]');
      if (passwordInput) passwordInput.value = password;
    }, CONFIG.credentials.password);

    await delay(500);

    // Submit form
    await page.evaluate(() => {
      const form = document.querySelector('form');
      if (form) form.submit();
      const button = document.querySelector('button[type="submit"]');
      if (button) button.click();
    });

    // Wait for navigation after login
    await page.waitForNavigation({
      waitUntil: 'networkidle2',
      timeout: 15000
    }).catch(() => {
      // Navigation might have happened via JS, check current URL
      console.log('   ⚠️  Navigation timeout (continuing anyway)...');
    });

    await delay(2000);

    // Verify login success
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      throw new Error('Login failed - still on login page');
    }

    console.log('   ✅ Login successful!');
    console.log(`   📍 Current URL: ${currentUrl}`);

    return true;
  } catch (error) {
    console.error(`   ❌ Login failed: ${error.message}`);
    throw error;
  }
}

/**
 * Capture a single screenshot
 */
async function captureScreenshot(page, screenshot) {
  const { name, url, viewport = 'desktop', description } = screenshot;

  try {
    console.log(`\n📸 Capturing: ${name}`);
    console.log(`   URL: ${CONFIG.baseUrl}${url}`);
    console.log(`   Viewport: ${viewport}`);
    console.log(`   Description: ${description}`);

    // Set viewport
    await page.setViewport(CONFIG.viewport[viewport]);

    // Navigate to URL
    await page.goto(`${CONFIG.baseUrl}${url}`, {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Wait for page to stabilize
    await delay(2500);

    // Check if we got redirected to login (session expired)
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      console.log('   ⚠️  Session expired, re-logging in...');
      await login(page);
      // Retry navigation
      await page.goto(`${CONFIG.baseUrl}${url}`, {
        waitUntil: 'networkidle2',
        timeout: 30000
      });
      await delay(2500);
    }

    // Try to wait for main content
    try {
      await page.waitForSelector('main, aside, [class*="dashboard"], [class*="container"]', {
        timeout: 5000
      });
    } catch (e) {
      // Continue anyway
    }

    // Capture full page screenshot
    const filename = path.join(CONFIG.screenshotsDir, `${name}.png`);
    await page.screenshot({
      path: filename,
      fullPage: true
    });

    console.log(`   ✅ Saved: ${filename}`);
    return true;
  } catch (error) {
    console.error(`   ❌ Error: ${error.message}`);

    // Try to capture error screenshot
    try {
      const errorFilename = path.join(CONFIG.screenshotsDir, `${name}-error.png`);
      await page.screenshot({ path: errorFilename, fullPage: true });
      console.log(`   📷 Error screenshot saved: ${errorFilename}`);
    } catch (screenshotError) {
      // Ignore
    }

    return false;
  }
}

/**
 * Generate HTML index
 */
function generateIndexHtml() {
  const screenshots = fs.readdirSync(CONFIG.screenshotsDir)
    .filter(f => f.endsWith('.png') && !f.includes('-error'))
    .sort();

  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PsychSync Screenshots</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      padding: 2rem;
    }
    h1 {
      font-size: 2rem;
      margin-bottom: 0.5rem;
      color: #facc15;
    }
    .subtitle {
      color: #94a3b8;
      margin-bottom: 2rem;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
      gap: 2rem;
    }
    .card {
      background: #1e293b;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
      transition: transform 0.2s;
    }
    .card:hover {
      transform: translateY(-4px);
    }
    .card img {
      width: 100%;
      height: auto;
      display: block;
    }
    .card-info {
      padding: 1rem;
    }
    .card-title {
      font-weight: 600;
      color: #facc15;
      margin-bottom: 0.5rem;
    }
    .badge {
      display: inline-block;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      margin-right: 0.5rem;
    }
    .badge-desktop {
      background: #3b82f6;
    }
    .badge-mobile {
      background: #10b981;
    }
    .timestamp {
      text-align: center;
      padding: 2rem 0;
      color: #64748b;
      font-size: 0.875rem;
    }
  </style>
</head>
<body>
  <h1>📸 PsychSync Screenshots</h1>
  <p class="subtitle">Automated screenshots captured on ${new Date().toLocaleDateString()}</p>

  <div class="grid">
    ${screenshots.map(ss => {
      const name = ss.replace('.png', '').replace(/-/g, ' ');
      const info = SCREENSHOTS.find(s => s.name === ss.replace('.png', ''));
      const desc = info?.description || 'Screenshot';
      const viewport = info?.viewport || 'desktop';
      const badgeClass = viewport === 'mobile' ? 'badge-mobile' : 'badge-desktop';
      return `
    <div class="card">
      <img src="${ss}" alt="${name}">
      <div class="card-info">
        <div class="card-title">
          <span class="badge ${badgeClass}">${viewport}</span>
          ${name}
        </div>
        <div style="color: #94a3b8; font-size: 0.875rem;">${desc}</div>
      </div>
    </div>
      `;
    }).join('')}
  </div>

  <div class="timestamp">
    Generated on ${new Date().toISOString()}<br>
    Total screenshots: ${screenshots.length}
  </div>
</body>
</html>
  `;

  const indexPath = path.join(CONFIG.screenshotsDir, 'index.html');
  fs.writeFileSync(indexPath, html);
  console.log(`\n📄 Index HTML: ${indexPath}`);
  console.log(`   Open in browser: file://${path.resolve(indexPath)}`);
}

/**
 * Main execution
 */
async function main() {
  console.log('🚀 PsychSync Screenshot Automation with Authentication');
  console.log('=' .repeat(60));

  ensureScreenshotsDir();

  const { browser, page } = await initBrowser();

  try {
    // First, login
    await login(page);

    // Then capture all screenshots
    let successCount = 0;
    let failCount = 0;

    for (const screenshot of SCREENSHOTS) {
      const success = await captureScreenshot(page, screenshot);
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
    }

    generateIndexHtml();

    console.log('\n' + '='.repeat(60));
    console.log('✅ Screenshot Capture Complete!');
    console.log(`   Success: ${successCount}/${SCREENSHOTS.length}`);
    console.log(`   Failed:  ${failCount}/${SCREENSHOTS.length}`);
    console.log(`   Output:  ${CONFIG.screenshotsDir}/`);
    console.log('\n📖 View screenshots: Open index.html in browser');

  } catch (error) {
    console.error('\n❌ Fatal error:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { captureScreenshot, SCREENSHOTS, CONFIG };
