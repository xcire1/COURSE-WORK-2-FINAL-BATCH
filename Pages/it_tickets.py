import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="IT Support Tickets", layout="wide")
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

st.title("IT Support Tickets Dashboard")
st.success(f"Welcome, {st.session_state.get('username', 'User')}!")

def load_it_tickets():
    try:
        df = pd.read_csv("DATA/it_tickets.csv")
        df['created_at'] = pd.to_datetime(df['created_at'], format='%m/%d/%Y %H:%M')
        df['created_date'] = df['created_at'].dt.date
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


df = load_it_tickets()

if df.empty:
    st.warning("No IT tickets data found.")
    st.stop()

# Sidebar filters
with st.sidebar:
    st.header("Filters")

    selected_priority = st.selectbox("Priority", ['All'] + sorted(df['priority'].unique().tolist()))
    selected_status = st.selectbox("Status", ['All'] + sorted(df['status'].unique().tolist()))
    selected_assignee = st.selectbox("Assigned To", ['All'] + sorted(df['assigned_to'].unique().tolist()))

    min_date, max_date = df['created_at'].min().date(), df['created_at'].max().date()
    date_range = st.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

# Apply filters
filtered_df = df.copy()
if selected_priority != 'All': filtered_df = filtered_df[filtered_df['priority'] == selected_priority]
if selected_status != 'All': filtered_df = filtered_df[filtered_df['status'] == selected_status]
if selected_assignee != 'All': filtered_df = filtered_df[filtered_df['assigned_to'] == selected_assignee]
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['created_at'].dt.date >= start_date) & (filtered_df['created_at'].dt.date <= end_date)]

# Key metrics
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total Tickets", len(filtered_df))
with col2: st.metric("Open Tickets", len(filtered_df[filtered_df['status'] == 'Open']))
with col3: st.metric("Avg Resolution", f"{filtered_df['resolution_time_hours'].mean():.1f}h")
with col4: st.metric("SLA Breaches", len(filtered_df[filtered_df['resolution_time_hours'] > 48]))

# Main tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Team Performance", "Ticket Details"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(filtered_df, names='priority', title="Tickets by Priority"), use_container_width=True)
        st.plotly_chart(px.bar(filtered_df['status'].value_counts(), title="Tickets by Status"),
                        use_container_width=True)
    with col2:
        st.plotly_chart(px.imshow(pd.crosstab(filtered_df['priority'], filtered_df['status']),
                                  title="Priority vs Status"), use_container_width=True)
        st.plotly_chart(px.histogram(filtered_df, x='resolution_time_hours', title="Resolution Time Distribution"),
                        use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.bar(filtered_df['assigned_to'].value_counts(), title="Tickets per Support Staff"),
                        use_container_width=True)
        staff_perf = filtered_df.groupby('assigned_to')['resolution_time_hours'].mean().round(1)
        st.plotly_chart(px.bar(staff_perf, title="Avg Resolution Time by Staff"), use_container_width=True)
    with col2:
        st.plotly_chart(px.bar(pd.crosstab(filtered_df['assigned_to'], filtered_df['priority']),
                               title="Workload by Priority", barmode='stack'), use_container_width=True)
        st.dataframe(filtered_df.groupby('assigned_to').agg({
            'ticket_id': 'count', 'resolution_time_hours': ['mean', 'min', 'max']
        }).round(1), use_container_width=True)

with tab3:
    search_term = st.text_input("Search descriptions")
    display_df = filtered_df[
        filtered_df['description'].str.contains(search_term, case=False, na=False)] if search_term else filtered_df

    sort_col = st.selectbox("Sort by", ['created_at', 'priority', 'status', 'assigned_to'])
    sort_order = st.radio("Order", ['Descending', 'Ascending'], horizontal=True)

    display_df = display_df.sort_values(by=sort_col, ascending=(sort_order == 'Ascending'))
    display_df['created_at'] = display_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')

    st.dataframe(display_df, use_container_width=True, height=400)

    csv = display_df.to_csv(index=False)
    st.download_button("Download CSV", data=csv, file_name=f"it_tickets_{datetime.now().strftime('%Y%m%d')}.csv")

# Navigation
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.page_link("pages/it_tickets.py", label="Cyber Incidents")

with col2:
    st.page_link("pages/Datasets_metadata.py", label="Datasets")

with col3:
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.switch_page("Home.py")