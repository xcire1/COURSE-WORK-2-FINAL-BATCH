"""
Gemini AI Assistant - Data Analysis Chat Interface
This application provides AI-powered data analysis with Streamlit and Google's Gemini API.
Features include multi-dataset analysis, domain-specific insights, and persistent user sessions.
"""

import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import os

# Initialize Gemini client with API key from Streamlit secrets
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Configure Streamlit page settings
st.set_page_config(page_title="Gemini AI Assistant", layout="wide")


# Persistent session storage using Streamlit's cache_resource
# This maintains session data across reruns but resets when the app restarts
@st.cache_resource
def persistent_session():
    """Create a persistent session storage that survives Streamlit reruns."""
    return {"logged_in": False, "username": "", "role": "user"}


# Get or create the persistent session
session = persistent_session()

# Initialize Streamlit session state from persistent session
# This ensures UI state is preserved during interaction
if "logged_in" not in st.session_state:
    st.session_state.logged_in = session["logged_in"]
if "username" not in st.session_state:
    st.session_state.username = session["username"]
if "role" not in st.session_state:
    st.session_state.role = session["role"]


def update_persistent_session(logged_in: bool, username: str, role: str):
    """Update both persistent session and Streamlit session state."""
    session["logged_in"] = logged_in
    session["username"] = username
    session["role"] = role
    # Sync with Streamlit session state
    st.session_state.logged_in = logged_in
    st.session_state.username = username
    st.session_state.role = role


# Sync current session state with persistent storage
update_persistent_session(
    st.session_state.logged_in,
    st.session_state.username,
    st.session_state.role
)

# --- Authentication Check ---
# Ensure user is logged in before accessing the application
if not st.session_state.logged_in:
    st.error("You must be logged in to use the Gemini AI Assistant.")
    if st.button("Go to Login Page"):
        st.switch_page("Home.py")  # Redirect to login page
    st.stop()  # Stop execution if not logged in

# Display welcome message for authenticated user
st.subheader("Gemini AI Assistant")
st.success(f"Welcome, {st.session_state.username}!")

# --- Data Configuration ---
DATA_FOLDER = "DATA/"  # Folder containing CSV datasets


def load_all_csv_data():
    """
    Load all CSV files from the DATA folder and generate summaries.

    Returns:
        tuple: (combined_summary_string, dictionary_of_dataframes)
    """
    summaries = []
    full_data = {}

    # Check if DATA folder exists
    if not os.path.exists(DATA_FOLDER):
        return "DATA folder does not exist.", {}

    # Iterate through all CSV files in the DATA folder
    for filename in os.listdir(DATA_FOLDER):
        if filename.lower().endswith(".csv"):
            path = os.path.join(DATA_FOLDER, filename)
            try:
                # Load CSV into pandas DataFrame
                df = pd.read_csv(path)
                full_data[filename] = df

                # Create comprehensive summary for this dataset
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
                # Handle file loading errors gracefully
                summaries.append(f"Error loading {filename}: {e}")

    # Return appropriate message if no CSVs found
    if not summaries:
        return "No CSV files found.", {}

    # Combine all dataset summaries
    return "\n\n".join(summaries), full_data


def build_dataset_insight_prompt(user_prompt: str):
    """
    Build an enhanced prompt for dataset analysis requests.

    Args:
        user_prompt: The original user query

    Returns:
        str: Enhanced prompt with dataset context for the AI
    """
    datasets_summary, dataframes = load_all_csv_data()

    prompt = f"""
The user is asking for dataset insights, analysis, or breakdowns.

Below are summaries of all available datasets:

{datasets_summary}

Please provide:
- Trends
- Patterns
- Anomalies
- Clusters
- Recommendations

User Request:
{user_prompt}
"""
    return prompt


# --- Chat History Display ---
# Initialize chat history if it doesn't exist
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display all previous chat messages
for message in st.session_state.messages:
    role = "assistant" if message["role"] == "model" else message["role"]
    with st.chat_message(role):
        st.markdown(message["parts"][0]["text"])

# --- Sidebar Controls ---
with st.sidebar:
    st.title("Chat Controls")

    # Display message count metric
    st.metric("Messages", len(st.session_state.messages))

    # Clear chat button
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.subheader("Logout")
    if st.button("Log Out", use_container_width=True):
        # Reset session state and redirect to login
        update_persistent_session(False, "", "user")
        st.switch_page("Home.py")

# --- AI Interaction Mode Selection ---
st.divider()
st.subheader("AI Interaction Mode")

# Radio button for selecting interaction mode
mode = st.radio(
    "Choose how you want to interact:",
    ["Chat with AI", "AI Insights by Domain"],
    horizontal=True
)

