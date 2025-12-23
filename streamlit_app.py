import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
import time
import re
import subprocess
import sys

# Page Configuration
st.set_page_config(
    page_title="MITS IMS Attendance",
    page_icon="🎓",
    layout="centered", # centering for login feel
    initial_sidebar_state="collapsed"
)

# Custom Styling to Match the User's Premium Dark Theme
st.markdown("""
    <style>
    /* Global Styles */
    .stApp {
        background-color: #020617;
        color: white;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Login Box Styling */
    .css-1544g2n {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 2rem;
        border-radius: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: rgba(59, 130, 246, 0.05); /* Blue tint */
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 0.75rem;
    }
    
    /* Button */
    .stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 0.75rem;
        width: 100%;
        border: none;
        padding: 0.75rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #1d4ed8;
        transform: scale(1.02);
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Custom Card for Subject */
    .subject-card {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #3b82f6; /* Default Blue */
        transition: background-color 0.2s;
    }
    .subject-card:hover {
        background-color: rgba(255, 255, 255, 0.08);
    }
    .status-green { border-left-color: #10b981; }
    .status-yellow { border-left-color: #f59e0b; }
    .status-red { border-left-color: #ef4444; }
    
    .percentage-text {
        font-size: 1.5rem;
        font-weight: bold;
        float: right;
    }
    .green-text { color: #34d399; }
    .yellow-text { color: #fbbf24; }
    .red-text { color: #f87171; }
    
    </style>
    """, unsafe_allow_html=True)

# Install Playwright Dependencies (Cached)
@st.cache_resource
def install_browsers():
    try:
        # Check if we can run playwright
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Failed to install Playwright browsers: {e}")

install_browsers()

# Logic to fetch attendance (Adapted from original app.py)
def fetch_attendance(username, password):
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = browser.new_page()
            
            # Navigate
            page.goto("http://mitsims.in/", timeout=60000)
            
            # Login
            page.wait_for_selector("#studentLink", state="visible")
            page.click("#studentLink", force=True)
            
            page.wait_for_selector("#stuLogin", state="visible")
            page.fill("#studentForm #inputStuId", "")
            page.type("#studentForm #inputStuId", username, delay=50)
            page.fill("#studentForm #inputPassword", "")
            page.type("#studentForm #inputPassword", password, delay=50)
            
            page.click("#studentSubmitButton", force=True)
            
            # Validation
            try:
                page.wait_for_selector("#studentName, #studentErrorDiv", timeout=8000)
            except:
                # Fallback JS Submit
                page.evaluate("""
                    var form = document.querySelector('#studentForm');
                    if (form) form.submit();
                """)
                page.wait_for_selector("#studentName, #studentErrorDiv", timeout=15000)

            # Check Errors
            error_div = page.query_selector("#studentErrorDiv")
            if error_div:
                err_text = error_div.inner_text().strip()
                if err_text:
                    browser.close()
                    return {"error": err_text}
            
            # Custom wait to ensure table loads
            time.sleep(4)

            # Check Login Success
            if "dashboard" not in page.url.lower() and not page.query_selector("#studentName"):
                 browser.close()
                 return {"error": "Login failed (Still on login page). Check credentials."}

            # Extract Data
            full_text = page.inner_text("body")
            
            # Name
            student_name = "Student"
            try:
                match = re.search(r"([A-Z\s]+)\s+\|\s+Change Password", full_text)
                if match:
                    student_name = match.group(1).strip()
            except:
                pass
                
            # Parse Attendance
            attendance_data = []
            
            # Optimized parsing logic
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            IGNORE_PHRASES = ["TOTAL CONDUCTED", "CLASSES ATTENDED", "ATTENDANCE", "SUBJECT CODE", "S.NO", "SUBJECT DETAILS", "SEMESTER ACTIVITY"]
            
            for i, line in enumerate(lines):
                if any(phrase in line.upper() for phrase in IGNORE_PHRASES):
                    continue
                
                match_subject_code = re.match(r'^\d*[A-Z]+\d+[A-Z0-9]*$', line)
                is_text_subject = (line.isupper() and len(line) > 3 and not re.search(r'\d', line))
                
                if match_subject_code or is_text_subject:
                    try:
                        lookahead = lines[i+1:i+6]
                        numbers = []
                        for sub in lookahead:
                            if re.match(r'^[\d\.]+%?$', sub) or sub == '-':
                                val = sub.replace('%', '').replace('-', '0')
                                numbers.append(float(val))
                        
                        if len(numbers) >= 3:
                            # Usually: Attended, Total, Percentage
                            # Or: Total, Attended, Percentage?
                            # Standard format: Attended, Conducted, %
                            # Verification: Total >= Attended
                            attended = numbers[0]
                            total = numbers[1]
                            percentage = numbers[2]
                            
                            # Sometimes orders are swapped, let's heuristic
                            # If first number > second number, swap? No, Attended <= Total.
                            if attended > total:
                                # swap? depends on portal columns. Assuming logic from app.py is correct:
                                # app.py line 200: attended=numbers_found[0], total=numbers_found[1]
                                pass
                                
                            if total >= attended and percentage <= 100.0:
                                attendance_data.append({
                                    "code": line,
                                    "attended": int(attended),
                                    "total": int(total),
                                    "percentage": percentage
                                })
                    except:
                        pass
            
            browser.close()
            return {
                "success": True, 
                "name": student_name, 
                "data": attendance_data, 
                "debug_text": full_text[:2000] if not attendance_data else ""
            }
            
        except Exception as e:
            return {"error": f"Connection Error: {str(e)}"}


