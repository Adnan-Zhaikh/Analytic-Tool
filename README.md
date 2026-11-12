# Analytic Tool

Drop in a CSV or Excel file and get instant stats, charts, and insights. It's a data dashboard built with Streamlit, pandas, and Plotly, and your data never leaves your session.

<!-- Add screenshots: the dashboard after uploading a file, the Trends tab, and the correlation heatmap.
If you deploy it (for example on Streamlit Community Cloud), add the live link here. -->

## Why I built it

Every time I got a new dataset, I repeated the same steps: clean the column names, fix the types, check for missing values and duplicates, then plot the same few charts. I wanted a tool that does that whole routine automatically, so I can understand a file in seconds instead of minutes. It also let me learn the data stack (pandas, Plotly, Streamlit) on one real project.

## What it does

Upload a `.csv`, `.xlsx`, or `.xls` file and it runs a full pipeline:

**1. Cleans the data automatically**
- Normalizes column names (trimmed, lowercase, spaces become underscores, duplicates numbered)
- Detects date columns and number columns stored as text, including values like `$1,200`, `₹500`, or `45%`
- Removes completely empty rows and columns, and duplicate rows
- Shows a "What the cleaning did" report so nothing happens silently

**2. Summarizes it**
- Headline numbers: columns, missing %, duplicates, and memory size
- A column profile with type, missing values, unique count, and min/max/mean/std for each column
- Plain-English insights: highest and lowest period, overall change, and the latest period-over-period change

**3. Lets you explore it in five tabs**

| Tab | What you get |
| --- | --- |
| **Overview** | Column profile, key insights, distribution histogram for any numeric column |
| **Trends** | Line chart by day, week, month, quarter, or year, with sum, mean, count, max, or min |
| **Categories** | Top N categories by your chosen metric, as bar charts |
| **Relations** | Correlation heatmap and a scatter explorer you can color by category |
| **Raw Data** | Search across every column, then download the cleaned data or the column profile as CSV |

A sidebar lets you choose the value column, date column, category column, and date range.

## How it works

The project is split into three files, each with one job:

```
Analytic-Tool/
├── app.py            # The Streamlit interface: layout, widgets, tabs
├── analytics.py      # All data logic: loading, cleaning, profiling, trends, insights
├── charts.py         # Plotly chart builders with one consistent style
├── requirements.txt
└── README.md
```

- `analytics.py` has no Streamlit code in it. It takes a DataFrame and returns a DataFrame or a report, so it can be tested and reused anywhere.
- `charts.py` wraps Plotly Express in small functions that share one `_style()` helper, so every chart looks the same. If there's no data, they return a friendly "No data to display" figure instead of crashing.
- `app.py` calls the other two and arranges the results. The whole cleaning pipeline is cached on the file's content, so changing a control doesn't re-clean the file.

## Stack

Python, Streamlit, pandas, NumPy, Plotly, openpyxl (for Excel files).

## What I learned

- **Streamlit:** building a full interactive app in plain Python: file upload, sidebar controls, columns, tabs, expanders, download buttons, and stopping the page early with `st.stop()` when there's nothing to show yet.
- **Caching:** `@st.cache_data` stops Streamlit from re-running the expensive cleaning on every click.
- **pandas, beyond the basics:**
  - `to_datetime` and `to_numeric` with `errors="coerce"` to turn messy text into real types
  - `resample` to group a time series by day, week, or month
  - `groupby` with different aggregations
  - `select_dtypes` to find columns by type
  - `corr` for the correlation matrix
- **Plotly:** the difference between `plotly.express` for quick charts and `graph_objects` for control (the correlation heatmap), and how to style every figure from one function.
- **Separating logic from the interface:** keeping data code away from UI code makes both easier to read and fix.
- **Handling messy real-world data:** empty data, missing columns, text that looks like numbers, and files with only one numeric column. Most of the work in a tool like this is handling what can go wrong.
- **Writing reports, not just results:** each cleaning step returns a small report of what it changed, which makes the tool easier to trust.

<!-- Optional: add one specific problem you ran into and how you solved it. -->

## Run it locally

Requirements: Python 3.11 or newer.

```bash
git clone https://github.com/Adnan-Zhaikh/Analytic-Tool.git
cd Analytic-Tool
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

It opens at [http://localhost:8501](http://localhost:8501). For a quick test, upload any CSV with a date column, a numeric column, and a category column (sales data works well).

## Roadmap


- [ ] Sample data set to check before uploading the data.

## Author

**Adnan** — [@Adnan-Zhaikh](https://github.com/Adnan-Zhaikh)