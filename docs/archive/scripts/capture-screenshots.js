#!/usr/bin/env node

/**
 * PsychSync Screenshot Automation Script
 *
 * This script uses Puppeteer to automatically capture screenshots
 * of your new sidebar navigation for documentation purposes.
 *
 * Prerequisites:
 *   npm install puppeteer
 *
 * Usage:
 *   node capture-screenshots.js
 *
 * Output:
 *   ./screenshots/ directory with all captured images
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
    laptop: { width: 1366, height: 768 },
    tablet: { width: 768, height: 1024 },
    mobile: { width: 375, height: 812 }
  },
  delays: {
    pageLoad: 2000,
    hover: 500,
    click: 1000,
    screenshot: 500
  }
};

// Screenshot definitions
const SCREENSHOTS = [
  // ===== FULL SIDEBAR SHOTS =====
  {
    name: '01-sidebar-collapsed',
    url: '/dashboard',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
      await page.evaluate(() => {
        // Collapse all sections
        document.querySelectorAll('button[class*="flex items-center"]').forEach(btn => {
          if (btn.textContent.includes('▼')) {
            btn.click();
          }
        });
      });
    },
    description: 'Full sidebar in collapsed state'
  },
  {
    name: '02-sidebar-expanded-all',
    url: '/dashboard',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
      await page.evaluate(() => {
        // Expand all sections
        document.querySelectorAll('button[class*="flex items-center"]').forEach(btn => {
          if (btn.textContent.includes('▼') || !btn.textContent.includes('▲')) {
            btn.click();
          }
        });
      });
    },
    description: 'Full sidebar with all sections expanded'
  },

  // ===== EARLY WARNING SECTION =====
  {
    name: '03-early-warning-collapsed',
    url: '/dashboard',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
      // Ensure Early Warning is collapsed
      await page.evaluate(() => {
        const earlyWarningBtn = Array.from(document.querySelectorAll('button')).find(btn =>
          btn.textContent.includes('Early Warning')
        );
        if (earlyWarningBtn && earlyWarningBtn.textContent.includes('▼')) {
          // Click to expand first
          earlyWarningBtn.click();
        }
      });
    },
    description: 'Early Warning section collapsed'
  },
  {
    name: '04-early-warning-expanded',
    url: '/dashboard',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
      await page.evaluate(() => {
        const earlyWarningBtn = Array.from(document.querySelectorAll('button')).find(btn =>
          btn.textContent.includes('Early Warning')
        );
        if (earlyWarningBtn && !earlyWarningBtn.textContent.includes('▲')) {
          earlyWarningBtn.click();
        }
      });
    },
    description: 'Early Warning section expanded showing all 7 features'
  },
  {
    name: '05-early-warning-hover',
    url: '/dashboard',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
      const earlyWarningBtn = await page.$('button:has-text("Early Warning")');
      if (earlyWarningBtn) {
        await earlyWarningBtn.hover();
      }
    },
    description: 'Early Warning section with hover state'
  },

  // ===== ACTIVE STATES =====
  {
    name: '06-active-burnout-prevention',
    url: '/burnout-prevention',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
      await page.evaluate(() => {
        const earlyWarningBtn = Array.from(document.querySelectorAll('button')).find(btn =>
          btn.textContent.includes('Early Warning')
        );
        if (earlyWarningBtn && !earlyWarningBtn.textContent.includes('▲')) {
          earlyWarningBtn.click();
        }
      });
    },
    description: 'Active state on Burnout Prevention'
  },
  {
    name: '07-active-behavioral-analytics',
    url: '/behavioral-analytics',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
      await page.evaluate(() => {
        const earlyWarningBtn = Array.from(document.querySelectorAll('button')).find(btn =>
          btn.textContent.includes('Early Warning')
        );
        if (earlyWarningBtn && !earlyWarningBtn.textContent.includes('▲')) {
          earlyWarningBtn.click();
        }
      });
    },
    description: 'Active state on Behavioral Analytics'
  },

  // ===== FEATURE PAGES =====
  {
    name: '08-burnout-prevention-page',
    url: '/burnout-prevention',
    action: async (page) => {
      await page.waitForSelector('[class*="burnout"]', { visible: true });
    },
    description: 'Full Burnout Prevention page'
  },
  {
    name: '09-team-dashboard-page',
    url: '/team-dashboard',
    action: async (page) => {
      await page.waitForSelector('main', { visible: true });
    },
    description: 'Team Dashboard page'
  },
  {
    name: '10-anomaly-detection-page',
    url: '/anomaly-detection',
    action: async (page) => {
      await page.waitForSelector('main', { visible: true });
    },
    description: 'Anomaly Detection page'
  },

  // ===== COMPARISON SHOTS =====
  {
    name: '11-visual-separator',
    url: '/dashboard',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
      // Scroll to show the separator
      await page.evaluate(() => {
        const separator = Array.from(document.querySelectorAll('div')).find(div =>
          div.textContent.includes('Risk Detection')
        );
        if (separator) {
          separator.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    },
    description: 'Visual separator detail (⚡ Risk Detection)'
  },

  // ===== MOBILE RESPONSIVE =====
  {
    name: '12-mobile-sidebar-collapsed',
    url: '/dashboard',
    viewport: 'mobile',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
    },
    description: 'Mobile view - collapsed sidebar'
  },
  {
    name: '13-mobile-early-warning-expanded',
    url: '/dashboard',
    viewport: 'mobile',
    action: async (page) => {
      await page.waitForSelector('aside', { visible: true });
      await page.evaluate(() => {
        const earlyWarningBtn = Array.from(document.querySelectorAll('button')).find(btn =>
          btn.textContent.includes('Early Warning')
        );
        if (earlyWarningBtn && !earlyWarningBtn.textContent.includes('▲')) {
          earlyWarningBtn.click();
        }
      });
    },
    description: 'Mobile view - Early Warning expanded'
  }
];

/**
 * Helper function to create a delay (replaces deprecated page.waitForTimeout)
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
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

  // Set default viewport
  await page.setViewport(CONFIG.viewport.desktop);

  return { browser, page };
}

/**
 * Ensure screenshots directory exists
 */
