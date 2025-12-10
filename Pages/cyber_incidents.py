import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from google import genai
from google.genai import types
import os

st.set_page_config(page_title="Cyber Incidents Dashboard", layout="wide")

# Persistent session state
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("username", "")

# Redirect if not logged in
if not st.session_state.logged_in:
    st.error("You must be logged in to view this page.")
    if st.button("Go to login page"):
        st.switch_page("Home.py")
    st.stop()

st.title("Cyber Incidents Dashboard")
st.success(f"Welcome, {st.session_state.username}")

# Gemini Client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Folder to store uploaded CSVs
UPLOAD_FOLDER = "uploaded_csvs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# CSV Upload Section
st.subheader("Upload a new CSV")
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
if uploaded_file:
    try:
        df_uploaded = pd.read_csv(uploaded_file)
        save_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
        df_uploaded.to_csv(save_path, index=False)
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
    except Exception as e:
        st.error(f"Error uploading CSV: {e}")

# Allow user to select dataset (default or uploaded)
available_files = ["DATA/cyber_Incidents.csv"] + [
    f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".csv")
]

selected_file = st.selectbox("Select dataset to analyze", available_files)

# Load the selected dataset
@st.cache_data
def load_dataset(path):
    try:
        df = pd.read_csv(path)
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['date'] = df['timestamp'].dt.date
        df['month'] = df['timestamp'].dt.to_period('M')
        df['year'] = df['timestamp'].dt.year
        return df
    except Exception as e:
        st.error(f"Error loading {path}: {e}")
        return pd.DataFrame()

if selected_file.startswith("DATA/"):
    df = load_dataset(selected_file)
else:
    df = load_dataset(os.path.join(UPLOAD_FOLDER, selected_file))

if df.empty:
    st.warning("No data found in the selected dataset.")
    st.stop()

st.caption(f"Loaded {len(df)} incidents from {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")

# Sidebar Filters
with st.sidebar:
    st.header("Filters")
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()
    date_range = st.date_input("Date Range", (min_date, max_date), min_value=min_date, max_value=max_date)
    selected_severity = st.selectbox("Severity", ['All'] + sorted(df['severity'].unique()))
    selected_category = st.selectbox("Category", ['All'] + sorted(df['category'].unique()))
    selected_status = st.selectbox("Status", ['All'] + sorted(df['status'].unique()))

    st.divider()
    st.subheader("Quick Stats")
    st.metric("Total Incidents", len(df))
    st.metric("Categories", df['category'].nunique())

# Apply Filters
filtered_df = df.copy()
if len(date_range) == 2:
    start, end = date_range
    filtered_df = filtered_df[(filtered_df['date'] >= start) & (filtered_df['date'] <= end)]
if selected_severity != "All":
    filtered_df = filtered_df[filtered_df['severity'] == selected_severity]
if selected_category != "All":
    filtered_df = filtered_df[filtered_df['category'] == selected_category]
if selected_status != "All":
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

# Overview Metrics
st.subheader("Overview Metrics")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Incidents", len(filtered_df))
c2.metric("Critical Incidents", len(filtered_df[filtered_df['severity'] == "Critical"]))
c3.metric("Open Incidents", len(filtered_df[filtered_df['status'] == "Open"]))
c4.metric("Categories", filtered_df['category'].nunique())

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Charts", "Trends", "Details", "Summary", "AI Insights"])

# Charts Tab
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        severity_counts = filtered_df['severity'].value_counts()
        st.plotly_chart(
            px.bar(x=severity_counts.index, y=severity_counts.values, labels={'x': 'Severity', 'y': 'Count'}, title="Incidents by Severity"),
            use_container_width=True
        )
        status_counts = filtered_df['status'].value_counts()
        st.plotly_chart(
            px.bar(x=status_counts.index, y=status_counts.values, labels={'x': 'Status', 'y': 'Count'}, title="Incidents by Status"),
            use_container_width=True
        )
    with c2:
        cat_counts = filtered_df['category'].value_counts()
        st.plotly_chart(
            px.bar(x=cat_counts.values, y=cat_counts.index, orientation='h', title="Incidents by Category"),
            use_container_width=True
        )
        sev_cat = pd.crosstab(filtered_df['category'], filtered_df['severity']).reset_index().melt(id_vars='category', var_name='severity', value_name='count')
        st.plotly_chart(
            px.bar(sev_cat, x='category', y='count', color='severity', title="Severity by Category (Grouped Bar Chart)"),
            use_container_width=True
        )

