// Bookmarklet: View Details Test
// Copy this code and create a bookmark with it as the URL
// javascript:(function(){ /* Full test code here */

(function() {
    console.log('🎯 View Details Quick Test - Started');

    // Highlight View Details buttons
    const buttons = Array.from(document.querySelectorAll('button')).filter(btn =>
        btn.textContent.toLowerCase().includes('view details') ||
        btn.textContent.toLowerCase().includes('view')
    );

    if (buttons.length > 0) {
        console.log(`✅ Found ${buttons.length} View Details buttons`);

        // Highlight each button
        buttons.forEach((btn, index) => {
            btn.style.border = '3px solid #4CAF50';
            btn.style.boxShadow = '0 0 15px rgba(76, 175, 80, 0.6)';

            // Add click handler for testing
            btn.addEventListener('click', (e) => {
                console.log(`🎉 View Details Button ${index + 1} CLICKED SUCCESSFULLY!`);
                alert(`✅ View Details Button ${index + 1} Working!`);
            });

            // Add number label
            const label = document.createElement('span');
            label.textContent = `TEST ${index + 1}`;
            label.style.cssText = `
                position: absolute;
                top: -10px;
                right: -10px;
                background: #4CAF50;
                color: white;
                padding: 2px 6px;
                border-radius: 50%;
                font-size: 10px;
                font-weight: bold;
                z-index: 1000;
            `;
            btn.style.position = 'relative';
            btn.appendChild(label);
        });

        // Show results
        const resultDiv = document.createElement('div');
        resultDiv.innerHTML = `
            <div style="
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4CAF50;
                color: white;
                padding: 15px;
                border-radius: 8px;
                z-index: 10000;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                max-width: 300px;
            ">
                <strong>✅ View Details Test Complete!</strong><br>
                Found ${buttons.length} buttons<br>
                Click any button to test<br>
                <small>Check console for details</small><br>
                <button onclick="this.parentElement.remove()" style="
                    background: white;
                    color: #4CAF50;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    margin-top: 10px;
                    cursor: pointer;
                ">Close</button>
            </div>
        `;
        document.body.appendChild(resultDiv);

        console.log('🎉 View Details buttons highlighted and ready for testing!');
        alert(`✅ Found ${buttons.length} View Details buttons! They are now highlighted. Click any to test.`);

    } else {
        console.log('❌ No View Details buttons found');
        alert('❌ No View Details buttons found on this page');
    }

})();
