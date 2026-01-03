import os
import sqlite3
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api import db as db_module

TEST_DB = "database/test_monitoring.db"

@pytest.fixture(scope="function")
def test_db():
    # Remove existing test database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    conn = sqlite3.connect(TEST_DB)

    # Deterministic schema with PRIMARY KEY
    conn.executescript(
        """
        CREATE TABLE services (
            id INTEGER PRIMARY KEY,
            name TEXT,
            IP TEXT,
            frequency_seconds INTEGER,
            alerting_window_seconds INTEGER
        );

        CREATE TABLE admins (
            id INTEGER PRIMARY KEY,
            name TEXT,
            contact_type TEXT,
            contact_value TEXT
        );

        CREATE TABLE service_admins (
            id INTEGER PRIMARY KEY,
            service_id INTEGER,
            admin_id INTEGER,
            role TEXT
        );
        """
    )

    # Start data
    conn.execute("INSERT INTO admins (name, contact_type, contact_value) VALUES ('Alice', 'email', 'alice@test.com')")
    conn.execute("INSERT INTO admins (name, contact_type, contact_value) VALUES ('Bob', 'email', 'bob@test.com')")
    conn.execute("INSERT INTO admins (name, contact_type, contact_value) VALUES ('Hanna', 'email', 'hanna@test.com')")
    conn.execute("INSERT INTO admins (name, contact_type, contact_value) VALUES ('John', 'email', 'john@test.com')")
    conn.execute("INSERT INTO services (name, IP, frequency_seconds, alerting_window_seconds) VALUES ('svc1', '1.1.1.1', 60, 300)")
    conn.execute("INSERT INTO services (name, IP, frequency_seconds, alerting_window_seconds) VALUES ('svc2', '1.1.1.2', 20, 200)")
    conn.execute("INSERT INTO service_admins (service_id, admin_id, role) VALUES (1, 1, 'primary')")
    conn.execute("INSERT INTO service_admins (service_id, admin_id, role) VALUES (1, 2, 'secondary')")
    conn.execute("INSERT INTO service_admins (service_id, admin_id, role) VALUES (2, 3, 'primary')")
    conn.execute("INSERT INTO service_admins (service_id, admin_id, role) VALUES (2, 4, 'secondary')")


    conn.commit()
    conn.close()

    yield TEST_DB

    try:
        os.remove(TEST_DB)
        print("Database removed after test.")
    except Exception as e:
        print(f"Exception while cleaning database: {e}")

@pytest.fixture(scope="function")
def client(test_db):
    # Dependency override
    def override_get_db():
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    app.dependency_overrides[db_module.get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()