# Trends Tab
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        monthly = filtered_df.set_index("timestamp").resample("M").size()
        st.plotly_chart(px.line(x=monthly.index, y=monthly.values, labels={"x": "Month", "y": "Incidents"}, title="Monthly Incident Trends"), use_container_width=True)
    with c2:
        filtered_df["day"] = filtered_df["timestamp"].dt.day_name()
        filtered_df["hour"] = filtered_df["timestamp"].dt.hour
        hourly = filtered_df['hour'].value_counts().sort_index()
        st.plotly_chart(px.bar(x=hourly.index, y=hourly.values, labels={'x': 'Hour', 'y': 'Incidents'}, title="Incidents by Hour of Day"), use_container_width=True)

# Details Tab
with tab3:
    st.subheader("Incident Details")
    search = st.text_input("Search descriptions")
    results = filtered_df[filtered_df['description'].str.contains(search, case=False, na=False)] if search else filtered_df
    sort_by = st.selectbox("Sort by", ['timestamp', 'severity', 'category', 'status'])
    order = st.radio("Order", ['Descending', 'Ascending'], horizontal=True)
    results = results.sort_values(sort_by, ascending=(order == "Ascending"))
    display_df = results.copy()
    display_df["timestamp"] = display_df["timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')
    st.dataframe(display_df, use_container_width=True, height=400)
    st.download_button("Download CSV", results.to_csv(index=False), file_name=f"cyber_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")

# Summary Tab
with tab4:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Severity Summary")
        for s, count in filtered_df['severity'].value_counts().items():
            st.write(f"{s}: {count}")
        st.subheader("Status Summary")
        for s, count in filtered_df['status'].value_counts().items():
            st.write(f"{s}: {count}")
    with c2:
        st.subheader("Category Summary")
        for c, count in filtered_df['category'].value_counts().items():
            st.write(f"{c}: {count}")
        st.subheader("Recent Activity")
        recent = filtered_df.nlargest(5, 'timestamp')
        for _, r in recent.iterrows():
            st.write(f"{r['timestamp'].strftime('%m/%d %H:%M')} - {r['severity']} {r['category']} ({r['status']})")

# AI Insights Tab
with tab5:
    st.header("AI Incident Insights")
    st.info("The AI will analyze your filtered incidents, detect patterns, risks, and suggest improvements.")
    if st.button("Generate AI Insights", use_container_width=True):
        if filtered_df.empty:
            st.warning("No data available for AI analysis.")
        else:
            with st.spinner("Analyzing incident data with AI..."):
                prompt = f"""
Analyze the following cyber incident dataset. Provide insights, breakdowns, threat assessment,
patterns, trends, root cause analysis, and recommended actions.

Dataset Preview:
{filtered_df.head().to_string()}

Column Info:
{list(filtered_df.columns)}

Dataset Size: {len(filtered_df)}

Required Output:
Executive Summary
Key Trends
Severity Breakdown
Risk Assessment
Category-based Observations
High-risk Patterns
Recommended Fixes and Mitigations
Predictive Insights
"""
                response = client.models.generate_content(
                    model="gemini-3-pro-preview",
                    config=types.GenerateContentConfig(system_instruction="You are a cybersecurity analyst AI. Return sharp, accurate insights."),
                    contents=[prompt]
                )
                st.subheader("AI-Generated Insights")
                st.write(response.text)

# Logout button
st.divider()
if st.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.switch_page("Home.py")
