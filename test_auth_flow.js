// Simple test script to verify frontend-backend authentication flow
const axios = require('axios');

async function testAuthFlow() {
    console.log('🔍 Testing Authentication Flow...\n');

    try {
        // Test 1: Check backend health
        console.log('1. Testing backend health...');
        const healthResponse = await axios.get('http://localhost:8000/api/v1/auth/test-simple');
        console.log('✅ Backend health:', healthResponse.data);

        // Test 2: Test simplified token endpoint
        console.log('\n2. Testing simplified token endpoint...');
        const tokenResponse = await axios.post('http://localhost:8000/api/v1/simple-token', {}, {
            headers: { 'Content-Type': 'application/json' }
        });
        console.log('✅ Token response:', tokenResponse.data);

        // Test 3: Verify frontend accessibility
        console.log('\n3. Testing frontend accessibility...');
        const frontendResponse = await axios.get('http://localhost:5175');
        console.log('✅ Frontend accessible (status:', frontendResponse.status, ')');

        console.log('\n🎉 All tests passed! Authentication flow is ready.');

    } catch (error) {
        console.error('❌ Test failed:', error.message);
        if (error.response) {
            console.error('Response status:', error.response.status);
            console.error('Response data:', error.response.data);
        }
    }
}

testAuthFlow();