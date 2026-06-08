
import streamlit as st

st.markdown('<div class="constitution-card">', unsafe_allow_html=True)

def render_constitution():
    st.title("📜 The KrachBooks Constitution")
    st.caption("A guide to how we read, discuss, and occasionally cause chaos.")
    st.divider()

    # Philosophy
    st.info(
        "KrachBooks exists to help us discover books we might never have picked up on our own and have great conversations about them. "
        "The goal is to have fun, challenge our perspectives, learn something new, and (occasionally) bully KD."
    )

    # Club Structure
    with st.expander("📚 Curator Responsibilities", expanded=True):
        st.markdown("""
        **Monthly Curator**

        Each month, one member serves as the Curator. The Curator is responsible for:

        * **Book Selection:** Choosing a shortlist of books they're genuinely excited about.
        * **Voting:** Opening voting early enough that members can acquire the winning book before the month begins.
        * **Meeting Logistics:** Coordinating the discussion meeting. The default meeting time is the **second Sunday of the month**.
        * **Calendar Invite:** Sending a calendar invite in the group chat to avoid timezone confusion.
        """)

    # Participation
    with st.expander("💬 Participation", expanded=True):
        st.success(
            "Discussion matters more than completion. If you've only read a chapter, come anyway."
        )

        st.markdown("""
        * **Attendance:** You are always welcome at the discussion, regardless of how much of the book you've finished.
        * **Monthly Check-In:** All members should complete the Check-In form before the meeting, even if they did not finish the book.
        * **Suggestions:** Use the Suggestions section of the Check-In form to propose future books, themes, or improvements.
        """)

    # Rules
    with st.expander("🤝 Rules of Engagement", expanded=True):
        st.markdown("""
        - Don't be a jerk.
        - Respect differing opinions and reading experiences.
        - Tangents are encouraged, provided they eventually find their way home.
        - Avoid major spoilers unless everyone has agreed they're fair game.
        """)

    # Voting
    with st.expander("🗳️ Voting & Decisions", expanded=True):
        st.markdown("""
        * **Voting Rights:** All active members may vote.
        * **Book Selection:** The winning book becomes the next month's read. (RCV is used)
        * **The People's Golden Veto:** If a curator somehow manages to nominate nothing but 500-page textbooks on tax law, operating systems, or similarly questionable choices, the club may collectively veto the shortlist.

        Use this power wisely.
        """)

    # Amendments
    with st.expander("🪴 Amendments"):
        st.markdown("""
        This constitution is living document. If the club decides a rule no longer serves us, we can discuss it during a regular meeting and update the constitution accordingly.
        """)

    st.divider()
    st.caption("Last Updated: June 2026")

st.markdown('</div>', unsafe_allow_html=True)

