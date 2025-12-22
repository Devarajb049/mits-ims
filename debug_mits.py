from playwright.sync_api import sync_playwright
import time

def debug_login():
    username = "25695A0514"
    password = "Deva@514"
    
    print("Debugging login for:", username)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Navigating...")
            page.goto("http://mitsims.in/", timeout=60000)
            
            print("Clicking Student link...")
            page.click("#studentLink")
            
            print("Filling credentials...")
            page.fill("#inputStuId", username)
            page.fill("#inputPassword", password)
            page.click("#studentSubmitButton")
            
            print("Waiting for dashboard...")
            state = "networkidle"
            try:
                page.wait_for_load_state(state, timeout=15000)
            except:
                print("Network idle wait timed out, proceeding...")

            # Wait a bit more for potential JS rendering
            time.sleep(5)
            
            # Check where we are
            print("Current URL:", page.url)
            print("Taking screenshot...")
            page.screenshot(path="debug_dashboard.png")
            
            print("Saving HTML...")
            with open("debug_dashboard.html", "w", encoding="utf-8") as f:
                f.write(page.content())
                
            print("Done. Files saved.")
            
        except Exception as e:
            print("Error:", e)
        finally:
            browser.close()

if __name__ == "__main__":
    debug_login()
