import streamlit as st
import pandas as pd

from charts import (
    line_chart, bar_chart, histogram, scatter_plot, heatmap
)

from analytics import (
    load_file, generate_sample, normalize_columns, infer_types, clean_data,
    summary_stats, column_profile, trend_by,
    category_breakdown, correlation_matrix, generate_insights,
)


st.set_page_config(page_title="Data Dashboard",page_icon=":bar_chart:", layout="wide")

@st.cache_data(show_spinner=False)
def process_pipeline(file_bytes, filename):
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
    return df, {
        "load": load_report,
        "renamed": renamed,
        "types": type_report,
        "clean": clean_report,
    }

@st.cache_data(show_spinner=False)
def process_sample():
    """Same pipeline as process_pipeline, but generates data in memory."""
    df, load_report = generate_sample()
    df, renamed = normalize_columns(df)
    df, type_report = infer_types(df)
    df, clean_report = clean_data(df)
    return df, {
        "load": load_report, "renamed": renamed,
        "types": type_report, "clean": clean_report,
    }



st.title("📊 Upload & Analyse")
st.caption("Drop a CSV or Excel file — get instant stats, charts and insights.")

# initialise once
if "data_source" not in st.session_state:
    st.session_state.data_source = None

col_a, col_b = st.columns([3, 1])

with col_a:
    uploaded = st.file_uploader(
        "Choose a file", type=["csv", "xlsx", "xls"], label_visibility="collapsed"
    )

with col_b:
    st.write("")
    if st.button("🎲 Try sample data", use_container_width=True):
        st.session_state.data_source = "sample"

# an upload always takes precedence and clears the sample flag
if uploaded is not None:
    st.session_state.data_source = "upload"
    df, reports = process_pipeline(uploaded.getvalue(), uploaded.name)
    source_label = uploaded.name
elif st.session_state.data_source == "sample":
    df, reports = process_sample()
    source_label = reports["load"]["filename"] + " (sample)"
else:
    st.info(
        "Upload a file, or click **Try sample data** to explore with a "
        "2,600-row retail sales dataset."
    )
    st.stop()

st.success(
    f"Loaded **{source_label}** — {reports['load']['raw_rows']:,} raw rows → "
    f"{len(df):,} clean rows, {df.shape[1]} columns."
)

stats = summary_stats(df)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rows", f"{stats['rows']:,}")
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

with tab_categories:
    if not cat_col:
        st.info("No category column detected.")
    else:
        top_n = st.slider("Show top N categories", 3, 30, 10)
        breakdown = category_breakdown(df, cat_col, value_col, top_n=top_n)

        left, right = st.columns([3, 2])
        with left:
            st.plotly_chart(
                bar_chart(breakdown, cat_col, value_col,
                          f"Top {top_n} {cat_col} by {value_col}"),
                use_container_width=True
            )
        with right:
            st.plotly_chart(
                bar_chart(breakdown, cat_col, value_col,
                          "Same data, horizontal", horizontal=True),
                use_container_width=True
            )
        st.dataframe(breakdown, use_container_width=True, hide_index=True)

with tab_relations:
    if len(num_cols) < 2:
        st.info("Need at least two numeric columns for this view.")
    else:
        st.subheader("Correlation Matrix")
        st.plotly_chart(heatmap(correlation_matrix(df)), use_container_width=True)

        st.subheader("Scatter Explorer")
        s1, s2, s3 = st.columns(3)
        x_col = s1.selectbox("X axis", num_cols, index=0, key="sc_x")
        y_col = s2.selectbox("Y axis", num_cols, index=min(1, len(num_cols) - 1), key="sc_y")
        color_by = s3.selectbox("Colour by", ["None"] + cat_cols, key="sc_c")

        st.plotly_chart(
            scatter_plot(df, x_col, y_col,
                         color=None if color_by == "None" else color_by,
                         title=f"{y_col} vs {x_col}"),
            use_container_width=True
        )

with tab_data:
    st.subheader("Filtered Data")
    st.caption(f"{len(df):,} rows × {df.shape[1]} columns")

    search = st.text_input("Search across all columns")
    view = df
    if search:
        mask = df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        view = df[mask]
        st.caption(f"{len(view):,} rows match “{search}”")

    st.dataframe(view.head(1000), use_container_width=True, hide_index=True)
    if len(view) > 1000:
        st.caption("Showing the first 1,000 rows. Use the download button for the full set.")

    st.divider()
    d1, d2 = st.columns(2)

    d1.download_button(
        "⬇️ Download cleaned data (CSV)",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name="cleaned_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

    summary = column_profile(view).to_csv(index=False).encode("utf-8")
    d2.download_button(
        "⬇️ Download column profile (CSV)",
        data=summary,
        file_name="column_profile.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.divider()
st.caption("Built with pandas + Plotly + Streamlit · Data never leaves your session.")
st.caption("Sample: 2 years of retail orders across 5 regions — includes messy data on purpose.")
