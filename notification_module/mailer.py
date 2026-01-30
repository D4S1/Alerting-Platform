from email.message import EmailMessage
import smtplib


class Mailer:
    def __init__(self, host=None, port=None, username=None, password=None, sender=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender

    def send(self, to: str, subject: str, body: str) -> bool:
        try:
            msg = EmailMessage()
            msg["From"] = self.sender
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content(body)

            with smtplib.SMTP(self.host, self.port) as server:
                server.set_debuglevel(1)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(
                    self.username,
                    self.password
                )
                server.send_message(msg)

            return True
        except Exception:
            return False
