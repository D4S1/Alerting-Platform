import sqlite3
from typing import List, Optional
from contextlib import contextmanager
from dataclasses import dataclass
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


@dataclass
class Admin:
    id: int
    contact_value: str


@dataclass
class Incident:
    id: int
    service_id: int
    status: str


class Database:
    """
    SQLite database access layer for the monitoring system.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_incident(self, incident_id: int) -> Incident:
        """
        Fetch an incident by its ID.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, service_id, status FROM incidents WHERE id = ?",
                (incident_id,)
            ).fetchone()

        return Incident(*row)

    def get_admins(self, service_id: int, role: str) -> List[Admin]:
        """
        Fetch administrators for a service with a given role.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.id, a.contact_value
                FROM admins a
                JOIN service_admins sa ON sa.admin_id = a.id
                WHERE sa.service_id = ? AND sa.role = ?
                """,
                (service_id, role)
            ).fetchall()

        return [Admin(*row) for row in rows]

    def get_admins_by_incident(self, incident_id: int, role: str) -> List[Admin]:
        """
        Fetch administrators for an incident with a given role.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.id, a.contact_value
                FROM admins a
                JOIN service_admins sa ON sa.admin_id = a.id
                JOIN incidents i ON i.service_id = sa.service_id
                WHERE i.id = ? AND sa.role = ?
                """,
                (incident_id, role)
            ).fetchall()

        return [Admin(*row) for row in rows]
    
    def get_service_by_incident(self, incident_id: int)-> Optional[str]:
        """
        Fetch the service name and IP for a given incident.
        """
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT s.name
                FROM incidents i
                JOIN services s ON s.id = i.service_id
                WHERE i.id = ?
                """,
                (incident_id,)
            ).fetchone()

        if not row:
            return None

        return row["name"]


    def insert_contact_attempt(
        self,
        incident_id: int,
        admin_id: int,
        channel: str,
        result: str,
        attempted_at: datetime
    ):
        """
        Store a contact attempt for an incident.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO contact_attempts
                (incident_id, admin_id, channel, result, attempted_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (incident_id, admin_id, channel, result, attempted_at)
            )
            conn.commit()

    def is_incident_acknowledged(self, incident_id: int) -> bool:
        """
        Check whether an incident has been acknowledged.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT status FROM incidents WHERE id = ?",
                (incident_id,)
            ).fetchone()

        return row and row[0] == "acknowledged"

    def get_notified_admins(self, incident_id: int) -> List[Admin]:
        """
        Return all administrators who were notified about the incident.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT a.id, a.contact_value
                FROM admins a
                JOIN contact_attempts ca ON ca.admin_id = a.id
                WHERE ca.incident_id = ?
                """,
                (incident_id,)
            ).fetchall()

        return [Admin(*row) for row in rows]

    def add_service(self, service) -> None:
        """
        Add a new monitored service.
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO services (name, IP, frequency_seconds, alerting_window_seconds)
                VALUES (?, ?, ?, ?)
                """,
                (
                    service.name,
                    service.IP,
                    service.frequency_seconds,
                    service.alerting_window_seconds,
                ),
            )
            conn.commit()

    def delete_service(self, service_id: int) -> bool:
        """
        Delete a service and its administrator mappings.

        Returns True if the service existed, False otherwise.
        """
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM services WHERE id = ?",
                (service_id,),
            )

            if cur.rowcount == 0:
                return False

            conn.execute(
                "DELETE FROM service_admins WHERE service_id = ?",
                (service_id,),
            )
            conn.commit()

        return True

    def update_service_admin(
        self,
        service_id: int,
        admin_id: int,
        role: str,
    ) -> bool:
        """
        Update the administrator assigned to a service for a given role.

        Returns True if updated, False if service/role not found.
        """
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE service_admins
                SET admin_id = ?
                WHERE service_id = ? AND role = ?
                """,
                (admin_id, service_id, role),
            )
            conn.commit()

        return cur.rowcount > 0

    def update_admin_contact(
        self,
        admin_id: int,
        contact_type: str | None,
        contact_value: str | None,
    ) -> bool:
        """
        Update administrator contact details.

        Returns True if admin exists, False otherwise.
        """
        fields = []
        values = []

        if contact_type is not None:
            fields.append("contact_type = ?")
            values.append(contact_type)

        if contact_value is not None:
            fields.append("contact_value = ?")
            values.append(contact_value)

        if not fields:
            return False

        values.append(admin_id)

        with self._connect() as conn:
            cur = conn.execute(
                f"""
                UPDATE admins
                SET {', '.join(fields)}
                WHERE id = ?
                """,
                values,
            )
            conn.commit()

        return cur.rowcount > 0
