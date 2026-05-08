import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path

import base64
import re
import calendar
import urllib.request
import json

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
# COLUMN PATTERNS
# ──────────────────────────────────────────────────────────────────────────────
COL_PATTERNS = {
    "name": ["name", "tag", "your name"],
    "finished": ["reading status", "finished", "completed"],
    "days": ["time to read", "days"],
    "format": ["format"],
    "rating": ["rating", "rate"],
    "quotes": ["quote", "favorite quote", "favourite quote"],
    "vote": ["vote", "next month"],
}

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def match_col(df, key):
    for col in df.columns:
        if any(p in col.lower() for p in COL_PATTERNS.get(key, [key])):
            return col
    return None


def parse_rating(val):
    if pd.isna(val):
        return None

    match = re.search(r"(\d+(?:\.\d+)?)", str(val))
    return float(match.group(1)) if match else None


def is_finished(val):
    if pd.isna(val):
        return False

    return any(
        w in str(val).lower()
        for w in ["yes", "finished", "done", "complete", "read"]
    )


def normalize_df(df):
    df = df.copy()

    rating_col = match_col(df, "rating")
    finished_col = match_col(df, "finished")
    name_col = match_col(df, "name")

    df["_rating"] = df[rating_col].apply(parse_rating) if rating_col else None

    df["_finished"] = (
        df[finished_col].apply(is_finished)
        if finished_col
        else False
    )

    df["_name"] = (
        df[name_col].fillna("Anonymous").str.strip()
        if name_col
        else "Anonymous"
    )

    return df


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

    icon_name = "military_tech" if earned else "lock"

    return f"""
    <div class="badge-placeholder">
        <span class="material-icons">{icon_name}</span>
    </div>
    """


# ──────────────────────────────────────────────────────────────────────────────
# OPENLIBRARY LOOKUP
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def fetch_book_info(isbn: str):
    try:
        url = (
            f"https://openlibrary.org/api/books"
            f"?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        )

        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode())

        key = f"ISBN:{isbn}"

        if key not in data:
            return None, None, None

        book = data[key]

        title = book.get("title")

        authors_list = book.get("authors", [])

        author_name = (
            authors_list[0].get("name")
            if authors_list
            else "Unknown Author"
        )

        covers = book.get("cover", {})

        cover_url = (
            covers.get("large")
            or covers.get("medium")
            or covers.get("small")
        )

        return title, cover_url, author_name

    except Exception:
        return None, None, None


# ──────────────────────────────────────────────────────────────────────────────
# LOAD CSV DATA
# ──────────────────────────────────────────────────────────────────────────────
def load_from_data_folder():
    months = {}

    if not DATA_DIR.exists():
        return months

    for csv_path in sorted(DATA_DIR.glob("*.csv")):
        stem = csv_path.stem

        isbn = None
        book_label = None

        match = re.match(r"^(\d{4})-(\d{2})_(.+)$", stem)

        if match:
            year, month_num, rest = match.groups()

            month_label = (
                f"{calendar.month_name[int(month_num)]} {year}"
            )

            candidate = re.sub(r"[^0-9X]", "", rest.upper())

            if len(candidate) in (10, 13):
                isbn = candidate
            else:
                book_label = (
                    rest.replace("_", " ")
                    .replace("-", " ")
                )

        else:
            parts = stem.replace("_", " ").split(" ", 1)

            month_label = parts[0]

            book_label = (
                parts[1]
                if len(parts) > 1
                else "Unknown Book"
            )

        try:
            df = pd.read_csv(csv_path)
            df = normalize_df(df)

            months[month_label] = {
                "df": df,
                "book": book_label or "Loading...",
                "isbn": isbn,
                "cover_url": None,
                "author": None,
            }

        except Exception as e:
            st.warning(f"Could not load {csv_path.name}: {e}")

    return months


# ──────────────────────────────────────────────────────────────────────────────
# SESSION
# ──────────────────────────────────────────────────────────────────────────────
st.session_state.months = load_from_data_folder()

