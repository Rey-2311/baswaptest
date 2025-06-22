import smtplib
import os
import pytz
from datetime import datetime
from email.mime.text import MIMEText

# Load credentials from GitHub Secrets
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = os.environ["BASWAP_EMAIL"]  # Your Gmail address
SMTP_PASSWORD = os.environ["BASWAP_EMAIL_PWD"]  # Your App Password

def send_email(subject, body, to_email):
    """Send an email using Gmail SMTP."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def alert_email(last_recorded_time):
    """Send an alert email if data has not been recorded in the last period."""
    mailing_list = ["10422050@student.vgu.edu.vn", "10222034@student.vgu.edu.vn"]

    gmt_plus_7_tz = pytz.timezone('Asia/Bangkok')  # GMT+7

    # Convert the UTC time to GMT+7
    gmt_plus_7_time = last_recorded_time.astimezone(gmt_plus_7_tz)

     # Get current time in GMT+7
    current_time_gmt_plus_7 = datetime.now(gmt_plus_7_tz)

    time_difference = current_time_gmt_plus_7 - gmt_plus_7_time
    
    subject = "⚠️ Alert: No Data Recorded in the Last Hour"
    body = f"""
    Dear User,

    We have detected that no new data has been recorded in the last {time_difference.total_seconds() / 3600:.2f} hours.
    Please check the system to ensure everything is functioning properly.

    Last recorded timestamp: {gmt_plus_7_time.strftime('%Y-%m-%d %H:%M:%S UTC')}
    Current time: {current_time_gmt_plus_7.strftime('%Y-%m-%d %H:%M:%S UTC')}

    If you believe this is an error, please verify the data source.

    Best regards,  
    Your Monitoring System
    """

    for email in mailing_list:
        send_email(subject, body, email)