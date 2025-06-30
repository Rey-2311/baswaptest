import streamlit as st
import base64
from googleapiclient.errors import HttpError
from config import SECRET_ACC, COMBINED_ID, APP_TEXTS, COL_NAMES
from utils.drive_handler import DriveManager
import folium
from streamlit_folium import st_folium
from datetime import datetime
from data import combined_data_retrieve, thingspeak_retrieve
from sidebar import sidebar_inputs
from aggregation import filter_data, apply_aggregation
from plotting import plot_line_chart, display_statistics

st.set_page_config(page_title="BASWAP", page_icon="💧", layout="wide")

# ── Minimal Debug ─────────────────────────────────────────────────────────────
st.markdown("## 🔧 Quick Secret & File Check")

# 1) Secret loaded?
st.write("Secret loaded:", isinstance(SECRET_ACC, str), "length:", len(SECRET_ACC))

# 2) Decode & parse
try:
    raw = base64.b64decode(SECRET_ACC).decode("utf-8")
    svc = __import__("json").loads(raw)
    st.success("Service account JSON parsed; client_email: " + svc.get("client_email", "N/A"))
except Exception as e:
    st.error("Secret decode/parse error: " + str(e))

# 3) Drive metadata
dm = DriveManager(SECRET_ACC)
try:
    meta = dm.drive_service.files().get(
        fileId=COMBINED_ID,
        supportsAllDrives=True,
        fields="id,name"
    ).execute()
    st.success(f"Found file: {meta['name']} (ID: {meta['id']})")
except HttpError as e:
    st.error("Metadata error: " + str(e))

# 4) Read CSV
try:
    df_test = dm.read_csv_file(COMBINED_ID)
    st.success(f"CSV read OK (shape: {df_test.shape})")
except Exception as e:
    st.error("CSV read error: " + str(e))

# ── App Header & Nav ──────────────────────────────────────────────────────────
st.markdown("""
<style>
header { visibility: hidden; }
.custom-header {
  position: fixed; top:0; left:0; right:0; height:4.5rem;
  display:flex; align-items:center; padding:0 1rem; background:#fff;
  box-shadow:0 1px 2px rgba(0,0,0,0.1); z-index:1000; gap:2rem;
}
.custom-header .logo { font-size:1.65rem; font-weight:600; color:#000; }
.custom-header .nav { display:flex; gap:1rem; margin-left:auto; }
.custom-header .nav a { text-decoration:none; color:#262730; font-size:0.9rem; padding-bottom:0.25rem; border-bottom:2px solid transparent; }
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
  <div class="nav">
    <a href="?page={page}&lang={toggle_lang}" target="_self">{toggle_label}</a>
  </div>
</div>
""", unsafe_allow_html=True)

texts = APP_TEXTS[lang]

if page=="Overview":
    m = folium.Map(location=[10.231140,105.980999], zoom_start=8)
    st_folium(m, width="100%", height=400)
    st.title(texts["app_title"])
    st.markdown(texts["description"])
    df = combined_data_retrieve()
    df = thingspeak_retrieve(df)
    first, last = datetime(2025,1,17).date(), df["Timestamp (GMT+7)"].max().date()
    date_from, date_to, target_col, agg = sidebar_inputs(df,lang,first,last)
    fdf = filter_data(df,date_from,date_to)
    display_statistics(fdf,target_col)
    def dv(df_,col,title,freq,cols,agg): 
        st.subheader(title)
        df2 = df_.copy() if freq=="None" else apply_aggregation(df_,cols,col,freq,agg)
        plot_line_chart(df2,col,freq)
    dv(fdf,target_col,f"{texts['raw_view']} {target_col}","None",COL_NAMES,agg)
    dv(fdf,target_col,f"{texts['hourly_view']} {target_col}","Hour",COL_NAMES,agg)
    dv(fdf,target_col,f"{texts['daily_view']} {target_col}","Day",COL_NAMES,agg)
    st.subheader(texts["data_table"])
    tbl = st.multiselect(texts["columns_select"],options=COL_NAMES,default=COL_NAMES)
    tbl.insert(0,"Timestamp (GMT+7)")
    st.write(f"{texts['data_dimensions']} ({fdf.shape[0]}, {len(tbl)})")
    st.dataframe(fdf[tbl],use_container_width=True)
    st.button(texts["clear_cache"],on_click=st.cache_data.clear,help="Clears cached data.")
else:
    st.title("About")
    st.markdown("""
**BASWAP** is a buoy-based water-quality monitoring dashboard for Vinh Long, Vietnam.
You can add team info, data sources, contact details, or whatever you like here.
""")
