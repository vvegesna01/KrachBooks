import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import base64
import re
import calendar
import urllib.request
import json

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KrachBooks",
    page_icon="auto_stories",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Midnight Ink theme styling ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Lato:wght@300;400;700&display=swap');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');

.material-icons {
    font-family: 'Material Icons';
    font-weight: normal;
    font-style: normal;
    font-size: 24px;
    display: inline-block;
    line-height: 1;
    text-transform: none;
    letter-spacing: normal;
    word-wrap: normal;
    white-space: nowrap;
    direction: ltr;
    vertical-align: middle;
}

html, body, [class*="stApp"], .main, section[data-testid="stSidebar"] {
    background-color: #1A1A2E !important;
    color: #E0E0E0 !important;
    font-family: 'Lato', sans-serif;
}
section[data-testid="stSidebar"] {
    background-color: #16213E !important;
    border-right: 1px solid #0F3460;
}
section[data-testid="stSidebar"] * { color: #E0E0E0 !important; }

.main-header {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    font-weight: 900;
    color: #00B4D8;
    letter-spacing: -1px;
    line-height: 1.1;
}
.sub-header {
    font-family: 'Lato', sans-serif;
    font-weight: 300;
    color: #6B7280;
    font-size: 1.1rem;
    margin-top: -0.5rem;
}
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #E0E0E0;
    border-bottom: 3px solid #00B4D8;
    padding-bottom: 0.3rem;
    margin-bottom: 1rem;
}
.stat-card {
    background: #0F3460;
    border-radius: 16px;
    padding: 1.5rem;
    border: 1px solid #0F3460;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    text-align: center;
}
.stat-number {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 900;
    color: #00B4D8;
    line-height: 1;
}
.stat-label {
    font-size: 0.8rem;
    color: #6B7280;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.4rem;
}
.quote-card {
    background: #16213E;
    border-left: 4px solid #00B4D8;
    padding: 1rem 1.5rem;
    border-radius: 0 12px 12px 0;
    margin: 0.5rem 0;
    font-style: italic;
    color: #E0E0E0;
}
/* ── Badge animations ── */
@keyframes badgeEntrance {
    0%   { opacity: 0; transform: scale(0.4) rotate(-15deg); }
    60%  { transform: scale(1.15) rotate(4deg); }
    80%  { transform: scale(0.95) rotate(-2deg); }
    100% { opacity: 1; transform: scale(1) rotate(0deg); }
}
@keyframes badgeFloat {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    33%       { transform: translateY(-6px) rotate(1.5deg); }
    66%       { transform: translateY(-3px) rotate(-1deg); }
}
@keyframes electricPulse {
    0%, 100% { box-shadow: 0 0 12px 4px rgba(0,180,216,0.3), 0 0 0 0 rgba(0,180,216,0); }
    50%       { box-shadow: 0 0 24px 8px rgba(0,180,216,0.6), 0 0 40px 12px rgba(0,180,216,0.2); }
}
@keyframes lockedWobble {
    0%, 100% { transform: rotate(0deg); }
    25%       { transform: rotate(-3deg); }
    75%       { transform: rotate(3deg); }
}

.badge-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5rem 0.5rem;
    border-radius: 10px;
    cursor: default;
    transition: background 0.3s ease;
    position: relative;
}
.badge-wrap:hover {
    background: rgba(0,180,216,0.08);
}

.badge-img-earned {
    animation:
        badgeEntrance 0.7s cubic-bezier(0.34,1.56,0.64,1) both,
        badgeFloat 4s ease-in-out 0.7s infinite;
    filter: drop-shadow(0 6px 16px rgba(0,180,216,0.55))
            drop-shadow(0 2px 4px rgba(0,0,0,0.6));
    transition: transform 0.2s ease, filter 0.2s ease;
}
.badge-img-earned:hover {
    animation: none;
    transform: scale(1.18) rotate(-3deg);
    filter: drop-shadow(0 10px 28px rgba(0,180,216,0.9))
            drop-shadow(0 4px 8px rgba(0,0,0,0.7));
}

