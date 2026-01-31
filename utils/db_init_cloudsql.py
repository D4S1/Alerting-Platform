import argparse
import os
from sqlalchemy import create_engine
from models import Base


def init_db(db_url: str):
    engine = create_engine(
        db_url,
        echo=True,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(engine)
    print("Empty production database created successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url")
    args = parser.parse_args()

    if args.db_url:
        db_url = args.db_url
    else:
        db_user = os.environ["DB_USER"]
        db_pass = os.environ["DB_PASSWORD"]
        db_name = os.environ["DB_NAME"]
        db_host = os.environ["DB_HOST"]  # /cloudsql/PROJECT:REGION:INSTANCE

        db_url = (
            f"postgresql+psycopg2://{db_user}:{db_pass}"
            f"@{db_host}/{db_name}"
        )

    init_db(db_url)
