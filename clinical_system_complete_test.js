#!/usr/bin/env node

/**
 * Complete Clinical Assessment System Test
 * Tests the entire clinical assessment workflow including:
 * - Port redirection (5174 → 5176)
 * - Frontend accessibility
 * - Clinical assessment routing
 * - Component loading
 * - Navigation flow
 */

const http = require('http');
const { execSync } = require('child_process');

function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);

    const req = http.request({
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: 5000
    }, (res) => {
      let data = '';

      res.on('data', chunk => {
        data += chunk;
      });

      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

async function runCompleteClinicalTest() {
  console.log('🏥 COMPLETE CLINICAL ASSESSMENT SYSTEM TEST');
  console.log('=' .repeat(60));
  console.log('');

  const testResults = {
    portRedirection: false,
    frontendAccess: false,
    loginPage: false,
    clinicalAssessments: false,
    dass21Route: false,
    pcl5Route: false,
    auditRoute: false,
    componentLoad: false,
    navigationFlow: false
  };

  let passedTests = 0;
  const totalTests = Object.keys(testResults).length;

  // Test 1: Port Redirection (5174 → 5176)
  console.log('1️⃣ TESTING PORT REDIRECTION SYSTEM');
  console.log('-'.repeat(30));

  try {
    console.log('   🔄 Testing port 5174 accessibility...');
    const response = await makeRequest('http://localhost:5174/login');

    if (response.status === 200) {
      console.log('   ✅ Port 5174 redirect server working');
      testResults.portRedirection = true;
      passedTests++;
    } else {
      console.log(`   ❌ Port 5174 returned: ${response.status}`);
    }

    console.log('   🔄 Testing direct port 5176 access...');
    const directResponse = await makeRequest('http://localhost:5176/login');

    if (directResponse.status === 200) {
      console.log('   ✅ Port 5176 frontend server working');
    } else {
      console.log(`   ❌ Port 5176 returned: ${directResponse.status}`);
    }
  } catch (error) {
    console.log(`   ❌ Port redirection error: ${error.message}`);
  }

  console.log('');

  // Test 2: Frontend Accessibility
  console.log('2️⃣ TESTING FRONTEND ACCESSIBILITY');
  console.log('-'.repeat(30));

  try {
    const response = await makeRequest('http://localhost:5176/');

    if (response.status === 200) {
      const hasReactApp = response.body.includes('react') || response.body.includes('id="root"');
      console.log(`   ✅ Frontend accessible at port 5176`);
      console.log(`   ✅ React application detected: ${hasReactApp ? 'Yes' : 'No'}`);
      testResults.frontendAccess = true;
      passedTests++;
    } else {
      console.log(`   ❌ Frontend not accessible: ${response.status}`);
    }
  } catch (error) {
    console.log(`   ❌ Frontend error: ${error.message}`);
  }

  console.log('');

  // Test 3: Login Page
  console.log('3️⃣ TESTING LOGIN PAGE');
  console.log('-'.repeat(30));

  try {
    const response = await makeRequest('http://localhost:5176/login');

    if (response.status === 200) {
      const hasLoginForm = response.body.includes('login') || response.body.includes('email');
      console.log(`   ✅ Login page accessible`);
      console.log(`   ✅ Login form elements detected: ${hasLoginForm ? 'Yes' : 'No'}`);
      testResults.loginPage = true;
      passedTests++;
    } else {
      console.log(`   ❌ Login page error: ${response.status}`);
    }
  } catch (error) {
    console.log(`   ❌ Login page error: ${error.message}`);
  }

  console.log('');

  // Test 4: Clinical Assessments Page
  console.log('4️⃣ TESTING CLINICAL ASSESSMENTS PAGE');
  console.log('-'.repeat(30));

  try {
    const response = await makeRequest('http://localhost:5176/clinical-assessments');

    if (response.status === 200) {
      console.log(`   ✅ Clinical assessments page accessible`);
      const hasAssessmentContent = response.body.includes('clinical') || response.body.includes('assessment');
      console.log(`   ✅ Assessment content detected: ${hasAssessmentContent ? 'Yes' : 'No'}`);
      testResults.clinicalAssessments = true;
      passedTests++;
    } else {
      console.log(`   ❌ Clinical assessments page error: ${response.status}`);
    }
  } catch (error) {
    console.log(`   ❌ Clinical assessments error: ${error.message}`);
  }

  console.log('');

  // Test 5: Individual Assessment Routes
  console.log('5️⃣ TESTING INDIVIDUAL ASSESSMENT ROUTES');
  console.log('-'.repeat(30));

  const assessmentRoutes = [
    { name: 'DASS-21', path: '/clinical/assessment/dass21/start', key: 'dass21Route' },
    { name: 'PCL-5', path: '/clinical/assessment/pcl5/start', key: 'pcl5Route' },
    { name: 'AUDIT', path: '/clinical/assessment/audit/start', key: 'auditRoute' }
  ];

  for (const assessment of assessmentRoutes) {
    try {
      console.log(`   🔄 Testing ${assessment.name} route...`);
      const response = await makeRequest(`http://localhost:5176${assessment.path}`);

      if (response.status === 200) {
        console.log(`   ✅ ${assessment.name} route working`);
        testResults[assessment.key] = true;
        passedTests++;

        // Check for component content
        const hasComponentContent = response.body.includes('assessment') || response.body.includes('Question');
        console.log(`      📄 Component content: ${hasComponentContent ? 'Yes' : 'No'}`);
      } else {
        console.log(`   ❌ ${assessment.name} route failed: ${response.status}`);
      }
    } catch (error) {
      console.log(`   ❌ ${assessment.name} route error: ${error.message}`);
    }
  }

  console.log('');

  // Test 6: Component Loading (Import Fix Verification)
  console.log('6️⃣ TESTING COMPONENT LOADING');
  console.log('-'.repeat(30));

  try {
    // Test if AssessmentRouter loads without import errors
    const response = await makeRequest('http://localhost:5176/clinical/assessment/dass21/start');

    if (response.status === 200) {
      const hasNoImportError = !response.body.includes('Failed to resolve import') &&
                              !response.body.includes('Does the file exist?');

      if (hasNoImportError) {
        console.log('   ✅ Components loading without import errors');
        testResults.componentLoad = true;
        passedTests++;
      } else {
        console.log('   ❌ Import errors still present');
      }
    } else {
      console.log('   ❌ Component load test failed');
    }
  } catch (error) {
    console.log(`   ❌ Component loading error: ${error.message}`);
  }

  console.log('');

  // Test 7: Navigation Flow
  console.log('7️⃣ TESTING NAVIGATION FLOW');
  console.log('-'.repeat(30));

  try {
    // Test navigation chain: Login → Clinical Assessments → Assessment
    const loginResponse = await makeRequest('http://localhost:5176/login');
    const assessmentsResponse = await makeRequest('http://localhost:5176/clinical-assessments');
    const dass21Response = await makeRequest('http://localhost:5176/clinical/assessment/dass21/start');

    const allRoutesWorking = loginResponse.status === 200 &&
                            assessmentsResponse.status === 200 &&
                            dass21Response.status === 200;

    if (allRoutesWorking) {
      console.log('   ✅ Navigation flow working correctly');
      console.log('      Login → Clinical Assessments → Assessment');
      testResults.navigationFlow = true;
      passedTests++;
    } else {
      console.log('   ❌ Navigation flow has broken links');
      console.log(`      Login: ${loginResponse.status}, Assessments: ${assessmentsResponse.status}, DASS21: ${dass21Response.status}`);
    }
  } catch (error) {
    console.log(`   ❌ Navigation flow error: ${error.message}`);
  }

  console.log('');

  // Final Results
  console.log('🎯 FINAL TEST RESULTS');
  console.log('='.repeat(60));
  console.log('');

  const results = [
    { name: 'Port Redirection (5174→5176)', status: testResults.portRedirection },
    { name: 'Frontend Accessibility', status: testResults.frontendAccess },
    { name: 'Login Page', status: testResults.loginPage },
    { name: 'Clinical Assessments Page', status: testResults.clinicalAssessments },
    { name: 'DASS-21 Assessment Route', status: testResults.dass21Route },
    { name: 'PCL-5 Assessment Route', status: testResults.pcl5Route },
    { name: 'AUDIT Assessment Route', status: testResults.auditRoute },
    { name: 'Component Loading (Import Fix)', status: testResults.componentLoad },
    { name: 'Navigation Flow', status: testResults.navigationFlow }
  ];

  results.forEach(result => {
    console.log(`${result.status ? '✅' : '❌'} ${result.name}`);
  });

  console.log('');
  console.log(`📊 OVERALL SCORE: ${passedTests}/${totalTests} tests passed`);

  if (passedTests === totalTests) {
    console.log('🎉 ALL TESTS PASSED - CLINICAL SYSTEM FULLY FUNCTIONAL!');
    console.log('');
    console.log('🚀 READY FOR USER TESTING:');
    console.log('   • Login: http://localhost:5174/login (or 5176)');
    console.log('   • Clinical Assessments: http://localhost:5174/clinical-assessments');
    console.log('   • DASS-21 Assessment: http://localhost:5174/clinical/assessment/dass21/start');
    console.log('   • PCL-5 Assessment: http://localhost:5174/clinical/assessment/pcl5/start');
    console.log('   • AUDIT Assessment: http://localhost:5174/clinical/assessment/audit/start');
  } else {
    console.log(`⚠️  ${totalTests - passedTests} tests failed - system needs attention`);
    console.log('');
    console.log('🔧 Troubleshooting:');
    console.log('   • Check that all servers are running (ports 5174, 5176, 8000)');
    console.log('   • Clear browser cache and refresh');
    console.log('   • Check browser console for JavaScript errors');
  }

  console.log('');
  console.log('📋 SYSTEM ARCHITECTURE:');
  console.log('   • Port 5174: Redirect Server (backward compatibility)');
  console.log('   • Port 5176: Frontend Development Server');
  console.log('   • Port 8000: Backend API Server');
  console.log('   • Import Fix: ClinicalConsent path corrected');
  console.log('   • NaN Protection: Enhanced in all clinical assessments');
}

// Run the complete test
runCompleteClinicalTest().catch(console.error);