#!/usr/bin/env node

/**
 * Debug script to test login process
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  baseUrl: 'http://localhost:5173',
  apiUrl: 'http://localhost:8000',
  credentials: {
    email: process.env.SCREENSHOT_USER_EMAIL || 'sherif.tito.77@gmail.com',
    password: process.env.SCREENSHOT_USER_PASSWORD || 'heba1982'
  }
};

async function debugLogin() {
  console.log('🔍 Debug Login Process');
  console.log('=' .repeat(50));
  console.log(`Email: ${CONFIG.credentials.email}`);
  console.log(`Frontend: ${CONFIG.baseUrl}`);
  console.log(`Backend: ${CONFIG.apiUrl}`);
  console.log('=' .repeat(50));

  // Check if backend is accessible
  console.log('\n0️⃣ Checking backend availability...');
  try {
    const fetch = (await import('node-fetch')).default;
    const healthCheck = await fetch(`${CONFIG.apiUrl}/api/v1/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (healthCheck.ok) {
      console.log('   ✅ Backend is running');
    } else {
      console.log('   ⚠️  Backend responded with:', healthCheck.status);
    }
  } catch (e) {
    console.log('   ❌ Backend is not accessible!');
    console.log('   Make sure to run: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload');
    console.log('\nSkipping browser launch since backend is down.');
    return;
  }

  const browser = await puppeteer.launch({
    headless: false,  // Show browser for debugging
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 100  // Slow down actions for visibility
  });

  const page = await browser.newPage();

  // Enable request/response interception
  const requests = [];
  const responses = [];

  page.on('request', request => {
    requests.push({
      url: request.url(),
      method: request.method(),
      headers: request.headers(),
      postData: request.postData()
    });
  });

  page.on('response', response => {
    responses.push({
      url: response.url(),
      status: response.status(),
      ok: response.ok()
    });
  });

  // Capture console messages
  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text()
    });
  });

  // Save screenshots for each step
  const debugDir = './debug-screenshots';
  if (!fs.existsSync(debugDir)) {
    fs.mkdirSync(debugDir, { recursive: true });
  }

  try {
    console.log('\n1️⃣ Navigating to login page...');
    await page.goto(`${CONFIG.baseUrl}/login`, {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    await page.screenshot({ path: path.join(debugDir, '01-login-page.png'), fullPage: true });
    console.log('   ✅ Login page loaded');

    // Check all input fields
    console.log('\n2️⃣ Analyzing form fields...');
    const inputs = await page.evaluate(() => {
      const allInputs = Array.from(document.querySelectorAll('input'));
      return allInputs.map(input => ({
        type: input.type,
        name: input.name,
        id: input.id,
        placeholder: input.placeholder,
        className: input.className
      }));
    });

    console.log('   Found inputs:', JSON.stringify(inputs, null, 2));

    // Check for form
    const formInfo = await page.evaluate(() => {
      const form = document.querySelector('form');
      if (!form) return { found: false };

      return {
        found: true,
        action: form.action,
        method: form.method,
        buttonCount: form.querySelectorAll('button').length,
        submitButtons: Array.from(form.querySelectorAll('button[type="submit"]')).map(b => ({
          text: b.textContent.trim(),
          type: b.type
        }))
      };
    });

    console.log('   Form info:', JSON.stringify(formInfo, null, 2));

    console.log('\n3️⃣ Filling in credentials...');

    // Try multiple selector strategies
    const emailFilled = await page.evaluate((email) => {
      // Try different selectors
      const selectors = [
        'input[type="email"]',
        'input[name="email"]',
        'input[id*="email"]',
        'input[placeholder*="email" i]'
      ];

      for (const selector of selectors) {
        const input = document.querySelector(selector);
        if (input) {
          input.value = email;
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));
          return { success: true, selector };
        }
      }
      return { success: false };
    }, CONFIG.credentials.email);

    console.log('   Email fill result:', emailFilled);

    const passwordFilled = await page.evaluate((password) => {
      const selectors = [
        'input[type="password"]',
        'input[name="password"]',
        'input[id*="password"]'
      ];

      for (const selector of selectors) {
        const input = document.querySelector(selector);
        if (input) {
          input.value = password;
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));
          return { success: true, selector };
        }
      }
      return { success: false };
    }, CONFIG.credentials.password);

    console.log('   Password fill result:', passwordFilled);

    await page.screenshot({ path: path.join(debugDir, '02-form-filled.png'), fullPage: true });

    console.log('\n4️⃣ Submitting form...');

    // Try clicking submit button
    const submitResult = await page.evaluate(() => {
      const selectors = [
        'button[type="submit"]',
        'form button',
        'button:contains("Submit")',
        'button:contains("Sign In")',
        'button:contains("Login")'
      ];

      // Find button by text content
      const buttons = Array.from(document.querySelectorAll('button'));
      for (const button of buttons) {
        const text = button.textContent.trim().toLowerCase();
        if (text.includes('sign') || text.includes('login') || text.includes('submit')) {
          button.click();
          return { success: true, text: button.textContent.trim() };
        }
      }

      // Try form submit
      const form = document.querySelector('form');
      if (form) {
        form.submit();
        return { success: true, method: 'form.submit()' };
      }

      return { success: false };
    });

    console.log('   Submit result:', submitResult);

    console.log('\n5️⃣ Waiting for navigation and API response...');

    // Wait for navigation or timeout
    try {
      await Promise.race([
        page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 10000 }),
        new Promise(resolve => setTimeout(resolve, 8000))
      ]);
    } catch (e) {
      console.log('   ⚠️  Navigation timeout or no navigation occurred');
    }

    // Additional wait for any async operations
    await new Promise(resolve => setTimeout(resolve, 2000));

    await page.screenshot({ path: path.join(debugDir, '03-after-submit.png'), fullPage: true });

    const currentUrl = page.url();
    console.log(`\n6️⃣ Current URL: ${currentUrl}`);

    // Check for error messages
    const errorMessages = await page.evaluate(() => {
      const errorSelectors = [
        '[class*="error"]',
        '[class*="alert"]',
        '[role="alert"]',
        '.text-red'
      ];

      const errors = [];
      for (const selector of errorSelectors) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
          const text = el.textContent.trim();
          if (text) errors.push({ selector, text });
        });
      }

      return errors;
    });

    if (errorMessages.length > 0) {
      console.log('   ❌ Error messages found:');
      errorMessages.forEach(err => console.log(`      - ${err.text}`));
    }

    // Check if we're logged in
    const isLoggedIn = await page.evaluate(() => {
      // Check for dashboard elements
      const dashboardElements = [
        'aside',
        '[class*="dashboard"]',
        '[class*="sidebar"]'
      ];

      for (const selector of dashboardElements) {
        if (document.querySelector(selector)) {
          return true;
        }
      }

      return false;
    });

    if (isLoggedIn) {
      console.log('   ✅ Successfully logged in!');
    } else if (currentUrl.includes('/login')) {
      console.log('   ❌ Still on login page - login failed');
    } else {
      console.log('   ⚠️  Redirected to:', currentUrl);
    }

    await page.screenshot({ path: path.join(debugDir, '04-final-state.png'), fullPage: true });

    console.log('\n📸 Debug screenshots saved to:', debugDir);
    console.log('   - 01-login-page.png');
    console.log('   - 02-form-filled.png');
    console.log('   - 03-after-submit.png');
    console.log('   - 04-final-state.png');

    // Print network requests
    console.log('\n🌐 Network Requests:');
    const apiRequests = requests.filter(r => r.url.includes('localhost:8000') || r.url.includes('/api'));
    if (apiRequests.length > 0) {
      apiRequests.forEach(req => {
        console.log(`   ${req.method} ${req.url}`);
        if (req.postData) {
          console.log(`      Body: ${req.postData.substring(0, 100)}...`);
        }
      });
    } else {
      console.log('   ⚠️  No API requests detected!');
    }

    // Print responses
    console.log('\n📥 API Responses:');
    const apiResponses = responses.filter(r => r.url.includes('localhost:8000') || r.url.includes('/api'));
    if (apiResponses.length > 0) {
      apiResponses.forEach(resp => {
        const status = resp.ok ? '✅' : '❌';
        console.log(`   ${status} ${resp.status} - ${resp.url}`);
      });
    } else {
      console.log('   ⚠️  No API responses detected!');
    }

    // Print console messages
    if (consoleMessages.length > 0) {
      console.log('\n💻 Browser Console Messages:');
      consoleMessages.forEach(msg => {
        if (msg.type === 'error') {
          console.log(`   ❌ ${msg.text}`);
        } else if (msg.type === 'warning') {
          console.log(`   ⚠️  ${msg.text}`);
        }
      });
    }

    console.log('\n⏳ Keeping browser open for 10 seconds for manual inspection...');
    await new Promise(resolve => setTimeout(resolve, 10000));

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
  }
}

debugLogin().catch(console.error);
