# ui/forms.py — Monthly check-in form and ranked-choice voting form.

# Votes sheet columns (in order):
#     Timestamp | Month | BookTitle | VotedBy | Rank1 | Rank2 | Rank3

#   BookTitle = denormalised copy of Rank1 (voter's top pick).
#   Lets you query by book title OR by month without pivoting.

from __future__ import annotations

import pandas as pd
import streamlit as st
from utils.book_api import get_book_info
from utils.gsheet_ops import get_data, upsert_checkin, upsert_vote

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
        st.success("✅ **You've already checked in!** Your previous answers are pre-filled below. Feel free to update them.")

    with st.form("checkin_form", clear_on_submit=False):
        st.subheader("Reading Status")
        
        # Use horizontal radio buttons instead of a selectbox for faster clicking
        finished_opts = ["Yes", "Didn't Start", "Still Reading", "DNF"]
        finished_def = finished_opts.index(_get("Finished", "Still Reading")) if _get("Finished", "Still Reading") in finished_opts else 2
        finished = st.radio("Did you finish the book?", finished_opts, index=finished_def, horizontal=True)

        st.divider()
        st.subheader("More Stats")
        
        # Group inputs into columns for a more compact, dashboard-like feel
        
        days = st.number_input(
            "Days to read (0 if not done)",
            min_value=0, max_value=365,
            value=int(_get("DaysToRead", 0) or 0),
        )
        fmt_opts = ["Kindle/eBook", "Audiobook", "Hardcopy"]
        fmt_def = fmt_opts.index(_get("Format", "Kindle/eBook")) if _get("Format", "Kindle/eBook") in fmt_opts else 0
        fmt = st.selectbox("Reading Format", fmt_opts, index=fmt_def)

        # Sliders are visually much nicer for 1-5 star ratings
        rating = st.slider(
            "Your Rating (1–5 ⭐)",
            min_value=1.0, max_value=5.0, step=0.25,
            value=round(float(_get("Rating", 3.0) or 3.0) * 4) / 4,
            format="%f"
        )

        st.divider()
        st.subheader("Your Thoughts")
        quote = st.text_area("✍️ Review or favourite quotes", value=_get("Quote", ""), height=100)
        feedback = st.text_area("💭 General thoughts / feedback", value=_get("Feedback", ""), height=100)

        # Adding some space before the button
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾 Save Check-in", use_container_width=True)

    if submitted:
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            current_book, user, finished, days, fmt, rating, quote, feedback,
        ]
        try:
            upsert_checkin(user, current_book, row)
            st.toast("Check-in saved successfully!", icon="🎉")
            st.balloons()
        except Exception as e:
            st.error(f"Couldn't save: {e}")


def render_voting_form(user: str, config: dict) -> None:
    """
    Ranked-choice voting form. Members rank all nominated books 1st → 3rd.

    Pre-fills from existing ballot if the user has already voted this month.
    Validation blocks submission if any rank is empty or if the same book
    appears more than once.
    """
    month = config.get("current_month", "This Month")
    section("🗳️", "Vote for Next Month's Book")

    noms_df = get_data("Nominations")
    if noms_df.empty or "BookTitle" not in noms_df.columns:
        st.info("No nominations yet. Ask your curator to add some!")
        return

    if "Month" in noms_df.columns:
        noms_df = noms_df[noms_df["Month"].str.strip() == month.strip()]

    # Only show books still in play (not yet resolved from a prior round)
    if "Status" in noms_df.columns:
        noms_df = noms_df[noms_df["Status"].isin(["Nominated", ""])]

    books = noms_df["BookTitle"].dropna().tolist()
    if not books:
        st.info("No nominations for this month yet.")
        return

