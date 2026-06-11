"""
ui/curator.py — Curator control panel: nominations, voting management, config.
"""
from __future__ import annotations

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

    month        = config.get("current_month", "")
    voting_open  = config.get("voting_open", "False").lower() == "true"

    _step_card("01", "📚", "Add Book Nominations",
               "Add 2–3 books for the club to vote on. Covers are fetched automatically.")
    with st.expander("📚 Step 1 — Add Book Nominations", expanded=True):
        _nominations_step(user, month)

    _step_card("02", "🗳️", "Manage Voting",
               "Open voting for members, watch the live tally, then close to pick the winner automatically.")
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
    with st.form("nom_form"):
        st.markdown("Add 2–3 books for the club to vote on.")
        nom_title = st.text_input("Book Title")
        submitted = st.form_submit_button("➕ Add Nomination")

    if submitted and nom_title:
        try:
            add_nomination(month, nom_title, user)
            st.success(f"Added **{nom_title}**!")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    noms_df = get_data("Nominations")
    if not noms_df.empty and "Month" in noms_df.columns:
        this_month = noms_df[noms_df["Month"].str.strip() == month.strip()]
        if not this_month.empty:
            st.markdown("**Current nominations:**")
            for _, row in this_month.iterrows():
                meta = get_book_info(row["BookTitle"])
                c1, c2 = st.columns([1, 5])
                with c1:
                    if meta and meta["cover_url"]:
                        st.image(meta["cover_url"], width=60)
                with c2:
                    st.markdown(f"**{row['BookTitle']}**")


def _voting_step(month: str, voting_open: bool) -> None:
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
        if voting_open and st.button("🔒 Close Voting & Pick Winner", use_container_width=True, type="primary"):
            votes_df = get_data("Votes")
            if not votes_df.empty and "BookTitle" in votes_df.columns and "Month" in votes_df.columns:
                month_votes = votes_df[votes_df["Month"].str.strip() == month.strip()]
                if not month_votes.empty:
                    winner = month_votes["BookTitle"].value_counts().idxmax()
                    try:
                        close_voting(winner, month)
                        st.success(f"🎉 Winner: **{winner}**! Voting closed.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("No votes recorded yet!")
            else:
                st.warning("No votes data found.")

    # Live tally chart
    votes_df = get_data("Votes")
    if not votes_df.empty and "BookTitle" in votes_df.columns and "Month" in votes_df.columns:
        month_votes = votes_df[votes_df["Month"].str.strip() == month.strip()]
        if not month_votes.empty:
            tally         = month_votes["BookTitle"].value_counts().reset_index()
            tally.columns = ["Book", "Votes"]
            st.markdown("**Live tally:**")
            fig = px.bar(
                tally, x="Book", y="Votes", text="Votes",
                color_discrete_sequence=[THEME["accent"]],
                title="Current Votes",
            )
            fig.update_layout(**plot_layout())
            st.plotly_chart(fig, use_container_width=True)


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