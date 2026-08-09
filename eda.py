"""
eda.py
------
Investigate Hotel Business using Data Visualization
Standalone Exploratory Data Analysis script (Stage 0 -> Stage 3 of the
project brief), built with Pandas / NumPy / Matplotlib / Seaborn as
required by the brief.

Run with:
    python eda.py

What it does:
    1. Loads the raw dataset and prints a data overview (Stage 1.1)
    2. Assesses data quality: missing values, duplicates, inconsistent
       values, anomalies (Stage 1.2) and cleans the data (utils.clean_data)
    3. Answers the three business questions with charts saved to ./charts
       (Stage 2.1, 2.2, 2.3)
    4. Prints a written summary & business recommendations (Stage 3) and
       saves them to insights_report.md
    5. Saves the cleaned dataset to data/cleaned_hotel_bookings.csv so the
       Streamlit dashboard can reuse it without re-cleaning

This script intentionally prints its reasoning to the console (like a
notebook's markdown + output cells) so it can be pasted straight into a
Jupyter Notebook if a .ipynb submission is required.
"""

import os
import textwrap

import matplotlib
matplotlib.use("Agg")  # headless, safe for servers / CI
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

import utils

sns.set_theme(style="whitegrid", palette="deep")
CHART_DIR = "charts"
os.makedirs(CHART_DIR, exist_ok=True)

HOTEL_PALETTE = utils.HOTEL_COLORS


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def savefig(fig, name: str) -> None:
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> saved {path}")


# ---------------------------------------------------------------------------
# STAGE 0 — Problem Statement
# ---------------------------------------------------------------------------

def stage0():
    section("STAGE 0 — PROBLEM STATEMENT")
    print(textwrap.dedent("""
    Why booking behaviour matters:
      Understanding who books, when, and who cancels lets a hotel forecast
      occupancy, price rooms correctly, staff appropriately for busy periods,
      and design deposit / cancellation policies that protect revenue without
      discouraging genuine guests.

    Three business questions this project answers:
      1. Which hotel type do customers book most often (City vs Resort)?
      2. Does length of stay affect the cancellation rate?
      3. Does lead time (booking-to-arrival gap) affect the cancellation rate?

    Objective / main deliverable:
      A data-driven report (this script + its charts + the companion Streamlit
      dashboard) that quantifies booking and cancellation patterns and turns
      them into concrete, actionable recommendations for hotel management.
    """))


# ---------------------------------------------------------------------------
# STAGE 1 — Data Preprocessing
# ---------------------------------------------------------------------------

def stage1():
    section("STAGE 1 — DATA PREPROCESSING")

    df_raw = utils.load_raw_data()
    print(f"1.1 Data Overview")
    print(f"  Rows x Columns : {df_raw.shape[0]:,} x {df_raw.shape[1]}")
    print(f"  Period covered : {df_raw['arrival_date_year'].min()}"
          f" - {df_raw['arrival_date_year'].max()}")
    print("  Columns most relevant to the business questions:")
    print("    hotel, is_canceled, lead_time, arrival_date_month/year,")
    print("    stays_in_weekend_nights, stays_in_weekdays_nights")

    print("\n1.2 Data Assessment (BEFORE cleaning)")
    q = utils.assess_data_quality(df_raw)
    print(f"  Missing values by column:")
    for col, n in q["missing_by_column"].items():
        pct = n / q["n_rows_raw"] * 100
        print(f"    {col:<10} {n:>7,} missing  ({pct:5.1f}%)")
    print(f"  Duplicate rows            : {q['n_duplicates']:,}")
    print(f"  Rows with 'Undefined' meal: {q['n_undefined_meal']:,}")
    print(f"  Negative adr rows         : {q['n_negative_adr']:,}")
    print(f"  adr > 1000 (extreme) rows : {q['n_extreme_adr']:,}")
    print(f"  Zero-guest bookings       : {q['n_zero_guest_bookings']:,}")

    print(textwrap.dedent("""
    Cleaning decisions & justification:
      - children (4 missing)        -> fill 0.  Implies solo/adults-only booking.
      - city (488 missing)          -> fill "Unknown". Too few to drop; kept
                                        for completeness of other columns.
      - agent (16,340 missing)      -> fill 0. NaN means the guest booked
                                        directly, without a travel agent.
      - company (112,593 missing)   -> fill 0. NaN means it was not a
                                        corporate-negotiated booking.
      - 33,261 duplicate rows       -> dropped. Exact full-row duplicates are
                                        almost certainly repeated records, not
                                        genuinely identical independent bookings.
      - meal == "Undefined"         -> recoded to "No Meal" (same real-world
                                        meaning: no meal package purchased).
      - 1 row with negative adr     -> dropped (invalid price, data-entry error).
      - 180 bookings with 0 guests  -> dropped (adults+children+babies == 0
                                        cannot be a real booking).
      - adr > 1000 (63 rows)        -> kept but treated as legitimate outliers
                                        (e.g. long/luxury bookings); charts use
                                        rates/medians so they are not distorted.
    """))

    df = utils.clean_data(df_raw)
    print(f"  Rows AFTER cleaning: {len(df):,} "
          f"(removed {len(df_raw) - len(df):,} rows, "
          f"{ (len(df_raw)-len(df))/len(df_raw)*100:.1f}% of raw data)")

    df.to_csv("data/cleaned_hotel_bookings.csv", index=False)
    print("  -> saved data/cleaned_hotel_bookings.csv")
    return df


