# combined_streamlit_app_with_flexible_sidebar.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import openpyxl
import plotly.graph_objects as go

# Set Streamlit page configuration
st.set_page_config(layout="wide")

# Define the volume metrics (Dcc and D%)
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
    "D10cc(Gy)%": 0.10,
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

# Define the doses for volume calculation (Vcc and V%)
doses = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000]

def process_excel(uploaded_file):
    try:
        # Create a pandas ExcelFile object from the uploaded file
        xls = pd.ExcelFile(uploaded_file, engine='openpyxl')
        sheet_names = xls.sheet_names

        # Extract filename
        filename = uploaded_file.name
        patient_number = os.path.splitext(filename)[0]
        st.write(f"**Processing file:** {filename}")

        # Initialize dictionaries to collect all results
        Dcc_metrics = {}
        D_percent_metrics = {}
        Vcc_metrics = {}
        V_percent_metrics = {}

        for sheet_name in sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            df = df.fillna(0)

            # Calculate Dcc metrics
            for metric, volume in Dcc_values.items():
                volume_difference = np.abs(df.iloc[1:, 1:].values - volume)
                if volume_difference.size == 0:
                    st.warning(f"No data found in sheet '{sheet_name}' for metric '{metric}'. Skipping.")
                    continue
                row, col = np.unravel_index(np.argmin(volume_difference), volume_difference.shape)
                dose_row = df.iat[row + 1, 0]
                dose_col = df.iat[0, col + 1]
                try:
                    dose = int(dose_row + dose_col)
                except (ValueError, TypeError):
                    st.warning(f"Non-integer dose values found in sheet '{sheet_name}' for metric '{metric}'. Skipping.")
                    continue
                # Format the metric name with (Gy) suffix
                formatted_metric = f"{metric}(Gy)"
                Dcc_metrics[formatted_metric] = dose / 100  # Convert cGy to Gy

            # Calculate D% metrics
            if df.shape[0] > 1 and df.shape[1] > 1:
                total_volume = df.iat[1, 1]  # Assuming this is the total volume
            else:
                total_volume = 0
                st.warning(f"Insufficient data in sheet '{sheet_name}' to calculate total volume.")

            for metric, percentage in D_percent_values.items():
                if total_volume == 0:
                    D_percent_metrics[f"{metric}(Gy)"] = np.nan
                    continue
                volume_threshold = percentage * total_volume
                volume_difference = np.abs(df.iloc[1:, 1:].values - volume_threshold)
                if volume_difference.size == 0:
                    st.warning(f"No data found in sheet '{sheet_name}' for metric '{metric}'. Skipping.")
                    continue
                row, col = np.unravel_index(np.argmin(volume_difference), volume_difference.shape)
                dose_row = df.iat[row + 1, 0]
                dose_col = df.iat[0, col + 1]
                try:
                    dose = int(dose_row + dose_col)
                except (ValueError, TypeError):
                    st.warning(f"Non-integer dose values found in sheet '{sheet_name}' for metric '{metric}'. Skipping.")
                    continue
                # Format the metric name with (Gy) suffix
                formatted_metric = f"{metric}(Gy)"
                D_percent_metrics[formatted_metric] = dose / 100  # Convert cGy to Gy

            # Calculate Vcc and V% metrics
            try:
                header = df.iloc[0, 1:].astype(float)  # Dose increments from the first row, excluding the first cell
                index = df.iloc[1:, 0].astype(float)    # Base doses from the first column, excluding the first cell
            except ValueError:
                st.warning(f"Non-numeric data found in headers or index of sheet '{sheet_name}'. Skipping V metrics.")
                continue

            for dose in doses:
                dose_diff = np.abs(index.values[:, None] + header.values - dose)
                if dose_diff.size == 0:
                    st.warning(f"No data found in sheet '{sheet_name}' for dose '{dose}'. Skipping.")
                    continue
                row, col = np.unravel_index(np.argmin(dose_diff), dose_diff.shape)
                try:
                    volume = df.iloc[row + 1, col + 1]
                except IndexError:
                    st.warning(f"Index out of bounds for dose '{dose}' in sheet '{sheet_name}'. Skipping.")
                    continue
                dose_str = f'V{int(dose / 100)}Gy'
                # Format the metric names
                Vcc_metric = f"{dose_str}(cc)"
                V_percent_metric = f"{dose_str}(%)"
                Vcc_metrics[Vcc_metric] = volume
                if total_volume > 0:
                    V_percent_metrics[f"{dose_str}(%)"] = round((volume / total_volume) * 100, 1)
                else:
                    V_percent_metrics[f"{dose_str}(%)"] = np.nan

        # Create separate DataFrames for each metric type
        Dcc_df = pd.DataFrame([Dcc_metrics])
        Dcc_df.index = ['Dcc']

        D_percent_df = pd.DataFrame([D_percent_metrics])
        D_percent_df.index = ['D%']

        Vcc_df = pd.DataFrame([Vcc_metrics])
        Vcc_df.index = ['Vcc']

        V_percent_df = pd.DataFrame([V_percent_metrics])
        V_percent_df.index = ['V%']

        return Dcc_df, D_percent_df, Vcc_df, V_percent_df

    except FileNotFoundError:
        st.error(f"The file '{uploaded_file.name}' does not exist. Please check the file and try again.")
    except Exception as e:
        st.error(f"An error occurred while processing the Excel file: {e}")
    return None, None, None, None

