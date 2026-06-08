# utils/club_constitution.py
import streamlit as st

def render_constitution():
    st.title("📜 The KrachBooks Constitution")
    
    st.markdown("""
    ### 1. The Core Philosophy
    KrachBooks is a community built on shared curiosity. We read to understand, to challenge our perspectives, and to enjoy the act of discovery together.
    
    ### 2. The Curator’s Role
    The Curator rotates monthly. They are responsible for:
    * **Selection:** Choosing a book that pushes the club's boundaries.
    * **Guidance:** Setting the theme or "guiding question" for the month.
    * **Communication:** Ensuring members have enough lead time to acquire the text.
    
    ### 3. Participation Standards
    * **Attendance:** If you cannot finish the book, come anyway! We prioritize discussion over completion.
    * **Respect:** Every opinion is valid, but arguments must be backed by reasons, not just feelings.
    * **Feedback:** If you have a suggestion for the club, use the 'Suggestions' tab to keep it recorded.
    
    ### 4. The Voting System
    * Nominations are collected throughout the month.
    * Voting is open to all active members. 
    * The majority vote wins, but the Curator holds the 'Golden Veto' to be used only in extreme cases of logistical impossibility.
    
    ### 5. Amendments
    This document is a living entity. If the club feels the need for a change, we will hold a 'Constitutional Review' meeting during the mid-year check-in.
    """)