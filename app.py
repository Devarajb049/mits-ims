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
    
    with sync_playwright() as p:
        browser = None
        try:
            # 1. Launch Browser
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = browser.new_page()
            
            # 2. Navigation
            try:
                page.goto("http://mitsims.in/", timeout=45000)
            except Exception:
                return jsonify({"error": "The MITS server is taking too long to respond. Please try after some time."}), 504
            
            # 3. Open Login Form
            try:
                page.wait_for_selector("#studentLink", state="visible", timeout=15000)
                page.click("#studentLink", force=True)
                page.wait_for_selector("#studentForm #inputStuId", state="visible", timeout=15000)
            except Exception:
                return jsonify({"error": "Connection timed out. Please try after some time."}), 504
            
            # 4. Submit Credentials
            page.fill("#studentForm #inputStuId", username)
            page.fill("#studentForm #inputPassword", password)
            page.click("#studentSubmitButton", force=True)
            
            # 5. Wait for Dashboard or Error
            try:
                page.wait_for_selector("#studentName, #studentErrorDiv", timeout=10000)
            except:
                try:
                    page.evaluate("if(document.querySelector('#studentForm')) document.querySelector('#studentForm').submit();")
                    page.wait_for_selector("#studentName, #studentErrorDiv", timeout=12000)
                except Exception:
                    return jsonify({"error": "Login failed or timed out. Please check your credentials and try after some time."}), 401

            # 6. Check for specific error message
            error_div = page.query_selector("#studentErrorDiv")
            if error_div:
                err_text = ""
                try:
                    err_text = error_div.inner_text().strip()
                except:
                    pass
                if err_text:
                    if any(kw in err_text.lower() for kw in ["invalid", "wrong", "mismatch", "incorrect"]):
                        return jsonify({"error": "Invalid Registration Number or Password"}), 401
                    return jsonify({"error": err_text}), 401

            # Verify if dashboard actually loaded
            if not page.query_selector("#studentName"):
                 return jsonify({"error": "Invalid Registration Number or Password"}), 401
            
            # 7. extraction
            time.sleep(4)
            full_text = page.inner_text("body")
            
            # Name extraction
            student_name = "Student"
            match = re.search(r"([A-Z\s]+)\s+\|\s+Change Password", full_text)
            if match:
                student_name = match.group(1).strip()

            attendance_data = []
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                upper_line = line.upper()
                if "TOTAL CONDUCTED" in upper_line or "ATTENDANCE %" in upper_line:
                    continue

                match_subject_code = re.match(r'^\d*[A-Z]+\d+[A-Z0-9]*$', line)
                is_text_subject = (line.isupper() and len(line) > 3 and not re.search(r'\d', line))

                if match_subject_code or is_text_subject:
                    try:
                        lookahead = lines[i+1:i+6]
                        numbers_found = []
                        for sub in lookahead:
                            if re.match(r'^[\d\.]+%?$', sub) or sub == '-':
                                val = sub.replace('%', '').replace('-', '0')
                                numbers_found.append(val)
                        
                        if len(numbers_found) >= 3:
                            attendance_data.append({
                                "code": line,
                                "attended": numbers_found[0],
                                "total": numbers_found[1],
                                "percentage": numbers_found[2]
                            })
                    except:
                        pass

            return jsonify({
                "message": "Success", 
                "student_name": student_name,
                "data": attendance_data
            })

        except Exception as e:
            err_msg = str(e)
            if "Target page, context or browser has been closed" in err_msg or "Timeout" in err_msg:
                return jsonify({"error": "Connection timed out. Please try after some time."}), 504
            return jsonify({"error": "Something went wrong. Please try after some time."}), 500
        finally:
            if browser:
                try:
                    browser.close()
                except:
                    pass

if __name__ == '__main__':
    app.run(debug=True, port=5000)
