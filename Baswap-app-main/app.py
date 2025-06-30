import streamlit as st
import base64, json
from googleapiclient.errors import HttpError
import folium
from streamlit_folium import st_folium
from datetime import datetime

from config import SECRET_ACC, COMBINED_ID, APP_TEXTS, COL_NAMES
from utils.drive_handler import DriveManager
from data import combined_data_retrieve, thingspeak_retrieve
from sidebar import sidebar_inputs
from aggregation import filter_data, apply_aggregation
from plotting import plot_line_chart, display_statistics

st.set_page_config(page_title="BASWAP", page_icon="💧", layout="wide")

# ── Minimal Authentication Debug ──────────────────────────────────────────────
st.markdown("## 🔧 Authentication Debug")
try:
    svc_info = json.loads(base64.b64decode(SECRET_ACC).decode("utf-8"))
    st.write("✔️ Parsed key for:", svc_info.get("client_email"))
except Exception as e:
    st.error("❌ SERVICE_ACCOUNT invalid or not Base64-encoded")
    st.stop()

try:
    dm = DriveManager(SECRET_ACC)
    st.write("✔️ DriveManager initialized")
except Exception as e:
    st.error(f"❌ DriveManager init failed: {e}")
    st.stop()

try:
    meta = dm.drive_service.files().get(fileId=COMBINED_ID, fields="id,name").execute()
    st.write("✔️ File accessible:", meta["name"])
except HttpError as e:
    st.error(f"❌ File access failed: {e}")
    st.stop()

# ── App Header & Navigation ───────────────────────────────────────────────────
st.markdown("""
<style>
header { visibility: hidden; }
.custom-header { position: fixed; top:0; left:0; right:0; height:4.5rem;
  display:flex; align-items:center; padding:0 1rem; background:#fff;
  box-shadow:0 1px 2px rgba(0,0,0,0.1); z-index:1000; gap:2rem;
}
.custom-header .logo { font-size:1.65rem; font-weight:600; color:#000; }
.custom-header .nav { display:flex; gap:1rem; }
.custom-header .nav a { text-decoration:none; color:#262730;
  font-size:0.9rem; padding-bottom:0.25rem; border-bottom:2px solid transparent;
}
.custom-header .nav a.active { color:#09c; border-bottom-color:#09c; }
body>.main { margin-top:4.5rem; }
</style>
""", unsafe_allow_html=True)

qs = st.query_params
page = qs.get("page", "Overview")
lang = qs.get("lang", "vi")
if page not in ("Overview","About"): page="Overview"
if lang not in ("en","vi"): lang="vi"
toggle_lang = "en" if lang=="vi" else "vi"
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

# ── Main Pages ────────────────────────────────────────────────────────────────
if page=="Overview":
    m = folium.Map(location=[10.231140,105.980999], zoom_start=8)
    st_folium(m, width="100%", height=400)

    st.title(texts["app_title"])
    st.markdown(texts["description"])

    df = combined_data_retrieve()
    df = thingspeak_retrieve(df)
    first_date = datetime(2025,1,17).date()
    last_date = df["Timestamp (GMT+7)"].max().date()

    date_from,date_to,target_col,agg_functions = sidebar_inputs(df,lang,first_date,last_date)
    filtered_df = filter_data(df,date_from,date_to)
    display_statistics(filtered_df,target_col)

    def display_view(df,col,title,freq,cols,funcs):
        st.subheader(title)
        view_df = df.copy() if freq=="None" else apply_aggregation(df,cols,col,freq,funcs)
        plot_line_chart(view_df,col,freq)

    display_view(filtered_df,target_col,f"{texts['raw_view']} {target_col}","None",COL_NAMES,agg_functions)
    display_view(filtered_df,target_col,f"{texts['hourly_view']} {target_col}","Hour",COL_NAMES,agg_functions)
    display_view(filtered_df,target_col,f"{texts['daily_view']} {target_col}","Day",COL_NAMES,agg_functions)

    st.subheader(texts["data_table"])
    tbl = st.multiselect(texts["columns_select"],options=COL_NAMES,default=COL_NAMES)
    tbl.insert(0,"Timestamp (GMT+7)")
    st.write(f"{texts['data_dimensions']} ({filtered_df.shape[0]}, {len(tbl)})")
    st.dataframe(filtered_df[tbl],use_container_width=True)
    st.button(texts["clear_cache"],help="Clears cache",on_click=st.cache_data.clear)
else:
    st.title("About")
    st.markdown("""
**BASWAP** is a buoy-based water-quality monitoring dashboard for Vinh Long, Vietnam.
Add team info, data sources, or contact details here.
""")