# ── Nomination cards (Wide List Layout) ───────────────────────────────────
    st.markdown("### The Nominees")
    st.write("Review this month's choices below before casting your ballot.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    for book in books:
        meta = get_book_info(book)
        book_row = noms_df[noms_df["BookTitle"] == book].iloc[0]
        
        with st.container(border=True):
            # Horizontal split: 1 part for the image, 4 parts for the text
            img_col, text_col = st.columns([1, 4], gap="medium")
            
            with img_col:
                if meta and meta.get("cover_url"):
                    st.image(meta["cover_url"], use_container_width=True)
                else:
                    st.caption("*(No cover available)*")
                    
            with text_col:
                st.subheader(book, anchor=False)
                
                # Match the "Nominated by" styling for the author
                author = book_row.get("Author", "Unknown Author")
                st.caption(f"By {author}")
                
                # Emoji-led visual metadata
                length = book_row.get("LengthPages", "")
                genre = book_row.get("Genre", "")
                diff = book_row.get("Difficulty", "")
                
                meta_parts = []
                if genre:
                    meta_parts.append(f"🎭 {genre}")
                if length:
                    meta_parts.append(f"📖 {length} pages")
                if diff:
                    meta_parts.append(f"🖊️ {diff}")
                
                if meta_parts:
                    st.markdown(" &nbsp;•&nbsp; ".join(meta_parts))
                
                # Show the description directly
                description = book_row.get("Description", "")
                if description:
                    st.write("")
                    st.markdown(description)
                
                # Highlight why it was nominated
                why = book_row.get("WhyNominated", "")
                if why:
                    st.info(f"**Why I'm drawn to this book:** {why}")
                    
                st.caption(f"*Nominated by {book_row.get('NominatedBy', '—')}*")

    # ── Pre-fill from existing ballot ────

    votes_df   = get_data("Votes")
    prior_vote = {"Rank1": None, "Rank2": None, "Rank3": None}

    if not votes_df.empty and "VotedBy" in votes_df.columns and "Month" in votes_df.columns:
        mask = (
            (votes_df["VotedBy"].str.lower() == user.lower()) &
            (votes_df["Month"].str.strip() == month.strip())
        )
        if votes_df[mask].shape[0] > 0:
            existing_row = votes_df[mask].iloc[0]
            for rank in ["Rank1", "Rank2", "Rank3"]:
                val = existing_row.get(rank)
                if pd.notna(val) and val in books:
                    prior_vote[rank] = val
            st.success(
                f"✅ You've already voted — "
                f"1st: **{prior_vote['Rank1']}**, "
                f"2nd: **{prior_vote['Rank2']}**, "
                f"3rd: **{prior_vote['Rank3']}**. "
                "Submit again to update."
            )

# ── Ballot ────────────────────────────────────────────────────────────────
    st.markdown("### Cast Your Ballot")
    st.caption("Rank your top choices. 1st place gets the most weight!")

    PLACEHOLDER = "— pick a book —"
    options = [PLACEHOLDER] + books

    def _default_idx(rank_key: str) -> int:
        val = prior_vote[rank_key]
        return options.index(val) if val and val in options else 0

    with st.form("vote_form"):
        # Put the rankings side-by-side to save vertical space
        rank_col1, rank_col2, rank_col3 = st.columns(3)
        
        with rank_col1:
            rank1 = st.selectbox("🥇 1st choice", options, index=_default_idx("Rank1"))
        with rank_col2:
            rank2 = st.selectbox("🥈 2nd choice", options, index=_default_idx("Rank2"))
        with rank_col3:
            rank3 = st.selectbox("🥉 3rd choice", options, index=_default_idx("Rank3"))

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🗳️ Cast Vote", type="primary", use_container_width=True)

    if submitted:
        st.balloons()
        chosen = [r for r in [rank1, rank2, rank3] if r != PLACEHOLDER]
        
        # Fixed logic: User only needs to provide up to 3 ranks, even if there are 10 nominations
        required_ranks = min(3, len(books))

        if len(chosen) < required_ranks:
            st.error(f"Please rank your top {required_ranks} books before submitting.")
        elif len(set(chosen)) < len(chosen):
            st.error("You selected the same book twice! Each book can only appear once in your ranking.")
        else:
            try:
                upsert_vote(user, month, rank1, rank1, rank2, rank3)
                st.toast("Vote recorded!", icon="✅")
                st.success(f"Vote recorded — 1st: **{rank1}**, 2nd: **{rank2}**, 3rd: **{rank3}** 🎉")
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't save vote: {e}")