if (errorMessage) {
    document.getElementById("error-container").style.display = "block";
    document.getElementById("success-container").style.display = "none";
} else {
    document.getElementById("error-container").style.display = "none";
    document.getElementById("success-container").style.display = "block";
}