import argparse
import random
import sqlite3
from datetime import timedelta
from typing import Dict

import pandas as pd
from faker import Faker


SEED = 0
faker = Faker()
faker.seed_instance(SEED)
random.seed(SEED)


def generate_services(n: int) -> pd.DataFrame:
    """
    Generate monitored services.

    Args:
        n: Number of services to generate.

    Returns:
        DataFrame containing service definitions.
    """
    df = pd.DataFrame({
        "name": [faker.domain_word() for _ in range(n)],
        "IP": [faker.ipv4() for _ in range(n)],
        "frequency_seconds": [random.choice([30, 60, 120, 300]) for _ in range(n)],
        "alerting_window_seconds": [random.choice([300, 600, 900]) for _ in range(n)],
    })
    df.insert(0, "id", range(1, n + 1))
    return df


def generate_admins(n: int) -> pd.DataFrame:
    """
    Generate administrators with contact details.

    Args:
        n: Number of administrators.

    Returns:
        DataFrame containing administrators.
    """
    contact_types = ["email", "phone"]
    rows = []

    for _ in range(n):
        contact_type = random.choice(contact_types)
        contact_value = (
            faker.email()
            if contact_type == "email"
            else faker.phone_number()
        )

        rows.append({
            "name": faker.name(),
            "contact_type": contact_type,
            "contact_value": contact_value
        })

    df = pd.DataFrame(rows)
    df.insert(0, "id", range(1, n + 1))
    return df


def generate_service_admins(service_ids, admin_ids) -> pd.DataFrame:
    """
    Assign primary and secondary administrators to each service.

    Args:
        service_ids: List of service IDs.
        admin_ids: List of administrator IDs (must be 2x services).

    Returns:
        DataFrame mapping services to administrators.
    """
    if len(admin_ids) != 2 * len(service_ids):
        raise ValueError(
            "Number of administrators must be exactly twice the number of services"
        )

    rows = []
    for i, service_id in enumerate(service_ids):
        rows.append({
            "service_id": service_id,
            "admin_id": admin_ids[2 * i],
            "role": "primary"
        })
        rows.append({
            "service_id": service_id,
            "admin_id": admin_ids[2 * i + 1],
            "role": "secondary"
        })

    return pd.DataFrame(rows)


def generate_incidents(n: int, service_ids) -> pd.DataFrame:
    """
    Generate incidents for services.

    Args:
        n: Number of incidents.
        service_ids: List of service IDs.

    Returns:
        DataFrame containing incidents.
    """
    statuses = ["registered", "acknowledged", "resolved"]
    rows = []

    for _ in range(n):
        start = faker.date_time_between(start_date="-30d", end_date="now")
        status = random.choice(statuses)
        end = (
            start + timedelta(minutes=random.randint(5, 300))
            if status == "resolved"
            else None
        )

        rows.append({
            "service_id": random.choice(service_ids),
            "started_at": start,
            "ended_at": end,
            "status": status
        })

    df = pd.DataFrame(rows)
    df.insert(0, "id", range(1, n + 1))
    return df


def generate_contact_attempts(
    incidents: pd.DataFrame,
    service_admins: pd.DataFrame,
    admins: pd.DataFrame
) -> pd.DataFrame:
    """
    Generate administrator contact attempts for incidents.

    Args:
        incidents: DataFrame of incidents.
        service_admins: Service-to-admin mapping.
        admins: DataFrame of administrators.

    Returns:
        DataFrame containing contact attempts.
    """
    rows = []

    for _, incident in incidents.iterrows():
        inc_id = incident.id
        role = random.choice(["primary", "secondary"])

        primary_admin = admins.iloc[
            service_admins.query(
                'service_id == @incident.service_id and role == "primary"'
            ).admin_id
        ]

        secondary_admin = admins.iloc[
            service_admins.query(
                'service_id == @incident.service_id and role == "secondary"'
            ).admin_id
        ]

        primary_attempted_at = incident.started_at
        secondary_attempted_at = (
            primary_attempted_at + timedelta(minutes=5)
            if role == "secondary"
            else None
        )

        if incident.status in ["acknowledged", "resolved"]:
            rows.append({
                "incident_id": inc_id,
                "admin_id": primary_admin.index.item(),
                "attempted_at": primary_attempted_at,
                "channel": primary_admin.contact_type.item(),
                "result": "acknowledged" if role == "primary" else "ignored",
                "response_at": (
                    primary_attempted_at + timedelta(minutes=1.5)
                    if role == "primary"
                    else None
                )
            })

            if role == "secondary":
                rows.append({
                    "incident_id": inc_id,
                    "admin_id": secondary_admin.index.item(),
                    "attempted_at": secondary_attempted_at,
                    "channel": secondary_admin.contact_type.item(),
                    "result": "acknowledged",
                    "response_at": secondary_attempted_at + timedelta(minutes=1.5)
                })

        else:
            rows.append({
                "incident_id": inc_id,
                "admin_id": primary_admin.index.item(),
                "attempted_at": primary_attempted_at,
                "channel": primary_admin.contact_type.item(),
                "result": None,
                "response_at": None
            })

    return pd.DataFrame(rows)


def generate_data(num_services: int, num_incidents: int) -> Dict[str, pd.DataFrame]:
    """
    Generate a complete test dataset.

    Args:
        num_services: Number of services.
        num_incidents: Number of incidents.

    Returns:
        Dictionary of DataFrames keyed by table name.
    """
    services = generate_services(num_services)
    admins = generate_admins(num_services * 2)
    service_admins = generate_service_admins(
        services['id'].tolist(),
        admins['id'].tolist()
    )
    incidents = generate_incidents(num_incidents, services['id'].tolist())
    contact_attempts = generate_contact_attempts(
        incidents, service_admins, admins
    )

    return {
        "services": services,
        "admins": admins,
        "service_admins": service_admins,
        "incidents": incidents,
        "contact_attempts": contact_attempts,
    }


def save_dfs_to_sqlite(
    dfs: Dict[str, pd.DataFrame],
    db_path: str,
    if_exists: str = "replace"
) -> None:
    """
    Save DataFrames to a SQLite database.

    Args:
        dfs: Dictionary {table_name: DataFrame}.
        db_path: Path to SQLite database file.
        if_exists: Table write mode: replace, append or fail.
    """
    conn = sqlite3.connect(db_path)
    try:
        for table_name, df in dfs.items():
            df.to_sql(
                name=table_name,
                con=conn,
                if_exists=if_exists,
                index=False,
                dtype={"id": "INTEGER PRIMARY KEY"}
            )
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate sample monitoring data and store it in SQLite"
    )

    parser.add_argument(
        "-s", "--n_services",
        type=int,
        required=True,
        help="Number of services to generate"
    )
    parser.add_argument(
        "-i", "--n_incidents",
        type=int,
        required=True,
        help="Number of incidents to generate"
    )
    parser.add_argument(
        "-db", "--db_path",
        type=str,
        required=True,
        help="Path to SQLite database file"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["replace", "append", "fail"],
        default="replace",
        help="SQLite table write mode"
    )

    args = parser.parse_args()

    tables = generate_data(
        num_services=args.n_services,
        num_incidents=args.n_incidents
    )

    save_dfs_to_sqlite(
        dfs=tables,
        db_path=args.db_path,
        if_exists=args.mode
    )
