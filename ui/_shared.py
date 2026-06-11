"""
ui/_shared.py — Shared constants, theme, and helper functions.
Imported by every other ui/* module; never imports from them.
"""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).parent.parent / "assets"

CURATORS = [
    "Keeth", "Pranjal", "Aryan", "KD", "Ani", "Shivani",
    "Maya", "detpleasant2000", "Satabdiya",
]

MEMBERS = [
    "Test User", "Ani", "Aryan", "BO$$", "DetPleasant2000", "KD", "Kavya",
    "Keeth", "Maya", "OJ", "Pranjal", "Pooja", "RishRash", "Satabdiya",
    "Shivani", "Smrithi", "Tanvi", "Viswa",
]

# Plotly chart theme
THEME = {
    "bg":      "#1a1318",
    "paper":   "#241b23",
    "accent":  "#ff6542",
    "gold":    "#e0cba8",
    "muted":   "#9a8a98",
    "grid":    "rgba(136,73,143,0.2)",
    "palette": ["#ff6542", "#e0cba8", "#779fa1", "#88498f", "#a89faa"],
}


def plot_layout(**extra) -> dict:
    """Base Plotly layout dict. Pass keyword overrides to merge."""
    base = dict(
        plot_bgcolor=THEME["bg"],
        paper_bgcolor=THEME["paper"],
        font=dict(family="DM Sans, sans-serif", color="#f2ece8", size=13),
        title_font=dict(family="Fraunces, serif", color=THEME["gold"], size=18),
        xaxis=dict(gridcolor=THEME["grid"], color=THEME["muted"], linecolor=THEME["grid"]),
        yaxis=dict(gridcolor=THEME["grid"], color=THEME["muted"], linecolor=THEME["grid"]),
        legend=dict(bgcolor=THEME["paper"], font=dict(color="#f2ece8")),
        margin=dict(t=55, l=35, r=35, b=35),
    )
    base.update(extra)
    return base


def load_badge_img(badge_id: str, earned: bool = True, size: int = 130) -> str:
    for ext, mime in [("svg", "image/svg+xml"), ("png", "image/png")]:
        p = ASSETS_DIR / f"{badge_id}.{ext}"
        if p.exists():
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            css = "badge-img-earned" if earned else "badge-img-locked"
            return f'<img src="data:{mime};base64,{b64}" width="{size}" class="{css}"/>'
    return f'<span style="font-size:{size//2}px">{"⭐" if earned else "🔒"}</span>'


def stat_card(number, label) -> None:
    st.markdown(
        f'<div class="stat-card">'
        f'<div class="stat-number">{number}</div>'
        f'<div class="stat-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


def section(icon: str, title: str) -> None:
    st.markdown(
        f'<div class="section-title">'
        f'<span style="margin-right:8px">{icon}</span>{title}</div>',
        unsafe_allow_html=True,
    )