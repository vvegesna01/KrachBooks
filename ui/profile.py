"""
ui/profile.py — User profile: stats, badges, reading pace chart, check-in history.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.gsheet_ops import get_data

from ._shared import CURATORS, THEME, load_badge_img, plot_layout, stat_card, section


def render_profile(user: str) -> None:
    section("🏅", f"{user}'s Profile")

    checkins_df = get_data("Checkins")
    user_clean  = user.strip().lower()

    if checkins_df.empty or "Name" not in checkins_df.columns:
        st.info("No check-in data yet.")
        return

    user_df = checkins_df[checkins_df["Name"].str.lower() == user_clean].copy()

    stats        = _compute_user_stats(user_df)
    all_member_avgs = _compute_all_member_avg_ratings(checkins_df)
    badges       = _compute_badges(user_clean, user_df, stats, all_member_avgs)

    # ── Stats row ─────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    avg_r = stats["avg_rating"]
    with c1: stat_card(stats["n_finished"],                       "Books Finished")
    with c2: stat_card(f"{stats['streak']} 🔥",                  "Current Streak")
    with c3: stat_card(f"{avg_r:.2f}⭐" if avg_r else "—",       "Your Avg Rating")

    st.markdown("<br>", unsafe_allow_html=True)

    _render_achievement_badges(user_clean, badges)
    _render_monthly_collection(user_df, checkins_df)
    _render_pace_chart(user_df)
    _render_checkin_history(user_df)


# ── Stats computation ─────────────────────────────────────────────────────────

def _compute_user_stats(user_df: pd.DataFrame) -> dict:
    """Return a dict of scalar stats for the current user."""
    n_finished = 0
    fastest    = 999.0
    ratings    = []
    streak     = 0

    if user_df.empty:
        return {"n_finished": 0, "fastest": fastest, "avg_rating": None, "streak": 0}

    if "Finished" in user_df.columns:
        n_finished = int((user_df["Finished"].str.lower() == "yes").sum())

    if "DaysToRead" in user_df.columns and "Finished" in user_df.columns:
        finished_reads = user_df[user_df["Finished"].str.strip().str.lower() == "yes"].copy()
        speeds = pd.to_numeric(finished_reads["DaysToRead"], errors="coerce").dropna()
        speeds = speeds[speeds > 0]
        if not speeds.empty:
            fastest = float(speeds.min())

    if "Rating" in user_df.columns:
        ratings = pd.to_numeric(user_df["Rating"].dropna(), errors="coerce").dropna().tolist()

    avg_rating = sum(ratings) / len(ratings) if ratings else None
    return {"n_finished": n_finished, "fastest": fastest, "avg_rating": avg_rating, "streak": streak}


def _compute_streak(user_df: pd.DataFrame, checkins_df: pd.DataFrame) -> int:
    """Count consecutive most-recent books where the user participated."""
    all_books_ordered = (
        checkins_df.sort_values("Timestamp")["BookTitle"].dropna().unique().tolist()
        if "Timestamp" in checkins_df.columns
        else checkins_df["BookTitle"].dropna().unique().tolist()
    )

    participated = set()
    if not user_df.empty and "Finished" in user_df.columns:
        active = user_df["Finished"].str.strip().str.lower().isin(["yes", "still reading"])
        participated = set(user_df[active]["BookTitle"].str.lower().tolist())

    streak = 0
    for book in reversed(all_books_ordered):
        if book.lower() in participated:
            streak += 1
        else:
            break
    return streak


def _compute_all_member_avg_ratings(checkins_df: pd.DataFrame) -> dict[str, float]:
    """Return {member_name_lower: avg_rating} for members with ≥2 ratings."""
    avgs = {}
    if checkins_df.empty or "Name" not in checkins_df.columns or "Rating" not in checkins_df.columns:
        return avgs
    for name, grp in checkins_df.groupby("Name"):
        rs = pd.to_numeric(grp["Rating"].dropna(), errors="coerce").dropna().tolist()
        if len(rs) >= 2:
            avgs[name.strip().lower()] = sum(rs) / len(rs)
    return avgs


# ── Badge computation ─────────────────────────────────────────────────────────

def _compute_badges(
    user_clean: str,
    user_df: pd.DataFrame,
    stats: dict,
    all_member_avgs: dict,
) -> list[tuple[str, str, bool]]:
    """Return list of (badge_id, label, earned) tuples."""

    # Iron Resolve — 90%+ completion rate
    completed  = len(user_df[user_df["Finished"].str.lower().eq("yes")]) if "Finished" in user_df.columns else 0
    attempted  = len(user_df[user_df["Finished"].str.lower().isin(["yes", "no", "dnf"])]) if "Finished" in user_df.columns else 0
    iron_resolve = (completed / attempted >= 0.90) if attempted > 0 else False

    # Wandering Bard — 5+ audiobooks finished
    audiobooks_finished = 0
    if "Format" in user_df.columns and "Finished" in user_df.columns:
        audiobooks_finished = int(
            (user_df["Format"].str.lower().eq("audiobook") & user_df["Finished"].str.lower().eq("yes")).sum()
        )

    # Philosopher — 7+ non-empty quotes
    quotes_submitted = 0
    if "Quote" in user_df.columns:
        valid = user_df["Quote"].fillna("").astype(str).str.strip()
        quotes_submitted = len(valid[~valid.str.lower().isin(["", "none", "n/a", "na", "-", "."])])

    lowest_rater  = min(all_member_avgs, key=all_member_avgs.get) if all_member_avgs else None
    highest_rater = max(all_member_avgs, key=all_member_avgs.get) if all_member_avgs else None

    return [
        ("curator",          "Trusted Curator",                  user_clean in {c.strip().lower() for c in CURATORS}),
        ("speed_dragon",     "Speed Dragon (< 3 days)",          stats["fastest"] < 3),
        ("loyalist",         "Loyal Krachhead (12+ books)",      stats["n_finished"] >= 12),
        ("bookworm",         "Bookworm (6+ books)",              stats["n_finished"] >= 6),
        ("iron_resolve",     "Iron Resolve (90%+ completion)",   iron_resolve),
        ("wandering_bard",   "Bard's Apprentice (5 audiobooks)", audiobooks_finished >= 5),
        ("philosopher",      "Philosopher (7+ quotes)",          quotes_submitted >= 7),
        ("harsh_critic",     "Harsh Critic",                     lowest_rater  is not None and user_clean == lowest_rater),
        ("golden_retriever", "Golden Retriever Reader",          highest_rater is not None and user_clean == highest_rater),
    ]


# ── Rendering helpers ─────────────────────────────────────────────────────────

def _badge_block(badge_id: str, label: str, earned: bool) -> None:
    img_html    = load_badge_img(badge_id, earned=earned, size=130)
    status_html = (
        '<span class="badge-status-earned">★ Earned!</span>'
        if earned else
        '<span class="badge-status-locked">🔒 Locked</span>'
    )
    st.markdown(
        f'<div class="badge-wrap">{img_html}'
        f'<div class="badge-label">{label}</div>'
        f'{status_html}</div>',
        unsafe_allow_html=True,
    )


def _render_achievement_badges(user_clean: str, badges: list) -> None:
    section("🏆", "Your Badges")
    BADGE_COLS = 3
    for row_start in range(0, len(badges), BADGE_COLS):
        batch = badges[row_start : row_start + BADGE_COLS]
        cols  = st.columns(BADGE_COLS)
        for ci, (badge_id, label, earned) in enumerate(batch):
            with cols[ci]:
                _badge_block(badge_id, label, earned)


def _render_monthly_collection(user_df: pd.DataFrame, checkins_df: pd.DataFrame) -> None:
    if checkins_df.empty or "BookTitle" not in checkins_df.columns:
        return

    all_books = checkins_df["BookTitle"].dropna().unique()
    finished_books = set()
    if not user_df.empty and "Finished" in user_df.columns:
        finished_books = set(
            user_df[user_df["Finished"].str.lower() == "yes"]["BookTitle"].str.lower().tolist()
        )

    section("📅", "Monthly Collection")
    month_badges = [
        (f"books/book_{i+1}", book, book.lower() in finished_books)
        for i, book in enumerate(all_books)
    ]

    for row_start in range(0, len(month_badges), 4):
        row_slice = month_badges[row_start : row_start + 4]
        cols      = st.columns(4)
        for ci, (badge_id, label, earned) in enumerate(row_slice):
            with cols[ci]:
                _badge_block(badge_id, label, earned)


def _render_pace_chart(user_df: pd.DataFrame) -> None:
    if user_df.empty or "DaysToRead" not in user_df.columns or "Finished" not in user_df.columns:
        return

    pace_df = user_df[user_df["Finished"].str.lower() == "yes"].copy()
    pace_df["DaysToRead"] = pd.to_numeric(pace_df["DaysToRead"], errors="coerce")
    pace_df = pace_df.dropna(subset=["DaysToRead", "BookTitle"])
    pace_df = pace_df[pace_df["DaysToRead"] > 0]

    if len(pace_df) < 2:
        return

    section("⚡", "Reading Pace")
    avg_days = pace_df["DaysToRead"].mean()

    # Colour bars by whether they're above/below the user's own average
    pace_df["Color"] = pace_df["DaysToRead"].apply(
        lambda d: THEME["palette"][2] if d <= avg_days else THEME["accent"]
    )
    if "Timestamp" in pace_df.columns:
        pace_df = pace_df.sort_values("Timestamp")

    fig = px.bar(
        pace_df, x="BookTitle", y="DaysToRead", text="DaysToRead",
        title="Days to finish each book",
        color="Color", color_discrete_map="identity",
    )
    fig.add_hline(
        y=avg_days, line_dash="dot", line_color=THEME["gold"],
        annotation_text=f"your avg · {avg_days:.0f}d",
        annotation_font_color=THEME["gold"],
        annotation_position="top left",
    )
    fig.update_traces(texttemplate="%{text}d", textposition="outside")
    fig.update_layout(**plot_layout(
        xaxis_title="",
        yaxis_title="Days",
        showlegend=False,
        yaxis=dict(gridcolor=THEME["grid"], color=THEME["muted"]),
    ))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        f'<p class="page-intro-sm" style="text-align:center">'
        f'<span style="color:{THEME["palette"][2]}">■</span> faster than your avg &nbsp;'
        f'<span style="color:{THEME["accent"]}">■</span> slower than your avg</p>',
        unsafe_allow_html=True,
    )


def _render_checkin_history(user_df: pd.DataFrame) -> None:
    if user_df.empty:
        return
    section("📖", "Your Check-ins")
    show_cols = [c for c in ["BookTitle", "Finished", "DaysToRead", "Format", "Rating", "Timestamp"] if c in user_df.columns]
    st.dataframe(user_df[show_cols], use_container_width=True, hide_index=True)