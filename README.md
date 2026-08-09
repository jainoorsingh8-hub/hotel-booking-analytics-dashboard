# 🏨 Investigate Hotel Business using Data Visualization

Sample URL- https://hotel-booking-analytics-dashboard-rgddtckk3nkfuaerfgs4n5.streamlit.app/

An end-to-end analysis of a 2017–2019 hotel bookings dataset (~119K rows),
answering three business questions for hotel management:

1. **Which hotel type do customers book most often?**
2. **Does length of stay affect the cancellation rate?**
3. **Does lead time (booking-to-arrival gap) affect the cancellation rate?**

The project has two parts that share one cleaning pipeline (`utils.py`), so
their numbers always match:

| File | Purpose |
|---|---|
| `eda.py` | Standalone script (Matplotlib/Seaborn) that reproduces the full brief: data overview, cleaning, the 3 business questions, and a written summary + recommendations. Saves static charts to `charts/`. |
| `streamlit_app.py` | Interactive Plotly/Streamlit dashboard with filters, KPIs, and the same three analyses, for presenting to non-technical stakeholders. |
| `utils.py` | Shared data loading, cleaning, feature engineering and aggregation functions used by both of the above. |

## 📁 Project Structure

```
hotel_project/
├── data/
│   └── hotel_bookings_data.csv     # raw dataset (input)
├── charts/                         # PNG charts produced by eda.py
├── .streamlit/
│   └── config.toml                 # dashboard theme
├── utils.py                        # shared cleaning & aggregation logic
├── eda.py                          # Stage 0-3 analysis script (matplotlib/seaborn)
├── streamlit_app.py                # interactive dashboard (plotly)
├── requirements.txt
└── README.md
```

Running either script also produces, at the project root:
- `data/cleaned_hotel_bookings.csv` — the cleaned dataset
- `insights_report.md` — the written summary & recommendations (Stage 3)

## 🚀 Getting Started

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the offline EDA (prints the full analysis, saves charts + report)
python eda.py

# 4. Launch the interactive dashboard
streamlit run streamlit_app.py
```

The dashboard opens at `http://localhost:8501`. Use the sidebar to filter by
hotel type, year and month — every chart, KPI and insight box updates live.
You can also upload a different bookings CSV from the sidebar (it must share
the same columns) to reuse the dashboard on new data.

## 🧹 Data Cleaning Summary

| Issue | Rows affected | Decision |
|---|---:|---|
| `children` missing | 4 | Filled with 0 |
| `city` missing | 488 | Filled with "Unknown" |
| `agent` missing | 16,340 | Filled with 0 (no agent used) |
| `company` missing | 112,593 | Filled with 0 (not corporate) |
| Duplicate rows | 33,261 | Dropped |
| `meal` = "Undefined" | ~1,169 | Recoded to "No Meal" |
| Negative `adr` | 1 | Dropped |
| 0-guest bookings | 180 | Dropped |

Full justification for each decision is in the docstring of
`utils.clean_data()` and printed by `eda.py` when it runs.

## 📊 Key Findings (see `insights_report.md` after running `eda.py`)

- **City Hotel** accounts for the majority of bookings and is busiest in the
  autumn months.
- **Cancellation rate rises with length of stay**, and is consistently higher
  for City Hotel than Resort Hotel.
- **Cancellation rate rises sharply with lead time** — bookings made under a
  week before arrival are cancelled far less often than bookings made many
  months ahead.

## 🛠️ Tech Stack

- **Data**: Pandas, NumPy
- **Static charts (brief requirement)**: Matplotlib, Seaborn
- **Interactive dashboard**: Streamlit, Plotly

## 📓 Turning this into the required Jupyter Notebook submission

The brief asks for a single `.ipynb` exported to PDF/HTML. `eda.py` is
written section-by-section (Stage 0 → Stage 3) so you can paste each function
body into its own notebook cell, run it, and the printed text + saved PNGs
become your notebook's markdown and output cells. If you'd like, this can
also be generated as an actual `.ipynb` file — just ask.
