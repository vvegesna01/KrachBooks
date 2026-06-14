"""
ui/forms.py — Monthly check-in form and voting form.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.book_api import get_book_info
from utils.gsheet_ops import get_data, append_row, upsert_checkin, upsert_vote

from ._shared import section


def render_checkin_form(user: str, config: dict) -> None:
    current_book = config.get("current_book", "")
    section("✏️", f"Monthly Check-in — {current_book}")

    checkins_df = get_data("Checkins")

    existing = pd.DataFrame()
    if not checkins_df.empty and "Name" in checkins_df.columns:
        mask = (checkins_df["Name"].str.lower() == user.lower()) & (
            checkins_df.get("BookTitle", pd.Series(dtype=str)).str.lower() == current_book.lower()
        )
        existing = checkins_df[mask]

    def _get(col, default):
        if not existing.empty and col in existing.columns:
            val = existing.iloc[0][col]
            return val if pd.notna(val) else default
        return default

    if not existing.empty:
        st.info("✅ You've already checked in for this book. Your previous answers are pre-filled — submit again to update.")

    with st.form("checkin_form", clear_on_submit=False):
        finished_opts = ["Yes", "No", "Still Reading", "DNF"]
        finished_def  = finished_opts.index(_get("Finished", "Still Reading")) if _get("Finished", "Still Reading") in finished_opts else 2
        finished      = st.selectbox("Did you finish?", finished_opts, index=finished_def)

        days = st.number_input(
            "Days to read (0 if not done)",
            min_value=0, max_value=365,
            value=int(_get("DaysToRead", 0) or 0),
        )

        fmt_opts = ["Kindle/eBook", "Audiobook", "Hardcopy"]
        fmt_def  = fmt_opts.index(_get("Format", "Kindle/eBook")) if _get("Format", "Kindle/eBook") in fmt_opts else 0
        fmt      = st.selectbox("Format", fmt_opts, index=fmt_def)

        rating = st.number_input(
            "Rating (1–5 ⭐)",
            min_value=1.0, max_value=5.0, step=0.25,
            value=round(float(_get("Rating", 3.0) or 3.0) * 4) / 4,
        )

        quote    = st.text_area("Review or favourite quotes ", value=_get("Quote", ""),    height=100)
        feedback = st.text_area("General thoughts / feedback", value=_get("Feedback", ""), height=100)

        submitted = st.form_submit_button("💾 Submit Check-in", use_container_width=True)

    if submitted:
        from datetime import datetime
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            current_book, user, finished, days, fmt, rating, quote, feedback,
        ]
        try:
            upsert_checkin(user, current_book, row)
            st.success("Check-in saved! 🎉")
            st.balloons()
        except Exception as e:
            st.error(f"Couldn't save: {e}")


def render_voting_form(user: str, config: dict) -> None:
    month = config.get("current_month", "This Month")
    section("🗳️", "Vote for Next Month's Book")

    noms_df = get_data("Nominations")
    if noms_df.empty or "BookTitle" not in noms_df.columns:
        st.info("No nominations yet. Ask your curator to add some!")
        return

    if "Month" in noms_df.columns:
        noms_df = noms_df[noms_df["Month"].str.strip() == month.strip()]

    books = noms_df["BookTitle"].dropna().tolist()
    if not books:
        st.info("No nominations for this month yet.")
        return

    # Pre-fill with existing vote if any
    votes_df  = get_data("Votes")
    user_vote = None
    if not votes_df.empty and "VotedBy" in votes_df.columns and "Month" in votes_df.columns:
        mask = (votes_df["VotedBy"].str.lower() == user.lower()) & (
            votes_df["Month"].str.strip() == month.strip()
        )
        if votes_df[mask].shape[0] > 0:
            user_vote = votes_df[mask].iloc[0].get("BookTitle", None)

    if user_vote:
        st.success(f"✅ You voted for **{user_vote}** — you can change your vote below.")

    st.markdown("<br>", unsafe_allow_html=True)
    COLS = min(len(books), 4)
    cols = st.columns(COLS)
    for i, book in enumerate(books):
        meta = get_book_info(book)
        with cols[i % COLS]:
            if meta and meta["cover_url"]:
                st.image(meta["cover_url"], width=130)
            nominated_by = noms_df[noms_df["BookTitle"] == book]["NominatedBy"].values
            nominated_by = nominated_by[0] if len(nominated_by) > 0 else "—"
            st.markdown(
                f'<div class="nom-card"><strong>{book}</strong><br>'
                f'<small>nominated by {nominated_by}</small></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("vote_form"):
        choice    = st.radio("Your vote:", books, index=books.index(user_vote) if user_vote in books else 0)
        submitted = st.form_submit_button("🗳️ Cast Vote", use_container_width=True)

    if submitted:
        try:
            upsert_vote(user, month, choice)
            st.success(f"Voted for **{choice}**! 🎉")
            st.rerun()
        except Exception as e:
            st.error(f"Couldn't save vote: {e}")