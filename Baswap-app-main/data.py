import os
import sys
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from config import GMT7, UTC, THINGSPEAK_URL, COMBINED_ID, SECRET_ACC

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils")))
from utils import DriveManager

def convert_utc_to_GMT7(timestamp):
    return timestamp.replace(tzinfo=UTC).astimezone(GMT7)

@st.cache_data(ttl=86400)
def combined_data_retrieve():
    drive_handler = DriveManager(SECRET_ACC)
    df = drive_handler.read_csv_file(COMBINED_ID)

    ts = pd.to_datetime(df["Timestamp (GMT+7)"], utc=True, errors="coerce")
    if ts.isna().any():
        mask = ~ts.isna()
        df = df.loc[mask].copy()
        ts = ts.loc[mask]
    df["Timestamp (GMT+7)"] = ts.dt.tz_convert("Asia/Bangkok")
    return df

def fetch_thingspeak_data(results):
    url = f"{THINGSPEAK_URL}?results={results}"
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)["feeds"]
    else:
        st.error("Failed to fetch data from Thingspeak API")
        return []

def append_new_data(df, feeds):
    last_timestamp = df.iloc[-1, 0]
    for feed in feeds:
        timestamp = feed.get("created_at", "")
        if not timestamp:
            continue
        utc_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        gmt7_time = convert_utc_to_GMT7(utc_time)
        if gmt7_time > last_timestamp:
            df.loc[len(df)] = [
                gmt7_time,
                float(feed.get("field1", 0)),
                float(feed.get("field2", 0)),
                int(feed.get("field3", 0)),
                float(feed.get("field4", 0)),
                float(feed.get("field5", 0)),
                int(feed.get("field3", 0)) / 2000,
            ]
    df = df.sort_values("Timestamp (GMT+7)").reset_index(drop=True)
    return df

def thingspeak_retrieve(df):
    today = datetime.now(GMT7).date()
    date_diff = (today - df.iloc[-1, 0].date()).days
    results = 150 * date_diff
    feeds = fetch_thingspeak_data(results)
    return append_new_data(df, feeds)
