import requests
import streamlit as st


@st.cache_data(ttl=3600)
def get_book_info_by_isbn(isbn: str):
    """Fetch book metadata from OpenLibrary using ISBN — most accurate."""
    isbn = str(isbn).strip().replace("-", "")
    url  = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        data = requests.get(url, timeout=5).json()
    except Exception:
        return None

    key  = f"ISBN:{isbn}"
    book = data.get(key)
    if not book:
        return None

    cover_url = None
    covers    = book.get("cover", {})
    # prefer large, fall back to medium then small
    for size in ("large", "medium", "small"):
        if covers.get(size):
            cover_url = covers[size]
            break

    authors = book.get("authors", [])
    author  = authors[0].get("name", "Unknown") if authors else "Unknown"

    return {
        "title":     book.get("title"),
        "author":    author,
        "cover_url": cover_url,
        "isbn":      isbn,
    }


@st.cache_data(ttl=3600)
def get_book_info_by_title(title: str):
    """Fallback: search OpenLibrary by title when no ISBN is available."""
    url = f"https://openlibrary.org/search.json?title={title}&limit=1"
    try:
        response = requests.get(url, timeout=5).json()
    except Exception:
        return None

    if response.get("docs"):
        doc      = response["docs"][0]
        cover_id = doc.get("cover_i")
        return {
            "title":     doc.get("title"),
            "author":    doc.get("author_name", ["Unknown"])[0],
            "cover_url": (
                f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                if cover_id else None
            ),
            "isbn": None,
        }
    return None


def get_book_info(title: str, isbn: str = None):
    """
    Main entry point. Uses ISBN lookup if available, falls back to title search.
    isbn can be None, empty string, or 'nan' — all treated as absent.
    """
    clean_isbn = str(isbn).strip() if isbn else ""
    if clean_isbn and clean_isbn.lower() not in ("nan", "none", ""):
        result = get_book_info_by_isbn(clean_isbn)
        if result and result.get("cover_url"):
            return result

    # fall back to title search
    return get_book_info_by_title(title)