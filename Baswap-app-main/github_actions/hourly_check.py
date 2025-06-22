import logging
import logging.handlers
import requests
import json
import pytz
from datetime import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils")))
from gmail_handler import alert_email

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

if __name__ == "__main__":
    
    # approximately 150 measurements a day
    url = f"https://api.thingspeak.com/channels/2652379/feeds.json?results=1" 
    csv_data = [['Timestamp (GMT+7)', 'DO Value', 'DO Temperature', 'EC Value (us/cm)', 'EC Temperature', 'Battery Voltage']]  # CSV header

    response = requests.get(url)
    data = json.loads(response.text)

    # Timezones: UTC (GMT+0) and target timezone (GMT+7)
    utc_tz = pytz.timezone('UTC')
    # gmt_plus_7_tz = pytz.timezone('Asia/Bangkok')  # GMT+7

    for feed in data['feeds']:
        timestamp = feed.get('created_at', '')

        if timestamp:
            # Parse the timestamp in UTC (GMT+0)
            utc_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc_tz)

            # # Convert the UTC time to GMT+7
            # gmt_plus_7_time = utc_time.astimezone(gmt_plus_7_tz)

            # # Get the date in GMT+7
            # gmt_plus_7_date = gmt_plus_7_time.date()

            #  # Get current time in GMT+7
            # current_time_gmt_plus_7 = datetime.now(gmt_plus_7_tz)

            # # Check if the timestamp is within the last hour
            # time_difference = current_time_gmt_plus_7 - gmt_plus_7_time

            # Get current time in UTC
            current_time_utc = datetime.now(utc_tz)

            # Parse the timestamp in UTC (GMT+0)
            utc_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc_tz)

            # Check if the timestamp is within the last hour
            time_difference = current_time_utc - utc_time

            if time_difference.total_seconds() >= 3600:
                alert_email(utc_time)