import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path

import base64
import re
from data_parser import load_months, match_col, COL_PATTERNS

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KrachBooks",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# LOAD CSS
# ──────────────────────────────────────────────────────────────────────────────
def load_css(path="styles.css"):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

# ──────────────────────────────────────────────────────────────────────────────
# THEME
# ──────────────────────────────────────────────────────────────────────────────
THEME = {
    "bg": "#160F29",            # Midnight Violet
    "paper": "#1E1636",
    "card": "#246A73",         # Stormy Teal
    "accent": "#368F8B",       # Dark Cyan
    "text": "#F3DFC1",         # Champagne Mist
    "muted": "#DDBEA8",        # Desert Sand
    "grid": "rgba(54, 143, 139, 0.18)",
    "palette": [
        "#368F8B",
        "#246A73",
        "#DDBEA8",
        "#F3DFC1",
        "#5B4B8A",
    ],
    "bar_scale": ["#246A73", "#368F8B"],
}


def plot_layout(**extra):
    base = dict(
        plot_bgcolor=THEME["bg"],
        paper_bgcolor=THEME["paper"],
        font=dict(
            family="Inter, sans-serif",
            color=THEME["text"],
            size=13,
        ),
        title_font=dict(
            family="Fraunces, serif",
            color=THEME["text"],
            size=20,
        ),
        xaxis=dict(
            gridcolor=THEME["grid"],
            color=THEME["accent"],
            linecolor=THEME["grid"],
        ),
        yaxis=dict(
            gridcolor=THEME["grid"],
            color=THEME["accent"],
            linecolor=THEME["grid"],
        ),
        legend=dict(
            bgcolor=THEME["paper"],
            font=dict(color=THEME["text"]),
        ),
        margin=dict(t=60, l=40, r=40, b=40),
    )

    base.update(extra)
    return base


# ──────────────────────────────────────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────────────────────────────────────
ASSETS_DIR = Path(__file__).parent / "assets"
DATA_DIR = Path(__file__).parent / "data"


# ──────────────────────────────────────────────────────────────────────────────
# BADGE LOADER
# ──────────────────────────────────────────────────────────────────────────────
def load_badge(badge_id, earned=True, size=140, shape="circle"):
    for ext, mime in [
        ("svg", "image/svg+xml"),
        ("png", "image/png"),
    ]:
        p = ASSETS_DIR / f"{badge_id}.{ext}"

        if p.exists():
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()

            css_main = (
                "badge-img-earned"
                if earned
                else "badge-img-locked"
            )

            if shape == "square":
                css_main += " img-square"

            return (
                f'<img src="data:{mime};base64,{b64}" '
                f'width="{size}" class="{css_main}"/>'
            )

    icon_name = "stars" if earned else "lock"

    return f"""
    <div class="badge-placeholder">
        <span class="material-icons">{icon_name}</span>
    </div>
    """


