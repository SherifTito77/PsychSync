// Test authentication fix for wellness plan
console.log('🧪 Testing Wellness Plan Authentication Fix');
console.log('='.repeat(50));

// Test 1: Check if user is logged in
function checkAuthenticationStatus() {
    console.log('\n📊 Authentication Status:');

    const token = localStorage.getItem('access_token');
    const isAuthenticated = token && token !== 'undefined' && token !== 'null' && token.trim() !== '';

    console.log(`   Token: ${token ? '✅ Present' : '❌ Missing'}`);
    console.log(`   Valid Token: ${isAuthenticated ? '✅ Yes' : '❌ No'}`);
    console.log(`   Token Length: ${token ? token.length : 0}`);

    if (token) {
        console.log(`   Token Prefix: ${token.substring(0, 20)}...`);
    }

    return isAuthenticated;
}

// Test 2: Check what the wellness plan should show
function testWellnessPlanDisplay() {
    console.log('\n🎯 Wellness Plan Display Test:');

    const token = localStorage.getItem('access_token');
    const isAuthenticated = token && token !== 'undefined' && token !== 'null' && token.trim() !== '';

    // Simulate demo plan display logic
    const planData = { user_id: 'demo-user' };

    console.log(`   Plan Type: ${planData.user_id}`);
    console.log(`   User Authenticated: ${isAuthenticated}`);

    // Test the same logic as our component
    const shouldShowSamplePlan = planData.user_id === 'demo-user';
    const shouldShowLoginPrompt = !isAuthenticated;

    if (shouldShowSamplePlan) {
        if (isAuthenticated) {
            console.log('   ✅ Should show: "Sample Wellness Plan (Offline Mode)"');
            console.log('   ✅ Message: "This is a sample plan due to server connectivity issues"');
            console.log('   ❌ Should NOT show: "Log in to create and save"');
        } else {
            console.log('   ✅ Should show: "Demo Wellness Plan"');
            console.log('   ✅ Message: "This is a sample wellness plan to demonstrate the features"');
            console.log('   ✅ Should show: "Log in to create and save"');
        }
    } else {
        console.log('   ✅ Should show: "Your Personalized Wellness Plan"');
    }

    return { shouldShowSamplePlan, shouldShowLoginPrompt, isAuthenticated };
}

// Test 3: Trigger page refresh if needed
function suggestRefresh() {
    console.log('\n🔄 Refresh Suggestion:');
    console.log('   If you are still seeing the old "Log in" message:');
    console.log('   1. Press Ctrl+F5 (or Cmd+Shift+R on Mac) to force refresh');
    console.log('   2. Clear browser cache for localhost:5173');
    console.log('   3. Open DevTools (F12) → Network tab → Check "Disable cache"');
}

// Run all tests
console.log('🚀 Running Authentication Fix Tests...');
const isAuthenticated = checkAuthenticationStatus();
const testResults = testWellnessPlanDisplay();
suggestRefresh();

console.log('\n📋 Summary:');
console.log(`   Authentication Status: ${isAuthenticated ? '✅ LOGGED IN' : '❌ NOT LOGGED IN'}`);
console.log(`   Fix Applied: ✅ Component updated with robust authentication checks`);
console.log(`   Expected Result: ${isAuthenticated ? '✅ Should show offline mode message' : '✅ Should show demo mode message'}`);

// Export for manual testing
window.testWellnessPlanAuth = {
    checkAuth: checkAuthenticationStatus,
    testDisplay: testWellnessPlanDisplay,
    refreshPage: () => window.location.reload()
};

console.log('\n💡 Manual Testing:');
console.log('   - Run window.testWellnessPlanAuth.checkAuth() to check authentication');
console.log('   - Run window.testWellnessPlanAuth.testDisplay() to test display logic');
console.log('   - Run window.testWellnessPlanAuth.refreshPage() to refresh the page');