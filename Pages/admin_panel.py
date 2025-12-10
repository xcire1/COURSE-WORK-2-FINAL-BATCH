import streamlit as st
import sys
import os
import shutil
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), 'project_app', 'services'))
from project_app.Authentication_system import *

st.set_page_config(
    page_title="Admin Panel",
    page_icon="🛠️",
    layout="wide"
)

# Persistent session
@st.cache_resource
def persistent_session():
    return {"logged_in": False, "username": "", "role": "user"}

session = persistent_session()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = session["logged_in"]

if "username" not in st.session_state:
    st.session_state.username = session["username"]

if "role" not in st.session_state:
    st.session_state.role = session["role"]

def update_persistent_session(logged_in, username, role):
    session["logged_in"] = logged_in
    session["username"] = username
    session["role"] = role

st.session_state.logged_in = session["logged_in"]
st.session_state.username = session["username"]
st.session_state.role = session["role"]

# Access control
if not st.session_state.logged_in or st.session_state.role != "admin":
    st.error("❌ Access denied. Admins only!")
    st.stop()

st.title("Admin Panel - CSV & User Management")

# Paths
CSV_FOLDER = Path("DATA")
TRASH_FOLDER = Path("DATA/trash")
TRASH_FOLDER.mkdir(exist_ok=True)

# CSV MANAGEMENT
def list_csv_files(folder):
    return [f.name for f in folder.glob("*.csv")]

# Delete CSV
st.subheader("Delete a CSV file")
csv_files = list_csv_files(CSV_FOLDER)
if csv_files:
    csv_to_delete = st.selectbox("Select a CSV to delete", csv_files)
    if st.button("Delete CSV"):
        shutil.move(str(CSV_FOLDER / csv_to_delete), str(TRASH_FOLDER / csv_to_delete))
        st.success(f"CSV '{csv_to_delete}' has been deleted (moved to trash).")
else:
    st.info("No CSV files available for deletion.")

# Restore CSV
st.subheader("Restore a CSV file")
deleted_csvs = list_csv_files(TRASH_FOLDER)
if deleted_csvs:
    csv_to_restore = st.selectbox("Select a CSV to restore", deleted_csvs)
    if st.button("Restore CSV"):
        shutil.move(str(TRASH_FOLDER / csv_to_restore), str(CSV_FOLDER / csv_to_restore))
        st.success(f"CSV '{csv_to_restore}' has been restored.")
else:
    st.info("No CSV files in trash to restore.")

# USER MANAGEMENT
st.subheader("Manage Registered Users")

try:
    users = get_all_users()  # Should return a list of dicts: [{"username":..., "role":...}, ...]
except Exception as e:
    st.error("Could not fetch users. Make sure 'get_all_users()' exists in Authentication_system.py")
    users = []

if users:
    usernames = [user['username'] for user in users]
    selected_user = st.selectbox("Select a user to manage", usernames)

    if selected_user:
        user_role = next(u['role'] for u in users if u['username'] == selected_user)
        st.write(f"Username: {selected_user} | Current Role: {user_role.upper()}")

        # Change role
        new_role = st.selectbox("Change role to:", ["User", "Admin"], index=0 if user_role=="user" else 1)
        if st.button("Update Role"):
            update_user_role(selected_user, new_role.lower())
            st.success(f"{selected_user}'s role has been updated to {new_role.upper()}.")

        # Delete user
        if st.button("Delete User"):
            if selected_user == st.session_state.username:
                st.error("You cannot delete yourself!")
            else:
                delete_user(selected_user)
                st.success(f"User '{selected_user}' has been deleted.")
else:
    st.info("No registered users found.")
