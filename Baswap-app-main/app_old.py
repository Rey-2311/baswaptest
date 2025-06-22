import streamlit as st
import os
import sys
import requests
import json
import pytz
import pandas as pd
import altair as alt
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils")))
from drive_handler import DriveManager

# Constants
GMT7 = pytz.timezone("Asia/Bangkok")
UTC = pytz.utc
THINGSPEAK_URL = "https://api.thingspeak.com/channels/2652379/feeds.json"
COMBINED_FILENAME = "combined_data.csv"
# COMBINED_ID = st.secrets["FILE_ID"]
# SECRET_ACC = st.secrets["SERVICE_ACCOUNT"]
SECRET_ACC = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAiYmFzd2FwIiwKICAicHJpdmF0ZV9rZXlfaWQiOiAiMThhMjVlNDRiNDIxMjQxMmYwMDQ0YzYyZTliNGY4ZWIzMmM5ZDdhNCIsCiAgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZnSUJBREFOQmdrcWhraUc5dzBCQVFFRkFBU0NCS2d3Z2dTa0FnRUFBb0lCQVFDWklnM3VwWHdoUWdRM1xuWFpzVnQzRCtXNHpYdFV3U1J1ejZVWFhlQUZIcDR5Wm8vbkpYRE5sRzdPaDdIWW1oSHlGeHlUc2N3b09hSVNQR1xuOER1R2w1R3Ewd0ZQcDJ6V3pTNXlYb3FMdEp3Q2QvU0xTbjc2cDJBRlZtZUg5cXJDcVkrUXhIYnlWMnlPTml0RFxuTEVqeVlPNEFCQ20rdU53UXZrTi9Sc1RDaHlOWEhlYUlPSUp1MEIrbHd4ejdhVGxWWkhOalMzT3BGaFgycE80Vlxub3VxMEh6eUdzQTZYQ3FVM3ZoOHlJeU1CbEd3THpSRUVIeUluMytpbHZkaS94OGYvSEZnODlHQll6VDlWQjNYWFxueU1UTksySU5IV2RxbW54WENSdUNXSEIxRmxObVd5STAyVElCb0Q3cXplYjBIb1lKTldYSWJzNVY0N2tKYmxOaFxuTkh6dU9sTFBBZ01CQUFFQ2dnRUFDQ0dleThWTnloWlBVd0ZOY3VIQ3hqN21RNjRFMUJPZ0VjcXhqNUJFeVQ2ZVxuazRTdlhaLzVDYU1hMVM3RVdDSG5ETHU2djlRMFdNTFp1MzZXS3BkeHpMaFhvWHNxZEYyQTBlSGpTWGZWc092ZFxudUdmRVJsc001anVvVTdmdGFWakhudEJQNEo1enpUbGpJclgvU1orTUE4UTAwMFBOcTdYdXI1dDZaem4xem5KYVxuNjY3eFhHMzQvV1dTQTB5THZ1K1RsWUZ0WFRpNmhLUlNQVnNSMVhwVk1BdWdEdzArdzVYUmQxY3lvUFJsY1dReFxuSDRrVDFPem9UT2htU1lCWHFrd2tVd3l5c291NldRY3ZEcUdaTldaeDY0WUthRUsremlyU3p2UUhweDlidkxiOFxuQW91NUkzbXlXR3JiNkd2V09hVXdHUGxFaUpWbmdhZ1lVUFNFbWVydGdRS0JnUURXUUROeTlDTFlRZDhsSTNSRFxua1RuejdPSldoK0lWN3IwQUQyK2ZGeXlldlZLNmExbXdIVlFnUkpoNkNCcHh6c2ZxU0hQcTZodkxuem1jcWZYb1xuZ2NEcTIrTDBMOTJTdkpyd2FyQTRFVnJKRUVxZ25tOHlSL2RGdk1tcGMzSkFOWDJDMjVJM2NGR1oyNXBCMEVpeFxucm82M1kyQ3hEcEhINHV3RTJiRm1wMTJUSndLQmdRQzIrUVhkeS9DTzhLWTM3VC9GUUs5UW1NT0lWazhYTFJFMVxuSEN4SysvcW95eEgrRFVtS2hjWUZCWjhjNWlDa2VyRm1CSHRNa3d1RzBxMHg4TmhDd01GWEUwOWhuMWQ2ejZGNlxuL21pWktucTV6SkdheU5qM21kWlMvaVBGbVBXcXVjbVBXTFZZeVpoZVNINFJMd2toQzRwT0E5bnJ0VHBsSjdjZ1xuakhQM00zbnNHUUtCZ1FETU9XcFJXeEdUM2taY1drMUswclhSSTY0a0dXYVN6WHp1LzhmQWVCQ2FSNUVDRGEzeVxuU0NLV2w0eFlWajBPMnJLSlNnTGttNzllK3ltcGdnRGJYa09NRzRsY2hmdkpFV3NIWEVzWlJzR3BBcFNBUWtWd1xuUWxVYjduYXp4VTNVa3FoUEFnbUFPdG90dEx4M201aVBkZnFvS0Z4VXFiU2dPbGdMejQ1Z2NZeXE1UUtCZ0ZESFxuNUtVbGt0RW93ZG5UTHVKaFNvVmt6SDcyeS9oSmQxMWhVTlRTSnJvNjNYaXlXUk9GT0FXams3bm9oK1RXSGxnU1xuQm5XcVBkNktTTmpSb2tqbVhQV2FtdU5ZdkFDR2hwNk1qNVYvd2FzaCsrN0FXYm9HK3k2czhSSWVFK2dLR2tqbFxuT3pzMTFjVmFiLzRhTEFlZzFyRFcxbkZRRTdYeE1OSjM4QUxsZ1NDUkFvR0JBTks2SnJFb0JhVzgrdCtnY3hQOVxuUXQvS0FFWW1xKy81d1YzOGJGbGhvSDhCS0swTURwVTZUUDc2VnR6aUVpcDFxSjY3VFg2bi9idVZ6aWJJai85SVxuZ1hJRFNlRDVWWHhHdkQ3cFArUm9kOTZ2cWNNREgycUF4aEs1WDk4S0FCRlZnR2tSQ2pxaXBhdStrOVpyOU1OL1xueHZieUU1Q3JqY1I5aEtMQndTSjJ3cDlJXG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLAogICJjbGllbnRfZW1haWwiOiAiYmFzd2FwLWRyaXZlQGJhc3dhcC5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMTMzOTQ5MjM5MjM1ODY4Mjg3ODQiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L2Jhc3dhcC1kcml2ZSU0MGJhc3dhcC5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgInVuaXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIKfQo="
COMBINED_ID = "19Ku74Co8_V-Y-Wwan5Qf6cfS4QlUCl72"

