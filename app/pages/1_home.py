import streamlit as st
from pathlib import Path

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_path = Path(__file__).resolve().parents[1] / "styles" / "style.css"
load_css(css_path)

header_container = st.container()
# --- Header ---
header_container.markdown('<div class="title">🌊 Antarctica</div>', unsafe_allow_html=True)
header_container.markdown(
        '<div class="subtitle">Understanding emissions through the lens of the ocean</div>',
        unsafe_allow_html=True
    )

st.markdown(
    """
    ### Why the ocean?
    
    The ocean regulates our climate, absorbs carbon, and reflects the health of our planet.
    This tool helps you quantify environmental impact through data-driven emissions analysis.

    """,
    unsafe_allow_html=True
)

# --- How it works ---
st.markdown("## 🌐 How it works")

with st.expander("**1. Upload Your Data**",False):
    st.write(
        """
        Start by uploading your activity or transport dataset. We support CSV and Excel formats.
        A template is available to guide you in structuring your data for accurate emissions calculations.
        """
    )
    with open("data/data_template.csv", "rb") as file:
        st.download_button(
            label="Download template",
            data=file,
            file_name="emissions_template.csv",
            mime="text.csv",
            icon=":material/download:",
        )

with st.expander("**2. Processing**",False):
    st.write(
        """
        Once your data is uploaded, we apply validated emission factors to calculate your carbon footprint.
        Our backend processes the data efficiently, providing you with accurate results in seconds.
        """
    )

with st.expander("**3. Visualize**",False):
    st.write(
        """
        Finally, we present your emissions data through interactive charts and graphs.
        Explore your impact across different activities, time periods, or categories to identify key areas for improvement.
        """
    )
    

st.markdown(
    """
    Ready to dive in? Click the button below to start analyzing your emissions data!
    """,
    unsafe_allow_html=True
)
st.page_link("pages/2_workspace.py", label="🚀 Get Started")




