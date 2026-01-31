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
        db_url = os.environ.get("db_url", "")

    init_db(db_url)
