import bcrypt
from pathlib import Path
from typing import Dict, Tuple, List, Optional

# USERS_FILE will be located in project_app/services/users.txt
USERS_FILE = Path(__file__).resolve().parent / "services" / "users.txt"
USERS_FILE.parent.mkdir(parents=True, exist_ok=True)  # ensure services/ directory exists


# -----------------------
# Low-level helpers
# -----------------------
def _ensure_users_file():
    """Make sure users.txt exists."""
    if not USERS_FILE.exists():
        USERS_FILE.write_text("", encoding="utf-8")


def _parse_user_line(line: str) -> Tuple[str, str, str]:
    """
    Parse a line from users.txt into (username, hashed_password, role).
    Backwards-compatible: if role missing, defaults to 'user'.
    """
    parts = line.strip().split(",")

    if len(parts) == 0 or parts[0].strip() == "":
        raise ValueError("Invalid or empty user line")

    username = parts[0].strip()

    if len(parts) < 2 or parts[1].strip() == "":
        raise ValueError("Malformed user line (missing password)")

    hashed = parts[1].strip()

    role = parts[2].strip() if len(parts) >= 3 and parts[2].strip() != "" else "user"

    return username, hashed, role


def _format_user_line(username: str, hashed: str, role: str) -> str:
    return f"{username},{hashed},{role}\n"


# -----------------------
# Password utilities
# -----------------------
def hash_password(plain_text_password: str) -> str:
    password_bytes = plain_text_password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_text_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_text_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# -----------------------
# User storage operations
# -----------------------
def load_users() -> Dict[str, Tuple[str, str]]:
    """
    Load users into dict: {username: (hashed_password, role)}
    """
    _ensure_users_file()
    users: Dict[str, Tuple[str, str]] = {}

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                username, hashed, role = _parse_user_line(line)
                users[username] = (hashed, role)
            except ValueError:
                continue  # skip invalid lines

    return users


def save_all_users(users: Dict[str, Tuple[str, str]]) -> None:
    """
    Overwrite users.txt with the provided users dict.
    """
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        for username, (hashed, role) in users.items():
            f.write(_format_user_line(username, hashed, role))


def get_all_users() -> List[Dict[str, str]]:
    """Return list of users WITHOUT passwords."""
    users = load_users()
    return [{"username": u, "role": r} for u, (_, r) in users.items()]


# -----------------------
# Public API
# -----------------------
def user_exists(username: str) -> bool:
    return username in load_users()


def register_user(username: str, password: str, role: str = "user") -> None:
    if not username:
        raise ValueError("Username cannot be empty.")
    if user_exists(username):
        raise ValueError(f"Username '{username}' already exists.")

    hashed = hash_password(password)
    users = load_users()
    users[username] = (hashed, role)
    save_all_users(users)


def login_user(username: str, password: str) -> bool:
    users = load_users()
    if username not in users:
        return False
    hashed, _role = users[username]
    return verify_password(password, hashed)


def get_user_role(username: str) -> Optional[str]:
    users = load_users()
    if username not in users:
        return None
    return users[username][1]


def delete_user(username: str) -> bool:
    users = load_users()
    if username not in users:
        return False
    users.pop(username)
    save_all_users(users)
    return True


def update_password(username: str, new_password: str) -> bool:
    users = load_users()
    if username not in users:
        return False

    _, role = users[username]
    users[username] = (hash_password(new_password), role)
    save_all_users(users)
    return True


def set_role(username: str, role: str) -> bool:
    users = load_users()
    if username not in users:
        return False

    hashed, _old_role = users[username]
    users[username] = (hashed, role)
    save_all_users(users)
    return True


# -----------------------
# Validation
# -----------------------
def validate_username(username: str) -> Tuple[bool, str]:
    if not username:
        return False, "Username cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if "," in username:
        return False, "Username cannot contain commas."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    return True, ""


# -----------------------
# Optional CLI Inspect Mode
# -----------------------
if __name__ == "__main__":
    print("Authentication helper module.")
    print("Users file location:", USERS_FILE)
    print("Existing users:")
    for u in get_all_users():
        print(f"- {u['username']} ({u['role']})")
