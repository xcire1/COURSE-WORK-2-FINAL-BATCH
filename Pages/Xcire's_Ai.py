"""
Gemini AI Assistant - Data Analysis Chat Interface
AI-powered dataset analysis, domain insights, and persistent sessions.
"""

import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import os

# Initialize Gemini client with API key from Streamlit secrets
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Streamlit page settings
st.set_page_config(page_title="Gemini AI Assistant", layout="wide")


# -------------------------------
# Persistent Session
# -------------------------------
@st.cache_resource
def persistent_session():
    """Persistent session storage that survives reruns."""
    return {"logged_in": False, "username": "", "role": "user"}


session = persistent_session()

# Sync Streamlit state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = session["logged_in"]
if "username" not in st.session_state:
    st.session_state.username = session["username"]
if "role" not in st.session_state:
    st.session_state.role = session["role"]


def update_persistent_session(logged_in: bool, username: str, role: str):
    """Update persistent and Streamlit session."""
    session["logged_in"] = logged_in
    session["username"] = username
    session["role"] = role
    st.session_state.logged_in = logged_in
    st.session_state.username = username
    st.session_state.role = role


# Sync state once
update_persistent_session(
    st.session_state.logged_in,
    st.session_state.username,
    st.session_state.role
)

# -------------------------------
# Authentication Check
# -------------------------------
if not st.session_state.logged_in:
    st.error("You must be logged in to use the Gemini AI Assistant.")
    if st.button("Go to Login Page"):
        st.switch_page("Home.py")
    st.stop()

st.subheader("Gemini AI Assistant")
st.success(f"Welcome, {st.session_state.username}!")


# -------------------------------
# DATA LOADING
# -------------------------------
DATA_FOLDER = "DATA/"


def load_all_csv_data():
    """Load all CSVs from DATA folder with summaries."""
    summaries = []
    full_data = {}

    if not os.path.exists(DATA_FOLDER):
        return "DATA folder does not exist.", {}

    for filename in os.listdir(DATA_FOLDER):
        if filename.lower().endswith(".csv"):
            path = os.path.join(DATA_FOLDER, filename)
            try:
                df = pd.read_csv(path)
                full_data[filename] = df

                summary = f"""
Dataset: {filename}
Rows: {len(df)}
Columns: {', '.join(df.columns)}

Column breakdown:
{df.describe(include='all').transpose().to_string()}

Top 5 rows:
{df.head().to_string(index=False)}
"""
                summaries.append(summary)

            except Exception as e:
                summaries.append(f"Error loading {filename}: {e}")

    if not summaries:
        return "No CSV files found.", {}

    return "\n\n".join(summaries), full_data


def build_dataset_insight_prompt(user_prompt: str):
    """Construct enhanced dataset prompt."""
    datasets_summary, _ = load_all_csv_data()

    return f"""
The user is asking for dataset insights.

Below are all dataset summaries:

{datasets_summary}

Provide:
- Trends
- Patterns
- Anomalies
- Recommendations

