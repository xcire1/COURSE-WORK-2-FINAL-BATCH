import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ---- Gemini AI ----
from google import genai
from google.genai import types
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="Datasets Manager", layout="wide")

# Persistent session state
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("username", "")

# Redirect if not logged in
if not st.session_state.logged_in:
    st.error("You must be logged in to view this page.")
    if st.button("Go to login page"):
        st.switch_page("Home.py")
    st.stop()

st.title("Datasets Manager Dashboard")
st.success(f"Hello, {st.session_state.get('username', '')}")

# Folder for uploaded CSVs
UPLOAD_FOLDER = "uploaded_csvs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Upload CSV
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

# Select dataset
available_files = ["DATA/datasets_metadata.csv"] + [
    f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".csv")
]
selected_file = st.selectbox("Select dataset to manage", available_files)

@st.cache_data
def load_metadata(path):
    try:
        df = pd.read_csv(path)
        df["upload_date"] = pd.to_datetime(df["upload_date"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Could not load {path}: {e}")
        return pd.DataFrame()

if selected_file.startswith("DATA/"):
    df = load_metadata(selected_file)
else:
    df = load_metadata(os.path.join(UPLOAD_FOLDER, selected_file))

if df.empty:
    st.warning("No dataset metadata found in the selected file.")
    st.stop()

st.caption(f"Managing {len(df)} datasets — {df['rows'].sum():,} total rows")

# ---- Sidebar Filters ----
with st.sidebar:
    st.header("Filters")
    uploader = st.selectbox("Uploaded By", ["All"] + sorted(df["uploaded_by"].unique().tolist()))
    min_d, max_d = df["upload_date"].min().date(), df["upload_date"].max().date()
    date_range = st.date_input("Upload Date Range", (min_d, max_d), min_value=min_d, max_value=max_d)
    row_range = st.slider("Rows", int(df["rows"].min()), int(df["rows"].max()), (int(df["rows"].min()), int(df["rows"].max())))
    col_range = st.slider("Columns", int(df["columns"].min()), int(df["columns"].max()), (int(df["columns"].min()), int(df["columns"].max())))

    st.divider()
    st.subheader("Stats")
    st.metric("Datasets", len(df))
    st.metric("Total Rows", f"{df['rows'].sum():,}")
    st.metric("Uploaders", df["uploaded_by"].nunique())

# ---- Apply Filters ----
filtered = df.copy()
if uploader != "All":
    filtered = filtered[filtered["uploaded_by"] == uploader]

if len(date_range) == 2:
    start, end = date_range
    filtered = filtered[(filtered["upload_date"].dt.date >= start) & (filtered["upload_date"].dt.date <= end)]

filtered = filtered[
    filtered["rows"].between(row_range[0], row_range[1]) &
    filtered["columns"].between(col_range[0], col_range[1])
].reset_index(drop=True)

# Overview
st.subheader("Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Filtered Datasets", len(filtered))
c2.metric("Total Rows", f"{filtered['rows'].sum():,}")
c3.metric("Total Columns", filtered["columns"].sum())
c4.metric("Avg Rows", f"{filtered['rows'].mean():,.0f}")

# ---- Tabs including AI Insights ----
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Analytics", "User Stats", "Timeline", "Details", "AI Insights"])

# TAB 1 — Analytics
with tab1:
    colA, colB = st.columns(2)
    with colA:
        st.plotly_chart(px.bar(filtered, x="name", y="rows", title="Dataset Size (Rows)").update_layout(xaxis_tickangle=-45), use_container_width=True)
        st.plotly_chart(px.bar(filtered, x="name", y=["rows", "columns"], title="Rows vs Columns").update_layout(xaxis_tickangle=-45), use_container_width=True)

    with colB:
        filtered["complexity"] = filtered["rows"] * filtered["columns"]
        st.plotly_chart(px.bar(filtered, x="name", y="complexity", title="Dataset Complexity").update_layout(xaxis_tickangle=-45), use_container_width=True)
        st.plotly_chart(px.bar(filtered, x="name", y="columns", title="Columns per Dataset").update_layout(xaxis_tickangle=-45), use_container_width=True)

# TAB 2 — User Stats
with tab2:
    colA, colB = st.columns(2)
    with colA:
        counts = filtered["uploaded_by"].value_counts()
        st.plotly_chart(px.bar(x=counts.index, y=counts.values, title="Datasets per Uploader"), use_container_width=True)

        row_counts = filtered.groupby("uploaded_by")["rows"].sum()
        st.plotly_chart(px.bar(x=row_counts.index, y=row_counts.values, title="Rows Contributed by Uploader"), use_container_width=True)

    with colB:
        uploader_stats = filtered.groupby("uploaded_by").agg(
            Datasets=("dataset_id", "count"),
            Total_Rows=("rows", "sum"),
            Avg_Rows=("rows", "mean"),
            Max_Rows=("rows", "max"),
            Avg_Cols=("columns", "mean"),
            Max_Cols=("columns", "max"),
        ).round(0)
        st.subheader("Uploader Statistics")
        st.dataframe(uploader_stats, use_container_width=True)

# TAB 3 — Timeline
with tab3:
    ordered = filtered.sort_values("upload_date").copy()
    ordered["cumulative_rows"] = ordered["rows"].cumsum()
    ordered["cumulative_ds"] = range(1, len(ordered) + 1)

    st.plotly_chart(px.bar(ordered, x="upload_date", y="rows", title="Uploads Over Time"), use_container_width=True)
    st.plotly_chart(px.bar(ordered, x="upload_date", y="cumulative_rows", title="Cumulative Rows Uploaded"), use_container_width=True)
    st.plotly_chart(px.bar(ordered, x="upload_date", y="cumulative_ds", title="Cumulative Dataset Count"), use_container_width=True)

# TAB 4 — Details
with tab4:
    search = st.text_input("Search by dataset name")
    table = filtered[filtered["name"].str.contains(search, case=False, na=False)] if search else filtered

    table = table.copy()
    table["upload_date"] = table["upload_date"].dt.strftime("%Y-%m-%d")
    table["rows"] = table["rows"].apply(lambda x: f"{x:,}")

    st.dataframe(table, use_container_width=True)

    if st.button("Download CSV"):
        st.download_button("Download CSV", table.to_csv(index=False),
                           file_name=f"datasets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                           mime="text/csv")

# TAB 5 — AI Insights
with tab5:
    st.header("AI Dataset Insights")
    st.info("AI analyzes dataset metadata trends, complexity, risks, and recommendations.")

    if st.button("Generate AI Insights", use_container_width=True):

        if filtered.empty:
            st.warning("No dataset available for AI analysis.")
        else:
            with st.spinner("Analyzing dataset metadata..."):

                prompt = f"""
Analyze the following dataset metadata and produce insights.

Dataset Preview:
{filtered.head().to_string()}

Columns:
{list(filtered.columns)}

Total datasets analyzed: {len(filtered)}

Provide:
- Executive Summary
- Dataset Quality & Health
- Uploader Contribution Analysis
- Growth & Timeline Patterns
- Complexity (rows x columns) Insights
- Risk Assessment (storage, redundancy, quality issues)
- Optimization Recommendations
- Predictive Insights (future upload activity or scaling concerns)
"""

                response = client.models.generate_content(
                    model="gemini-3-pro-preview",
                    config=types.GenerateContentConfig(
                        system_instruction="You are a data governance and analytics expert. Provide precise, strategic insights."
                    ),
                    contents=[prompt]
                )

                st.subheader("AI-Generated Insights")
                st.write(response.text)

# Navigation
st.divider()
c1, c2, c3 = st.columns([2, 1, 1])
c1.page_link("Home.py", label="Back")
c2.page_link("Home.py", label="Home")

if c3.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.switch_page("Home.py")
