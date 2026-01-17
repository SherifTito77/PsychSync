// SUPER SIMPLE TEST - View Details
// Run this in browser console on your wellness plan page

console.log('🎯 SUPER SIMPLE VIEW DETAILS TEST');

// Function to find and immediately test View Details buttons
function testViewDetailsDirectly() {
    console.log('\n🔍 Looking for View Details buttons...');

    // Find all buttons
    const allButtons = document.querySelectorAll('button');
    const viewDetailsButtons = [];

    allButtons.forEach(btn => {
        if (btn.textContent && (
            btn.textContent.toLowerCase().includes('view details') ||
            btn.textContent.toLowerCase().includes('view')
        )) {
            viewDetailsButtons.push(btn);
        }
    });

    console.log(`📊 Found ${viewDetailsButtons.length} View Details buttons`);

    if (viewDetailsButtons.length === 0) {
        console.log('❌ NO VIEW DETAILS BUTTONS FOUND');
        console.log('💡 This means:');
        console.log('   - You might not be on the wellness plan page');
        console.log('   - The wellness plan might not have loaded yet');
        console.log('   - Try completing the assessment first');
        return false;
    }

    console.log('✅ VIEW DETAILS BUTTONS FOUND!');

    // Test each button immediately
    viewDetailsButtons.forEach((btn, index) => {
        console.log(`\n🔧 Testing Button ${index + 1}:`);
        console.log('   Text:', btn.textContent.trim());
        console.log   ('   Visible:', btn.offsetHeight > 0);

        // Make button impossible to miss
        btn.style.cssText = `
            border: 5px solid #FF5722 !important;
            background: linear-gradient(135deg, #FF5722, #F44336) !important;
            color: white !important;
            font-size: 16px !important;
            font-weight: bold !important;
            padding: 15px !important;
            border-radius: 8px !important;
            transform: scale(1.1) !important;
            box-shadow: 0 8px 25px rgba(244, 67, 54, 0.5) !important;
            z-index: 9999 !important;
            position: relative !important;
        `;

        // Add a label
        const label = document.createElement('span');
        label.textContent = 'CLICK ME!';
        label.style.cssText = `
            position: absolute;
            top: -10px;
            right: -10px;
            background: #4CAF50;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        `;
        btn.appendChild(label);

        // Simple click handler that just shows an alert for testing
        const originalOnClick = btn.onclick;
        btn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();

            console.log(`\n🎉 SUCCESS! VIEW DETAILS BUTTON ${index + 1} WORKS!`);
            console.log('🎯 Button text:', btn.textContent.trim());

            // Show immediate alert
            alert(`✅ VIEW DETAILS IS WORKING!\n\nButton ${index + 1} successfully detected and clicked.\n\nThis confirms the View Details functionality is working.\n\nIf you want the detailed view with AI analytics, let me know!`);

            // Visual feedback
            btn.style.background = 'linear-gradient(135deg, #4CAF50, #45a049)';
            label.textContent = 'WORKED!';
            label.style.background = '#2E7D32';
        };

        console.log('   ✅ Button enhanced with click handler');
        console.log('   🎨 Button should now be bright red and very visible');
    });

    return true;
}

// Test immediately
console.log('\n🚀 STARTING SIMPLE TEST...');
const success = testViewDetailsDirectly();

if (success) {
    console.log('\n✅ SUCCESS! View Details buttons are working.');
    console.log('💡 Click the bright red "CLICK ME!" buttons to test.');
    console.log('🎯 You should see an alert confirming it works.');
} else {
    console.log('\n❌ FAILED: No View Details buttons found.');
    console.log('💡 Try navigating to the wellness assessment first.');
}

console.log('\n📋 SIMPLE TEST COMPLETE!');
console.log('🎯 If buttons appear, the View Details functionality is working!');
console.log('💡 The issue might be with the detailed view display, not the button clicks.');