User Request:
{user_prompt}
"""


# -------------------------------
# Chat History
# -------------------------------
if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    role = "assistant" if message["role"] == "model" else message["role"]
    with st.chat_message(role):
        st.markdown(message["parts"][0]["text"])


# -------------------------------
# SIDEBAR CONTROLS
# -------------------------------
with st.sidebar:
    st.title("Chat Controls")

    st.metric("Messages", len(st.session_state.messages))

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.subheader("Logout")
    if st.button("Log Out", use_container_width=True):
        update_persistent_session(False, "", "user")
        st.switch_page("Home.py")


# -------------------------------
# MODE SELECTOR
# -------------------------------
st.divider()
st.subheader("AI Interaction Mode")

mode = st.radio(
    "Choose how you want to interact:",
    ["Chat with AI", "AI Insights by Domain"],
    horizontal=True
)

DOMAIN_MAP = {
    "cyber_incidents.csv": "Cyber Security Incidents",
    "it_tickets.csv": "IT Support Tickets",
    "datasets_metadata.csv": "Datasets Metadata"
}

available_domains = [
    DOMAIN_MAP[file]
    for file in os.listdir(DATA_FOLDER)
    if file in DOMAIN_MAP
]

REVERSE_DOMAIN_MAP = {
    DOMAIN_MAP[file]: file
    for file in os.listdir(DATA_FOLDER)
    if file in DOMAIN_MAP
}


# -------------------------------
# DOMAIN INSIGHTS MODE
# -------------------------------
if mode == "AI Insights by Domain":
    st.info("Select a dataset, problem type, and severity for focused AI analysis.")

    if not available_domains:
        st.error("No recognized datasets available.")
        st.stop()

    # Dataset selection
    domain_choice = st.selectbox("Choose a dataset domain:", available_domains)

    if domain_choice not in REVERSE_DOMAIN_MAP:
        st.error(f"Invalid selection: {domain_choice}")
        st.stop()

    df = pd.read_csv(os.path.join(DATA_FOLDER, REVERSE_DOMAIN_MAP[domain_choice]))

    if df.empty:
        st.warning("No data inside dataset.")
        st.stop()

    # -------------------------------
    # SAFE CATEGORY HANDLING (FIX)
    # -------------------------------
    if "category" in df.columns:
        category_options = ["All Categories"] + sorted(df["category"].dropna().unique())
        selected_category = st.selectbox("Choose category:", category_options)
    else:
        st.warning("This dataset has no 'category' column.")
        category_options = ["All Categories"]
        selected_category = "All Categories"

    # -------------------------------
    # SAFE SEVERITY HANDLING (FIX)
    # -------------------------------
    if "severity" in df.columns:
        severity_options = ["All Severities"] + sorted(df["severity"].dropna().unique())
        selected_severity = st.selectbox("Choose severity level:", severity_options)
    else:
        st.warning("This dataset has no 'severity' column.")
        severity_options = ["All Severities"]
        selected_severity = "All Severities"

    # Apply filters
    ai_df = df.copy()

    if "category" in df.columns and selected_category != "All Categories":
        ai_df = ai_df[ai_df["category"] == selected_category]

    if "severity" in df.columns and selected_severity != "All Severities":
        ai_df = ai_df[ai_df["severity"] == selected_severity]

    st.caption(f"AI will analyze **{len(ai_df)} incidents** after filters.")

    # Generate insights
    if st.button("Generate AI Insights", use_container_width=True):
        if ai_df.empty:
            st.warning("No incidents found.")
        else:
            with st.spinner("AI is analyzing…"):
                prompt = f"""
Cyber Incident Dataset Analysis

User Selections:
- Domain: {domain_choice}
- Category: {selected_category}
- Severity: {selected_severity}
- Filtered Rows: {len(ai_df)}

Dataset Preview:
{ai_df.head().to_string()}

Columns:
{list(ai_df.columns)}

Provide:
1. Executive Summary
2. Key Trends
3. Patterns & Anomalies
4. Severity Risk Analysis
5. Root Causes
6. Recommended Actions
7. Predictive Insights
"""

                response = client.models.generate_content(
                    model="gemini-3-pro-preview",
                    config=types.GenerateContentConfig(
                        system_instruction="You are a professional cybersecurity analyst."
                    ),
                    contents=[prompt]
                )

                st.subheader("AI-Generated Insights")
                st.write(response.text)


# -------------------------------
# NORMAL CHAT MODE
# -------------------------------
prompt = st.chat_input("Ask anything!")

if prompt:
    keywords = ["dataset", "analysis", "trend", "csv", "breakdown", "insight"]

    enhanced_prompt = (
        build_dataset_insight_prompt(prompt)
        if any(word in prompt.lower() for word in keywords)
        else prompt
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "parts": [{"text": enhanced_prompt}]
    })

    response = client.models.generate_content_stream(
        model="gemini-3-pro-preview",
        config=types.GenerateContentConfig(
            system_instruction="Answer as a professional analyst."
        ),
        contents=st.session_state.messages,
    )

    with st.chat_message("assistant"):
        container = st.empty()
        full_reply = ""
        for chunk in response:
            full_reply += chunk.text
            container.markdown(full_reply)

    st.session_state.messages.append({
        "role": "model",
        "parts": [{"text": full_reply}]
    })
