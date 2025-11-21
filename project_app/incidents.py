from datetime import date
from pathlib import Path
import sqlite3
import pandas as pd

from project_app.data.db import connect_database

#     CONSTANTS

VALID_SEVERITIES = ['Low', 'Medium', 'High', 'Critical']
VALID_STATUSES = ['Open', 'In Progress', 'Resolved', 'Closed']

#     VALIDATION HELPERS

def validate_incident_fields(date_value, incident_type, severity, status, description):
    """Validate incident fields before insert/update."""
    if not all([date_value, incident_type, severity, status, description]):
        raise ValueError("All fields except 'reported_by' are required.")

    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Severity must be one of {VALID_SEVERITIES}.")

    if status not in VALID_STATUSES:
        raise ValueError(f"Status must be one of {VALID_STATUSES}.")


#     CRUD FUNCTIONS

def insert_incident(date_value, incident_type, severity, status, description, reported_by=None):
    """Insert a new cyber incident."""
    validate_incident_fields(date_value, incident_type, severity, status, description)

    conn = connect_database()  # Removed db_path parameter
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cyber_incidents 
        (date, incident_type, severity, status, description, reported_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date_value, incident_type, severity, status, description, reported_by))

    conn.commit()
    incident_id = cursor.lastrowid
    conn.close()

    return incident_id


def get_all_incidents():
    """Return all incidents as a DataFrame."""
    conn = connect_database()  # Removed db_path parameter
    df = pd.read_sql_query(
        "SELECT * FROM cyber_incidents ORDER BY id DESC", conn
    )
    conn.close()
    return df

def update_incident(incident_id, date_value, incident_type, severity, status, description, reported_by=None):
    """Update an existing incident."""
    validate_incident_fields(date_value, incident_type, severity, status, description)

    conn = connect_database()  # Removed db_path parameter
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cyber_incidents
        SET date = ?, incident_type = ?, severity = ?, status = ?, description = ?, reported_by = ?
        WHERE id = ?
    """, (date_value, incident_type, severity, status, description, reported_by, incident_id))

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    return updated > 0   # True if updated, False if ID not found


def update_incident_status(incident_id, new_status):
    """Change the status of an incident."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Status must be one of {VALID_STATUSES}.")

    conn = connect_database()  # Removed db_path parameter
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cyber_incidents
        SET status = ?
        WHERE id = ?
    """, (new_status, incident_id))

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    return updated > 0


def delete_incident(incident_id):
    """Delete an incident by ID."""
    conn = connect_database()  # Removed db_path parameter
    cursor = conn.cursor()

    cursor.execute("DELETE FROM cyber_incidents WHERE id = ?", (incident_id,))
    conn.commit()

    deleted = cursor.rowcount
    conn.close()

    return deleted > 0


#     USER MIGRATION (Existing)

def migrate_users_from_file(filepath="DATA/users.txt"):
    """Migrate users from users.txt to database."""
    filepath = Path(filepath)

    if not filepath.exists():
        print(f"File not found: {filepath}")
        return

    conn = connect_database()  # Added connection
    cursor = conn.cursor()
    migrated_count = 0

    with filepath.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(',')
            if len(parts) >= 2:
                username = parts[0].strip()
                password_hash = parts[1].strip()

                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                        (username, password_hash, 'user')
                    )
                    if cursor.rowcount > 0:
                        migrated_count += 1
                except sqlite3.Error as e:
                    print(f"Error migrating user {username}: {e}")

    conn.commit()
    conn.close()
    print(f"Migrated {migrated_count} users from {filepath.name}")