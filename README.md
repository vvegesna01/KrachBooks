# Krachheads-Book-Club-Dashboard

A dashboard for my book club! 


# Badge System

All badge images go in the assets/ folder next to app.py. Each file must be named exactly matching the badge ID used in code (it takes png and svg also)

KrachBooks/

├── app.py

├── assets/

│   ├── book_1.svg      ← badge for month 1

│   ├── book_2.svg      ← badge for month 2

│   ├── ...

│   ├── book_10.svg

│   ├── bookworm.svg    ← special: finish 5+ books

│   └── champion.svg    ← special: finish ALL books


# Two types of Badges

Book badges — one per month, auto-generated from your loaded CSVs. The code in the My Badges tab does this:

pythonbadge_defs = [

    (f"book_{i}", st.session_state.months[month]["book"], month in finished_months)

    for i, month in enumerate(all_months[:10], 1)

]

So month 1 → book_1.svg, month 2 → book_2.svg, etc. A member earns it by having _finished = True in that month's CSV. The cap is 

currently 10 months — raise that number if your club goes longer.


Special badges — defined in this list right below:

pythonspecial = [

    ("bookworm",

     "Bookworm (5+ books)" if n_finished >= 5 else f"Bookworm — {5 - n_finished} more!",

     n_finished >= 5),

    ("champion",

     "champion" if (n_finished >= n_total > 0) else f"Finish all {n_total}!",

     n_finished >= n_total > 0),
]

Each entry is a tuple of (badge_id, label, earned_condition). To add more special badges, just extend this list. For example:

pythonspecial = [

    ("bookworm",   "Bookworm (5+ books)",    n_finished >= 5),

    ("champion",   "Club Champion 👑",        n_finished >= n_total > 0),

    ("speedreader","Speed Reader",            some_condition),

    ("critic",     "Harsh Critic",            another_condition),

]

Then add speedreader.svg and critic.svg to your assets/ folder and you're done.

Conditions you could build on

The member's data is available before the badge list, so you can compute anything from the loaded CSVs:
python


# KrachBooks — Setup Guide

## Google Sheets Schema

Your spreadsheet needs these **exact worksheet tab names**:

### `Config` sheet
| Key | Value |
|---|---|
| current_book | The Midnight Library |
| current_curator | Keval |
| current_month | June 2026 |
| voting_open | False |

### `Checkins` sheet (columns in this exact order)
```
Timestamp | BookTitle | Name | Finished | DaysToRead | Format | Rating | Quote | Feedback
```

### `Nominations` sheet
```
Month | BookTitle | NominatedBy | CoverURL
```

### `Votes` sheet
```
Month | BookTitle | VotedBy
```

---

## Streamlit Secrets (`secrets.toml`)

```toml
[app]
password = "your_club_password_here"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

Make sure the service account email has **Editor** access to the spreadsheet.

---

## Adding a New Member

Edit the `MEMBERS` list in `utils/ui.py`.

## Adding a New Curator

Edit the `CURATORS` list in `utils/ui.py` — lowercase names only.

---

## How the Voting Flow Works

1. Curator opens the **✨ Curator** tab → adds 2–3 nominations
2. Curator clicks **Open Voting** — sets `voting_open = True` in Config
3. Members see the **🗳️ Vote** tab with book covers and a radio button
4. Members can change their vote; only the latest counts (upsert logic)
5. Curator clicks **Close Voting & Pick Winner** → tallies votes, sets `current_book`, closes voting
6. Members now see "Voting closed, this month's book is X"

## How Check-ins Work

- Any member can fill the check-in form at any time during the month
- Submitting again **overwrites** their previous entry for that book (no duplicates)
- The Dashboard aggregates all check-ins for stats

## Cache

`get_data()` caches for 30 seconds. After writing, it clears the cache automatically.
For manual refresh, use `st.cache_data.clear()` or just wait 30s.


MEMBERS = ["Ani","Aryan","BO$$", "DetPleasant2000", "KD", "Kavya", "Lightspeed", "Maya", "OJ", "Pranjal", "Pooja", 
        "RishRash", "Satabdiya", "Shivani", "Smrithi", "Tanvi", "Viswa"]
