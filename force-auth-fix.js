// Force authentication fix for wellness plan
console.log('🔧 Force Authentication Fix');
console.log('='.repeat(40));

// Method 1: Check current state
function checkAuth() {
    console.log('\n📊 Current Authentication State:');

    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');

    console.log(`   access_token: ${token ? '✅ Present' : '❌ Missing'}`);
    console.log(`   user data: ${userData ? '✅ Present' : '❌ Missing'}`);

    if (token) {
        console.log(`   Token length: ${token.length}`);
        console.log(`   Token starts: ${token.substring(0, 20)}...`);
    }

    if (userData) {
        try {
            const parsed = JSON.parse(userData);
            console.log(`   User email: ${parsed.email || 'missing'}`);
            console.log(`   User ID: ${parsed.id || 'missing'}`);
        } catch (e) {
            console.log('   User data: Invalid JSON');
        }
    }

    // Test the exact same logic as our component
    const isAuthenticated =
        (token && token !== 'undefined' && token !== 'null' && token.trim() !== '') ||
        (userData && userData !== 'undefined' && userData !== 'null' && userData.trim() !== '');

    console.log(`   Component should show: ${isAuthenticated ? 'Sample Plan (Offline Mode)' : 'Demo Plan with Login'}`);

    return isAuthenticated;
}

// Method 2: Force override if user is logged in but detection fails
function forceAuthOverride() {
    console.log('\n🔧 Forcing Authentication Override...');

    // Set override flag
    localStorage.setItem('user_authenticated_override', 'true');
    console.log('✅ Override flag set');

    // Also ensure user data exists
    const userData = localStorage.getItem('user');
    if (!userData) {
        // Create minimal user data if missing
        const fallbackUser = {
            id: 'logged-in-user',
            email: 'user@example.com',
            name: 'Logged In User'
        };
        localStorage.setItem('user', JSON.stringify(fallbackUser));
        console.log('✅ Fallback user data created');
    }

    console.log('🔄 Refresh the page to see the fix');
}

// Method 3: Clear override if needed
function clearAuthOverride() {
    console.log('\n🗑️ Clearing Authentication Override...');
    localStorage.removeItem('user_authenticated_override');
    console.log('✅ Override cleared');
}

// Immediate fix
console.log('\n🚀 Applying Immediate Fix:');

const isCurrentlyAuth = checkAuth();

if (!isCurrentlyAuth && localStorage.length > 0) {
    console.log('⚠️ User appears logged in but detection failed');
    console.log('🔧 Applying authentication override...');
    forceAuthOverride();
} else if (isCurrentlyAuth) {
    console.log('✅ Authentication detection working correctly');
} else {
    console.log('❌ No authentication indicators found');
    console.log('💡 User may need to log in first');
}

// Export for manual use
window.wellnessAuthFix = {
    check: checkAuth,
    force: forceAuthOverride,
    clear: clearAuthOverride
};

console.log('\n💡 Manual commands:');
console.log('   wellnessAuthFix.check() - Check authentication state');
console.log('   wellnessAuthFix.force() - Force authentication override');
console.log('   wellnessAuthFix.clear() - Clear override');
console.log('\n🔄 After running these commands, refresh the page to see changes');