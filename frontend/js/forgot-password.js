const API = "https://bikeservicebooking.onrender.com";

async function sendResetLink() {

    const email = document.getElementById("email").value;

    if (!email) {
        alert("Please enter your email.");
        return;
    }

    try {

        const response = await fetch(
            API + "/password/forgot-password",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: email
                })
            }
        );

        const data = await response.json();

        document.getElementById("message").innerText =
            data.message || data.detail;

    } catch (error) {

        document.getElementById("message").innerText =
            "Server Error";

    }

}