import argparse
from sqlalchemy import create_engine
from models import Base


def init_db(db_path: str):
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=True)
    Base.metadata.create_all(engine)
    print(f"Empty production database created at {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True, help="Path to sqlite file")
    args = parser.parse_args()

    init_db(args.db_path)
