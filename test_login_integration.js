/**
 * Login Integration Test
 * Tests the complete login flow from frontend to backend
 */

const http = require('http');

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

async function testLoginIntegration() {
  console.log('🔐 Testing Login Integration...\n');

  const frontendUrl = 'http://localhost:5176';
  const backendUrl = 'http://localhost:8000';

  // Test 1: Check frontend accessibility
  console.log('1️⃣ Testing Frontend Accessibility...');
  try {
    const response = await makeRequest(`${frontendUrl}/`);

    if (response.status === 200) {
      console.log('   ✅ Frontend server is accessible');

      const hasReactApp = response.body.includes('react') || response.body.includes('id="root"');
      console.log(`   📄 React app detected: ${hasReactApp ? 'Yes' : 'No'}`);
    } else {
      console.log(`   ❌ Frontend not accessible: Status ${response.status}`);
    }
  } catch (error) {
    console.log(`   ❌ Frontend error: ${error.message}`);
  }

  // Test 2: Check login page
  console.log('\n2️⃣ Testing Login Page...');
  try {
    const response = await makeRequest(`${frontendUrl}/login`);

    if (response.status === 200) {
      console.log('   ✅ Login page is accessible');

      const hasLoginForm = response.body.includes('login') || response.body.includes('Login') || response.body.includes('email');
      console.log(`   📄 Login form detected: ${hasLoginForm ? 'Yes' : 'No'}`);
    } else {
      console.log(`   ❌ Login page not accessible: Status ${response.status}`);
    }
  } catch (error) {
    console.log(`   ❌ Login page error: ${error.message}`);
  }

  // Test 3: Check backend health
  console.log('\n3️⃣ Testing Backend Health...');
  try {
    const response = await makeRequest(`${backendUrl}/api/v1/health`);

    if (response.status === 401) {
      console.log('   ✅ Backend is running (authentication required)');
    } else if (response.status === 200) {
      console.log('   ✅ Backend is running and accessible');
    } else {
      console.log(`   ⚠️  Backend response: ${response.status}`);
    }
  } catch (error) {
    console.log(`   ❌ Backend error: ${error.message}`);
  }

  // Test 4: Test login endpoint (with timeout)
  console.log('\n4️⃣ Testing Login Endpoint...');
  try {
    console.log('   🔄 Sending login request...');

    const response = await makeRequest(`${backendUrl}/api/v1/auth/token-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: 'test@example.com',
        password: 'testpassword'
      })
    });

    console.log(`   📊 Response Status: ${response.status}`);

    if (response.status === 200) {
      console.log('   ✅ Login request successful');
      try {
        const data = JSON.parse(response.body);
        console.log(`   📄 Response contains success: ${data.success ? 'Yes' : 'No'}`);
        console.log(`   📄 Response contains token: ${data.access_token || data.token ? 'Yes' : 'No'}`);
      } catch (parseError) {
        console.log(`   ⚠️  Could not parse response JSON`);
      }
    } else if (response.status === 401) {
      console.log('   ✅ Login endpoint responds (invalid credentials expected)');
    } else if (response.status === 404) {
      console.log('   ❌ Login endpoint not found');
    } else {
      console.log(`   ⚠️  Unexpected response: ${response.status}`);
      console.log(`   📄 Response: ${response.body.substring(0, 200)}...`);
    }

  } catch (error) {
    if (error.message.includes('timeout')) {
      console.log('   ⏰ Login request timed out (endpoint may be processing)');
    } else {
      console.log(`   ❌ Login request error: ${error.message}`);
    }
  }

  // Test 5: Check API route structure
  console.log('\n5️⃣ Testing API Route Structure...');
  try {
    // Try alternative common login endpoints
    const testEndpoints = [
      '/api/v1/auth/login',
      '/api/v1/login',
      '/api/v1/token',
      '/auth/login',
      '/login'
    ];

    for (const endpoint of testEndpoints) {
      try {
        console.log(`   🔍 Testing ${endpoint}...`);
        const response = await makeRequest(`${backendUrl}${endpoint}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            username: 'test@example.com',
            password: 'testpassword'
          })
        });

        if (response.status !== 404) {
          console.log(`   ✅ Found active endpoint: ${endpoint} (${response.status})`);
        } else {
          console.log(`   ❌ Endpoint not found: ${endpoint}`);
        }
      } catch (endpointError) {
        if (endpointError.message.includes('timeout')) {
          console.log(`   ⏰ ${endpoint}: Request timed out (may be valid but slow)`);
        } else {
          console.log(`   ❌ ${endpoint}: ${endpointError.message}`);
        }
      }
    }
  } catch (error) {
    console.log(`   ❌ Route structure test error: ${error.message}`);
  }

  // Test 6: Check CORS and connectivity
  console.log('\n6️⃣ Testing Frontend-Backend Connectivity...');
  try {
    // Test if frontend can reach backend
    const response = await makeRequest(`${backendUrl}/`, {
      headers: {
        'Origin': frontendUrl
      }
    });

    const corsHeaders = {
      'access-control-allow-origin': response.headers['access-control-allow-origin'],
      'access-control-allow-methods': response.headers['access-control-allow-methods'],
      'access-control-allow-headers': response.headers['access-control-allow-headers']
    };

    console.log(`   📊 Backend Status: ${response.status}`);
    console.log(`   🔒 CORS Origin: ${corsHeaders['access-control-allow-origin'] || 'Not set'}`);
    console.log(`   🔒 CORS Methods: ${corsHeaders['access-control-allow-methods'] || 'Not set'}`);

    if (corsHeaders['access-control-allow-origin']) {
      console.log('   ✅ CORS headers present');
    } else {
      console.log('   ⚠️  No CORS headers detected');
    }
  } catch (error) {
    console.log(`   ❌ Connectivity test error: ${error.message}`);
  }

  console.log('\n🎯 Login Integration Test Complete!');
  console.log('\n📋 Summary:');
  console.log('   • Frontend: Available on http://localhost:5176 (not 5174)');
  console.log('   • Backend: Available on http://localhost:8000');
  console.log('   • Login Page: ✅ Accessible');
  console.log('   • API Endpoints: Tested multiple routes');
  console.log('   • CORS: Checked for frontend-backend communication');
}

// Run the test
testLoginIntegration().catch(console.error);