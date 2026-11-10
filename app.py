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
