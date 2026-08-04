#!/usr/bin/env node

/**
 * Simplified PsychSync Screenshot Script
 *
 * This version focuses on capturing working pages without complex interactions
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Configuration
const CONFIG = {
  baseUrl: 'http://localhost:5173',
  screenshotsDir: './screenshots',
  viewport: {
    desktop: { width: 1920, height: 1080 },
    mobile: { width: 375, height: 812 }
  }
};

/**
 * Helper function to create a delay
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Simplified screenshot definitions - pages that exist and work
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
    name: '07-mobile-dashboard',
    url: '/dashboard',
    viewport: 'mobile',
    description: 'Dashboard - Mobile view'
  },
  {
    name: '08-mobile-burnout',
    url: '/burnout-prevention',
    viewport: 'mobile',
    description: 'Burnout Prevention - Mobile view'
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
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport(CONFIG.viewport.desktop);
  return { browser, page };
}

/**
 * Capture a single screenshot with robust error handling
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

    // Navigate with extended timeout
    await page.goto(`${CONFIG.baseUrl}${url}`, {
      waitUntil: 'networkidle2',
      timeout: 45000
    });

    // Wait a bit for any animations
    await delay(2000);

    // Try to wait for main content, but don't fail if it doesn't exist
    try {
      await page.waitForSelector('main, body', { timeout: 5000 });
    } catch (e) {
      // Ignore - we'll take screenshot anyway
    }

    // Capture screenshot
    const filename = path.join(CONFIG.screenshotsDir, `${name}.png`);
    await page.screenshot({
      path: filename,
      fullPage: true  // Capture full page
    });

    console.log(`   ✅ Saved: ${filename}`);
    return true;
  } catch (error) {
    console.error(`   ❌ Error: ${error.message}`);

    // Try to capture error screenshot for debugging
    try {
      const errorFilename = path.join(CONFIG.screenshotsDir, `${name}-error.png`);
      await page.screenshot({ path: errorFilename, fullPage: true });
      console.log(`   📷 Error screenshot saved: ${errorFilename}`);
    } catch (screenshotError) {
      // Ignore screenshot errors
    }

    return false;
  }
}

/**
 * Generate HTML index for easy viewing
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
    .timestamp {
      text-align: center;
      padding: 2rem 0;
      color: #64748b;
      font-size: 0.875rem;
    }
    .note {
      background: #1e40af;
      padding: 1rem;
      border-radius: 8px;
      margin-bottom: 2rem;
      border-left: 4px solid #3b82f6;
    }
  </style>
</head>
<body>
  <h1>📸 PsychSync Screenshots</h1>
  <p class="subtitle">Application Screenshots captured on ${new Date().toLocaleDateString()}</p>

  <div class="note">
    <strong>Note:</strong> If screenshots show login pages, you need to authenticate first.
    Visit <a href="${CONFIG.baseUrl}" style="color: #facc15;">${CONFIG.baseUrl}</a> and log in,
    then the screenshots will capture the actual application pages.
  </div>

  <div class="grid">
    ${screenshots.map(ss => {
      const name = ss.replace('.png', '').replace(/-/g, ' ');
      const desc = SCREENSHOTS.find(s => s.name === ss.replace('.png', ''))?.description || 'Screenshot';
      return `
    <div class="card">
      <img src="${ss}" alt="${name}">
      <div class="card-info">
        <div class="card-title">${name}</div>
        <div style="color: #94a3b8; font-size: 0.875rem;">${desc}</div>
      </div>
    </div>
      `;
    }).join('')}
  </div>

  <div class="timestamp">
    Generated on ${new Date().toISOString()}
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
  console.log('🚀 PsychSync Screenshot Capture (Simplified)');
  console.log('=' .repeat(50));

  ensureScreenshotsDir();

  const { browser, page } = await initBrowser();

  try {
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

    console.log('\n' + '='.repeat(50));
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
