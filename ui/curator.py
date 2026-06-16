"""
ui/curator.py — Curator control panel: nominations, voting management, config.

Nominations sheet columns (in order):
    Month | BookTitle | Author | Genre | LengthPages | Difficulty
    | Description | WhyNominated | NominatedBy | Status

Votes sheet columns (in order):
    Timestamp | Month | BookTitle | VotedBy | Rank1 | Rank2 | Rank3

  BookTitle in Votes = the voter's 1st-choice book (denormalised copy of Rank1),
  stored so you can query "who wanted this book?" without pivoting.

  Status in Nominations: "Nominated" → "Won" / "Passed" when curator closes voting.
  Your close_voting() should write "Won" to the winner row and "Passed" to the rest.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.book_api import get_book_info
from utils.gsheet_ops import (
    get_data, add_nomination, close_voting, update_config,
)

from ._shared import THEME, plot_layout, section


def render_curator_panel(user: str, config: dict) -> None:
    section("✨", "Curator Panel")
    st.markdown(
        '<p class="page-intro-sm">You\'re the curator this month — here\'s your control panel.</p>',
        unsafe_allow_html=True,
    )

    month       = config.get("current_month", "")
    voting_open = config.get("voting_open", "False").lower() == "true"

    _step_card("01", "📚", "Add Book Nominations",
               "Add 2–3 books for the club to vote on. Fill in the details — members will see everything when they cast their ranked ballot.")
    with st.expander("📚 Step 1 — Add Book Nominations", expanded=True):
        _nominations_step(user, month)

    _step_card("02", "🗳️", "Manage Voting",
               "Open ranked-choice voting for members, watch the live tally, then close when everyone has voted.")
    with st.expander("🗳️ Step 2 — Manage Voting", expanded=True):
        _voting_step(month, voting_open)

    _step_card("03", "⚙️", "Update Config",
               "Set the current month and hand off the curator role to whoever is up next.")
    with st.expander("⚙️ Step 3 — Update Config"):
        _config_step(config, month)


# ── Private helpers ───────────────────────────────────────────────────────────

def _step_card(num: str, icon: str, title: str, body: str) -> None:
    st.markdown(
        f'<div class="curator-step-card">'
        f'<div class="curator-step-number-col"><span class="curator-step-big-num">{num}</span></div>'
        f'<div class="curator-step-content">'
        f'<div class="curator-step-title"><span>{icon}</span> {title}</div>'
        f'<div class="curator-step-body">{body}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _nominations_step(user: str, month: str) -> None:
    """Nomination form with full metadata fields matching the book club template."""
    with st.form("nom_form"):
        st.markdown("Fill in the details below — members will see all of this when they vote.")

        col1, col2 = st.columns(2)
        with col1:
            nom_title  = st.text_input("Book Title *")
            nom_author = st.text_input("Author *")
            nom_genre  = st.text_input("Genre (e.g. Mystery / Literary Fiction)")
        with col2:
            nom_length     = st.number_input("Length (pages)", min_value=0, step=1, value=0)
            nom_difficulty = st.selectbox("Difficulty", ["Easy", "Moderate", "Challenging"])

        nom_description = st.text_area(
            "Book description",
            height=120,
            placeholder="A brief plot summary or what the book is about...",
        )
        nom_why = st.text_area(
            "Why are you nominating this?",
            height=100,
            placeholder="What drew you to this book? Why would the club enjoy it?",
        )

        submitted = st.form_submit_button("➕ Add Nomination")

    if submitted:
        if not nom_title or not nom_author:
            st.error("Title and author are required.")
        else:
            try:
                add_nomination(
                    month, nom_title, user,
                    author=nom_author,
                    genre=nom_genre,
                    length_pages=nom_length if nom_length > 0 else None,
                    difficulty=nom_difficulty,
                    description=nom_description,
                    why_nominated=nom_why,
                )
                st.success(f"Added **{nom_title}**!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    # Show current nominations for this month
    noms_df = get_data("Nominations")
    if not noms_df.empty and "Month" in noms_df.columns:
        this_month = noms_df[noms_df["Month"].str.strip() == month.strip()]
        if not this_month.empty:
            st.markdown("---")
            st.markdown(f"**Nominations for {month}** ({len(this_month)} so far)")
            for _, row in this_month.iterrows():
                meta = get_book_info(row["BookTitle"])
                c1, c2 = st.columns([1, 6])
                with c1:
                    if meta and meta.get("cover_url"):
                        st.image(meta["cover_url"], width=60)
                with c2:
                    length     = row.get("LengthPages", "")
                    meta_parts = [p for p in [
                        row.get("Author"), row.get("Genre"),
                        f"{length} pages" if length else None,
                        row.get("Difficulty"),
                    ] if p]
                    st.markdown(f"**{row['BookTitle']}**  \n{' · '.join(meta_parts)}")


def _voting_step(month: str, voting_open: bool) -> None:
    """Voting management: open/close controls + ranked-choice tally view."""
    status_label = "🟢 Voting is OPEN" if voting_open else "🔴 Voting is CLOSED"
    st.markdown(f"**Status:** {status_label}")

    col1, col2 = st.columns(2)
    with col1:
        if not voting_open and st.button("Open Voting", use_container_width=True):
            try:
                update_config("voting_open", "True")
                st.success("Voting opened!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    with col2:
        if voting_open and st.button("🔒 Close Voting", use_container_width=True, type="primary"):
            try:
                update_config("voting_open", "False")
                st.success("Voting closed. Review the tally below and declare a winner.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    # ── Ranked-choice tally ───────────────────────────────────────────────────
    votes_df = get_data("Votes")
    if votes_df.empty or "VotedBy" not in votes_df.columns:
        st.info("No votes yet.")
        return

    if "Month" in votes_df.columns:
        votes_df = votes_df[votes_df["Month"].str.strip() == month.strip()]

    if votes_df.empty:
        st.info("No votes for this month yet.")
        return

    st.markdown(f"**{len(votes_df)} ballot(s) submitted**")

    # Count how many times each book appears in each rank position
    rank_cols = ["Rank1", "Rank2", "Rank3"]
    present   = [c for c in rank_cols if c in votes_df.columns]
    all_books = pd.concat([votes_df[c].dropna() for c in present]).unique()

    tally_rows = []
    for book in all_books:
        row = {"Book": book}
        for i, col in enumerate(present, start=1):
            row[f"#{i}"] = int((votes_df[col] == book).sum())
        tally_rows.append(row)

    tally_df = pd.DataFrame(tally_rows).sort_values("#1", ascending=False)

    st.markdown("**Ranked-choice tally:**")
    st.dataframe(tally_df.set_index("Book"), use_container_width=True)

    melted = tally_df.melt(id_vars="Book", var_name="Rank", value_name="Votes")
    fig = px.bar(
        melted, x="Book", y="Votes", color="Rank", text="Votes",
        color_discrete_sequence=[
            THEME["accent"],
            THEME.get("accent2", "#8FA88A"),
            THEME.get("muted", "#C5B99A"),
        ],
        barmode="group",
        title="Votes by rank",
    )
    fig.update_layout(**plot_layout())
    st.plotly_chart(fig, use_container_width=True)

    # Manual winner declaration — curator decides based on tally
    st.markdown("---")
    st.markdown("**Declare winner** — pick the book to record:")
    book_options = tally_df["Book"].tolist()
    winner_pick  = st.selectbox("Winner", book_options, label_visibility="collapsed")
    if st.button("🏆 Set as Winner & Record", use_container_width=True):
        try:
            # close_voting should write "Won" to winner row, "Passed" to all others
            close_voting(winner_pick, month)
            st.success(f"🎉 **{winner_pick}** recorded as winner!")
            st.rerun()
        except Exception as e:
            st.error(str(e))


def _config_step(config: dict, month: str) -> None:
    with st.form("config_form"):
        new_month   = st.text_input("Current Month (e.g. June 2026)", value=month)
        new_curator = st.text_input("Next Curator's Name", value=config.get("current_curator", ""))
        save_cfg    = st.form_submit_button("💾 Save Config")

    if save_cfg:
        try:
            update_config("current_month", new_month)
            update_config("current_curator", new_curator)
            st.success("Config updated!")
            st.rerun()
        except Exception as e:
            st.error(str(e))