import streamlit as st, base64, json, folium, binascii
from streamlit_folium import st_folium
from googleapiclient.errors import HttpError
from datetime import datetime

from config import SECRET_ACC, COMBINED_ID, APP_TEXTS, COL_NAMES
from utils.drive_handler import DriveManager
from data import combined_data_retrieve, thingspeak_retrieve
from sidebar import sidebar_inputs
from aggregation import filter_data, apply_aggregation
from plotting import plot_line_chart, display_statistics

st.set_page_config(page_title="BASWAP", page_icon="💧", layout="wide")

# ── compact key sanity ────────────────────────────────────────────────────────
try:
    svc_info  = json.loads(base64.b64decode(SECRET_ACC, validate=True))
    svc_email = svc_info.get("client_email", "unknown")
    st.write("✅ service-acct:", svc_email)
except (binascii.Error, json.JSONDecodeError) as e:
    st.error(f"❌ SERVICE_ACCOUNT malformed: {e}")

dm = DriveManager(SECRET_ACC)

# ── quick drive visibility ────────────────────────────────────────────────────
st.markdown("### 🔍 Drive visibility")
try:
    files = dm.drive_service.files().list(
        pageSize=10, supportsAllDrives=True, includeItemsFromAllDrives=True,
        fields="files(id,name)"
    ).execute().get("files", [])
    if not files:
        st.warning("No files visible to service account.")
    else:
        for f in files: st.write(f"{f['name']} — {f['id']}")
except Exception as e:
    st.error(f"List error: {e}")

# specific file sanity
try:
    meta = dm.drive_service.files().get(
        fileId=COMBINED_ID, supportsAllDrives=True,
        fields="id,name"
    ).execute()
    st.success(f"Found target file: {meta['name']}")
except HttpError as e:
    st.error(f"Target file lookup failed: {e}")

# ── main app header ───────────────────────────────────────────────────────────
st.markdown("""
<style>
header{visibility:hidden}.custom-header{position:fixed;top:0;left:0;right:0;height:4.5rem;
display:flex;align-items:center;padding:0 1rem;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.1);z-index:1000;gap:2rem}
.custom-header .logo{font-size:1.65rem;font-weight:600;color:#000}
.custom-header .nav{display:flex;gap:1rem}
.custom-header .nav a{font-size:.9rem;color:#262730;text-decoration:none;border-bottom:2px solid transparent;padding-bottom:.25rem}
.custom-header .nav a.active{color:#09c;border-bottom-color:#09c}
body>.main{margin-top:4.5rem}
</style>
""", unsafe_allow_html=True)

qs   = st.query_params
page = qs.get("page","Overview")
lang = qs.get("lang","vi")
if page not in ("Overview","About"): page="Overview"
if lang not in ("en","vi"): lang="vi"
toggle_lang  = "en" if lang=="vi" else "vi"
toggle_label = APP_TEXTS[lang]["toggle_button"]

st.markdown(f"""
<div class="custom-header">
  <div class="logo">BASWAP</div>
  <div class="nav">
    <a href="?page=Overview&lang={lang}" class="{ 'active' if page=='Overview' else ''}" target="_self">Overview</a>
    <a href="?page=About&lang={lang}"    class="{ 'active' if page=='About'    else ''}" target="_self">About</a>
  </div>
  <div class="nav" style="margin-left:auto;">
    <a href="?page={page}&lang={toggle_lang}" target="_self">{toggle_label}</a>
  </div>
</div>
""", unsafe_allow_html=True)

texts = APP_TEXTS[lang]

# ── pages ─────────────────────────────────────────────────────────────────────
if page=="Overview":
    st_folium(folium.Map(location=[10.23114,105.980999],zoom_start=8),width="100%",height=400)

    st.title(texts["app_title"])
    st.markdown(texts["description"])

    df = combined_data_retrieve()
    df = thingspeak_retrieve(df)
    first_date=datetime(2025,1,17).date()
    last_date = df["Timestamp (GMT+7)"].max().date()

    date_from,date_to,target_col,agg_functions = sidebar_inputs(df,lang,first_date,last_date)
    filtered_df = filter_data(df,date_from,date_to)
    display_statistics(filtered_df,target_col)

    def view(df,title,freq):
        st.subheader(title)
        view_df = df if freq=="None" else apply_aggregation(df,COL_NAMES,target_col,freq,agg_functions)
        plot_line_chart(view_df,target_col,freq)

    view(filtered_df,f"{texts['raw_view']} {target_col}","None")
    view(filtered_df,f"{texts['hourly_view']} {target_col}","Hour")
    view(filtered_df,f"{texts['daily_view']} {target_col}","Day")

    st.subheader(texts["data_table"])
    cols = st.multiselect(texts["columns_select"],options=COL_NAMES,default=COL_NAMES)
    st.dataframe(filtered_df[["Timestamp (GMT+7)",*cols]],use_container_width=True)
    st.button(texts["clear_cache"],on_click=st.cache_data.clear)
else:
    st.title("About")
    st.markdown("""
**BASWAP** is a buoy-based water-quality monitoring dashboard for Vinh Long, Vietnam.
""")
