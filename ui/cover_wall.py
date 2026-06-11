"""
ui/cover_wall.py — Book cover shelf with per-book deep-dive panel.

Each book slot renders the cover image via st.markdown, then overlays an
invisible full-size st.button on top using CSS absolute positioning.
Tapping anywhere on the cover triggers the button → updates session_state
→ reruns. No query params, no visible buttons.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.book_api import get_book_info
from utils.gsheet_ops import get_books_lookup

from ._shared import THEME, plot_layout, stat_card, section



# ── Cover Wall ────────────────────────────────────────────────────────────────

def render_cover_wall(checkins_df: pd.DataFrame, key_prefix: str = "wall"):
    section("📚", "Book Cover Wall")
    st.markdown('<p class="page-intro-sm">Click a cover to explore that book\'s stats and quotes.</p>',
                unsafe_allow_html=True)

    if checkins_df.empty or "BookTitle" not in checkins_df.columns:
        st.info("No books logged yet.")
        return

    if "selected_book" not in st.session_state:
        st.session_state.selected_book = None

    books        = checkins_df["BookTitle"].dropna().unique()
    books_lookup = get_books_lookup()
    COLS         = 4

    for row_start in range(0, len(books), COLS):
        row_books = books[row_start: row_start + COLS]

        # Build shelf HTML: covers sit on a wood plank
        covers_html = ""
        for book in row_books:
            book_entry   = books_lookup.get(book.strip().lower(), {})
            isbn         = book_entry.get("isbn", "")
            meta         = get_book_info(book, isbn=isbn)
            is_selected  = st.session_state.selected_book == book
            selected_cls = " shelf-book--selected" if is_selected else ""

            if meta and meta["cover_url"]:
                img_html = f'<img src="{meta["cover_url"]}" class="shelf-book-img"/><div class="shelf-book-spine"></div>'
            else:
                img_html = f'<div class="shelf-book-placeholder">{book}</div><div class="shelf-book-spine"></div>'

            covers_html += (
                f'<div class="shelf-book-slot">' 
                f'<div class="shelf-book{selected_cls}">{img_html}</div>' 
                f'</div>'
            )

        st.markdown(
            f'<div class="shelf-row-wrap">' 
            f'<div class="shelf-books-row">{covers_html}</div>' 
            f'<div class="shelf-plank"><div class="shelf-plank-shadow"></div></div>' 
            f'</div>',
            unsafe_allow_html=True,
        )

        # Buttons row — Streamlit native so clicks work
        cols = st.columns(COLS)
        for i, book in enumerate(row_books):
            is_selected = st.session_state.selected_book == book
            with cols[i]:
                btn_label = "✓ Selected" if is_selected else "View"
                if st.button(btn_label, key=f"{key_prefix}_btn_{book}", use_container_width=True):
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
        author     = (meta or {}).get("author", "")

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
            quotes = quotes[~quotes["Quote"].str.strip().str.lower().isin(["", "nan", "none"])]
            if not quotes.empty:
                _section("💬", "Quotes & Reviews")
                for _, row in quotes.iterrows():
                    quote = str(row["Quote"]).strip()
                    name  = str(row["Name"]).strip()
                    if quote and quote.lower() not in ("nan", "none", ""):
                        st.markdown(
                            f'<div class="quote-card">"{quote}"'
                            f'<br><small class="quote-attr">— {name}</small></div>',
                            unsafe_allow_html=True,
                        )