#!/usr/bin/env node

/**
 * Comprehensive Clinical Assessment Routing Validation Test
 * This test validates that the clinical assessment routing fix is working properly
 * for DASS-21, PCL-5, and AUDIT assessments.
 */

const puppeteer = require('puppeteer');

async function validateClinicalRouting() {
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: { width: 1200, height: 800 }
  });

  const page = await browser.newPage();
  const baseUrl = 'http://localhost:5176';

  console.log('🏥 Starting Clinical Assessment Routing Validation...\n');

  try {
    // Test 1: Navigate to Clinical Assessments page
    console.log('1️⃣ Navigating to Clinical Assessments page...');
    await page.goto(`${baseUrl}/clinical-assessments`);
    await page.waitForSelector('h1', { timeout: 10000 });

    const pageTitle = await page.$eval('h1', el => el.textContent);
    console.log(`   ✓ Page title: "${pageTitle}"`);

    // Test 2: Check that DASS-21 assessment is present
    console.log('\n2️⃣ Checking DASS-21 assessment availability...');
    const dass21Exists = await page.$('h3:contains("DASS-21")') !== null;

    // Look for the assessment card with DASS-21
    const dass21Card = await page.evaluate(() => {
      const headers = Array.from(document.querySelectorAll('h3, h4, .card-title'));
      const dass21Header = headers.find(h =>
        h.textContent.includes('DASS-21') ||
        h.textContent.includes('Depression, Anxiety, Stress')
      );
      return !!dass21Header;
    });

    if (dass21Card) {
      console.log('   ✓ DASS-21 assessment found');
    } else {
      console.log('   ❌ DASS-21 assessment not found');
    }

    // Test 3: Check that PCL-5 assessment is present
    console.log('\n3️⃣ Checking PCL-5 assessment availability...');
    const pcl5Card = await page.evaluate(() => {
      const headers = Array.from(document.querySelectorAll('h3, h4, .card-title'));
      const pcl5Header = headers.find(h =>
        h.textContent.includes('PCL-5') ||
        h.textContent.includes('PTSD')
      );
      return !!pcl5Header;
    });

    if (pcl5Card) {
      console.log('   ✓ PCL-5 assessment found');
    } else {
      console.log('   ❌ PCL-5 assessment not found');
    }

    // Test 4: Check that AUDIT assessment is present
    console.log('\n4️⃣ Checking AUDIT assessment availability...');
    const auditCard = await page.evaluate(() => {
      const headers = Array.from(document.querySelectorAll('h3, h4, .card-title'));
      const auditHeader = headers.find(h =>
        h.textContent.includes('AUDIT') ||
        h.textContent.includes('Alcohol Use')
      );
      return !!auditHeader;
    });

    if (auditCard) {
      console.log('   ✓ AUDIT assessment found');
    } else {
      console.log('   ❌ AUDIT assessment not found');
    }

    // Test 5: Test DASS-21 navigation
    console.log('\n5️⃣ Testing DASS-21 assessment navigation...');
    const dass21Navigation = await testAssessmentNavigation(page, 'dass21', baseUrl);
    console.log(`   ${dass21Navigation.success ? '✓' : '❌'} DASS-21 navigation: ${dass21Navigation.message}`);

    // Test 6: Test PCL-5 navigation
    console.log('\n6️⃣ Testing PCL-5 assessment navigation...');
    const pcl5Navigation = await testAssessmentNavigation(page, 'pcl5', baseUrl);
    console.log(`   ${pcl5Navigation.success ? '✓' : '❌'} PCL-5 navigation: ${pcl5Navigation.message}`);

    // Test 7: Test AUDIT navigation
    console.log('\n7️⃣ Testing AUDIT assessment navigation...');
    const auditNavigation = await testAssessmentNavigation(page, 'audit', baseUrl);
    console.log(`   ${auditNavigation.success ? '✓' : '❌'} AUDIT navigation: ${auditNavigation.message}`);

    // Test 8: Verify routing structure in App.tsx
    console.log('\n8️⃣ Verifying routing configuration...');
    const routingValid = await verifyRoutingConfiguration(page, baseUrl);
    console.log(`   ${routingValid.success ? '✓' : '❌'} Routing configuration: ${routingValid.message}`);

    // Summary
    const totalTests = 8;
    const passedTests = [
      dass21Card,
      pcl5Card,
      auditCard,
      dass21Navigation.success,
      pcl5Navigation.success,
      auditNavigation.success,
      routingValid.success
    ].filter(Boolean).length;

    console.log(`\n🎯 Clinical Routing Validation Complete!`);
    console.log(`📊 Results: ${passedTests}/${totalTests} tests passed`);

    if (passedTests === totalTests) {
      console.log('🎉 All clinical assessment routing tests PASSED!');
    } else {
      console.log('⚠️  Some clinical routing tests failed. Check the output above.');
    }

  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
  } finally {
    await browser.close();
  }
}