def process_csv(csv_file):
    try:
        # Extract filename
        filename = csv_file.name
        patient_number = os.path.splitext(filename)[0]
        st.write(f"**Processing file:** {filename}")

        # Initialize dictionaries to collect all results
        Dcc_metrics = {}
        D_percent_metrics = {}
        Vcc_metrics = {}
        V_percent_metrics = {}

        # Read the CSV file
        df = pd.read_csv(csv_file, header=None)
        if df.empty:
            st.error("The uploaded CSV file is empty.")
            return None, None, None, None

        df = df.fillna(0)

        # Calculate Dcc metrics
        for metric, volume in Dcc_values.items():
            volume_difference = np.abs(df.iloc[1:, 1:].values - volume)
            if volume_difference.size == 0:
                st.warning(f"No data found for metric '{metric}'. Skipping.")
                continue
            row, col = np.unravel_index(np.argmin(volume_difference), volume_difference.shape)
            dose_row = df.iat[row + 1, 0]
            dose_col = df.iat[0, col + 1]
            try:
                dose = int(dose_row + dose_col)
            except (ValueError, TypeError):
                st.warning(f"Non-integer dose values found for metric '{metric}'. Skipping.")
                continue
            # Format the metric name with (Gy) suffix
            formatted_metric = f"{metric}(Gy)"
            Dcc_metrics[formatted_metric] = dose / 100  # Convert cGy to Gy

        # Calculate D% metrics
        if df.shape[0] > 1 and df.shape[1] > 1:
            total_volume = df.iat[1, 1]  # Assuming this is the total volume
        else:
            total_volume = 0
            st.warning("Insufficient data to calculate total volume.")

        for metric, percentage in D_percent_values.items():
            if total_volume == 0:
                D_percent_metrics[f"{metric}(Gy)"] = np.nan
                continue
            volume_threshold = percentage * total_volume
            volume_difference = np.abs(df.iloc[1:, 1:].values - volume_threshold)
            if volume_difference.size == 0:
                st.warning(f"No data found for metric '{metric}'. Skipping.")
                continue
            row, col = np.unravel_index(np.argmin(volume_difference), volume_difference.shape)
            dose_row = df.iat[row + 1, 0]
            dose_col = df.iat[0, col + 1]
            try:
                dose = int(dose_row + dose_col)
            except (ValueError, TypeError):
                st.warning(f"Non-integer dose values found for metric '{metric}'. Skipping.")
                continue
            # Format the metric name with (Gy) suffix
            formatted_metric = f"{metric}(Gy)"
            D_percent_metrics[formatted_metric] = dose / 100  # Convert cGy to Gy

        # Calculate Vcc and V% metrics
        try:
            header = df.iloc[0, 1:].astype(float)  # Dose increments from the first row, excluding the first cell
            index = df.iloc[1:, 0].astype(float)    # Base doses from the first column, excluding the first cell
        except ValueError:
            st.warning("Non-numeric data found in headers or index. Skipping V metrics.")
            header = pd.Series(dtype=float)
            index = pd.Series(dtype=float)

        for dose in doses:
            dose_diff = np.abs(index.values[:, None] + header.values - dose)
            if dose_diff.size == 0:
                st.warning(f"No data found for dose '{dose}'. Skipping.")
                continue
            row, col = np.unravel_index(np.argmin(dose_diff), dose_diff.shape)
            try:
                volume = df.iloc[row + 1, col + 1]
            except IndexError:
                st.warning(f"Index out of bounds for dose '{dose}'. Skipping.")
                continue
            dose_str = f'V{int(dose / 100)}Gy'
            # Format the metric names
            Vcc_metric = f"{dose_str}(cc)"
            V_percent_metric = f"{dose_str}(%)"
            Vcc_metrics[Vcc_metric] = volume
            if total_volume > 0:
                V_percent_metrics[f"{dose_str}(%)"] = round((volume / total_volume) * 100, 1)
            else:
                V_percent_metrics[f"{dose_str}(%)"] = np.nan

        # Create separate DataFrames for each metric type
        Dcc_df = pd.DataFrame([Dcc_metrics])
        Dcc_df.index = ['Dcc']

        D_percent_df = pd.DataFrame([D_percent_metrics])
        D_percent_df.index = ['D%']

        Vcc_df = pd.DataFrame([Vcc_metrics])
        Vcc_df.index = ['Vcc']

        V_percent_df = pd.DataFrame([V_percent_metrics])
        V_percent_df.index = ['V%']

        return Dcc_df, D_percent_df, Vcc_df, V_percent_df

    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file.")
        return None, None, None, None
    except pd.errors.ParserError:
        st.error("Error parsing the CSV file. Please ensure it is properly formatted.")
        return None, None, None, None
    except Exception as e:
        st.error(f"An error occurred while processing the CSV file: {e}")
        return None, None, None, None

