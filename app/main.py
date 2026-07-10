import streamlit as st

pages = {
    "Emissions calculator": [
        st.Page("pages/1_home.py", title="Home"),
        st.Page("pages/2_workspace.py", title="Workspace"),
        st.Page("pages/5_simulation.py", title="Simulation"),
    ],
    "Resources": [
        st.Page("pages/3_about.py", title="About Us"),
        st.Page("pages/4_resources.py", title="Reference Library"),
    ],
}

pg = st.navigation(pages)
pg.run()