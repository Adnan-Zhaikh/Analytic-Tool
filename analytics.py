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
        if parsed.notna().mea() >= max_date_ratio:
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