.badge-img-locked {
    filter: grayscale(100%) opacity(0.2) brightness(0.4);
    animation: badgeEntrance 0.5s ease both, lockedWobble 6s ease-in-out 1s infinite;
    transition: filter 0.3s ease;
}
.badge-img-locked:hover {
    filter: grayscale(80%) opacity(0.35) brightness(0.5);
}

/* Shimmer ring around earned badges */
.badge-glow {
    position: relative;
    display: inline-block;
    z-index: 1; 
}

.badge-glow::before {
    content: '';
    position: absolute;
    inset: -10px; 
    border-radius: 50%;
    background: radial-gradient(circle, 
        rgba(0,180,216,0.7) 0%, 
        rgba(0,180,216,0.3) 45%, 
        transparent 70%
    );
    background-size: 200% 200%;
    animation: electricPulse 3s ease-in-out infinite;
    z-index: -1;
    pointer-events: none;
}
            
.badge-glow-square {
    position: relative;
    display: inline-block;
    z-index: 1;
}

.badge-glow-square::before {
    content: '';
    position: absolute;
    inset: -3px; 
    border-radius: 6px;
    background: radial-gradient(color, 
        rgba(0,180,216,0.4) 0%, 
        transparent 80%
    );
    animation: electricPulse 3s ease-in-out infinite;
    z-index: -1;
    pointer-events: none;
}

/* Ensure the image itself doesn't get clipped into a circle */
.img-square {
    border-radius: 6px !important;
    object-fit: cover;
}

