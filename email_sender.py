import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.sender_email = os.getenv("EMAIL_SENDER")
        self.receiver_email = os.getenv("EMAIL_RECEIVER")
        self.password = os.getenv("EMAIL_APP_PASSWORD")
        # Target time logic handled here or in main loop

    def should_send_email(self, last_sent_date_str: str = None) -> bool:
        """
        Checks if it's time to send the email (e.g., 08:00 AM).
        Returns True if we should send, False otherwise.
        """
        now = datetime.now()
        target_time_str = os.getenv("EMAIL_SEND_TIME", "08:00")
        try:
            target_hour, target_minute = map(int, target_time_str.split(":"))
        except ValueError:
            logger.error(f"Invalid EMAIL_SEND_TIME format: {target_time_str}. Defaulting to 08:00.")
            target_hour, target_minute = 8, 0

        # Check if already sent today
        if last_sent_date_str:
            try:
                last_sent = datetime.strptime(last_sent_date_str, "%Y-%m-%d").date()
                if last_sent == now.date():
                    return False
            except ValueError:
                logger.warning(f"Invalid last_sent_date format: {last_sent_date_str}. Assuming not sent today.")

        # Check if current time is past the target time
        if now.hour > target_hour or (now.hour == target_hour and now.minute >= target_minute):
            return True

        return False

    def send_report(self, insights: list) -> bool:
        """
        Formats and sends the email report.
        Returns True if sent successfully, False otherwise.
        """
        if not insights:
            logger.info("No insights to report.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Project 28 - Daily Business Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg["From"] = self.sender_email
        msg["To"] = self.receiver_email

        # Format the email content
        text_content = "Here is your daily business report:\n\n"
        html_content = "<html><body><h2>Daily Business Report</h2><ul>"

        for insight in insights:
            # Handle if insight is a dict or string
            if isinstance(insight, dict):
                 insight_text = insight.get('content', str(insight))
            else:
                 insight_text = str(insight)

            text_content += f"- {insight_text}\n"
            html_content += f"<li>{insight_text}</li>"

        html_content += "</ul></body></html>"

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")

        msg.attach(part1)
        msg.attach(part2)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, self.receiver_email, msg.as_string())

            logger.info("Email sent successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
