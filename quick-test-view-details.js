// Quick View Details Test - Run this in browser console on http://localhost:5174
console.log('🎯 Quick View Details Test Started');

// Test 1: Check if we're on the right page
const currentUrl = window.location.href;
console.log('📍 Current URL:', currentUrl);

if (currentUrl.includes('localhost:5174')) {
    console.log('✅ Correct development server (port 5174)');
} else {
    console.log('⚠️ Not on port 5174, please navigate to http://localhost:5174');
}

// Test 2: Look for wellness plan components
setTimeout(() => {
    console.log('\n🔍 Testing for wellness plan components...');

    // Look for View Details buttons
    const buttons = Array.from(document.querySelectorAll('button')).filter(btn =>
        btn.textContent.toLowerCase().includes('view details')
    );

    console.log(`📋 Found ${buttons.length} View Details buttons`);

    if (buttons.length > 0) {
        buttons.forEach((btn, index) => {
            console.log(`  Button ${index + 1}: Found and ready to test`);

            // Highlight button for visual verification
            btn.style.border = '3px solid #4CAF50';
            btn.style.boxShadow = '0 0 20px rgba(76, 175, 80, 0.5)';

            // Add click listener for testing
            btn.addEventListener('click', () => {
                console.log(`🎉 SUCCESS: View Details button ${index + 1} clicked!`);
                console.log('🔍 Looking for detailed view modal...');

                // Look for modal or detailed view
                setTimeout(() => {
                    const modal = document.querySelector('[class*="modal"], [class*="details"], [style*="fixed"]');
                    if (modal) {
                        console.log('✅ Detailed view modal detected!');
                        console.log('🎯 View Details functionality is working!');
                    } else {
                        console.log('⚠️ Checking for detailed view content...');
                        const detailedView = document.querySelector('[class*="max-w-6xl"]');
                        if (detailedView) {
                            console.log('✅ Detailed view content detected!');
                        } else {
                            console.log('❌ No detailed view found - may need to click a wellness goal first');
                        }
                    }
                }, 500);
            });
        });

        console.log('🎉 View Details buttons are ready! Click any button to test.');

    } else {
        console.log('❌ No View Details buttons found');
        console.log('💡 You may need to navigate to the wellness plan page first');
        console.log('🔍 Look for wellness plan or assessment results');
    }

    // Test 3: Check for wellness plan cards
    const planCards = document.querySelectorAll('[class*="card"], [class*="wellness"], [class*="goal"]');
    console.log(`📊 Found ${planCards.length} wellness-related elements`);

}, 2000);

console.log('\n💡 Instructions:');
console.log('1. Navigate to http://localhost:5174');
console.log('2. Go to wellness plan or assessments section');
console.log('3. Click on "View Details" buttons (they will be highlighted)');
console.log('4. Check console for success messages');
console.log('5. Verify the detailed view appears with AI analytics');
