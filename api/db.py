import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "database/monitoring.db"

@contextmanager
def get_db(db_path: str = DB_PATH):  # for FastAPI endpoints
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# Database access layer
class Database:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ---------- INCIDENTS ----------

    def get_incident(self, incident_id: int):
        row = self.conn.execute(
            "SELECT * FROM incidents WHERE id = ?",
            (incident_id,)
        ).fetchone()

        return row

    def is_incident_acknowledged(self, incident_id: int) -> bool:
        row = self.conn.execute(
            "SELECT acknowledged_at FROM incidents WHERE id = ?",
            (incident_id,)
        ).fetchone()

        return row and row["acknowledged_at"] is not None

    # ---------- ADMINS ----------

    def get_admins(self, service_id: int, role: str):
        return self.conn.execute(
            """
            SELECT a.*
            FROM admins a
            JOIN service_admins sa ON sa.admin_id = a.id
            WHERE sa.service_id = ?
              AND sa.role = ?
            """,
            (service_id, role)
        ).fetchall()

    def get_admins_by_incident(self, incident_id: int, role: str):
        return self.conn.execute(
            """
            SELECT a.*
            FROM admins a
            JOIN incidents i ON i.service_id = a.service_id
            WHERE i.id = ?
              AND a.role = ?
            """,
            (incident_id, role)
        ).fetchall()

    # ---------- NOTIFICATIONS ----------
    def insert_contact_attempt(
        self,
        incident_id: int,
        admin_id: int,
        channel: str,
        result: str,
        attempted_at: datetime,
    ):
        self.conn.execute(
            """
            INSERT INTO contact_attempts
            (incident_id, admin_id, channel, result, attempted_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                admin_id,
                channel,
                result,
                attempted_at.isoformat(),
            )
        )

    def get_notified_admins(self, incident_id: int):
        return self.conn.execute(
            """
            SELECT DISTINCT a.*
            FROM admins a
            JOIN contact_attempts ca ON ca.admin_id = a.id
            WHERE ca.incident_id = ?
            """,
            (incident_id,)
        ).fetchall()