# ---------------------------------------------------------------------------
# STAGE 2.1 — Hotel type & seasonality
# ---------------------------------------------------------------------------

def stage2_1(df: pd.DataFrame):
    section("STAGE 2.1 — MONTHLY BOOKING ANALYSIS BY HOTEL TYPE")

    share = utils.hotel_share(df)
    print(share.to_string(index=False))
    top = share.iloc[0]
    print(f"\n  -> '{top['hotel']}' is booked most often "
          f"({top['pct']}% of all bookings).")

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        share["bookings"], labels=share["hotel"], autopct="%1.1f%%",
        colors=[HOTEL_PALETTE.get(h, "#888888") for h in share["hotel"]],
        startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    ax.set_title("Share of Bookings by Hotel Type", fontsize=14, fontweight="bold")
    savefig(fig, "01_hotel_type_share.png")

    monthly = utils.monthly_bookings(df)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(
        data=monthly, x="arrival_date_month", y="bookings", hue="hotel",
        marker="o", palette=HOTEL_PALETTE, ax=ax,
    )
    ax.set_title("Bookings per Month by Hotel Type (2017-2019 combined)",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Arrival Month")
    ax.set_ylabel("Number of Bookings")
    plt.xticks(rotation=40, ha="right")
    ax.legend(title="")
    savefig(fig, "02_monthly_bookings_by_hotel.png")

    busiest = monthly.groupby("arrival_date_month", observed=False)["bookings"].sum().idxmax()
    quietest = monthly.groupby("arrival_date_month", observed=False)["bookings"].sum().idxmin()
    print(f"  Busiest month overall : {busiest}")
    print(f"  Quietest month overall: {quietest}")
    return {"share": share, "monthly": monthly, "busiest": busiest, "quietest": quietest}


# ---------------------------------------------------------------------------
# STAGE 2.2 — Stay duration vs cancellation
# ---------------------------------------------------------------------------

def stage2_2(df: pd.DataFrame):
    section("STAGE 2.2 — IMPACT OF STAY DURATION ON CANCELLATION RATE")

    overall = utils.overall_cancellation_rate(df)
    print(overall.to_string(index=False))

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.barplot(
        data=overall, x="hotel", y="cancellation_rate",
        palette=HOTEL_PALETTE, ax=ax, hue="hotel", legend=False,
    )
    ax.set_title("Overall Cancellation Rate by Hotel Type", fontsize=14, fontweight="bold")
    ax.set_ylabel("Cancellation Rate (%)")
    ax.set_xlabel("")
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha="center", va="bottom", fontweight="bold")
    savefig(fig, "03_cancellation_rate_by_hotel.png")

    by_stay = utils.cancellation_rate_by(df, "stay_bucket")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.lineplot(
        data=by_stay, x="stay_bucket", y="cancellation_rate", hue="hotel",
        marker="o", palette=HOTEL_PALETTE, ax=ax,
    )
    ax.set_title("Cancellation Rate vs. Total Length of Stay", fontsize=14, fontweight="bold")
    ax.set_xlabel("Total Nights Booked")
    ax.set_ylabel("Cancellation Rate (%)")
    ax.legend(title="")
    savefig(fig, "04_cancellation_rate_by_stay_length.png")

    print(by_stay.to_string(index=False))
    return {"overall": overall, "by_stay": by_stay}


# ---------------------------------------------------------------------------
# STAGE 2.3 — Lead time vs cancellation
# ---------------------------------------------------------------------------

