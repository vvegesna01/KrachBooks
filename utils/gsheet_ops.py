import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from typing import Optional

SHEET_ID = "1Wb3GY9oRy2m-VRhQVemCfwX8SY-fdigkl1CUpGVClNc"


# ── READ (public CSV — no auth needed) ───────────────────────────────────────

@st.cache_data(ttl=30)
def get_data(worksheet_name: str) -> pd.DataFrame:
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/gviz/tq?tqx=out:csv&sheet={worksheet_name}"
    )
    try:
        return pd.read_csv(url)
    except Exception:
        return pd.DataFrame()

def get_config():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        ws = gc.open_by_key(SHEET_ID).worksheet("Config")
        records = ws.get_all_records()
        return {
            str(row["Key"]).strip(): str(row["Value"]).strip()
            for row in records
            if row.get("Key")
        }
    except Exception as e:
        st.error(f"Config load failed: {e}")
        return {}


def get_books_lookup():
    """
    Return Books sheet as {booktitle_lower: {isbn, cover_url}} dict.
    Used by the cover wall to pass ISBNs to the book API.
    """
    df = get_data("Books")
    if df.empty or "BookTitle" not in df.columns:
        return {}
    lookup = {}
    for _, row in df.iterrows():
        title = str(row.get("BookTitle", "")).strip().lower()
        if title:
            lookup[title] = {
                "isbn":      str(row.get("ISBN", "")).strip(),
                "cover_url": str(row.get("CoverURL", "")).strip(),
            }
    return lookup


# ── WRITE HELPERS (gspread — service account) ───


def _sheet(worksheet_name: str):
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    return gc.open_by_key(SHEET_ID).worksheet(worksheet_name)


def append_row(worksheet_name: str, data_list: list):
    _sheet(worksheet_name).append_row(data_list, value_input_option="USER_ENTERED")


def update_config(key: str, value: str):
    """Set a key in the Config sheet (upsert)."""
    ws = _sheet("Config")
    cell = ws.find(key)
    if cell:
        ws.update_cell(cell.row, 2, value)
    else:
        ws.append_row([key, value])
    get_data.clear()


def upsert_checkin(name: str, book_title: str, row_data: list):
    """
    If the user already has a check-in for this book, overwrite it.
    Otherwise append. row_data = [Timestamp, BookTitle, Name, Finished, DaysToRead, Format, Rating, Quote, Feedback]
    """
    ws = _sheet("Checkins")
    records = ws.get_all_values()
    headers = records[0] if records else []

    try:
        name_col  = headers.index("Name") + 1
        book_col  = headers.index("BookTitle") + 1
    except ValueError:
        ws.append_row(row_data, value_input_option="USER_ENTERED")
        get_data.clear()
        return

    for i, row in enumerate(records[1:], start=2):
        if (len(row) >= max(name_col, book_col) and
                row[name_col - 1].strip().lower() == name.strip().lower() and
                row[book_col - 1].strip().lower() == book_title.strip().lower()):
            ws.update(f"A{i}", [row_data])
            get_data.clear()
            return

    ws.append_row(row_data, value_input_option="USER_ENTERED")
    get_data.clear()


def upsert_vote(name: str, month: str, book_title: str,
                rank1: str, rank2: str, rank3: str):
    """
    One vote per member per month — overwrite if they change their mind.

    Votes sheet columns (in order):
        Timestamp | Month | BookTitle | VotedBy | Rank1 | Rank2 | Rank3

    book_title is a denormalised copy of rank1 (top pick) for easy per-book queries.
    """
    ws = _sheet("Votes")
    records = ws.get_all_values()
    headers = records[0] if records else []

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row   = [timestamp, month, book_title, name, rank1, rank2, rank3]

    try:
        name_col  = headers.index("VotedBy") + 1
        month_col = headers.index("Month") + 1
    except ValueError:
        # Headers missing — just append
        ws.append_row(new_row, value_input_option="USER_ENTERED")
        get_data.clear()
        return

    for i, row in enumerate(records[1:], start=2):
        if (len(row) >= max(name_col, month_col) and
                row[name_col - 1].strip().lower() == name.strip().lower() and
                row[month_col - 1].strip().lower() == month.strip().lower()):
            ws.update(f"A{i}", [new_row])
            get_data.clear()
            return

    ws.append_row(new_row, value_input_option="USER_ENTERED")
    get_data.clear()


def add_nomination(month: str, book_title: str, nominated_by: str,
                   author: str = "", genre: str = "",
                   length_pages: Optional[int] = None , difficulty: str = "",
                   description: str = "", why_nominated: str = "",
                   cover_url: str = ""):
    """
    Append a nomination row matching the Nominations sheet column order:
        Month | BookTitle | Author | Genre | LengthPages | Difficulty
        | Description | WhyNominated | NominatedBy | Status
    """
    append_row("Nominations", [
        month,
        book_title,
        author,
        genre,
        length_pages if length_pages is not None else "",
        difficulty,
        description,
        why_nominated,
        nominated_by,
        "Nominated",          # Status — always starts as Nominated
    ])
    get_data.clear()


def close_voting(winning_book: str, month: str):
    """
    Curator closes voting:
      1. Write "Won" to the winner row in Nominations, "Passed" to all others
         for this month.
      2. Update Config: current_book = winner, voting_open = False.
    """
    ws = _sheet("Nominations")
    records = ws.get_all_values()
    headers = records[0] if records else []

    try:
        month_col  = headers.index("Month") + 1
        title_col  = headers.index("BookTitle") + 1
        status_col = headers.index("Status") + 1
    except ValueError:
        # Can't find required columns — still update Config so voting closes
        pass
    else:
        for i, row in enumerate(records[1:], start=2):
            if (len(row) >= max(month_col, title_col) and
                    row[month_col - 1].strip().lower() == month.strip().lower()):
                is_winner = row[title_col - 1].strip().lower() == winning_book.strip().lower()
                ws.update_cell(i, status_col, "Won" if is_winner else "Passed")

    update_config("current_book", winning_book)
    update_config("voting_open", "False")
    get_data.clear()


def get_all_books():
    df = get_data("Books")

    if df.empty or "BookTitle" not in df.columns:
        return []

    return sorted(
        df["BookTitle"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
