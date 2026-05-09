"""
data_parser.py
~~~~~~~~~~~~~~
Handles all CSV discovery, column normalisation, and OpenLibrary lookups
for KrachBooks.  app.py should import load_months() and nothing else.

Public API
----------
load_months(data_dir) -> dict[month_label, MonthData]

MonthData is a TypedDict:
    df         : pd.DataFrame   # normalised; always has _name, _finished, _rating
    book       : str            # resolved title (or ISBN fallback)
    isbn       : str | None
    cover_url  : str | None
    author     : str | None
"""

from __future__ import annotations

import calendar
import json
import re
import urllib.request
from pathlib import Path
from typing import TypedDict

import pandas as pd
import streamlit as st         

# ──────────────────────────────────────────────────────────────────────────────
# COLUMN PATTERNS
# Keys are short names used throughout the app; values are substrings to match
# against the raw (lower-cased) CSV column headers.
# ──────────────────────────────────────────────────────────────────────────────
COL_PATTERNS: dict[str, list[str]] = {
    "name":     ["name", "tag", "your name"],
    "finished": ["reading status", "finished", "completed"],
    "days":     ["time to read", "days"],
    "format":   ["format"],
    "rating":   ["rating", "rate"],
    "quotes":   ["quote", "review", "favorite quote", "favourite quote"],
    "vote":     ["vote", "next month"],
}


# ──────────────────────────────────────────────────────────────────────────────
# TypedDict for a single month's data
# ──────────────────────────────────────────────────────────────────────────────
class MonthData(TypedDict):
    df:        pd.DataFrame
    book:      str
    isbn:      str | None
    cover_url: str | None
    author:    str | None


# ──────────────────────────────────────────────────────────────────────────────
# LOW-LEVEL HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def match_col(df: pd.DataFrame, key: str) -> str | None:
    """Return the first column name whose header contains any pattern for *key*."""
    patterns = COL_PATTERNS.get(key, [key])
    for col in df.columns:
        if any(p in col.lower() for p in patterns):
            return col
    return None


def parse_rating(val) -> float | None:
    """Extract the first number from a rating cell (e.g. '4/5', '3 stars' → 4.0, 3.0)."""
    if pd.isna(val):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", str(val))
    return float(m.group(1)) if m else None


def is_finished(val) -> bool:
    """
    Return True only when the cell clearly indicates the book was finished.

    Handles common form responses:
        Finished  → True
        Yes       → True
        Done      → True
        Still reading / Currently reading / In progress / DNF  → False
    """
    if pd.isna(val):
        return False

    lowered = str(val).lower().strip()

    # Explicit not-finished phrases — checked before the positive keywords so
    # that e.g. "still reading" doesn't match the word "reading".
    not_finished: list[str] = [
        "still reading",
        "currently reading",
        "in progress",
        "not finished",
        "not done",
        "dnf",
        "did not finish",
    ]
    if any(phrase in lowered for phrase in not_finished):
        return False

    finished: list[str] = ["yes", "finished", "done", "complete", "read"]
    return any(w in lowered for w in finished)


# ──────────────────────────────────────────────────────────────────────────────
# NORMALISE A RAW CSV DataFrame
# ──────────────────────────────────────────────────────────────────────────────

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add three canonical columns to *df* (copy):

    _name      str    — member display name, never NaN
    _finished  bool   — whether the member finished the book
    _rating    float  — numeric rating, NaN when absent
    """
    df = df.copy()

    rating_col   = match_col(df, "rating")
    finished_col = match_col(df, "finished")
    name_col     = match_col(df, "name")

    df["_rating"] = (
        df[rating_col].apply(parse_rating)
        if rating_col
        else None
    )

    df["_finished"] = (
        df[finished_col].apply(is_finished)
        if finished_col
        else pd.Series([False] * len(df), index=df.index)
    )

    df["_name"] = (
        df[name_col].fillna("Anonymous").str.strip()
        if name_col
        else "Anonymous"
    )

    return df


# ──────────────────────────────────────────────────────────────────────────────
# OPENLIBRARY LOOKUP
# Cached per-ISBN so hot-reloads don't re-fetch.
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def fetch_book_info(isbn: str) -> tuple[str | None, str | None, str | None]:
    """
    Return (title, cover_url, author_name) for *isbn* via OpenLibrary.
    All three values are None on any error or missing data.
    """
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
        author_name = authors_list[0].get("name") if authors_list else "Unknown Author"

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
# FILENAME PARSER
# ──────────────────────────────────────────────────────────────────────────────

def _parse_stem(stem: str) -> tuple[str, str | None, str | None]:
    """
    Parse a CSV filename stem into (month_label, isbn_or_None, book_label_or_None).

    Supported formats
    -----------------
    2025-11_9780593135204   →  "November 2025", isbn="9780593135204", book=None
    2025-11_Some_Book_Title →  "November 2025", isbn=None, book="Some Book Title"
    anything else           →  stem as month_label, isbn=None, book="Unknown Book"
    """
    m = re.match(r"^(\d{4})-(\d{2})_(.+)$", stem)
    if m:
        year, month_num, rest = m.groups()
        month_label = f"{calendar.month_name[int(month_num)]} {year}"

        candidate = re.sub(r"[^0-9X]", "", rest.upper())
        if len(candidate) in (10, 13):
            return month_label, candidate, None

        book_label = rest.replace("_", " ").replace("-", " ")
        return month_label, None, book_label

    # Fallback: treat whole stem as label
    parts = stem.replace("_", " ").split(" ", 1)
    month_label = parts[0]
    book_label  = parts[1] if len(parts) > 1 else "Unknown Book"
    return month_label, None, book_label


# ──────────────────────────────────────────────────────────────────────────────
# MAIN PUBLIC FUNCTION
# ──────────────────────────────────────────────────────────────────────────────

def load_months(data_dir: Path | str | None = None) -> dict[str, MonthData]:
    """
    Discover every ``*.csv`` inside *data_dir*, parse and normalise each one,
    resolve book metadata via OpenLibrary where an ISBN is embedded in the
    filename, and return an ordered dict keyed by month label.

    Parameters
    ----------
    data_dir:
        Directory to scan.  Defaults to a ``data/`` folder next to this file.

    Returns
    -------
    dict[str, MonthData]
        Keys are human-readable month labels, e.g. ``"November 2025"``.
        Values are :class:`MonthData` dicts ready for use in the dashboard.
    """
    if data_dir is None:
        data_dir = Path(__file__).parent / "data"

    data_dir = Path(data_dir)
    months: dict[str, MonthData] = {}

    if not data_dir.exists():
        return months

    for csv_path in sorted(data_dir.glob("*.csv")):
        month_label, isbn, book_label = _parse_stem(csv_path.stem)

        try:
            df = pd.read_csv(csv_path)
            df = normalize_df(df)
        except Exception as exc:
            # Surface the error in the Streamlit UI without crashing the app
            import streamlit as _st
            _st.warning(f"Could not load {csv_path.name}: {exc}")
            continue

        months[month_label] = MonthData(
            df=df,
            book=book_label or "Loading…",
            isbn=isbn,
            cover_url=None,
            author=None,
        )

    # Enrich entries that have an ISBN
    for data in months.values():
        if data["isbn"]:
            title, cover_url, author = fetch_book_info(data["isbn"])
            data["book"]      = title or f"ISBN {data['isbn']}"
            data["cover_url"] = cover_url
            data["author"]    = author or "Unknown Author"

    return months