def stage2_3(df: pd.DataFrame):
    section("STAGE 2.3 — IMPACT OF LEAD TIME ON CANCELLATION RATE")

    by_lead = utils.cancellation_rate_by(df, "lead_time_bucket")
    print(by_lead.to_string(index=False))

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.lineplot(
        data=by_lead, x="lead_time_bucket", y="cancellation_rate", hue="hotel",
        marker="o", palette=HOTEL_PALETTE, ax=ax,
    )
    ax.set_title("Cancellation Rate vs. Lead Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Lead Time (days before arrival)")
    ax.set_ylabel("Cancellation Rate (%)")
    ax.legend(title="")
    savefig(fig, "05_cancellation_rate_by_lead_time.png")

    lowest = by_lead.loc[by_lead["cancellation_rate"].idxmin()]
    highest = by_lead.loc[by_lead["cancellation_rate"].idxmax()]
    print(f"\n  Lowest cancellation rate : {lowest['lead_time_bucket']} days "
          f"({lowest['hotel']}, {lowest['cancellation_rate']}%)")
    print(f"  Highest cancellation rate: {highest['lead_time_bucket']} days "
          f"({highest['hotel']}, {highest['cancellation_rate']}%)")
    return {"by_lead": by_lead}


# ---------------------------------------------------------------------------
# STAGE 3 — Summary & Recommendations
# ---------------------------------------------------------------------------

def stage3(df, r1, r2, r3):
    section("STAGE 3 — SUMMARY & RECOMMENDATIONS")

    top_hotel = r1["share"].iloc[0]["hotel"]
    top_pct = r1["share"].iloc[0]["pct"]
    overall_cancel = r2["overall"]
    higher_cancel_hotel = overall_cancel.loc[overall_cancel["cancellation_rate"].idxmax()]

    report = f"""# Hotel Business — Key Findings & Recommendations

## 1. Key Findings

- **Hotel type popularity:** {top_hotel} is booked most often, accounting for
  **{top_pct}%** of all bookings. Bookings peak around **{r1['busiest']}** and
  are quietest around **{r1['quietest']}**.
- **Stay duration & cancellations:** {higher_cancel_hotel['hotel']} has the
  higher overall cancellation rate at **{higher_cancel_hotel['cancellation_rate']}%**.
  Cancellation rate generally rises as the length of stay increases, especially
  for longer bookings, suggesting guests treat long stays as more provisional.
- **Lead time & cancellations:** Cancellation rate climbs steadily the further
  in advance a booking is made — bookings made **less than a week** out are
  cancelled far less often than bookings made **many months** ahead, which are
  more likely to be spontaneous placeholders or subject to changing plans.

## 2. Recommendations

1. **Grow the less-popular hotel type** with off-peak packages and bundle deals
   during its quiet months; **capitalise on peak season** for the more popular
   hotel type with dynamic (higher) pricing and early-bird incentives.
2. **Reduce revenue lost to long-stay cancellations** by introducing partial
   non-refundable deposits or tiered cancellation-fee policies that scale with
   stay length, and by offering discounted, better-protected rates for
   guests who commit to non-refundable long stays.
3. **Reduce far-ahead-booking cancellations** with automatic reminder emails
   as the stay approaches, a small non-refundable deposit for bookings made
   more than ~3 months in advance, and easy (fee-light) rescheduling instead
   of outright cancellation.
4. **Biggest-impact recommendation:** Introducing a modest deposit requirement
   for long-lead-time bookings (see Stage 2.3 chart) is likely to have the
   single largest impact, because that is where the cancellation rate is both
   highest and applies to the largest volume of advance bookings.

*(Charts referenced above are saved in the `charts/` folder:
01_hotel_type_share.png, 02_monthly_bookings_by_hotel.png,
03_cancellation_rate_by_hotel.png, 04_cancellation_rate_by_stay_length.png,
05_cancellation_rate_by_lead_time.png)*
"""
    with open("insights_report.md", "w") as f:
        f.write(report)
    print(report)
    print("  -> saved insights_report.md")


def main():
    stage0()
    df = stage1()
    r1 = stage2_1(df)
    r2 = stage2_2(df)
    r3 = stage2_3(df)
    stage3(df, r1, r2, r3)
    section("DONE")
    print("All charts saved in ./charts, cleaned data in ./data, "
          "summary in insights_report.md")


if __name__ == "__main__":
    main()
