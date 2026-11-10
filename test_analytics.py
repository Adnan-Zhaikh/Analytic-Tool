import pandas as pd
from analytics import (normalize_columns, infer_types, clean_data,
                       summary_stats, trend_by, category_breakdown)

def test_pipeline():
    raw = pd.DataFrame({
        " Order Date ": ["2024-01-05", "2024-02-10", "2024-02-15", "bad-date"],
        "Total ": ["1,250.50", "900", "2,100.75", "500"],
        "Region": ["North", "South", "North", None],
        "Empty": [None, None, None, None],
    })

    df, _ = normalize_columns(raw)
    assert list(df.columns) == ["order_date", "total", "region", "empty"]

    df, types = infer_types(df)
    assert "order_date" in types["dates"]
    assert "total" in types["numeric"]

    df, clean = clean_data(df)
    assert "empty" not in df.columns          # all-empty column dropped
    assert clean["cols_removed"] == 1

    s = summary_stats(df)
    assert s["rows"] == 4

    t = trend_by(df, "order_date", "total", freq="ME")
    assert len(t) == 2                        # Jan + Feb

    b = category_breakdown(df, "region", "total", top_n=5)
    assert b.iloc[0]["region"] == "North"     # 1250.50 + 2100.75

    print("All checks passed")

if __name__ == "__main__":
    test_pipeline()
