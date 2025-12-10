from datetime import date
from pathlib import Path
import sqlite3
import pandas as pd

import project_app
from project_app.data.db import connect_database

#     CONSTANTS

VALID_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
VALID_STATUSES = ['Open', 'In Progress', 'Resolved', 'Closed']

#     VALIDATION HELPERS

def validate_ticket_fields(date_value, ticket_type, priority, status, description):
    """Validate ticket fields before insert/update."""
    if not all([date_value, ticket_type, priority, status, description]):
        raise ValueError("All fields except 'reported_by' are required.")

    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Priority must be one of {VALID_PRIORITIES}.")

    if status not in VALID_STATUSES:
        raise ValueError(f"Status must be one of {VALID_STATUSES}.")


#     CRUD FUNCTIONS

def insert_ticket(date_value, ticket_type, priority, status, description, reported_by=None):
    """Insert a new ticket."""
    validate_ticket_fields(date_value, ticket_type, priority, status, description)

    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tickets
        (date, ticket_type, priority, status, description, reported_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date_value, ticket_type, priority, status, description, reported_by))

    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()

    return ticket_id


def get_all_tickets():
    """Return all tickets as a DataFrame."""
    conn = connect_database()
    df = pd.read_sql_query(
        "SELECT * FROM tickets ORDER BY id DESC", conn
    )
    conn.close()
    return df


def update_ticket(ticket_id, date_value, ticket_type, priority, status, description, reported_by=None):
    """Update an existing ticket."""
    validate_ticket_fields(date_value, ticket_type, priority, status, description)

    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET date = ?, ticket_type = ?, priority = ?, status = ?, description = ?, reported_by = ?
        WHERE id = ?
    """, (date_value, ticket_type, priority, status, description, reported_by, ticket_id))

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    return updated > 0   # True if updated, False if ID not found


def update_ticket_status(ticket_id, new_status):
    """Change the status of a ticket."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Status must be one of {VALID_STATUSES}.")

    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets
        SET status = ?
        WHERE id = ?
    """, (new_status, ticket_id))

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    return updated > 0


def delete_ticket(ticket_id):
    """Delete a ticket by ID."""
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()

    deleted = cursor.rowcount
    conn.close()

    return deleted > 0


#     USER MIGRATION (unchanged structure)

def migrate_users_from_file(filepath="DATA/users.txt"):
    """Migrate users from users.txt to database."""
    filepath = Path(filepath)

    if not filepath.exists():
        print(f"File not found: {filepath}")
        return

    conn = connect_database()
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
    print(f"Migrated {migrated_count} users from {filepath}")
