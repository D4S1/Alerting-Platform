from database.db import Database

def get_database() -> Database:
    return Database("database/monitoring.db")
