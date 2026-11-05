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

    