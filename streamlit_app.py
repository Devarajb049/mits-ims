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
    header[data-testid="stHeader"] { background: transparent; }
    footer { display: none; }
    #MainMenu { display: none; }
    a.anchor-link { display: none !important; }
    .css-15zrgzn { display: none; }

    /* Fixed Width & Responsive Container */
    div[data-testid="stForm"] {
        background: #1e293b; /* Solid Obsidian */
        border: 1px solid #334155;
        border-radius: 1.25rem;
        padding: 2.5rem;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
        
        /* Fixed Constrains */
        width: 100%;
        max-width: 420px; 
        margin: 0 auto; /* Center Horizontal */
        display: block;
    }

    /* Inputs - Merged Container */
    .stTextInput > div > div {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 0.75rem;
        transition: all 0.2s ease;
    }
    
    /* Clear default input styles */
    .stTextInput > div > div > input {
        background-color: transparent !important;
        border: none !important;
        color: #f8fafc;
        padding: 0.8rem 1rem;
    }

    /* Focus State */
    .stTextInput > div > div:focus-within {
        border-color: #60a5fa;
        background: #020617;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
    }

    /* Mobile Responsiveness */
    @media (max-width: 480px) {
        div[data-testid="stForm"] {
            padding: 1.5rem;
            border-radius: 1rem;
            max-width: 100%;
        }
        .stApp {
            background: #020617;
        }
        h1 { font-size: 2rem !important; }
    }

    /* Helper for vertical centering */
    .login-spacer {
        height: 10vh;
        display: flex;
        justify-content: center;
    }
    @media (min-height: 800px) {
        .login-spacer { height: 15vh; }
    }
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
    st.markdown("""
        <div style="text-align: center; margin-bottom: 3rem;">
            <h1 style="font-weight: 800; font-size: 3.5rem; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; letter-spacing: -1px;">MITS IMS</h1>
            <p style="color: #94a3b8; font-size: 1.1rem; font-weight: 300;">Secure Attendance Portal</p>
        </div>
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

