document.addEventListener('DOMContentLoaded', async function() {
    // Fetch specializations
    try {
        const response = await fetch('/doctors/specializations');
        const data = await response.json();
        const select = document.getElementById('specialization');
        
        data.specializations.forEach(spec => {
            const option = document.createElement('option');
            option.value = spec;
            option.textContent = spec;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching specializations:', error);
    }

    // Handle form submission
    document.getElementById('doctorRegistrationForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            phone_number: document.getElementById('phoneNumber').value,
            specialization: document.getElementById('specialization').value,
            license_number: document.getElementById('licenseNumber').value
        };

        try {
            const response = await fetch('/doctors/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                alert('Registration submitted successfully! Your application is pending review.');
                window.location.href = '/dashboard.html';
            } else {
                const error = await response.json();
                alert(error.detail || 'Failed to submit registration');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to submit registration');
        }
    });
});