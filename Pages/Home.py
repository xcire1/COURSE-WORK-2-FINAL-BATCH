import streamlit as st
import sys
import os
import time

# Import fix
sys.path.append(os.path.join(os.path.dirname(__file__), 'project_app', 'services'))
from project_app.Authentication_system import *

st.set_page_config(
    page_title="Login / Register",
    page_icon="🔐",
    layout="centered"
)

# ------------------------------
# REMEMBER-ME COOKIE MANAGER
# ------------------------------
def set_cookie(key, value, days=30):
    st.session_state[f"cookie_{key}"] = value
    st.session_state[f"cookie_exp_{key}"] = time.time() + days * 24 * 3600

def get_cookie(key):
    val = st.session_state.get(f"cookie_{key}")
    exp = st.session_state.get(f"cookie_exp_{key}")
    if val and exp and exp > time.time():
        return val
    return None

def delete_cookie(key):
    st.session_state[f"cookie_{key}"] = None
    st.session_state[f"cookie_exp_{key}"] = 0


# INIT SESSION STATE

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = "user"


# ------------------------------
# AUTO LOGIN USING COOKIE
# ------------------------------
cookie_user = get_cookie("username")

if cookie_user and not st.session_state.logged_in:
    st.session_state.logged_in = True
    st.session_state.username = cookie_user
    st.session_state.role = get_user_role(cookie_user)


# ------------------------------
# MAIN PAGE START
# ------------------------------
st.title("🔐 Multi-Domain Intelligence Platform")

# ---------------------------------------------------------
# If logged in → show dashboard + logout on MAIN PAGE
# ---------------------------------------------------------
if st.session_state.logged_in:

    st.success(f"Welcome, **{st.session_state.username}**!")
    st.write(f"**Role:** {st.session_state.role.upper()}")

    st.write("---")
    st.subheader("📊 Dashboards")

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

    st.write("---")
    st.subheader("👤 Profile & Admin")

    if st.button("Profile Page"):
        st.switch_page("pages/profile.py")

    if st.session_state.role == "admin":
        if st.button("Admin Panel"):
            st.switch_page("pages/admin_panel.py")

    st.write("---")
    st.subheader("Logout")

    # LOGOUT BUTTON MOVED HERE
    if st.button("Log Out"):
        st.session_state.logged_in = False
        delete_cookie("username")
        st.session_state.username = ""
        st.session_state.role = "user"
        st.rerun()

    st.stop()


# ---------------------------------------------------------
# NOT LOGGED IN → Show LOGIN + REGISTER TABS on MAIN PAGE
# ---------------------------------------------------------
st.info("Please log in to continue.")

tab_login, tab_register = st.tabs(["Login", "Register"])

# ---------------- LOGIN TAB ----------------
with tab_login:
    st.subheader("Login")

    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")
    remember = st.checkbox("Remember me")

    if st.button("Log In", type="primary"):
        if login_user(login_username, login_password):
            st.session_state.logged_in = True
            st.session_state.username = login_username
            st.session_state.role = get_user_role(login_username)

            if remember:
                set_cookie("username", login_username)

            st.success("Successfully logged in!")
            st.rerun()
        else:
            st.error("Invalid username or password.")


# ---------------- REGISTER TAB ----------------
with tab_register:
    st.subheader("Register")

    reg_user = st.text_input("New Username")
    reg_pass = st.text_input("New Password", type="password")
    reg_confirm = st.text_input("Confirm Password", type="password")

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
                register_user(reg_user, reg_pass, role="user")
                st.success("Account created successfully!")
                st.info("You can now log in.")
