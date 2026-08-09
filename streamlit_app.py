"""
streamlit_app.py
-----------------
Investigate Hotel Business using Data Visualization — Interactive Dashboard

Run with:
    streamlit run streamlit_app.py

This dashboard answers the project's three business questions interactively:
    1. Which hotel type do customers book most often?
    2. Does length of stay affect the cancellation rate?
    3. Does lead time affect the cancellation rate?

It reuses the exact same cleaning logic as eda.py (via utils.py) so numbers
in the dashboard always match the offline analysis.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import utils

# ---------------------------------------------------------------------------
# Page configuration & style
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Hotel Business Intelligence Dashboard",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stHeader"] {
        background-color: #F7F9FB !important;
        color-scheme: light !important;
    }
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }

    .hero {
        padding: 2rem 2.2rem;
        border-radius: 16px;
        background: linear-gradient(120deg, #0F3057 0%, #205295 55%, #2E86AB 100%);
        color: white;
        margin-bottom: 1.6rem;
        box-shadow: 0 8px 24px rgba(15, 48, 87, 0.25);
    }
    .hero h1 {
        margin: 0;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .hero p {
        margin: 0.4rem 0 0 0;
        font-size: 1.02rem;
        opacity: 0.92;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #E7ECF1;
        border-radius: 14px;
        padding: 1rem 1rem 0.6rem 1rem;
        box-shadow: 0 2px 10px rgba(15, 48, 87, 0.05);
    }
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] * {
        color: #5B6B7C !important;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] * {
        color: #0F3057 !important;
    }

    .insight-box {
        background: white;
        border-left: 5px solid #2E86AB;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin: 0.6rem 0 1.1rem 0;
        box-shadow: 0 2px 8px rgba(15, 48, 87, 0.05);
    }
    .rec-card {
        background: white;
        border: 1px solid #E7ECF1;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 10px rgba(15, 48, 87, 0.05);
    }
    .rec-card h4 {
        margin-top: 0;
        color: #0F3057;
    }

    section[data-testid="stSidebar"] {
        background-color: #0F3057;
    }
    section[data-testid="stSidebar"] * {
        color: #F0F4F8 !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
        background-color: #2E86AB !important;
    }

    /* Force readable text in the main content area by targeting Streamlit's
       actual component test-ids (built-in widgets like st.metric / st.tabs /
       st.markdown compute their text color from the active theme via JS, so
       generic tag selectors like "p" or "span" don't reliably win against
       them — the test-id + !important combo below mirrors the technique
       already used for the sidebar, which does work reliably). */
    div[data-testid="stMain"] [data-testid="stMarkdownContainer"],
    div[data-testid="stMain"] [data-testid="stMarkdownContainer"] *,
    div[data-testid="stMain"] [data-testid="stHeading"],
    div[data-testid="stMain"] [data-testid="stHeading"] *,
    div[data-testid="stMain"] [data-testid="stCaptionContainer"],
    div[data-testid="stMain"] [data-testid="stCaptionContainer"] *,
    div[data-testid="stMain"] [data-testid="stTab"],
    div[data-testid="stMain"] [data-testid="stTab"] p,
    div[data-testid="stMain"] [data-testid="stTab"] span {
        color: #1B2733 !important;
    }

    /* Give the tab strip its own light background so dark tab labels are
       never sitting on the platform's dark fallback background. */
    div[data-testid="stMain"] [data-testid="stTabs"] {
        background-color: #F7F9FB;
    }
    div[data-testid="stMain"] [data-baseweb="tab-border"] {
        background-color: #E7ECF1 !important;
    }

    .insight-box, .insight-box * ,
    .rec-card p, .rec-card p * {
        color: #1B2733 !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

HOTEL_COLORS = utils.HOTEL_COLORS
PLOTLY_TEMPLATE = "plotly_white"


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading and cleaning data...")
def get_clean_data(file) -> pd.DataFrame:
    if file is None:
        raw = utils.load_raw_data(utils.RAW_DATA_PATH)
    else:
        raw = pd.read_csv(file)
    return utils.clean_data(raw)


@st.cache_data(show_spinner=False)
def get_raw_data(file) -> pd.DataFrame:
    if file is None:
        return utils.load_raw_data(utils.RAW_DATA_PATH)
    return pd.read_csv(file)


# ---------------------------------------------------------------------------
# Sidebar — data source & filters
# ---------------------------------------------------------------------------

st.sidebar.markdown("## 🏨 Hotel Analytics")
st.sidebar.caption("Investigate Hotel Business using Data Visualization")

uploaded = st.sidebar.file_uploader(
    "Upload a different bookings CSV (optional)", type=["csv"]
)

try:
    df_raw = get_raw_data(uploaded)
    df = get_clean_data(uploaded)
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

st.sidebar.markdown("### Filters")

hotel_options = sorted(df["hotel"].unique().tolist())
sel_hotels = st.sidebar.multiselect("Hotel type", hotel_options, default=hotel_options)

year_options = sorted(df["arrival_date_year"].unique().tolist())
sel_years = st.sidebar.multiselect("Arrival year", year_options, default=year_options)

month_options = [m for m in utils.MONTH_ORDER if m in df["arrival_date_month"].unique()]
sel_months = st.sidebar.multiselect("Arrival month", month_options, default=month_options)

st.sidebar.markdown("---")
if st.sidebar.button("↺ Reset filters"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Cleaned dataset: **{len(df):,}** bookings "
    f"({len(df_raw):,} raw rows before cleaning)."
)

mask = (
    df["hotel"].isin(sel_hotels)
    & df["arrival_date_year"].isin(sel_years)
    & df["arrival_date_month"].isin(sel_months)
)
fdf = df[mask].copy()

if fdf.empty:
    st.warning("No bookings match the selected filters. Please widen your selection.")
    st.stop()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>🏨 Hotel Business Intelligence Dashboard</h1>
        <p>Understanding booking &amp; cancellation behaviour · Hotel bookings dataset, 2017–2019</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

total_bookings = len(fdf)
cancel_rate = fdf["is_canceled"].mean() * 100
avg_lead = fdf["lead_time"].mean()
avg_nights = fdf["total_nights"].mean()
avg_adr = fdf["adr"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Bookings", f"{total_bookings:,}")
k2.metric("Cancellation Rate", f"{cancel_rate:.1f}%")
k3.metric("Avg. Lead Time", f"{avg_lead:.0f} days")
k4.metric("Avg. Stay Length", f"{avg_nights:.1f} nights")
k5.metric("Avg. Daily Rate", f"${avg_adr:,.0f}")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_quality, tab_hotel, tab_stay, tab_lead, tab_reco = st.tabs(
    [
        "📊 Overview",
        "🧹 Data Quality",
        "🏨 Hotel Type & Seasonality",
        "🛏️ Stay Duration",
        "⏳ Lead Time",
        "✅ Recommendations",
    ]
)

# --- Overview ---------------------------------------------------------------
with tab_overview:
    st.subheader("Dataset Overview")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.write(
            f"The dataset covers hotel bookings from "
            f"**{int(df['arrival_date_year'].min())}** to "
            f"**{int(df['arrival_date_year'].max())}**, across **City Hotel** "
            f"and **Resort Hotel** properties. After cleaning, "
            f"**{len(df):,}** bookings remain "
            f"({fdf.shape[0]:,} match your current filters)."
        )
        st.dataframe(fdf.head(20), width='stretch', height=320)
    with c2:
        st.markdown("**Columns used in this analysis**")
        st.markdown(
            "- `hotel` — City / Resort\n"
            "- `is_canceled` — cancellation flag\n"
            "- `lead_time` — days between booking & arrival\n"
            "- `stays_in_*_nights` — length of stay\n"
            "- `arrival_date_month/year` — seasonality\n"
            "- `adr` — average daily rate"
        )
    st.download_button(
        "⬇️ Download filtered data (CSV)",
        fdf.to_csv(index=False).encode("utf-8"),
        file_name="filtered_hotel_bookings.csv",
        mime="text/csv",
    )

# --- Data Quality -------------------------------------------------------
with tab_quality:
    st.subheader("Data Assessment & Cleaning")
    q = utils.assess_data_quality(df_raw)

    st.markdown(
        f"""
        <div class="insight-box">
        Started with <b>{q['n_rows_raw']:,}</b> raw rows →
        <b>{len(df):,}</b> rows after cleaning
        ({(q['n_rows_raw']-len(df))/q['n_rows_raw']*100:.1f}% removed).
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        miss = pd.Series(q["missing_by_column"]).reset_index()
        miss.columns = ["column", "missing"]
        if not miss.empty:
            fig = px.bar(
                miss, x="missing", y="column", orientation="h",
                title="Missing Values by Column (raw data)",
                color_discrete_sequence=["#2E86AB"],
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(yaxis_title="", xaxis_title="Missing rows")
            st.plotly_chart(fig, width='stretch')
    with c2:
        anomalies = pd.DataFrame({
            "issue": ["Duplicate rows", "Undefined meal", "Negative adr", "Zero-guest bookings"],
            "count": [q["n_duplicates"], q["n_undefined_meal"], q["n_negative_adr"], q["n_zero_guest_bookings"]],
        })
        fig = px.bar(
            anomalies, x="issue", y="count",
            title="Other Data Quality Issues Found",
            color_discrete_sequence=["#E76F51"],
            template=PLOTLY_TEMPLATE,
        )
        fig.update_layout(xaxis_title="", yaxis_title="Rows affected")
        st.plotly_chart(fig, width='stretch')

    st.markdown("#### Cleaning decisions")
    st.markdown(
        """
| Issue | Decision | Why |
|---|---|---|
| `children` missing | Fill with 0 | Assume no children travelling |
| `city` missing | Fill with "Unknown" | Too few rows to drop |
| `agent` missing | Fill with 0 | NaN = booked directly, no agent |
| `company` missing | Fill with 0 | NaN = not a corporate booking |
| Duplicate rows | Dropped | Exact duplicates are repeated records |
| `meal` = "Undefined" | Recoded to "No Meal" | Same real-world meaning |
| Negative `adr` | Dropped | Invalid price |
| 0-guest bookings | Dropped | Not a real booking |
| 0-night bookings | Dropped | Not a real stay |
"""
    )

# --- Hotel Type & Seasonality --------------------------------------------
with tab_hotel:
    st.subheader("Business Question 1 — Which hotel type is booked most often?")

    share = utils.hotel_share(fdf)
    monthly = utils.monthly_bookings(fdf)

    c1, c2 = st.columns([1, 2])
    with c1:
        fig = px.pie(
            share, names="hotel", values="bookings", hole=0.45,
            color="hotel", color_discrete_map=HOTEL_COLORS,
            template=PLOTLY_TEMPLATE, title="Share of Bookings by Hotel Type",
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, width='stretch')
    with c2:
        fig = px.line(
            monthly, x="arrival_date_month", y="bookings", color="hotel",
            markers=True, color_discrete_map=HOTEL_COLORS,
            category_orders={"arrival_date_month": utils.MONTH_ORDER},
            template=PLOTLY_TEMPLATE, title="Bookings per Month by Hotel Type",
        )
        fig.update_layout(xaxis_title="Arrival Month", yaxis_title="Bookings", legend_title="")
        st.plotly_chart(fig, width='stretch')

    busiest = monthly.groupby("arrival_date_month", observed=False)["bookings"].sum().idxmax()
    quietest = monthly.groupby("arrival_date_month", observed=False)["bookings"].sum().idxmin()
    top = share.iloc[0]
    st.markdown(
        f"""
        <div class="insight-box">
        <b>{top['hotel']}</b> is booked most often, making up <b>{top['pct']}%</b>
        of bookings in the current selection. Bookings peak in
        <b>{busiest}</b> and are quietest in <b>{quietest}</b> — likely
        reflecting seasonal travel and holiday patterns.
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Stay Duration --------------------------------------------------------
with tab_stay:
    st.subheader("Business Question 2 — Does stay length affect cancellations?")

    overall = utils.overall_cancellation_rate(fdf)
    by_stay = utils.cancellation_rate_by(fdf, "stay_bucket")

    c1, c2 = st.columns([1, 2])
    with c1:
        fig = px.bar(
            overall, x="hotel", y="cancellation_rate", color="hotel",
            color_discrete_map=HOTEL_COLORS, template=PLOTLY_TEMPLATE,
            title="Overall Cancellation Rate by Hotel Type", text="cancellation_rate",
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False, yaxis_title="Cancellation Rate (%)", xaxis_title="")
        st.plotly_chart(fig, width='stretch')
    with c2:
        fig = px.line(
            by_stay, x="stay_bucket", y="cancellation_rate", color="hotel",
            markers=True, color_discrete_map=HOTEL_COLORS,
            category_orders={"stay_bucket": utils.STAY_BUCKET_ORDER},
            template=PLOTLY_TEMPLATE, title="Cancellation Rate vs. Total Length of Stay",
        )
        fig.update_layout(xaxis_title="Total Nights Booked", yaxis_title="Cancellation Rate (%)", legend_title="")
        st.plotly_chart(fig, width='stretch')

    higher = overall.loc[overall["cancellation_rate"].idxmax()]
    st.markdown(
        f"""
        <div class="insight-box">
        <b>{higher['hotel']}</b> has the higher overall cancellation rate at
        <b>{higher['cancellation_rate']}%</b>. Across both hotel types,
        cancellation rate tends to <b>rise with stay length</b> — long
        stays are booked more provisionally and cancelled more often.
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Lead Time --------------------------------------------------------
with tab_lead:
    st.subheader("Business Question 3 — Does lead time affect cancellations?")

    by_lead = utils.cancellation_rate_by(fdf, "lead_time_bucket")

    fig = px.line(
        by_lead, x="lead_time_bucket", y="cancellation_rate", color="hotel",
        markers=True, color_discrete_map=HOTEL_COLORS,
        category_orders={"lead_time_bucket": utils.LEAD_TIME_BUCKET_ORDER},
        template=PLOTLY_TEMPLATE, title="Cancellation Rate vs. Lead Time",
    )
    fig.update_layout(xaxis_title="Lead Time (days before arrival)", yaxis_title="Cancellation Rate (%)", legend_title="")
    st.plotly_chart(fig, width='stretch')

    lowest = by_lead.loc[by_lead["cancellation_rate"].idxmin()]
    highest = by_lead.loc[by_lead["cancellation_rate"].idxmax()]
    st.markdown(
        f"""
        <div class="insight-box">
        Cancellation rate is lowest for bookings made
        <b>{lowest['lead_time_bucket']} days</b> ahead
        (<b>{lowest['hotel']}</b>, {lowest['cancellation_rate']}%), and highest for
        <b>{highest['lead_time_bucket']} days</b> ahead
        (<b>{highest['hotel']}</b>, {highest['cancellation_rate']}%).
        The longer the gap between booking and arrival, the more likely
        a guest's plans change before check-in.
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- Recommendations --------------------------------------------------------
with tab_reco:
    st.subheader("Summary & Business Recommendations")

    recs = [
        ("📈 Grow & capitalise on seasonality",
         "Promote off-peak packages for the less-booked hotel type and use "
         "dynamic pricing / early-bird offers during peak months for the "
         "more popular one."),
        ("🛏️ Protect revenue from long-stay cancellations",
         "Introduce partial non-refundable deposits or tiered cancellation "
         "fees that scale with stay length, with better rates for guests "
         "who commit to non-refundable long stays."),
        ("⏳ Reduce far-ahead-booking cancellations",
         "Send automatic reminders as the stay approaches, require a small "
         "deposit for bookings made more than ~3 months out, and offer easy, "
         "fee-light rescheduling instead of cancellation."),
        ("🎯 Highest-impact action",
         "A modest deposit requirement for long-lead-time bookings — this is "
         "where cancellation rates are highest and the booking volume is "
         "largest, so it offers the best return on effort."),
    ]
    for title, text in recs:
        st.markdown(
            f"""<div class="rec-card"><h4>{title}</h4><p>{text}</p></div>""",
            unsafe_allow_html=True,
        )

    st.info(
        "These recommendations follow directly from the charts in the "
        "**Hotel Type**, **Stay Duration** and **Lead Time** tabs — adjust "
        "the sidebar filters to re-check them against any subset of the data."
    )

st.markdown("---")
st.caption("Built with Streamlit · Plotly · Pandas — Investigate Hotel Business using Data Visualization project")