# --- UI LAYOUT ---

# State Management
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'data' not in st.session_state:
    st.session_state.data = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

# Login Screen
if not st.session_state.logged_in:
    st.title("MITS IMS Portal")
    st.markdown("<p style='color: #94a3b8;'>Secure Attendance Access</p>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Registration Number", placeholder="e.g. 21691A0...")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Get Attendance")
        
        if submitted:
            if not username or not password:
                st.warning("Please enter both ID and Password")
            else:
                with st.spinner("Connecting to MITS Portal..."):
                    result = fetch_attendance(username, password)
                    
                if "error" in result:
                    st.error(result['error'])
                else:
                    st.session_state.logged_in = True
                    st.session_state.data = result['data']
                    st.session_state.user_name = result['name']
                    st.session_state.debug_text = result.get('debug_text', "")
                    st.rerun()

# Dashboard Screen
else:
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"Welcome, {st.session_state.user_name}")
    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.data = None
            st.rerun()

    data = st.session_state.data
    
    if not data:
        st.info("No attendance data found. The page might not have loaded correctly.")
        if st.session_state.get('debug_text'):
            with st.expander("Show Debug Info (Send this to developer)"):
                st.code(st.session_state.debug_text)
    else:
        # Statistics
        total_attended = sum(d['attended'] for d in data)
        total_conducted = sum(d['total'] for d in data)
        overall = (total_attended / total_conducted * 100) if total_conducted > 0 else 0
        
        # Color for overall
        color = "green" if overall >= 75 else "yellow" if overall >= 65 else "red"
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); border-radius: 20px; padding: 20px; text-align: center; margin-bottom: 30px;">
            <p style="color: #94a3b8; letter-spacing: 2px;">AGGREGATE PERCENTAGE</p>
            <h1 style="font-size: 4rem; color: {'#34d399' if overall >= 75 else '#fbbf24' if overall >= 65 else '#f87171'}; margin: 0;">{overall:.2f}%</h1>
            <p style="color: #cbd5e1; margin-top: 10px;">
                Classes: <b style="color:white">{total_attended}</b> / <b style="color:white">{total_conducted}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Grid for Subjects
        st.subheader("Subject Detailed Report")
        
        for item in data:
            perc = item['percentage']
            status_class = "status-green"
            text_class = "green-text"
            
            if perc < 75:
                status_class = "status-yellow"
                text_class = "yellow-text"
            if perc < 65:
                status_class = "status-red"
                text_class = "red-text"
                
            st.markdown(f"""
            <div class="subject-card {status_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0; font-size: 1.1rem; color: white;">{item['code']}</h3>
                        <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #94a3b8;">
                            Attended: <b style="color: white;">{item['attended']}</b> / {item['total']}
                        </p>
                    </div>
                    <div>
                        <span class="percentage-text {text_class}">{perc}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

