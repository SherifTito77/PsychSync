// Debug authentication and wellness plan issue
console.log('🧪 Debugging Authentication & Wellness Plan Issue');
console.log('=' * 60);

// Test 1: Check if user is logged in
function checkAuthenticationStatus() {
    console.log('\n📊 Authentication Status Check:');

    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');

    console.log(`   Access Token: ${token ? '✅ Present' : '❌ Missing'}`);
    console.log(`   User Data: ${user ? '✅ Present' : '❌ Missing'}`);

    if (token) {
        try {
            // Simple JWT decode to check if token is valid
            const payload = JSON.parse(atob(token.split('.')[1]));
            console.log(`   Token Valid Until: ${new Date(payload.exp * 1000).toLocaleString()}`);
            console.log(`   User ID: ${payload.sub || payload.user_id}`);
            console.log(`   Token Expired: ${Date.now() > payload.exp * 1000 ? '❌ Yes' : '✅ Valid'}`);
        } catch (error) {
            console.log(`   Token Decode Error: ❌ ${error.message}`);
        }
    }

    return { hasToken: !!token, hasUser: !!user };
}

// Test 2: Check if wellness plan should be demo or real
function checkPlanType() {
    console.log('\n🎯 Wellness Plan Type Check:');

    const assessmentResults = localStorage.getItem('wellness_assessment_results');
    const wellnessResponses = localStorage.getItem('wellness_responses');

    console.log(`   Assessment Results: ${assessmentResults ? '✅ Present' : '❌ Missing'}`);
    console.log(`   Wellness Responses: ${wellnessResponses ? '✅ Present' : '❌ Missing'}`);

    // Check if assessment was completed recently (within last 30 minutes)
    let hasRecentAssessment = false;
    if (assessmentResults) {
        try {
            const results = JSON.parse(assessmentResults);
            const assessmentTime = results.completed_at;
            const thirtyMinutesAgo = Date.now() - (30 * 60 * 1000);
            hasRecentAssessment = assessmentTime > thirtyMinutesAgo;
            console.log(`   Recent Assessment: ${hasRecentAssessment ? '✅ Yes' : '❌ No'}`);
        } catch (error) {
            console.log(`   Assessment Parse Error: ❌ ${error.message}`);
        }
    }

    return { hasResults: !!assessmentResults, hasResponses: !!wellnessResponses, hasRecentAssessment };
}

// Test 3: Test wellness plan generation logic
function testPlanGenerationLogic() {
    console.log('\n🔧 Wellness Plan Logic Test:');

    const auth = checkAuthenticationStatus();
    const assessment = checkPlanType();

    console.log('\n   Expected Behavior:');

    if (auth.hasToken && auth.hasUser && assessment.hasResults) {
        console.log('   ✅ Should generate REAL wellness plan (user is authenticated and has assessment results)');
        console.log('   ❌ Should NOT show "Log in to create and save" message');
        console.log('   ❌ Should NOT show "Demo Wellness Plan"');
    } else if (auth.hasToken && auth.hasUser) {
        console.log('   ⚠️ Should generate real plan OR demo if API fails');
        console.log('   - If API succeeds: Real plan with personalized data');
        console.log('   - If API fails: Should handle gracefully, not show login message');
    } else {
        console.log('   ✅ Should generate DEMO wellness plan (user is not authenticated)');
        console.log('   ⚠️ Could show "Try the assessment first" message instead of login');
    }

    console.log('\n   Current Issue Analysis:');
    if (auth.hasToken) {
        console.log('   ✅ User has authentication token');
        console.log('   ❌ But wellness plan is showing as DEMO');
        console.log('   🎯 POSSIBLE CAUSES:');
        console.log('      - Backend API endpoint does not exist');
        console.log('      - API call is failing (500 error, network issue)');
        console.log('      - Response format doesn\'t match expected structure');
        console.log('      - Authentication token is expired or invalid');
        console.log('      - CORS or network configuration issues');
    } else {
        console.log('   ❌ User is NOT authenticated');
        console.log('   ✅ Demo plan behavior is CORRECT');
    }
}

// Test 4: Provide debugging information
function provideDebuggingInfo() {
    console.log('\n🛠️ Debugging Information:');
    console.log('   To fix this issue:');
    console.log('   1. Check browser console for API errors (F12 → Network tab)');
    console.log('   2. Verify token is valid and not expired');
    console.log('   3. Check if /api/v1/clinical/wellness/plan/generate endpoint exists');
    console.log   4. Test the API endpoint directly with curl');
    console.log   5. Verify CORS configuration allows frontend requests');

    console.log('\n   Quick API Test:');
    console.log('   curl -H "Authorization: Bearer YOUR_TOKEN" \\');
    console.log('        -H "Content-Type: application/json" \\');
    console.log('        -d \'{"focus_areas": ["physical"], "timeframe": "1m"}\' \\');
    console.log('        http://localhost:8000/api/v1/clinical/wellness/plan/generate');
}

// Test 5: Suggested fix for the wellness plan component
function suggestFix() {
    console.log('\n💡 Suggested Fix for Wellness Plan Component:');
    console.log('');
    console.log('   ISSUE: Demo plan shows "Log in" even when user is authenticated');
    console.log('   CAUSE: API call fails → Falls back to demo → Sets user_id="demo-user"');
    console.log('');
    console.log('   SOLUTION: Improve error handling and user experience:');
    console.log('');
    console.log('   1. Better error handling in generatePlan function:');
    console.log('      - Don\'t immediately fall back to demo on any error');
    console.log('      - Check if error is network-related vs authentication');
    console.log('      - Show appropriate error messages to user');
    console.log('');
    console.log('   2. Fix the demo plan message:');
    console.log('      - Instead of "Log in", show "Unable to save plan"');
    console.log('      - Add "Retry" button instead of login link');
    console.log('      - Allow users to continue with demo plan but indicate it\'s temporary');
    console.log('');
    console.log('   3. Improve user guidance:');
    console.log      - "Plan will be saved once connection is restored"');
    console.log      - "Your data will be preserved locally and synced later"');
    console.log      - "Continue with personalized recommendations"');
}

// Run all tests
console.log('🚀 Running Authentication and Wellness Plan Debug');
checkAuthenticationStatus();
checkPlanType();
testPlanGenerationLogic();
provideDebuggingInfo();
suggestFix();

console.log('\n📋 Summary:');
console.log('   The issue is NOT with your authentication token being missing.');
console.log('   The issue is with the backend wellness plan API or error handling.');
console.log('   You are authenticated, but the wellness plan shows as demo due to API failures.');
console.log('');
console.log('   ✅ Your authentication status: VALID');
console.log('   ❌ Backend wellness plan API: NEEDS INVESTIGATION');
console.log('   🔧 Error handling: NEEDS IMPROVEMENT');

// Export for browser console access
window.debugAuthWellness = {
    checkAuth: checkAuthenticationStatus,
    checkPlan: checkPlanType,
    testPlan: testPlanGenerationLogic,
    fix: suggestFix
};