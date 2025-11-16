// Auto-Login Bookmarklet for PsychSync
// Create a bookmark with this URL to auto-login instantly

javascript:(function(){
    const email = 'test@example.com';
    const password = 'password';

    fetch('http://localhost:8000/api/v1/token', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`
    })
    .then(response => response.json())
    .then(data => {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify({
            email: 'test@example.com',
            full_name: 'Test User',
            is_active: true,
            id: 'bbc97a1b-211c-4f02-994d-011d94170647'
        }));
        alert('✅ Auto-login successful! Refreshing page...');
        location.reload();
    })
    .catch(error => {
        alert('❌ Auto-login failed. Make sure backend is running on localhost:8000');
        console.error('Login error:', error);
    });
})();