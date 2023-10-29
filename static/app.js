if (errorMessage) {
    document.getElementById("error-container").style.display = "block";
    document.getElementById("success-container").style.display = "none";
    document.getElementById("final-message").textContent = "There was an error";
} else {
    document.getElementById("error-container").style.display = "none";
    document.getElementById("success-container").style.display = "block";
    document.getElementById("final-message").textContent = "Thank you for using our app!";
}