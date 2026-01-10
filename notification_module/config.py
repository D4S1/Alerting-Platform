import os
from dotenv import load_dotenv

load_dotenv()
class SMTPConfig:
    HOST = os.getenv("SMTP_HOST")
    PORT = int(os.getenv("SMTP_PORT", "587"))
    USERNAME = os.getenv("SMTP_USERNAME")
    PASSWORD = os.getenv("SMTP_PASSWORD")
    FROM = os.getenv("SMTP_FROM", USERNAME)


def validate():
    missing = [
        name for name, value in {
            "SMTP_HOST": SMTPConfig.HOST,
            "SMTP_USERNAME": SMTPConfig.USERNAME,
            "SMTP_PASSWORD": SMTPConfig.PASSWORD,
        }.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
