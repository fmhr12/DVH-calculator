# dvh_metrics_minimal_app.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import openpyxl  # needed for reading .xlsx

# --- Page config ---
st.set_page_config(layout="wide")

# --- Metric definitions ---
Dcc_values = {
    "D0.035cc": 0.035,
    "D0.1cc": 0.1,
    "D0.5cc": 0.5,
    "D2cc": 2,
    "D5cc": 5,
    "D10cc": 10,
    "D15cc": 15,
    "D20cc": 20,
    "D25cc": 25,
    "D30cc": 30,
    "D35cc": 35,
    "D40cc": 40,
    "D45cc": 45,
    "D50cc": 50,
    "D55cc": 55,
    "D60cc": 60,
    "D65cc": 65,
    "D70cc": 70,
    "D75cc": 75,
    "D80cc": 80,
    "D85cc": 85,
    "D90cc": 90,
    "D95cc": 95,
    "D100cc": 100,
}

D_percent_values = {
    "D2%": 0.02,
    "D5%": 0.05,
    # Note: kept your original keys as-is to preserve behavior
    "D10%": 0.10,
    "D15%": 0.15,
    "D20%": 0.20,
    "D25%": 0.25,
    "D30%": 0.30,
    "D35%": 0.35,
    "D40%": 0.40,
    "D45%": 0.45,
    "D50%": 0.50,
    "D55%": 0.55,
    "D60%": 0.60,
    "D65%": 0.65,
    "D70%": 0.70,
    "D75%": 0.75,
    "D80%": 0.80,
    "D85%": 0.85,
    "D90%": 0.90,
    "D95%": 0.95,
    "D97%": 0.97,
    "D98%": 0.98,
    "D99%": 0.99
}

# Doses to evaluate V metrics at (in cGy)
doses = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000]


# --- Core processors ---
def process_excel(uploaded_file):
    try:
        xls = pd.ExcelFile(uploaded_file, engine='openpyxl')
        sheet_names = xls.sheet_names

        filename = uploaded_file.name
        st.write(f"**Processing file:** {filename}")

        Dcc_metrics, D_percent_metrics, Vcc_metrics, V_percent_metrics = {}, {}, {}, {}

        for sheet_name in sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            df = df.fillna(0)

            # Dcc
            for metric, volume in Dcc_values.items():
                volume_difference = np.abs(df.iloc[1:, 1:].values - volume)
                if volume_difference.size == 0:
                    st.warning(f"No data in '{sheet_name}' for metric '{metric}'. Skipping.")
                    continue
                row, col = np.unravel_index(np.argmin(volume_difference), volume_difference.shape)
                dose_row = df.iat[row + 1, 0]
                dose_col = df.iat[0, col + 1]
                try:
                    dose = int(dose_row + dose_col)
                except (ValueError, TypeError):
                    st.warning(f"Non-integer dose in '{sheet_name}' for '{metric}'. Skipping.")
                    continue
                Dcc_metrics[f"{metric}(Gy)"] = dose / 100.0  # cGy -> Gy

            # Total volume for D% / V%
            if df.shape[0] > 1 and df.shape[1] > 1:
                total_volume = df.iat[1, 1]
            else:
                total_volume = 0
                st.warning(f"Insufficient data in '{sheet_name}' for total volume.")

            # D%
            for metric, percentage in D_percent_values.items():
                if total_volume == 0:
                    D_percent_metrics[f"{metric}(Gy)"] = np.nan
                    continue
                volume_threshold = percentage * total_volume
                volume_difference = np.abs(df.iloc[1:, 1:].values - volume_threshold)
                if volume_difference.size == 0:
                    st.warning(f"No data in '{sheet_name}' for metric '{metric}'. Skipping.")
                    continue
                row, col = np.unravel_index(np.argmin(volume_difference), volume_difference.shape)
                dose_row = df.iat[row + 1, 0]
                dose_col = df.iat[0, col + 1]
                try:
                    dose = int(dose_row + dose_col)
                except (ValueError, TypeError):
                    st.warning(f"Non-integer dose in '{sheet_name}' for '{metric}'. Skipping.")
                    continue
                D_percent_metrics[f"{metric}(Gy)"] = dose / 100.0

            # Vcc / V%
            try:
                header = df.iloc[0, 1:].astype(float)   # dose increments
                index = df.iloc[1:, 0].astype(float)    # base doses
            except ValueError:
                st.warning(f"Non-numeric headers/index in '{sheet_name}'. Skipping V metrics.")
                continue

            for d in doses:
                dose_diff = np.abs(index.values[:, None] + header.values - d)
                if dose_diff.size == 0:
                    st.warning(f"No data in '{sheet_name}' for dose '{d}'. Skipping.")
                    continue
                row, col = np.unravel_index(np.argmin(dose_diff), dose_diff.shape)
                try:
                    volume = df.iloc[row + 1, col + 1]
                except IndexError:
                    st.warning(f"Index OOB for dose '{d}' in '{sheet_name}'. Skipping.")
                    continue
                dose_str = f"V{int(d/100)}Gy"
                Vcc_metrics[f"{dose_str}(cc)"] = volume
                V_percent_metrics[f"{dose_str}(%)"] = (
                    round((volume / total_volume) * 100.0, 1) if total_volume > 0 else np.nan
                )

        Dcc_df = pd.DataFrame([Dcc_metrics], index=['Dcc'])
        D_percent_df = pd.DataFrame([D_percent_metrics], index=['D%'])
        Vcc_df = pd.DataFrame([Vcc_metrics], index=['Vcc'])
        V_percent_df = pd.DataFrame([V_percent_metrics], index=['V%'])

        return Dcc_df, D_percent_df, Vcc_df, V_percent_df

    except FileNotFoundError:
        st.error(f"The file '{uploaded_file.name}' does not exist.")
    except Exception as e:
        st.error(f"Error processing Excel: {e}")
    return None, None, None, None


