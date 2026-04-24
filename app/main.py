import streamlit as st

pages = {
    "Emissions calculator": [
        st.Page("pages/1_home.py", title="Home"),
        st.Page("pages/2_workspace.py", title="Workspace"),
    ],
    "Resources": [
        st.Page("pages/3_about.py", title="About Us"),
        st.Page("pages/4_resources.py", title="External Resources"),
    ],
}

pg = st.navigation(pages)
pg.run()