.badge-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: #E0E0E0;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    text-align: center;
    line-height: 1.3;
}
.badge-status-earned {
    font-size: 0.72rem;
    color: #48BB78;
    font-weight: 700;
    margin-top: 0.15rem;
}
.badge-status-locked {
    font-size: 0.72rem;
    color: #6B7280;
    font-weight: 600;
    margin-top: 0.15rem;
}
.stTabs [data-baseweb="tab-list"] {
    background-color: #16213E;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Lato', sans-serif;
    font-weight: 700;
    color: #6B7280 !important;
    border-radius: 8px;
}
.stTabs [aria-selected="true"] {
    background-color: #0F3460 !important;
    color: #E0E0E0 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #00B4D8 !important;
}
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background-color: #16213E !important;
    border-color: #0F3460 !important;
    color: #E0E0E0 !important;
}
p, li, span, label { color: #E0E0E0; }
h1, h2, h3, h4 {
    color: #E0E0E0 !important;
    font-family: 'Playfair Display', serif;
}
hr { border-color: #0F3460; }
.book-cover-placeholder {
    width: 100px;
    height: 150px;
    background: linear-gradient(135deg, #16213E, #0F3460);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Plot theme ────────────────────────────────────────────────────────────────
PLOT_BG  = "#1A1A2E"
FONT_CLR = "#E0E0E0"
GRID_CLR = "#EDE8E0"
ACCENT   = "#00B4D8"



def dark_layout(**extra):
    base = dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PLOT_BG,
        font=dict(family="Lato", color=FONT_CLR),
        title_font=dict(family="Playfair Display", color=FONT_CLR, size=18),
        xaxis=dict(gridcolor=GRID_CLR, color=FONT_CLR, linecolor=GRID_CLR),
        yaxis=dict(gridcolor=GRID_CLR, color=FONT_CLR, linecolor=GRID_CLR),
        coloraxis_showscale=False,
        legend=dict(bgcolor=PLOT_BG, font=dict(color=FONT_CLR)),
    )
    base.update(extra)
    return base

# ── Constants ─────────────────────────────────────────────────────────────────
ASSETS_DIR = Path(__file__).parent / "assets"
DATA_DIR   = Path(__file__).parent / "data"

COL_PATTERNS = {
    "name":        ["name", "tag", "your name"],
    "finished":    ["reading status", "finished", "completed"],
    "days":        ["time to read", "how many days", "days"],
    "format":      ["format"],
    "rating":      ["rating", "rate"],
    "quotes":      ["quote", "favourite quote", "favorite quote"],
    "vote":        ["vote", "next month"],
}

def match_col(df, key):
    for col in df.columns:
        if any(p in col.lower() for p in COL_PATTERNS.get(key, [key])):
            return col
    return None

def parse_rating(val):
    if pd.isna(val):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", str(val))
    return float(m.group(1)) if m else None

def is_finished(val):
    if pd.isna(val):
        return False
    return any(w in str(val).lower() for w in ["yes", "finished", "done", "complete", "read"])

def normalize_df(df):
    df = df.copy()
    rc = match_col(df, "rating")
    fc = match_col(df, "finished")
    nc = match_col(df, "name")
    df["_rating"]   = df[rc].apply(parse_rating) if rc else None
    df["_finished"] = df[fc].apply(is_finished)  if fc else False
    df["_name"]     = df[nc].fillna("Anonymous").str.strip() if nc else "Anonymous"
    return df

def svg_to_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def load_badge(badge_id, earned=True, size=140, shape="circle"):
    for ext, mime in [("svg", "image/svg+xml"), ("png", "image/png")]:
        p = ASSETS_DIR / f"{badge_id}.{ext}"
        if p.exists():
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            delay = abs(hash(badge_id)) % 600
            
            # Determine classes based on shape
            css_main = "badge-img-earned" if earned else "badge-img-locked"
            if shape == "square":
                css_main += " img-square"
                glow_class = "badge-glow-square"
            else:
                glow_class = "badge-glow"

            img = f'<img src="data:{mime};base64,{b64}" width="{size}" class="{css_main}" style="animation-delay:{delay}ms"/>'
            
            if earned:
                return f'<span class="{glow_class}">{img}</span>'
            return img
            
    # Fallback remains the same
    icon_name = "lock" if not earned else "military_tech"
    fallback_icon = f'<span class="material-icons" style="font-size: 48px; color: #E53E3E;">{icon_name}</span>'
    return f'<div style="width:{size}px;height:{size}px;background:#EDE8E0;border-radius:{"4px" if shape=="square" else "50%"};display:flex;align-items:center;justify-content:center;font-size:2.5rem;opacity:0.5">{fallback_icon}</div>'

# ── OpenLibrary lookup ────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def fetch_book_info(isbn: str):
    try:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode())
        key  = f"ISBN:{isbn}"
        if key not in data:
            return None, None, None # Added third None for author
        book      = data[key]
        title     = book.get("title")
        # Extract author name
        authors_list = book.get("authors", [])
        author_name = authors_list[0].get("name") if authors_list else "Unknown Author"
        
        covers    = book.get("cover", {})
        cover_url = covers.get("large") or covers.get("medium") or covers.get("small")
        return title, cover_url, author_name
    except Exception:
        return None, None, None

# ── Load CSVs ─────────────────────────────────────────────────────────────────
def load_from_data_folder():
    months = {}
    if not DATA_DIR.exists():
        return months
    for csv_path in sorted(DATA_DIR.glob("*.csv")):
        stem  = csv_path.stem
        isbn  = None
        book_label = None

        m = re.match(r"^(\d{4})-(\d{2})_(.+)$", stem)
        if m:
            year, month_num, rest = m.groups()
            month_label = f"{calendar.month_name[int(month_num)]} {year}"
            candidate   = re.sub(r"[^0-9X]", "", rest.upper())
            if len(candidate) in (10, 13):
                isbn = candidate
            else:
                book_label = rest.replace("_", " ").replace("-", " ")
        else:
            m2 = re.match(r"^\d+_([^_]+)_(.+)$", stem)
            if m2:
                month_label = m2.group(1)
                book_label  = m2.group(2).replace("_", " ").replace("-", " ")
            else:
                parts = stem.replace("_", " ").split(" ", 1)
                month_label = parts[0]
                book_label  = parts[1] if len(parts) > 1 else "Unknown Book"

        try:
            df = pd.read_csv(csv_path)
            df = normalize_df(df)
            months[month_label] = {
                "df":        df,
                "book":      book_label or "Loading…",
                "isbn":      isbn,
                "cover_url": None,
            }
        except Exception as e:
            st.warning(f"Could not load {csv_path.name}: {e}")
    return months

# ── Session + ISBN resolution ─────────────────────────────────────────────────
st.session_state.months = load_from_data_folder()

for data in st.session_state.months.values():
    if data.get("isbn"):
        title, cover_url, author = fetch_book_info(data["isbn"])
        data["book"]      = title or f"ISBN {data['isbn']}"
        data["cover_url"] = cover_url
        data["author"]    = author or "Unknown Author"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="main-header">KrachBooks <span class="material-icons" style="font-size: 3rem; color: #E53E3E;">auto_stories</span></div>', unsafe_allow_html=True)
    st.markdown("---")
    if st.session_state.months:
        st.markdown('<div class="section-title"><span class="material-icons">calendar_month</span>Months Loaded</div>', unsafe_allow_html=True)
        for m, d in st.session_state.months.items():
            st.markdown(f"- **{m}** — _{d['book']}_")
    else:
        st.info("No CSVs in `/data`.\nName files like:\n`2025-01_[isbn].csv`")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">KrachBooks <span class="material-icons" style="font-size: 3rem; color: #E53E3E;">auto_stories</span></div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">some krached stats, and badges!</div>', unsafe_allow_html=True)

if not st.session_state.months:
    st.warning(f"No CSV files found in `{DATA_DIR}`. Add files and refresh!")
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["Dashboard", "By Month", "Quotes", "My Badges"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-title"><span class="material-icons">leaderboard</span> Club Overview</div>', unsafe_allow_html=True)

    rows = []
    for month, data in st.session_state.months.items():
        df         = data["df"]
        n_total    = len(df)
        n_finished = int(df["_finished"].sum())
        avg_rating = df["_rating"].dropna().mean()
        rows.append({
            "Month":          month,
            "Book":           data["book"],
            "Active Members": n_total,
            "Author":         data.get("author", "Unknown"),
            "Finished":       n_finished,
            "% Finished":     round(n_finished / n_total * 100, 1) if n_total > 0 else 0,
            "Avg Rating":     round(avg_rating, 2) if not pd.isna(avg_rating) else None,
        })

    summary        = pd.DataFrame(rows)
    total_active   = 17
    overall_avg    = summary["Avg Rating"].dropna().mean()
    best_row       = summary.loc[summary["Avg Rating"].idxmax()] if summary["Avg Rating"].notna().any() else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{len(st.session_state.months)}</div>
            <div class="stat-label">Months Tracked</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{total_active}</div>
            <div class="stat-label">Active Members</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        avg_str = f"{overall_avg:.1f} ⭐" if not pd.isna(overall_avg) else "—"
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{avg_str}</div>
            <div class="stat-label">Overall Avg Rating</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        best_title = best_row["Book"] if best_row is not None else "—"
        best_author = best_row["Author"] if best_row is not None else ""
        title_short = best_title[:18] + "…" if len(best_title) > 18 else best_title
    
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number" style="font-size:2.4rem">{title_short}</div>
            <div class="stat-label">{best_author}</div> 
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        # Keeping Completion Rate as a Bar Chart for clear comparison
        fig2 = px.bar(
            summary, x="Month", y="% Finished",
            text="% Finished",
            color="% Finished",
            color_continuous_scale=["#16213E", "#00B4D8"], # Dark navy to Bright blue
            title="Completion Rate by Month",
        )
        fig2.update_traces(texttemplate="%{text}%", textposition="outside",
                            textfont_color="#E0E0E0")
        fig2.update_layout(**dark_layout(yaxis=dict(range=[0, 110])))
        st.plotly_chart(fig2, use_container_width=True)  

    with col_right:
        # Aggregate ALL ratings across all months
        all_ratings = []
        for m_data in st.session_state.months.values():
            m_ratings = m_data["df"]["_rating"].dropna().tolist()
            all_ratings.extend(m_ratings)
        
        if all_ratings:
            # Round ratings to nearest whole star for the breakdown
            rating_df = pd.DataFrame({"Stars": [f"{int(round(r))} Star" for r in all_ratings]})
            breakdown = rating_df["Stars"].value_counts().reset_index()
            breakdown.columns = ["Rating", "Count"]
            breakdown = breakdown.sort_values("Rating", ascending=False)

            midnight_colors = ["#00B4D8", "#90E0EF", "#F5D9A8", "#0F3460", "#16213E"]
            
            fig = px.pie(
                breakdown,
                names="Rating", 
                values="Count",
                title="Ratings Breakdown",
                color_discrete_sequence=midnight_colors
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(**dark_layout())
            st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">Month Summary</div>', unsafe_allow_html=True)
    disp = summary.copy()
    disp["Avg Rating"] = disp["Avg Rating"].apply(lambda x: f"{x:.2f} ⭐" if pd.notna(x) else "—")
    disp["% Finished"] = disp["% Finished"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(disp, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BY MONTH
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-title"><span class="material-icons">calendar_month</span> Monthly Deep Dive</div>', unsafe_allow_html=True)
    selected_month = st.selectbox("Select a month", list(st.session_state.months.keys()))

    if selected_month:
        data       = st.session_state.months[selected_month]
        df         = data["df"]
        book       = data["book"]
        author    =  data.get("author")
        cover_url  = data.get("cover_url")
        n_total    = len(df)
        n_finished = int(df["_finished"].sum())
        avg_rating = df["_rating"].dropna().mean()
        avg_str    = f"{avg_rating:.1f} ⭐" if not pd.isna(avg_rating) else "—"

        # Book header with cover
        cover_col, info_col = st.columns([1, 4])
        with cover_col:
            if cover_url:
                st.image(cover_url, width=320)
            else:
                st.markdown('<div class="book-cover-placeholder">📖</div>', unsafe_allow_html=True)
        with info_col:
            st.markdown(f"### {book}")
            st.markdown(f"**By: {author}**")
            st.markdown(f"**{selected_month}** &nbsp;|&nbsp; {n_finished}/{n_total} members finished &nbsp;|&nbsp; {avg_str} avg")

        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="stat-card">
                <div class="stat-number">{n_total}</div>
                <div class="stat-label">Responses</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="stat-card">
                <div class="stat-number">{n_finished} / {n_total}</div>
                <div class="stat-label">Members Finished</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="stat-card">
                <div class="stat-number">{avg_str}</div>
                <div class="stat-label">Avg Rating</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)

        with col_a:
            ratings = df["_rating"].dropna()
            if not ratings.empty:
                fig = px.histogram(ratings, x=ratings, nbins=10,
                                   title="Rating Distribution",
                                   color_discrete_sequence=[ACCENT])
                fig.update_layout(**dark_layout(xaxis_title="Rating", yaxis_title="Count"))
                st.plotly_chart(fig, use_container_width=True)

        with col_b:
            fmt_col = match_col(df, "format")
            if fmt_col:
                fmt_counts = df[fmt_col].value_counts().reset_index()
                fmt_counts.columns = ["Format", "Count"]
                # Midnight Ink Palette: Blues, Deep Navy, and Soft Gold
                midnight_colors = ["#00B4D8", "#0F3460", "#16213E", "#F5D9A8", "#90E0EF"]
                
                fig2 = px.pie(fmt_counts, names="Format", values="Count",
                            title="Format Breakdown",
                            color_discrete_sequence=midnight_colors)
                
                fig2.update_traces(textposition='inside', textinfo='percent+label', 
                                marker=dict(line=dict(color='#1A1A2E', width=2)))
                fig2.update_layout(**dark_layout())
                st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — QUOTES
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="section-title"><span class="material-icons">format_quote</span> Favourite Quotes</div>', unsafe_allow_html=True)

    for month, data in st.session_state.months.items():
        df        = data["df"]
        book      = data["book"]
        quote_col = match_col(df, "quotes")
        if not quote_col:
            continue
        with st.expander(f"📖 {book} — {month}"):
            found = False
            for _, row in df.iterrows():
                q = str(row.get(quote_col, "")).strip()
                if q and q.lower() not in ["nan", "", "none", "-"]:
                    found = True
                    st.markdown(
                        f'<div class="quote-card">"{q}"<br><small>— {row["_name"]}</small></div>',
                        unsafe_allow_html=True,
                    )
            if not found:
                st.caption("No quotes shared for this month.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MY BADGES 
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-title"><span class="material-icons">workspace_premium</span> My Badges</div>', unsafe_allow_html=True)
    st.markdown("Enter your name/tag below to see which badges you've earned!")

    member_name = st.text_input("Your name or tag", placeholder="e.g. Krached Keval")

    if member_name:
        member_clean = member_name.strip().lower()
        all_months = list(st.session_state.months.keys())
        
        # Data gathering for logic
        finished_months = []
        member_speeds = []
        months_2025 = [m for m in all_months if "2025" in m]
        months_2026 = [m for m in all_months if "2026" in m]
        
        finished_2025 = 0
        finished_2026 = 0

        for month, data in st.session_state.months.items():
            df = data["df"]
            # Look for the specific member
            m_rows = df[df["_name"].str.lower() == member_clean]
            
            if not m_rows.empty and m_rows["_finished"].any():
                finished_months.append(month)
                
                # Check for Year-specific counts
                if "2025" in month: finished_2025 += 1
                if "2026" in month: finished_2026 += 1
                
                # Check for Speed Demon (less than 3 days)
                days_col = match_col(df, "days")
                if days_col:
                    try:
                        days_val = float(m_rows[days_col].iloc[0])
                        member_speeds.append(days_val)
                    except: pass

        n_finished = len(finished_months)
        n_total = len(all_months)
        fastest_read = min(member_speeds) if member_speeds else 999

        # Stats Cards
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

        # --- Section 1: Special Badges ---
        # st.markdown("### <span class="material-icons" style='vertical-align:bottom'>stars</span> Special Achievements")
        st.markdown('<div class="section-title"><span class="material-icons">stars</span> Special Achievements</div>', unsafe_allow_html=True)
        curators_list = ["lightspeed", "pranjal", "nitarek", "kd", "ani", "potato365", "smrithi", ]
        
        special_badges = [
            ("champion_2025", "2025 Completely Krached", finished_2025 >= len(months_2025) and len(months_2025) > 0),
            ("champion_2026", "2026 Completely Krached", finished_2026 >= len(months_2026) and len(months_2026) > 0),
            ("curator", "Trusted Curator", member_clean in curators_list),
            ("speed_demon", "Speed Demon (< 3 days)", fastest_read < 3),
            ("loyalist", "Loyal Krachhead (12+ Months)", n_finished >= 12),
            ("bookworm", "Bookworm (5+ books)", n_finished >= 5),
        ]

        # Display Special Badges in a grid
        cols_per_row_special = 3
        for i in range(0, len(special_badges), cols_per_row_special):
            batch = special_badges[i : i + cols_per_row_special]
            cols = st.columns(cols_per_row_special)
            for ci, (badge_id, label, earned) in enumerate(batch):
                with cols[ci]:
                    img_html = load_badge(badge_id, earned=earned, size=150)
                    status_html = '<span class="badge-status-earned"> ★ Earned!</span>' if earned else '<span class="badge-status-locked">🔒 Locked</span>'
                    st.markdown(f"""<div class="badge-wrap">
                        <div>{img_html}</div>
                        <div class="badge-label">{label}</div>
                        {status_html}
                    </div>""", unsafe_allow_html=True)

        # --- Section 2: Monthly Badges ---
        st.markdown('<div class="section-title"><span class="material-icons">calendar_today</span> Monthly Collection</div>', unsafe_allow_html=True)
        # st.markdown("### <span class="material-icons" style='vertical-align:bottom'>calendar_today</span> Monthly Collection")
        month_badges = [
            (f"book_{i}", st.session_state.months[month]["book"], month in finished_months)
            for i, month in enumerate(all_months, 1)
        ]
        
        cols_per_row = 4
        for row_start in range(0, len(month_badges), cols_per_row):
            row_slice = month_badges[row_start : row_start + cols_per_row]
            cols = st.columns(cols_per_row)
            for ci, (badge_id, label, earned) in enumerate(row_slice):
                with cols[ci]:
                    img_html = load_badge(badge_id, earned=earned, size=150, shape="square")
                    status_html = '<span class="badge-status-earned"> ★ Earned!</span>' if earned else '<span class="badge-status-locked">🔒 Locked</span>'
                    st.markdown(f"""<div class="badge-wrap">
                        <div>{img_html}</div>
                        <div class="badge-label">{label[:26]}</div>
                        {status_html}
                    </div>""", unsafe_allow_html=True)

        if n_finished == 0 and member_clean not in curators_list:
            st.info(f"No finished books found for **{member_name}**. Ensure your name matches the form exactly!")