def process_csv(csv_file):
    try:
        filename = csv_file.name
        st.write(f"**Processing file:** {filename}")

        Dcc_metrics, D_percent_metrics, Vcc_metrics, V_percent_metrics = {}, {}, {}, {}

        df = pd.read_csv(csv_file, header=None)
        if df.empty:
            st.error("Uploaded CSV is empty.")
            return None, None, None, None

        df = df.fillna(0)

        # Dcc
        for metric, volume in Dcc_values.items():
            volume_difference = np.abs(df.iloc[1:, 1:].values - volume)
            if volume_difference.size == 0:
                st.warning(f"No data for '{metric}'. Skipping.")
                continue
            row, col = np.unravel_index(np.argmin(volume_difference), volume_difference.shape)
            dose_row = df.iat[row + 1, 0]
            dose_col = df.iat[0, col + 1]
            try:
                dose = int(dose_row + dose_col)
            except (ValueError, TypeError):
                st.warning(f"Non-integer dose for '{metric}'. Skipping.")
                continue
            Dcc_metrics[f"{metric}(Gy)"] = dose / 100.0

        # Total volume for D% / V%
        if df.shape[0] > 1 and df.shape[1] > 1:
            total_volume = df.iat[1, 1]
        else:
            total_volume = 0
            st.warning("Insufficient data for total volume.")

        # D%
        for metric, percentage in D_percent_values.items():
            if total_volume == 0:
                D_percent_metrics[f"{metric}(Gy)"] = np.nan
                continue
            volume_threshold = percentage * total_volume
            volume_difference = np.abs(df.iloc[1:, 1:].values - volume_threshold)
            if volume_difference.size == 0:
                st.warning(f"No data for '{metric}'. Skipping.")
                continue
            row, col = np.unravel_index(np.argmin(volume_difference), volume_difference.shape)
            dose_row = df.iat[row + 1, 0]
            dose_col = df.iat[0, col + 1]
            try:
                dose = int(dose_row + dose_col)
            except (ValueError, TypeError):
                st.warning(f"Non-integer dose for '{metric}'. Skipping.")
                continue
            D_percent_metrics[f"{metric}(Gy)"] = dose / 100.0

        # Vcc / V%
        try:
            header = df.iloc[0, 1:].astype(float)
            index = df.iloc[1:, 0].astype(float)
        except ValueError:
            st.warning("Non-numeric headers/index. Skipping V metrics.")
            header = pd.Series(dtype=float)
            index = pd.Series(dtype=float)

        for d in doses:
            dose_diff = np.abs(index.values[:, None] + header.values - d)
            if dose_diff.size == 0:
                st.warning(f"No data for dose '{d}'. Skipping.")
                continue
            row, col = np.unravel_index(np.argmin(dose_diff), dose_diff.shape)
            try:
                volume = df.iloc[row + 1, col + 1]
            except IndexError:
                st.warning(f"Index OOB for dose '{d}'. Skipping.")
                continue
            dose_str = f"V{int(d/100)}Gy"
            Vcc_metrics[f"{dose_str}(cc)"] = volume
            V_percent_metrics[f"{dose_str}(%)"] = (
                round((volume / total_volume) * 100.0, 1) if total_volume > 0 else np.nan
            )

        Dcc_df = pd.DataFrame([Dcc_metrics], index=['Dcc'])
        D_percent_df = pd.DataFrame([D_percent_metrics], index=['D%'])
        Vcc_df = pd.DataFrame([Vcc_metrics], index=['Vcc'])
        V_percent_df = pd.DataFrame([V_percent_metrics], index=['V%'])

        return Dcc_df, D_percent_df, Vcc_df, V_percent_df

    except pd.errors.EmptyDataError:
        st.error("Uploaded CSV is empty.")
    except pd.errors.ParserError:
        st.error("Error parsing CSV. Check formatting.")
    except Exception as e:
        st.error(f"Error processing CSV: {e}")
    return None, None, None, None


