import streamlit as st

def render_footer():
    st.markdown("---")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.info("🚀 Help shape KrachBooks")

        st.caption(
            """
            Found a bug? Want a new feature? Have an idea for a fun new badge?
            """
        )

        st.link_button(
            "💡 Submit Feature Requests, View Roadmap",
            "https://krachbooks.canny.io",
        )
    with col2:
        st.caption("Built and maintained by")
        st.page_link(
            "https://kvegesna.vercel.app",
            label="Keerthana Vegesna",
            icon="👩‍💻",
        )

    st.markdown("---")
    st.caption("© 2026 Krach Club • Version 2.0")