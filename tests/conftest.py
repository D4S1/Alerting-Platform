import os
import sqlite3
import pytest
from fastapi.testclient import TestClient

from database.db import Database
from api.main import app
from api.db import get_database


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

        CREATE TABLE incidents (
            id INTEGER PRIMARY KEY,
            service_id INTEGER,
            started_at TEXT,
            ended_at TEXT,
            status TEXT
        );

        CREATE TABLE contact_attempts (
            id INTEGER PRIMARY KEY,
            incident_id INTEGER,
            admin_id INTEGER,
            attempted_at TEXT,
            channel TEXT,
            result TEXT,
            response_at TEXT
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
    conn.execute("INSERT INTO incidents (service_id, started_at, status) VALUES (1, datetime('now'), 'registered')")

    conn.commit()
    conn.close()

    yield TEST_DB

    try:
        os.remove(TEST_DB)
        print("Database removed after test.")
    except Exception as e:
        print(f"Exception while cleaning database: {e}")

@pytest.fixture(scope="function")
def test_database(test_db):
    return Database(test_db)

@pytest.fixture(scope="function")
def client(test_database):
    def override_get_database():
        return test_database

    app.dependency_overrides[get_database] = override_get_database

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
