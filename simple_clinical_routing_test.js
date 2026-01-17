/**
 * Simple Clinical Assessment Routing Test
 * Tests the key routing functionality without requiring external dependencies
 */

const http = require('http');

function makeRequest(url) {
  return new Promise((resolve, reject) => {
    const options = new URL(url);

    const req = http.request({
      hostname: options.hostname,
      port: options.port,
      path: options.pathname + options.search,
      method: 'GET',
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

    req.end();
  });
}

async function testClinicalRoutes() {
  const baseUrl = 'http://localhost:5176';

  console.log('🏥 Testing Clinical Assessment Routes...\n');

  const testRoutes = [
    {
      name: 'Clinical Assessments Page',
      path: '/clinical-assessments',
      expected: 200
    },
    {
      name: 'DASS-21 Assessment Start',
      path: '/clinical/assessment/dass21/start',
      expected: 200
    },
    {
      name: 'PCL-5 Assessment Start',
      path: '/clinical/assessment/pcl5/start',
      expected: 200
    },
    {
      name: 'AUDIT Assessment Start',
      path: '/clinical/assessment/audit/start',
      expected: 200
    },
    {
      name: 'Clinical Consent',
      path: '/clinical/consent',
      expected: 200
    }
  ];

  let passedTests = 0;
  let totalTests = testRoutes.length;

  for (const test of testRoutes) {
    try {
      console.log(`📍 Testing ${test.name}: ${test.path}`);

      const response = await makeRequest(`${baseUrl}${test.path}`);

      if (response.status === test.expected) {
        console.log(`   ✅ PASS - Status ${response.status}`);
        passedTests++;
      } else {
        console.log(`   ❌ FAIL - Expected ${test.expected}, got ${response.status}`);
      }

      // Check if response contains key elements
      if (response.status === 200 && response.body.length > 0) {
        if (test.path.includes('clinical-assessments')) {
          const hasAssessments = response.body.includes('DASS-21') ||
                               response.body.includes('PCL-5') ||
                               response.body.includes('AUDIT');
          console.log(`   📄 Content: ${hasAssessments ? 'Contains assessments' : 'Missing assessments'}`);
        }
      }

    } catch (error) {
      console.log(`   ❌ ERROR - ${error.message}`);
    }

    console.log(''); // Empty line for readability
  }

  // Summary
  console.log(`🎯 Clinical Routing Test Results:`);
  console.log(`📊 ${passedTests}/${totalTests} tests passed`);

  if (passedTests === totalTests) {
    console.log('🎉 All clinical routing tests PASSED!');
    console.log('✅ The clinical assessment routing fix is working correctly.');
  } else {
    console.log('⚠️  Some routing tests failed.');
    console.log('❌ Check the frontend server and routing configuration.');
  }

  return passedTests === totalTests;
}

// Run the test
testClinicalRoutes().catch(console.error);
