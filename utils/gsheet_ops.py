import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

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
    """Return Config sheet as a plain {key: value} dict."""
    df = get_data("Config")
    if df.empty or "Key" not in df.columns:
        return {}
    return dict(zip(df["Key"].str.strip(), df["Value"].str.strip()))


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


# ── WRITE HELPERS (gspread — service account) ─────────────────────────────────

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
    Otherwise append. row_data = [Timestamp, BookTitle, Name, Finished,
                                   DaysToRead, Format, Rating, Quote, Feedback]
    """
    ws = _sheet("Checkins")
    records = ws.get_all_values()          # [[header...], [row...], ...]
    headers = records[0] if records else []

    try:
        name_col  = headers.index("Name") + 1          # 1-indexed
        book_col  = headers.index("BookTitle") + 1
    except ValueError:
        ws.append_row(row_data, value_input_option="USER_ENTERED")
        get_data.clear()
        return

    for i, row in enumerate(records[1:], start=2):
        if (len(row) >= max(name_col, book_col) and
                row[name_col - 1].strip().lower() == name.strip().lower() and
                row[book_col - 1].strip().lower() == book_title.strip().lower()):
            # overwrite the whole row
            ws.update(f"A{i}", [row_data])
            get_data.clear()
            return

    ws.append_row(row_data, value_input_option="USER_ENTERED")
    get_data.clear()


def upsert_vote(name: str, month: str, book_title: str):
    """One vote per member per month — overwrite if they change their mind."""
    ws = _sheet("Votes")
    records = ws.get_all_values()
    headers = records[0] if records else []

    try:
        name_col  = headers.index("VotedBy") + 1
        month_col = headers.index("Month") + 1
    except ValueError:
        ws.append_row([month, book_title, name])
        get_data.clear()
        return

    for i, row in enumerate(records[1:], start=2):
        if (len(row) >= max(name_col, month_col) and
                row[name_col - 1].strip().lower() == name.strip().lower() and
                row[month_col - 1].strip().lower() == month.strip().lower()):
            ws.update(f"A{i}", [[month, book_title, name]])
            get_data.clear()
            return

    ws.append_row([month, book_title, name])
    get_data.clear()


def add_nomination(month: str, book_title: str, nominated_by: str, cover_url: str = ""):
    append_row("Nominations", [month, book_title, nominated_by, cover_url])
    get_data.clear()


def close_voting(winning_book: str, month: str):
    """Curator closes voting: set current_book + voting_open=False in Config."""
    update_config("current_book", winning_book)
    update_config("voting_open", "False")
    get_data.clear()