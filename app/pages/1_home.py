import streamlit as st
from pathlib import Path
from app.components.file_upload import load_css

st.set_page_config(layout="wide")

load_css()

header_container = st.container()
# --- Header ---
header_container.markdown("""
                          <div class="hero">
                            <div class="hero-tag">Home</div>
                            <div class="hero-title">Ship Emission Tracker</div>
                            <div class="hero-subtitle">Understanding emissions through the lens of the ocean</div>
                        </div>
                        """,
                        unsafe_allow_html=True)
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

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

with st.expander("**1. Upload Your Data**", False):
    st.write(
        """
        Start by uploading two files: your **port calls** dataset and a **vessel info** file.
        The model matches both files to enrich each port call with the corresponding vessel's
        technical specifications. CSV and Excel formats are supported.

        Both files have minimum column requirements for the model to run — download the templates
        below to make sure your data is structured correctly.
        """
    )

    from pathlib import Path

    port_calls_template   = Path(__file__).parents[2] / "data" / "templates" / "port_calls_template.csv"
    vessels_info_template = Path(__file__).parents[2] / "data" / "templates" / "vessels_info_template.csv"

    col1, col2 = st.columns([1, 1])

    with col1:
        st.download_button(
            label="Download port calls template",
            data=open(port_calls_template, "rb"),
            file_name="port_calls_template.csv",
            mime="text/csv",
            icon=":material/download:",
        )

    with col2:
        st.download_button(
            label="Download vessel info template",
            data=open(vessels_info_template, "rb"),
            file_name="vessels_info_template.csv",
            mime="text/csv",
            icon=":material/download:",
        )

with st.expander("**2. Customise Emission Factors & Uncertainties (Optional)**", False):
    st.write(
        """
        By default the model uses a built-in set of emission factors and uncertainty values
        validated against international maritime standards.

        If you have fleet-specific or port-specific data, you can override the defaults by
        uploading your own **emission factors** and **uncertainties** as JSON files.
        Templates and format documentation are available in the Resources section.
        """
    )
    EF_template   = Path(__file__).parents[2] / "data" / "templates" / "emission_factors_template.json"
    U_template = Path(__file__).parents[2] / "data" / "templates" / "uncertainties_template.json"

    col1, col2 = st.columns([1, 1])
    with col1:
        with open(EF_template, "rb") as file:
            st.download_button(
                label="Download emission factors template",
                data=file.read(),                       
                file_name="emission_factors_template.json", 
                mime="application/json",                
                icon=":material/download:",
            )

    with col2:
        with open(U_template, "rb") as file:
            st.download_button(
                label="Download uncertainties template",
                data=file.read(),                       
                file_name="uncertainties.json", 
                mime="application/json",                
                icon=":material/download:",
            )

with st.expander("**3. Run the Model**", False):
    st.write(
        """
        Once your files are uploaded, hit **Run Emissions Model**. The pipeline will:
        - Match each port call to its vessel's technical specs
        - Apply emission factors across three operational modes: navigation, manoeuvring, and hotelling
        - Calculate total emissions and uncertainties for CO, NOx, NMVOC, TSP/PM, BC, SFOC and CO₂
        
        Results are ready in seconds.
        """
    )

with st.expander("**4. Explore & Filter**", False):
    st.write(
        """
        Results are displayed as an interactive time series chart. Use the filters to drill down by:
        vessel name, vessel type, terminal, fuel type, and vessel size range.
        Select one or more pollutants to compare them side by side on the same chart.
        """
    )

with st.expander("**5. Download Your Report**", False):
    st.write(
        """
        Export your results as an Excel report. You can download the **full results** or a
        **filtered version** reflecting exactly what is displayed in the chart —
        useful for sharing targeted insights with specific stakeholders.
        """
    )
    st.markdown(
        """
        Ready to dive in? Click the button below to start analyzing your emissions data!
        """,
        unsafe_allow_html=True
    )
    st.page_link("pages/2_workspace.py", label="🚀 Get Started")
    






