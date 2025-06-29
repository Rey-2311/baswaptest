import streamlit as st
import base64
import binascii
import folium
from streamlit_folium import st_folium
from datetime import datetime
from googleapiclient.errors import HttpError

from config import SECRET_ACC, COMBINED_ID, APP_TEXTS, COL_NAMES
from utils.drive_handler import DriveManager
from data import combined_data_retrieve, thingspeak_retrieve
from sidebar import sidebar_inputs
from aggregation import filter_data, apply_aggregation
from plotting import plot_line_chart, display_statistics

st.set_page_config(page_title="BASWAP", page_icon="💧", layout="wide")

# ── Secret & File ID Debug ────────────────────────────────────────────────────
st.markdown("## 🔧 Secret & File ID Debug")
raw = SECRET_ACC.strip()
st.write("First 100 chars of SECRET_ACC:", raw[:100])
try:
    decoded = base64.b64decode(raw, validate=True)
    info = decoded.decode("utf-8")
    st.success(f"SECRET_ACC is valid Base64 (decoded length: {len(decoded)} bytes)")
    # extract client_email from the JSON
    import json
    svc_info = json.loads(info)
    st.write("Service account email in key:", svc_info.get("client_email"))
except Exception as e:
    st.error(f"SECRET_ACC decode or JSON parse failed: {e}")

st.write("COMBINED_ID:", COMBINED_ID)

# ── Initialize DriveManager ───────────────────────────────────────────────────
dm = DriveManager(SECRET_ACC)

# ── File Listing Across All Drives Debug ───────────────────────────────────────
st.markdown("### 📄 File Listing (All Drives) Debug")
try:
    results = dm.drive_service.files().list(
        pageSize=20,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields="files(id, name, driveId)"
    ).execute()
    files = results.get("files", [])
    if not files:
        st.warning("No files visible (in My Drive or Shared Drives).")
    else:
        st.write("Files visible across all Drives:")
        for f in files:
            drv = f.get("driveId") or "MyDrive"
            st.write(f"- {f['name']}  (ID: {f['id']}, Drive: {drv})")
except Exception as e:
    st.error(f"Failed to list files across all Drives: {e}")

# ── Permissions Check on the Specific File ────────────────────────────────────
st.markdown("### 🔐 File Permissions Debug")
try:
    perms = dm.drive_service.permissions().list(
        fileId=COMBINED_ID,
        supportsAllDrives=True,
        fields="permissions(id, type, role, emailAddress)"
    ).execute().get("permissions", [])
    if not perms:
        st.warning("No permissions entries found for this file.")
    else:
        st.write("Permissions on the file:")
        for p in perms:
            st.write(f"- {p.get('type')} {p.get('role')} {p.get('emailAddress')}")
except HttpError as e:
    st.error(f"Permissions lookup failed: {e}")

# ── Drive File Metadata Check ─────────────────────────────────────────────────
st.markdown("### 🔍 Drive File Metadata Check")
try:
    meta = dm.drive_service.files().get(
        fileId=COMBINED_ID,
        supportsAllDrives=True,
        fields="id,name,owners"
    ).execute()
    st.success(f"✅ Metadata fetched! File name: {meta['name']} (ID: {meta['id']})")
    st.write("Owners:", [o.get("emailAddress") for o in meta.get("owners", [])])
except HttpError as e:
    st.error(f"Metadata lookup failed: {e}")

# ── CSV Read Debug ─────────────────────────────────────────────────────────────
st.markdown("### 📥 CSV Read Debug")
try:
    df_test = dm.read_csv_file(COMBINED_ID)
    st.success(f"DriveManager read_csv_file OK (shape: {df_test.shape})")
except Exception as e:
    st.error(f"DriveManager read_csv_file failed: {e}")

# ── UI Header & Navigation ────────────────────────────────────────────────────
st.markdown("""
<style>
header { visibility: hidden; }
.custom-header {
    position: fixed; top: 0; left: 0; right: 0;
    height: 4.5rem; display: flex; align-items: center;
    padding: 0 1rem; background: #fff;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    z-index: 1000; gap: 2rem;
}
.custom-header .logo {
    font-size: 1.65rem; font-weight: 600; color: #000;
}
.custom-header .nav { display: flex; gap: 1rem; }
.custom-header .nav a {
    text-decoration: none; color: #262730;
    font-size: 0.9rem; padding-bottom: 0.25rem;
    border-bottom: 2px solid transparent;
}
.custom-header .nav a.active { color: #09c; border-bottom-color: #09c; }
body > .main { margin-top: 4.5rem; }
</style>
""", unsafe_allow_html=True)

qs   = st.query_params
page = qs.get("page", "Overview")
lang = qs.get("lang", "vi")
if page not in ("Overview", "About"): page = "Overview"
if lang not in ("en", "vi"): lang = "vi"
toggle_lang  = "en" if lang == "vi" else "vi"
toggle_label = APP_TEXTS[lang]["toggle_button"]

st.markdown(f"""
<div class="custom-header">
  <div class="logo">BASWAP</div>
  <div class="nav">
    <a href="?page=Overview&lang={lang}" class="{'active' if page=='Overview' else ''}" target="_self">Overview</a>
    <a href="?page=About&lang={lang}"    class="{'active' if page=='About'    else ''}" target="_self">About</a>
  </div>
  <div class="nav" style="margin-left:auto;">
    <a href="?page={page}&lang={toggle_lang}" target="_self">{toggle_label}</a>
  </div>
</div>
""", unsafe_allow_html=True)

texts = APP_TEXTS[lang]

if page == "Overview":
    m = folium.Map(location=[10.231140, 105.980999], zoom_start=8)
    st_folium(m, width="100%", height=400)

    st.title(texts["app_title"])
    st.markdown(texts["description"])

    df = combined_data_retrieve()
    df = thingspeak_retrieve(df)
    first_date = datetime(2025, 1, 17).date()
    last_date  = df["Timestamp (GMT+7)"].max().date()

    date_from, date_to, target_col, agg_functions = sidebar_inputs(
        df, lang, first_date, last_date
    )
    filtered_df = filter_data(df, date_from, date_to)
    display_statistics(filtered_df, target_col)

    def display_view(df, target_col, view_title, resample_freq, selected_cols, agg_functions):
        st.subheader(view_title)
        if resample_freq == "None":
            view_df = df.copy()
        else:
            view_df = apply_aggregation(df, selected_cols, target_col, resample_freq, agg_functions)
        plot_line_chart(view_df, target_col, resample_freq)

    display_view(filtered_df, target_col, f"{texts['raw_view']} {target_col}", "None", COL_NAMES, agg_functions)
    display_view(filtered_df, target_col, f"{texts['hourly_view']} {target_col}", "Hour", COL_NAMES, agg_functions)
    display_view(filtered_df, target_col, f"{texts['daily_view']} {target_col}", "Day", COL_NAMES, agg_functions)

    st.subheader(texts["data_table"])
    selected_table_cols = st.multiselect(texts["columns_select"], options=COL_NAMES, default=COL_NAMES)
    selected_table_cols.insert(0, "Timestamp (GMT+7)")
    st.write(f"{texts['data_dimensions']} ({filtered_df.shape[0]}, {len(selected_table_cols)}).")
    st.dataframe(filtered_df[selected_table_cols], use_container_width=True)

    st.button(texts["clear_cache"], help="Clears cached data for fresh fetch.", on_click=st.cache_data.clear)
else:
    st.title("About")
    st.markdown("""
**BASWAP** is a buoy-based water-quality monitoring dashboard for Vinh Long, Vietnam.
You can add team info, data sources, contact details, or whatever you like here.
""")