def determine_risk_group(Dcc_df, Vcc_df):
    high_risk_messages = []
    is_high_risk = False
    risk_details = {}

    # Check D10cc(Gy) > 59.2
    if 'D10cc(Gy)' in Dcc_df.columns:
        d10cc_value = Dcc_df.at['Dcc', 'D10cc(Gy)']
        if pd.notnull(d10cc_value) and d10cc_value > 59.2:
            high_risk_messages.append("**D10cc(Gy) > 59.2:** Patient is in high risk group.")
            is_high_risk = True
            risk_details['D10cc'] = d10cc_value

    # Check V60Gy(cc) > 12.6
    if 'V60Gy(cc)' in Vcc_df.columns:
        v60cc_value = Vcc_df.at['Vcc', 'V60Gy(cc)']
        if pd.notnull(v60cc_value) and v60cc_value > 12.6:
            high_risk_messages.append("**V60Gy(cc) > 12.6:** Patient is in high risk group.")
            is_high_risk = True
            risk_details['V60Gy'] = v60cc_value

    return is_high_risk, high_risk_messages, risk_details

def load_survival_data():
    """
    Load the survival data files.
    Each file should contain a 'risk_group' column with 'low' and 'high' values.
    Returns a dictionary with keys as identifiers and values as DataFrames.
    """
    survival_data_files = {
        'D10cc(Gy)': 'survival_data_D10.csv',
        'V60Gy(cc)': 'survival_data_v60.csv'
    }
    survival_datasets = {}
    for key, file in survival_data_files.items():
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                # Ensure 'risk_group' column exists
                if 'risk_group' not in df.columns:
                    st.error(f"'risk_group' column not found in '{file}'.")
                    continue
                survival_datasets[key] = df
            except Exception as e:
                st.error(f"Error loading {file}: {e}")
        else:
            st.error(f"Survival data file '{file}' not found.")
    return survival_datasets

