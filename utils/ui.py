"""
ui.py — All rendering components for KrachBooks.
"""
from __future__ import annotations

import base64
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.book_api import get_book_info
from utils.gsheet_ops import (
    get_data, get_config, get_books_lookup, append_row, upsert_checkin,
    upsert_vote, add_nomination, close_voting, update_config,
)

ASSETS_DIR = Path(__file__).parent.parent / "assets"

CURATORS = [
    "lightspeed", "pranjal", "aryan", "kd", "ani", "shivani", "maya", "detpleasant2000",
]

MEMBERS = ["Ani", "BO$$", "DetPleasant2000", "Kavya", "Lightspeed", "Maya", "Aryan", "OJ", "Pooja", "Pranjal", 
        "RishRash", "Satabdiya", "Shivani", "Smrithi", "Tanvi", "Viswa"
]

THEME = {
    "bg":      "#1a1a1a",
    "paper":   "#222222",
    "accent":  "#fcb97d",
    "gold":    "#edd892",
    "muted":   "#b5b8a3",
    "grid":    "rgba(252,185,125,0.15)",
    "palette": ["#fcb97d", "#edd892", "#c6b89e", "#aaba9e", "#b5b8a3"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _plot_layout(**extra):
    base = dict(
        plot_bgcolor=THEME["bg"],
        paper_bgcolor=THEME["paper"],
        font=dict(family="Georgia, serif", color="#f0e6d3", size=13),
        title_font=dict(family="Georgia, serif", color=THEME["gold"], size=18),
        xaxis=dict(gridcolor=THEME["grid"], color=THEME["muted"], linecolor=THEME["grid"]),
        yaxis=dict(gridcolor=THEME["grid"], color=THEME["muted"], linecolor=THEME["grid"]),
        legend=dict(bgcolor=THEME["paper"], font=dict(color="#f0e6d3")),
        margin=dict(t=55, l=35, r=35, b=35),
    )
    base.update(extra)
    return base


def _load_badge_img(badge_id: str, earned: bool = True, size: int = 130) -> str:
    for ext, mime in [("svg", "image/svg+xml"), ("png", "image/png")]:
        p = ASSETS_DIR / f"{badge_id}.{ext}"
        if p.exists():
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            css = "badge-img-earned" if earned else "badge-img-locked"
            return f'<img src="data:{mime};base64,{b64}" width="{size}" class="{css}"/>'
    return f'<span style="font-size:{size//2}px">{"⭐" if earned else "🔒"}</span>'


def _stat_card(number, label):
    st.markdown(
        f'<div class="stat-card">'
        f'<div class="stat-number">{number}</div>'
        f'<div class="stat-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def _section(icon: str, title: str):
    st.markdown(
        f'<div class="section-title">'
        f'<span style="margin-right:8px">{icon}</span>{title}</div>',
        unsafe_allow_html=True,
    )


# ── Cover Wall ────────────────────────────────────────────────────────────────

def render_cover_wall(checkins_df: pd.DataFrame):
    _section("📚", "Book Cover Wall")
    st.markdown(
        '<p class="page-intro-sm">Click a cover to explore that book\'s stats and quotes.</p>',
        unsafe_allow_html=True,
    )

    if checkins_df.empty or "BookTitle" not in checkins_df.columns:
        st.info("No books logged yet.")
        return

    if "selected_book" not in st.session_state:
        st.session_state.selected_book = None

    books        = checkins_df["BookTitle"].dropna().unique()
    books_lookup = get_books_lookup()
    COLS         = 6

    for row_start in range(0, len(books), COLS):
        cols = st.columns(COLS)
        for i, book in enumerate(books[row_start: row_start + COLS]):
            book_entry  = books_lookup.get(book.strip().lower(), {})
            isbn        = book_entry.get("isbn", "")
            meta        = get_book_info(book, isbn=isbn)
            is_selected = st.session_state.selected_book == book
            frame_cls   = "cover-frame cover-frame--selected" if is_selected else "cover-frame"

            with cols[i]:
                if meta and meta["cover_url"]:
                    st.markdown(
                        f'<div class="{frame_cls}"><img src="{meta["cover_url"]}" width="100%"/></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="cover-placeholder">{book}</div>',
                        unsafe_allow_html=True,
                    )
                btn_label = "✓ Selected" if is_selected else "View"
                if st.button(btn_label, key=f"book_btn_{book}", use_container_width=True):
                    st.session_state.selected_book = None if is_selected else book
                    st.rerun()

    # ── Deep Dive Panel ───────────────────────────────────────────────────────
    selected     = st.session_state.selected_book
    books_lookup = get_books_lookup()
    if selected and not checkins_df.empty:
        book_df = checkins_df[checkins_df["BookTitle"] == selected].copy()
        if book_df.empty:
            return

        book_entry = books_lookup.get(selected.strip().lower(), {})
        meta       = get_book_info(selected, isbn=book_entry.get("isbn", ""))
        author = (meta or {}).get("author", "")

        st.markdown("<hr>", unsafe_allow_html=True)
        _section("🔍", selected)

        cover_col, info_col = st.columns([1, 4])
        with cover_col:
            if meta and meta["cover_url"]:
                st.image(meta["cover_url"], width=180)
        with info_col:
            st.markdown(f"## {selected}")
            if author:
                st.markdown(f"*by {author}*")

            n_total    = len(book_df)
            n_finished = int((book_df["Finished"].str.lower() == "yes").sum()) if "Finished" in book_df.columns else 0
            ratings    = pd.to_numeric(book_df["Rating"].dropna(), errors="coerce").dropna() if "Rating" in book_df.columns else pd.Series(dtype=float)
            avg_rating = ratings.mean() if not ratings.empty else None
            avg_str    = f"{avg_rating:.1f} ⭐" if avg_rating else "—"
            pct        = round(n_finished / n_total * 100) if n_total else 0

            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1: _stat_card(n_total,    "Responses")
            with c2: _stat_card(n_finished, "Finished")
            with c3: _stat_card(f"{pct}%",  "Completion")
            with c4: _stat_card(avg_str,    "Avg Rating")

        st.markdown("<br>", unsafe_allow_html=True)

        chart_l, chart_r = st.columns(2)
        with chart_l:
            if not ratings.empty:
                fig_hist = px.histogram(
                    ratings, x=ratings, nbins=5,
                    title="Rating Distribution",
                    color_discrete_sequence=[THEME["accent"]],
                )
                fig_hist.update_layout(**_plot_layout(xaxis_title="Rating", yaxis_title="Count"))
                st.plotly_chart(fig_hist, use_container_width=True)

        with chart_r:
            if "Format" in book_df.columns:
                fmt_counts = book_df["Format"].value_counts().reset_index()
                fmt_counts.columns = ["Format", "Count"]
                fig_fmt = px.pie(
                    fmt_counts, names="Format", values="Count",
                    title="Format Breakdown",
                    color_discrete_sequence=THEME["palette"],
                )
                fig_fmt.update_layout(**_plot_layout())
                st.plotly_chart(fig_fmt, use_container_width=True)

        _section("👥", "Member Responses")
        show_cols = [c for c in ["Name", "Finished", "DaysToRead", "Format", "Rating"] if c in book_df.columns]
        st.dataframe(book_df[show_cols].reset_index(drop=True), use_container_width=True, hide_index=True)

        if "Quote" in book_df.columns:
            quotes = book_df[["Name", "Quote"]].dropna(subset=["Quote"])
            quotes = quotes[quotes["Quote"].str.strip().str.lower().isin(["", "nan", "none"]) == False]
            if not quotes.empty:
                _section("💬", "Quotes & Reviews")
                for _, row in quotes.iterrows():
                    quote = str(row["Quote"]).strip()
                    name  = str(row["Name"]).strip()
                    if quote and quote.lower() not in ("nan", "none", ""):
                        st.markdown(
                            f'<div class="quote-card">'
                            f'"{quote}"'
                            f'<br><small style="color:var(--text-muted)">— {name}</small>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )


# ── Dashboard / Stats ─────────────────────────────────────────────────────────

# ── Dashboard / Stats ─────────────────────────────────────────────────────────
 
def render_dashboard(checkins_df: pd.DataFrame, config: dict):
    _section("📊", "Club Overview")
 
    current_book = config.get("current_book", "—")
    st.markdown(
        f'<div class="current-book-banner">📖 Currently reading: <strong>{current_book}</strong></div>',
        unsafe_allow_html=True,
    )
 
    if checkins_df.empty:
        st.info("No check-in data yet.")
        return
 
    df = checkins_df.copy()
    df.columns = [c.strip() for c in df.columns]
 
    col_map      = {c.lower(): c for c in df.columns}
    finished_col = col_map.get("finished", None)
    rating_col   = col_map.get("rating", None)
    book_col     = col_map.get("booktitle", None)
 
    total_members = df[col_map["name"]].nunique() if "name" in col_map else "—"
    total_entries = len(df)
    n_finished    = int((df[finished_col].str.lower() == "yes").sum()) if finished_col else 0
    n_books       = df[book_col].nunique() if book_col else "—"
    avg_rating    = df[rating_col].dropna().astype(float).mean() if rating_col else None
    avg_str       = f"{avg_rating:.1f} ⭐" if avg_rating and not math.isnan(avg_rating) else "—"
    pct_done      = round(n_finished / total_entries * 100, 1) if total_entries else 0
 
    c1, c2, c3, c4 = st.columns(4)
    with c1: _stat_card(total_members, "Members")
    with c2: _stat_card(n_books, "Books Read")
    with c3: _stat_card(f"{pct_done}%", "Completion Rate")
    with c4: _stat_card(avg_str, "Avg Rating")
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    col_l, col_r = st.columns(2)
 
    if book_col and finished_col:
        book_stats = (
            df.groupby(book_col)
            .apply(lambda g: round((g[finished_col].str.lower() == "yes").sum() / len(g) * 100, 1))
            .reset_index()
        )
        book_stats.columns = ["Book", "% Finished"]
        with col_l:
            fig = px.bar(
                book_stats, x="Book", y="% Finished", text="% Finished",
                color="% Finished", color_continuous_scale=["#c6b89e", "#fcb97d"],
                title="Completion Rate by Book",
            )
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(**_plot_layout(yaxis=dict(range=[0, 115], gridcolor=THEME["grid"], color=THEME["muted"])))
            st.plotly_chart(fig, use_container_width=True)
 
    if rating_col:
        all_ratings = df[rating_col].dropna().astype(float).tolist()
        if all_ratings:
            rdf = pd.DataFrame({"Stars": [f"{int(round(r))}★" for r in all_ratings]})
            breakdown = rdf["Stars"].value_counts().reset_index()
            breakdown.columns = ["Rating", "Count"]
            with col_r:
                fig2 = px.pie(
                    breakdown, names="Rating", values="Count",
                    title="Ratings Breakdown",
                    color_discrete_sequence=THEME["palette"],
                )
                fig2.update_layout(**_plot_layout())
                st.plotly_chart(fig2, use_container_width=True)
 
# ── Check-in Form ─────────────────────────────────────────────────────────────

def render_checkin_form(user: str, config: dict):
    current_book = config.get("current_book", "")
    _section("✏️", f"Monthly Check-in — {current_book}")

    checkins_df = get_data("Checkins")

    existing = pd.DataFrame()
    if not checkins_df.empty and "Name" in checkins_df.columns:
        mask = (
            checkins_df["Name"].str.lower() == user.lower()
        ) & (checkins_df.get("BookTitle", pd.Series(dtype=str)).str.lower() == current_book.lower())
        existing = checkins_df[mask]

    def _get(col, default):
        if not existing.empty and col in existing.columns:
            val = existing.iloc[0][col]
            return val if pd.notna(val) else default
        return default

    already_submitted = not existing.empty
    if already_submitted:
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

        fmt_opts  = ["Kindle/eBook", "Audiobook", "Hardcopy"]
        fmt_def   = fmt_opts.index(_get("Format", "Kindle/eBook")) if _get("Format", "Kindle/eBook") in fmt_opts else 0
        fmt       = st.selectbox("Format", fmt_opts, index=fmt_def)

        rating = st.slider(
            "Rating (1–5 ⭐)",
            min_value=1, max_value=5,
            value=int(_get("Rating", 3) or 3),
        )

        quote    = st.text_area("Favourite quote or passage", value=_get("Quote", ""), height=100)
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


# ── Voting Form (non-curators) ────────────────────────────────────────────────

def render_voting_form(user: str, config: dict):
    month = config.get("current_month", "This Month")
    _section("🗳️", "Vote for Next Month's Book")
    st.markdown(
        '<p class="page-intro-sm">Pick your favourite from the curator\'s nominations below.</p>',
        unsafe_allow_html=True,
    )

    noms_df = get_data("Nominations")
    if noms_df.empty or "BookTitle" not in noms_df.columns:
        st.markdown(
            '<div class="current-book-banner">📭 No nominations yet — check back once your curator adds some!</div>',
            unsafe_allow_html=True,
        )
        return

    if "Month" in noms_df.columns:
        noms_df = noms_df[noms_df["Month"].str.strip() == month.strip()]

    books = noms_df["BookTitle"].dropna().tolist()
    if not books:
        st.info("No nominations for this month yet.")
        return

    # ── Check existing vote ───────────────────────────────────────────────────
    votes_df  = get_data("Votes")
    user_vote = None
    if not votes_df.empty and "VotedBy" in votes_df.columns and "Month" in votes_df.columns:
        mask = (
            votes_df["VotedBy"].str.lower() == user.lower()
        ) & (votes_df["Month"].str.strip() == month.strip())
        if votes_df[mask].shape[0] > 0:
            user_vote = votes_df[mask].iloc[0].get("BookTitle", None)

    # ── Nominee cards ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <style>
    .nominee-grid { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
    .nominee-card {
        background: var(--surface);
        border: 1.5px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        flex: 1 1 160px;
        max-width: 220px;
        text-align: center;
        transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
    }
    .nominee-card:hover {
        border-color: var(--caramel);
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(252,185,125,0.15);
    }
    .nominee-card--voted {
        border-color: var(--caramel) !important;
        background: rgba(252,185,125,0.07);
        box-shadow: 0 0 0 3px rgba(252,185,125,0.2);
    }
    .nominee-cover {
        border-radius: 6px;
        width: 100px;
        height: 148px;
        object-fit: cover;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    .nominee-cover-placeholder {
        width: 100px;
        height: 148px;
        background: var(--surface-2);
        border: 1px dashed var(--border);
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        color: var(--text-muted);
        margin: 0 auto 10px auto;
        padding: 8px;
    }
    .nominee-title {
        font-family: 'Fraunces', serif;
        font-size: 0.9rem;
        color: var(--text);
        font-weight: 600;
        margin-bottom: 4px;
        line-height: 1.3;
    }
    .nominee-voted-badge {
        display: inline-block;
        background: var(--caramel);
        color: var(--bg);
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 20px;
        margin-top: 6px;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)

    import html as _html

    cards_html = '<div class="nominee-grid">'
    for book in books:
        meta      = get_book_info(book)
        is_voted  = user_vote and user_vote.lower() == book.lower()
        card_cls  = "nominee-card nominee-card--voted" if is_voted else "nominee-card"
        safe_book = _html.escape(book)

        if meta and meta.get("cover_url"):
            cover_html = f'<img class="nominee-cover" src="{meta["cover_url"]}" />'
        else:
            cover_html = (
                f'<div class="nominee-cover-placeholder">'
                f'<span style="font-size:2rem; display:block; margin-bottom:6px;">📖</span>'
                f'<span>{safe_book}</span>'
                f'</div>'
            )

        voted_badge = '<div class="nominee-voted-badge">Your Vote</div>' if is_voted else ""

        cards_html += (
            f'<div class="{card_cls}">'
            f'{cover_html}'
            f'<div class="nominee-title">{safe_book}</div>'
            f'{voted_badge}'
            f'</div>'
        )
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # ── Vote form ─────────────────────────────────────────────────────────────
    if user_vote:
        st.markdown(
            f'<div class="current-book-banner">✅ You voted for <strong>{user_vote}</strong>. '
            f'Change your mind below.</div>',
            unsafe_allow_html=True,
        )

    with st.form("vote_form"):
        choice = st.selectbox(
            "Cast your vote",
            books,
            index=books.index(user_vote) if user_vote in books else 0,
            help="Select the book you want the club to read next month.",
        )
        submitted = st.form_submit_button(
            "🗳️  Submit Vote",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        try:
            upsert_vote(user, month, choice)
            st.success(f"Voted for **{choice}**! 🎉")
            st.rerun()
        except Exception as e:
            st.error(f"Couldn't save vote: {e}")


# ── Curator Panel ─────────────────────────────────────────────────────────────

def render_curator_panel(user: str, config: dict):
    month        = config.get("current_month", "")
    voting_open  = config.get("voting_open", "False").lower() == "true"
    current_book = config.get("current_book", "")

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(237,216,146,0.1), rgba(252,185,125,0.06));
        border: 1px solid var(--border);
        border-left: 4px solid var(--gold);
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 28px;
    ">
        <div style="font-family:'Fraunces',serif; font-size:1.1rem; color:var(--gold); margin-bottom:4px;">
            ✨ You're the Curator for {month}
        </div>
        <div style="font-size:0.85rem; color:var(--text-muted);">
            Use the steps below to nominate books, open voting, and confirm next month's pick.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step 1: Nominations ──────────────────────────────────────────────────
    st.markdown("""
    <div class="curator-step-card">
        <div class="curator-step-number">01</div>
        <div>
            <div class="curator-step-title">📚 Add Nominations</div>
            <div class="curator-step-body">Add 2–3 books for the club to vote on. They'll appear as cards in the voting tab.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("nom_form"):
        col_a, col_b = st.columns([4, 1])
        with col_a:
            nom_title = st.text_input("Book title", placeholder="e.g. Tomorrow, and Tomorrow, and Tomorrow", label_visibility="collapsed")
        with col_b:
            submitted = st.form_submit_button("➕ Add", use_container_width=True)

    if submitted and nom_title:
        try:
            add_nomination(month, nom_title, user)
            st.success(f"Added **{nom_title}**!")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    noms_df = get_data("Nominations")
    if not noms_df.empty and "Month" in noms_df.columns:
        this_month_noms = noms_df[noms_df["Month"].str.strip() == month.strip()]
        if not this_month_noms.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            cols = st.columns(len(this_month_noms))
            for i, (_, row) in enumerate(this_month_noms.iterrows()):
                meta = get_book_info(row["BookTitle"])
                with cols[i]:
                    if meta and meta.get("cover_url"):
                        st.image(meta["cover_url"], width=90)
                    st.markdown(
                        f'<div style="font-size:0.8rem; color:var(--text); font-family:Fraunces,serif; margin-top:6px; line-height:1.3">'
                        f'{row["BookTitle"]}</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 2: Voting ────────────────────────────────────────────────────────
    status_color = "var(--ash-2)" if voting_open else "var(--text-muted)"
    status_dot   = "🟢" if voting_open else "🔴"
    status_text  = "Voting is OPEN — members can cast their votes." if voting_open else "Voting is closed."

    st.markdown(f"""
    <div class="curator-step-card">
        <div class="curator-step-number">02</div>
        <div style="flex:1">
            <div class="curator-step-title">🗳️ Manage Voting</div>
            <div class="curator-step-body" style="margin-bottom:12px;">
                {status_dot} <span style="color:{status_color}">{status_text}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if not voting_open:
            if st.button("🔓  Open Voting", use_container_width=True):
                try:
                    update_config("voting_open", "True")
                    st.success("Voting is now open!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with col2:
        if voting_open:
            if st.button("🔒  Close Voting", use_container_width=True, type="primary"):
                st.session_state["confirm_close"] = True

    # Confirm close — show winner preview before committing
    if st.session_state.get("confirm_close"):
        votes_df = get_data("Votes")
        if not votes_df.empty and "BookTitle" in votes_df.columns and "Month" in votes_df.columns:
            month_votes = votes_df[votes_df["Month"].str.strip() == month.strip()]
            if not month_votes.empty:
                tally  = month_votes["BookTitle"].value_counts()
                winner = tally.idxmax()
                total  = tally.sum()

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="
                    background: rgba(252,185,125,0.1);
                    border: 1px solid var(--caramel);
                    border-radius: 12px;
                    padding: 20px 24px;
                    margin-bottom: 12px;
                ">
                    <div style="font-family:'Fraunces',serif; font-size:1rem; color:var(--gold); margin-bottom:8px;">
                        Confirm Winner
                    </div>
                    <div style="font-size:1.4rem; font-family:'Fraunces',serif; color:var(--caramel); margin-bottom:4px;">
                        🏆 {winner}
                    </div>
                    <div style="font-size:0.82rem; color:var(--text-muted);">
                        {tally[winner]} of {total} votes
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c_confirm, c_cancel = st.columns(2)
                with c_confirm:
                    if st.button("✅  Confirm & Close", use_container_width=True, type="primary"):
                        try:
                            close_voting(winner, month)
                            st.session_state.pop("confirm_close", None)
                            st.success(f"🎉 **{winner}** is next month's book!")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                with c_cancel:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.pop("confirm_close", None)
                        st.rerun()
            else:
                st.warning("No votes recorded yet — can't close.")
                st.session_state.pop("confirm_close", None)

    # ── Live tally ────────────────────────────────────────────────────────────
    votes_df = get_data("Votes")
    if not votes_df.empty and "BookTitle" in votes_df.columns and "Month" in votes_df.columns:
        month_votes = votes_df[votes_df["Month"].str.strip() == month.strip()]
        if not month_votes.empty:
            tally       = month_votes["BookTitle"].value_counts().reset_index()
            tally.columns = ["Book", "Votes"]
            total_votes = tally["Votes"].sum()

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f'<div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:10px; '
                f'text-transform:uppercase; letter-spacing:1px;">'
                f'Live Tally · {total_votes} vote{"s" if total_votes != 1 else ""} cast</div>',
                unsafe_allow_html=True,
            )
            for _, row in tally.iterrows():
                pct        = row["Votes"] / total_votes * 100
                is_leading = row["Book"] == tally.iloc[0]["Book"]
                bar_color  = "var(--caramel)" if is_leading else "var(--khaki)"
                st.markdown(f"""
                <div style="margin-bottom: 12px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                        <span style="font-size:0.85rem; color:var(--text); font-family:'Fraunces',serif;">{row['Book']}</span>
                        <span style="font-size:0.8rem; color:var(--text-muted);">{row['Votes']} vote{"s" if row['Votes'] != 1 else ""} · {pct:.0f}%</span>
                    </div>
                    <div style="background:var(--surface-2); border-radius:4px; height:8px; overflow:hidden;">
                        <div style="background:{bar_color}; width:{pct}%; height:100%; border-radius:4px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step 3: Config ────────────────────────────────────────────────────────
    st.markdown("""
    <div class="curator-step-card">
        <div class="curator-step-number">03</div>
        <div>
            <div class="curator-step-title">⚙️ Update Config</div>
            <div class="curator-step-body">Roll over to next month — update the month label and hand off the curator role.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("config_form"):
        new_month   = st.text_input("Current Month", value=month, placeholder="e.g. July 2026")
        new_curator = st.text_input("Next Curator's Name", value=config.get("current_curator", ""), placeholder="Exact name from the members list")
        if st.form_submit_button("💾  Save Config", use_container_width=True):
            try:
                update_config("current_month", new_month)
                update_config("current_curator", new_curator)
                st.success("Config updated!")
                st.rerun()
            except Exception as e:
                st.error(str(e))


# ── Profile / My Badges ───────────────────────────────────────────────────────

def render_profile(user: str):
    _section("🏅", f"{user}'s Profile")

    checkins_df = get_data("Checkins")
    all_months  = get_data("Nominations")
    user_clean  = user.strip().lower()

    if checkins_df.empty or "Name" not in checkins_df.columns:
        st.info("No check-in data yet.")
        return

    user_df = checkins_df[checkins_df["Name"].str.lower() == user_clean].copy()

    n_finished = 0
    fastest    = 999
    ratings    = []

    if not user_df.empty:
        if "Finished" in user_df.columns:
            n_finished = int((user_df["Finished"].str.lower() == "yes").sum())
        if "DaysToRead" in user_df.columns:
            speeds = user_df["DaysToRead"].dropna()
            speeds = pd.to_numeric(speeds, errors="coerce").dropna()
            if not speeds.empty:
                fastest = float(speeds.min())
        if "Rating" in user_df.columns:
            ratings = pd.to_numeric(user_df["Rating"].dropna(), errors="coerce").dropna().tolist()

    n_total  = len(checkins_df["BookTitle"].dropna().unique()) if not checkins_df.empty else 0
    pct      = round(n_finished / n_total * 100) if n_total > 0 else 0
    avg_r    = sum(ratings) / len(ratings) if ratings else None

    c1, c2, c3 = st.columns(3)
    with c1: _stat_card(n_finished, "Books Finished")
    with c2: _stat_card(f"{pct}%", "Completion Rate")
    with c3: _stat_card(f"{avg_r:.1f}⭐" if avg_r else "—", "Your Avg Rating")

    st.markdown("<br>", unsafe_allow_html=True)

    all_member_avgs = {}
    if not checkins_df.empty and "Name" in checkins_df.columns and "Rating" in checkins_df.columns:
        for name, grp in checkins_df.groupby("Name"):
            rs = pd.to_numeric(grp["Rating"].dropna(), errors="coerce").dropna().tolist()
            if len(rs) >= 2:
                all_member_avgs[name.strip().lower()] = sum(rs) / len(rs)

    lowest_rater  = min(all_member_avgs, key=all_member_avgs.get) if all_member_avgs else None
    highest_rater = max(all_member_avgs, key=all_member_avgs.get) if all_member_avgs else None

    _section("🏆", "Your Badges")

    special_badges = [
        ("curator",          "Trusted Curator",           user_clean in CURATORS),
        ("speed_dragon",     "Speed Dragon (< 3 days)",   fastest < 3),
        ("loyalist",         "Loyal Krachhead (12+)",     n_finished >= 12),
        ("bookworm",         "Bookworm (6+ books)",       n_finished >= 6),
        ("harsh_critic",     "Harsh Critic",              lowest_rater  is not None and user_clean == lowest_rater),
        ("golden_retriever", "Golden Retriever Reader",   highest_rater is not None and user_clean == highest_rater),
    ]

    BADGE_COLS = 3
    for row_start in range(0, len(special_badges), BADGE_COLS):
        batch = special_badges[row_start: row_start + BADGE_COLS]
        cols  = st.columns(BADGE_COLS)
        for ci, (badge_id, label, earned) in enumerate(batch):
            with cols[ci]:
                img_html    = _load_badge_img(badge_id, earned=earned, size=130)
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

    if not checkins_df.empty and "BookTitle" in checkins_df.columns:
        all_books = checkins_df["BookTitle"].dropna().unique()
        finished_books = set()
        if not user_df.empty and "Finished" in user_df.columns:
            finished_books = set(
                user_df[user_df["Finished"].str.lower() == "yes"]["BookTitle"]
                .str.lower().tolist()
            )

        _section("📅", "Monthly Collection")
        month_badges = [
            (f"books/book_{i+1}", book, book.lower() in finished_books)
            for i, book in enumerate(all_books)
        ]

        for row_start in range(0, len(month_badges), 4):
            row_slice = month_badges[row_start: row_start + 4]
            cols      = st.columns(4)
            for ci, (badge_id, label, earned) in enumerate(row_slice):
                with cols[ci]:
                    img_html    = _load_badge_img(badge_id, earned=earned, size=130)
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

    if not user_df.empty:
        _section("📖", "Your Check-ins")
        show_cols = [c for c in ["BookTitle", "Finished", "DaysToRead", "Format", "Rating", "Timestamp"] if c in user_df.columns]
        st.dataframe(user_df[show_cols], use_container_width=True, hide_index=True)