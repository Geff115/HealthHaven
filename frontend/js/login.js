document.getElementById("login-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const submitButton = document.querySelector("button[type='submit']");
    submitButton.disabled = true;
    submitButton.textContent = "Logging in...";

    try {
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        console.log("Attempting login...");
        const response = await fetch("http://127.0.0.1:8000/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: formData,
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem("token", data.access_token);
            
            // Decode and check token data
            const tokenParts = data.access_token.split('.');
            const tokenPayload = JSON.parse(atob(tokenParts[1]));
            const userRole = tokenPayload.role.toString().toLowerCase();

            // Check role and redirect
            if (userRole === "admin") {
                // Store token and redirect directly
                sessionStorage.setItem('isAdmin', 'true');
                window.location.replace("/admin.html");
            } else {
                window.location.replace("/dashboard.html");
            }
        } else {
            const error = await response.json();
            console.error("Login failed:", error);
            if (response.status === 401) {
                alert("Invalid username or password");
            } else if (response.status === 400) {
                alert(error.detail || "Login failed");
            } else {
                alert("Error: " + (error.detail || "An unknown error occurred"));
            }
        }
    } catch (err) {
        console.error("Error during login:", err);
        alert("Unable to connect to the server. Please try again later.");
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Login";
    }
});