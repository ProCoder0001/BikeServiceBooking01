const API = "https://bikeservicebooking.onrender.com";

async function resetPassword() {

    const params = new URLSearchParams(window.location.search);

    const token = params.get("token");

    const password =
        document.getElementById("password").value;

    const confirm =
        document.getElementById("confirm_password").value;

    if (!password || !confirm) {
        alert("Please fill all fields.");
        return;
    }

    if (password !== confirm) {
        alert("Passwords do not match.");
        return;
    }

    try {

        const response = await fetch(
            API + "/password/reset-password",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    token: token,
                    password: password
                })
            }
        );

        const data = await response.json();

        document.getElementById("message").innerText =
            data.message || data.detail;

        if (response.ok) {

            alert("Password updated successfully!");

            window.location.href = "login.html";

        }

    } catch (error) {

        document.getElementById("message").innerText =
            "Server Error";

    }

}