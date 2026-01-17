// Debug localStorage for wellness plan authentication
console.log('🔍 Debugging localStorage Authentication');
console.log('='.repeat(50));

// Check all authentication-related items
console.log('\n📊 localStorage Contents:');
for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && (key.includes('token') || key.includes('auth') || key.includes('user'))) {
        const value = localStorage.getItem(key);
        console.log(`   ${key}: ${value ? value.substring(0, 50) + (value.length > 50 ? '...' : '') : 'null'}`);
        console.log(`     Length: ${value ? value.length : 0}`);
        console.log(`     Type: ${typeof value}`);
        if (value) {
            console.log(`     Starts with: ${value.substring(0, 10)}...`);
        }
    }
}

// Test authentication detection exactly like our component
console.log('\n🧪 Authentication Test:');
const token = localStorage.getItem('access_token');
console.log(`   Raw token: ${token}`);
console.log(`   Token exists: ${!!token}`);
console.log(`   Token type: ${typeof token}`);
console.log(`   Token === "undefined": ${token === 'undefined'}`);
console.log(`   Token === "null": ${token === 'null'}`);
console.log(`   Token trimmed length: ${token ? token.trim().length : 0}`);

// Test our exact logic
const isAuthenticated = token && token !== 'undefined' && token !== 'null' && token.trim() !== '';
console.log(`   Is Authenticated: ${isAuthenticated}`);
console.log(`   Should show login: ${!isAuthenticated}`);

// Check other possible token keys
const possibleKeys = ['access_token', 'token', 'auth_token', 'jwt_token', 'user_token'];
console.log('\n🔑 Checking other possible token keys:');
possibleKeys.forEach(key => {
    const value = localStorage.getItem(key);
    if (value) {
        console.log(`   ✅ Found ${key}: ${value.substring(0, 20)}...`);
    } else {
        console.log(`   ❌ No ${key}`);
    }
});

// Force update the component's behavior
console.log('\n🔧 Fix Attempt:');
if (!isAuthenticated && localStorage.length > 0) {
    console.log('⚠️ User appears logged in but token detection failed');
    console.log('🔍 Checking for alternative auth indicators...');

    // Check if user exists even without token
    const userData = localStorage.getItem('user');
    if (userData) {
        console.log('✅ Found user data - user is logged in');
        console.log('🔧 Setting override flag...');
        localStorage.setItem('user_authenticated_override', 'true');
    }
}

console.log('\n📋 Immediate Fix:');
console.log('   If token exists but detection fails, the component should:');
console.log('   1. Check for user data as fallback');
console.log('   2. Look for session cookies');
console.log('   3. Use context-based authentication');

// Export for browser console use
window.debugAuth = {
    checkToken: () => localStorage.getItem('access_token'),
    checkUser: () => localStorage.getItem('user'),
    setOverride: () => localStorage.setItem('user_authenticated_override', 'true'),
    clearOverride: () => localStorage.removeItem('user_authenticated_override')
};

console.log('\n💡 Manual commands:');
console.log('   window.debugAuth.checkToken() - Check token');
console.log('   window.debugAuth.checkUser() - Check user data');
console.log('   window.debugAuth.setOverride() - Set authentication override');
console.log('   window.debugAuth.clearOverride() - Clear override');
