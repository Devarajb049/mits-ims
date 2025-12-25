# 🎓 MITS IMS Attendance Tracker

A high-performance **MITS IMS Attendance Automation & Analytical Dashboard** designed to automate portal interactions and provide strategic attendance insights.

## 🚀 Key Components

### 1. Automated Scraper (Playwright)
*   **Engine**: Playwright (Chromium) for ExtJS portal interaction.
*   **Logic**: Headless login with regex parsing of body text to extract Subject Codes, Classes Attended, and Total Conducted.
*   **Stability**: Handled timeouts and masked portal error messages for better user experience.

### 2. Glassmorphism Dashboard
*   **UI**: Custom CSS Glassmorphism + Tailwind CSS integrated into Streamlit.
*   **Analytics**: Aggregate percentage calculation and color-coded reporting (Green ≥75%, Yellow 65-74%, Red <65%).

---

## 🧮 Actual Formula

### 1. Reach Target % (Classes to Attend)
Calculates how many *more* classes are needed ($x$) to reach a target percentage ($T$) given current attended ($A$) and total conducted ($C$):

$$x = \lceil \frac{(T \times C - 100 \times A)}{(100 - T)} \rceil$$

---

## 🛠️ Tech Stack
- **Web App**: Streamlit
- **Scraping**: Playwright (Python)
- **Math**: Python `math` library (Ceil)
- **Design**: Custom CSS + Google Fonts (Outfit) + FontAwesome 6.4.0

---

## 🚀 Installation & Usage

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Run the App**:
   ```bash
   streamlit run streamlit_app.py
   ```

---

## 👨‍💻 Author
**Deva Raj Bhojanapu**
- [GitHub](https://github.com/Devarajb049/)

---
*Made with ❤️ for MITS Students.*
