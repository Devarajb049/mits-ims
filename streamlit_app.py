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
    /* Premium Modern Dark Theme */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e293b 0%, #020617 100%);
        font-family: 'Outfit', sans-serif;
        color: #f8fafc;
    }

    /* Hide Defaults & Anchor Links */
    header[data-testid="stHeader"] { display: none; }
    footer { display: none; }
    #MainMenu { display: none; }
    .stDeployButton { display: none; }
    [data-testid="stToolbar"] { display: none; }
    [data-testid="stDecoration"] { display: none; }
    [data-testid="stStatusWidget"] { display: none; }
    a.anchor-link { display: none !important; }
    .css-15zrgzn { display: none; }

    /* Layout & Scroll Fixes */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 100%;
    }
    
    /* Global Styles - Deep Dark Blue Theme */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0f2e4a 0%, #020617 80%);
        font-family: 'Outfit', sans-serif;
        color: #e2e8f0;
        overflow-x: hidden;
    }

    /* Fixed Width Card with Glow */
    div[data-testid="stForm"] {
        background: #0b1421;
        border: 1px solid #1e293b;
        border-radius: 1.5rem;
        padding: 2.5rem;
        box-shadow: 0 0 40px -10px rgba(56, 189, 248, 0.15); /* Blue Glow */
        width: 100%;
        max-width: 400px; 
        margin: 0 auto;
        position: relative;
    }
    
    /* Inputs */
    .stTextInput > label {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        font-weight: 500;
        margin-bottom: 0.4rem;
    }
    
    .stTextInput > div > div {
        background: #162032;
        border: 1px solid #28354a;
        border-radius: 0.75rem;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input {
        color: white;
        padding: 0.8rem 1rem;
        background-color: transparent !important;
        border: none !important;
    }

    .stTextInput > div > div:focus-within {
        border-color: #38bdf8;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        background: #1a253a;
    }
    
    /* Primary Button - Bright Blue */
    .stButton > button {
        background: linear-gradient(90deg, #0ea5e9 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 0.9rem;
        border-radius: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: none; 
        font-size: 1rem;
        width: 100% !important;
        box-shadow: 0 4px 15px -3px rgba(14, 165, 233, 0.4);
        margin-top: 1.5rem;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -3px rgba(14, 165, 233, 0.5);
    }
    
    /* Logo Container in Header */
    .logo-container {
        display: flex;
        justify-content: center;
        margin-bottom: 1.5rem;
    }
    .logo-circle {
        width: 60px;
        height: 60px;
        background: rgba(14, 165, 233, 0.1);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(14, 165, 233, 0.3);
        box-shadow: 0 0 20px rgba(14, 165, 233, 0.2);
    }

    /* Footer */
    .custom-footer {
        text-align: center;
        padding: 2rem 0;
        color: #475569;
        font-size: 0.75rem;
        border-top: none;
        margin-top: 2rem;
        background: transparent;
    }

    /* Spacers */
    .login-spacer { height: 8vh; display: flex; justify-content: center; }
    @media (min-height: 800px) { .login-spacer { height: 12vh; } }
    
    /* Dashboard Colors & Cards */
    .glass-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #334155;
    }
    
    .border-green { border-left-color: #10b981 !important; background: rgba(16, 185, 129, 0.05); }
    .border-yellow { border-left-color: #f59e0b !important; background: rgba(245, 158, 11, 0.05); }
    .border-red { border-left-color: #ef4444 !important; background: rgba(239, 68, 68, 0.05); }
    
    .text-green { color: #34d399; }
    .text-yellow { color: #fbbf24; }
    .text-red { color: #f87171; }
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
            student_name = ""
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
    st.markdown('<div class="login-spacer"></div>', unsafe_allow_html=True)
    
    # Custom Logo & Header matching the screenshot look
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div class="logo-container">
                <div class="logo-circle">
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="#38bdf8" viewBox="0 0 16 16">
                      <path d="M11.251.068a.5.5 0 0 1 .227.58L9.677 6.5H13a.5.5 0 0 1 .364.843l-8 8.5a.5.5 0 0 1-.842-.49L6.323 9.5H3a.5.5 0 0 1-.364-.843l8-8.5a.5.5 0 0 1 .615-.09z"/>
                    </svg>
                </div>
            </div>
            <h1 style="font-weight: 800; font-size: 1.8rem; color: white; margin-bottom: 0.5rem; letter-spacing: 0.5px; text-transform: uppercase;">SCHOOL PORTAL</h1>
            <p style="color: #64748b; font-size: 0.9rem; font-weight: 400;">Secure Login for Students & Faculty</p>
        </div>
    """, unsafe_allow_html=True)

    """, unsafe_allow_html=True)
    
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
        if st.session_state.user_name:
            st.title(f"Welcome, {st.session_state.user_name}")
        else:
            st.title("Welcome")
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
<div class="aggregate-card">
    <p style="color: #94a3b8; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Aggregate Percentage</p>
    <h1 style="font-size: 3.5rem; font-weight: 700; color: {'#34d399' if overall >= 75 else '#fbbf24' if overall >= 65 else '#f87171'}; margin: 0; line-height: 1;">{overall:.2f}%</h1>
     <p style="color: #64748b; margin-top: 1rem; font-size: 0.875rem;">
        Classes Attended: <b style="color: #f1f5f9">{total_attended}</b> / <span style="color: #94a3b8">{total_conducted}</span>
    </p>
</div>
""", unsafe_allow_html=True)
        
        # Grid for Subjects
        st.subheader("Subject Detailed Report")
        
        for item in data:
            perc = item['percentage']
            
            border_cls = "border-green"
            text_cls = "text-green"
            
            if perc < 75:
                border_cls = "border-yellow"
                text_cls = "text-yellow"
            if perc < 65:
                border_cls = "border-red"
                text_cls = "text-red"
                
            st.markdown(f"""
            <div class="glass-card {border_cls}">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3 style="margin: 0; font-size: 1.1rem; font-weight: 600; color: white;">{item['code']}</h3>
                        <div style="margin-top: 0.5rem; display: flex; align-items: center; gap: 0.75rem;">
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Attended: <b style="color: white;">{item['attended']}</b></span>
                            <span style="width: 4px; height: 4px; background: #475569; border-radius: 50%;"></span>
                            <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Total: <b style="color: white;">{item['total']}</b></span>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.5rem; font-weight: 800; line-height: 1;" class="{text_cls}">{perc}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Footer (Always Visible)
st.markdown("""
<div class="custom-footer">
    <p>&copy; 2025 MITS IMS. All Rights Reserved.</p>
</div>
""", unsafe_allow_html=True)

