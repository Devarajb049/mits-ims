import streamlit as st
from playwright.sync_api import sync_playwright
import time
import re
import subprocess

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
  /* ===============================
   GLOBAL RESET & THEME
================================ */
.stApp {
    background: radial-gradient(circle at 50% 10%, #2e3b4e, #020617);
    font-family: 'Outfit', sans-serif;
    color: #e2e8f0;
    overflow-x: hidden;
}

/* ===============================
   HIDE STREAMLIT DEFAULT UI
================================ */
header[data-testid="stHeader"],
footer,
#MainMenu,
.stDeployButton,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stFooter"],
a.anchor-link,
[class*="viewerBadge"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}

/* ===============================
   PAGE LAYOUT
================================ */
.block-container {
    padding-top: 5rem !important;
    padding-bottom: 2rem !important;
    max-width: 450px;
    margin: 0 auto;
}

/* ===============================
   FORM CONTAINER
================================ */
div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* ===============================
   UNIFIED INPUT STYLE
   (TEXT + PASSWORD)
================================ */
.stTextInput {
    background: transparent !important;
}

.stTextInput div[data-baseweb="input"] {
    background: rgba(255, 255, 255, 0.12) !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 999px !important;
    backdrop-filter: blur(10px);
    transition: all 0.25s ease;
}

/* FOCUS STATE */
.stTextInput div[data-baseweb="input"]:focus-within {
    background: rgba(255, 255, 255, 0.22) !important;
    border-color: #fb7185 !important;
    border-radius: 999px !important;
    box-shadow: 0 0 0 1.5px rgba(251, 113, 133, 0.9);
}

/* INPUT FIELD */
.stTextInput input {
    background: transparent !important;
    color: #ffffff !important;
    padding: 0.75rem 1rem !important;
    font-weight: 500;
    border: none !important;
}

/* PLACEHOLDER */
.stTextInput input::placeholder {
    color: #94a3b8 !important;
}

/* REMOVE LABEL GAP */
.stTextInput label {
    display: none !important;
}

/* ===============================
   LOGOUT BUTTON (SINGLE, RWD)
================================ */
button[kind="secondary"][data-testid="baseButton-secondary"] {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #e5e7eb !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 999px !important;
    padding: 0.45rem 1rem !important;
    font-size: 0.8rem !important;
    font-weight: 600;
    position: fixed;
    top: 1rem;
    right: 1rem;
    backdrop-filter: blur(10px);
    transition: all 0.2s ease;
    z-index: 9999;
}

/* Hover */
button[kind="secondary"][data-testid="baseButton-secondary"]:hover {
    background: rgba(255, 255, 255, 0.18) !important;
    color: #ffffff !important;
    box-shadow: 0 0 12px rgba(255,255,255,0.25);
    transform: translateY(-1px);
}


/* ===============================
   DASHBOARD CARDS
================================ */
.custom-card {
    background: #0f172a;
    border-radius: 1rem;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid #1e293b;
}

.aggregate-card {
    background: radial-gradient(circle at 50% 100%, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 1.5rem;
    padding: 2rem;
    text-align: center;
    margin-bottom: 2rem;
}

.percentage-display {
    font-weight: 800;
    font-size: 1.75rem;
}

/* ===============================
   TEXT COLORS
================================ */
.text-green { color: #34d399; }
.text-yellow { color: #fbbf24; }
.text-red { color: #f87171; }

/* ===============================
   FOOTER
================================ */
.custom-footer {
    text-align: center;
    margin: 2rem auto;
    color: #64748b;
    font-size: 0.8rem;
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
        # Labels are hidden via CSS for cleaner glassmorphism look
        username = st.text_input("Username", placeholder="Registration Number")
        password = st.text_input("Password", placeholder="Password", type="password")
        
        submitted = st.form_submit_button("Sign In")
        
        if submitted:
            if not username or not password:
                st.warning("Please enter Credentials")
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
    with c_logout:
       if st.button("⏻ Logout", key="logout"):
           st.session_state.logged_in = False
           st.session_state.data = None
           st.rerun()

    data = st.session_state.data
    
    if not data:
        st.info("No attendance data found. The page might not have loaded correctly.")
        pass
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
            
                text_cls = "text-green"
            
            if perc < 75:
                text_cls = "text-yellow"
            if perc < 65:
                text_cls = "text-red"

                
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
