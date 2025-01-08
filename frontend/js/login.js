document.getElementById("login-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const submitButton = document.querySelector("button[type='submit']");
    submitButton.disabled = true;
    submitButton.textContent = "Logging in...";

    try {
        // Create form data (FastAPI OAuth2 expects form data, not JSON)
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

            // Store the token in localStorage
            localStorage.setItem("token", data.access_token);
            console.log("Token stored:", localStorage.getItem("token"));
            alert("Login successful!");

            // Redirect to the dashboard or home page
            window.location.href = "/";
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

// Add this to verify the script is loaded
console.log("Login script loaded successfully");