async function testAssessmentNavigation(page, assessmentId, baseUrl) {
  try {
    // Go back to clinical assessments page
    await page.goto(`${baseUrl}/clinical-assessments`);
    await page.waitForTimeout(1000);

    // Look for the specific assessment and click its start button
    const navigationSuccess = await page.evaluate((id) => {
      const headers = Array.from(document.querySelectorAll('h1, h2, h3, h4, .card-title, [data-testid]'));

      // Find the assessment card for this specific assessment
      const assessmentHeader = headers.find(h => {
        const text = h.textContent.toLowerCase();
        if (id === 'dass21') return text.includes('dass-21') || text.includes('depression, anxiety, stress');
        if (id === 'pcl5') return text.includes('pcl-5') || text.includes('ptsd');
        if (id === 'audit') return text.includes('audit') || text.includes('alcohol');
        return false;
      });

      if (!assessmentHeader) return { success: false, message: 'Assessment not found' };

      // Find the containing card and look for start button
      const card = assessmentHeader.closest('.card, .assessment-card, [class*="card"], [class*="assessment"]');
      if (!card) return { success: false, message: 'Assessment card not found' };

      const startButton = card.querySelector('button, [role="button"], a, [data-testid*="start"]');
      if (!startButton) return { success: false, message: 'Start button not found' };

      // Click the start button
      startButton.click();
      return { success: true, message: 'Start button clicked' };

    }, assessmentId);

    if (!navigationSuccess.success) {
      return navigationSuccess;
    }

    // Wait for navigation
    await page.waitForNavigation({ timeout: 5000 }).catch(() => {});

    // Check current URL
    const currentUrl = page.url();
    console.log(`   📍 Current URL after navigation: ${currentUrl}`);

    // Verify we're on the correct assessment route
    const expectedPattern = new RegExp(`${baseUrl}/clinical/assessment/${assessmentId}/`);
    const isCorrectRoute = expectedPattern.test(currentUrl);

    if (isCorrectRoute) {
      return { success: true, message: `Successfully navigated to ${assessmentId} assessment` };
    } else {
      return { success: false, message: `Incorrect route. Expected pattern: ${expectedPattern}, Got: ${currentUrl}` };
    }

  } catch (error) {
    return { success: false, message: `Navigation error: ${error.message}` };
  }
}

async function verifyRoutingConfiguration(page, baseUrl) {
  try {
    // Test direct navigation to assessment routes
    const testRoutes = [
      `${baseUrl}/clinical/assessment/dass21/start`,
      `${baseUrl}/clinical/assessment/pcl5/start`,
      `${baseUrl}/clinical/assessment/audit/start`
    ];

    for (const route of testRoutes) {
      await page.goto(route, { timeout: 5000 });
      const currentUrl = page.url();

      // Check if we get a 404 or error
      const hasError = await page.evaluate(() => {
        return document.body.textContent.includes('404') ||
               document.body.textContent.includes('Not Found') ||
               document.title.includes('404');
      });

      if (hasError) {
        return { success: false, message: `Route ${route} leads to 404 error` };
      }
    }

    return { success: true, message: 'All assessment routes are accessible' };

  } catch (error) {
    return { success: false, message: `Routing verification error: ${error.message}` };
  }
}

// Run the validation
validateClinicalRouting().catch(console.error);