# ──────────────────────────────────────────────────────────────────────────────
# SESSION
# ──────────────────────────────────────────────────────────────────────────────
st.session_state.months = load_months()

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────────
# MAIN HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="main-header">📚 KrachBooks</div>
    <div class="sub-header">
        some krached stats, and badges
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.months:
    st.warning("No CSV files found in /data")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "Dashboard",
    "Books",
    "Quotes",
    "My Badges",
    "Info",
])

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown(
        """
        <div class="section-title">
            <span class="material-icons">
                leaderboard
            </span>
            Club Overview
        </div>
        """,
        unsafe_allow_html=True,
    )

    rows = []

    for month, data in st.session_state.months.items():
        df = data["df"]

        n_total = len(df)
        n_finished = int(df["_finished"].sum())

        avg_rating = df["_rating"].dropna().mean()

        rows.append({
            "Month": month,
            "Book": data["book"],
            "Author": data.get("author", "Unknown"),
            "Active Members": n_total,
            "Finished": n_finished,
            "% Finished": (
                round(n_finished / n_total * 100, 1)
                if n_total > 0
                else 0
            ),
            "Avg Rating": (
                round(avg_rating, 2)
                if not pd.isna(avg_rating)
                else None
            ),
        })

    summary = pd.DataFrame(rows)

    total_active = 17
    overall_avg = summary["Avg Rating"].dropna().mean()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">
                    {len(summary)}
                </div>
                <div class="stat-label">
                    Months Active
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">
                    {total_active}
                </div>
                <div class="stat-label">
                    Active Members
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        avg_str = (
            f"{overall_avg:.1f} ⭐"
            if not pd.isna(overall_avg)
            else "—"
        )

        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">
                    {avg_str}
                </div>
                <div class="stat-label">
                    Overall Avg Rating
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        fig_bar = px.bar(
            summary,
            x="Month",
            y="% Finished",
            text="% Finished",
            color="% Finished",
            color_continuous_scale=THEME["bar_scale"],
            title="Completion Rate by Month",
        )

        fig_bar.update_traces(
            texttemplate="%{text}%",
            textposition="outside",
        )

        fig_bar.update_layout(
            **plot_layout(
                yaxis=dict(
                    range=[0, 110],
                    gridcolor=THEME["grid"],
                    color=THEME["accent"],
                ),
            )
        )

        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        all_ratings = []

        for m_data in st.session_state.months.values():
            all_ratings.extend(
                m_data["df"]["_rating"]
                .dropna()
                .tolist()
            )

        if all_ratings:
            rating_df = pd.DataFrame({
                "Stars": [
                    f"{int(round(r))} Star"
                    for r in all_ratings
                ]
            })

            breakdown = (
                rating_df["Stars"]
                .value_counts()
                .reset_index()
            )

            breakdown.columns = ["Rating", "Count"]

            fig_pie = px.pie(
                breakdown,
                names="Rating",
                values="Count",
                title="Ratings Breakdown",
                color_discrete_sequence=THEME["palette"],
            )

            fig_pie.update_layout(**plot_layout())

            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown(
        '<div class="section-title">Month Summary</div>',
        unsafe_allow_html=True,
    )

    disp = summary.copy()

    disp["Avg Rating"] = disp["Avg Rating"].apply(
        lambda x: f"{x:.2f} ⭐"
        if pd.notna(x)
        else "—"
    )

    disp["% Finished"] = disp["% Finished"].apply(
        lambda x: f"{x:.1f}%"
    )

    st.dataframe(
        disp,
        use_container_width=True,
        hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# BOOKS — Cover Wall + Deep Dive
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown(
        """
        <div class="section-title">
            <span class="material-icons">auto_stories</span>
            Book Cover Wall
        </div>
        <p style="color:#DDBEA8; font-size:0.93em; margin-bottom:1.2rem;">
            Click a cover to explore that month's stats.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # ── initialise selection state ────────────────────────────────────────────
    if "selected_month" not in st.session_state:
        st.session_state.selected_month = None

    # ── cover wall ────────────────────────────────────────────────────────────
    month_list = list(st.session_state.months.keys())
    COVERS_PER_ROW = 6

    # Collapse the wall when a book is selected, expand when none selected
    wall_expanded = st.session_state.selected_month is None
    wall_label = (
        "All Books"
        if wall_expanded
        else f"All Books  —  click to browse or change selection"
    )

    with st.expander(wall_label, expanded=wall_expanded):
        for row_start in range(0, len(month_list), COVERS_PER_ROW):
            row_months = month_list[row_start : row_start + COVERS_PER_ROW]
            cols = st.columns(COVERS_PER_ROW)

            for ci, month in enumerate(row_months):
                mdata = st.session_state.months[month]
                cover_url = mdata.get("cover_url")
                is_selected = st.session_state.selected_month == month

                with cols[ci]:
                    border_style = (
                        "3px solid #368F8B" if is_selected else "3px solid transparent"
                    )

                    if cover_url:
                        st.markdown(
                            f"""
                            <div style="
                                border: {border_style};
                                border-radius: 8px;
                                overflow: hidden;
                                margin-bottom: 2px;
                                max-width: 200px;
                                height: 300px;
                                margin-left: auto;
                                margin-right: auto;
                            ">
                                <img src="{cover_url}" style="
                                    width: 100%;
                                    height: 100%;
                                    object-fit: cover;
                                    display: block;
                                "/>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    else:
                        st.markdown(
                            f"""
                            <div style="
                                background: linear-gradient(135deg, #1E1636, #246A73);
                                border-radius: 6px;
                                aspect-ratio: 2/3;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                padding: 0.5rem;
                                text-align: center;
                                font-family: 'Fraunces', serif;
                                font-size: 0.7rem;
                                color: #F3DFC1;
                                min-height: 150px;
                            ">
                                <br>{mdata['book']}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st.markdown("</div>", unsafe_allow_html=True)

                    st.caption(month)
                    btn_label = "✓ Selected" if is_selected else "View Stats"
                    if st.button(btn_label, key=f"cover_btn_{month}", use_container_width=True):
                        if st.session_state.selected_month == month:
                            st.session_state.selected_month = None
                        else:
                            st.session_state.selected_month = month
                        st.rerun()

    # ── deep dive panel ───────────────────────────────────────────────────────
    selected_month = st.session_state.selected_month

    if selected_month and selected_month in st.session_state.months:
        st.markdown(
            f"""
            <hr style="margin: 2rem 0 1.5rem;">
            <div class="section-title">
                <span class="material-icons">leaderboard</span>
                {selected_month} — Deep Dive
            </div>
            """,
            unsafe_allow_html=True,
        )

        data = st.session_state.months[selected_month]
        df = data["df"]
        book = data["book"]
        author = data.get("author")
        cover_url = data.get("cover_url")

        n_total = len(df)
        n_finished = int(df["_finished"].sum())
        avg_rating = df["_rating"].dropna().mean()
        avg_str = (
            f"{avg_rating:.1f} ⭐" if not pd.isna(avg_rating) else "—"
        )

        # Book header
        cover_col, info_col = st.columns([1, 4])
        with cover_col:
            if cover_url:
                st.image(cover_url, width=200)
        with info_col:
            st.markdown(f"## {book}")
            if author:
                st.markdown(f"**By: {author}**")
            st.markdown(
                f"**{selected_month}** • {n_finished}/{n_total} finished • {avg_str} average rating"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Stat cards
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""<div class="stat-card">
                    <div class="stat-number">{n_total}</div>
                    <div class="stat-label">Responses</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""<div class="stat-card">
                    <div class="stat-number">{n_finished}</div>
                    <div class="stat-label">Members Finished</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""<div class="stat-card">
                    <div class="stat-number">{avg_str}</div>
                    <div class="stat-label">Avg Rating</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts
        left, right = st.columns(2)
        with left:
            ratings = df["_rating"].dropna()
            if not ratings.empty:
                fig_hist = px.histogram(
                    ratings,
                    x=ratings,
                    nbins=10,
                    title="Rating Distribution",
                    color_discrete_sequence=[THEME["accent"]],
                )
                fig_hist.update_layout(
                    **plot_layout(xaxis_title="Rating", yaxis_title="Count")
                )
                st.plotly_chart(fig_hist, use_container_width=True)

        with right:
            fmt_col = match_col(df, "format")
            if fmt_col:
                fmt_counts = df[fmt_col].value_counts().reset_index()
                fmt_counts.columns = ["Format", "Count"]
                fig_fmt = px.pie(
                    fmt_counts,
                    names="Format",
                    values="Count",
                    title="Format Breakdown",
                    color_discrete_sequence=THEME["palette"],
                )
                fig_fmt.update_layout(**plot_layout())
                st.plotly_chart(fig_fmt, use_container_width=True)

        # ── Book Awards ───────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title">'
            '<span class="material-icons">emoji_events</span> Book Awards</div>',
            unsafe_allow_html=True,
        )

        # Compute award winners across all months
        book_stats = {}
        for m, mdata in st.session_state.months.items():
            mdf = mdata["df"]
            mn_total     = len(mdf)
            mn_finished  = int(mdf["_finished"].sum())
            mn_abandoned = mn_total - mn_finished
            ratings      = mdf["_rating"].dropna()
            mn_avg_rating = ratings.mean() if not ratings.empty else None
            mn_rating_var = ratings.var()  if len(ratings) > 1  else None
            book_stats[m] = {
                "book":       mdata["book"],
                "abandoned":  mn_abandoned,
                "avg_rating": mn_avg_rating,
                "rating_var": mn_rating_var,
            }

        def winner_month(stat_key, highest=True):
            candidates = {
                m: s[stat_key]
                for m, s in book_stats.items()
                if s[stat_key] is not None
            }
            if not candidates:
                return None
            return (
                max(candidates, key=candidates.get)
                if highest
                else min(candidates, key=candidates.get)
            )

        most_abandoned_month   = winner_month("abandoned",  highest=True)
        highest_variance_month = winner_month("rating_var", highest=True)
        most_hated_month       = winner_month("avg_rating", highest=False)
        highest_rated_month    = winner_month("avg_rating", highest=True)

        book_awards = [
            (
                "highest_rated",
                "Highest Rated Book",
                "Highest average rating",
                selected_month == highest_rated_month,
                book_stats.get(highest_rated_month, {}).get("book", "—"),
            ),
            (
                "most_abandoned",
                "Most Abandoned",
                "Highest count of members who didn't finish",
                selected_month == most_abandoned_month,
                book_stats.get(most_abandoned_month, {}).get("book", "—"),
            ),
            (
                "club_civil_war",
                "Club Civil War Award",
                "Highest rating variance",
                selected_month == highest_variance_month,
                book_stats.get(highest_variance_month, {}).get("book", "—"),
            ),
            (
                "most_hated",
                "Most Hated Book",
                "Lowest average rating",
                selected_month == most_hated_month,
                book_stats.get(most_hated_month, {}).get("book", "—"),
            ),
        ]

        award_cols = st.columns(4)
        for ci, (badge_id, award_title, award_desc, this_book_wins, current_holder) in enumerate(book_awards):
            with award_cols[ci]:
                img_html = load_badge(badge_id, earned=this_book_wins, size=120)
                if this_book_wins:
                    card_style = "border: 2px solid #368F8B; border-radius: 12px; padding: 14px; text-align: center; background: #1E1636;"
                    status = '<div style="color:#368F8B; font-weight:700; margin-top:6px;">★ This book wins!</div>'
                else:
                    card_style = "border: 1px solid #246A73; border-radius: 12px; padding: 14px; text-align: center; background: #160F29; opacity: 0.75;"
                    status = f'<div style="color:#DDBEA8; font-size:0.78em; margin-top:6px;">Current holder:<br><em>{current_holder}</em></div>'
                st.markdown(
                    f'<div style="{card_style}">'
                    f'{img_html}'
                    f'<div style="font-weight:700; color:#F3DFC1; margin-top:8px;">{award_title}</div>'
                    f'<div style="font-size:0.78em; color:#DDBEA8; margin-top:4px;">{award_desc}</div>'
                    f'{status}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

# ══════════════════════════════════════════════════════════════════════════════
# QUOTES
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown(
        """
        <div class="section-title">
            <span class="material-icons">
                format_quote
            </span>
            Favorite Quotes
        </div>
        """,
        unsafe_allow_html=True,
    )

    for month, data in st.session_state.months.items():
        df = data["df"]

        quote_col = match_col(df, "quotes")

        if not quote_col:
            continue

        with st.expander(
            f"📖 {data['book']} — {month}"
        ):
            found = False

            for _, row in df.iterrows():
                quote = str(
                    row.get(quote_col, "")
                ).strip()

                if quote and quote.lower() not in [
                    "nan",
                    "",
                    "none",
                    "-"
                ]:
                    found = True

                    st.markdown(
                        f'''
                        <div class="quote-card">
                            "{quote}"
                            <br>
                            <small>
                                — {row["_name"]}
                            </small>
                        </div>
                        ''',
                        unsafe_allow_html=True,
                    )

            if not found:
                st.caption("No quotes shared.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MY BADGES
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown(
        '<div class="section-title">'
        '<span class="material-icons">workspace_premium</span> My Badges</div>',
        unsafe_allow_html=True,
    )
    st.markdown("Enter your name/tag below to see which badges you've earned!")

    member_name = st.text_input("Your name or tag", placeholder="e.g. Krached Keval")

    if member_name:
        member_clean  = member_name.strip().lower()
        all_months    = list(st.session_state.months.keys())
        months_2025   = [m for m in all_months if "2025" in m]
        months_2026   = [m for m in all_months if "2026" in m]

        finished_months = []
        member_speeds   = []
        member_ratings  = []
        finished_2025   = 0
        finished_2026   = 0

        for month, data in st.session_state.months.items():
            df     = data["df"]
            m_rows = df[df["_name"].str.lower() == member_clean]
            if not m_rows.empty:
                if m_rows["_finished"].any():
                    finished_months.append(month)
                    if "2025" in month:
                        finished_2025 += 1
                    if "2026" in month:
                        finished_2026 += 1
                    days_col = match_col(df, "days")
                    if days_col:
                        try:
                            days_val = float(m_rows[days_col].iloc[0])
                            member_speeds.append(days_val)
                        except Exception:
                            pass
                # Collect ratings regardless of finished status
                rating_val = m_rows["_rating"].dropna()
                if not rating_val.empty:
                    member_ratings.append(rating_val.iloc[0])

        n_finished   = len(finished_months)
        n_total      = len(all_months)
        fastest_read = min(member_speeds) if member_speeds else 999
        avg_member_rating = sum(member_ratings) / len(member_ratings) if member_ratings else None

        # Compute average ratings for ALL members to find who has lowest/highest
        all_member_ratings = {}
        for month, data in st.session_state.months.items():
            df = data["df"]
            for _, row in df.iterrows():
                name = row["_name"].strip().lower()
                r = row["_rating"]
                if pd.notna(r):
                    all_member_ratings.setdefault(name, []).append(r)
        all_member_avgs = {
            name: sum(rs) / len(rs)
            for name, rs in all_member_ratings.items()
            if len(rs) >= 2  # require at least 2 ratings to qualify
        }
        lowest_rater  = min(all_member_avgs, key=all_member_avgs.get) if all_member_avgs else None
        highest_rater = max(all_member_avgs, key=all_member_avgs.get) if all_member_avgs else None

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="stat-card">
                <div class="stat-number">{n_finished}</div>
                <div class="stat-label">Books Finished</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            pct = round(n_finished / n_total * 100) if n_total > 0 else 0
            st.markdown(f"""<div class="stat-card">
                <div class="stat-number">{pct}%</div>
                <div class="stat-label">Completion Rate</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Special Badges ────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-title">'
            '<span class="material-icons">stars</span> Special Achievements</div>',
            unsafe_allow_html=True,
        )

        curators_list = ["lightspeed", "pranjal", "nitarek", "kd", "ani", "shivani"]
        special_badges = [
            ("curator",       "Trusted Curator",
             member_clean in curators_list),
            ("champion_2025", "2025 Completely Krached",
             finished_2025 >= len(months_2025) and len(months_2025) > 0),
            ("champion_2026", "2026 Completely Krached",
             finished_2026 >= len(months_2026) and len(months_2026) > 0),
            ("speed_dragon",   "Speed Dragon (< 3 days)",
             fastest_read < 3),
            ("loyalist",      "Loyal Krachhead (12+ months)",
             n_finished >= 12),
            ("bookworm",      "Bookworm (6+ books)",
             n_finished >= 6),
            ("harsh_critic",      "Harsh Critic",
             lowest_rater is not None and member_clean == lowest_rater),
            ("golden_retriever",  "Golden Retriever Reader",
             highest_rater is not None and member_clean == highest_rater),
        ]

        for i in range(0, len(special_badges), 3):
            batch = special_badges[i : i + 3]
            cols  = st.columns(3)
            for ci, (badge_id, badge_label, earned) in enumerate(batch):
                with cols[ci]:
                    img_html    = load_badge(badge_id, earned=earned, size=150)
                    status_html = (
                        '<span class="badge-status-earned">★ Earned!</span>'
                        if earned else
                        '<span class="badge-status-locked">🔒 Locked</span>'
                    )
                    st.markdown(
                        f'<div class="badge-wrap">'
                        f'<div>{img_html}</div>'
                        f'<div class="badge-label">{badge_label}</div>'
                        f'{status_html}</div>',
                        unsafe_allow_html=True,
                    )

        # ── Monthly Badges ────────────────────────────────────────────────────
        st.markdown(
            '<div class="section-title">'
            '<span class="material-icons">calendar_today</span> Monthly Collection</div>',
            unsafe_allow_html=True,
        )

        month_badges = [
            (f"books/book_{i}", st.session_state.months[month]["book"], month in finished_months)
            for i, month in enumerate(all_months, 1)
        ]

        for row_start in range(0, len(month_badges), 4):
            row_slice = month_badges[row_start : row_start + 4]
            cols      = st.columns(4)
            for ci, (badge_id, badge_label, earned) in enumerate(row_slice):
                with cols[ci]:
                    img_html    = load_badge(badge_id, earned=earned, size=150, shape="square")
                    status_html = (
                        '<span class="badge-status-earned">★ Earned!</span>'
                        if earned else
                        '<span class="badge-status-locked">🔒 Locked</span>'
                    )
                    st.markdown(
                        f'<div class="badge-wrap">'
                        f'<div>{img_html}</div>'
                        f'<div class="badge-label">{badge_label}</div>'
                        f'{status_html}</div>',
                        unsafe_allow_html=True,
                    )

        if n_finished == 0 and member_clean not in curators_list:
            st.info(
                f"No finished books found for **{member_name}**. "
                "Make sure your name matches the form exactly!"
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — INFO
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown(
        """
        <div class="section-title">
            <span class="material-icons">menu_book</span>
            Curator's Handbook
        </div>
        <p style="color:#DDBEA8; font-size:0.97em; margin-bottom:1.5rem;">
            So you're this month's curator, congrats! Here's everything you need
            to keep the club running smoothly. ✨
        </p>
        """,
        unsafe_allow_html=True,
    )

    steps = [
        {
            "icon": "dynamic_form",
            "number": "01",
            "title": "Send Out the Google Form",
            "body": (
                "Once the book has been picked, send the monthly Google Form out "
                "to all members. Make sure the form is open and the link is shared "
                "in the group chat so everyone can fill it in at their own pace. "
                ""
            ),
        },
        {
            "icon": "table_view",
            "number": "02",
            "title": "Send the CSV to Keerthana",
            "body": (
                "After the meeting (or once responses have settled), download the "
                "CSV export of the Google Form responses and send it to "
                "<strong style='color:#F3DFC1;'>Keerthana</strong> so the dashboard "
                "can be updated with the new month's data. "
            ),
        },
        {
            "icon": "event",
            "number": "03",
            "title": "Arrange the Meeting Time",
            "body": (
                "The default meeting slot is the <strong style='color:#F3DFC1;'>first "
                "Sunday of the month</strong>. If that doesn't work for the group, "
                "it's your job to find an alternative time — poll the group early "
                "so there's no last-minute scramble!"
            ),
        },
        {
            "icon": "how_to_vote",
            "number": "04",
            "title": "Remind Next Month's Curator to Send Voting",
            "body": (
                "Before the club meeting, make sure the <strong style='color:#F3DFC1;'>"
                "next month's curator</strong> has sent out the ranked-choice voting "
                "for book nominations. Members should have a chance to vote "
                "<em>before</em> everyone gathers, so the new book can be announced "
                "at the meeting."
            ),
        },
    ]

    for step in steps:
        st.markdown(
            f"""
            <div class="curator-step-card">
                <div class="curator-step-number">{step['number']}</div>
                <div>
                    <div class="curator-step-title">
                        <span class="material-icons">{step['icon']}</span>
                        {step['title']}
                    </div>
                    <div class="curator-step-body">{step['body']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="curator-checklist">
            <span class="material-icons">tips_and_updates</span>
            <strong style="color:#F3DFC1;">Quick Checklist</strong><br>
            ☐ &nbsp; Google Form sent to members<br>
            ☐ &nbsp; CSV exported &amp; sent to Keerthana<br>
            ☐ &nbsp; Meeting time confirmed (1st Sunday or rescheduled)<br>
            ☐ &nbsp; Next curator's ranked-choice vote live before meeting
        </div>
        """,
        unsafe_allow_html=True,
    )