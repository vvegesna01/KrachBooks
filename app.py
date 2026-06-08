"""
KrachBooks — main entry point.

Tab layout:
  📊 Dashboard   — club-wide stats
  📚 Books       — cover wall + book deep dive
  ✏️ Check-in    — monthly check-in form
  🗳️ Vote        — voting (members) OR curator panel (current curator only)
  🏅 My Profile  — personal badges & stats
"""

import streamlit as st

# ── Page config must be FIRST ─────────────────────────────────────────────────
st.set_page_config(
    page_title="KrachBooks 📚",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
def load_css(path="styles.css"):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ── Auth ──────────────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown(
        '<div class="main-header">📚 KrachBooks</div>'
        '<div class="sub-header">your book club, tracked.</div>',
        unsafe_allow_html=True,
    )
    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("<br>", unsafe_allow_html=True)
        pwd = st.text_input("Club Password", type="password", placeholder="enter the secret…")
        if st.button("Unlock 🔓", use_container_width=True):
            if pwd == st.secrets["app"]["password"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong password. Try again!")
    st.stop()

# ── Imports ───────────────────────────────────────────────────────────────────
from utils.gsheet_ops import get_data, get_config
from utils.ui import (
    render_dashboard, render_cover_wall,
    render_checkin_form, render_voting_form,
    render_curator_panel, render_profile,
    MEMBERS,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">📚 KrachBooks</div>'
    '<div class="sub-header">some krached stats, and badges</div>',
    unsafe_allow_html=True,
)

# ── Load config first so we can determine role before anything else ───────────
config          = get_config()
current_curator = config.get("current_curator", "").strip().lower()
current_book    = config.get("current_book", "No book selected yet")
voting_open     = config.get("voting_open", "False").lower() == "true"

# ── User selection ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 👤 Who are you?")
    user = st.selectbox(
        "Select your name",
        ["— select —"] + MEMBERS,
        label_visibility="collapsed",
    )
    if user and user != "— select —":
        st.session_state.user = user
        # Role label uses config, not the hardcoded CURATORS list
        role_label = "✨ Curator" if user.strip().lower() == current_curator else "Member <3"
        st.markdown(f"**Role:** {role_label}")
    st.markdown("---")
    if st.button("🔒 Log out"):
        st.session_state.authenticated = False
        st.session_state.pop("user", None)
        st.rerun()

# ── Require user selection ────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user == "— select —":
    st.info("👈 Select your name from the sidebar to get started.")
    st.stop()

user       = st.session_state.user
# is_curator = True ONLY for the current month's curator read from Config
is_curator = user.strip().lower() == current_curator

# ── Load shared data ──────────────────────────────────────────────────────────
checkins_df = get_data("Checkins")

# ── Tabs ──────────────────────────────────────────────────────────────────────
vote_tab_label = "✨ Curator" if is_curator else "🗳️ Vote"
tabs = st.tabs(["📊 Dashboard", "📚 Books", "✏️ Check-in", vote_tab_label, "🏅 My Profile"])

with tabs[0]:
    render_dashboard(checkins_df, config)

with tabs[1]:
    render_cover_wall(checkins_df)

with tabs[2]:
    render_checkin_form(user, config)

with tabs[3]:
    if is_curator:
        render_curator_panel(user, config)
    else:
        if voting_open:
            render_voting_form(user, config)
        else:
            st.markdown('<div class="section-title">🗳️ Voting</div>', unsafe_allow_html=True)
            st.info(f"Voting is currently closed. The book for this month is: **{current_book}**")

with tabs[4]:
    render_profile(user)