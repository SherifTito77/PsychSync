# Memory Leak Load Testing Guide

This guide provides instructions for running a comprehensive 2-hour load testing session to verify that memory leaks have been fixed.

## Prerequisites

1. **Chrome DevTools** or **Firefox DevTools**
2. **Node.js** (for automation scripts)
3. **Redis CLI** (for backend cache monitoring)
4. **2 hours** of uninterrupted testing time

## Automated Load Testing Script

### Option 1: Puppeteer Automated Test

Create a file `scripts/load-test-memory.js`:

```javascript
/**
 * Memory Leak Load Testing Script
 *
 * This script automates a 2-hour user session to detect memory leaks
 * by periodically measuring heap size and tracking memory growth.
 *
 * Usage: node scripts/load-test-memory.js
 */

import puppeteer from 'puppeteer';
import { writeFileSync, appendFileSync } from 'fs';
import path from 'path';

const RESULTS_FILE = path.join(process.cwd(), 'memory-test-results.json');
const SCREENSHOT_DIR = path.join(process.cwd(), 'memory-test-screenshots');

// Test configuration
const CONFIG = {
  duration: 2 * 60 * 60 * 1000, // 2 hours in milliseconds
  checkInterval: 5 * 60 * 1000, // Check every 5 minutes
  baseUrl: 'http://localhost:5173',
  actions: [
    'navigate',
    'click',
    'scroll',
    'wait',
    'navigate-back',
  ],
};

class MemoryLoadTester {
  constructor() {
    this.browser = null;
    this.page = null;
    this.metrics = [];
    this.startTime = null;
  }

  async init() {
    console.log('🚀 Starting Memory Leak Load Test...\n');

    this.browser = await puppeteer.launch({
      headless: false, // Run with visible browser for debugging
      args: [
        '--enable-precise-memory-info',
        '--js-flags=--expose-gc',
      ],
    });

    this.page = await this.browser.newPage();

    // Enable performance monitoring
    await this.page.coverage.startJSCoverage();
    await this.page.coverage.startCSSCoverage();

    // Create screenshots directory
    const fs = require('fs');
    if (!fs.existsSync(SCREENSHOT_DIR)) {
      fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    }
  }

  async getMemoryMetrics() {
    const metrics = await this.page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize / 1048576, // MB
          totalJSHeapSize: performance.memory.totalJSHeapSize / 1048576, // MB
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit / 1048576, // MB
        };
      }
      return null;
    });

    return metrics;
  }

  async simulateUserAction(action) {
    try {
      switch (action) {
        case 'navigate':
          const pages = [
            '/dashboard',
            '/teams',
            '/assessments',
            '/analytics',
            '/settings',
          ];
          const randomPage = pages[Math.floor(Math.random() * pages.length)];
          await this.page.goto(`${CONFIG.baseUrl}${randomPage}`, {
            waitUntil: 'networkidle0',
          });
          break;

        case 'click':
          // Click a random button
          await this.page.evaluate(() => {
            const buttons = document.querySelectorAll('button:not([disabled])');
            if (buttons.length > 0) {
              buttons[Math.floor(Math.random() * buttons.length)].click();
            }
          });
          await this.page.waitForTimeout(1000);
          break;

        case 'scroll':
          await this.page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
          });
          await this.page.waitForTimeout(500);
          break;

        case 'wait':
          await this.page.waitForTimeout(3000);
          break;

        case 'navigate-back':
          await this.page.goBack();
          await this.page.waitForTimeout(1000);
          break;
      }
    } catch (error) {
      console.warn(`⚠️  Action failed: ${action}`, error.message);
    }
  }

  async collectMetrics(timestamp, iteration) {
    const memoryMetrics = await this.getMemoryMetrics();

    const metrics = {
      timestamp,
      iteration,
      elapsedTime: Date.now() - this.startTime,
      url: this.page.url(),
      memory: memoryMetrics,
    };

    this.metrics.push(metrics);

    // Log current state
    console.log(`\n📊 Metrics [Iteration ${iteration}]:`);
    console.log(`   Elapsed: ${Math.round(metrics.elapsedTime / 60000)} minutes`);
    console.log(`   URL: ${metrics.url}`);
    if (memoryMetrics) {
      console.log(`   Heap Used: ${memoryMetrics.usedJSHeapSize.toFixed(2)} MB`);
      console.log(`   Heap Total: ${memoryMetrics.totalJSHeapSize.toFixed(2)} MB`);
      console.log(`   Heap Limit: ${memoryMetrics.jsHeapSizeLimit.toFixed(2)} MB`);
      console.log(`   Usage: ${((memoryMetrics.usedJSHeapSize / memoryMetrics.jsHeapSizeLimit) * 100).toFixed(2)}%`);
    }

    // Take screenshot
    const screenshotPath = path.join(SCREENSHOT_DIR, `screenshot-${iteration}.png`);
    await this.page.screenshot({ path: screenshotPath, fullPage: false });

    // Write incremental results
    writeFileSync(RESULTS_FILE, JSON.stringify(this.metrics, null, 2));

    return metrics;
  }

  async run() {
    this.startTime = Date.now();
    let iteration = 0;
    let nextCheckTime = this.startTime + CONFIG.checkInterval;

    console.log(`⏱️  Test duration: ${CONFIG.duration / 60000} minutes`);
    console.log(`📍 Check interval: ${CONFIG.checkInterval / 60000} minutes`);
    console.log(`🔗 Base URL: ${CONFIG.baseUrl}\n`);

    // Initial metrics
    await this.collectMetrics(Date.now(), iteration++);

    // Main test loop
    while (Date.now() - this.startTime < CONFIG.duration) {
      // Perform random actions
      const action = CONFIG.actions[Math.floor(Math.random() * CONFIG.actions.length)];
      console.log(`\n🎬 Action: ${action}`);
      await this.simulateUserAction(action);

      // Collect metrics at intervals
      if (Date.now() >= nextCheckTime) {
        await this.collectMetrics(Date.now(), iteration++);
        nextCheckTime = Date.now() + CONFIG.checkInterval;

        // Force garbage collection if available
        try {
          await this.page.evaluate(() => {
            if (window.gc) window.gc();
          });
        } catch (e) {
          // GC not exposed, continue
        }
      }

      // Small delay between actions
      await this.page.waitForTimeout(2000);
    }

    // Final metrics
    await this.collectMetrics(Date.now(), iteration);

    await this.generateReport();
  }

  async generateReport() {
    console.log('\n\n📈 FINAL REPORT\n' + '='.repeat(60));

    const initialMemory = this.metrics[0].memory;
    const finalMemory = this.metrics[this.metrics.length - 1].memory;

    if (initialMemory && finalMemory) {
      const memoryGrowth = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
      const growthRate = memoryGrowth / (this.metrics.length * (CONFIG.checkInterval / 60000)); // MB per check interval

      console.log(`Initial Memory: ${initialMemory.usedJSHeapSize.toFixed(2)} MB`);
      console.log(`Final Memory: ${finalMemory.usedJSHeapSize.toFixed(2)} MB`);
      console.log(`Total Growth: ${memoryGrowth.toFixed(2)} MB (${memoryGrowth > 0 ? '+' : ''})`);
      console.log(`Growth Rate: ${growthRate.toFixed(4)} MB per ${CONFIG.checkInterval / 60000} minutes`);
      console.log(`Test Duration: ${((Date.now() - this.startTime) / 60000).toFixed(2)} minutes\n`);

      // Analysis
      if (memoryGrowth > 50) {
        console.log('🚨 WARNING: Significant memory growth detected!');
        console.log('   This suggests a memory leak that needs investigation.');
      } else if (memoryGrowth > 20) {
        console.log('⚠️  CAUTION: Moderate memory growth detected.');
        console.log('   Monitor in production to ensure this is acceptable.');
      } else {
        console.log('✅ SUCCESS: Memory usage is stable.');
        console.log('   No significant memory leaks detected.');
      }
    }

    console.log(`\n📁 Results saved to: ${RESULTS_FILE}`);
    console.log(`📁 Screenshots saved to: ${SCREENSHOT_DIR}`);
    console.log('='.repeat(60) + '\n');
  }

  async cleanup() {
    await this.page.coverage.stopJSCoverage();
    await this.page.coverage.stopCSSCoverage();
    await this.browser.close();
  }
}

// Run the test
const tester = new MemoryLoadTester();

try {
  await tester.init();
  await tester.run();
} catch (error) {
  console.error('❌ Test failed:', error);
  process.exit(1);
} finally {
  await tester.cleanup();
}
```

