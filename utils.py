# # theme_utils.py
# import streamlit as st
# import streamlit.components.v1 as components
 
# # ── Palette definitions (must mirror styles.css :root / [data-theme="dark"]) ──
 
# LIGHT = dict(
#     bg       = "#FAF7F4",
#     paper    = "#FFFFFF",
#     grid     = "#E2D8CF",
#     text     = "#2C2420",
#     axis     = "#7A6860",
#     accent   = "#B07A8A",
#     # bar / line colour scales
#     seq_warm = ["#F0EAE3", "#C4909F", "#B07A8A"],
#     seq_cool = ["#EAF0EA", "#7AAF7A", "#4A7C4A"],
# )
 
# DARK = dict(
#     bg       = "#1C1714",
#     paper    = "#2A2320",
#     grid     = "#3D3330",
#     text     = "#EDE8E3",
#     axis     = "#8C7D76",
#     accent   = "#C4909F",
#     seq_warm = ["#3D3330", "#C4909F", "#EDE8E3"],
#     seq_cool = ["#1A3A20", "#7AAF7A", "#A5D6A7"],
# )
 
 
# def detect_dark_mode() -> bool:
#     """
#     Returns True when the app is running in dark mode.
 
#     Strategy:
#       1. Check st.session_state (set by the toggle snippet below).
#       2. Fall back to False (light) — matches config.toml base="light".
 
#     Call inject_theme_detector() once near the top of app.py so the
#     JS toggle can write back into session state.
#     """
#     return st.session_state.get("krach_dark", False)
 
 
# def inject_theme_detector():
#     """
#     Injects a tiny JS bridge that:
#       - Reads Streamlit's [data-theme] attribute on <html> (set automatically
#         when the user switches via the ☀/🌙 button in Streamlit ≥ 1.35).
#       - Adds / removes the body.krach-dark class so CSS vars update instantly.
#       - Posts the value back to Streamlit via the URL hash so Python can read it
#         on the next rerun (avoids needing a real custom component).
 
#     Place this call once, before any chart is rendered:
#         inject_theme_detector()
#     """
#     components.html(
#         """
#         <script>
#         (function() {
#             function syncTheme() {
#                 const html = window.parent.document.documentElement;
#                 const body = window.parent.document.body;
#                 const isDark = html.getAttribute('data-theme') === 'dark';
#                 if (isDark) {
#                     body.classList.add('krach-dark');
#                 } else {
#                     body.classList.remove('krach-dark');
#                 }
#             }
#             syncTheme();
#             // Re-sync whenever Streamlit swaps the theme attribute
#             const obs = new MutationObserver(syncTheme);
#             obs.observe(window.parent.document.documentElement, {
#                 attributes: true, attributeFilter: ['data-theme']
#             });
#         })();
#         </script>
#         """,
#         height=0,
#     )
 
 
# def palette() -> dict:
#     """Return the active palette dict."""
#     return DARK if detect_dark_mode() else LIGHT
 
 
# def plot_layout(**extra) -> dict:
#     """
#     Returns a Plotly layout dict wired to the current theme.
#     Pass any extra keys to override defaults.
 
#     Usage:
#         fig = px.bar(df, x="Month", y="Avg Rating")
#         fig.update_layout(**plot_layout(yaxis_range=[0, 5]))
#     """
#     p = palette()
#     base = dict(
#         plot_bgcolor  = p["bg"],
#         paper_bgcolor = p["paper"],
#         font          = dict(family="Fraunces, sans-serif", color=p["text"]),
#         title_font    = dict(family="Fraunces, serif", color=p["text"], size=18),
#         xaxis         = dict(gridcolor=p["grid"], color=p["axis"],
#                              linecolor=p["grid"], zerolinecolor=p["grid"]),
#         yaxis         = dict(gridcolor=p["grid"], color=p["axis"],
#                              linecolor=p["grid"], zerolinecolor=p["grid"]),
#         coloraxis_showscale = False,
#         legend        = dict(bgcolor=p["paper"], font=dict(color=p["text"])),
#         margin        = dict(t=48, b=24, l=8, r=8),
#     )
#     base.update(extra)
#     return base
 
 
# def warm_scale() -> list:
#     """Colour scale for ratings / warm metrics."""
#     return palette()["seq_warm"]
 
 
# def cool_scale() -> list:
#     """Colour scale for completion / positive metrics."""
#     return palette()["seq_cool"]