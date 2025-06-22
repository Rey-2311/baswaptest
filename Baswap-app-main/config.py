import pytz
import streamlit as st

# Timezone constants
GMT7 = pytz.timezone("Asia/Bangkok")
UTC = pytz.utc

# API URLs and filenames
THINGSPEAK_URL = "https://api.thingspeak.com/channels/2652379/feeds.json"
COMBINED_FILENAME = "combined_data.csv"

# Secrets from Streamlit's secrets management
COMBINED_ID = st.secrets["FILE_ID"]
SECRET_ACC = st.secrets["SERVICE_ACCOUNT"]

COL_NAMES = [
    "EC Value (us/cm)",
    "EC Value (g/l)",
    "EC Temperature",
    "Battery Voltage"
]

APP_TEXTS = {
    "en": {
        "app_title": "BASWAP APP",
        "description": """
            This app retrieves water quality data from a buoy-based monitoring system in Vinh Long, Vietnam.
            * **Data source:** [Thingspeak](https://thingspeak.mathworks.com/channels/2652379).
        """,
        "raw_view": "Raw Data View of",
        "hourly_view": "Hourly Data View of",
        "daily_view": "Daily Data View of",
        "data_table": "🔍 Data Table",
        "columns_select": "Select columns to display in the table:",
        "data_dimensions": "Data Dimension (row, column):",
        "clear_cache": "Clear Cache",
        "toggle_button": "Tiếng Việt",  # Label to switch language to Vietnamese.
        "toggle_tooltip": "Nhấn để thay đổi ngôn ngữ"  # Tooltip in Vietnamese.
    },
    "vi": {
        "app_title": "ỨNG DỤNG BASWAP",
        "description": """
            Ứng dụng này truy xuất dữ liệu chất lượng nước từ hệ thống theo dõi trên phao ở Vĩnh Long, Việt Nam.
            * **Nguồn dữ liệu:** [Thingspeak](https://thingspeak.mathworks.com/channels/2652379).
        """,
        "raw_view": "Biểu đồ dữ liệu gốc cho",
        "hourly_view": "Biểu đồ dữ liệu theo giờ cho",
        "daily_view": "Biểu đồ dữ liệu theo ngày cho",
        "data_table": "🔍 Bảng Dữ Liệu",
        "columns_select": "Chọn các cột để hiển thị trong bảng:",
        "data_dimensions": "Kích thước dữ liệu (hàng, cột):",
        "clear_cache": "Xóa Bộ Nhớ Cache",
        "toggle_button": "English",  # Label to switch language to English.
        "toggle_tooltip": "Click to change language"  # Tooltip in English.
    }
}

SIDE_TEXTS = {
    "en": {
        "sidebar_header": "## ⚙️ Graph Settings",
        "sidebar_description": (
            "Use the options below to customize how the data is shown in the charts.\n\n"
            "You can choose what measurement to analyze, set a date range, and select which summary statistics to display in the hourly and daily view."
        ),
        "sidebar_choose_column": "Choose a column to plot:",
        "sidebar_first_day": "First Recorded Day",
        "sidebar_today": "Last Recorded Day",
        "sidebar_start_date": "Start Date (From):",
        "sidebar_end_date": "End Date (To):",
        "sidebar_summary_stats": "Choose summary statistics to calculate (applied in Hourly and Daily views):"
    },
    "vi": {
        "sidebar_header": "## ⚙️ Điều chỉnh biểu đồ",
        "sidebar_description": (
            "Sử dụng các tùy chọn bên dưới để tùy chỉnh cách dữ liệu được hiển thị trong các biểu đồ.\n\n"
            "Bạn có thể chọn chỉ số cần phân tích, khoảng thời gian, và chọn các thống kê để hiển thị trong biểu đồ theo giờ và theo ngày."
        ),
        "sidebar_choose_column": "Chọn cột để lập biểu đồ:",
        "sidebar_first_day": "Ngày đo đầu tiên",
        "sidebar_today": "Ngày đo gần nhất",
        "sidebar_start_date": "Ngày bắt đầu (Từ):",
        "sidebar_end_date": "Ngày kết thúc (Đến):",
        "sidebar_summary_stats": "Chọn các thống kê tóm tắt để tính (áp dụng cho chế độ theo giờ và ngày):"
    }
}