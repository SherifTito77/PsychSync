#!/bin/bash
# Clear Browser Tokens Script
# Run these commands in your browser's Developer Console (F12)

echo "Open your browser's Developer Console (F12 or Cmd+Option+I)"
echo "Then copy and paste these commands:"

cat << 'EOF'
// 1. Clear all tokens and user data
localStorage.clear();
sessionStorage.clear();

// 2. Clear any specific tokens
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
localStorage.removeItem('user');

// 3. Clear any cached data
if ('caches' in window) {
  caches.keys().then(names => {
    names.forEach(name => caches.delete(name));
  });
}

// 4. Reload the page
console.log('✅ All tokens cleared! Reloading...');
setTimeout(() => location.reload(), 1000);
EOF

echo ""
echo "Then go to http://localhost:5173/login and log in again."
