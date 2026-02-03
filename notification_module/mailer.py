import os
import smtplib
from email.message import EmailMessage

class Mailer:
    def __init__(self, host=None, port=None, username=None, password=None, sender=None):
        self.host = host or os.environ.get("SMTP_HOST")
        self.port = int(port or os.environ.get("SMTP_PORT", 587))
        self.username = username or os.environ.get("SMTP_USERNAME")
        self.password = password or os.environ.get("SMTP_PASSWORD")
        self.sender = sender or os.environ.get("SMTP_FROM")

    def send(self, to: str, subject: str, body: str) -> bool:
        try:
            msg = EmailMessage()
            msg["From"] = self.sender
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content(body)

            print(f"Connecting to SMTP: {self.host}:{self.port} as {self.sender}...", flush=True)

            with smtplib.SMTP(self.host, self.port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {to}", flush=True)
            return True

        except Exception as e:
            print(f"SMTP Error: {e}", flush=True)
            print(f"Message to be sent: {body}")
            return False