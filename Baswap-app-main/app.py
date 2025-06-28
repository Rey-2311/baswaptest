import streamlit as st
from datetime import datetime
from data import combined_data_retrieve, thingspeak_retrieve
from sidebar import sidebar_inputs
from aggregation import filter_data, apply_aggregation
from plotting import plot_line_chart, display_statistics
from config import COL_NAMES, APP_TEXTS

st.set_page_config(page_title="BASWAP", page_icon="💧", layout="wide")

st.markdown("""<style>
header { visibility: hidden; }
.custom-header {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 4.5rem;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 2rem;
    padding: 0 1rem;
    background: #fff;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    z-index: 1000;
}
.custom-header .logo {
    font-size: 1.65rem;
    font-weight: 600;
    color: #000;
}
.custom-header .nav {
    display: flex;
    gap: 1rem;
}
.custom-header .nav a {
    text-decoration: none;
    color: #262730;
    font-size: 0.9rem;
    padding-bottom: 0.25rem;
    border-bottom: 2px solid transparent;
}
.custom-header .nav a:hover {
    border-bottom-color: #262730;
}
.custom-header .nav a.active {
    color: #09c;
    border-bottom-color: #09c;
}
body > .main {
    margin-top: 5rem;
}
</style>""", unsafe_allow_html=True)

qs = st.query_params
page = qs.get("page", "Overview")
lang = qs.get("lang", "vi")
if page not in ("Overview", "About"):
    page = "Overview"
if lang not in ("en", "vi"):
    lang = "vi"

toggle_lang = "en" if lang == "vi" else "vi"
toggle_label = APP_TEXTS[lang]["toggle_button"]

st.markdown(f"""<div class="custom-header"><div class="logo">BASWAP</div><div class="nav"><a href="?page=Overview&lang={lang}" target="_self" class="{'active' if page=='Overview' else ''}">Overview</a><a href="?page=About&lang={lang}" target="_self" class="{'active' if page=='About' else ''}">About</a></div><div class="nav" style="margin-left:auto;"><a href="?page={page}&lang={toggle_lang}" target="_self">{toggle_label}</a></div></div>""", unsafe_allow_html=True)

if page == "Overview":
    st.markdown("<style>body > .main { margin-top: calc(100vh + 5rem); }</style>", unsafe_allow_html=True)

texts = APP_TEXTS[lang]

if page == "Overview":
    st.title(texts["app_title"])
    st.markdown(texts["description"])
    df = combined_data_retrieve()
    df = thingspeak_retrieve(df)
    first_date = datetime(2025, 1, 17).date()
    last_date = df["Timestamp (GMT+7)"].max().date()
    date_from, date_to, target_col, agg_functions = sidebar_inputs(df, lang, first_date, last_date)
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
    st.button(texts["clear_cache"], help="This clears all cached data, ensuring the app fetches the latest available information.", on_click=st.cache_data.clear)
else:
    st.title("About")
    st.markdown("""**BASWAP** is a buoy-based water-quality monitoring dashboard for Vinh Long, Vietnam. You can add team info, data sources, contact details, or whatever you like here.""")
