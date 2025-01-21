document.addEventListener("DOMContentLoaded", async () => {
    // Show loading state
    const form = document.getElementById("updateProfileForm");
    form.style.opacity = "0.6";

    try {
        const response = await fetch("/users/me", {  // Add /users prefix
            headers: {
                Authorization: `Bearer ${localStorage.getItem("token")}`,
                "Content-Type": "application/json"
            },
        });

        if (response.status === 401) {
            // Handle unauthorized access
            window.location.href = "/login.html";
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Prefill form fields with null checks
        const fields = ["email", "first_name", "last_name", "city", "state", "country"];
        fields.forEach(field => {
            const element = document.getElementById(field);
            if (element) {
                element.value = data[field] || "";
            }
        });

    } catch (error) {
        console.error("Error fetching user data:", error);
        showNotification("Failed to load profile data. Please try again later.", "error");
    } finally {
        form.style.opacity = "1";
    }
});

document.getElementById("updateProfileForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const submitButton = e.target.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = "Updating...";

    const userData = {};
    // Only include fields that have values
    ["email", "first_name", "last_name", "city", "state", "country"].forEach(field => {
        const value = document.getElementById(field).value.trim();
        if (value) {
            userData[field] = value;
        }
    });

    try {
        const response = await fetch("/users/me", {  // Add /users prefix
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
            body: JSON.stringify(userData),
        });

        if (response.status === 401) {
            window.location.href = "/login.html";
            return;
        }

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to update profile");
        }

        const data = await response.json();
        showNotification("Profile updated successfully!", "success");
        
    } catch (error) {
        console.error("Error updating profile:", error);
        showNotification(error.message || "Failed to update profile. Please try again later.", "error");
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Update Profile";
    }
});

// Profile picture handling
const profilePicture = document.getElementById('profilePicture');
const pictureInput = document.getElementById('pictureInput');

// Update profile picture when loaded
function updateProfilePicture(data) {
    if (data.profile_picture) {
        profilePicture.src = data.profile_picture;
    }
}

// Handle file selection
pictureInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type and size
    if (!file.type.startsWith('image/')) {
        showNotification('Please select an image file.', 'error');
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        showNotification('File size should be less than 5MB.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/users/me/profile-picture', {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${localStorage.getItem('token')}`,
            },
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Failed to upload profile picture');
        }

        const data = await response.json();
        profilePicture.src = data.file_path;
        showNotification('Profile picture updated successfully!', 'success');
    } catch (error) {
        console.error('Error uploading profile picture:', error);
        showNotification('Failed to upload profile picture. Please try again.', 'error');
    }
});

// Add preview before upload
pictureInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            profilePicture.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});

// Update the fetch user data function to handle profile picture
async function fetchUserData() {
    try {
        const response = await fetch('/users/me', {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });

        if (response.ok) {
            const data = await response.json();
            // Update profile picture
            updateProfilePicture(data);
            // ... rest of your existing field updates ...
        }
    } catch (error) {
        console.error('Error fetching user data:', error);
    }
}

// Helper function for notifications
function showNotification(message, type = "success") {
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}