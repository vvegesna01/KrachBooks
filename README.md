# Krachheads-Book-Club-Dashboard

A dashboard for my book club! 

# Pattern for google sheets data

2025-01_[ISBN].csv → November 2025 / Project Hail Mary

2025-02_[ISBN].csv → December 2025 / Everything is Tuberculosis


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

# Already computed:

n_finished      # how many books this member finished

n_total         # total months in the club

finished_months # list of month names they completed


# More Ideas

## Ideas for Badges

1. Hype Train - first to finish the book club book 3 times
2. Quote Machine - sends in the most quotes
3. Harsh Critic - (all ratings are below avg rating for that month, basically lowest average ratings.)
4. Golden Retriever Reader - Highest average ratings
5. Most Influential Voter - the person whose vote won the most amount of times?
6. Reading Streak Badges - 3 months, 6 months, 12 months (I already have bookworm for 5 months and loyal reader for 12 months)

## Badges for books?

1. Most Abandoned Book
2. Highest Rating Variance: Club Civil War Award
3. Most Hated Book


## Personal Stats 

1. Total pages read
2. 
