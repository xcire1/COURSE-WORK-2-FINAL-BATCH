import bcrypt
import os
from pathlib import Path

# Force users.txt to be in the same folder as this script
# Use the script's directory so the path is portable and not hard-coded
USERS_FILE = Path(__file__).resolve().parent / "users.txt"
# TEMPORARY TEST CODE - Remove after testing 
test_password = "SecurePassword123"


def hash_password(plain_text_password):
    # Encode the password to bytes, required by bcrypt
    password_bytes = plain_text_password.encode('utf-8')
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    # Decode the hash back to a string to store in a text file
    return hashed_password.decode('utf-8')


def verify_password(plain_text_password, hashed_password):
    # Encode both the plaintext password and stored hash to bytes
    password_bytes = plain_text_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    # bcrypt.checkpw handles extracting the salt and comparing
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


def user_exists(username):
    if not USERS_FILE.exists():
        return False

    with open(USERS_FILE, "r") as f:
        for line in f:
            stored_user, _ = line.strip().split(",", 1)
            if stored_user == username:
                return True
    return False


def register_user(username, password):
    hashed_password = hash_password(password)

    # Create file if it doesn’t exist
    # Create file if it doesn't exist
    if not USERS_FILE.exists():
        open(USERS_FILE, "w").close()

    # Prevent duplicate usernames
    if user_exists(username):
        print(f"Error: Username '{username}' already exists.")
        return

    with open(USERS_FILE, "a") as f:
        f.write(f"{username},{hashed_password}\n")

    print(f"User '{username}' registered successfully.")


def login_user(username, password):
    # Create file if it doesn’t exist
    # Create file if it doesn't exist
    if not USERS_FILE.exists():
        open(USERS_FILE, "w").close()

    with open(USERS_FILE, "r") as f:
        for line in f.readlines():
            user, hash_value = line.strip().split(',', 1)
            if user == username:
                return verify_password(password, hash_value)
    return False


def validate_username(username):
    # Validate username input
    if not username:
        return False, "Username cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    return True, ""


def validate_password(password):
    # Validate password input
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    return True, ""


def main():
    print("\nAUTHENTICATION SYSTEM PROGRAMM!")

    while True:
        display_menu()
        choice = input("\nPlease select an option (1-3): ").strip()

        if choice == '1':
            print("\n USER REGISTRATION")
            username = input("Enter a username: ").strip()

            # Validate username
            is_valid, error_msg = validate_username(username)
            if not is_valid:
                print(f"Error: {error_msg}")
                continue

            password = input("Enter a password: ").strip()

            # Validate password
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                print(f"Error: {error_msg}")
                continue

            # Confirm password
            password_confirm = input("Confirm password: ").strip()
            if password != password_confirm:
                print("Error: Passwords do not match.")
                continue

            register_user(username, password)

        elif choice == '2':
            print("\n USER LOGIN ")
            username = input("Enter your username: ").strip()
            password = input("Enter your password: ").strip()

            if login_user(username, password):
                print("\nYou are now logged in.")
                input("\nPress Enter to return to main menu...")
            else:
                print("\nError: Invalid username or password.")

        elif choice == '3':
            print("\nThank you for using the authentication system.")
            print("Exiting...")
            break

        else:
            print("\nError: Invalid option. Please select 1, 2, or 3.")


def display_menu():
    print("\nMULTI-DOMAIN INTELLIGENCE PLATFORM")
    print("\nSecure Authentication System")
    print("\n[1] Register a new user")
    print("[2] Login")
    print("[3] Exit")

if __name__ == "__main__":
    main()
