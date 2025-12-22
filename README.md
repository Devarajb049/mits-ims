# MITS IMS Attendance Portal

A modern, glassmorphism-styled web application to view your MITS IMS attendance.

## Prerequisites

- Python 3.x
- Chrome Browser installed

## Installation

1.  Open this folder in your terminal.
2.  Install dependencies:
    ```bash
    pip install flask flask-cors selenium webdriver_manager
    ```

## Usage

1.  Run the application:
    ```bash
    python app.py
    ```
2.  Open your browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

3.  Enter your Register Number and Password.
4.  The app will fetch and display your attendance percentage for each subject.

## Features

-   **Secure**: Runs locally on your machine.
-   **Automated**: Uses Selenium to log in and scrape data.
-   **Modern UI**: Beautiful glassmorphism design.