# --- Risk logic ---
def determine_risk_group(Dcc_df, Vcc_df):
    """
    High risk if either:
      - D10cc(Gy) > 59.2
      - V60Gy(cc) > 12.6
    """
    high_risk_messages = []
    is_high_risk = False

    if 'D10cc(Gy)' in Dcc_df.columns:
        d10cc_value = Dcc_df.at['Dcc', 'D10cc(Gy)']
        if pd.notnull(d10cc_value) and d10cc_value > 59.2:
            high_risk_messages.append("D10cc(Gy) > 59.2")
            is_high_risk = True

    if 'V60Gy(cc)' in Vcc_df.columns:
        v60cc_value = Vcc_df.at['Vcc', 'V60Gy(cc)']
        if pd.notnull(v60cc_value) and v60cc_value > 12.6:
            high_risk_messages.append("V60Gy(cc) > 12.6")
            is_high_risk = True

    return is_high_risk, high_risk_messages


# --- UI ---
def main():
    st.title("DVH Metrics Calculator & Risk Flag")
    st.write(
        "Upload a CSV or Excel file containing a **cumulative DVH table**. "
        "The app computes Dcc(Gy), D%(Gy), VGy(cc), and VGy(%) and flags whether the person is **high-risk** or **low-risk**."
    )

    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx', 'xls'])

    if uploaded_file is not None:
        # Reset pointer before reading
        uploaded_file.seek(0)

        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            Dcc_df, D_percent_df, Vcc_df, V_percent_df = process_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            Dcc_df, D_percent_df, Vcc_df, V_percent_df = process_csv(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel file.")
            return

        if all(x is not None for x in [Dcc_df, D_percent_df, Vcc_df, V_percent_df]):
            # Show metrics
            st.subheader("Dcc (Gy)")
            st.dataframe(Dcc_df, use_container_width=True)

            st.subheader("D% (Gy)")
            st.dataframe(D_percent_df, use_container_width=True)

            st.subheader("V (cc)")
            st.dataframe(Vcc_df, use_container_width=True)

            st.subheader("V (%)")
            st.dataframe(V_percent_df, use_container_width=True)

            # Risk assessment
            is_high_risk, msgs = determine_risk_group(Dcc_df, Vcc_df)

            st.subheader("Risk Group")
            if is_high_risk:
                reasons = "; ".join(msgs) if msgs else "High-risk criteria met."
                st.error(f"**High-risk** — {reasons}")
            else:
                st.success("**Low-risk** — does not meet high-risk criteria (D10cc(Gy) > 59.2 or V60Gy(cc) > 12.6).")


if __name__ == "__main__":
    main()
