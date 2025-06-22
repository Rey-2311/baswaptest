import logging
import logging.handlers
import requests
import json
import csv
import os
import sys
import pytz
import pandas as pd
from datetime import date, timedelta, datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils")))
from drive_handler import DriveManager

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

COMBINED_FILENAME = "combined_data.csv"
COMBINED_ID = os.environ["FILE_ID"]

if __name__ == "__main__":
    drive_handler = DriveManager(os.environ["SERVICE_ACCOUNT"])
    df = drive_handler.read_csv_file(COMBINED_ID)

    extracted_date = date.today()  # Default time zone is UTC so at 1am in UTC+7, it is still counted as yesterday
    # extracted_date = date.today() - timedelta(days=1) # Default extracted_date to yesterday 

    #Uncomment the following line to choose a custom date manually
    # extracted_date = date(2024, 10, 4)  # Example: Custom date (YYYY, MM, DD)

    date_difference = (date.today() - extracted_date).days + 1

    # Generate a dynamic filename by the current day
    csv_filename = os.path.join(f'{extracted_date.strftime("%Y-%m-%d")}.csv')

    # approximately 150 measurements a day
    url = f"https://api.thingspeak.com/channels/2652379/feeds.json?results={150 * date_difference}" 
    csv_data = [['Timestamp (GMT+7)', 'DO Value', 'DO Temperature', 'EC Value (us/cm)', 'EC Temperature', 'Battery Voltage']]  # CSV header

    response = requests.get(url)
    data = json.loads(response.text)

    # Timezones: UTC (GMT+0) and target timezone (GMT+7)
    utc_tz = pytz.timezone('UTC')
    gmt_plus_7_tz = pytz.timezone('Asia/Bangkok')  # GMT+7

    for feed in data['feeds']:
        timestamp = feed.get('created_at', '')

        if timestamp:
            # Parse the timestamp in UTC (GMT+0)
            utc_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc_tz)

            # Convert the UTC time to GMT+7
            gmt_plus_7_time = utc_time.astimezone(gmt_plus_7_tz)

            # Get the date in GMT+7
            gmt_plus_7_date = gmt_plus_7_time.date()

            # Only append if the date in GMT+7 matches the extracted_date
            if gmt_plus_7_date == extracted_date:
                csv_data.append([
                    gmt_plus_7_time,         # Timestamp in GMT
                    feed.get('field1', ''),  # DO value
                    feed.get('field2', ''),  # DO temperature
                    feed.get('field3', ''),  # EC value (us/cm)
                    feed.get('field4', ''),  # EC temperature
                    feed.get('field5', ''),   # Battery Voltage
                    str(float(feed.get('field3', '')) / 2000),  # EC value (g/l)
                ])

                ''' Combine data '''
                if (gmt_plus_7_time > pd.to_datetime(df.iloc[-1, 0])):
                    df.loc[len(df)] = [
                            gmt_plus_7_time,         # Timestamp in GMT
                            feed.get('field1', ''),  # DO value
                            feed.get('field2', ''),  # DO temperature
                            feed.get('field3', ''),  # EC value (us/cm)
                            feed.get('field4', ''),  # EC temperature
                            feed.get('field5', ''),   # Battery Voltage
                            str(float(feed.get('field3', '')) / 2000),  # EC value (g/l)
                        ]

    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)

    df.to_csv(COMBINED_FILENAME, index=False)  # Save without the index column

    print(f'Data successfully saved to {csv_filename}')
    logger.info(f'Data of thinkspeak successfully saved to {csv_filename}')

    drive_handler.upload_file(csv_filename, "1YtqvPlqmHrxI5oHlBBq_FgO2vQhi76A-")
    drive_handler.upload_file(COMBINED_FILENAME, "1YtqvPlqmHrxI5oHlBBq_FgO2vQhi76A-", COMBINED_ID)