def convert_utc_to_GMT7(timestamp):
    """Convert UTC timestamp to GMT+7."""
    return timestamp.replace(tzinfo=UTC).astimezone(GMT7)

# Data Retrieval from Google Drive
@st.cache_data(ttl=86400)
def combined_data_retrieve():
    drive_handler = DriveManager(SECRET_ACC)
    df = drive_handler.read_csv_file(COMBINED_ID)
    df["Timestamp (GMT+7)"] = pd.to_datetime(df["Timestamp (GMT+7)"], utc=True).dt.tz_convert("Asia/Bangkok")
    return df

# Thingspeak API Data Retrieval
def fetch_thingspeak_data(results):
    url = f"{THINGSPEAK_URL}?results={results}"
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)["feeds"]
    else:
        st.error("Failed to fetch data from Thingspeak API")
        return []

def append_new_data(df, feeds):
    """Append new data from Thingspeak API to DataFrame."""
    last_timestamp = df.iloc[-1, 0]

    for feed in feeds:
        timestamp = feed.get('created_at', '')
        if timestamp:
            utc_time = datetime.strptime(timestamp, r"%Y-%m-%dT%H:%M:%SZ")
            gmt7_time = convert_utc_to_GMT7(utc_time)

            if gmt7_time > last_timestamp:
                df.loc[len(df)] = [
                    gmt7_time,
                    float(feed.get("field1", 0)),
                    float(feed.get("field2", 0)),
                    int(feed.get("field3", 0)),
                    float(feed.get("field4", 0)),
                    float(feed.get("field5", 0)),
                    int(feed.get("field3", 0)) / 2000
                ]

    df["Timestamp (GMT+7)"] = pd.to_datetime(df["Timestamp (GMT+7)"], utc=True).dt.tz_convert("Asia/Bangkok")
    return df

