import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Datasets Manager", page_icon="", layout="wide")

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


st.title("Datasets Manager")
st.success(f"Hello, {st.session_state.get('username','')}")

# ----------------------- LOAD METADATA -----------------------
@st.cache_data
def load_metadata():
    try:
        df = pd.read_csv("DATA/datasets_metadata.csv")
        df['upload_date'] = pd.to_datetime(df['upload_date'])
        return df
    except Exception as e:
        st.error(f"Could not load metadata: {e}")
        return pd.DataFrame()

df = load_metadata()
if df.empty:
    st.warning("No dataset metadata found.")
    st.stop()

st.caption(f"Managing {len(df)} datasets — {df['rows'].sum():,} total rows")

# ----------------------- SIDEBAR FILTERS -----------------------
with st.sidebar:
    st.header("Filters")

    uploader = st.selectbox("Uploaded By", ['All'] + sorted(df['uploaded_by'].unique().tolist()))
    min_d, max_d = df['upload_date'].min().date(), df['upload_date'].max().date()
    date_range = st.date_input("Upload Date Range", (min_d, max_d), min_value=min_d, max_value=max_d)

    row_range = st.slider("Rows", int(df.rows.min()), int(df.rows.max()),
                          (int(df.rows.min()), int(df.rows.max())))
    col_range = st.slider(
        "Columns",
        int(df['columns'].min()),
        int(df['columns'].max()),
        (int(df['columns'].min()), int(df['columns'].max()))
    )

    st.divider()
    st.subheader("Stats")
    st.metric("Datasets", len(df))
    st.metric("Total Rows", f"{df.rows.sum():,}")
    st.metric("Uploaders", df.uploaded_by.nunique())

# ----------------------- FILTERING -----------------------
filtered = df.copy()

if uploader != "All":
    filtered = filtered[filtered.uploaded_by == uploader]

if len(date_range) == 2:
    start, end = date_range
    filtered = filtered[
        (filtered.upload_date.dt.date >= start) &
        (filtered.upload_date.dt.date <= end)
    ]

filtered = filtered[
    filtered['rows'].between(*row_range) &
    filtered['columns'].between(*col_range)
]


# ----------------------- KEY METRICS -----------------------
st.subheader("Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Filtered Datasets", len(filtered))
c2.metric("Total Rows", f"{filtered.rows.sum():,}")
c3.metric("Total Columns", filtered.columns.sum())
c4.metric("Avg Rows", f"{filtered.rows.mean():,.0f}")

# ----------------------- TABS -----------------------
tab1, tab2, tab3, tab4 = st.tabs(["Analytics", "User Stats", "Timeline", "Details"])

# ----------------------- TAB 1: Analytics -----------------------
with tab1:
    colA, colB = st.columns(2)

    with colA:
        st.plotly_chart(
            px.bar(filtered, x="name", y="rows", title="Dataset Size").update_layout(xaxis_tickangle=-45),
            use_container_width=True
        )
        st.plotly_chart(
            px.scatter(filtered, x="rows", y="columns", size="rows",
                       color="uploaded_by", title="Rows vs Columns"),
            use_container_width=True
        )

    with colB:
        filtered["complexity"] = filtered.rows * filtered.columns
        st.plotly_chart(px.pie(filtered, values="complexity", names="name",
                               title="Complexity Distribution"), use_container_width=True)
        st.plotly_chart(px.box(filtered, y="columns", points="all",
                               title="Column Distribution"), use_container_width=True)

# ----------------------- TAB 2: Uploaders -----------------------
with tab2:
    colA, colB = st.columns(2)

    with colA:
        st.plotly_chart(
            px.bar(filtered.uploaded_by.value_counts(),
                   title="Datasets per Uploader"),
            use_container_width=True
        )
        st.plotly_chart(
            px.pie(filtered.groupby("uploaded_by")['rows'].sum(),
                   title="Rows by Uploader"),
            use_container_width=True
        )

    with colB:
        uploader_stats = filtered.groupby('uploaded_by').agg(
            Datasets=('dataset_id', 'count'),
            Total_Rows=('rows', 'sum'),
            Avg_Rows=('rows', 'mean'),
            Max_Rows=('rows', 'max'),
            Avg_Cols=('columns', 'mean'),
            Max_Cols=('columns', 'max'),
        ).round(0)
        st.subheader("Uploader Statistics")
        st.dataframe(uploader_stats, use_container_width=True)

# ----------------------- TAB 3: TIMELINE -----------------------
with tab3:
    ordered = filtered.sort_values('upload_date')
    ordered['cumulative_rows'] = ordered.rows.cumsum()
    ordered['cumulative_ds'] = range(1, len(ordered) + 1)

    st.plotly_chart(
        px.line(ordered, x="upload_date", y="rows", markers=True,
                title="Upload Timeline"),
        use_container_width=True
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ordered.upload_date, y=ordered.cumulative_rows, name="Cumulative Rows"))
    fig.add_trace(go.Scatter(x=ordered.upload_date, y=ordered.cumulative_ds, name="Cumulative Datasets", yaxis="y2"))
    fig.update_layout(
        title="Cumulative Growth",
        yaxis=dict(title="Rows"),
        yaxis2=dict(title="Datasets", overlaying="y", side="right")
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------- TAB 4: DETAILED TABLE -----------------------
with tab4:
    search = st.text_input("Search by dataset name")
    table = filtered[filtered.name.str.contains(search, case=False, na=False)] if search else filtered

    table = table.copy()
    table['upload_date'] = table.upload_date.dt.strftime("%Y-%m-%d")
    table['rows'] = table.rows.apply(lambda x: f"{x:,}")

    st.dataframe(table, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    if c1.button("Export CSV"):
        st.download_button("Download CSV", table.to_csv(index=False),
                           f"datasets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")
    if c2.button("Refresh"):
        st.cache_data.clear()
        st.rerun()
    if c3.button("Generate Report"):
        st.write({
            "Datasets": len(filtered),
            "Rows": f"{filtered.rows.sum():,}",
            "Columns": filtered.columns.sum(),
            "Avg Rows": f"{filtered.rows.mean():,.0f}",
            "Date Range": f"{filtered.upload_date.min():%Y-%m-%d} to {filtered.upload_date.max():%Y-%m-%d}",
            "Uploaders": ", ".join(filtered.uploaded_by.unique())
        })

# ----------------------- NAVIGATION -----------------------
st.divider()
c1, c2, c3 = st.columns([2, 1, 1])

c1.page_link("1_Dashboard.py", label="Back")
c2.page_link("Home.py", label="Home")
if c3.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.switch_page("Home.py")