### Option 2: Manual Testing Guide

If you prefer manual testing, follow these steps:

## Manual Load Testing Procedure

### 1. **Preparation (10 minutes)**

1. Open Chrome DevTools (**F12** or **Cmd+Option+I**)
2. Go to **Memory** tab
3. Open **Performance Monitor** (DevTools → More tools → Performance Monitor)

### 2. **Baseline Measurement (5 minutes)**

1. Navigate to `http://localhost:5173`
2. Take a heap snapshot:
   - DevTools → Memory → Click "Take heap snapshot"
   - Save as "baseline.heapsnapshot"
3. Record initial metrics:
   - JS Heap Size
   - Number of nodes
   - Number of listeners

### 3. **Load Testing Phase (2 hours)**

Perform these actions in a continuous loop:

```javascript
// Copy this script into Chrome DevTools Console and run it
const testActions = [
  () => window.location.assign('/dashboard'),
  () => window.location.assign('/teams'),
  () => window.location.assign('/assessments'),
  () => window.location.assign('/analytics'),
  () => window.scrollTo(0, document.body.scrollHeight),
  () => document.querySelectorAll('button')[0]?.click(),
];

let iterations = 0;
const totalIterations = 240; // 2 hours at 30-second intervals

const testInterval = setInterval(() => {
  const action = testActions[iterations % testActions.length];
  try {
    action();
    console.log(`Iteration ${iterations + 1}/${totalIterations}: Action executed`);

    // Log memory every 10 iterations (5 minutes)
    if (iterations % 10 === 0 && performance.memory) {
      console.log('Memory:', {
        used: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
        total: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB',
        limit: (performance.memory.jsHeapSizeLimit / 1048576).toFixed(2) + ' MB',
      });
    }
  } catch (error) {
    console.error('Action failed:', error);
  }

  iterations++;

  if (iterations >= totalIterations) {
    clearInterval(testInterval);
    console.log('✅ Load test complete!');
  }
}, 30000); // Every 30 seconds
```

