import streamlit as st
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'project_app', 'services'))
from project_app.Authentication_system import *

st.set_page_config(
    page_title="Login / Register",
    page_icon="🔐",
    layout="centered"
)


# -------------------------
# Persistent session setup
# -------------------------
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

st.title("Erick's Intelligence Platform")


# -------------------------
# Dummy authentication
# -------------------------
def dummy_authenticate(username, password):
    return username == "admin" and password == "1234"


# -------------------------
# Logged-in dashboard
# -------------------------
if st.session_state.logged_in:
    st.success(f"Welcome, {st.session_state.username}!")
    st.write(f"Role: {st.session_state.role.upper()}")

    st.write("")
    st.subheader("Dashboards")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Cyber Incidents"):
            st.switch_page("pages/cyber_incidents.py")
    with col2:
        if st.button("Datasets Metadata"):
            st.switch_page("pages/Datasets_metadata.py")
    with col3:
        if st.button("IT Tickets"):
            st.switch_page("pages/it_tickets.py")

    st.write("")
    st.subheader("Profile & Admin")
    if st.button("Profile Page"):
        st.switch_page("pages/profile.py")

    if st.session_state.role == "admin":
        if st.button("Admin Panel"):
            st.switch_page("pages/admin_panel.py")

    st.write("")
    st.subheader("Logout")
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = "user"
        update_persistent_session(False, "", "user")

    st.stop()


# Login / Register Tabs

st.info("Please log in to continue.")
tab_login, tab_register = st.tabs(["Login", "Register"])

# -------------------------
# Login Tab
# -------------------------
with tab_login:
    st.subheader("Login")

    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")
    login_role = st.radio("Login as:", ["User", "Admin"], horizontal=True)

    if st.button("Log In", type="primary"):
        # First check real database
        if login_user(login_username, login_password):
            actual_role = get_user_role(login_username)
        # Fallback to dummy admin
        elif dummy_authenticate(login_username, login_password):
            actual_role = "admin"
        else:
            actual_role = None

        if actual_role is None:
            st.error("Invalid username or password.")
        elif login_role.lower() != actual_role.lower():
            st.error(f"This account is registered as {actual_role.upper()}, not {login_role.upper()}.")
        else:
            st.session_state.logged_in = True
            st.session_state.username = login_username
            st.session_state.role = actual_role
            update_persistent_session(True, login_username, actual_role)
            st.success(f"Successfully logged in as {actual_role.upper()}!")

# -------------------------
# Register Tab
# -------------------------
with tab_register:
    st.subheader("Register")

    reg_user = st.text_input("New Username", key="reg_user")
    reg_pass = st.text_input("New Password", type="password", key="reg_pass")
    reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
    reg_role = st.radio("Register as:", ["User", "Admin"], horizontal=True)

    if st.button("Create Account"):
        if reg_pass != reg_confirm:
            st.error("Passwords do not match.")
        else:
            valid_u, err_u = validate_username(reg_user)
            valid_p, err_p = validate_password(reg_pass)

            if not valid_u:
                st.error(err_u)
            elif not valid_p:
                st.error(err_p)
            elif user_exists(reg_user):
                st.error("Username already exists!")
            else:
                register_user(reg_user, reg_pass, role=reg_role.lower())
                st.success(f"Account created successfully as {reg_role.upper()}!")
                st.info("You can now log in.")
