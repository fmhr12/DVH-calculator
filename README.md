# DVH Calculator & Survival Analysis Tool

## 📖 Overview
The **Dose-Volume Histogram (DVH) Calculator & Survival Analysis Tool** is a user-friendly **Streamlit** web application designed to calculate **Dose-Volume Histogram (DVH)** metrics and visualize **Kaplan-Meier survival curves** for radiation therapy patients. The tool helps identify high-risk groups based on clinical thresholds and provides comprehensive data visualization for risk assessment.

## 🚀 Features
- **DVH Metric Calculations:**
  - **Dcc (Gy):** Dose to specific volumes (e.g., `D10cc`, `D20cc`)  
  - **D% (Gy):** Dose to specific percentages of volume (e.g., `D5%`, `D95%`)  
  - **Vcc (cc):** Volume receiving specific doses (e.g., `V60Gy`)  
  - **V% (%):** Percentage of volume receiving specific doses  

- **High-Risk Group Detection:**  
  - Flags patients as high-risk if:  
    - `D10cc(Gy) > 59.2`  
    - `V60Gy(cc) > 12.6`  

- **Kaplan-Meier Survival Curve Visualization:**  
  - Interactive survival curve plots for better clinical decision-making.  
  - Sidebar controls to toggle survival curve visibility.

- **File Upload Support:**  
  - Upload **CSV** or **Excel** (`.xlsx`, `.xls`) files.

- **Sample Dataset Downloads:**  
  - Download high-risk and low-risk sample datasets for testing.

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/dvh-calculator.git
cd dvh-calculator
```

### 2. Install Dependencies
Install all the required Python packages using the following command:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the Streamlit application using:
```bash
streamlit run combined_streamlit_app_with_flexible_sidebar.py
```