# Domain to dataset filename mapping
DOMAIN_MAP = {
    "cyber_incidents.csv": "Cyber Security Incidents",
    "it_tickets.csv": "IT Support Tickets",
    "datasets_metadata.csv": "Datasets Metadata"
}

# Get available domains based on existing files
available_domains = [
    DOMAIN_MAP[file]
    for file in os.listdir(DATA_FOLDER)
    if file in DOMAIN_MAP
]

# Reverse mapping for display name to filename lookup
REVERSE_DOMAIN_MAP = {
    DOMAIN_MAP[file]: file
    for file in os.listdir(DATA_FOLDER)
    if file in DOMAIN_MAP
}

# --- AI Insights by Domain Mode ---
if mode == "AI Insights by Domain":
    st.info("Select a dataset, problem type, and severity for focused AI analysis.")

    # Check if datasets are available
    if not available_domains:
        st.error("No recognized datasets available in DATA/ folder.")
        st.stop()

    # Step 1: Dataset Selection
    domain_choice = st.selectbox("Choose a dataset domain:", available_domains)

    # Validate selection
    if domain_choice not in REVERSE_DOMAIN_MAP:
        st.error(f"Invalid dataset selection: {domain_choice}")
        st.stop()

    # Load selected dataset
    user_selected_dataset = REVERSE_DOMAIN_MAP[domain_choice]
    df = pd.read_csv(os.path.join(DATA_FOLDER, user_selected_dataset))

    if df.empty:
        st.warning("No data found in the selected dataset.")
        st.stop()

    # Step 2: Problem Type (Category) Selection
    category_options = ['All Categories'] + sorted(df['category'].dropna().unique())
    selected_category = st.selectbox("Choose category (problem type):", category_options)

    # Step 3: Severity Level Selection
    severity_options = ['All Severities'] + sorted(df['severity'].dropna().unique())
    selected_severity = st.selectbox("Choose severity level:", severity_options)

    # Apply filters to dataset
    ai_df = df.copy()
    if selected_category != "All Categories":
        ai_df = ai_df[ai_df['category'] == selected_category]
    if selected_severity != "All Severities":
        ai_df = ai_df[ai_df['severity'] == selected_severity]

    st.caption(f"AI will analyze **{len(ai_df)} incidents** after applying filters.")

    # Generate insights button
    if st.button("Generate AI Insights", use_container_width=True):
        if ai_df.empty:
            st.warning("No incidents match your selected filters.")
        else:
            with st.spinner("AI is analyzing your selected dataset and filters..."):
                # Construct detailed prompt for cybersecurity analysis
                prompt = f"""
You are analyzing a cyber incident dataset.

User Selections:
- Domain: {domain_choice}
- Problem Type (Category): {selected_category}
- Severity Level: {selected_severity}
- Total Filtered Incidents: {len(ai_df)}

Dataset Preview:
{ai_df.head().to_string()}

Column List:
{list(ai_df.columns)}

Provide a detailed cyber analysis including:
1. Executive Summary
2. Key Trends for Selected Category/Severity
3. Incident Frequency Analysis
4. Patterns & Anomalies
5. Category-Based Observations
6. Severity Risk Assessment
7. Root Cause Evaluation
8. Recommended Preventive & Corrective Actions
9. Predictive Insights
"""
                # Call Gemini API for analysis
                response = client.models.generate_content(
                    model="gemini-3-pro-preview",
                    config=types.GenerateContentConfig(
                        system_instruction="You are a professional cybersecurity analyst. Provide structured, high-clarity insights."
                    ),
                    contents=[prompt]
                )

                # Display AI insights
                st.subheader("AI-Generated Insights")
                st.write(response.text)

# --- Normal Chat Mode ---
# Chat input for general conversation
prompt = st.chat_input("Ask anything!")

if prompt:
    # Keywords that trigger dataset analysis mode
    keywords = ["dataset", "analysis", "trend", "csv", "breakdown", "insight"]

    # Enhance prompt with dataset context if keywords are detected
    enhanced_prompt = (
        build_dataset_insight_prompt(prompt)
        if any(word in prompt.lower() for word in keywords)
        else prompt
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({
        "role": "user",
        "parts": [{"text": enhanced_prompt}]
    })

    # Stream response from Gemini API
    response = client.models.generate_content_stream(
        model="gemini-3-pro-preview",
        config=types.GenerateContentConfig(
            system_instruction="Answer as a professional analyst with clear, deep insights."
        ),
        contents=st.session_state.messages,
    )

    # Display streaming response
    with st.chat_message("assistant"):
        container = st.empty()
        full_reply = ""
        for chunk in response:
            full_reply += chunk.text
            container.markdown(full_reply)

    # Add AI response to chat history
    st.session_state.messages.append({
        "role": "model",
        "parts": [{"text": full_reply}]
    })