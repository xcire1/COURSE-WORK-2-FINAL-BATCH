import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import os

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="Gemini AI Assistant", layout="wide")

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

if not st.session_state.logged_in:
    st.error("You must be logged in to use the Gemini AI Assistant.")
    if st.button("Go to Login Page"):
        st.switch_page("Home.py")
    st.stop()

st.subheader("Gemini AI Assistant")
st.success(f"Welcome, {st.session_state.username}!")

DATA_FOLDER = "DATA/"

def load_all_csv_data():
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
    datasets_summary, dataframes = load_all_csv_data()

    prompt = f"""
The user wants data analysis, insights, or domain breakdown.

Below are all datasets available:

{datasets_summary}

Tasks:
- Analyze all datasets
- Identify clusters, trends, anomalies, and patterns
- Provide insights and recommended actions
- Produce a structured and professional summary

User request:
{user_prompt}
"""
    return prompt

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    role = "assistant" if message["role"] == "model" else message["role"]
    with st.chat_message(role):
        st.markdown(message["parts"][0]["text"])

with st.sidebar:
    st.title("Chat Controls")
    st.metric("Messages", len(st.session_state.messages))

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.write("")
    st.subheader("Logout")

    if st.button("Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = "user"
        update_persistent_session(False, "", "user")
        st.switch_page("Home.py")

prompt = st.chat_input("Ask anything! Example: 'Analyze all CSV data'")

if prompt:
    keywords = ["insight", "analysis", "dataset", "csv", "breakdown", "trend"]

    if any(word in prompt.lower() for word in keywords):
        enhanced_prompt = build_dataset_insight_prompt(prompt)
    else:
        enhanced_prompt = prompt

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "parts": [{"text": enhanced_prompt}]
    })

    response = client.models.generate_content_stream(
        model="gemini-3-pro-preview",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a professional data analyst and cybersecurity advisor. "
                "Provide clear insights, breakdowns, and recommendations."
            )
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

    st.rerun()
