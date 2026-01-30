from email.message import EmailMessage
import smtplib
from config import SMTPConfig


class Mailer:
    def send(self, to: str, subject: str, body: str) -> bool:
        try:
            msg = EmailMessage()
            msg["From"] = SMTPConfig.FROM
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content(body)

            with smtplib.SMTP(SMTPConfig.HOST, SMTPConfig.PORT) as server:
                server.set_debuglevel(1)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(
                    SMTPConfig.USERNAME,
                    SMTPConfig.PASSWORD
                )
                server.send_message(msg)

            return True
        except Exception as e:
            # TODO: logger
            print(f"SMTP error: {e}")
            return False
