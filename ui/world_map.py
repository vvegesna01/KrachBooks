"""
ui/world_map.py — Choropleth map of countries explored through club books.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.gsheet_ops import get_data

from ._shared import THEME, plot_layout, section


def _explode_countries(map_df: pd.DataFrame) -> pd.DataFrame:
    """
    Split comma-separated country strings into one row per country.
    "India, Pakistan" → two rows with the same BookTitle.
    Strips whitespace and drops any empty strings left after splitting.
    """
    exploded = (
        map_df
        .assign(Country=map_df["Country"].str.split(","))
        .explode("Country")
    )
    exploded["Country"] = exploded["Country"].str.strip()
    return exploded[exploded["Country"] != ""].reset_index(drop=True)


def render_world_map(checkins_df: pd.DataFrame) -> None:
    section("🌍", "Countries We've Explored")
    st.markdown(
        '<p class="page-intro-sm">Every book takes us somewhere. Here\'s where we\'ve been.</p>',
        unsafe_allow_html=True,
    )

    books_df = get_data("Books")
    if books_df.empty or "Country" not in books_df.columns or "BookTitle" not in books_df.columns:
        st.info("Add a 'Country' column to your Books sheet to see the map.")
        return

    map_df = books_df[["BookTitle", "Country"]].dropna(subset=["Country"])
    map_df = map_df[map_df["Country"].str.strip() != ""]

    if map_df.empty:
        st.info("No country data yet — fill in the Country column in your Books sheet.")
        return

    # Explode comma-separated countries into one row per (book, country) pair
    # e.g. "India, Pakistan" → two rows, both pointing at the same BookTitle
    map_df = _explode_countries(map_df)

    country_counts = (
        map_df.groupby("Country")
        .agg(
            Books=("BookTitle", "nunique"),  # distinct books, not rows
            Titles=("BookTitle", lambda x: "<br>".join(f"• {t}" for t in x.unique())),
        )
        .reset_index()
    )

    max_books   = int(country_counts["Books"].max())
    tick_vals   = list(range(1, max_books + 1))
    color_scale = [
        [0.00, "#1a1318"],  # 0 books — invisible (bg colour)
        [0.01, "#779fa1"],  # 1 book  — pacific teal
        [0.50, "#88498f"],  # mid     — grape
        [1.00, "#f9b14a"],  # max     — tomato
    ]

    fig = px.choropleth(
        country_counts,
        locations="Country",
        locationmode="country names",
        color="Books",
        hover_name="Country",
        hover_data={"Books": True, "Titles": True, "Country": False},
        color_continuous_scale=color_scale,
        range_color=[0, max_books],
        title="",
    )
    fig.update_layout(
        plot_bgcolor=THEME["bg"],
        paper_bgcolor=THEME["bg"],
        geo=dict(
            bgcolor=THEME["bg"],
            landcolor="#2a1f28",
            showland=True,
            showocean=True,
            oceancolor=THEME["bg"],
            showlakes=False,
            showcountries=True,
            countrycolor="rgba(255,255,255,0.07)",
            showcoastlines=True,
            coastlinecolor="rgba(255,255,255,0.1)",
            showframe=False,
            projection_type="natural earth",
        ),
        coloraxis_colorbar=dict(
            title="Books",
            tickvals=tick_vals,
            ticktext=[str(v) for v in tick_vals],
            tickfont=dict(color="#f2ece8"),
            bgcolor=THEME["paper"],
            bordercolor="rgba(136,73,143,0.3)",
            thickness=14,
        ),
        font=dict(color="#f2ece8"),
        margin=dict(t=10, l=0, r=0, b=0),
        height=480,
    )
    st.plotly_chart(fig, use_container_width=True)

    # st.markdown("<br>", unsafe_allow_html=True)
    # section("📍", "Books by Country")

    # cols = st.columns(3)
    # for i, (_, row) in enumerate(country_counts.sort_values("Country").iterrows()):
    #     books_for_country = map_df[map_df["Country"] == row["Country"]]["BookTitle"].unique()
    #     titles_html = "".join(
    #         f'<span class="country-book-item">• {t}</span><br>'
    #         for t in books_for_country
    #     )
    #     with cols[i % 3]:
    #         st.markdown(
    #             f'<div class="country-card">'
    #             f'<div class="country-card-name">📍 {row["Country"]}</div>'
    #             f'{titles_html}</div>',
    #             unsafe_allow_html=True,
    #         )