def plot_survival_curves(survival_datasets, risk_group_flags):
    """
    Plot survival curves based on the patient's risk group.
    
    Parameters:
    - survival_datasets: Dictionary containing survival data DataFrames.
    - risk_group_flags: Dictionary indicating if high risk criteria are met for 'D10cc(Gy)' and 'V60Gy(cc)'.
    """
    try:
        for key, is_high_risk in risk_group_flags.items():
            dataset = survival_datasets.get(key)
            if dataset is None or dataset.empty:
                st.warning(f"No data available for survival dataset '{key}'. Skipping.")
                continue

            # Provide multiselect for risk groups, default based on flags
            default_selection = ['high'] if is_high_risk else ['low']
            selected_risk_groups = st.multiselect(
                f'Select Risk Groups to Plot for {key}',
                options=['low', 'high'],
                default=default_selection,
                key=f'multiselect_{key}'
            )

            if not selected_risk_groups:
                st.warning(f"Please select at least one risk group to display the survival curves for {key}.")
                st.markdown("---")
                continue

            # Filter data based on selected risk groups
            filtered_data = dataset[dataset['risk_group'].str.lower().isin(selected_risk_groups)]

            if filtered_data.empty:
                st.warning(f"No survival data found for the selected risk groups in '{key}'. Skipping.")
                st.markdown("---")
                continue

            # Group selection
            groups = filtered_data['group'].unique()
            selected_groups = st.multiselect(
                f'Select Survival Groups to Plot for {key} Risk Groups: {", ".join(selected_risk_groups).capitalize()}',
                options=groups,
                default=groups.tolist(),
                key=f'survival_multiselect_{key}'
            )

            if not selected_groups:
                st.warning(f"Please select at least one survival group to display for '{key}'.")
                st.markdown("---")
                continue

            # Create a placeholder for the figure
            fig_placeholder = st.empty()

            # Slider for selecting time point with unique key
            time_min = filtered_data['timeline'].min()
            time_max = filtered_data['timeline'].max()
            selected_time = st.slider(
                f'Select Time Point (Months) for {key} Risk Groups: {", ".join(selected_risk_groups).capitalize()}',
                min_value=float(time_min),
                max_value=float(time_max),
                value=float(time_min),
                step=1.0,
                key=f'slider_{key}'
            )

            # Create figure
            fig = go.Figure()
            for group in selected_groups:
                group_data = filtered_data[filtered_data['group'] == group].sort_values('timeline')
                if group_data.empty:
                    st.warning(f"No data available for group '{group}' in dataset '{key}'. Skipping.")
                    continue
                color = group_data['color'].iloc[0] if 'color' in group_data.columns else 'blue'
                linestyle = group_data['linestyle'].iloc[0] if 'linestyle' in group_data.columns else 'solid'
                fig.add_trace(
                    go.Scatter(
                        x=group_data['timeline'],
                        y=group_data['survival_probability'],
                        mode='lines',
                        name=group,
                        line=dict(color=color, dash=linestyle),
                        hovertemplate='%{y:.4f}<extra></extra>'
                    )
                )
            # Add vertical line at selected time point
            if selected_time is not None:
                fig.add_vline(x=selected_time, line_dash="dash", line_color="gray")
            # Update layout
            fig.update_layout(
                title=f'Kaplan-Meier Survival Curves for {key} Risk Groups: {", ".join(selected_risk_groups).capitalize()}',
                xaxis_title='Time (Months)',
                yaxis_title='Survival Probability',
                hovermode='x',
                width=1000,
                height=600,
                xaxis=dict(
                    showspikes=True,
                    spikecolor="gray",
                    spikethickness=1,
                    spikedash='dot',
                    spikemode='across',
                ),
                hoverdistance=100,  # Distance to show hover effect
                spikedistance=1000,  # Distance to show spike
            )
            fig_placeholder.plotly_chart(fig, use_container_width=True)

            # Compute survival probabilities at the selected time
            probabilities = []
            for group in selected_groups:
                group_data = filtered_data[filtered_data['group'] == group].sort_values('timeline')
                if group_data.empty:
                    continue
                # Interpolate survival probability at selected time
                survival_prob = np.interp(
                    selected_time, group_data['timeline'], group_data['survival_probability']
                )
                probabilities.append({'Group': group, 'Survival Probability': survival_prob})

            # Display the probabilities in a table
            if probabilities:
                prob_df = pd.DataFrame(probabilities)
                prob_df.set_index('Group', inplace=True)
                st.write(f'### Survival Probabilities {selected_time:.0f} Months after Radiotherapy ')
                st.table(prob_df)
            else:
                st.warning(f"No survival probabilities to display for {key} Risk Groups: {', '.join(selected_risk_groups).capitalize()}.")
            st.markdown("---")  # Add a horizontal separator

    except Exception as e:
        st.error(f"An error occurred while plotting survival curves: {e}")

