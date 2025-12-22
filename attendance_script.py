import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def calculate_attendance():
    print("--- MITS IMS Attendance Calculator ---")
    username = input("Enter your Register Number: ")
    password = input("Enter your Password: ")

    print("\nStarting Browser...")
    
    # Setup Chrome Driver
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Uncomment to run in background
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # 1. Navigate to MITS IMS
        print("Navigating to mitsims.in...")
        driver.get("http://mitsims.in/")

        # 2. Click on Student Login
        # Based on previous analysis: button/link is 'Student'
        wait = WebDriverWait(driver, 10)
        
        # Click the "Student" link/button
        # Finding by text usually works best for these portals
        try:
             student_link = wait.until(EC.element_to_be_clickable((By.ID, "studentLink")))
             student_link.click()
        except:
            print("Could not find ID 'studentLink', trying by text...")
            student_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Student')]")
            student_link.click()

        # 3. Enter Credentials
        print("Logging in...")
        user_field = wait.until(EC.visibility_of_element_located((By.ID, "inputStuId")))
        pass_field = driver.find_element(By.ID, "inputPassword")
        submit_btn = driver.find_element(By.ID, "studentSubmitButton")

        user_field.clear()
        user_field.send_keys(username)
        pass_field.clear()
        pass_field.send_keys(password)
        submit_btn.click()

        # 4. Wait for Login to complete
        # We wait for the URL to change or a specific element (like 'Dashboard' or 'Logout')
        time.sleep(3) # Basic wait for transition

        if "login" in driver.current_url.lower():
            print("Login might have failed. Please check your credentials.")
            input("Press Enter to close browser...")
            return

        print("Login Successful!")
        print("Analyzing Attendance...")

        # NOTE: Since we don't know the exact internal structure, we will look for common tables.
        # This part tries to find a table with attendance data.
        
        # Heuristic: Look for tables and print their headers to help identify
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        found_data = False
        
        for table in tables:
            headers = [th.text.lower() for th in table.find_elements(By.TAG_NAME, "th")]
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            # Check if this looks like an attendance table
            if any(x in headers for x in ['subject', 'course', 'attended', 'total', '%', 'percentage']):
                print("\n--- Attendance Data Found ---")
                
                total_classes_overall = 0
                total_attended_overall = 0
                
                # Print Header
                header_text = [th.text for th in table.find_elements(By.TAG_NAME, "th")]
                print(" | ".join(header_text))
                
                for row in rows[1:]: # Skip header
                    cols = row.find_elements(By.TAG_NAME, "td")
                    col_text = [c.text for c in cols]
                    
                    if col_text:
                        print(" | ".join(col_text))
                        
                        # Try to sum up if numbers exist
                        # Assuming structure often implies columns for Total and Attended
                        # This avoids complex regex for now and just prints user data
                        
                found_data = True
                print("-----------------------------")

        if not found_data:
            print("\nCould not automatically identify the attendance table.")
            print("The page is open. Please check the attendance manually.")
            
        print("\nProcess Complete.")
        input("Press Enter to close the browser...")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    calculate_attendance()
