"""
ui/archive.py — Past nominations archive, grouped by month.

Reads from the Nominations sheet. Requires a `Status` column with values:
  "Nominated"  — voting still open / current month
  "Won"        — this book was picked for that month
  "Passed"     — nominated but not selected

Your close_voting() in gsheet_ops.py should write:
  - "Won"    on the winner row
  - "Passed" on all other rows for that month
"""
from __future__ import annotations

import streamlit as st

from utils.book_api import get_book_info
from utils.gsheet_ops import get_data

from ._shared import section


def render_archive(config: dict) -> None:
    section("📖", "Past Nominations")
    st.markdown(
        '<p class="page-intro-sm">Every book the club has considered — winners and runners-up alike.</p>',
        unsafe_allow_html=True,
    )

    noms_df = get_data("Nominations")

    if noms_df.empty or "BookTitle" not in noms_df.columns:
        st.info("Nothing here yet — past nominations will appear once a voting round closes.")
        return

    required_cols = {"Month", "Status"}
    if not required_cols.issubset(noms_df.columns):
        st.warning("Nominations sheet is missing `Month` or `Status` columns.")
        return

    current_month = config.get("current_month", "").strip()

    # Only show months that have at least one resolved nomination
    resolved = noms_df[noms_df["Status"].isin(["Won", "Passed"])]

    if resolved.empty:
        st.info("No past rounds yet. Archive updates once the curator closes voting for a month.")
        return

    # Also include current month's losers if voting has closed and results exist
    voting_open = config.get("voting_open", "False").lower() == "true"
    if not voting_open and current_month:
        current_resolved = noms_df[
            (noms_df["Month"].str.strip() == current_month) &
            (noms_df["Status"].isin(["Won", "Passed"]))
        ]
        resolved = noms_df[noms_df["Status"].isin(["Won", "Passed"])]
    
    # Sort months — most recent first
    # Assumes "Month YYYY" format (e.g. "June 2026"); falls back to string sort
    months_in_order = (
        resolved["Month"]
        .str.strip()
        .drop_duplicates()
        .sort_values(ascending=False)
        .tolist()
    )

    for month in months_in_order:
        is_current = month == current_month
        label      = f"{month} {'(current)' if is_current else ''}"

        month_df = resolved[resolved["Month"].str.strip() == month]
        winner   = month_df[month_df["Status"] == "Won"]
        runners  = month_df[month_df["Status"] == "Passed"]

        with st.expander(label, expanded=is_current):
            # ── Winner ────────────────────────────────────────────────────────
            if not winner.empty:
                row  = winner.iloc[0]
                meta = get_book_info(row["BookTitle"])
                st.markdown("##### 🏆 Selected")
                _book_card(row, meta, highlight=True)
            
            # ── Runners-up ────────────────────────────────────────────────────
            if not runners.empty:
                st.markdown("##### Not picked this round")
                for _, row in runners.iterrows():
                    meta = get_book_info(row["BookTitle"])
                    _book_card(row, meta, highlight=False)


# ── Private helpers ───────────────────────────────────────────────────────────

def _book_card(row, meta: dict | None, highlight: bool) -> None:
    """Render one nomination row as a horizontal card."""
    border_style = (
        "border-left: 3px solid var(--accent-color, #8FA88A); padding-left: 0.75rem;"
        if highlight else
        "border-left: 3px solid transparent; padding-left: 0.75rem; opacity: 0.75;"
    )

    c1, c2 = st.columns([1, 6])
    with c1:
        if meta and meta.get("cover_url"):
            st.image(meta["cover_url"], width=60)

    with c2:
        author      = row.get("Author", "")
        genre       = row.get("Genre", "")
        length      = row.get("LengthPages", "")
        difficulty  = row.get("Difficulty", "")
        nominated_by = row.get("NominatedBy", "")
        description = row.get("Description", "")
        why         = row.get("WhyNominated", "")

        meta_parts = [p for p in [genre, f"{length} pages" if length else None, difficulty] if p]

        st.markdown(
            f'<div style="{border_style}">'
            f'<strong>{row["BookTitle"]}</strong>'
            + (f" <span style='opacity:0.6; font-size:0.85em'>by {author}</span>" if author else "")
            + (f"<br><small>{' · '.join(meta_parts)}</small>" if meta_parts else "")
            + (f"<br><small style='opacity:0.55'>nominated by {nominated_by}</small>" if nominated_by else "")
            + "</div>",
            unsafe_allow_html=True,
        )

        if description or why:
            with st.expander("Details"):
                if description:
                    st.markdown(description)
                if why:
                    st.markdown(f"**Why nominated:** {why}")

    st.markdown("<div style='margin-bottom: 0.5rem'></div>", unsafe_allow_html=True)