function ensureScreenshotsDir() {
  if (!fs.existsSync(CONFIG.screenshotsDir)) {
    fs.mkdirSync(CONFIG.screenshotsDir, { recursive: true });
  }
}

/**
 * Capture a single screenshot
 */
async function captureScreenshot(page, screenshot) {
  const { name, url, action, viewport = 'desktop', description } = screenshot;

  try {
    console.log(`\n📸 Capturing: ${name}`);
    console.log(`   URL: ${url}`);
    console.log(`   Viewport: ${viewport}`);
    console.log(`   Description: ${description}`);

    // Set viewport
    await page.setViewport(CONFIG.viewport[viewport]);

    // Navigate to URL
    await page.goto(`${CONFIG.baseUrl}${url}`, {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    // Wait for page load
    await delay(CONFIG.delays.pageLoad);

    // Execute custom action
    if (action) {
      await action(page);
      await delay(CONFIG.delays.click);
    }

    // Capture screenshot
    const filename = path.join(CONFIG.screenshotsDir, `${name}.png`);
    await page.screenshot({
      path: filename,
      fullPage: false
    });

    console.log(`   ✅ Saved: ${filename}`);
    return true;
  } catch (error) {
    console.error(`   ❌ Error: ${error.message}`);
    return false;
  }
}

/**
 * Generate comparison image (Before/After)
 */
async function generateComparison(browser) {
  console.log('\n📊 Generating comparison image...');

  const page = await browser.newPage();
  await page.setViewport(CONFIG.viewport.desktop);

  // This would require your old sidebar version
  // For now, we'll create a placeholder
  const comparisonPath = path.join(CONFIG.screenshotsDir, '00-comparison.png');

  try {
    await page.goto(`${CONFIG.baseUrl}/dashboard`, {
      waitUntil: 'networkidle0'
    });

    // Take screenshot of current state
    await page.screenshot({
      path: comparisonPath,
      fullPage: false
    });

    console.log(`   ✅ Comparison saved: ${comparisonPath}`);
  } catch (error) {
    console.error(`   ❌ Error generating comparison: ${error.message}`);
  }

  await page.close();
}

/**
 * Generate HTML index for easy viewing
 */
function generateIndexHtml() {
  const screenshots = fs.readdirSync(CONFIG.screenshotsDir)
    .filter(f => f.endsWith('.png'))
    .sort();

  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PsychSync Sidebar - Screenshots</title>
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
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
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
    .card-desc {
      font-size: 0.875rem;
      color: #94a3b8;
      line-height: 1.5;
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
  <h1>⚡ PsychSync Sidebar Screenshots</h1>
  <p class="subtitle">New Navigation Structure - Early Warning & Risk Section</p>

  <div class="grid">
    ${screenshots.map(ss => {
      const name = ss.replace('.png', '').replace(/-/g, ' ');
      return `
    <div class="card">
      <img src="${ss}" alt="${name}">
      <div class="card-info">
        <div class="card-title">${name}</div>
        <div class="card-desc">Screenshot captured for documentation</div>
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
  console.log('🚀 PsychSync Screenshot Automation');
  console.log('=' .repeat(50));

  // Ensure output directory
  ensureScreenshotsDir();

  // Initialize browser
  const { browser, page } = await initBrowser();

  try {
    // Capture all screenshots
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

    // Generate comparison
    await generateComparison(browser);

    // Generate index HTML
    generateIndexHtml();

    // Summary
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