def provide_sample_downloads():
    """
    Provides download buttons for sample datasets: high_risk_sample.xlsx and low_risk_sample.xlsx.
    Users can download these files to understand the required format and use them as input for the app.
    """
    st.sidebar.header("Download Sample Datasets")

    sample_files = {
        "High Risk Sample Dataset": "high_risk_sample.xlsx",
        "Low Risk Sample Dataset": "low_risk_sample.xlsx"
    }

    for description, file_name in sample_files.items():
        if os.path.exists(file_name):
            with open(file_name, "rb") as file:
                btn = st.sidebar.download_button(
                    label=f"Download {description}",
                    data=file,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.sidebar.error(f"Sample file '{file_name}' not found. Please ensure it is placed in the app directory.")

def main():
    st.title("DVH Calculator & Survival Analysis Tool")
    st.write("""
        **Upload a CSV or Excel file for a cumulative DVH table to calculate Dcc(Gy), D%(Gy), VGy(cc), and VGy(%) metrics.**
        
        The app will notify if the patient is in a high-risk group based on `D10cc(Gy)` and `V60Gy(cc)` metrics and display the corresponding survival curves.
        
        **Sidebar Controls:** After uploading and processing the DVH data, use the sidebar to manually add or remove survival curves as desired, regardless of the patient's risk group.
    """)

    # Provide download buttons for sample datasets
    provide_sample_downloads()

    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx', 'xls'])

    if uploaded_file is not None:
        
        # Reset the file pointer to the beginning
        uploaded_file.seek(0)

        # Process the uploaded file
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            Dcc_df, D_percent_df, Vcc_df, V_percent_df = process_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            Dcc_df, D_percent_df, Vcc_df, V_percent_df = process_csv(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or Excel file.")
            Dcc_df, D_percent_df, Vcc_df, V_percent_df = None, None, None, None

        # If processing was successful, display the metrics
        if Dcc_df is not None and D_percent_df is not None and Vcc_df is not None and V_percent_df is not None:
            st.write("## Dcc(Gy) Metrics")
            st.dataframe(Dcc_df)

            st.write("## D%(Gy) Metrics")
            st.dataframe(D_percent_df)

            st.write("## VGy(cc) Metrics")
            st.dataframe(Vcc_df)

            st.write("## VGy(%) Metrics")
            st.dataframe(V_percent_df)

            # Determine the risk group
            is_high_risk, high_risk_messages, risk_details = determine_risk_group(Dcc_df, Vcc_df)

            # Display risk group notifications
            st.write("## Risk Group Notifications")
            if is_high_risk:
                for message in high_risk_messages:
                    st.warning(message)
            else:
                st.success("Patient does not meet any high-risk criteria based on D10cc(Gy) and V60Gy(cc).")

            # Load survival data
            survival_datasets = load_survival_data()

            # Create a dictionary to map criteria to their risk flags
            risk_group_flags = {
                'D10cc(Gy)': 'D10cc' in risk_details,
                'V60Gy(cc)': 'V60Gy' in risk_details
            }

            # Plot survival curves based on selected survival keys
            plot_survival_curves(survival_datasets, risk_group_flags)

if __name__ == "__main__":
    main()
