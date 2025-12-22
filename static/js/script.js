document.addEventListener('DOMContentLoaded', () => {
    const loginSection = document.getElementById('login-section');
    const loadingSection = document.getElementById('loading-section');
    const loginWrapper = document.getElementById('login-wrapper');
    const loginForm = document.getElementById('login-form');
    const errorMsg = document.getElementById('error-message');
    
    // Dashboard Elements
    const dashboardSection = document.getElementById('dashboard-section');
    const displayName = document.getElementById('display-name');
    const displayId = document.getElementById('display-id');
    const overallPercentage = document.getElementById('overall-percentage');
    const totalAttendedEl = document.getElementById('total-attended');
    const totalConductedEl = document.getElementById('total-conducted');
    const courseList = document.getElementById('course-list');
    const logoutBtn = document.getElementById('logout-btn');

    // Progress Elements
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    // Auto-Login Check
    const storedUser = localStorage.getItem('mits_user');
    const storedPass = localStorage.getItem('mits_pass');
    
    if (storedUser && storedPass) {
        // Auto-login
        fetchAttendance(storedUser, storedPass);
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        fetchAttendance(username, password);
    });

    async function fetchAttendance(username, password) {
        // UI Transition
        loginSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');
        
        // Hide dashboard if refreshing
        dashboardSection.classList.add('hidden');
        loginWrapper.style.display = 'flex'; 
        
        errorMsg.classList.remove('error-visible');
        errorMsg.textContent = '';
        
        // Progress Animation
        progressFill.style.width = '10%';
        progressText.textContent = "Connecting to MITS Portal...";
        
        // Simulated progress updates
        setTimeout(() => {
            progressFill.style.width = '45%';
            progressText.textContent = "Logging securely...";
        }, 2000);
        
        setTimeout(() => {
            progressFill.style.width = '85%';
            progressText.textContent = "Analyzing attendance records...";
        }, 6000);

        try {
            const response = await fetch('/api/attendance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to fetch attendance');
            }

            // Save Credentials
            localStorage.setItem('mits_user', username);
            localStorage.setItem('mits_pass', password);

            // Update User Profile
            displayName.textContent = result.student_name || "";
            displayId.textContent = username;

            renderDashboard(result.data);
            
            // Switch Views
            loginWrapper.style.display = 'none'; // Hide entire login wrapper
            dashboardSection.classList.remove('hidden');

        } catch (error) {
            loadingSection.classList.add('hidden');
            loginSection.classList.remove('hidden');
            
            errorMsg.textContent = error.message;
            errorMsg.classList.add('error-visible');
            errorMsg.classList.remove('error-hidden');
            
            // If auth failed, clear stored creds to prevent loop
            if (error.message.includes('Login failed') || error.message.includes('401')) {
                localStorage.removeItem('mits_user');
                localStorage.removeItem('mits_pass');
            }
        }
    }

    logoutBtn.addEventListener('click', () => {
        // Clear Storage
        localStorage.removeItem('mits_user');
        localStorage.removeItem('mits_pass');
        
        dashboardSection.classList.add('hidden');
        loginWrapper.style.display = 'flex'; // Restore wrapper
        loginSection.classList.remove('hidden');
        loadingSection.classList.add('hidden');
        
        document.getElementById('password').value = '';
        steps.forEach(s => s.classList.remove('active'));
    });
    
    // Refresh Handler
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
             const u = localStorage.getItem('mits_user');
             const p = localStorage.getItem('mits_pass');
             if(u && p) fetchAttendance(u, p);
        });
    }

    // Password Toggle
    const togglePassword = document.getElementById('toggle-password');
    const passwordInput = document.getElementById('password');

    togglePassword.addEventListener('click', () => {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        
        // Toggle Icon Class on the <i> element
        const icon = togglePassword.querySelector('i');
        if (type === 'text') {
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        } else {
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        }
    });

    function renderDashboard(data) {
        courseList.innerHTML = '';
        
        let totalAttended = 0;
        let totalConducted = 0;
        
        if (!data || data.length === 0) {
            courseList.innerHTML = '<p class="text-center text-slate-400 py-10">No attendance data found.</p>';
            return;
        }

        data.forEach(row => {
            const subject = row.code || "Unknown";
            const attended = parseInt(row.attended) || 0;
            const conducted = parseInt(row.total) || 0;
            const percentage = parseFloat(row.percentage) || 0;
            
            totalAttended += attended;
            totalConducted += conducted;

            // Color Logic
            let colorClass = 'text-emerald-400';
            let borderClass = 'border-emerald-500';
            
            if (percentage < 65) {
                colorClass = 'text-red-400';
                borderClass = 'border-red-500';
            } else if (percentage < 75) {
                colorClass = 'text-amber-400';
                borderClass = 'border-amber-500';
            }

            const item = document.createElement('div');
            item.className = `glass p-5 rounded-2xl border-l-4 ${borderClass} hover:bg-white/5 transition-all group animate-fade-in`;
            
            item.innerHTML = `
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div class="flex-1">
                        <h4 class="text-white font-semibold text-lg leading-tight mb-1">${subject}</h4>
                        <div class="flex items-center gap-3 text-xs text-slate-400 uppercase tracking-wider font-medium">
                            <span>Attended: <b class="text-white">${attended}</b></span>
                            <span class="w-1 h-1 rounded-full bg-slate-600"></span>
                            <span>Conducted: <b class="text-white">${conducted}</b></span>
                        </div>
                    </div>
                    
                    <div class="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
                        <div class="text-right">
                            <div class="text-2xl font-bold ${colorClass}">${percentage}%</div>
                        </div>
                    </div>
                </div>
            `;
            courseList.appendChild(item);
        });

        // Update Stats
        totalAttendedEl.textContent = totalAttended;
        totalConductedEl.textContent = totalConducted;
        
        let overallPerc = 0;
        if (totalConducted > 0) {
            overallPerc = ((totalAttended / totalConducted) * 100).toFixed(2);
        }
        
        // Update Aggregate Display
        overallPercentage.textContent = `${overallPerc}%`;
        
        const statusText = document.getElementById('status-text');
        if (overallPerc >= 75) {
            overallPercentage.className = "relative text-6xl md:text-7xl font-extrabold text-emerald-400 tracking-tight";
            if(statusText) {
                statusText.textContent = "Safe Zone";
                statusText.className = "text-xs font-bold text-emerald-400 uppercase tracking-widest";
            }
        } else {
            overallPercentage.className = "relative text-6xl md:text-7xl font-extrabold text-red-400 tracking-tight";
            if(statusText) {
                statusText.textContent = "Shortage Warning";
                statusText.className = "text-xs font-bold text-red-400 uppercase tracking-widest";
            }
        }
    }
});
