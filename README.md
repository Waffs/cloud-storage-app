# cloud-storage-app

A cloud-based platform where users can securely store and manage their files, including videos, documents, pictures, and more.
Our service offers free and subscription-based plans to meet the diverse storage needs of our users.


# Project Description 

+ **Title:** Cloud Storage App
+ **Live Demo:** https://youtu.be/BMizSHzITyA

## Features
+ **File Types Supported:** Store various file types, including videos, documents, images, and other formats.
+ **User-Friendly Interface:** Easy-to-use interface for uploading, organizing, and managing files.
+ **Cloud-Based:** Access your files from anywhere, anytime with internet connectivity.

### Flexible Storage Plans:
+ **Free Plan:** 5 GB of free cloud storage.
+ **Subscription Plans:** Paid plans offer up to 200 GB of storage, ideal for users with more extensive storage requirements.


## Tech Stack
+ Frontend: HTML, CSS, JavaScript
+ Backend: Python, Firebase (for authentication and storage)

## Code files description


+ **main.py**
  This file contains the app main logic. 
  It is a Python code which defines a Flask web application that allows users to authenticate with their Google account and interact with Google Drive.The file imports necessary libraries for Flask, Google OAuth, and Google Drive API integration. It sets up a secret key for session management and specifies the permissions required to access Google Drive. Main.py includes helper functions for managing OAuth tokens, refreshing them when expired, and logging requests and responses for debugging purposes. Basic error handling is also in place, particularly for server errors, which are logged and returned as a 500 error response.

+ **Sign-Up and Login Scripts:**
    You'll find the Sign-up and Login scripts in the logic folder.
    The JavaScript code handles user authentication using Firebase for both sign-up and login pages.
    In the sign-up process, users can create an account with their email and password. If successful, the user is shown a success message and redirected to the login page. If there’s an error, the user sees a corresponding error message (e.g., "No user found").
    In the login process, users enter their email and password. If successful, the user is logged in and redirected to the file upload page. Error messages are also shown if the credentials are incorrect

+ **Templates**
    The Template folder typically contains files that define the structure of this web app. 
    This includes the home, signup, login and addfile pages.

   * **/Index.html** 
    This file contains code that creates the structure and content of the homepage for the cloud storage service.
    It includes a hero section with a welcome message and buttons to sign up or log in. The features section highlights the benefits like fast uploads and unlimited storage. The pricing section displays different storage plans (Free, Pro, Business), and a testimonials section showing user feedback. Finally, the footer includes links to the Privacy Policy, Terms of Service, and social media accounts.

    * **/addfile.html**
    This file contains code that enables users to upload files

+ **Css folder**
 This folder contains the styling code. 
 While the landing page features bright colors, the rest of the pages have a simple design.


## Contributing
We welcome contributions to improve the app! If you'd like to contribute, follow these steps:

Fork the repository.
Create a new branch for your feature or bug fix.
Commit your changes.
Push the branch and create a Pull Request.


