###Online Voting System with Fingerprint and OTP Authentication
This project is an online voting system designed to facilitate secure and authenticated voting using both fingerprint and OTP (One-Time Password) authentication methods. The system is built using Django, a high-level Python web framework.

Features
User Authentication:

Registration and login using university ID and password.
Two-factor authentication options:
Fingerprint authentication (integrated with device fingerprint sensor).
OTP authentication via SMS/Email.

Voting Process:
Once authenticated, users can vote for candidates of their choice.
Ensures each user can only vote once in each category using unique identifiers tied to each voter.

Admin Interface:
Secure admin panel to manage users and candidates.
Provides oversight of voting activities and results.

Technologies Used
Backend:
Django: Web framework for rapid development and security features.

Frontend:
HTML/CSS/JavaScript/Bootstrap: Frontend technologies for interface development.
Bootstrap: Frontend framework for responsive design.

Database:
SQLite3: Database systems used for storing user data, candidate information, and voting records.
