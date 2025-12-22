from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import time
import re

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/attendance', methods=['POST'])
def get_attendance():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    print(f"Starting attendance fetch via Playwright for: {username}")
    
    try:
        with sync_playwright() as p:
            # optimize: use chromium, headless, with specific args for speed
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = browser.new_page()
            
            # 1. Navigate
            print("Navigating...")
            try:
                page.goto("http://mitsims.in/", timeout=60000)
            except Exception as nav_err:
                print(f"Navigation Error: {nav_err}")
                browser.close()
                return jsonify({"error": "Portal Unreachable. The MITS server is taking too long to respond. Please try again."}), 504
            
            # 2. Login Logic
            print("Clicking Student link...")
            # Ensure the link is visible - sometimes waiting for .card works better
            page.wait_for_selector("#studentLink", state="visible")
            page.click("#studentLink", force=True)
            
            print("Entering credentials...")
            # Wait for the student form container to be explicitly visible
            page.wait_for_selector("#stuLogin", state="visible")
            
            # Use specific selectors for the student form to avoid ambiguity with other hidden forms
            # HTML structure: #studentForm -> #inputStuId / #inputPassword
            page.fill("#studentForm #inputStuId", "")
            page.type("#studentForm #inputStuId", username, delay=50)

            page.fill("#studentForm #inputPassword", "")
            page.type("#studentForm #inputPassword", password, delay=50)
            
            print("Submitting...")
            # Try normal click first
            page.click("#studentSubmitButton", force=True)
            
            # 3. Validation
            try:
                # Wait for navigation to dashboard or error
                page.wait_for_selector("#studentName, #studentErrorDiv", timeout=8000)
            except:
                print("Click might not have worked. Trying JS Submit...")
                # Fallback: Submit form directly
                # Robust check: ensure form exists before submitting
                try:
                    page.evaluate("""
                        var form = document.querySelector('#studentForm');
                        if (form) {
                            form.submit();
                        } else {
                            // Try finding form by the button
                            var btn = document.querySelector('#studentSubmitButton');
                            if(btn && btn.form) {
                                btn.form.submit();
                            }
                        }
                    """)
                    # Wait again after JS submit check
                    page.wait_for_selector("#studentName, #studentErrorDiv", timeout=15000)
                except Exception as eval_e:
                     print(f"JS Submit failed or timed out: {eval_e}")
                     # If both failed, we might be stuck or already logged in (race condition)
                     pass

            # Check for specific error message
            error_div = page.query_selector("#studentErrorDiv")
            if error_div:
                err_text = error_div.inner_text().strip()
                if err_text:
                    browser.close()
                    return jsonify({"error": f"Login Error: {err_text}"}), 401

            # Check if we are still on login page by URL or form existence
            if page.query_selector("#studentForm") and not page.query_selector("#studentName"):
                 # Double check URL
                 if "dashboard" not in page.url.lower():
                     browser.close()
                     return jsonify({"error": "Login failed (Still on login page). Please check credentials."}), 401
            
            print("Login Successful, extracting Data...")
            
            # 1. Get all text first (moved up for name extraction scope)
            full_text = page.inner_text("body")
            
            # Extract Student Name and ID
            student_name = ""
            try:
                # Approach 1: Try specific selectors if known
                try:
                    # Common header location
                    header_text = page.inner_text(".header-top") # Example selector
                    if header_text and "|" in header_text:
                         student_name = header_text.split("|")[0].strip()
                except:
                    pass

                # Approach 2: Regex search in full text (very robust for text dumps)
                # Pattern: "NAME   |   Change Password"
                if student_name == "Student" or not student_name:
                    import re
                    # Look for:  Start of line or space -> Name -> | Change Password
                    match = re.search(r"([A-Z\s]+)\s+\|\s+Change Password", full_text)
                    if match:
                        student_name = match.group(1).strip()
                    else:
                        # Fallback: finding name near ID if possible, or sticking to default
                        pass
            except Exception as e:
                print(f"Name extraction error: {e}")

            attendance_data = []

            # STRATEGY D: Robust Line Parsing (Backwards/Forwards Search)
            # We dump the whole body text to find the data wherever it is.
            
            # Wait a moment for dynamic content
            time.sleep(3)
            
            # 1. Get all text
            full_text = page.inner_text("body")
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            
            print(f"DEBUG: Scanning {len(lines)} lines of text for attendance data...")
            
            # Common ExtJS headers to ignore
            IGNORE_PHRASES = ["TOTAL CONDUCTED", "CLASSES ATTENDED", "ATTENDANCE", "SUBJECT CODE", "S.NO", "SUBJECT DETAILS", "SEMESTER ACTIVITY"]
            
            for i, line in enumerate(lines):
                # Skip Headers
                if any(phrase in line.upper() for phrase in IGNORE_PHRASES):
                    continue

                # We are looking for the start of a row.
                # Heuristic 1: Line matches a Subject Code format (e.g. 23HUM102)
                match_subject_code = re.match(r'^\d*[A-Z]+\d+[A-Z0-9]*$', line)
                
                # Heuristic 2: Line is Uppercase Text (Subject Name) longer than 3 chars, no digits
                # e.g. "VERBAL", "CLOUD COMPUTING"
                is_text_subject = (line.isupper() and len(line) > 3 and not re.search(r'\d', line))

                if match_subject_code or is_text_subject:
                    # Potential Subject found at line i.
                    # The numbers (Attended, Conducted, %) should be in the next few lines.
                    # Example sequence:
                    # Line i: VERBAL
                    # Line i+1: 2
                    # Line i+2: 2
                    # Line i+3: 100.0
                    
                    try:
                        # process next 5 lines
                        lookahead = lines[i+1:i+6]
                        numbers_found = []
                        
                        for sub in lookahead:
                            # Match integers or floats (including %) OR Hyphen
                            # e.g. "2", "100.0", "100%", "-"
                            if re.match(r'^[\d\.]+%?$', sub) or sub == '-':
                                val = sub.replace('%', '').replace('-', '0')
                                numbers_found.append(val)
                        
                        # We need at least 3 numbers: Attended, Conducted, Percentage
                        if len(numbers_found) >= 3:
                            attended = numbers_found[0]
                            total = numbers_found[1]
                            percentage = numbers_found[2]
                            
                            # Sanity Check: Total >= Attended and Percentage <= 100
                            # This filters out random noise
                            try:
                                if float(total) >= float(attended) and float(percentage) <= 100.0:
                                    attendance_data.append({
                                        "code": line,
                                        "attended": attended,
                                        "total": total,
                                        "percentage": percentage
                                    })
                            except:
                                pass # formatting error
                                
                    except Exception as e:
                        print(f"Error parsing block at line {i}: {e}")

            browser.close()
            
            print(f"DEBUG: Found {len(attendance_data)} records.")
            return jsonify({
                "message": "Success", 
                "student_name": student_name,
                "data": attendance_data
            })

    except Exception as e:
        print(f"Playwright Error: {e}")
        # Generic user-friendly error as requested
        return jsonify({"error": "Connection timed out or failed. Please try again."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
