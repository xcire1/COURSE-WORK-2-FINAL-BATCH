import streamlit as st
from datetime import datetime, timedelta

COOKIE_NAME = "login_token"

def set_login_cookie(username: str):
    """Save login cookie + session state"""
    expires = datetime.now() + timedelta(days=7)
    st.session_state.logged_in = True
    st.session_state.username = username
    st.set_cookie(COOKIE_NAME, username, expires=expires)


def clear_login_cookie():
    """Logout: delete cookie + reset session state"""
    st.delete_cookie(COOKIE_NAME)
    st.session_state.logged_in = False
    st.session_state.username = ""


def restore_login_from_cookie():
    """Load login state from browser cookie"""
    if COOKIE_NAME in st.cookies:
        username = st.cookies.get(COOKIE_NAME)
        if username:
            st.session_state.logged_in = True
            st.session_state.username = username
