"""
ui/dashboard.py — Club-wide stats overview and current month progress banner.
"""
from __future__ import annotations

import math

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.gsheet_ops import get_data

from ._shared import MEMBERS, THEME, plot_layout, stat_card, section


def render_month_progress(checkins_df: pd.DataFrame, config: dict) -> None:
    current_book = config.get("current_book", "")
    month        = config.get("current_month", "This Month")

    section("📅", f"{month} — Progress")
    st.markdown(
        f'<div class="current-book-banner">📖 Currently reading: <strong>{current_book}</strong></div>',
        unsafe_allow_html=True,
    )

    if checkins_df.empty:
        return

    df = checkins_df.copy()
    if "BookTitle" in df.columns and current_book:
        df = df[df["BookTitle"].str.lower() == current_book.strip().lower()]

    total_members = len(MEMBERS)
    responded     = df["Name"].nunique() if "Name" in df.columns else 0
    n_finished    = int((df["Finished"].str.lower() == "yes").sum()) if "Finished" in df.columns else 0
    ratings       = (
        pd.to_numeric(df["Rating"].dropna(), errors="coerce").dropna()
        if "Rating" in df.columns
        else pd.Series(dtype=float)
    )
    avg_r    = f"{ratings.mean():.1f} ⭐" if not ratings.empty else "—"
    resp_pct = round(responded / total_members * 100) if total_members else 0
    fin_pct  = round(n_finished / responded * 100)    if responded   else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-number">{responded} / {total_members}</div>'
            f'<div class="stat-label">Responses in</div>'
            f'<div style="height:6px;border-radius:4px;background:rgba(136,73,143,0.18);margin-top:10px;overflow:hidden">'
            f'<div style="height:100%;width:{resp_pct}%;background:#ff6542;border-radius:4px"></div></div>'
            f'<div class="stat-label" style="margin-top:5px">{resp_pct}% of members</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-number">{n_finished} / {responded}</div>'
            f'<div class="stat-label">Finished reading</div>'
            f'<div style="height:6px;border-radius:4px;background:rgba(136,73,143,0.18);margin-top:10px;overflow:hidden">'
            f'<div style="height:100%;width:{fin_pct}%;background:#779fa1;border-radius:4px"></div></div>'
            f'<div class="stat-label" style="margin-top:5px">{fin_pct}% of respondents</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        stat_card(avg_r, f"Avg rating · {len(ratings)} so far")

    st.markdown("<br>", unsafe_allow_html=True)


def render_dashboard(checkins_df: pd.DataFrame, config: dict) -> None:
    section("📊", "Club Overview")

    if checkins_df.empty:
        st.info("No check-in data yet.")
        return

    df = checkins_df.copy()
    df.columns = [c.strip() for c in df.columns]
    col_map = {c.lower(): c for c in df.columns}

    finished_col = col_map.get("finished")
    rating_col   = col_map.get("rating")
    book_col     = col_map.get("booktitle")

    total_members = df[col_map["name"]].nunique() if "name" in col_map else "—"
    total_entries = len(df)
    n_finished    = int((df[finished_col].str.lower() == "yes").sum()) if finished_col else 0
    n_books       = df[book_col].nunique() if book_col else "—"
    avg_rating    = df[rating_col].dropna().astype(float).mean() if rating_col else None
    avg_str       = f"{avg_rating:.1f} ⭐" if avg_rating and not math.isnan(avg_rating) else "—"
    pct_done      = round(n_finished / total_entries * 100, 1) if total_entries else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card(total_members, "Members")
    with c2: stat_card(n_books,       "Books Read")
    with c3: stat_card(f"{pct_done}%","Completion Rate")
    with c4: stat_card(avg_str,       "Avg Rating")

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
                color="% Finished", color_continuous_scale=["#779fa1", "#ff6542"],
                title="Completion Rate by Book",
            )
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(**plot_layout(yaxis=dict(range=[0, 115], gridcolor=THEME["grid"], color=THEME["muted"])))
            st.plotly_chart(fig, use_container_width=True)

    if rating_col:
        all_ratings = df[rating_col].dropna().astype(float).tolist()
        if all_ratings:
            rdf       = pd.DataFrame({"Stars": [f"{int(round(r))}★" for r in all_ratings]})
            breakdown = rdf["Stars"].value_counts().reset_index()
            breakdown.columns = ["Rating", "Count"]
            with col_r:
                fig2 = px.pie(
                    breakdown, names="Rating", values="Count",
                    title="Ratings Breakdown",
                    color_discrete_sequence=THEME["palette"],
                )
                fig2.update_layout(**plot_layout())
                st.plotly_chart(fig2, use_container_width=True)

    _render_genre_and_avg_ratings(df, book_col, rating_col)
    _render_leaderboard(df, col_map, finished_col, rating_col, book_col)


