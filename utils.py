"""
utils.py
--------
Shared data-loading, cleaning and feature-engineering functions for the
"Investigate Hotel Business using Data Visualization" project.

Both eda.py (the offline / notebook-style analysis script) and
streamlit_app.py (the interactive dashboard) import this module so that
the cleaning logic is defined ONCE and is guaranteed to be identical in
both places.

Author: Data Analyst (Hotel Business Project)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

RAW_DATA_PATH = "data/hotel_bookings_data.csv"

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

STAY_BUCKET_ORDER = ["1", "2", "3", "4", "5", "6", "7", "8-14", "15+"]

LEAD_TIME_BUCKET_ORDER = [
    "0-7", "8-30", "31-60", "61-90", "91-180", "181-365", "365+"
]

HOTEL_COLORS = {"City Hotel": "#2E86AB", "Resort Hotel": "#E76F51"}


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------

def load_raw_data(path: str = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the raw hotel bookings CSV exactly as delivered."""
    df = pd.read_csv(path)
    return df


# --------------------------------------------------------------------------
# Cleaning
# --------------------------------------------------------------------------

def assess_data_quality(df: pd.DataFrame) -> dict:
    """
    Return a dictionary summarising the data-quality issues in the RAW
    dataframe, before any cleaning. Used for both the printed EDA report
    and the "Data Quality" tab of the Streamlit app.
    """
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    n_duplicates = int(df.duplicated().sum())

    n_negative_adr = int((df["adr"] < 0).sum()) if "adr" in df else 0
    n_extreme_adr = int((df["adr"] > 1000).sum()) if "adr" in df else 0

    guests = df["adults"] + df["children"].fillna(0) + df["babies"]
    n_zero_guests = int((guests == 0).sum())

    n_undefined_meal = int((df["meal"] == "Undefined").sum()) if "meal" in df else 0

    return {
        "n_rows_raw": len(df),
        "missing_by_column": missing.to_dict(),
        "n_duplicates": n_duplicates,
        "n_negative_adr": n_negative_adr,
        "n_extreme_adr": n_extreme_adr,
        "n_zero_guest_bookings": n_zero_guests,
        "n_undefined_meal": n_undefined_meal,
    }


def clean_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Apply every cleaning / preprocessing decision described in Stage 1 of
    the project brief, and return a NEW, cleaned dataframe with extra
    engineered columns used throughout the analysis.

    Cleaning decisions (see README for the full justification of each):
      1. children (4 missing)   -> filled with 0 (assume no children travelling)
      2. city (488 missing)     -> filled with "Unknown"
      3. agent (16,340 missing) -> filled with 0 (no agent = booked directly)
      4. company (112,593 missing) -> filled with 0 (no corporate account)
      5. Duplicate rows (33,261) -> dropped
      6. meal == "Undefined"    -> recoded to "No Meal" (both mean no meal
                                    package was purchased)
      7. adr < 0                -> dropped (invalid / negative price)
      8. adr > 1000              -> kept but flagged (extreme, not impossible,
                                    e.g. long luxury stays); visualisations use
                                    the median or a capped view to stay readable
      9. bookings with 0 total guests -> dropped (data-entry errors)
    """
    df = df_raw.copy()

    # 1. children -------------------------------------------------------
    df["children"] = df["children"].fillna(0)

    # 2. city -------------------------------------------------------
    df["city"] = df["city"].fillna("Unknown")

    # 3 & 4. agent / company: NaN means "not applicable", not "unknown"
    df["agent"] = df["agent"].fillna(0)
    df["company"] = df["company"].fillna(0)

    # 5. duplicates -------------------------------------------------------
    df = df.drop_duplicates()

    # 6. meal -------------------------------------------------------
    df["meal"] = df["meal"].replace({"Undefined": "No Meal"})

    # 7. negative adr -------------------------------------------------------
    df = df[df["adr"] >= 0]

    # 9. zero-guest bookings -------------------------------------------------------
    total_guests = df["adults"] + df["children"] + df["babies"]
    df = df[total_guests > 0]

    # -----------------------------------------------------------------
    # Feature engineering
    # -----------------------------------------------------------------
    df["total_nights"] = df["stays_in_weekend_nights"] + df["stays_in_weekdays_nights"]
    df = df[df["total_nights"] > 0]  # a stay of 0 nights is not a real stay

    df["total_guests"] = total_guests.loc[df.index]

    df["is_canceled"] = df["is_canceled"].astype(int)
    df["status_label"] = df["is_canceled"].map({0: "Not Canceled", 1: "Canceled"})

    # Arrival month as an ordered category (for correct chart ordering)
    df["arrival_date_month"] = pd.Categorical(
        df["arrival_date_month"], categories=MONTH_ORDER, ordered=True
    )

    # A proper arrival date (day 1 of month used only where needed for a
    # continuous year-month timeline)
    month_num = df["arrival_date_month"].cat.codes + 1
    df["arrival_year_month"] = pd.to_datetime(
        dict(year=df["arrival_date_year"], month=month_num, day=1)
    )

    df["stay_bucket"] = bucket_stay_length(df["total_nights"])
    df["lead_time_bucket"] = bucket_lead_time(df["lead_time"])

    return df.reset_index(drop=True)


# --------------------------------------------------------------------------
# Bucketing helpers (kept identical between eda.py and the Streamlit app)
# --------------------------------------------------------------------------

def bucket_stay_length(nights: pd.Series) -> pd.Categorical:
    def _bucket(n):
        if n >= 15:
            return "15+"
        if n >= 8:
            return "8-14"
        return str(int(n))
    return pd.Categorical(nights.apply(_bucket), categories=STAY_BUCKET_ORDER, ordered=True)


def bucket_lead_time(lead_time: pd.Series) -> pd.Categorical:
    bins = [-1, 7, 30, 60, 90, 180, 365, np.inf]
    labels = LEAD_TIME_BUCKET_ORDER
    return pd.cut(lead_time, bins=bins, labels=labels, ordered=True)


# --------------------------------------------------------------------------
# Aggregation helpers used by both EDA script & dashboard
# --------------------------------------------------------------------------

def hotel_share(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["hotel"].value_counts().rename_axis("hotel").reset_index(name="bookings")
    counts["pct"] = (counts["bookings"] / counts["bookings"].sum() * 100).round(1)
    return counts


def monthly_bookings(df: pd.DataFrame) -> pd.DataFrame:
    grp = (
        df.groupby(["hotel", "arrival_date_month"], observed=False)
        .size()
        .reset_index(name="bookings")
    )
    return grp


def cancellation_rate_by(df: pd.DataFrame, by: str) -> pd.DataFrame:
    grp = (
        df.groupby(["hotel", by], observed=False)["is_canceled"]
        .agg(bookings="count", cancellations="sum")
        .reset_index()
    )
    grp["cancellation_rate"] = (grp["cancellations"] / grp["bookings"] * 100).round(1)
    return grp


def overall_cancellation_rate(df: pd.DataFrame) -> pd.DataFrame:
    grp = (
        df.groupby("hotel")["is_canceled"]
        .agg(bookings="count", cancellations="sum")
        .reset_index()
    )
    grp["cancellation_rate"] = (grp["cancellations"] / grp["bookings"] * 100).round(1)
    return grp
