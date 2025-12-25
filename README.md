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

## 🛠️ Tech Stack
- **Web App**: Streamlit
- **Scraping**: Playwright (Python)
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

## 🔍 SEO Keywords
`MITS IMS` `MITSIMS` `Attendance Tracker` `MITS Portal` `Student Attendance` `MITS Attendance Scraper` `MITS IMS Login` `MITS Attendance`

---
*Made with ❤️ for MITS Students.*
