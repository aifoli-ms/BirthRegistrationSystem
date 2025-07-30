# Ghana e-Birth USSD Service

This is a Flask-based Python application that simulates a USSD service for registering births in Ghana. It provides a menu-driven interface for parents and health workers to submit birth registration details, verify existing registrations, and get help.

The application is designed to be connected to a USSD gateway provider like Africa's Talking for testing and deployment.

## Features

* **Dual Registration Flows:** Separate, tailored menus for Parents/Guardians and Health Workers.
* **Optional Father's Details:** Users can choose whether to include the father's name and National Identification Number (NIN).
* **Input Validation:** Each piece of data entered by the user is validated for correct format and reasonable values.
* **Robust UBRN Generation:** Creates a Unique Birth Registration Number (UBRN) based on region, district, date, and a sequence number, complete with a check digit.
* **Registration Verification:** Allows users to check the status of a registration by entering a UBRN.
* **SMS Notifications:** Simulates sending a confirmation SMS with the UBRN to the user upon successful registration.
* **Help Menu:** Provides information about the service, costs, and contact details.

## Known Issues & Bugs

* **Incomplete Health Worker Flow:** The logic for the Health Worker to add a father's details is currently a placeholder and not fully implemented. The main parent/guardian flow is complete.
* **In-Memory Database:** The application uses a simple Python dictionary as a database. This means all registration data will be **lost** every time the application is restarted. This is for simulation purposes only.
* **Simplified UBRN Sequence:** The function to get the next sequence number for a UBRN is simulated with a random number. In a real system, this would require a database query to prevent duplicate UBRNs.

---

## Setup and Testing Instructions

Follow these steps to run the application locally and test it using the Africa's Talking simulator.

### Step 1: Prerequisites

* Make sure you have **Python 3** installed on your system.
* You will need an account with **Africa's Talking**. You can create a free sandbox account to get started.

### Step 2: Install Dependencies

1.  Open your terminal or command prompt.
2.  Install the required Python library, Flask:
    ```sh
    pip install Flask
    ```

### Step 3: Run the Local Flask Server

1.  Save the application code as a Python file (e.g., `app.py`).
2.  In your terminal, navigate to the directory where you saved the file.
3.  Run the application with the following command:
    ```sh
    python app.py
    ```
4.  You should see output indicating that the server is running on `http://127.0.0.1:8000` or `http://0.0.0.0:8000`. Keep this terminal window open.

### Step 4: Expose Your Local Server with Ngrok

The Africa's Talking platform needs a public URL to send requests to your local application. We will use `ngrok` to create a secure, public URL for our local server.

1.  [Download and install ngrok](https://ngrok.com/download) if you haven't already.
2.  Open a **new** terminal window (leave the Flask server running in the other one).
3.  Run the following command to expose port 8000:
    ```sh
    ngrok http 8000
    ```
4.  `ngrok` will display a public URL, usually ending in `.ngrok-free.app`. It will look something like this: `https://<random-string>.ngrok-free.app`. **Copy this HTTPS URL.**

### Step 5: Configure Africa's Talking

Now, we will tell Africa's Talking to use your `ngrok` URL as the callback for a USSD service.

1.  Log in to your **Africa's Talking Sandbox** account.
2.  In the left-hand menu, go to **USSD** -> **USSD Service Codes**.
3.  Click the **"Create Channel"** button. This will give you a new USSD service code (e.g., `*384*...#`).
4.  In the **Callback URL** field, paste the `ngrok` HTTPS URL you copied earlier, and add `/callback` to the end of it. For example:
    ```
    https://<random-string>.ngrok-free.app/callback
    ```
5.  Click **"Create Channel"**.

### Step 6: Test Using the Simulator

You are now ready to test!

1.  In the Africa's Talking dashboard, go to the **Simulator** section.
2.  Select the **USSD** tab.
3.  Enter your phone number (the sandbox uses a virtual number, so any valid format will do).
4.  In the "USSD String" field, enter the service code you created (e.g., `*384*22441#`).
5.  Click the phone icon to start the session.
6.  The simulator will display the main menu from your Flask application. You can now interact with your USSD service by sending responses through the simulator's input field.

You can now test the full registration and verification flows as if you were using a real phone.
