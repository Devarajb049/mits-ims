import streamlit as st
from playwright.sync_api import sync_playwright
import time
import re
import subprocess
import sys
import math

# Page Configuration
st.set_page_config(
    page_title="MITS IMS Attendance",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Consolidated Premium Styling (Glassmorphism + Tailwind) ---
st.markdown(r"""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<script src="https://cdn.tailwindcss.com"></script>
<style>
    /* GLOBAL OVERRIDES */
    * { font-family: 'Outfit', sans-serif !important; box-sizing: border-box; }
    
    .stApp {
        background: radial-gradient(circle at 50% 10%, #1e293b, #020617) !important;
        color: #e2e8f0 !important;
    }

    /* Hide Streamlit Header/Footer */
    header[data-testid="stHeader"], footer, [data-testid="stToolbar"] {
        display: none !important;
    }

    /* Responsive Container */
    .block-container {
        padding: 3rem 1rem !important;
        max-width: 480px !important;
        margin: 0 auto !important;
    }

    /* GLASS CARD BASE */
    .glass-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
    }

    /* INPUT STYLING */
    .stTextInput div[data-baseweb="input"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput div[data-baseweb="input"]:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
    }
    .stTextInput input {
        color: white !important;
        padding: 0.75rem 1rem !important;
    }
    .stTextInput label { display: none !important; }

    /* PASSWORD TOGGLE FIX */
    button[data-testid="stTextInputPasswordVisibility"] {
        background: transparent !important;
        border: none !important;
        color: #94a3b8 !important;
        box-shadow: none !important;
    }

    /* LOGIN LOGO */
    .logo-glow {
        filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.4));
    }

    /* BUTTONS */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #38bdf8 0%, #1d4ed8 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.8rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        color: white !important;
        width: 100% !important;
        margin-top: 1rem !important;
    }

    /* LOGOUT BUTTON - FIXED CORNER */
    .fixed-logout {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 9999;
    }
    .fixed-logout button {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        border-radius: 50px !important;
        color: #f87171 !important;
        padding: 0.4rem 1.2rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        backdrop-filter: blur(8px) !important;
    }
    .fixed-logout button:hover {
        background: rgba(239, 68, 68, 0.2) !important;
        border-color: #f87171 !important;
    }

    /* SUBJECT CARDS */
    .subject-row {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        transition: transform 0.2s;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .subject-row:hover { transform: translateY(-2px); border-color: rgba(56, 189, 248, 0.2); }

    /* COLORS */
    .text-green { color: #10b981 !important; }
    .text-yellow { color: #fbbf24 !important; }
    .text-red { color: #f87171 !important; }

    /* Hide scrollbar but keep functionality */
    ::-webkit-scrollbar { width: 0px; background: transparent; }
</style>
""", unsafe_allow_html=True)

# Install Playwright Dependencies (Cached)
@st.cache_resource
def install_browsers():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Failed to install Playwright: {e}")

install_browsers()

# Logic to fetch attendance
def fetch_attendance(username, password):
    with sync_playwright() as p:
        browser = None
        try:
            # Launch browser with stability flags
            browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = browser.new_page()
            
            # 1. Page Navigation
            try:
                page.goto("http://mitsims.in/", timeout=45000)
            except Exception:
                return {"error": "The MITS server is taking too long to respond. Please try after some time."}
            
            # 2. Login Step 1: Open LoginForm
            try:
                page.wait_for_selector("#studentLink", state="visible", timeout=15000)
                page.click("#studentLink", force=True)
                page.wait_for_selector("#studentForm #inputStuId", state="visible", timeout=15000)
            except Exception:
                return {"error": "Connection timed out. Please try after some time."}
            
            # 3. Login Step 2: Fill and Submit
            page.fill("#studentForm #inputStuId", username)
            page.fill("#studentForm #inputPassword", password)
            page.click("#studentSubmitButton", force=True)
            
            # 4. Wait for Result (Success or Error)
            try:
                # Wait for either the dashboard element or error div
                page.wait_for_selector("#studentName, #studentErrorDiv", timeout=10000)
            except:
                # Fallback: force submit if click didn't trigger
                try:
                    page.evaluate("if(document.querySelector('#studentForm')) document.querySelector('#studentForm').submit();")
                    page.wait_for_selector("#studentName, #studentErrorDiv", timeout=10000)
                except Exception:
                    # If we still haven't found a success or error marker
                    return {"error": "Login failed or timed out. Please check your credentials and try after some time."}

            # 5. Explicit Error Check
            error_div = page.query_selector("#studentErrorDiv")
            if error_div:
                err_text = ""
                try:
                    err_text = error_div.inner_text().strip()
                except:
                    pass
                if err_text:
                    # Mask technical errors with user-friendly message
                    if any(kw in err_text.lower() for kw in ["invalid", "wrong", "mismatch", "incorrect"]):
                        return {"error": "Invalid Registration Number or Password"}
                    return {"error": err_text}
            
            # Verify if dashboard actually loaded
            if not page.query_selector("#studentName"):
                return {"error": "Invalid Registration Number or Password"}

            # 6. Data Extraction
            time.sleep(4) # Wait for attendance values to populate
            full_text = page.inner_text("body")
            
            # Name extraction
            student_name = "Student"
            name_match = re.search(r"([A-Z\s]+)\s+\|\s+Change Password", full_text)
            if name_match: student_name = name_match.group(1).strip()
            
            attendance_data = []
            lines = [l.strip() for l in full_text.split('\n') if l.strip()]
            for i, line in enumerate(lines):
                upper_line = line.upper()
                if "TOTAL CONDUCTED" in upper_line or "ATTENDANCE %" in upper_line:
                    continue
                
                is_subject = re.match(r'^\d*[A-Z]+\d+[A-Z0-9]*$', line) or (line.isupper() and 2 < len(line) < 30 and not re.search(r'\d', line))
                
                if is_subject:
                    try:
                        lookahead = lines[i+1:i+6]
                        nums = []
                        for sub in lookahead:
                            if re.match(r'^[\d\.]+%?$', sub) or sub == '-':
                                nums.append(float(sub.replace('%', '').replace('-', '0')))
                        if len(nums) >= 3:
                            attendance_data.append({
                                "code": line,
                                "attended": int(nums[0]),
                                "total": int(nums[1]),
                                "percentage": nums[2]
                            })
                    except: pass
            
            return {"success": True, "name": student_name, "data": attendance_data}

        except Exception as e:
            err_msg = str(e)
            if "Target page, context or browser has been closed" in err_msg or "Timeout" in err_msg:
                return {"error": "Connection timed out. Please try after some time."}
            return {"error": "Something went wrong. Please try after some time."}
        finally:
            if browser:
                try:
                    browser.close()
                except:
                    pass

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'data' not in st.session_state: st.session_state.data = None
if 'user_name' not in st.session_state: st.session_state.user_name = ""

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.markdown('<div class="h-10"></div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="text-center mb-8">
            <div class="flex justify-center mb-4">
                <div class="bg-blue-500/10 p-5 rounded-3xl border border-blue-500/20 logo-glow">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="#38bdf8" viewBox="0 0 16 16">
                        <path d="M11.251.068a.5.5 0 0 1 .227.58L9.677 6.5H13a.5.5 0 0 1 .364.843l-8 8.5a.5.5 0 0 1-.842-.49L6.323 9.5H3a.5.5 0 0 1-.364-.843l8-8.5a.5.5 0 0 1 .615-.09z"/>
                    </svg>
                </div>
            </div>
            <h1 class="text-3xl font-extrabold tracking-tight text-white mb-1">MITS IMS</h1>
            <p class="text-slate-400 text-sm">Attendance Portal for Students</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Registration Number")
        password = st.text_input("Password", placeholder="Password", type="password")
        submitted = st.form_submit_button("Sign In")
        
        if submitted:
            if not username or not password:
                st.warning("Please enter Credentials")
            else:
                with st.spinner("Logging in..."):
                    res = fetch_attendance(username, password)
                    if "error" in res:
                        st.error(res['error'])
                    else:
                        st.session_state.logged_in = True
                        st.session_state.data = res['data']
                        st.session_state.user_name = res['name']
                        st.rerun()

# --- DASHBOARD SCREEN ---
else:
    # Top-right Logout
    st.markdown('<div class="fixed-logout">', unsafe_allow_html=True)
    if st.button("Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.data = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    data = st.session_state.data
    
    # Welcome Header
    st.markdown(f"""
        <div class="mb-8">
            <span class="text-xs font-semibold text-blue-400 uppercase tracking-widest bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">Dashboard</span>
            <h2 class="text-2xl font-bold mt-3 text-white">Hello, {st.session_state.user_name} 👋</h2>
            <p class="text-slate-400 text-sm">Here's your attendance breakdown.</p>
        </div>
    """, unsafe_allow_html=True)

    if not data:
        st.info("No data fetched. Please re-login.")
    else:
        # Aggregate Card
        total_att = sum(d['attended'] for d in data)
        total_con = sum(d['total'] for d in data)
        overall = (total_att / total_con * 100) if total_con > 0 else 0
        
        clr = 'text-green'
        if overall < 75: clr = 'text-yellow'
        if overall < 65: clr = 'text-red'
            
        st.markdown(f'''
            <div class="glass-card text-center mb-8">
                <p class="text-slate-500 text-xs font-bold uppercase tracking-wider mb-2">Aggregate Percentage</p>
                <h1 class="text-5xl font-extrabold {clr}">{overall:.2f}%</h1>
                <div class="mt-4 text-slate-300 text-sm font-medium">
                    <span class="bg-slate-700/50 px-3 py-1 rounded-lg">{total_att}</span>
                    <span class="mx-2 opacity-30">/</span>
                    <span class="text-slate-500">{total_con}</span> 
                    <span class="ml-1 text-slate-500">Classes</span>
                </div>
            </div>
        ''', unsafe_allow_html=True)

        st.markdown('<h3 class="text-white font-bold text-sm uppercase tracking-tight mb-4">Detailed Report</h3>', unsafe_allow_html=True)

        # Subject List
        for d in data:
            p = d['percentage']
            s_clr = 'text-green'
            if p < 75: s_clr = 'text-yellow'
            if p < 65: s_clr = 'text-red'
            
            st.markdown(f'''
                <div class="subject-row">
                    <div class="flex-1">
                        <div class="text-white font-bold text-sm leading-tight mb-1">{d['code']}</div>
                        <div class="text-slate-500 text-[11px] font-medium">
                            Attended: <span class="text-slate-300">{d['attended']}</span> | 
                            Total: <span class="text-slate-300">{d['total']}</span>
                        </div>
                    </div>
                    <div class="text-lg font-extrabold {s_clr}">
                        {p}%
                    </div>
                </div>
            ''', unsafe_allow_html=True)

        st.markdown('<h3 class="text-white font-bold text-sm uppercase tracking-tight mb-4">Target Calculator</h3>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="glass-card mb-8">', unsafe_allow_html=True)
            
            target_pct = st.slider("Target Percentage (%)", 75, 95, 75)
            
            if overall < target_pct:
                needed = math.ceil((target_pct * total_con - 100 * total_att) / (100 - target_pct))
                if needed > 0:
                    st.success(f"You need to attend **{needed}** more classes to reach {target_pct}%.")
                else:
                    st.info(f"You are already above {target_pct}%.")
            else:
                st.info(f"You are already at {overall:.2f}%. Target {target_pct}% reached!")
            
            st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
    <div class="text-center py-12 text-slate-600 font-medium text-[11px] uppercase tracking-widest">
        &copy; 2025 MITS IMS
    </div>
""", unsafe_allow_html=True)