def thingspeak_retrieve(df):
    today = datetime.now(GMT7).date()
    date_diff = (today - df.iloc[-1, 0].date()).days
    results = 150 * date_diff

    feeds = fetch_thingspeak_data(results)
    return append_new_data(df, feeds)

# Sidebar Input Features (Aggregation and Date Range Only)
def sidebar_inputs(df):
    col_names = [col for col in df.columns if col != "Timestamp (GMT+7)"]
    selected_cols = st.sidebar.multiselect("Columns to display in detail", col_names, [name for name in col_names if name not in ["DO Value", "DO Temperature"]])
    selected_cols.insert(0, "Timestamp (GMT+7)")

    target_col = st.sidebar.selectbox("Choose a column to analyze:", [col for col in selected_cols if col != 'Timestamp (GMT+7)'], index=0)

    min_date = datetime(2025, 1, 17).date()  # Fixed first date
    max_date = datetime.now(GMT7).date()  # Today's date

    # Initialize session state variables
    if "date_from" not in st.session_state:
        st.session_state.date_from = max_date
    if "date_to" not in st.session_state:
        st.session_state.date_to = max_date

    # Sidebar buttons
    col1, col2 = st.sidebar.columns(2)
    if col1.button("First Day"):
        st.session_state.date_from = min_date  
    if col2.button("Today"):
        st.session_state.date_from, st.session_state.date_to = max_date, max_date

    # Date input fields
    date_from = st.sidebar.date_input("Date from:", min_value=min_date, max_value=max_date, value=st.session_state.date_from)
    date_to = st.sidebar.date_input("Date to:", min_value=min_date, max_value=max_date, value=st.session_state.date_to)

    # Aggregation options
    agg_functions = st.sidebar.multiselect("Aggregation Functions:", ["Min", "Max", "Median"], ["Min", "Max", "Median"])

    return selected_cols, date_from, date_to, target_col, agg_functions

# Data Filtering
def filter_data(df, date_from, date_to, selected_cols):
    # Filter data by selected date range
    filtered_df = df[(df["Timestamp (GMT+7)"].dt.date >= date_from) & 
                     (df["Timestamp (GMT+7)"].dt.date <= date_to)].copy()

    return filtered_df[selected_cols]

# Aggregation / Resampling Function
def apply_aggregation(df, selected_cols, target_col, resample_freq, agg_functions):
    if resample_freq == "None":
        return df  # No resampling, return original dataframe

    rule_map = {"Hour": "h", "Day": "d"}
    agg_map = {"Min": "min", "Max": "max", "Median": "median"}

    # Ensure only valid aggregation functions are selected
    if not set(agg_functions).issubset(agg_map.keys()):
        st.error("Invalid aggregation functions selected.")
        return df

    # Set timestamp as the index for resampling
    df_resampled = df.set_index("Timestamp (GMT+7)")

    agg_results = []
    for agg_function in agg_functions:
        if agg_function in ["Min", "Max"]:
            idx_func = "idxmin" if agg_function == "Min" else "idxmax"
            grouped = df_resampled.groupby(pd.Grouper(freq=rule_map[resample_freq]))[target_col]
            idx = grouped.apply(lambda x: getattr(x, idx_func)() if not x.empty else None).dropna()
            agg_df = df_resampled.loc[idx].reset_index()
        elif agg_function == "Median":
            agg_series = df_resampled[target_col].resample(rule_map[resample_freq]).median()
            agg_df = agg_series.reset_index()

        agg_df["Aggregation"] = agg_function
        agg_results.append(agg_df)

    return pd.concat(agg_results, ignore_index=True)

