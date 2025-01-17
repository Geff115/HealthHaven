// Handle reset password request
if (document.getElementById('reset-request-form')) {
    document.getElementById('reset-request-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;

        try {
            const response = await fetch('http://127.0.0.1:8000/auth/request-password-reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            if (response.ok) {
                alert('If your email is registered, you will receive a password reset link shortly.');
                window.location.href = 'login.html';
            } else {
                const data = await response.json();
                alert(data.detail || 'An error occurred');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred. Please try again later.');
        }
    });
}

// Handle password reset
if (document.getElementById('password-reset-form')) {
    // Verify token when page loads
    async function verifyToken() {
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token) {
            alert('Reset token is missing');
            window.location.href = 'login.html';
            return;
        }

        try {
            const response = await fetch(`http://127.0.0.1:8000/auth/verify-reset-token/${token}`);
            if (!response.ok) {
                alert('Invalid or expired reset token');
                window.location.href = 'login.html';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred. Please try again later.');
            window.location.href = 'login.html';
        }
    }

    // Call verifyToken when page loads
    verifyToken();

    document.getElementById('password-reset-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const newPassword = document.getElementById('new-password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (newPassword !== confirmPassword) {
            alert('Passwords do not match');
            return;
        }

        // Get token from URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token) {
            alert('Reset token is missing');
            return;
        }

        try {
            const response = await fetch('http://127.0.0.1:8000/auth/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token,
                    new_password: newPassword
                }),
            });

            if (response.ok) {
                alert('Password successfully reset');
                window.location.href = 'login.html';
            } else {
                const data = await response.json();
                alert(data.detail || 'An error occurred');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred. Please try again later.');
        }
    });
}