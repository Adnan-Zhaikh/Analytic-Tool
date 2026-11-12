import os

import pandas as pd
import numpy as np
from io import BytesIO

def load_file(uploaded_file):
    """
    Read a CSV or Excel file object into a DataFrame.
    Returns (df, report) where report is a dict of what happened.
    """
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()

    if name.endswith(".csv"):
        df = pd.read_csv(BytesIO(raw))
    elif name.endswith((".xlsx",".xls")):
        df = pd.read_excel(BytesIO(raw))
    else:
        raise ValueError(f"Unsupported file type: {name}")

    report = {"filename": uploaded_file.name, "raw_rows": len(df)}
    return df, report

def normalize_columns(df):
    """
    Clean column names and report any duplicates created.
    """
    original = list(df.columns)
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
          .str.strip()
          .str.replace(r"\s+", "_", regex=True)
          .str.lower()
    )

    seen, new_cols = {}, []
    for c in df.columns:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols

    renamed = {o: n for o, n in zip(original, new_cols) if str(o) != n}
    return df, renamed

def infer_types(df, max_date_ratio=0.7):
    """
    Try to convert object columns into datetime or numeric.
    Returns (df, type_report).
    """
    df = df.copy()
    report = {"dates": [], "numeric": [], "failed": []}

    for col in df.select_dtypes(include="object").columns:
        sample = df[col].dropna().astype(str).head(500)
        if sample.empty:
            continue

        # try dates first — "2024-01-05" is also parseable as text
        parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
        if parsed.notna().mean() >= max_date_ratio:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
            report["dates"].append(col)
            continue

        # then numbers — strip commas, currency symbols, percent signs
        cleaned = (
            sample.str.replace(r"[,\$₹€£%]", "", regex=True)
                  .str.strip()
        )
        num = pd.to_numeric(cleaned, errors="coerce")
        if num.notna().mean() >= max_date_ratio:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[,\$₹€£%]", "", regex=True),
                errors="coerce"
            )
            report["numeric"].append(col)

    return df, report

def clean_data(df):
    """
    Drop empty rows/cols, handle duplicates. Returns (df, clean_report).
    """
    df = df.copy()
    before = df.shape

    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")

    dupes = int(df.duplicated().sum())
    df = df.drop_duplicates()

    report = {
        "rows_removed": before[0] - df.shape[0],
        "cols_removed": before[1] - df.shape[1],
        "duplicates_removed": dupes,
    }
    return df, report

def summary_stats(df):
    """
    High-Level KPIs for the dashboard header row.
    """
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "missing_pct": round(float(df.isna().mean().mean() * 100), 2),
        "duplicates": int(df.duplicated().sum()),
        "numeric_cols": int(df.select_dtypes("number").shape[1]),
        "date_cols": int(df.select_dtypes("datetime").shape[1]),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1_048_576, 2),
    }

def column_profile(df):
    """
    One row per column: dtype, missing, unique, min/max, mean/std, etc.
    """
    rows = []
    for col in df.columns:
        s = df[col]
        row = {
            "column": col,
            "dtype": str(s.dtype),
            "missing": int(s.isna().sum()),
            "missing_pct": round(float(s.isna().mean() * 100), 2),
            "unique": int(s.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(s):
            row["min"] = float(s.min())
            row["max"] = float(s.max())
            row["mean"] = round(float(s.mean()), 2) if s.notna().any() else None
            row["std"] = round(float(s.std()), 2) if s.notna().any() else None
        elif pd.api.types.is_datetime64_any_dtype(s):
            row["min"] = s.min()
            row["max"] = s.max()
            row["mean"] = None
            row["std"] = None
        else:
            row["min"] = row["max"] = row["mean"] = row["std"] = None
        rows.append(row)
    return pd.DataFrame(rows)

def trend_by(df, date_col, value_col, freq="ME", agg="sum"):
    """
    Aggregate a value column by a date column, returning a time series.
    freq: "D", "W", "M", "ME", "Q", "Y"
    agg: "sum", "mean", "median", etc.
    """
    df = df.copy()
    if date_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"Columns not found: {date_col}, {value_col}")

    work = df[[date_col, value_col]].dropna()
    if work.empty:
        return pd.DataFrame(columns=[date_col, value_col])

    grouped = (
        work.set_index(date_col)[value_col]
          .resample(freq)
          .agg(agg)
          .reset_index()
    )
    return grouped

def category_breakdown(df, cat_col, value_col, top_n=10, agg="sum"):
    """
    Aggregate a value column by a categorical column, returning top N categories.
    """
    df = df.copy()
    if cat_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"Columns not found: {cat_col}, {value_col}")

    work = df[[cat_col, value_col]].dropna()
    if work.empty:
        return pd.DataFrame(columns=[cat_col, value_col])

    grouped = (
        work.groupby(cat_col)[value_col]
            .agg(agg)
            .reset_index()
            .sort_values(by=value_col, ascending=False)
            .head(top_n)
    )
    return grouped

def correlation_matrix(df, method="pearson"):
    """
    Compute correlation matrix for numeric columns.
    method: "pearson", "spearman", "kendall"
    """
    num = df.select_dtypes(include="number")
    if num.shape[1] < 2:
        return None  # Not enough numeric columns for correlation
    return num.corr(method=method, numeric_only=True)

def generate_insights(df, date_col, value_col, freq="ME"):
    """
    Generate a list of insights based on the data.
    Returns a list of strings.
    """
    trend = trend_by(df, date_col, value_col, freq=freq)
    if len(trend) < 2:
        return ["Not enough data to generate insights."]

    v = trend[value_col]
    insights = []

    peak_idx = v.idxmax()
    low_idx = v.idxmin()
    insights.append(
        f"Highest {value_col} was {v[peak_idx]:,.2f} "
        f"in {pd.Timestamp(trend.loc[peak_idx, date_col]).strftime('%b %Y')}."
    )
    insights.append(
        f"Lowest {value_col} was {v[low_idx]:,.2f} "
        f"in {pd.Timestamp(trend.loc[low_idx, date_col]).strftime('%b %Y')}."
    )

    first, last = v.iloc[0], v.iloc[-1]
    if first != 0:
        pct = ((last - first) / abs(first)) * 100
        direction = "increase" if pct > 0 else "decrease"
        insights.append(
            f"Overall trend is a {direction} of {abs(pct):.2f}% from {first:,.2f} to {last:,.2f}."
        )

    if len(v) >= 2:
        prev, curr = v.iloc[-2], v.iloc[-1]
        if prev != 0:
            mom = ((curr - prev) / abs(prev)) * 100
            insights.append(
                f"Month-over-month change is {mom:+.2f}% from {prev:,.2f} to {curr:,.2f}."
            )

    return insights

def load_sample(path="data/sample_sales.csv"):
    """
    Load the bundled sample dataset.
    Returns (df, report) in the same shape as load_file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Sample file not found at {path}")

    df = pd.read_csv(path)
    report = {"filename": os.path.basename(path), "raw_rows": len(df)}
    return df, report
