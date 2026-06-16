# ui/archive.py — Past nominations archive, grouped chronologically by month.

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.book_api import get_book_info
from utils.gsheet_ops import get_data
from ._shared import section


def render_archive(config: dict | None = None) -> None:
    section("📖", "Past Nominations")
    st.write("Every book the club has considered — winners and all honorable nominees")
    st.markdown("<br>", unsafe_allow_html=True)

    if config is None:
        config = {}

    noms_df = get_data("Nominations")

    if noms_df.empty or "BookTitle" not in noms_df.columns:
        st.info("Nothing here yet — past nominations will appear once a voting round closes.")
        return

    required_cols = {"Month", "Status"}
    if not required_cols.issubset(noms_df.columns):
        st.warning("Nominations sheet is missing `Month` or `Status` columns.")
        return

    current_month = config.get("current_month", "").strip()

    # Filter to only show resolved nominations
    resolved = noms_df[noms_df["Status"].isin(["Won", "Passed"])]

    if resolved.empty:
        st.info("No past rounds yet. Archive updates once the curator closes voting for a month.")
        return
    
    # ── Chronological Sorting Block ───────────────────────────────────────────
    unique_months = resolved["Month"].str.strip().drop_duplicates()
    
    # Create a temporary dataframe pairing the strings with parseable datetimes
    sort_df = pd.DataFrame({
        "MonthStr": unique_months,
        "MonthDate": pd.to_datetime(unique_months, errors='coerce')
    })
    
    # Sort by the actual date (ascending=False puts the newest months at the top)
    months_in_order = (
        sort_df.sort_values(by="MonthDate", ascending=False, na_position="last")
        ["MonthStr"]
        .tolist()
    )

    for month in months_in_order:
        is_current = month == current_month
        label = f" {month} {'(Current Month)' if is_current else ''}"

        month_df = resolved[resolved["Month"].str.strip() == month]
        winner = month_df[month_df["Status"] == "Won"]
        runners = month_df[month_df["Status"] == "Passed"]

        with st.expander(label, expanded=is_current):
            
            # ── The Winner ────────────────────────────────────────────────────
            if not winner.empty:
                w_row = winner.iloc[0]
                w_title = w_row["BookTitle"]
                w_author = w_row.get("Author", "Unknown Author")
                meta = get_book_info(w_title)
                st.markdown(f"### Winner: {w_title} - {w_author}")
            
            # ── The Runners-Up ────────────────────────────────────────────────
            if not runners.empty:
                if not winner.empty:
                    st.divider()
                    
                st.markdown("##### Also Nominated")
                
                for _, r_row in runners.iterrows():
                    r_title = r_row["BookTitle"]
                    r_author = r_row.get("Author", "")
                    
                    author_text = f" — *by {r_author}*" if pd.notna(r_author) and r_author else ""
                    st.markdown(f"• **{r_title}**{author_text}")