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