def _render_genre_and_avg_ratings(df: pd.DataFrame, book_col, rating_col) -> None:
    books_df = get_data("Books")
    if books_df.empty or "Genre" not in books_df.columns or "BookTitle" not in books_df.columns:
        return

    genre_df = books_df[["BookTitle", "Genre"]].dropna(subset=["Genre"])
    genre_df = genre_df[genre_df["Genre"].str.strip() != ""]
    if genre_df.empty:
        return

    genre_counts         = genre_df["Genre"].value_counts().reset_index()
    genre_counts.columns = ["Genre", "Count"]

    g_col, r_col = st.columns(2)
    with g_col:
        fig_genre = px.pie(
            genre_counts, names="Genre", values="Count",
            color_discrete_sequence=THEME["palette"],
            hole=0.45,
        )
        fig_genre.update_traces(textposition="outside", textinfo="label+percent", textfont_color="#f2ece8")
        fig_genre.update_layout(**plot_layout(
            title="Books read by genre",
            showlegend=False,
            margin=dict(t=55, l=60, r=60, b=60),
        ))
        st.plotly_chart(fig_genre, use_container_width=True)

    with r_col:
        if book_col and rating_col:
            avg_by_book = (
                df.groupby(book_col)[rating_col]
                .apply(lambda x: pd.to_numeric(x, errors="coerce").mean())
                .dropna()
                .sort_values()
                .reset_index()
            )
            avg_by_book.columns = ["Book", "Avg Rating"]
            avg_by_book["Avg Rating"] = avg_by_book["Avg Rating"].round(2)

            fig_ratings = px.bar(
                avg_by_book, x="Avg Rating", y="Book", orientation="h",
                text="Avg Rating",
                color="Avg Rating",
                color_continuous_scale=[THEME["muted"], THEME["accent"]],
                range_color=[1, 5],
                title="Avg rating by book",
            )
            fig_ratings.update_traces(texttemplate="%{text:.2f} ⭐", textposition="outside")
            fig_ratings.update_layout(**plot_layout(
                xaxis=dict(range=[0, 5.8], gridcolor=THEME["grid"], color=THEME["muted"]),
                yaxis=dict(gridcolor=THEME["grid"], color=THEME["muted"]),
                coloraxis_showscale=False,
                showlegend=False,
            ))
            st.plotly_chart(fig_ratings, use_container_width=True)


def _render_leaderboard(df: pd.DataFrame, col_map: dict, finished_col, rating_col, book_col) -> None:
    section("🏆", "Member Leaderboard")

    name_col = col_map.get("name")
    days_col = col_map.get("daystoread")
    if not name_col:
        return

    leaderboard_rows, speed_rows = [], []

    for member, grp in df.groupby(name_col):
        finished_count = int((grp[finished_col].str.lower() == "yes").sum()) if finished_col else 0
        ratings        = (
            pd.to_numeric(grp[rating_col].dropna(), errors="coerce").dropna()
            if rating_col else pd.Series(dtype=float)
        )
        avg_r = round(ratings.mean(), 2) if not ratings.empty else None
        leaderboard_rows.append({"Member": member, "Books Finished": finished_count, "Avg Rating": avg_r})

        if days_col and finished_col and book_col:
            for _, row in grp[grp[finished_col].str.lower() == "yes"].iterrows():
                days_val = pd.to_numeric(row.get(days_col), errors="coerce")
                if pd.notna(days_val) and days_val > 0:
                    speed_rows.append({"Member": member, "Days": int(days_val), "Book": str(row.get(book_col, "")).strip()})

    lb       = pd.DataFrame(leaderboard_rows)
    speed_df = pd.DataFrame(speed_rows)

    tab_books, tab_rating, tab_speed = st.tabs(["📚 Most Finished", "⭐ Highest Rated", "⚡ Fastest Reader"])

    with tab_books:
        sorted_books = (
            lb[lb["Books Finished"] > 0]
            .sort_values("Books Finished", ascending=False)
            .head(5).reset_index(drop=True)
        )
        sorted_books.index += 1
        sorted_books.index.name = "Rank"
        sorted_books["Books Finished"] = sorted_books["Books Finished"].apply(lambda x: f"{x} 📚")
        st.dataframe(sorted_books[["Member", "Books Finished"]], use_container_width=True)

    with tab_rating:
        sorted_rating = (
            lb[lb["Avg Rating"].notna()]
            .sort_values("Avg Rating", ascending=False)
            .head(5).reset_index(drop=True)
        )
        sorted_rating.index += 1
        sorted_rating.index.name = "Rank"
        sorted_rating["Avg Rating"] = sorted_rating["Avg Rating"].apply(lambda x: f"{x:.2f} ⭐")
        st.dataframe(sorted_rating[["Member", "Avg Rating", "Books Finished"]], use_container_width=True)

    with tab_speed:
        if not speed_df.empty:
            fastest = (
                speed_df.sort_values("Days")
                .groupby("Member", as_index=False).first()
                .sort_values("Days").head(5).reset_index(drop=True)
            )
            fastest.index += 1
            fastest.index.name = "Rank"
            fastest["Days"] = fastest["Days"].apply(lambda x: f"{x} days")
            fastest = fastest.rename(columns={"Days": "Fastest Read"})
            st.dataframe(fastest[["Member", "Fastest Read", "Book"]], use_container_width=True)
        else:
            st.info("No speed data yet.")