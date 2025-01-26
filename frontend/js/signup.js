document.getElementById("signup-form").addEventListener("submit", async function(event) {
    event.preventDefault(); // Prevent the form from reloading the page

    const firstName = document.getElementById("first_name").value;
    const lastName = document.getElementById("last_name").value;
    const dob = document.getElementById("dob").value;
    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const city = document.getElementById("city").value;
    const state = document.getElementById("state").value;
    const country = document.getElementById("country").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;

    // Password validations
    if (password !== confirmPassword) {
        alert("Passwords do not match!");
        return;
    }

    if (password.length < 8) {
        alert("Password must be at least 8 characters long.");
        return;
    }

    // Validating email with regex
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert("Please enter a valid email address.");
        return;
    }

    // username validations
    if (username.length < 3) {
        alert("Username must be at least 3 characters.");
        return;
    }

    const payload = {
        username: username,
        email: email,
        password: password,
        first_name: firstName,
        last_name: lastName,
        dob: dob,
        city: city,
        state: state,
        country: country
    };

    const submitButton = document.querySelector("button[type='submit']");
    submitButton.disabled = true;
    submitButton.textContent = "Processing...";

    try {
        const response = await fetch("http://127.0.0.1:8000/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            alert("Registration successful!");
            window.location.href = "login.html";
        } else {
            const error = await response.json();
            if (response.status === 400) {
                // Handling specific error cases from FastAPI backend
                if (error.detail === "Username already exists") {
                    alert("This username is already taken. Please choose another.");
                } else if (error.detail === "Email already exists") {
                    alert("This email is already registered. Please use another email.");
                } else {
                    alert(error.detail);
                }
            } else {
                alert("Error: " + (error.detail || "An unknown error occurred."));
            }
        }
    } catch (err) {
        console.error("Error during registration:", err);
        alert("Unable to connect to the server. Please try again later.");
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Sign Up";
    }
});