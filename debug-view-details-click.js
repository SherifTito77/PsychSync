// DEBUG: View Details Click Investigation
// Run this in browser console on http://localhost:5174

console.log('🔍 === DEBUGGING VIEW DETAILS CLICK ISSUES ===');

// First, let's check what happens when we manually trigger the state change
function testManualStateChange() {
    console.log('\n🧪 Testing Manual State Change...');

    // Find a wellness goal card to test with
    const goalCards = document.querySelectorAll('[class*="card"]');
    console.log(`Found ${goalCards.length} card elements`);

    if (goalCards.length > 0) {
        // Create a mock goal object for testing
        const mockGoal = {
            id: 'test-goal-1',
            domain: 'physical',
            title: 'Test Physical Wellness Goal',
            description: 'Test description for debugging purposes',
            priority: 'medium',
            current_score: 65,
            target_score: 90,
            action_steps: [
                {
                    id: 'test-step-1',
                    title: 'Test Action Step',
                    description: 'Test step description',
                    category: 'daily',
                    difficulty: 'easy',
                    time_required: '15 minutes',
                    resources: ['Test Resource 1', 'Test Resource 2'],
                    completed: false
                }
            ]
        };

        console.log('🎯 Mock goal created:', mockGoal);

        // Try to manually trigger the detailed view
        setTimeout(() => {
            console.log('🔍 Looking for the detailed view component...');

            // Check if we can find the detailed view after setting selectedGoal
            const detailedView = document.querySelector('[class*="max-w-6xl"]');

            if (detailedView) {
                console.log('✅ Detailed view container found!');
                console.log('📏 Container classes:', detailedView.className);
                console.log('📊 Container content preview:', detailedView.innerHTML.substring(0, 200) + '...');
            } else {
                console.log('❌ No detailed view container found');
                console.log('💡 Possible issues:');
                console.log('   - selectedGoal state not updating');
                console.log('   - Component not re-rendering');
                console.log('   - Conditional rendering not working');
                console.log('   - JavaScript errors blocking execution');
            }
        }, 1000);

        return mockGoal;
    } else {
        console.log('❌ No goal cards found');
        return null;
    }
}

// Check for JavaScript errors
function checkForErrors() {
    console.log('\n⚠️ Checking for JavaScript Errors...');

    // Look for error elements
    const errorElements = document.querySelectorAll('[class*="error"], [class*="Error"]');
    console.log(`Found ${errorElements.length} error elements`);

    if (errorElements.length > 0) {
        errorElements.forEach((error, index) => {
            console.log(`Error ${index + 1}:`, error.textContent);
        });
    }

    // Check for console errors (recent)
    const originalError = console.error;
    const errors = [];
    console.error = (...args) => {
        errors.push(args);
        originalError.apply(console, args);
    };

    setTimeout(() => {
        if (errors.length > 0) {
            console.log('🚨 Recent JavaScript errors:');
            errors.forEach((error, index) => {
                console.log(`  Error ${index + 1}:`, error);
            });
        } else {
            console.log('✅ No JavaScript errors detected');
        }
        console.error = originalError;
    }, 500);
}

// Check React DevTools availability
function checkReactDevTools() {
    console.log('\n🔧 Checking React DevTools...');

    // Try to access React component tree
    try {
        const root = document.getElementById('root');
        if (root) {
            console.log('✅ React root element found');

            // Look for React internals
            if (root._reactRootContainer) {
                console.log('✅ React container found');
                console.log('📊 React version available via DevTools');
            } else {
                console.log('⚠️ React container not found in expected location');
            }
        } else {
            console.log('❌ React root not found');
        }
    } catch (error) {
        console.log('⚠️ React DevTools check failed:', error.message);
    }
}

// Check View Details button state
function checkViewDetailsButtons() {
    console.log('\n🔍 Checking View Details Buttons...');

    const buttons = Array.from(document.querySelectorAll('button')).filter(btn =>
        btn.textContent.toLowerCase().includes('view details') ||
        btn.textContent.toLowerCase().includes('view')
    );

    console.log(`Found ${buttons.length} View Details buttons`);

    if (buttons.length > 0) {
        buttons.forEach((btn, index) => {
            console.log(`\n📋 Button ${index + 1}:`);
            console.log('  Text:', btn.textContent.trim());
            console.log('  Classes:', btn.className);
            console.log('  Has onClick:', !!btn.onclick);
            console.log('  Event listeners:', getEventListeners ? getEventListeners(btn) : 'Not available');

            // Test if button is actually clickable
            const rect = btn.getBoundingClientRect();
            console.log('  Position:', {
                top: rect.top,
                left: rect.left,
                width: rect.width,
                height: rect.height
            });
            console.log('  Visible:', rect.width > 0 && rect.height > 0);
            console.log('  Style display:', window.getComputedStyle(btn).display);
        });

        return buttons;
    } else {
        console.log('❌ No View Details buttons found');
        return [];
    }
}

// Force component re-render check
function forceComponentCheck() {
    console.log('\n🔄 Forcing Component Re-render Check...');

    // Look for wellness-related content
    const wellnessContent = document.querySelectorAll('[class*="wellness"], [class*="Wellness"], [class*="plan"], [class*="assessment"]');
    console.log(`Found ${wellnessContent.length} wellness-related elements`);

    wellnessContent.forEach((element, index) => {
        console.log(`Wellness element ${index + 1}:`, element.className);
    });

    // Check if we need to navigate to the right page
    const pageTitle = document.title;
    console.log('Current page title:', pageTitle);

    if (pageTitle.includes('PsychSync')) {
        console.log('✅ On PsychSync app');
    } else {
        console.log('⚠️ May need to navigate to wellness section');
    }
}

// Main debug function
function debugViewDetails() {
    console.log('🚀 Starting comprehensive View Details debug...');

    // Run all checks
    forceComponentCheck();
    checkForErrors();
    checkReactDevTools();

    setTimeout(() => {
        const buttons = checkViewDetailsButtons();
        const mockGoal = testManualStateChange();

        // Provide final recommendations
        console.log('\n📋 DEBUG RECOMMENDATIONS:');

        if (buttons.length === 0) {
            console.log('❌ ISSUE: No View Details buttons found');
            console.log('💡 SOLUTION: Navigate to wellness plan or assessment results page');
            console.log('🔍 Try: Menu → Assessments → Wellness Assessment → Generate Plan');
        } else if (mockGoal) {
            console.log('✅ Basic functionality detected');
            console.log('💡 NEXT STEP: Manually click a View Details button and check console');
            console.log('🔍 Look for: "SUCCESS: View Details Button X CLICKED!" message');
        } else {
            console.log('⚠️ Mixed results detected');
            console.log('💡 RECOMMENDATION: Run in browser console and manually test');
        }

        console.log('\n🧪 MANUAL TESTING INSTRUCTIONS:');
        console.log('1. Click any View Details button (they should be highlighted)');
        console.log('2. Check console for "SUCCESS" messages');
        console.log('3. Look for detailed view modal appearing');
        console.log('4. Verify AI-powered analytics content');
        console.log('5. Test back navigation functionality');

    }, 2000);
}

// Auto-run the debug
debugViewDetails();

// Make functions available for manual testing
window.debugViewDetails = {
    run: debugViewDetails,
    checkButtons: checkViewDetailsButtons,
    checkErrors: checkForErrors,
    testState: testManualStateChange
};

console.log('\n💻 Debug functions loaded. Run debugViewDetails.run() to re-run all tests.');