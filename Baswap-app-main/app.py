import streamlit as st
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# 1) Your existing page config (must be first Streamlit call)
st.set_page_config(
    page_title="BASWAP", 
    page_icon="💧", 
    layout="wide"
)

# ─────────────────────────────────────────────────────────────────────────────
# 2) Inject CSS for a top nav bar
st.markdown("""
<style>
/* hide default Streamlit header */
header { visibility: hidden; }
/* our custom header */
.custom-header {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 3rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1rem;
    background: #fff;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    z-index: 1000;
}
.custom-header .logo {
    font-size: 1.1rem;
    font-weight: 600;
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
    /* push all content below the header */
    margin-top: 3.5rem;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3) Read the current “page” from URL query-params
qs = st.experimental_get_query_params()
page = qs.get("page", ["Overview"])[0]
if page not in ("Overview", "About"):
    page = "Overview"

# ─────────────────────────────────────────────────────────────────────────────
# 4) Render our header html
st.markdown(f"""
<div class="custom-header">
  <div class="logo">BASWAP</div>
  <div class="nav">
    <a href="?page=Overview" class="{ 'active' if page=='Overview' else '' }">Overview</a>
    <a href="?page=About"    class="{ 'active' if page=='About'    else '' }">About</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 5) Page routing
if page == "Overview":
    # … copy in all of your existing app.py “Overview” code here …
    st.title("Overview")
    # e.g. your data fetch, charts, tables, etc.
else:
    st.title("About")
    st.markdown("""
    **BASWAP** is a buoy-based water-quality monitoring dashboard for Vinh Long, Vietnam.
    You can add team info, data sources, contact details, or whatever you like here.
    """)

# ─────────────────────────────────────────────────────────────────────────────


render_header()
from data import combined_data_retrieve, thingspeak_retrieve
from sidebar import sidebar_inputs
from aggregation import filter_data, apply_aggregation
from plotting import plot_line_chart, display_statistics
from config import COL_NAMES, APP_TEXTS

# Define text dictionaries for English and Vietnamese, including toggle tooltip texts.


# Callback function to update language immediately.
def update_language():
    st.session_state.language = "vi" if st.session_state.language == "en" else "en"
    # st.rerun()

# Initialize session state for language if not set.
if "language" not in st.session_state:
    st.session_state.language = "vi"
lang = st.session_state.language
texts = APP_TEXTS[lang]

# Add CSS to position the toggle button at the top right corner.
st.markdown(
    """
    <style>
        .lang-toggle {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 100;
        }
    </style>
    """, unsafe_allow_html=True
)

# Render the toggle button using a callback and assign the tooltip via the help parameter.
st.markdown('<div class="lang-toggle">', unsafe_allow_html=True)
st.button(label=texts["toggle_button"], 
          on_click=update_language, 
          help=texts["toggle_tooltip"])
st.markdown('</div>', unsafe_allow_html=True)

st.title(texts["app_title"])
st.markdown(texts["description"])

# Data retrieval.
df = combined_data_retrieve()
df = thingspeak_retrieve(df)
col_names = COL_NAMES
first_date = datetime(2025, 1, 17).date()  # Fixed first date
last_date = df['Timestamp (GMT+7)'].max().date()

# Sidebar inputs.
date_from, date_to, target_col, agg_functions = sidebar_inputs(df, lang, first_date, last_date)
filtered_df = filter_data(df, date_from, date_to)

# Display statistics.
display_statistics(filtered_df, target_col)

# Display views: Raw, Hourly, Daily.
def display_view(df, target_col, view_title, resample_freq, selected_cols, agg_functions):
    st.subheader(view_title)
    if resample_freq == "None":
        view_df = df.copy()
    else:
        view_df = apply_aggregation(df, selected_cols, target_col, resample_freq, agg_functions)
    plot_line_chart(view_df, target_col, resample_freq)

display_view(filtered_df, target_col, f"{texts['raw_view']} {target_col}",
             resample_freq="None", selected_cols=col_names, agg_functions=agg_functions)
display_view(filtered_df, target_col, f"{texts['hourly_view']} {target_col}",
             resample_freq="Hour", selected_cols=col_names, agg_functions=agg_functions)
display_view(filtered_df, target_col, f"{texts['daily_view']} {target_col}",
             resample_freq="Day", selected_cols=col_names, agg_functions=agg_functions)

# Data table section with column selector.
st.subheader(texts["data_table"])
selected_table_cols = st.multiselect(
    texts["columns_select"],
    options=col_names,
    default=col_names
)
selected_table_cols.insert(0, "Timestamp (GMT+7)")
st.write(f"{texts['data_dimensions']} ({filtered_df.shape[0]}, {len(selected_table_cols)}).")
st.dataframe(filtered_df[selected_table_cols], use_container_width=True)

st.button(texts["clear_cache"], 
          help="This clears all cached data, ensuring the app fetches the latest available information.", 
          on_click=st.cache_data.clear)