### 4. **Intermediate Checkpoints (Every 30 minutes)**

At each 30-minute mark:

1. Take a heap snapshot: `checkpoint-30m.heapsnapshot`, `checkpoint-60m.heapsnapshot`, etc.
2. Record metrics:
   ```javascript
   console.log({
     timestamp: new Date().toISOString(),
     memory: performance.memory,
     listeners: performance.getEntriesByType('resource').length,
   });
   ```

### 5. **Final Analysis (15 minutes)**

1. Take final heap snapshot: `final.heapsnapshot`
2. Compare snapshots:
   - Load `baseline.heapsnapshot`
   - Load `final.heapsnapshot`
   - View "Comparison" view
   - Look for:
     - **Detached DOM nodes** > 100 (indicates uncleaned components)
     - **Event listeners** increasing > 20%
     - **Strings** growing unbounded

### 6. **Analysis Checklist**

- [ ] JS Heap Size growth < 50MB over 2 hours
- [ ] Detached DOM nodes < 100
- [ ] Event listener count stable (±10%)
- [ ] No continuous upward trend in Performance Monitor
- [ ] Garbage collection reduces memory (not a flat line)

## Success Criteria

✅ **PASS**: Memory growth < 50MB after 2 hours
⚠️  **WARN**: Memory growth 50-100MB - monitor in production
❌ **FAIL**: Memory growth > 100MB - likely memory leak

## CI/CD Integration

Add to `.github/workflows/load-test.yml`:

```yaml
name: Memory Leak Load Test

on:
  schedule:
    - cron: '0 2 * * *'  # Run daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    timeout-minutes: 150

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Start dev server
        run: |
          cd frontend
          npm run dev &
          sleep 10

      - name: Run load test
        run: |
          cd frontend
          node scripts/load-test-memory.js

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: memory-test-results
          path: |
            frontend/memory-test-results.json
            frontend/memory-test-screenshots/

      - name: Check for memory leaks
        run: |
          node scripts/check-memory-results.js
```

## Troubleshooting

### Issue: "performance.memory is undefined"

**Solution**: Launch Chrome with `--enable-precise-memory-info` flag:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --enable-precise-memory-info \
  --js-flags=--expose-gc
```

### Issue: DevTools freezes during snapshot

**Solution**: Take snapshots less frequently (every 30 minutes instead of 15).

### Issue: Test runs too slow

**Solution**: Reduce `testInterval` or decrease `totalIterations`.
