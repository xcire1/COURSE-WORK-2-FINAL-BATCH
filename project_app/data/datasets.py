from datetime import date
from pathlib import Path
import sqlite3
import pandas as pd

import project_app
from project_app.data.db import connect_database


#                   CONSTANTS & VALIDATION
VALID_DATA_TYPES = ['CSV', 'Excel', 'JSON', 'Database', 'API']
VALID_ACCESS_LEVELS = ['Public', 'Internal', 'Restricted']


def validate_dataset_fields(name, data_type, size_mb, owner, access_level, description):
    """Validate dataset fields before insert/update."""
    if not all([name, data_type, size_mb, owner, access_level, description]):
        raise ValueError("All fields are required.")

    if data_type not in VALID_DATA_TYPES:
        raise ValueError(f"Data type must be one of: {VALID_DATA_TYPES}")

    if access_level not in VALID_ACCESS_LEVELS:
        raise ValueError(f"Access level must be one of: {VALID_ACCESS_LEVELS}")

    try:
        float(size_mb)
    except ValueError:
        raise ValueError("size_mb must be a numeric value.")


#                         CRUD FUNCTIONS
def insert_dataset(name, data_type, size_mb, owner, access_level, description, created_by=None):
    """Insert a new dataset record."""
    validate_dataset_fields(name, data_type, size_mb, owner, access_level, description)

    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO datasets 
        (name, data_type, size_mb, owner, access_level, description, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, DATE('now'))
    """, (name, data_type, size_mb, owner, access_level, description, created_by))

    conn.commit()
    dataset_id = cursor.lastrowid
    conn.close()

    return dataset_id


def get_all_datasets():
    """Return all dataset records as a DataFrame."""
    conn = connect_database()
    df = pd.read_sql_query(
        "SELECT * FROM datasets ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


def update_dataset(dataset_id, name, data_type, size_mb, owner, access_level, description, created_by=None):
    """Update an existing dataset."""
    validate_dataset_fields(name, data_type, size_mb, owner, access_level, description)

    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE datasets
        SET name = ?, data_type = ?, size_mb = ?, owner = ?, access_level = ?, 
            description = ?, created_by = ?
        WHERE id = ?
    """, (name, data_type, size_mb, owner, access_level, description, created_by, dataset_id))

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    return updated > 0


def update_dataset_access_level(dataset_id, new_access_level):
    """Change access level of a dataset."""
    if new_access_level not in VALID_ACCESS_LEVELS:
        raise ValueError(f"Access level must be one of {VALID_ACCESS_LEVELS}")

    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE datasets
        SET access_level = ?
        WHERE id = ?
    """, (new_access_level, dataset_id))

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    return updated > 0


def delete_dataset(dataset_id):
    """Delete a dataset by ID."""
    conn = connect_database()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
    conn.commit()

    deleted = cursor.rowcount
    conn.close()

    return deleted > 0


#                     OPTIONAL MIGRATION

def migrate_datasets_from_file(filepath="DATA/datasets.txt"):
    """
    Migrate datasets from a structured text file into the DB.
    Format per line:
    name,data_type,size_mb,owner,access_level,description
    """
    filepath = Path(filepath)

    if not filepath.exists():
        print(f"File not found: {filepath}")
        return

    conn = connect_database()
    cursor = conn.cursor()
    migrated = 0

    with filepath.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split(',')
            if len(parts) >= 6:
                name, data_type, size_mb, owner, access_level, description = [p.strip() for p in parts[:6]]

                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO datasets (name, data_type, size_mb, owner, access_level, description) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (name, data_type, size_mb, owner, access_level, description)
                    )
                    if cursor.rowcount > 0:
                        migrated += 1
                except sqlite3.Error as e:
                    print(f"Error migrating dataset '{name}': {e}")

    conn.commit()
    conn.close()
    print(f"Migrated {migrated} datasets from {filepath}")