for data in st.session_state.months.values():
    if data.get("isbn"):
        title, cover_url, author = fetch_book_info(data["isbn"])

        data["book"] = title or f"ISBN {data['isbn']}"
        data["cover_url"] = cover_url
        data["author"] = author or "Unknown Author"

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────────────
# MAIN HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="main-header">KrachBooks</div>
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
    "By Month",
    "Quotes",
    "My Badges",
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
                    Months Tracked
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
# BY MONTH
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown(
        """
        <div class="section-title">
            <span class="material-icons">
                calendar_month
            </span>
            Monthly Deep Dive
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_month = st.selectbox(
        "Select a month",
        list(st.session_state.months.keys()),
    )

    if selected_month:
        data = st.session_state.months[selected_month]

        df = data["df"]
        book = data["book"]

        author = data.get("author")
        cover_url = data.get("cover_url")

        n_total = len(df)
        n_finished = int(df["_finished"].sum())

        avg_rating = df["_rating"].dropna().mean()

        avg_str = (
            f"{avg_rating:.1f} ⭐"
            if not pd.isna(avg_rating)
            else "—"
        )

        cover_col, info_col = st.columns([1, 4])

        with cover_col:
            if cover_url:
                st.image(cover_url, width=250)

        with info_col:
            st.markdown(f"## {book}")

            if author:
                st.markdown(f"**By: {author}**")

            st.markdown(
                f"""
                **{selected_month}**
                • {n_finished}/{n_total} finished
                • {avg_str} average rating
                """
            )

        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-number">
                        {n_total}
                    </div>
                    <div class="stat-label">
                        Responses
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
                        {n_finished}
                    </div>
                    <div class="stat-label">
                        Members Finished
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-number">
                        {avg_str}
                    </div>
                    <div class="stat-label">
                        Avg Rating
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        left, right = st.columns(2)

        with left:
            ratings = df["_rating"].dropna()

            if not ratings.empty:
                fig_hist = px.histogram(
                    ratings,
                    x=ratings,
                    nbins=10,
                    title="Rating Distribution",
                    color_discrete_sequence=[
                        THEME["accent"]
                    ],
                )

                fig_hist.update_layout(
                    **plot_layout(
                        xaxis_title="Rating",
                        yaxis_title="Count",
                    )
                )

                st.plotly_chart(
                    fig_hist,
                    use_container_width=True,
                )

        with right:
            fmt_col = match_col(df, "format")

            if fmt_col:
                fmt_counts = (
                    df[fmt_col]
                    .value_counts()
                    .reset_index()
                )

                fmt_counts.columns = [
                    "Format",
                    "Count",
                ]

                fig_fmt = px.pie(
                    fmt_counts,
                    names="Format",
                    values="Count",
                    title="Format Breakdown",
                    color_discrete_sequence=THEME["palette"],
                )

                fig_fmt.update_layout(
                    **plot_layout()
                )

                st.plotly_chart(
                    fig_fmt,
                    use_container_width=True,
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
        finished_2025   = 0
        finished_2026   = 0

        for month, data in st.session_state.months.items():
            df     = data["df"]
            m_rows = df[df["_name"].str.lower() == member_clean]
            if not m_rows.empty and m_rows["_finished"].any():
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

        n_finished   = len(finished_months)
        n_total      = len(all_months)
        fastest_read = min(member_speeds) if member_speeds else 999

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

        curators_list = ["lightspeed", "pranjal", "nitarek", "kd", "ani", "potato365", "smrithi"]
        special_badges = [
            ("curator",       "Trusted Curator",
             member_clean in curators_list),
            ("champion_2025", "2025 Completely Krached",
             finished_2025 >= len(months_2025) and len(months_2025) > 0),
            ("champion_2026", "2026 Completely Krached",
             finished_2026 >= len(months_2026) and len(months_2026) > 0),
            ("speed_demon",   "Speed Demon (< 3 days)",
             fastest_read < 3),
            ("loyalist",      "Loyal Krachhead (12+)",
             n_finished >= 12),
            ("bookworm",      "Bookworm (5+ books)",
             n_finished >= 5),
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
            (f"book_{i}", st.session_state.months[month]["book"], month in finished_months)
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