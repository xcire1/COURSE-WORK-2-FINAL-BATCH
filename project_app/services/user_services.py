import bcrypt
import sqlite3
from pathlib import Path

from project_app.data.db import connect_database
from project_app.data.users import get_user_by_username, insert_user
from project_app.data.schema import create_users_table

# REGISTER USER
def register_user(username, password, role="user"):
    conn = connect_database()
    cur = conn.cursor()

    try:
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            return False, "Username already exists"

        # Hash password
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Insert user
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash.decode("utf-8"), role),
        )

        conn.commit()
        return True, "User registered successfully"

    except Exception as e:
        return False, f"Error: {e}"

    finally:
        conn.close()

# LOGIN USER
def login_user(username, password):
    conn = connect_database()
    cur = conn.cursor()

    try:
        cur.execute("SELECT password_hash, role FROM users WHERE username = ?", (username,))
        row = cur.fetchone()

        if not row:
            return "user not found", None

        stored_hash, role = row

        # Check password
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            return "login successful", role
        else:
            return "incorrect password", None

    except Exception as e:
        return f"Error: {e}", None

    finally:
        conn.close()


# MIGRATE users.txt → DATABASE

def migrate_users_from_file(filepath=None):
    """
    Migrates users from users.txt into the SQLite database.

    Expected users.txt format:
        username,password_hash
    """

    # Auto-detect users.txt if no file provided
    if filepath is None:
        filepath = Path(__file__).resolve().parents[2] / "users.txt"

    filepath = Path(filepath)

    # Ensure database and table exist
    conn = connect_database()
    create_users_table(conn)

    cursor = conn.cursor()
    migrated_count = 0

    if not filepath.exists():
        print(f" users.txt not found at: {filepath}")
        return 0

    with filepath.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Expect: username,password_hash
            parts = line.split(",", 1)
            if len(parts) < 2:
                continue

            username = parts[0].strip()
            password_hash = parts[1].strip()

            try:
                # INSERT OR IGNORE prevents duplicates
                cursor.execute(
                    "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash, "user"),
                )

                if cursor.rowcount > 0:
                    migrated_count += 1

            except sqlite3.Error as e:
                print(f"Error migrating user {username}: {e}")

    conn.commit()
    print(f"\n Migrated {migrated_count} user(s) from {filepath.name}")

    # Verification output
    verify_conn = connect_database()
    verify_cursor = verify_conn.cursor()
    verify_cursor.execute("SELECT id, username, role FROM users")
    users = verify_cursor.fetchall()

    print("\n Users in database:")
    print(f"{'ID':<5} {'Username':<15} {'Role':<10}")
    print("-" * 35)
    for user in users:
        print(f"{user[0]:<5} {user[1]:<15} {user[2]:<10}")

    print(f"\nTotal users: {len(users)}")

    verify_conn.close()
    conn.close()

    return migrated_count
