// Check if user is logged in
function isLoggedIn() {
    return localStorage.getItem("token") !== null;
}

// Logout function
async function logout() {
    try {
        const response = await fetch("http://127.0.0.1:8000/auth/logout", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            }
        });

        if (response.ok) {
            // Clear the token from localStorage
            localStorage.removeItem("token");
            // Redirect to login page
            window.location.href = "login.html";
        } else {
            alert("Logout failed. Please try again.");
        }
    } catch (error) {
        console.error("Error during logout:", error);
        alert("An error occurred during logout.");
    }
}

// Add event listener to logout button if it exists
document.addEventListener("DOMContentLoaded", function() {
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", logout);
    }
});