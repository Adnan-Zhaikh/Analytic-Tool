import streamlit as st
import pandas as pd

from charts import (
    line_chart, bar_chart, histogram, scatter_plot, heatmap
)

from analytics import (
    load_file, normalize_columns, infer_types, clean_data,
    summary_stats, column_profile, trend_by, 
    category_breakdown, correlation_matrix, generate_insights, 
)

st.set_page_config(page_title="Data Dashboard",page_icon=":bar_chart:", layout="wide")

@st.cache_data(show_spinner=False)
def process_pipeline(file_bytes, file_name):
    """
    Everything from raw bytes to clean df + reports.
    Cached on file content, so re-renders are instant.
    """
    class _F:
        def __init__(self, b, n):
            self._b, self.name = b, n
        def read(self):
            return self._b

    df, load_report = load_file(_F(file_bytes, filename))
    df, renamed = normalize_columns(df)
    df, type_report = infer_types(df)
    df, clean_report = clean_data(df)
    return df, {"load": load_report, "renamed": renamed,
                "types": type_report, "clean": clean_report}

st.title("📊 Upload & Analyse")
st.caption("Drop a CSV or Excel file — get instant stats, charts and insights.")

uploaded = st.file_uploader(
    "Choose a file", type=["csv", "xlsx", "xls"], label_visibility="collapsed"
)

if uploaded is None:
    st.info("Waiting for a file. Try a CSV with a date column, a numeric column, and a category column.")
    st.stop()

df, reports = process_pipeline(uploaded.read(), uploaded.name)

st.success(
    f"Loaded **{uploaded.name}** — {reports['load']['raw_rows']:,} raw rows → "
    f"{len(df):,} clean rows, {df.shape[1]} columns."
)

stats = summary_stats(df)
c1, c2, c3, c4, c5 = st.columns(5)
c2.metric("Columns", stats["columns"])
c3.metric("Missing", f"{stats['missing_pct']}%")
c4.metric("Duplicates", stats["duplicates"])
c5.metric("Size", f"{stats['memory_mb']} MB")

with st.expander("🧹 What the cleaning did", expanded=False):
    cr = reports["clean"]
    st.write(f"Empty rows removed: **{cr['rows_removed']}**")
    st.write(f"Empty columns removed: **{cr['cols_removed']}**")
    st.write(f"Duplicate rows removed: **{cr['duplicates_removed']}**")

    if reports["renamed"]:
        st.write("Renamed columns:")
        st.json(reports["renamed"])

    tr = reports["types"]
    if tr["dates"]:
        st.write(f"Detected as dates: {', '.join(tr['dates'])}")
    if tr["numeric"]:
        st.write(f"Detected as numbers: {', '.join(tr['numeric'])}")

st.sidebar.header("⚙️ Controls")

num_cols = df.select_dtypes("number").columns.tolist()
date_cols = df.select_dtypes("datetime").columns.tolist()
cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

if not num_cols:
    st.warning("No numeric columns detected — charts need at least one.")
    st.stop()

value_col = st.sidebar.selectbox("Value column (metric)", num_cols)

date_col = None
if date_cols:
    date_col = st.sidebar.selectbox("Date column", date_cols)

cat_col = None
if cat_cols:
    cat_col = st.sidebar.selectbox("Category column", cat_cols)

# date range filter
if date_col:
    lo, hi = df[date_col].min(), df[date_col].max()
    date_range = st.sidebar.date_input("Date range", value=(lo, hi))
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        df = df[(df[date_col] >= start) & (df[date_col] <= end)]

tab_overview, tab_trends, tab_categories, tab_relations, tab_data = st.tabs(
    ["Overview", "Trends", "Categories", "Relations", "Raw Data"]
)

with tab_overview:
    st.subheader("Column Profile")
    st.dataframe(column_profile(df), use_container_width=True, hide_index=True)

    if date_col and value_col:
        st.subheader("Key Insights")
        for line in generate_insights(df, date_col, value_col):
            st.markdown(f"- {line}")

    st.subheader("Distributions")
    pick = st.selectbox("Column to inspect", num_cols, key="hist_pick")
    st.plotly_chart(histogram(df, pick, f"Distribution of {pick}"),
                    use_container_width=True)

with tab_trends:
    if not date_col:
        st.info("No date column detected, so trends aren't available.")
    else:
        freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "ME",
                    "Quarterly": "QE", "Yearly": "YE"}
        fc1, fc2 = st.columns(2)
        freq_label = fc1.radio("Aggregation", list(freq_map), index=2, horizontal=True)
        agg = fc2.selectbox("Aggregate with", ["sum", "mean", "count", "max", "min"])

        trend = trend_by(df, date_col, value_col, freq=freq_map[freq_label], agg=agg)

        st.plotly_chart(
            line_chart(trend, date_col, value_col,
                       f"{value_col} by {freq_label.lower()}"),
            use_container_width=True
        )
        st.dataframe(trend, use_container_width=True, hide_index=True)