# Plotting Function
def plot_line_chart(df, col, resample_freq="None"):
    if col not in df.columns:
        st.error(f"Column '{col}' not found in DataFrame.")
        return
    
    df_filtered = df.copy()

    if resample_freq == "None":
        df_filtered["Aggregation"] = "Raw"
        chart = (
            alt.Chart(df_filtered)
            .mark_line(point=True)
            .encode(
                x=alt.X("Timestamp (GMT+7):T", title="Timestamp"),
                y=alt.Y(f"{col}:Q", title="Value"),
                color=alt.Color("Aggregation:N", title="Aggregation"),
                tooltip=[
                    alt.Tooltip("Timestamp (GMT+7):T", title="Exact Time", format="%d/%m/%Y %H:%M:%S"),
                    alt.Tooltip(f"{col}:Q", title="Value")
                ],
            )
            .interactive()
        )
    else:
        if resample_freq == "Hour":
            df_filtered["Timestamp (Rounded)"] = df_filtered["Timestamp (GMT+7)"].dt.floor('h')
        elif resample_freq == "Day":
            df_filtered["Timestamp (Rounded)"] = df_filtered["Timestamp (GMT+7)"].dt.floor('d')
        else:
            df_filtered["Timestamp (Rounded)"] = df_filtered["Timestamp (GMT+7)"]

        df_filtered["Timestamp (Rounded Display)"] = df_filtered["Timestamp (Rounded)"].dt.strftime(
            r"%H:%M:%S" if resample_freq == "Hour" else "%d/%m/%Y"
        )

        chart = (
            alt.Chart(df_filtered)
            .mark_line(point=True)
            .encode(
                x=alt.X("Timestamp (Rounded):T", title="Timestamp"),
                y=alt.Y(f"{col}:Q", title="Value"),
                color=alt.Color("Aggregation:N", title="Aggregation"),
                tooltip=[
                    alt.Tooltip("Timestamp (Rounded Display):N", title="Rounded Time"),
                    alt.Tooltip("Timestamp (GMT+7):T", title="Exact Time", format="%d/%m/%Y %H:%M:%S"),
                    alt.Tooltip(f"{col}:Q", title="Value"),
                    alt.Tooltip("Aggregation:N", title="Aggregation")
                ]
            )
            .interactive()
        )

    st.altair_chart(chart, use_container_width=True)

def display_statistics(df, target_col):
    """Display statistics based on raw data."""
    st.subheader("**📊 Overall Statistics (Raw Data)**")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Maximum", value=f"{df[target_col].max():.2f}")
    col2.metric(label="Minimum", value=f"{df[target_col].min():.2f}")
    col3.metric(label="Average", value=f"{df[target_col].mean():.2f}")
    col4.metric(label="Std Dev", value=f"{df[target_col].std():.2f}")


def display_view(df, target_col, view_title, resample_freq, selected_cols, agg_functions):
    """Display a view with a line chart only."""
    st.subheader(view_title)
    if resample_freq == "None":
        view_df = df.copy()
    else:
        view_df = apply_aggregation(df, selected_cols, target_col, resample_freq, agg_functions)
    
    plot_line_chart(view_df, target_col, resample_freq)


# Streamlit Layout
def app():
    st.set_page_config(page_title="BASWAP-APP", page_icon="💧", layout="wide")
    st.title("BASWAP APP")
    st.markdown("""
    This app retrieves water quality data from a buoy-based monitoring system in Vinh Long, Vietnam.
    * **Data source:** [Thingspeak](https://thingspeak.mathworks.com/channels/2652379).
    """)

    df = combined_data_retrieve()
    df = thingspeak_retrieve(df)

    selected_cols, date_from, date_to, target_col, agg_functions = sidebar_inputs(df)
    filtered_df = filter_data(df, date_from, date_to, selected_cols)

    # Display overall statistics from raw data only
    display_statistics(filtered_df, target_col)

    # Display three views: Raw, Hourly, and Daily.
    display_view(filtered_df, target_col, f"Raw Data View of {target_col}", resample_freq="None", selected_cols=selected_cols, agg_functions=agg_functions)
    display_view(filtered_df, target_col, f"Hourly Data View of {target_col}", resample_freq="Hour", selected_cols=selected_cols, agg_functions=agg_functions)
    display_view(filtered_df, target_col, f"Daily Data View of {target_col}", resample_freq="Day", selected_cols=selected_cols, agg_functions=agg_functions)

    # Show detailed table for the raw filtered data
    st.subheader("🔍 Data Table")
    st.write(f"Data Dimension: {filtered_df.shape[0]} rows and {filtered_df.shape[1]} columns.")
    st.dataframe(filtered_df, use_container_width=True)

    st.button("Clear Cache", help="This clears all cached data, ensuring the app fetches the latest available information.", on_click=st.cache_data.clear)


if __name__ == "__main__":
    app()
