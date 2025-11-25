import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Cyber Incidents Dashboard", layout="wide")

# Ensure session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Redirect if not logged in
if not st.session_state.logged_in:
    st.error("You must be logged in to view the dashboard.")
    if st.button("Go to login page"):
        st.switch_page("Home.py")
    st.stop()

st.title("Cyber Incidents Dashboard")
st.success(f"Welcome, {st.session_state.username}")

# Load Data
@st.cache_data
def load_cyber_incidents():
    try:
        df = pd.read_csv("DATA/cyber_Incidents.csv")
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['date'] = df['timestamp'].dt.date
        df['month'] = df['timestamp'].dt.to_period('M')
        df['year'] = df['timestamp'].dt.year
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_cyber_incidents()

if df.empty:
    st.warning("No cyber incidents data found.")
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
tab1, tab2, tab3, tab4 = st.tabs(["Charts", "Trends", "Details", "Summary"])

# Charts Tab
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        # Severity Pie Chart
        severity_counts = filtered_df['severity'].value_counts()
        st.plotly_chart(px.pie(values=severity_counts, names=severity_counts.index,
                               title="Incidents by Severity"), use_container_width=True)

        # Status Bar Chart
        status_counts = filtered_df['status'].value_counts()
        st.plotly_chart(px.bar(x=status_counts.index, y=status_counts.values,
                               labels={'x': 'Status', 'y': 'Count'},
                               title="Incidents by Status"), use_container_width=True)

    with c2:
        # Category Horizontal Bar Chart
        cat_counts = filtered_df['category'].value_counts()
        st.plotly_chart(px.bar(x=cat_counts.values, y=cat_counts.index, orientation='h',
                               title="Incidents by Category"), use_container_width=True)

        # Severity by Category Heatmap
        sev_cat = pd.crosstab(filtered_df['category'], filtered_df['severity'])
        st.plotly_chart(px.imshow(sev_cat, title="Severity by Category",
                                  aspect="auto"), use_container_width=True)

# Trends Tab
with tab2:
    c1, c2 = st.columns(2)

    with c1:
        monthly = filtered_df.set_index("timestamp").resample("M").size()
        st.plotly_chart(px.line(x=monthly.index, y=monthly.values,
                                title="Monthly Incident Trends",
                                labels={"x": "Month", "y": "Incidents"}),
                        use_container_width=True)

    with c2:
        filtered_df["day"] = filtered_df["timestamp"].dt.day_name()
        filtered_df["hour"] = filtered_df["timestamp"].dt.hour

        heatmap = filtered_df.pivot_table(
            index="day",
            columns="hour",
            values="incident_id",
            aggfunc="count",
            fill_value=0
        )

        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heatmap = heatmap.reindex(days_order)

        st.plotly_chart(px.imshow(
            heatmap,
            title="Incidents by Day and Hour",
            aspect="auto"
        ), use_container_width=True)

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

    st.download_button(
        label="Download CSV",
        data=results.to_csv(index=False),
        file_name=f"cyber_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

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

# Logout
st.divider()
if st.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.switch_page("Home.py")
