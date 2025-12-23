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

# Custom Styling
st.markdown("""
    <style>
    /* Global Reset & Theme */
    .stApp {
        background: #020617; /* Deep Navy/Black base */
        font-family: 'Outfit', sans-serif;
        color: #e2e8f0;
        overflow-x: hidden;
    }
    
    /* Hide Defaults & Floating Elements */
    header[data-testid="stHeader"], footer, #MainMenu, .stDeployButton, 
    [data-testid="stToolbar"], [data-testid="stDecoration"], 
    [data-testid="stStatusWidget"], a.anchor-link, .css-15zrgzn, 
    [data-testid="stFooter"], [class*="viewerBadge"] { 
        display: none !important; 
        visibility: hidden !important;
        height: 0 !important;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #020617; 
    }
    ::-webkit-scrollbar-thumb {
        background: #334155; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569; 
    }

    /* Layout */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 600px; /* Mobile-first width constraint */
        margin: 0 auto;
    }
    
    /* Login Card */
    div[data-testid="stForm"] {
        background: #0b1421;
        border: 1px solid #1e293b;
        border-radius: 1.5rem;
        padding: 2rem;
        box-shadow: 0 0 50px -10px rgba(56, 189, 248, 0.1);
        max-width: 400px; 
        margin: 0 auto;
    }
    
    /* Custom Card Style (Screenshot Match) */
    .custom-card {
        background: #0f172a; /* Dark Matte Navy */
        border-radius: 1rem;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #1e293b;
    }
    
    .percentage-display {
        font-weight: 800;
        font-size: 1.5rem;
    }
    
    /* Dashboard Aggregate */
    .aggregate-card {
        background: radial-gradient(circle at 50% 100%, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 1.5rem;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Colors */
    .text-green { color: #34d399; }
    .text-yellow { color: #fbbf24; }
    .text-red { color: #f87171; }
    
    /* PRECISE INPUT STYLING FOR PASSWORD FIELD */
    /* Target the input wrapper */
    .stTextInput > div > div {
        background: #1a1a2e !important; /* Very dark blue-grey/black */
        border: 1px solid #2d3748 !important; /* Subtle border */
        border-radius: 0.75rem !important;
        transition: all 0.2s ease-in-out;
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.2) !important; /* Inner shadow for depth */
        padding-right: 2.5rem; /* Space for eye icon if needed, though streamlit usually handles it */
    }
    
    /* Focus state */
    .stTextInput > div > div:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2), inset 0 2px 4px 0 rgba(0, 0, 0, 0.2) !important;
        background: #1e293b !important; /* Slightly lighter on focus */
    }
    
    /* The Input Element itself */
    .stTextInput input {
        color: #f1f5f9 !important; /* Bright white text */
        background-color: transparent !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500;
        letter-spacing: 0.05em; /* Spacing for password dots */
        padding-left: 0.5rem;
    }

    /* Placeholder Text */
    .stTextInput input::placeholder {
        color: #64748b !important;
        opacity: 1;
        letter-spacing: normal;
    }

    /* Eye Icon Visibility (if accessible) */
    /* Attempting to target the SVG icon inside the input */
    .stTextInput button[aria-label="Show password"] {
         color: #94a3b8 !important;
    }
    .stTextInput button[aria-label="Show password"]:hover {
         color: #f1f5f9 !important;
    }

    /* Label Styling */
    .stTextInput label {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.4rem !important;
    }
    
    /* Button */
    .stButton > button {
        background: #3b82f6; 
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white; 
        border: none;
        padding: 0.75rem;
        border-radius: 0.75rem;
        width: 100%;
        font-weight: 600;
        font-size: 1rem;
        transition: transform 0.1s, box-shadow 0.2s;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 12px -2px rgba(59, 130, 246, 0.4);
    }
    .stButton > button:active {
        transform: translateY(0);
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
            <h1 style="font-weight: 800; font-size: 1.8rem; color: white; margin-bottom: 0.5rem; letter-spacing: 0.5px; text-transform: uppercase;">MITS IMS</h1>
            <p style="color: #64748b; font-size: 0.9rem; font-weight: 400;">Secure Login for Students</p>
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
    # Header (Logout Button Only)
    c_spacer, c_logout = st.columns([5, 1])
    with c_logout:
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
        agg_hex = '#34d399' # Green
        if overall < 75:
            agg_hex = '#fbbf24' # Yellow
        if overall < 65:
            agg_hex = '#f87171' # Red
            
        overall_str = f"{overall:.2f}"
        
        st.markdown(f'''
<div class="aggregate-card">
    <p style="color: #94a3b8; font-size: 0.875rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">Aggregate Percentage</p>
    <h1 style="font-size: 3.5rem; font-weight: 700; color: {agg_hex}; margin: 0; line-height: 1;">{overall_str}%</h1>
     <p style="color: #64748b; margin-top: 1rem; font-size: 0.875rem;">
        Classes Attended: <b style="color: #f1f5f9">{total_attended}</b> / <span style="color: #94a3b8">{total_conducted}</span>
    </p>
</div>
''', unsafe_allow_html=True)
        
        # Grid for Subjects
        st.subheader("Subject Detailed Report")
        
        for item in data:
            perc = item['percentage']
            attended = item['attended']
            total = item['total']
            
            # Recalculate true percentage for graph width validity (fallback if perc is 0 but stats exist)
            if total > 0:
                graph_width = (attended / total) * 100
                if perc == 0 and graph_width > 0:
                     perc = round(graph_width, 2)
            else:
                graph_width = 0
            
            border_cls = "border-green"
            text_cls = "text-green"
            bar_color = "#34d399"
            
            if perc < 75:
                border_cls = "border-yellow"
                text_cls = "text-yellow"
                bar_color = "#fbbf24"
            if perc < 65:
                border_cls = "border-red"
                text_cls = "text-red"
                bar_color = "#f87171"
                
            # Custom Card HTML (No Graph, explicitly showing counts)
            card_html = f'''
            <div class="custom-card" style="align-items: center;">
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 1.1rem; color: white; margin-bottom: 0.4rem;">{item['code']}</div>
                    <div style="display: flex; gap: 1rem; font-size: 0.85rem; color: #94a3b8;">
                        <div>Attended: <b style="color: #cbd5e1;">{attended}</b></div>
                        <div>Conducted: <b style="color: #cbd5e1;">{total}</b></div>
                    </div>
                </div>
                <div class="percentage-display {text_cls}" style="font-size: 1.75rem;">
                    {perc}%
                </div>
            </div>
            '''
            st.markdown(card_html, unsafe_allow_html=True)

# Footer (Always Visible)
st.markdown('''
<div class="custom-footer" style="text-align: center; margin: 2rem auto; width: 100%;">
    <p>&copy; 2025 MITS IMS. All Rights Reserved.</p>
</div>
''', unsafe_allow_html=True)

# End of file marker
pass
