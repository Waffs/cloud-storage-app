import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.13.1/firebase-auth.js";

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyDp-qg3U1f9F24uobLpDV06Oeuj0O23Xk0",
    authDomain: "filestorageapp-35a72.firebaseapp.com",
    projectId: "filestorageapp-35a72",
    storageBucket: "filestorageapp-35a72.appspot.com",
    messagingSenderId: "855189446763",
    appId: "1:855189446763:web:bd9daa8f4f5c3d2c18512e",
    measurementId: "G-L7P0K5VX66"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

document.addEventListener("DOMContentLoaded", function () {

     //authentication error messages
    function errorMessages(errorCode) {
        switch (errorCode) { 
            case "auth/user-not-found":
                return "No user found with this email.";
            case "auth/wrong-password":
                return "Incorrect password. Please try again.";
            case "auth/invalid-credential":
                return "Invalid details. Please sign up.";
            default:
                return "An error occurred. Please try again.";
        }
    }



//SIGN UP PAGE
    // Check if signup form exists and handle signup
    const signupForm = document.getElementById('signupForm'); 
    const signupMessage = document.getElementById('signup-message'); 

    if (signupForm) {
        console.log("Signup form found");
        signupForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // Clear previous messages
            signupMessage.textContent = "";
            signupMessage.classList.remove("success", "error");
            signupMessage.style.display = "none"; 

            createUserWithEmailAndPassword(auth, email, password)
                .then((userCredential) => {
                    const user = userCredential.user;

                    // Display success message
                    signupMessage.textContent = "Signup successful!";
                    signupMessage.classList.add("success");
                    signupMessage.style.display = "block"; 

                    setTimeout(() => {
                        window.location.href = "login.html"; // Redirect to login page
                    }, 2000);
                })
                .catch((error) => {
                     const errorMessage = errorMessages(error.code);
                    // error message
                    signupMessage.textContent = errorMessage;
                    signupMessage.classList.add("error");
                    signupMessage.style.display = "block"; 
                });
        });
    }

//LOGIN PAGE


    // Check if login form exists and handle login
    const loginForm = document.getElementById('loginForm');
    const loginMessage = document.getElementById('login-message'); 

    

    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

             // Clear previous messages
             loginMessage.textContent = "";
             loginMessage.classList.remove("success", "error");
             loginMessage.style.display = "none"; 

            signInWithEmailAndPassword(auth, email, password)
                .then((userCredential) => {
                    const user = userCredential.user;
                    //sucess message
                    loginMessage.textContent = "login successful!";
                    loginMessage.classList.add("success");
                    loginMessage.style.display = "block"; 
                    setTimeout(() => {
                        window.location.href = "upload.html"; // Redirect to login page
                    }, 2000);
                })
                .catch((error) => {
                    const errorMessage = errorMessages(error.code);
                    // error message
                    loginMessage.textContent = errorMessage;
                    loginMessage.classList.add("error");
                    loginMessage.style.display = "block"; 
                });
        });
    }
});
